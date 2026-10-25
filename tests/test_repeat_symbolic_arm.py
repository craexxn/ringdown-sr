"""Frozen-data repetition contracts with controlled worker outcomes."""

import copy
import hashlib
import importlib.util
import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/repeat_symbolic_arm.py"
SPEC = importlib.util.spec_from_file_location("repeat_symbolic_arm", PATH)
REPEAT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPEAT)


def write(path, value):
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def hashes(directory):
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.iterdir()
        if p.is_file()
    }


def seal(directory):
    values = hashes(directory)
    write(directory / "checksums.json", {name: values[name] for name in REPEAT.FILES})


def stored_arm(directory, *, covariance=False, prediction=0.0):
    directory.mkdir()
    times = np.array([0.0, 0.25, 0.5])
    observed = np.array([1e-21, -1e-21, 2e-21])
    arrays = {"time_s": times, "observed": observed}
    if covariance:
        arrays["covariance"] = (
            np.array([[2.0, 1.0, 0.0], [1.0, 2.0, 0.0], [0.0, 0.0, 1.0]]) * 1e-42
        )
    np.savez(directory / "inputs.npz", **arrays)
    budget = REPEAT.SearchBudget(
        seed=123,
        niterations=1,
        populations=1,
        population_size=16,
        ncycles_per_iteration=1,
    )
    write(
        directory / "request.json", {"format": REPEAT.FORMAT, "budget": asdict(budget)}
    )
    write(
        directory / "result.json",
        {
            "format": REPEAT.FORMAT,
            "selected_index": 0,
            "rng": {"python_seed": 123, "backend_seed": 456},
            "candidates": [
                {
                    "tree": {"kind": "constant", "value_hex": float(prediction).hex()},
                    "complexity": 1,
                    "loss": 1.0,
                    "prediction": [prediction] * 3,
                    "residual": (observed - prediction).tolist(),
                }
            ],
            "timing_seconds": {"fit": 1.0},
        },
    )
    metadata = {
        "provenance": {"git": {"commit": "source", "dirty": False}},
        "environment": {"historical": True},
    }
    metadata["worker_provenance"] = copy.deepcopy(metadata["provenance"])
    metadata["adapter_source_sha256"] = {"adapter": "frozen-source"}
    metadata["worker_adapter_source_sha256"] = {"adapter": "frozen-source"}
    for name in ("metadata.json", "metadata_initial.json"):
        write(directory / name, metadata)
    write(
        directory / "pysr_parameters.json",
        {
            **REPEAT.search_parameters(budget),
            "run_id": "search",
            "output_directory": str(directory / "equations"),
        },
    )
    write(
        directory / "backend_options.json",
        [
            {"name": "seed", "type": "Int64", "value": "456"},
            {"name": "output_directory", "type": "String", "value": str(directory)},
        ],
    )
    write(directory / "status.json", {"status": "success"})
    seal(directory)
    return directory


@pytest.fixture
def source(tmp_path):
    return stored_arm(tmp_path / "source")


def fake_runner(calls, *, change=None, interrupt=False):
    def run(time_s, observed, *, covariance, output, budget):
        number = len(calls) + 1
        calls.append(
            {
                "time_s": time_s.copy(),
                "observed": observed.copy(),
                "covariance": None if covariance is None else covariance.copy(),
                "budget": budget,
                "output": output,
            }
        )
        stored_arm(output, covariance=covariance is not None)
        np.savez(
            output / "inputs.npz",
            time_s=time_s,
            observed=observed,
            **({} if covariance is None else {"covariance": covariance}),
        )
        result = REPEAT.read_json((output / "result.json").read_bytes())
        result["timing_seconds"]["fit"] = number * 2
        write(output / "result.json", result)
        seal(output)
        if change is not None:
            change(number, output)
        if interrupt:
            raise KeyboardInterrupt
        return SimpleNamespace(status="success")

    return run


