"""Inject failures into the real representation verifier without any free search."""

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from test_noiseless_control import (
    BACKEND_SEEDS,
    fake_runtime,  # noqa: F401 -- Register shared fixture.
    pools_environment,
)
from test_noiseless_control import DRIVER as OLD
from test_representation_profiles import PLUGINS, fields, plugin_fixture

from ringdown_sr import representation_control as control
from ringdown_sr import symbolic
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json
from ringdown_sr.representation_profiles import (
    PROFILE_FORMAT,
    RUNTIME_FILES,
    profile_parameters,
)

SPEC = importlib.util.spec_from_file_location(
    "representation_driver",
    Path(__file__).resolve().parents[1] / "scripts/run_representation_control.py",
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


@pytest.fixture
def runtime(request, monkeypatch):
    state = request.getfixturevalue("fake_runtime")
    monkeypatch.setattr(DRIVER, "BASE", OLD)
    state.alter = None
    state.preflight_alter = None

    def preflight(output, runtime, original, initial, sources, support, probe):
        snapshot = copy.deepcopy(initial)
        snapshot["environment"] = pools_environment(True)
        snapshot["blas_control"] = probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        )
        record = {
            "format": "ringdown-sr-representation-preflight-1",
            "status": "verified",
            "callback_calls": 0,
            "initial": snapshot,
            "final": snapshot,
            "source_sha256": sources,
            "profiles": [],
        }
        for cell in control.planned_cells():
            condition, seed = cell["condition"], cell["budget"]["seed"]
            record["profiles"].append(
                {
                    "condition": condition,
                    "python_seed": seed,
                    "backend_seed": BACKEND_SEEDS[seed],
                    "backend_options": fields(condition, seed),
                    "plugins_field": PLUGINS[condition],
                    "plugins": plugin_fixture(condition),
                }
            )
        if state.preflight_alter:
            state.preflight_alter(record)
        _write_json(output / "preflight.json", record)
        _write_json(
            output / "references.json", {"status": "verified", "source_sha256": sources}
        )
        DRIVER.verify_preflight(record, initial, sources, support, probe)
        return record

    monkeypatch.setattr(DRIVER, "inspect_backend", preflight)

    def enrich(number, directory, docs):
        cell = control.planned_cells()[number - 1]
        condition, seed = cell["condition"], cell["budget"]["seed"]
        sources = DRIVER.source_hashes()
        docs["pysr_parameters.json"] = {
            **profile_parameters(symbolic.SearchBudget(**cell["budget"]), condition),
            "output_directory": str(directory / "pysr"),
        }
        docs["backend_options.json"] = fields(condition, seed)
        docs["representation_profile.json"] = {
            "format": PROFILE_FORMAT,
            "condition": condition,
        }
        docs["representation_manifest.json"] = {
            "format": "ringdown-sr-representation-manifest-1",
            "sources": sources,
            "runtime": {key: sources[value] for key, value in RUNTIME_FILES.items()},
            "inputs": {
                "request.json": _sha256(_json_bytes(docs["request.json"])),
                "representation_profile.json": _sha256(
                    _json_bytes(docs["representation_profile.json"])
                ),
                "inputs.npz": _sha256((directory / "inputs.npz").read_bytes()),
            },
        }
        for name in (
            "RingdownSRLoss.jl",
            "RingdownSRSearch.jl",
            "RepresentationProfiles.jl",
        ):
            (directory / name).write_bytes(
                (DRIVER.ROOT / "julia/src" / name).read_bytes()
            )
        docs["result.json"]["callback_calls_during_fit"] = 10
        docs["representation_verification.json"] = {
            "format": "ringdown-sr-representation-verification-1",
            "status": "verified",
            "condition": condition,
            "backend_seed": BACKEND_SEEDS[seed],
            "plugins_field": PLUGINS[condition],
            "plugins": plugin_fixture(condition),
            "callback_calls_during_fit": 10,
            "callback_calls_total": 11,
            "profile_sha256": _sha256(_json_bytes(docs["representation_profile.json"])),
            "manifest_sha256": _sha256(
                _json_bytes(docs["representation_manifest.json"])
            ),
            "julia_source_sha256": sources["julia/src/RepresentationProfiles.jl"],
        }
        if state.alter:
            state.alter(number, directory, docs)

    state.hook = enrich
    return state


def report(output):
    return json.loads((output / "report.json").read_text())


