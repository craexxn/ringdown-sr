"""Inject failures into the actual grammar driver, without scientific searches."""

import copy
import json
import os
import signal
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from test_noiseless_control import DRIVER as OLD
from test_noiseless_control import (
    candidate,
    fake_runtime,  # noqa: F401 -- Register the shared non-search fixture.
    pools_environment,
)
from test_structure import constant, operator
from test_trigonometric_grammar import DRIVER, control, option_fixture

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    state = request.getfixturevalue("fake_runtime")
    monkeypatch.setattr(DRIVER, "BASE", OLD)
    state.alter = None
    state.preflight_alter = None
    state.archive = tmp_path / "archive.tar.gz"
    state.archive.write_bytes(b"non-executed archive fixture")
    arrays = frozen_data()
    monkeypatch.setattr(
        DRIVER,
        "read_archive",
        lambda archive: (b"non-executed archive fixture", arrays),
    )

    def preflight(output, runtime, initial, sources, support, probe, remaining):
        snapshot = copy.deepcopy(initial)
        snapshot["environment"] = pools_environment(True)
        snapshot["blas_control"] = probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        )
        record = {
            "format": control.FORMAT,
            "status": "verified",
            "mode": "options",
            "callback_calls": 0,
            "initial": snapshot,
            "final": snapshot,
            "source_sha256": sources,
            "profiles": [
                option_fixture(seed, i)
                for i in control.CONDITIONS
                for seed in control.SEEDS
            ],
        }
        if state.preflight_alter:
            state.preflight_alter(record)
        _write_json(output / "options.json", record)
        _write_json(output / "references.json", {"fixture": "no native execution"})
        DRIVER.verify_preflight(record, initial, sources, support, probe)
        return record, {
            name: (output / name).read_bytes()
            for name in ("options.json", "references.json")
        }

    monkeypatch.setattr(DRIVER, "inspect_backend", preflight)

    def enrich(number, directory, docs):
        cell = control.planned_cells()[number - 1]
        seed, iterations = cell["budget"]["seed"], cell["condition"]
        sources = control.source_hashes()
        native = option_fixture(seed, iterations)
        docs["pysr_parameters.json"] = {
            **control.profile_parameters(
                symbolic.SearchBudget(**cell["budget"]), iterations
            ),
            "output_directory": str(directory / "pysr"),
        }
        docs["backend_options.json"] = copy.deepcopy(native["backend_options"])
        docs["profile.json"] = {
            "format": control.PROFILE_FORMAT,
            "condition": iterations,
        }
        docs["manifest.json"] = {
            "format": control.FORMAT,
            "sources": sources,
            "runtime": {k: sources[v] for k, v in control.RUNTIME.items()},
            "inputs": {
                "request.json": _sha256(_json_bytes(docs["request.json"])),
                "profile.json": _sha256(_json_bytes(docs["profile.json"])),
                "inputs.npz": _sha256((directory / "inputs.npz").read_bytes()),
            },
        }
        for name in DRIVER.EXTRA_FILES:
            if name.endswith(".jl"):
                (directory / name).write_bytes(
                    (control.ROOT / "julia/src" / name).read_bytes()
                )
        docs["result.json"]["callback_calls_during_fit"] = 10
        docs["result.json"]["rng"]["state_status"] = (
            "not_exported; serialized search state is not a complete RNG checkpoint"
        )
        docs["verification.json"] = {
            **native,
            "format": control.FORMAT,
            "status": "verified",
            "callback_calls_during_fit": 10,
            "callback_calls_total": 11,
            "profile_sha256": _sha256(_json_bytes(docs["profile.json"])),
            "manifest_sha256": _sha256(_json_bytes(docs["manifest.json"])),
        }
        if state.alter:
            state.alter(number, directory, docs)

    state.hook = enrich
    return state