@pytest.mark.parametrize("covariance", [False, True])
def test_two_calls_keep_source_bits_budget_and_environment(
    tmp_path, monkeypatch, covariance
):
    source = stored_arm(tmp_path / "source", covariance=covariance)
    before = hashes(source)
    calls = []
    keys = (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "JULIA_NUM_THREADS",
    )
    env = {key: os.environ.get(key) for key in keys}
    monkeypatch.setattr(REPEAT, "run_search_arm", fake_runner(calls))
    report = REPEAT.repeat(source, tmp_path / "out", label="wsl2")
    assert hashes(source) == before
    assert {key: os.environ.get(key) for key in keys} == env
    assert len(calls) == 2 and calls[0]["output"] != calls[1]["output"]
    for key in ("time_s", "observed"):
        assert REPEAT.array_fingerprint(calls[0][key]) == REPEAT.array_fingerprint(
            calls[1][key]
        )
    assert (
        calls[0]["budget"]
        == calls[1]["budget"]
        == REPEAT.SearchBudget(**report["budget"])
    )
    if covariance:
        assert REPEAT.array_fingerprint(
            calls[0]["covariance"]
        ) == REPEAT.array_fingerprint(calls[1]["covariance"])
    else:
        assert calls[0]["covariance"] is calls[1]["covariance"] is None
    assert report["status"] == "completed"
    assert all(report["comparison"].values())
    assert (tmp_path / "out/source/inputs.npz").read_bytes() == (
        source / "inputs.npz"
    ).read_bytes()
    assert report["driver_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("field", ["prediction", "loss", "tree", "rng", "backend"])
def test_meaningful_differences_are_not_hidden_by_volatile_fields(
    source, tmp_path, monkeypatch, field
):
    calls = []

    def change(number, directory):
        if number != 2:
            return
        result = REPEAT.read_json((directory / "result.json").read_bytes())
        if field == "prediction":
            result["candidates"][0]["prediction"][0] = 1e-300
        elif field == "loss":
            result["candidates"][0]["loss"] = np.nextafter(1.0, 2.0)
        elif field == "tree":
            result["candidates"][0]["tree"]["value_hex"] = (-0.0).hex()
        elif field == "rng":
            result["rng"]["backend_seed"] = 999
        else:
            options = REPEAT.read_json(
                (directory / "backend_options.json").read_bytes()
            )
            options[0]["value"] = "999"
            write(directory / "backend_options.json", options)
        write(directory / "result.json", result)
        seal(directory)

    monkeypatch.setattr(REPEAT, "run_search_arm", fake_runner(calls, change=change))
    report = REPEAT.repeat(source, tmp_path / "out", label="test")
    assert report["status"] == "completed"
    key = (
        "rng_records_equal"
        if field == "rng"
        else "backend_options_repr_equal_except_output"
        if field == "backend"
        else "front_bitwise_equal"
    )
    assert report["comparison"][key] is False
    assert report["comparison"]["inputs_bitwise_equal"] is True


@pytest.mark.parametrize(
    "filename", ["inputs.npz", "request.json", "metadata.json", "result.json"]
)
def test_source_checksum_failure_prevents_any_search(
    source, tmp_path, monkeypatch, filename
):
    (source / filename).write_bytes(b"tampered")
    monkeypatch.setattr(
        REPEAT, "run_search_arm", lambda *a, **kw: pytest.fail("Search must not start")
    )
    with pytest.raises(ValueError, match="checksum"):
        REPEAT.repeat(source, tmp_path / "out", label="test")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("mode", ["changed", "missing"])
def test_changed_policy_is_rejected_before_start(source, tmp_path, mode):
    parameters = REPEAT.read_json((source / "pysr_parameters.json").read_bytes())
    if mode == "changed":
        parameters["parsimony"] = 0.1
    else:
        del parameters["maxdepth"]
    write(source / "pysr_parameters.json", parameters)
    seal(source)
    with pytest.raises(ValueError, match="policy"):
        REPEAT.repeat(source, tmp_path / "out", label="test")


def test_existing_output_and_source_descendants_are_rejected(source, tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep").write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        REPEAT.repeat(source, existing, label="test")
    assert (existing / "keep").read_bytes() == b"keep"
    with pytest.raises(ValueError, match="outside"):
        REPEAT.repeat(source, source / "nested", label="test")


@pytest.mark.parametrize("failure", ["status", "interrupt", "input", "source"])
def test_failed_run_keeps_initial_evidence_and_partial_output(
    source, tmp_path, monkeypatch, failure
):
    calls = []

    def change(number, directory):
        if number != 1:
            return
        if failure == "input":
            np.savez(directory / "inputs.npz", time_s=[0.0], observed=[1.0])
            seal(directory)
        elif failure == "source":
            (source / "request.json").write_bytes(b"changed")

    runner = fake_runner(calls, change=change, interrupt=failure == "interrupt")
    if failure == "status":

        def failed(*args, **kwargs):
            runner(*args, **kwargs)
            return SimpleNamespace(status="failed")

        monkeypatch.setattr(REPEAT, "run_search_arm", failed)
    else:
        monkeypatch.setattr(REPEAT, "run_search_arm", runner)
    with pytest.raises((ValueError, RuntimeError, KeyboardInterrupt)):
        REPEAT.repeat(source, tmp_path / "out", label="test")
    report = REPEAT.read_json((tmp_path / "out/report.json").read_bytes())
    assert report["status"] == "failed" and report["comparison"] is None
    assert report["driver_sha256"] and report["provenance"] and report["environment"]
    assert (tmp_path / "out/source/inputs.npz").exists()
    assert len(calls) == 1


def test_signature_preserves_signed_zero_and_does_not_modify_result(source):
    result = REPEAT.read_json((source / "result.json").read_bytes())
    before = copy.deepcopy(result)
    first = REPEAT.signature(result)
    assert result == before
    result["candidates"][0]["prediction"][0] = -0.0
    assert REPEAT.signature(result)["front"] != first["front"]


def test_non_float64_inputs_are_rejected(source, tmp_path):
    np.savez(
        source / "inputs.npz",
        time_s=np.array([0, 1], dtype=np.float32),
        observed=np.array([0, 1], dtype=np.float32),
    )
    seal(source)
    with pytest.raises(ValueError, match="Float64"):
        REPEAT.repeat(source, tmp_path / "out", label="test")
