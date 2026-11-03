"""Inject failures into the actual grammar driver, without scientific searches."""

import copy
import json

import pytest
from test_noiseless_control import (
    BACKEND_SEEDS,
    fake_runtime,  # noqa: F401 -- Register the shared non-search fixture.
    pools_environment,
)
from test_noiseless_control import DRIVER as OLD
from test_trigonometric_grammar import option_fixture

from ringdown_sr import search_duration as control
from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json

DRIVER = control.load_module(
    control.ROOT / "scripts/run_search_duration.py", "duration_factory"
).load_driver()


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    for seed, native in {
        20261103: 583244435,
        20261104: 286892023,
        20261105: 1870355541,
        20261106: 550057980,
        20261107: 288620641,
    }.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)
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
            "search_profiles": control.search_profiles(),
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
        docs["search_invocation.json"] = control.invocation_record(
            cell["budget"]["niterations"]
        )
        if state.alter:
            state.alter(number, directory, docs)

    state.hook = enrich
    return state


def assert_locked(output):
    report = json.loads((output / "report.json").read_bytes())
    assert report["status"] == "incomplete"
    assert report["final_verification"] != "passed"
    assert all(
        report[k] is None for k in ("summaries", "pair_differences", "comparison")
    )
    return report


def test_all_twenty_cells_preserve_inputs_fronts_and_selection(runtime, tmp_path):
    output = tmp_path / "full"
    result = DRIVER.run(runtime.archive, output, label="fixture")
    assert result["status"] == "completed"
    assert result["final_verification"] == "passed"
    assert len(runtime.calls) == 20
    assert len(result["pair_differences"]) == 20
    for cell, (time, observed, budget, directory) in zip(
        result["cells"], runtime.calls, strict=True
    ):
        assert len(time) == len(observed) == 128
        assert cell["budget"]["niterations"] == budget.niterations
        assert (
            cell["diagnostics"]["search_invocation"]["niterations"]
            == budget.niterations
        )
        assert cell["diagnostics"]["selected_index"] == 0
        assert [c["source_index"] for c in cell["diagnostics"]["candidates"]] == [0, 1]
    for name, digest in json.loads((output / "checksums.json").read_bytes()).items():
        assert _sha256((output / name).read_bytes()) == digest


@pytest.mark.parametrize("number", [1, 3])
@pytest.mark.parametrize(
    "fault", ["invocation", "python_budget", "seed", "profile", "selection", "residual"]
)
def test_consistently_rehashed_wrong_actual_budget_or_worker_fails(
    runtime, tmp_path, number, fault
):
    def alter(index, directory, docs):
        if index != number:
            return
        if fault == "invocation":
            docs["search_invocation.json"]["niterations"] = 999
        if fault == "python_budget":
            docs["pysr_parameters.json"]["niterations"] = 999
        if fault == "seed":
            docs["verification.json"]["backend_seed"] += 1
        if fault == "profile":
            docs["profile.json"]["condition"] = (
                "unrestricted" if index == 3 else "no_nested_trig"
            )
        if fault == "selection":
            docs["result.json"]["selected_index"] = 1
        if fault == "residual":
            docs["result.json"]["candidates"][0]["residual"][0] += 1

    runtime.alter = alter
    output = tmp_path / "failed"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert len(runtime.calls) == number
    assert_locked(output)


def test_real_timer_interrupts_parent_verification_and_restores_handler(
    runtime, tmp_path, monkeypatch
):
    import signal
    import time

    previous = signal.getsignal(signal.SIGALRM)

    def verify(*args):
        signal.setitimer(signal.ITIMER_REAL, 0.02)
        time.sleep(0.2)
        pytest.fail("Parent timer did not interrupt verification.")

    monkeypatch.setattr(DRIVER, "verify_cell", verify)
    output = tmp_path / "parent-timeout"
    with pytest.raises(TimeoutError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert len(runtime.calls) == 1
    assert_locked(output)
    assert signal.getsignal(signal.SIGALRM) is previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize(
    "fault", ["missing_native", "duplicate_native", "python_budget", "profile_count"]
)
def test_preflight_rejects_incomplete_or_wrong_profiles_before_search(
    runtime, tmp_path, fault
):
    def alter(record):
        if fault == "missing_native":
            record["profiles"].pop()
        if fault == "duplicate_native":
            record["profiles"][0] = copy.deepcopy(record["profiles"][1])
        if fault == "python_budget":
            record["search_profiles"][0]["parameters"]["niterations"] = 2000
        if fault == "profile_count":
            record["search_profiles"].pop()

    runtime.preflight_alter = alter
    output = tmp_path / "failed"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert not runtime.calls
    assert_locked(output)


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("worker failed"),
        TimeoutError("budget expired"),
        KeyboardInterrupt("cancelled"),
    ],
)
def test_partial_series_retained_without_retry_or_subgroup_release(
    runtime, tmp_path, error
):
    def alter(number, directory, docs):
        if number == 6:
            (directory / "partial.log").write_text("retained")
            raise error

    runtime.alter = alter
    output = tmp_path / "partial"
    with pytest.raises(type(error)):
        DRIVER.run(runtime.archive, output, label="fixture")
    report = assert_locked(output)
    assert len(runtime.calls) == 6
    assert sum(c["status"] == "completed" for c in report["cells"]) == 5
    assert (output / "cell-06/partial.log").read_text() == "retained"


def test_late_consumed_cell_mutation_revokes_entire_comparison(
    runtime, tmp_path, monkeypatch
):
    original = DRIVER.save_report
    done = False

    def save(output, report):
        nonlocal done
        original(output, report)
        if not done and report["cells"][-1]["status"] == "completed":
            done = True
            path = output / "cell-01/search_invocation.json"
            path.write_bytes(path.read_bytes() + b" ")

    monkeypatch.setattr(DRIVER, "save_report", save)
    output = tmp_path / "changed"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert_locked(output)


def test_final_publication_failure_revokes_even_after_rename(
    runtime, tmp_path, monkeypatch
):
    from pathlib import Path

    original = Path.replace
    done = False
    # Inject after the positive report reaches its final destination.
    output = tmp_path / "publication"

    def exact_publish(path, target):
        nonlocal done
        result = original(path, target)
        if (
            not done
            and path.name == "report.json.tmp"
            and Path(target) == output / "report.json"
        ):
            done = True
            raise OSError("publication failed after rename")
        return result

    monkeypatch.setattr(Path, "replace", exact_publish)
    with pytest.raises(OSError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert done
    assert_locked(output)