def test_full_mock_series_keeps_all_candidates_order_and_original_selection(
    runtime, tmp_path
):
    output = tmp_path / "complete"
    result = DRIVER.run(runtime.archive, output, label="fixture")
    assert result["status"] == "completed" and result["final_verification"] == "passed"
    assert len(runtime.calls) == 6
    for cell, (time, observed, budget, directory) in zip(
        result["cells"], runtime.calls, strict=True
    ):
        np.testing.assert_array_equal(time, np.arange(128) / 4096)
        assert cell["diagnostics"]["selected_index"] == 0
        assert [c["source_index"] for c in cell["diagnostics"]["candidates"]] == [0, 1]
        assert budget.niterations == 200
    assert result["comparison"]["outcome"] == "no_successes"
    for name, digest in json.loads((output / "checksums.json").read_text()).items():
        assert _sha256((output / name).read_bytes()) == digest
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")


@pytest.mark.parametrize("number", [1, 2])
def test_consistently_rehashed_nested_candidate_is_allowed_only_in_control(
    runtime, tmp_path, number
):
    def alter(index, directory, docs):
        if index == number:
            tree = operator(
                "*", constant(0), operator("sin", operator("cos", constant(1)))
            )
            docs["result.json"]["candidates"][0] = candidate(tree, frozen_data())

    runtime.alter = alter
    output = tmp_path / "nested"
    if number == 1:
        assert (
            DRIVER.run(runtime.archive, output, label="fixture")["status"]
            == "completed"
        )
    else:
        with pytest.raises(ValueError, match="descendant"):
            DRIVER.run(runtime.archive, output, label="fixture")
        report = json.loads((output / "report.json").read_text())
        assert report["comparison"] is None and report["status"] == "incomplete"
        assert len(runtime.calls) == 2


@pytest.mark.parametrize("remaining,expected", [(3210, 600), (45, 45)])
def test_dispatch_caps_each_worker_and_preserves_shorter_series_deadline(
    monkeypatch, tmp_path, remaining, expected
):
    output = tmp_path / "series"
    runtime = output / "runtime"
    runtime.mkdir(parents=True)
    sources = control.source_hashes()
    for name, source in control.RUNTIME.items():
        (runtime / name).write_bytes((control.ROOT / source).read_bytes())
    cell = control.planned_cells()[0]
    directory = output / cell["directory"]
    directory.mkdir()
    _write_json(
        directory / "request.json",
        {"format": symbolic.FORMAT, "budget": cell["budget"]},
    )
    np.savez(directory / "inputs.npz", time_s=np.arange(8), observed=np.arange(8))
    captured = []
    monkeypatch.setattr(
        DRIVER, "launch", lambda command, **kw: captured.append(kw["remaining"])
    )
    dispatch = DRIVER.dispatch(
        runtime, cell, sources, {}, output, lambda: remaining, lambda: None
    )
    dispatch(
        [
            sys.executable,
            str(control.ROOT / "scripts/run_python.py"),
            str(control.ROOT / "scripts/run_symbolic_worker.py"),
            str(directory),
        ],
        stdout=None,
    )
    assert captured == [expected]


