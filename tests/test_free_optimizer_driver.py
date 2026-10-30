"""Inject failures into the actual free-budget driver, without scientific searches."""

import copy
import json
import signal
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest
from test_free_optimizer_budget import DRIVER, control, option_fixture
from test_noiseless_control import DRIVER as OLD
from test_noiseless_control import (
    fake_runtime,  # noqa: F401 -- Register the shared non-search fixture.
    pools_environment,
)

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
                for i in control.ITERATIONS
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
        seed, iterations = cell["budget"]["seed"], cell["iterations"]
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
            "iterations": iterations,
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
            (directory / "FreeOptimizerBudget.jl").write_text("changed")
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
        "cell-01/FreeOptimizerBudget.jl",
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
