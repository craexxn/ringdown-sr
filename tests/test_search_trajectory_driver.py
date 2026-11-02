"""Failure injection for bounded trajectory orchestration, without any search."""

import copy
import importlib.util
import json
import signal
import sys
import time
from types import SimpleNamespace

import pytest
from test_free_optimizer_budget import option_fixture as budget_options
from test_noiseless_control import DRIVER as OLD
from test_noiseless_control import (
    fake_runtime,  # noqa: F401 -- Register the existing isolated fake worker.
    pools_environment,
)

from ringdown_sr import search_trajectory as policy
from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json

SPEC = importlib.util.spec_from_file_location(
    "trajectory_driver_tests", policy.ROOT / "scripts/run_search_trajectory.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


def option_fixture(seed, observed):
    record = budget_options(seed, 100)
    record["observed"] = observed
    record["baseline_plugins"] = copy.deepcopy(record["plugins"])
    record["baseline_plugins_field"] = copy.deepcopy(record["plugins_field"])
    if observed:
        name = "Main.SearchTrajectory.SearchTrajectoryObserver"
        record["plugins"].append({"type": name, "fields": []})
        record["plugins_field"] = {
            "type": record["plugins_field"]["type"][:-1] + "," + name + "}",
            "value": record["plugins_field"]["value"][:-1] + "," + name + "())",
        }
    record["expected_plugins_field"] = copy.deepcopy(record["plugins_field"])
    for field in record["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({policy.OBJECTIVE})", value=policy.OBJECTIVE)
        elif field["name"] == "plugins":
            field.update(record["plugins_field"])
    return record


def fake_clock():
    return SimpleNamespace(
        started=time.monotonic(),
        remaining=lambda: 3600,
        check=lambda: None,
        cancel=lambda: None,
    )


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    state = request.getfixturevalue("fake_runtime")
    monkeypatch.setattr(DRIVER, "BASE", OLD)
    # Signal mechanics themselves stay covered by the existing Linux tests.
    # This fixture permits pure failure-publication tests on Windows as well.
    if not hasattr(signal, "pthread_sigmask"):
        monkeypatch.setattr(signal, "pthread_sigmask", lambda *_: set(), raising=False)
        monkeypatch.setattr(signal, "SIG_BLOCK", 0, raising=False)
        monkeypatch.setattr(signal, "SIG_SETMASK", 1, raising=False)
    state.archive = tmp_path / "representation.tar.gz"
    state.archive.write_bytes(b"non-executed original archive fixture")
    arrays = frozen_data()
    monkeypatch.setattr(
        DRIVER,
        "read_archive",
        lambda archive: (b"non-executed original archive fixture", arrays),
    )
    state.alter = None
    state.preflight_alter = None
    state.observation_failure = None

    def preflight(output, runtime, initial, sources, support, probe, remaining):
        snapshot = copy.deepcopy(initial)
        snapshot["environment"] = pools_environment(True)
        snapshot["blas_control"] = probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        )
        record = {
            "format": policy.FORMAT,
            "status": "verified",
            "mode": "options",
            "callback_calls": 0,
            "initial": snapshot,
            "final": snapshot,
            "source_sha256": sources,
            "profiles": [
                option_fixture(c["budget"]["seed"], c["observed"])
                for c in policy.planned_cells()
            ],
        }
        if state.preflight_alter:
            state.preflight_alter(record)
        DRIVER.verify_preflight(record, initial, sources, support, probe)
        _write_json(output / "options.json", record)
        return record, {"options.json": (output / "options.json").read_bytes()}

    monkeypatch.setattr(DRIVER, "inspect_backend", preflight)

    def observation(
        path,
        *,
        expected_events,
        arrays,
        front,
        check,
        expected_sha256,
        expected_record,
        expected_units_sha256,
    ):
        check()
        if state.observation_failure:
            raise ValueError(state.observation_failure)
        assert expected_events == 400
        assert _sha256(path.read_bytes()) == expected_sha256
        assert (
            _sha256(path.with_name("observation_units.json").read_bytes())
            == expected_units_sha256
        )
        return {
            "observation": copy.deepcopy(expected_record),
            "trees": [],
            "fixture": "parser separately tested",
        }

    monkeypatch.setattr(policy, "verify_observations", observation)

    def enrich(number, directory, docs):
        cell = policy.planned_cells()[number - 1]
        sources = policy.source_hashes()
        native = option_fixture(cell["budget"]["seed"], cell["observed"])
        docs["pysr_parameters.json"] = {
            **policy.profile_parameters(
                symbolic.SearchBudget(**cell["budget"]), cell["observed"]
            ),
            "output_directory": str(directory / "pysr"),
        }
        docs["backend_options.json"] = copy.deepcopy(native["backend_options"])
        docs["profile.json"] = {
            "format": policy.PROFILE_FORMAT,
            "observed": cell["observed"],
        }
        docs["manifest.json"] = {
            "format": policy.FORMAT,
            "sources": sources,
            "runtime": {k: sources[v] for k, v in policy.RUNTIME.items()},
            "inputs": {
                "request.json": _sha256(_json_bytes(docs["request.json"])),
                "profile.json": _sha256(_json_bytes(docs["profile.json"])),
                "inputs.npz": _sha256((directory / "inputs.npz").read_bytes()),
            },
        }
        for name in DRIVER.EXTRA_FILES:
            if name.endswith(".jl"):
                (directory / name).write_bytes(
                    (policy.ROOT / "julia/src" / name).read_bytes()
                )
        docs["result.json"]["callback_calls_during_fit"] = 10
        docs["result.json"]["timing_seconds"] = {
            "worker_setup": 0.0,
            "fit_including_jit_and_python_exports": float(number),
        }
        raw = b"Observation parser fixture; not native event data.\n"
        units = b"Unit parser fixture; not a native status.\n"
        if cell["observed"]:
            (directory / "observations.jsonl").write_bytes(raw)
            (directory / "observation_units.json").write_bytes(units)
        observation_record = {
            "status": "completed" if cell["observed"] else "disabled",
            "event_count": 400 if cell["observed"] else 0,
            "member_count": 12800 if cell["observed"] else 0,
            "bytes_written": len(raw) if cell["observed"] else 0,
            "units_bytes": len(units) if cell["observed"] else 0,
            "total_bytes": len(raw) + len(units) if cell["observed"] else 0,
            "max_bytes": policy.MAX_OBSERVATION_BYTES,
            "expected_events": 400,
        }
        if cell["observed"]:
            observation_record.update(
                raw_sha256=_sha256(raw), units_sha256=_sha256(units)
            )
        docs["verification.json"] = {
            **native,
            "format": policy.FORMAT,
            "status": "verified",
            "callback_calls_during_fit": 10,
            "callback_calls_total": 11,
            "profile_sha256": _sha256(_json_bytes(docs["profile.json"])),
            "manifest_sha256": _sha256(_json_bytes(docs["manifest.json"])),
            "observation": observation_record,
            "observation_timing_seconds": {"hook": 0.0, "units_after_fit": 0.0},
        }
        if state.alter:
            state.alter(number, directory, docs)

    state.hook = enrich
    state.run = lambda output: DRIVER.run_with_deadline(
        state.archive, output, label="fixture", clock=fake_clock()
    )
    return state