@pytest.mark.parametrize("number", [1, 4])
@pytest.mark.parametrize(
    "fault",
    [
        "selection",
        "seed",
        "budget",
        "flags",
        "plugins",
        "plugin_fields",
        "optimizer",
        "callback",
        "total",
        "request",
        "profile",
        "manifest",
        "native",
        "residual",
        "mse",
        "extra",
        "time",
        "truth",
        "provenance",
        "blas",
    ],
)
def test_first_and_later_cells_reject_consistently_checksummed_forgery(
    runtime, tmp_path, number, fault
):
    def alter(index, directory, docs):
        if index != number:
            return
        front, native = docs["result.json"], docs["verification.json"]
        if fault == "selection":
            front["selected_index"] = 1
        elif fault == "seed":
            front["rng"]["backend_seed"] = native["backend_seed"] = 2
        elif fault == "budget":
            for fields in (docs["backend_options.json"], native["backend_options"]):
                next(f for f in fields if f["name"] == "optimizer_options")["value"] = (
                    "Optim.Options(iterations = 21, )"
                )
            native["optimizer_settings"]["iterations"] = "21"
        elif fault == "flags":
            for fields in (docs["backend_options.json"], native["backend_options"]):
                next(f for f in fields if f["name"] == "use_frequency")["value"] = (
                    "false"
                )
        elif fault == "plugins":
            native["plugins_field"] = {"type": "Tuple{}", "value": "()"}
            for fields in (docs["backend_options.json"], native["backend_options"]):
                next(f for f in fields if f["name"] == "plugins").update(
                    native["plugins_field"]
                )
        elif fault == "plugin_fields":
            native["plugins"][1]["fields"][0]["value"] = "false"
        elif fault == "optimizer":
            native["optimizer_settings"]["f_reltol"] = "0.1"
        elif fault == "callback":
            native["callback_calls_during_fit"] = front["callback_calls_during_fit"] = 0
        elif fault == "total":
            native["callback_calls_total"] = 10
        elif fault == "request":
            docs["request.json"]["budget"]["niterations"] = 201
        elif fault == "profile":
            docs["profile.json"]["truth"] = [1, 250, 0.008, 0]
        elif fault == "manifest":
            docs["manifest.json"]["sources"] = {}
        elif fault == "native":
            (directory / "TrigonometricGrammar.jl").write_text("changed")
        elif fault == "residual":
            front["candidates"][1]["residual"][0] *= -1
        elif fault == "mse":
            front["candidates"][1]["loss"] *= 2
        elif fault == "extra":
            docs["backend_options.json"].append(
                {"name": "unknown", "type": "Bool", "value": "true"}
            )
        elif fault in {"time", "truth"}:
            with np.load(directory / "inputs.npz") as saved:
                arrays = {k: saved[k] for k in saved.files}
            if fault == "time":
                arrays["time_s"] *= 2
            else:
                arrays["diagnostic_truth"] = [1]
            np.savez(directory / "inputs.npz", **arrays)
        elif fault == "provenance":
            docs["metadata.json"]["worker_provenance"] = {}
        else:
            docs["blas_control.json"]["snapshots"].pop("before_fit")

    runtime.alter = alter
    output = tmp_path / "forged"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    result = json.loads((output / "report.json").read_text())
    assert len(runtime.calls) == number
    assert all(
        result[k] is None for k in ("summaries", "pair_differences", "comparison")
    )
    assert all(c["status"] == "planned" for c in result["cells"][number:])


@pytest.mark.parametrize(
    "fault",
    ["missing", "duplicate", "seed", "flags", "plugin", "optimizer", "calls", "source"],
)
def test_preflight_fault_starts_no_search(runtime, tmp_path, fault):
    def alter(record):
        first = record["profiles"][0]
        if fault == "missing":
            record["profiles"].pop()
        elif fault == "duplicate":
            record["profiles"][1] = copy.deepcopy(first)
        elif fault == "seed":
            first["backend_seed"] = 1
        elif fault == "flags":
            next(f for f in first["backend_options"] if f["name"] == "use_frequency")[
                "value"
            ] = "false"
        elif fault == "plugin":
            first["plugins"][1]["fields"][0]["value"] = "false"
        elif fault == "optimizer":
            first["optimizer_settings"]["iterations"] = "21"
        elif fault == "calls":
            record["callback_calls"] = 1
        else:
            record["source_sha256"] = {}

    runtime.preflight_alter = alter
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, tmp_path / "preflight", label="fixture")
    assert not runtime.calls