def test_complete_series_keeps_order_coordinates_selection_and_all_fronts(
    runtime, tmp_path
):
    output = tmp_path / "complete"
    result = DRIVER.run_control(output, label="fixture")
    assert result["status"] == "completed"
    assert result["final_verification"] == "passed"
    assert result["started_count"] == 9
    for cell, (time, observed, budget, directory) in zip(
        result["cells"], runtime.calls, strict=True
    ):
        scale = cell["settings"]["time_scale"]
        np.testing.assert_array_equal(time, np.arange(128) / (4096 / scale))
        np.testing.assert_array_equal(
            observed.view(np.uint64), runtime.calls[0][1].view(np.uint64)
        )
        assert budget.niterations == 200
        diagnosis = cell["diagnostics"]
        assert diagnosis["selected_index"] == 0
        assert [c["source_index"] for c in diagnosis["candidates"]] == [0, 1]
        assert diagnosis["callback_calls_during_fit"] == 10
        assert diagnosis["callback_calls_total"] == 11
    assert all(
        s["status"] == "complete" for s in result["condition_summaries"].values()
    )
    assert all(d["status"] == "available" for d in result["seed_differences"])
    for name, digest in json.loads((output / "metadata.json").read_text())[
        "artifact_sha256"
    ].items():
        assert _sha256((output / name).read_bytes()) == digest
    with pytest.raises(FileExistsError):
        DRIVER.run_control(output, label="fixture")


@pytest.mark.parametrize("number", [1, 2, 3])
@pytest.mark.parametrize(
    "fault",
    [
        "selection",
        "seed",
        "backend_seed",
        "flags",
        "plugin_field",
        "plugin_record",
        "callback",
        "total_calls",
        "request",
        "profile",
        "manifest",
        "julia",
        "residual",
        "mse",
        "extra_backend",
        "covariance",
        "time",
        "provenance",
        "core",
    ],
)
def test_first_and_later_cells_reject_even_consistently_checksummed_forgery(
    runtime, tmp_path, number, fault
):
    def alter(index, directory, docs):
        if index != number:
            return
        front = docs["result.json"]
        native = docs["representation_verification.json"]
        if fault == "selection":
            front["selected_index"] = 1
        elif fault == "seed":
            front["rng"]["python_seed"] += 1
        elif fault == "backend_seed":
            next(f for f in docs["backend_options.json"] if f["name"] == "seed")[
                "value"
            ] = "4"
        elif fault == "flags":
            next(
                f for f in docs["backend_options.json"] if f["name"] == "use_frequency"
            )["value"] = "false" if number == 3 else "true"
        elif fault == "plugin_field":
            native["plugins_field"] = {"type": "Tuple{}", "value": "()"}
            next(
                f for f in docs["backend_options.json"] if f["name"] == "plugins"
            ).update(native["plugins_field"])
        elif fault == "plugin_record":
            native["plugins"][0]["fields"][0]["value"] = "3.18"
        elif fault == "callback":
            native["callback_calls_during_fit"] = front["callback_calls_during_fit"] = 0
        elif fault == "total_calls":
            native["callback_calls_total"] = 10
        elif fault == "request":
            docs["request.json"]["budget"]["niterations"] = 201
        elif fault == "profile":
            docs["representation_profile.json"]["condition"] = "combined"
        elif fault == "manifest":
            docs["representation_manifest.json"]["sources"].pop(
                "src/ringdown_sr/representation_profiles.py"
            )
        elif fault == "julia":
            (directory / "RepresentationProfiles.jl").write_text("changed")
        elif fault == "residual":
            front["candidates"][1]["residual"][1] *= -1
        elif fault == "mse":
            front["candidates"][1]["loss"] *= 1.1
        elif fault == "extra_backend":
            docs["backend_options.json"].append(
                {"name": "unplanned", "type": "Bool", "value": "true"}
            )
        elif fault in ("covariance", "time"):
            with np.load(directory / "inputs.npz") as saved:
                arrays = {k: saved[k] for k in saved.files}
            if fault == "time":
                arrays["time_s"] *= 2
            else:
                arrays["covariance"] = np.eye(128)
            np.savez(directory / "inputs.npz", **arrays)
        elif fault == "provenance":
            docs["metadata.json"]["worker_provenance"] = {"changed": True}
        else:
            docs["blas_control.json"]["snapshots"].pop("before_fit")

    runtime.alter = alter
    output = tmp_path / "forged"
    with pytest.raises(ValueError):
        DRIVER.run_control(output, label="fixture")
    result = report(output)
    assert result["status"] == "failed" and len(runtime.calls) == number
    assert result["cells"][number - 1]["status"] == "failed"
    assert all(c["status"] == "planned" for c in result["cells"][number:])


