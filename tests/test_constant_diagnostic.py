"""Counterexamples for fixed diagnostic identity, replays and summary barriers."""

import importlib.util
import math

import numpy as np
import pytest

from ringdown_sr import constant_diagnostic as d
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.symbolic import evaluate_tree


def load_script(name):
    spec = importlib.util.spec_from_file_location(
        name, d.ROOT / "scripts" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plugins():
    return [
        {
            "type": "SimulatedAnnealingPlugin",
            "fields": [{"name": "alpha", "type": "Float64", "value": "3.17"}],
        },
        {
            "type": "AdaptiveMutationWeightsPlugin",
            "fields": [
                {"name": name, "type": kind, "value": value}
                for name, kind, value in (
                    ("smoothing", "Float64", "0.02"),
                    ("floor", "Float64", "0.05"),
                    ("reward", "Symbol", ":cost"),
                    ("adaptation_strength", "Float64", "0.5"),
                )
            ],
        },
    ]


def synthetic_result(request, arrays):
    p = np.array(request["start"]["parameters"])
    tree = d.ringdown_tree(p)
    prediction = evaluate_tree(tree, arrays["time_s"])
    residual = arrays["observed"] - prediction
    loss = math.fsum(float(x) ** 2 for x in residual) / len(residual)
    hexes = lambda x: [float(v).hex() for v in x]
    draws = [np.ones(4), -np.ones(4)]
    restarts = [np.where(p == 0, v, p * (1 + 0.5 * v)) for v in draws]
    return {
        "request": request,
        "backend_seed": d.backend_seed(request["seed"]),
        "tree": tree,
        "parameters": hexes(p),
        "initial_parameters": hexes(p),
        "initial_loss": loss,
        "loss": loss,
        "prediction": hexes(prediction),
        "residual": hexes(residual),
        "rng_type": "Random.Xoshiro",
        "rng_before": ["1"] * 5,
        "rng_after": ["2"] * 5,
        "plugins": plugins(),
        "fit_callback_count": 10,
        "total_callback_count": 12,
        "restart_draws": [hexes(v) for v in draws],
        "restart_parameters": [hexes(v) for v in restarts],
        "states": [
            {
                "local_index": i + 1,
                "step": 0,
                "kind": "BFGSState",
                "parameters": hexes(v),
            }
            for i, v in enumerate([p] + restarts)
        ],
        "termination": {
            "status": "unavailable",
            "reason": "backend_does_not_return_local_optim_results",
        },
    }


def test_fixed_plan_and_order():
    arrays = frozen_data()
    calls = d.planned_calls(arrays["observed"])
    assert len(calls) == 48
    assert [x["start"]["name"] for x in calls[::6]] == [
        "L1",
        "L2",
        "L3",
        "L4",
        "R1",
        "R2",
        "R3",
        "R4",
    ]
    assert [x["iterations"] for x in calls[:4]] == [20, 100, 100, 20]
    assert [x["seed"] for x in calls[:6:2]] == list(d.SEEDS)
    assert len({(x["start"]["name"], x["seed"], x["iterations"]) for x in calls}) == 48
    assert d.backend_seed(20261020) == 465951028
    assert _sha256((d.ROOT / d.PLAN).read_bytes()) == d.PLAN_SHA256


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(backend_seed=1),
        lambda r: r.update(initial_parameters=["0x0.0p+0"] * 4),
        lambda r: r.update(initial_loss=1.0),
        lambda r: r.update(loss=1.0),
        lambda r: r.update(parameters=["0x0.0p+0"] * 4),
        lambda r: r.update(prediction=["0x0.0p+0"] * 128),
        lambda r: r.update(residual=["0x0.0p+0"] * 128),
        lambda r: r.update(restart_draws=[]),
        lambda r: r.update(restart_parameters=[]),
        lambda r: r["states"][0].update(parameters=["0x0.0p+0"] * 4),
        lambda r: r["states"][0].update(kind="NewtonState"),
        lambda r: r.update(termination={"status": "converged"}),
        lambda r: r.update(rng_type="default_rng"),
        lambda r: r.update(rng_before=[]),
        lambda r: r.update(total_callback_count=10),
        lambda r: r["plugins"][0]["fields"][0].update(value="0.0"),
    ],
)
def test_replay_counterexamples(mutation):
    arrays = frozen_data()
    request = d.planned_calls(arrays["observed"])[0]
    result = synthetic_result(request, arrays)
    assert (
        d.verify_result(result, request, arrays)["curve_marker"] == "outside_tolerance"
    )
    mutation(result)
    with pytest.raises((ValueError, AssertionError)):
        d.verify_result(result, request, arrays)