def locked(output):
    report = json.loads((output / "report.json").read_bytes())
    assert report["status"] == "incomplete"
    assert report["final_verification"] == "failed"
    assert report["comparative_interpretation"] is None
    assert not (output / "checksums.json").exists()
    assert not (output / "report.json.tmp").exists()
    assert "Vergleichende Interpretation: gesperrt." in (
        output / "summary.md"
    ).read_text(encoding="utf-8")
    return report


def test_six_cells_preserve_fronts_pairs_and_publish_only_at_end(runtime, tmp_path):
    output = tmp_path / "complete"
    report = runtime.run(output)
    assert len(runtime.calls) == 6
    assert [c["observed"] for c in report["cells"]] == [
        False,
        True,
        True,
        False,
        False,
        True,
    ]
    assert len(report["pairs"]) == 3
    assert report["comparative_interpretation"]["status"] == "available"
    assert [c["diagnostics"]["selected_index"] for c in report["cells"]] == [0] * 6
    assert [c["diagnostics"]["candidate_count"] for c in report["cells"]] == [2] * 6
    assert [
        c["diagnostics"]["observation"]["event_count"] for c in report["cells"]
    ] == [0, 400, 400, 0, 0, 400]
    assert report["historical_comparison"]["status"] == "not_assessed"
    for name, digest in json.loads((output / "checksums.json").read_bytes()).items():
        assert _sha256((output / name).read_bytes()) == digest