@pytest.mark.parametrize(
    "fault",
    [
        "options.json",
        "runtime/worker.py",
        "cell-01/inputs.npz",
        "cell-01/verification.json",
        "cell-01/result.json",
        "cell-01/TrigonometricGrammar.jl",
        "training.npz",
        "archive",
    ],
)
def test_late_mutation_blocks_all_groups_even_after_consistent_rehash(
    runtime, monkeypatch, tmp_path, fault
):
    original = DRIVER.save_report
    changed = False

    def save(output, report):
        nonlocal changed
        original(output, report)
        if (
            not changed
            and all(c["status"] == "completed" for c in report["cells"])
            and report["final_verification"] == "pending"
        ):
            changed = True
            path = runtime.archive if fault == "archive" else output / fault
            with path.open("ab") as file:
                file.write(b"\nchanged")
            if fault.startswith("cell-01/"):
                checksums = json.loads((output / "cell-01/checksums.json").read_text())
                checksums[path.name] = _sha256(path.read_bytes())
                _write_json(output / "cell-01/checksums.json", checksums)

    monkeypatch.setattr(DRIVER, "save_report", save)
    output = tmp_path / "late"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    result = json.loads((output / "report.json").read_text())
    assert result["final_verification"] == "failed"
    assert all(
        result[k] is None for k in ("summaries", "pair_differences", "comparison")
    )


@pytest.mark.parametrize(
    "error",
    [KeyboardInterrupt("stop"), TimeoutError("limit"), RuntimeError("worker failed")],
)
def test_partial_results_survive_without_retry_or_pair_summary(
    runtime, tmp_path, error
):
    def alter(number, directory, docs):
        if number == 3:
            (directory / "partial.log").write_text("retain")
            raise error

    runtime.alter = alter
    output = tmp_path / "partial"
    original = symbolic._run_worker
    with pytest.raises(type(error)):
        DRIVER.run(runtime.archive, output, label="fixture")
    result = json.loads((output / "report.json").read_text())
    assert len(runtime.calls) == 3
    assert [c["status"] for c in result["cells"][:2]] == ["completed", "completed"]
    assert (output / "cell-03/partial.log").read_text() == "retain"
    assert symbolic._run_worker is original
    assert result["pair_differences"] is result["summaries"] is None