def test_pair_difference_identity_and_rng():
    arrays = frozen_data()
    cells = []
    for request in d.planned_calls(arrays["observed"]):
        result = synthetic_result(request, arrays)
        cells.append(
            {
                "request": request,
                "status": "completed",
                "result": result,
                "diagnosis": d.verify_result(result, request, arrays),
            }
        )
    differences = d.pair_differences(cells)
    assert len(differences) == 24
    assert all(x["loss_100_minus_20"] == 0 for x in differences)
    cells[0]["diagnosis"]["parameter_match"]["status"] = "not_assessed"
    assert all(
        v is None
        for v in d.pair_differences(cells)[0]["parameters"][
            "errors_100_minus_20"
        ].values()
    )
    cells[-1]["result"]["rng_after"][0] = "3"
    with pytest.raises(ValueError, match="Paired RNG"):
        d.pair_differences(cells)
    cells[-1]["status"] = "failed"
    assert d.pair_differences(cells) is None


@pytest.mark.parametrize(
    "target", ["request.json", "inputs.npz", "worker.py", "manifest.json"]
)
def test_manifest_detects_consistent_rehash(tmp_path, monkeypatch, target):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    directory = tmp_path / "call"
    directory.mkdir()
    sources = {v: _sha256(v.encode()) for v in d.RUNTIME.values()}
    monkeypatch.setattr(d, "source_hashes", lambda: sources)
    for name, source in d.RUNTIME.items():
        (runtime / name).write_bytes(source.encode())
    for name in ("request.json", "inputs.npz"):
        (directory / name).write_bytes(name.encode())
    manifest = {
        "sources": sources,
        "runtime": {k: sources[v] for k, v in d.RUNTIME.items()},
        "inputs": {
            name: _sha256((directory / name).read_bytes())
            for name in ("request.json", "inputs.npz")
        },
    }
    _write_json(directory / "manifest.json", manifest)
    d.verify_manifest(directory, runtime)
    if target == "manifest.json":
        manifest["sources"] = {}
        _write_json(directory / target, manifest)
    else:
        root = runtime if target == "worker.py" else directory
        (root / target).write_bytes(b"changed")
    with pytest.raises(ValueError):
        d.verify_manifest(directory, runtime)


def test_wrong_archive_rejected_without_extraction(tmp_path):
    archive = tmp_path / "bad.tar.gz"
    archive.write_bytes(b"not an archive")
    with pytest.raises(ValueError, match="Unexpected scientific"):
        d.read_archive(archive)
    assert list(tmp_path.iterdir()) == [archive]


def test_synthetic_tree_preserves_phase_and_binary_grouping():
    parameters = [2.0, -3.0, 4.0, 0.5]
    times = np.arange(8) / 10
    np.testing.assert_allclose(
        evaluate_tree(d.ringdown_tree(parameters), times),
        2 * (np.exp(-3 * times) * np.cos(4 * times + 0.5)),
        rtol=1e-15,
    )


