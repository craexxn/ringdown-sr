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