@pytest.mark.parametrize(
    "fault", ["missing", "duplicate", "seed", "plugin", "options", "calls", "source"]
)
def test_preflight_failure_starts_no_cell(runtime, tmp_path, fault):
    def alter(record):
        if fault == "missing":
            record["profiles"].pop()
        elif fault == "duplicate":
            record["profiles"][1] = copy.deepcopy(record["profiles"][0])
        elif fault == "seed":
            record["profiles"][0]["backend_seed"] = 2
        elif fault == "plugin":
            record["profiles"][0]["plugins"][0]["fields"][0]["value"] = "9"
        elif fault == "options":
            record["profiles"][1]["backend_options"].append(
                {"name": "extra", "type": "Bool", "value": "true"}
            )
        elif fault == "calls":
            record["callback_calls"] = 1
        else:
            record["source_sha256"] = {}

    runtime.preflight_alter = alter
    output = tmp_path / "preflight"
    with pytest.raises(ValueError):
        DRIVER.run_control(output, label="fixture")
    assert not runtime.calls
    assert all(c["status"] == "planned" for c in report(output)["cells"])


@pytest.mark.parametrize(
    "fault",
    [
        "preflight.json",
        "runtime/run_representation_worker.py",
        "cell-01/representation_profile.json",
        "cell-01/representation_verification.json",
        "cell-01/RepresentationProfiles.jl",
        "cell-01/result.json",
        "training.npz",
    ],
)
def test_final_mutation_blocks_every_summary_and_difference(
    runtime, monkeypatch, tmp_path, fault
):
    original = DRIVER.save_report

    def save(output, result):
        original(output, result)
        if (
            result["cell_states"] == {"completed": 9}
            and result["final_verification"] == "pending"
        ):
            with (output / fault).open("ab") as file:
                file.write(b"\nchanged")

    monkeypatch.setattr(DRIVER, "save_report", save)
    output = tmp_path / "final"
    with pytest.raises(ValueError):
        DRIVER.run_control(output, label="fixture")
    result = report(output)
    assert result["final_verification"] == "failed"
    assert all(
        s["status"] == "not_assessed" and s["statistics"] is None
        for s in result["condition_summaries"].values()
    )
    assert all(
        d["status"] == "not_assessed" and d["metrics"] is None
        for d in result["seed_differences"]
    )


@pytest.mark.parametrize(
    "error,status",
    [
        (RuntimeError("worker failed"), "failed"),
        (KeyboardInterrupt("interrupted"), "aborted"),
    ],
)
def test_partial_state_retained_without_retries(runtime, tmp_path, error, status):
    def alter(number, directory, docs):
        if number == 2:
            (directory / "partial.log").write_text("keep")
            raise error

    runtime.alter = alter
    original = symbolic._run_worker
    output = tmp_path / "partial"
    with pytest.raises(type(error)):
        DRIVER.run_control(output, label="fixture")
    result = report(output)
    assert [c["status"] for c in result["cells"]] == ["completed", status] + [
        "planned"
    ] * 7
    assert (output / "cell-02/partial.log").read_text() == "keep"
    assert len(runtime.calls) == 2 and symbolic._run_worker is original


def test_dispatch_retains_launcher_cancellation_entry_and_writes_checked_manifest(
    tmp_path,
):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    for name, source in RUNTIME_FILES.items():
        (runtime / name).write_bytes((DRIVER.ROOT / source).read_bytes())
    cell = control.planned_cells()[0]
    directory = tmp_path / cell["directory"]
    directory.mkdir()
    _write_json(
        directory / "request.json",
        {"format": symbolic.FORMAT, "budget": cell["budget"]},
    )
    np.savez(directory / "inputs.npz", time_s=[0.0], observed=[0.0])
    calls = []

    def launch(command, *, stdout):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    dispatch = DRIVER.dispatch(runtime, cell, DRIVER.source_hashes(), launch)
    command = [
        DRIVER.sys.executable,
        str(DRIVER.ROOT / "scripts/run_python.py"),
        str(DRIVER.ROOT / "scripts/run_symbolic_worker.py"),
        str(directory),
    ]
    assert dispatch(command, stdout=None).returncode == 0
    assert calls == [
        [*command[:2], str(runtime / "run_representation_worker.py"), str(directory)]
    ]
    assert set(json.loads((directory / "representation_profile.json").read_text())) == {
        "format",
        "condition",
    }
    with pytest.raises(ValueError):
        dispatch(["unexpected"], stdout=None)