@pytest.mark.parametrize(
    "fault",
    [
        "callback",
        "tree",
        "selection",
        "residual",
        "loss",
        "native_seed",
        "plugin",
        "profile",
        "unexpected_control_observations",
    ],
)
def test_consistently_rehashed_forgery_cannot_release_pair(runtime, tmp_path, fault):
    def alter(number, directory, docs):
        if number != 2:
            return
        front = docs["result.json"]
        if fault == "callback":
            front["callback_calls_during_fit"] += 1
            docs["verification.json"]["callback_calls_during_fit"] += 1
            docs["verification.json"]["callback_calls_total"] += 1
        elif fault == "tree":
            front["candidates"][0]["tree"]["value_hex"] = float(1).hex()
        elif fault == "selection":
            front["selected_index"] = 1
        elif fault in {"residual", "loss"}:
            if fault == "residual":
                front["candidates"][1]["residual"][0] += 0.25
            else:
                front["candidates"][1]["loss"] *= 0.5
        elif fault == "native_seed":
            docs["verification.json"]["backend_seed"] = front["rng"]["backend_seed"] = 7
        elif fault == "plugin":
            docs["verification.json"]["plugins"][0]["fields"][0]["value"] = "99.0"
        elif fault == "profile":
            docs["profile.json"]["truth"] = [250, 0.008]
        else:
            docs["verification.json"]["observed"] = False

    runtime.alter = alter
    output = tmp_path / fault
    with pytest.raises((ValueError, KeyError, AssertionError)):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 2
    assert report["pairs"] == []
    assert all(c["status"] == "planned" for c in report["cells"][2:])


def test_pair_checks_all_candidate_fields_not_only_original_selection(
    runtime, tmp_path
):
    def alter(number, directory, docs):
        if number == 2:
            docs["result.json"]["candidates"][1]["display_equation"] = (
                "changed nonselected display"
            )

    runtime.alter = alter
    output = tmp_path / "nonselected"
    with pytest.raises(ValueError, match="exported search results differ"):
        runtime.run(output)
    assert len(runtime.calls) == 2
    locked(output)


@pytest.mark.parametrize("fault", ["missing", "negative", "extra", "control_nonzero"])
def test_invalid_observation_effort_cannot_release_comparison(runtime, tmp_path, fault):
    def alter(number, directory, docs):
        if number != 1:
            return
        timing = docs["verification.json"]["observation_timing_seconds"]
        if fault == "missing":
            timing.pop("hook")
        elif fault == "negative":
            timing["hook"] = -1.0
        elif fault == "extra":
            timing["unaccounted"] = 1.0
        else:
            timing["units_after_fit"] = 1.0

    runtime.alter = alter
    output = tmp_path / "effort"
    with pytest.raises(ValueError, match="observation effort accounting"):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 1
    assert all(cell["status"] == "planned" for cell in report["cells"][1:])


@pytest.mark.parametrize("reason", ["missing event", "duplicate event", "byte limit"])
def test_observation_verification_failure_stops_before_pair(runtime, tmp_path, reason):
    runtime.observation_failure = reason
    output = tmp_path / "observation"
    with pytest.raises(ValueError, match=reason):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 2
    assert report["cells"][1]["status"] == "failed"
    assert report["pairs"] == []


@pytest.mark.parametrize("fault", ["missing", "duplicate", "callback", "plugin"])
def test_bad_preflight_stops_before_any_search(runtime, tmp_path, fault):
    def alter(record):
        if fault == "missing":
            record["profiles"].pop()
        elif fault == "duplicate":
            record["profiles"][-1] = copy.deepcopy(record["profiles"][0])
        elif fault == "callback":
            record["callback_calls"] = 1
        else:
            record["profiles"][0]["plugins"][0]["fields"][0]["value"] = "9"

    runtime.preflight_alter = alter
    output = tmp_path / "preflight"
    with pytest.raises(ValueError):
        runtime.run(output)
    report = locked(output)
    assert not runtime.calls
    assert all(c["status"] == "planned" for c in report["cells"])