@pytest.mark.parametrize(
    "failure",
    [
        "none",
        "worker",
        "timeout",
        "signal",
        "late_artifact",
        "late_input",
        "late_source",
    ],
)
def test_driver_preserves_partial_results_and_blocks_late_failures(
    tmp_path, monkeypatch, failure
):
    import json

    monkeypatch.syspath_prepend(str(d.ROOT / "scripts"))
    driver = load_script("run_constant_diagnostic")
    archive = tmp_path / "input.tar.gz"
    archive.write_bytes(b"original")
    arrays = frozen_data()
    monkeypatch.setattr(driver, "_provenance", lambda: {"git": {"dirty": False}})
    monkeypatch.setattr(driver, "read_archive", lambda p: (b"original", arrays))
    monkeypatch.setattr(driver, "verify_controls", lambda r, a: None)
    monkeypatch.setattr(driver, "verify_blas_snapshots", lambda r: None)
    monkeypatch.setattr(driver, "verify_options_record", lambda r, ref: None)
    output = tmp_path / "out"
    sources = driver.source_hashes()
    monkeypatch.setattr(driver, "source_hashes", lambda: sources)

    def fake_launch(command, log, remaining):
        directory = Path(command[-1])
        request = json.loads((directory / "request.json").read_bytes())
        if request.get("mode") == "controls":
            result = {"request": request}
        else:
            if failure == "worker":
                raise RuntimeError("injected worker error")
            if failure == "timeout":
                raise TimeoutError("injected timeout")
            if failure == "signal":
                driver.cancel(15, None)
            result = synthetic_result(request, arrays)
        _write_json(directory / "result.json", result)

    from pathlib import Path

    monkeypatch.setattr(driver, "launch", fake_launch)
    original_pairs = driver.pair_differences

    def late_check(cells):
        differences = original_pairs(cells)
        if failure == "late_artifact":
            (output / "call-01/result.json").write_bytes(b"{}")
        elif failure == "late_input":
            archive.write_bytes(b"changed")
        elif failure == "late_source":
            monkeypatch.setattr(driver, "source_hashes", dict)
        return differences

    monkeypatch.setattr(driver, "pair_differences", late_check)
    if failure == "none":
        driver.run(archive, output)
    else:
        with pytest.raises((ValueError, TimeoutError, RuntimeError, KeyboardInterrupt)):
            driver.run(archive, output)
    report = json.loads((output / "report.json").read_bytes())
    assert (output / "checksums.json").is_file()
    if failure == "none":
        assert report["status"] == "completed"
        assert report["final_verification"] == "passed"
        assert len(report["pair_differences"]) == 24
    else:
        assert report["pair_differences"] is None
        assert report["summaries"] is None
        assert report["status"] == "incomplete"
        if failure.startswith("late"):
            assert len(report["cells"]) == 48
            assert all(c["status"] == "completed" for c in report["cells"])
        else:
            assert report["cells"][0]["status"] == "failed"


def option_pair():
    request = {"seed": 20261020}
    row = lambda name, value: {"name": name, "type": "Int64", "value": str(value)}
    reference = {
        "plugins": plugins(),
        "backend_options": [row("seed", 465951028), row("maxsize", 20)],
        "optimizer_settings": {
            "iterations": "20",
            "callback": "nothing",
            "g_abstol": "1.0e-8",
        },
        "rng_references": {
            "20261020": {"before": ["1"] * 5, "after": ["2"] * 5, "draws": []}
        },
    }
    result = {
        "request": request,
        "plugins": plugins(),
        "backend_options": [row("seed", 465951028), row("maxsize", 20)],
        "optimizer_settings": {
            "iterations": "20",
            "callback": "observing_callback",
            "g_abstol": "1.0e-8",
        },
        "rng_before": ["1"] * 5,
        "rng_after": ["2"] * 5,
        "restart_draws": [],
    }
    return result, reference


@pytest.mark.parametrize(
    "field",
    [
        "seed",
        "maxsize",
        "plugins",
        "optimizer_settings",
        "rng_before",
        "rng_after",
        "restart_draws",
        "field_coverage",
    ],
)
def test_absolute_options_and_rng_reject_first_call_tampering(field):
    result, reference = option_pair()
    d.verify_options_record(result, reference)
    if field in ("seed", "maxsize"):
        next(x for x in result["backend_options"] if x["name"] == field)["value"] = "0"
    elif field == "plugins":
        result["plugins"][0]["fields"][0]["value"] = "0.0"
    elif field == "optimizer_settings":
        result[field]["g_abstol"] = "0.001"
    elif field == "field_coverage":
        result["backend_options"].append(result["backend_options"][0])
    else:
        result[field] = ["changed"]
    with pytest.raises(ValueError):
        d.verify_options_record(result, reference)


@pytest.mark.parametrize("interrupted", [False, True])
def test_launcher_terminates_own_worker_on_timeout(monkeypatch, tmp_path, interrupted):
    import subprocess

    monkeypatch.syspath_prepend(str(d.ROOT / "scripts"))
    driver = load_script("run_constant_diagnostic")
    stopped = []

    class Process:
        def wait(self, timeout):
            if interrupted:
                driver.cancel(15, None)
            raise subprocess.TimeoutExpired("fixture", timeout)

    process = Process()
    monkeypatch.setattr(driver.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(driver.symbolic, "_stop_worker", lambda p: stopped.append(p))
    with (
        (tmp_path / "log").open("w") as log,
        pytest.raises((subprocess.TimeoutExpired, KeyboardInterrupt)),
    ):
        driver.launch(["fixture"], log, 0.1)
    assert stopped == [process]