@pytest.mark.parametrize(
    "error", [KeyboardInterrupt(), subprocess.TimeoutExpired("worker", 1)]
)
def test_timeout_and_interrupt_stop_the_own_process_group(monkeypatch, error):
    stopped = []
    process = SimpleNamespace(wait=lambda **kwargs: (_ for _ in ()).throw(error))
    monkeypatch.setattr(DRIVER.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(symbolic, "_stop_worker", stopped.append)
    with pytest.raises(type(error)):
        DRIVER.launch(["worker"], stdout=None, remaining=1)
    assert stopped == [process]


def test_sigterm_handler_restored_after_retained_abort(monkeypatch, tmp_path):
    seen = []
    previous = signal.getsignal(signal.SIGTERM)
    monkeypatch.setattr(
        DRIVER.sys,
        "argv",
        [
            "run",
            "--archive",
            str(tmp_path / "input"),
            "--output",
            str(tmp_path / "out"),
            "--label",
            "fixture",
        ],
    )

    def run(*args, **kwargs):
        seen.append(signal.getsignal(signal.SIGTERM))
        seen[-1](signal.SIGTERM, None)

    monkeypatch.setattr(DRIVER, "run", run)
    with pytest.raises(KeyboardInterrupt):
        DRIVER.main()
    assert seen and seen[0] != previous
    assert signal.getsignal(signal.SIGTERM) == previous


@pytest.mark.parametrize(
    "name", ["backend.py", "worker.py", "driver.py", "TrigonometricGrammar.jl"]
)
def test_changed_runtime_copy_fails_before_any_preflight_code_executes(
    monkeypatch, tmp_path, name
):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    sources = control.source_hashes()
    for key, source in control.RUNTIME.items():
        (runtime / key).write_bytes((control.ROOT / source).read_bytes())
    (runtime / name).write_text("changed before consumption")
    calls = []
    monkeypatch.setattr(DRIVER, "launch", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="before preflight consumption"):
        DRIVER.inspect_backend(tmp_path, runtime, None, sources, None, None, lambda: 60)
    assert not calls


@pytest.mark.parametrize("fault", ["summary_interrupt", "manifest_error", "mutation"])
def test_finalization_failures_never_leave_a_released_comparison(
    runtime, monkeypatch, tmp_path, fault
):
    output = tmp_path / "finalization"
    save, write_json = DRIVER.save_report, DRIVER._write_json
    write_text = type(output).write_text
    finalizing, injected = False, False

    def save_report(directory, report):
        nonlocal finalizing, injected
        finalizing = report["final_verification"] == "passed"
        save(directory, report)
        if finalizing and fault == "mutation" and not injected:
            injected = True
            path = output / "cell-01/result.json"
            path.write_bytes(path.read_bytes() + b"\n")
            checksums = json.loads((path.parent / "checksums.json").read_text())
            checksums[path.name] = _sha256(path.read_bytes())
            _write_json(path.parent / "checksums.json", checksums)

    def summary(path, *args, **kwargs):
        nonlocal injected
        if (
            finalizing
            and fault == "summary_interrupt"
            and not injected
            and path.name == "summary.md.tmp"
        ):
            injected = True
            raise KeyboardInterrupt("interrupted final summary")
        return write_text(path, *args, **kwargs)

    def manifest(path, value):
        nonlocal injected
        if (
            finalizing
            and fault == "manifest_error"
            and not injected
            and path.name == "checksums.json"
        ):
            injected = True
            raise OSError("cannot write final manifest")
        return write_json(path, value)

    monkeypatch.setattr(DRIVER, "save_report", save_report)
    monkeypatch.setattr(type(output), "write_text", summary)
    monkeypatch.setattr(DRIVER, "_write_json", manifest)
    expected = {"summary_interrupt": KeyboardInterrupt, "manifest_error": OSError}
    with pytest.raises(expected.get(fault, ValueError)):
        DRIVER.run(runtime.archive, output, label="fixture")
    result = json.loads((output / "report.json").read_text())
    assert injected and len(runtime.calls) == 6
    assert result["status"] == "incomplete"
    assert result["final_verification"] == "failed"
    assert all(
        result[key] is None for key in ("summaries", "pair_differences", "comparison")
    )
    assert "C_K=" not in (output / "summary.md").read_text()


def assert_locked_package(output):
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "incomplete"
    assert report["final_verification"] == "failed"
    assert all(
        report[key] is None for key in ("summaries", "pair_differences", "comparison")
    )
    assert "C_K=" not in (output / "summary.md").read_text()
    assert not (output / "checksums.json").exists()
    assert not (output / "report.json.tmp").exists()
    return report


@pytest.mark.parametrize("name", ["summary.md", "checksums.json", "report.json"])
@pytest.mark.parametrize("after_replace", [False, True])
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
def test_publication_failures_revoke_success_even_after_the_final_rename(
    runtime, monkeypatch, tmp_path, name, after_replace, error_type
):
    output = tmp_path / "publication"
    replace = type(output).replace
    injected = False

    def publish(path, target):
        nonlocal injected
        final = False
        if target == output / name:
            final = (
                path.parent != output
                if name != "report.json"
                else json.loads(path.read_bytes())["final_verification"] == "passed"
            )
        if final and not injected:
            injected = True
            if after_replace:
                replace(path, target)
            raise error_type("publication interrupted")
        return replace(path, target)

    monkeypatch.setattr(type(output), "replace", publish)
    with pytest.raises(error_type):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert injected and len(runtime.calls) == 6
    assert_locked_package(output)


@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("name", ["report.json", "summary.md", "checksums.json"])
def test_failed_first_revocation_still_locks_the_published_package(
    runtime, monkeypatch, tmp_path, error_type, name
):
    output = tmp_path / "failed-first-revocation"
    replace, unlink = type(output).replace, type(output).unlink
    published, interrupted = False, False
    attempted = []

    def publish(path, target):
        nonlocal published
        result = replace(path, target)
        if (
            target == output / "report.json"
            and not published
            and json.loads(target.read_bytes())["final_verification"] == "passed"
        ):
            published = True
            raise RuntimeError("primary failure after publication")
        return result

    def revoke(path, *args, **kwargs):
        nonlocal interrupted
        if published and path.parent == output:
            attempted.append(path.name)
            if path.name == name and not interrupted:
                interrupted = True
                raise error_type("first report revocation failed")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(type(output), "unlink", revoke)
    with pytest.raises((RuntimeError, error_type)) as caught:
        DRIVER.run(runtime.archive, output, label="fixture")
    assert published and interrupted and len(runtime.calls) == 6
    assert_locked_package(output)
    assert {"report.json", "summary.md", "checksums.json"} <= set(attempted)
    assert isinstance(caught.value, RuntimeError)
    assert str(caught.value) == "primary failure after publication"


@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("fault", ["removals", "summary_and_fallback"])
def test_repeated_revocation_errors_do_not_skip_remaining_abort_actions(
    runtime, monkeypatch, tmp_path, error_type, fault
):
    output = tmp_path / "repeated-revocation-errors"
    report = DRIVER.run(runtime.archive, output, label="fixture")
    artifact = output / "cell-01/result.json"
    original_artifact = artifact.read_bytes()
    unlink, write_text, write_json = (
        type(output).unlink,
        type(output).write_text,
        DRIVER._write_json,
    )
    attempts = []

    def revoke(path, *args, **kwargs):
        if path.parent == output:
            attempts.append(path.name)
            if fault == "removals" or (
                path.name == "report.json" and attempts.count(path.name) == 2
            ):
                raise error_type("revocation remains unavailable")
        return unlink(path, *args, **kwargs)

    def summary(path, *args, **kwargs):
        if fault == "summary_and_fallback" and path == output / "summary.md.tmp":
            raise error_type("abort summary unavailable")
        return write_text(path, *args, **kwargs)

    def machine_report(path, value):
        if fault == "summary_and_fallback" and path == output / "report.json":
            raise error_type("fallback report unavailable")
        return write_json(path, value)

    monkeypatch.setattr(type(output), "unlink", revoke)
    monkeypatch.setattr(type(output), "write_text", summary)
    monkeypatch.setattr(DRIVER, "_write_json", machine_report)
    clock = SimpleNamespace(started=DRIVER.time.monotonic(), cancel=lambda: None)
    DRIVER.retain_incomplete(output, report, RuntimeError("primary failure"), clock)
    assert artifact.read_bytes() == original_artifact
    assert {"checksums.json", "report.json", "summary.md"} <= set(attempts)
    assert report["status"] == "incomplete" and report["comparison"] is None
    if fault == "removals":
        assert len(attempts) == 12
        saved = json.loads((output / "report.json").read_bytes())
        assert saved["status"] == "incomplete" and saved["comparison"] is None
        assert "C_K=" not in (output / "summary.md").read_text()
        manifest = json.loads((output / "checksums.json").read_bytes())
        assert manifest["report.json"] != _sha256((output / "report.json").read_bytes())
    else:
        assert not (output / "report.json").exists()
        assert not (output / "summary.md").exists()
        assert not (output / "checksums.json").exists()
        assert "abort_persistence_error" in report
        assert {e["operation"] for e in report["abort_cleanup_errors"]} == {
            "write locked report",
            "remove unpersisted report",
        }


@pytest.mark.parametrize("delivery", ["process_signal", "python_callback"])
def test_repeated_cancellation_is_deferred_until_revocation_and_restores_state(
    runtime, monkeypatch, tmp_path, delivery
):
    output = tmp_path / "repeated-cancellation"
    report = DRIVER.run(runtime.archive, output, label="fixture")
    unlink = type(output).unlink
    cancellations = {signal.SIGINT, signal.SIGTERM}
    previous_mask = signal.pthread_sigmask(signal.SIG_UNBLOCK, cancellations)
    previous_handlers = {s: signal.getsignal(s) for s in cancellations}
    delivered = []

    def observe(signum, frame):
        saved = json.loads((output / "report.json").read_bytes())
        assert saved["status"] == "incomplete" and saved["comparison"] is None
        delivered.append(signum)

    def revoke(path, *args, **kwargs):
        if path.parent == output:
            for signum in cancellations:
                if delivery == "process_signal":
                    os.kill(os.getpid(), signum)
                else:
                    # Model Python delivery through a different unblocked thread.
                    signal.getsignal(signum)(signum, None)
        return unlink(path, *args, **kwargs)

    try:
        for signum in cancellations:
            signal.signal(signum, observe)
        monkeypatch.setattr(type(output), "unlink", revoke)
        clock = SimpleNamespace(started=DRIVER.time.monotonic(), cancel=lambda: None)
        DRIVER.retain_incomplete(output, report, RuntimeError("primary failure"), clock)
        assert_locked_package(output)
        assert not report["abort_cleanup_errors"]
        assert cancellations <= set(delivered + report["abort_signals"])
        assert all(signal.getsignal(s) is observe for s in cancellations)
        assert not signal.pthread_sigmask(signal.SIG_BLOCK, set()) & cancellations
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)