@pytest.mark.parametrize(
    "stage", ["after_publication", "stage_cleanup", "late_observation_mutation"]
)
def test_publication_or_cleanup_failure_revokes_released_interpretation(
    runtime, monkeypatch, tmp_path, stage
):
    output = tmp_path / stage
    replace = type(output).replace
    cleanup = DRIVER.HELPERS.tempfile.TemporaryDirectory.__exit__
    injected = False

    def publish(path, target):
        nonlocal injected
        result = replace(path, target)
        if (
            stage == "after_publication"
            and target == output / "report.json"
            and not injected
            and json.loads(target.read_bytes())["final_verification"] == "passed"
        ):
            injected = True
            raise RuntimeError("after positive rename")
        if (
            stage == "late_observation_mutation"
            and target == output / "checksums.json"
            and not injected
        ):
            injected = True
            raw = output / "cell-02/observations.jsonl"
            raw.write_bytes(raw.read_bytes() + b"changed")
            local = raw.parent / "checksums.json"
            values = json.loads(local.read_bytes())
            values[raw.name] = _sha256(raw.read_bytes())
            _write_json(local, values)
        return result

    def clean(*args):
        nonlocal injected
        result = cleanup(*args)
        if stage == "stage_cleanup" and not injected:
            injected = True
            raise RuntimeError("stage cleanup failed")
        return result

    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(DRIVER.HELPERS.tempfile.TemporaryDirectory, "__exit__", clean)
    with pytest.raises((RuntimeError, ValueError)):
        runtime.run(output)
    assert injected
    assert len(runtime.calls) == 6
    locked(output)


def test_failed_first_revocation_does_not_leave_positive_package(
    runtime, monkeypatch, tmp_path
):
    output = tmp_path / "revoke"
    replace, unlink = type(output).replace, type(output).unlink
    published, interrupted = False, False

    def publish(path, target):
        nonlocal published
        result = replace(path, target)
        if (
            target == output / "report.json"
            and not published
            and json.loads(target.read_bytes())["final_verification"] == "passed"
        ):
            published = True
            raise RuntimeError("primary publication failure")
        return result

    def revoke(path, *args, **kwargs):
        nonlocal interrupted
        if published and path == output / "report.json" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt("first revocation interrupted")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(type(output), "unlink", revoke)
    with pytest.raises(RuntimeError, match="primary publication failure"):
        runtime.run(output)
    assert published and interrupted
    locked(output)


def test_worker_dispatch_uses_minimum_of_remaining_and_per_worker_limit(
    runtime, monkeypatch, tmp_path
):
    cell = policy.planned_cells()[0]
    output = tmp_path / "dispatch"
    output.mkdir()
    directory = output / cell["directory"]
    directory.mkdir()
    sources = policy.source_hashes()
    native, _ = DRIVER.copy_runtime(output, sources)
    _write_json(
        directory / "request.json",
        {"format": symbolic.FORMAT, "budget": cell["budget"]},
    )
    (directory / "inputs.npz").write_bytes(b"dispatch-only not consumed arrays")
    captured = []
    monkeypatch.setattr(
        DRIVER, "launch", lambda *args, **kwargs: captured.append(kwargs["remaining"])
    )
    for remaining in (700, 17):
        dispatcher = DRIVER.dispatch(
            native,
            cell,
            sources,
            {},
            output,
            lambda value=remaining: value,
            lambda: None,
        )
        dispatcher(
            [
                sys.executable,
                str(policy.ROOT / "scripts/run_python.py"),
                str(policy.ROOT / "scripts/run_symbolic_worker.py"),
                str(directory),
            ],
            stdout=None,
        )
    assert captured == [600, 17]


def test_reused_output_and_source_overlap_rejected(runtime, tmp_path):
    output = tmp_path / "already"
    output.mkdir()
    for target in (output, policy.ROOT, runtime.archive.parent):
        with pytest.raises(ValueError):
            runtime.run(target)
    assert not runtime.calls


def test_scientific_command_requires_reference_linux_timer(monkeypatch):
    if hasattr(signal, "setitimer"):
        monkeypatch.delattr(signal, "setitimer")
    with pytest.raises(RuntimeError, match="Linux reference"):
        DRIVER.run("missing.tar.gz", "missing-output", label="fixture")