@pytest.mark.parametrize(
    "phase",
    [
        "source_hashes",
        "hash_read",
        "summary",
        "manifest",
        "summary_publish",
        "manifest_publish",
        "report_publish",
        "stage_cleanup",
    ],
)
def test_deadline_applies_throughout_finalization(
    runtime, monkeypatch, tmp_path, phase
):
    output = tmp_path / "deadline"
    now = SimpleNamespace(value=0.0)
    monkeypatch.setattr(DRIVER, "time", SimpleNamespace(monotonic=lambda: now.value))
    save, sources, hashing = (
        DRIVER.save_report,
        DRIVER.source_hashes,
        DRIVER.checked_hash,
    )
    write_json, write_text = DRIVER._write_json, type(output).write_text
    replace, cleanup = type(output).replace, DRIVER.tempfile.TemporaryDirectory.__exit__
    finalizing, injected = False, False

    def advance(current):
        nonlocal injected
        if finalizing and phase == current and not injected:
            injected = True
            now.value = control.LIMIT_SECONDS + 1.0

    def save_report(path, report):
        nonlocal finalizing
        finalizing = report["final_verification"] == "passed"
        return save(path, report)

    def source_hashes():
        result = sources()
        advance("source_hashes")
        return result

    def checked_hash(path, check):
        result = hashing(path, check)
        advance("hash_read")
        return result

    def summary(path, *args, **kwargs):
        result = write_text(path, *args, **kwargs)
        if path.name == "summary.md.tmp":
            advance("summary")
        return result

    def manifest(path, value):
        result = write_json(path, value)
        if path.name == "checksums.json":
            advance("manifest")
        return result

    def publish(path, target):
        result = replace(path, target)
        if target.parent == output:
            advance(
                {
                    "summary.md": "summary_publish",
                    "checksums.json": "manifest_publish",
                    "report.json": "report_publish",
                }.get(target.name)
            )
        return result

    def stage_exit(*args):
        result = cleanup(*args)
        advance("stage_cleanup")
        return result

    monkeypatch.setattr(DRIVER, "save_report", save_report)
    monkeypatch.setattr(DRIVER, "source_hashes", source_hashes)
    monkeypatch.setattr(DRIVER, "checked_hash", checked_hash)
    monkeypatch.setattr(DRIVER, "_write_json", manifest)
    monkeypatch.setattr(type(output), "write_text", summary)
    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(DRIVER.tempfile.TemporaryDirectory, "__exit__", stage_exit)
    with pytest.raises(TimeoutError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert injected and len(runtime.calls) == 6
    report = assert_locked_package(output)
    assert report["wall_seconds"] > control.LIMIT_SECONDS


def test_real_parent_timer_interrupts_blocking_work_and_restores_signal_state():
    script = """
import signal
import run_trigonometric_grammar as driver
previous = signal.getsignal(signal.SIGALRM)
try:
    with driver.WallTimeLimit(0.05):
        signal.pause()
except TimeoutError:
    pass
else:
    raise AssertionError('blocking parent work escaped its deadline')
assert signal.getsignal(signal.SIGALRM) == previous
assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
"""
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, 'scripts');" + script],
        cwd=control.ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_rehashed_cell_mutation_after_manifest_publication_is_not_adopted(
    runtime, monkeypatch, tmp_path
):
    output = tmp_path / "late-publication-mutation"
    replace = type(output).replace
    injected = False

    def publish(path, target):
        nonlocal injected
        result = replace(path, target)
        if target == output / "checksums.json" and not injected:
            injected = True
            artifact = output / "cell-01/result.json"
            artifact.write_bytes(artifact.read_bytes() + b"\n")
            local = artifact.parent / "checksums.json"
            entries = json.loads(local.read_bytes())
            entries[artifact.name] = _sha256(artifact.read_bytes())
            _write_json(local, entries)
            entries = json.loads(target.read_bytes())
            for changed in (artifact, local):
                entries[changed.relative_to(output).as_posix()] = _sha256(
                    changed.read_bytes()
                )
            _write_json(target, entries)
        return result

    monkeypatch.setattr(type(output), "replace", publish)
    with pytest.raises(ValueError, match="artifact changed"):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert injected
    assert_locked_package(output)


def test_repeated_abort_summary_failure_still_retains_a_locked_machine_report(
    runtime, monkeypatch, tmp_path
):
    output = tmp_path / "unwritable-summary"
    original = type(output).write_text
    failed = False

    def write(path, *args, **kwargs):
        nonlocal failed
        if path.name == "summary.md.tmp" and len(runtime.calls) == 6:
            failed = True
            raise OSError("summary persistence remains unavailable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(type(output), "write_text", write)
    with pytest.raises(OSError, match="summary persistence"):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert failed
    report = json.loads((output / "report.json").read_bytes())
    assert report["status"] == "incomplete" and report["comparison"] is None
    assert "abort_persistence_error" in report
    assert not (output / "summary.md").exists()
    assert not (output / "checksums.json").exists()


def test_existing_parent_timer_is_preserved():
    previous = signal.getsignal(signal.SIGALRM)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        with (
            pytest.raises(RuntimeError, match="existing parent wall timer"),
            DRIVER.WallTimeLimit(1),
        ):
            pytest.fail("foreign timer was overwritten")
        assert signal.getsignal(signal.SIGALRM) == previous
        assert signal.getitimer(signal.ITIMER_REAL)[0] > 0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def test_deadline_exceeded_during_final_directory_walk_blocks_release(
    runtime, monkeypatch, tmp_path
):
    output = tmp_path / "late-deadline"
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(DRIVER, "time", SimpleNamespace(monotonic=lambda: clock.now))
    rglob = type(output).rglob

    def walk(path, pattern):
        yield from rglob(path, pattern)
        if path == output and len(runtime.calls) == 6:
            clock.now = control.LIMIT_SECONDS + 1.0

    monkeypatch.setattr(type(output), "rglob", walk)
    with pytest.raises(TimeoutError):
        DRIVER.run(runtime.archive, output, label="fixture")
    result = json.loads((output / "report.json").read_text())
    assert result["status"] == "incomplete"
    assert result["final_verification"] == "failed"
    assert result["wall_seconds"] > control.LIMIT_SECONDS
    assert all(
        result[key] is None for key in ("summaries", "pair_differences", "comparison")
    )
