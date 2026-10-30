"""Frozen fixed-structure diagnostic and fail-closed replay, without free search."""

import io
import json
import math
import tarfile
from pathlib import Path

import numpy as np

from .noiseless_control import diagnose_candidate, fingerprint, frozen_data
from .pilot import _sha256
from .representation_profiles import source_hashes as base_sources
from .representation_profiles import validate_plugin_records
from .symbolic import ROOT, _check_prediction_replay, evaluate_tree

FORMAT = "ringdown-sr-constant-diagnostic-1"
PLAN = "docs/constant_diagnostic_plan.md"
PLAN_SHA256 = "5d546f1804da17239bfae33c1d3f3732f46582dc6cf96a4c3b850dda5be9861b"
ARCHIVE_SHA256 = "a5b0cdae4262a7f759c72fbe1e7e9c142d817fbffa088107953250da861050db"
SEEDS = (20261020, 20261021, 20261022)
LIMIT_SECONDS = 3600
RUNTIME = {
    "worker.py": "scripts/run_constant_diagnostic_worker.py",
    **{
        name: "julia/src/" + name
        for name in (
            "RingdownSRLoss.jl",
            "RingdownSRSearch.jl",
            "RepresentationProfiles.jl",
            "ConstantDiagnostic.jl",
        )
    },
}


def source_hashes():
    hashes = base_sources()
    for name in (
        PLAN,
        "scripts/run_constant_diagnostic.py",
        "scripts/run_constant_diagnostic_worker.py",
        "scripts/check_constant_diagnostic.py",
        "scripts/probe_symbolic_numerics.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen diagnostic plan changed.")
    return dict(sorted(hashes.items()))


def read_archive(path):
    """Read only pinned binary arrays; never extract or execute archived sources."""
    raw = Path(path).read_bytes()
    if _sha256(raw) != ARCHIVE_SHA256:
        raise ValueError("Unexpected scientific input archive.")
    arrays = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for name in ("training.npz", "diagnostic.npz"):
            matches = [
                p for p in archive if p.name == "representation-manjaro-001/" + name
            ]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError("Missing or duplicate archived input.")
            with np.load(
                io.BytesIO(archive.extractfile(matches[0]).read()), allow_pickle=False
            ) as saved:
                arrays.update({key: saved[key].copy() for key in saved.files})
    expected = frozen_data()
    if set(arrays) != set(expected) or any(
        fingerprint(arrays[key]) != fingerprint(expected[key]) for key in expected
    ):
        raise ValueError("Archived arrays do not match the frozen data bits.")
    return raw, arrays


def starts(observed):
    values = [
        (0.9, 247.5, 0.0072, -0.1),
        (1.1, 252.5, 0.0088, 0.1),
        (0.9, 252.5, 0.0088, -0.1),
        (1.1, 247.5, 0.0072, 0.1),
    ]
    duration = 128 / 4096
    values += [
        (float(np.max(np.abs(observed))), f, tau, math.pi / 2)
        for f in (128.0, 512.0)
        for tau in (duration / 8, duration / 2)
    ]
    return [
        {
            "name": ("L" if i < 4 else "R") + str(i % 4 + 1),
            "parameters": [a, -1 / tau, 2 * math.pi * f, phase],
        }
        for i, (a, f, tau, phase) in enumerate(values)
    ]


def planned_calls(observed):
    calls = []
    for start in starts(observed):
        for seed in SEEDS:
            pair = len(calls) // 2
            for iterations in (20, 100) if pair % 2 == 0 else (100, 20):
                calls.append(
                    {
                        "number": len(calls) + 1,
                        "start": start,
                        "seed": seed,
                        "iterations": iterations,
                    }
                )
    return calls


def backend_seed(seed):
    return int(np.random.RandomState(seed).randint(0, 2**31 - 1))


def verify_manifest(directory, runtime):
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if (
        set(manifest) != {"sources", "runtime", "inputs"}
        or manifest["sources"] != source_hashes()
    ):
        raise ValueError("Changed diagnostic source manifest.")
    if manifest["runtime"] != {
        name: manifest["sources"][src] for name, src in RUNTIME.items()
    }:
        raise ValueError("Wrong runtime manifest.")
    if set(manifest["inputs"]) != {"request.json", "inputs.npz"}:
        raise ValueError("Wrong diagnostic input manifest.")
    for root, hashes in (
        (runtime, manifest["runtime"]),
        (directory, manifest["inputs"]),
    ):
        for name, digest in hashes.items():
            p = root / name
            if p.is_symlink() or _sha256(p.read_bytes()) != digest:
                raise ValueError("Changed consumed diagnostic file.")
    return manifest


def decode(values):
    return np.array([float.fromhex(x) for x in values])


def ringdown_tree(parameters):
    """Preserve all thirteen nodes, including the additive phase constant."""

    def constant(value):
        return {"kind": "constant", "value_hex": float(value).hex()}

    def op(name, *children):
        names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
        return {
            "kind": "operator",
            "arity": len(children),
            "operator": name,
            "operator_index": names.index(name) + 1,
            "children": list(children),
        }

    a, b, c, phase = map(constant, parameters)
    t = {"kind": "variable", "index": 1}
    return op(
        "*",
        a,
        op("*", op("exp", op("*", b, t)), op("cos", op("+", op("*", c, t), phase))),
    )


def verify_options_record(result, reference):
    """Compare every field, with only the declared observation wrappers exempted."""
    for record in (result, reference):
        validate_plugin_records(record["plugins"], "baseline")
    actual = {x["name"]: x for x in result["backend_options"]}
    expected = {x["name"]: x for x in reference["backend_options"]}
    if len(actual) != len(result["backend_options"]) or set(actual) != set(expected):
        raise ValueError("Changed backend field coverage.")
    for key, field in actual.items():
        if key == "seed":
            expected_seed = backend_seed(result["request"]["seed"])
            if (
                field["value"] != str(expected_seed)
                or field["type"] != expected[key]["type"]
            ):
                raise ValueError("Changed actual backend seed option.")
        elif (
            key not in {"loss_function", "optimizer_options"} and field != expected[key]
        ):
            raise ValueError("Changed actual diagnostic backend option: " + key)
    settings, baseline = result["optimizer_settings"], reference["optimizer_settings"]
    if set(settings) != set(baseline):
        raise ValueError("Changed optimizer setting coverage.")
    for key in settings:
        if key == "callback":
            if settings[key] != "observing_callback":
                raise ValueError("Wrong optimizer observation callback.")
        elif settings[key] != baseline[key]:
            raise ValueError("Changed actual optimizer setting.")


def verify_result(result, request, arrays):
    if result["request"] != request or result["backend_seed"] != backend_seed(
        request["seed"]
    ):
        raise ValueError("Wrong actual diagnostic seed or request.")
    if result["initial_parameters"] != [
        x.hex() for x in request["start"]["parameters"]
    ]:
        raise ValueError("Changed optimizer start.")
    if result["tree"] != ringdown_tree(decode(result["parameters"])):
        raise ValueError("The fixed returned structure changed.")
    initial_prediction = evaluate_tree(
        ringdown_tree(request["start"]["parameters"]), arrays["time_s"]
    )
    initial_mse = math.fsum(
        float(x) ** 2 for x in arrays["observed"] - initial_prediction
    ) / len(initial_prediction)
    if not math.isclose(result["initial_loss"], initial_mse, rel_tol=1e-10, abs_tol=0):
        raise ValueError("Contradictory initial loss.")
    if result["loss"] > result["initial_loss"] or (
        result["loss"] == result["initial_loss"]
        and result["parameters"] != result["initial_parameters"]
    ):
        raise ValueError("Backend strict-improvement selection contradicted.")
    if result["rng_type"] != "Random.Xoshiro" or len(result["rng_before"]) != len(
        result["rng_after"]
    ):
        raise ValueError("Missing actual RNG state.")
    if not result["rng_before"] or any(
        not x.isdigit() for x in result["rng_before"] + result["rng_after"]
    ):
        raise ValueError("Invalid actual RNG state fields.")
    validate_plugin_records(result["plugins"], "baseline")
    if result["total_callback_count"] != result["fit_callback_count"] + 2:
        raise ValueError("Wrong fit/total callback accounting.")
    prediction = evaluate_tree(result["tree"], arrays["time_s"])
    native = decode(result["prediction"])
    _check_prediction_replay(prediction, native)
    residual = arrays["observed"] - native
    if not np.array_equal(
        residual.view(np.uint64), decode(result["residual"]).view(np.uint64)
    ):
        raise ValueError("Changed native residual.")
    loss = float(result["loss"])
    expected = math.fsum(float(x) ** 2 for x in residual) / len(residual)
    if not math.isfinite(loss) or not math.isclose(
        loss, expected, rel_tol=1e-10, abs_tol=0
    ):
        raise ValueError("Contradictory diagnostic MSE.")
    initial = np.asarray(request["start"]["parameters"])
    draws = [decode(x) for x in result["restart_draws"]]
    if len(draws) != 2 or len(result["restart_parameters"]) != 2:
        raise ValueError("Missing restart vectors.")
    expected_starts = [initial] + [
        np.where(initial == 0, d, initial * (1 + 0.5 * d)) for d in draws
    ]
    for i, start in enumerate(expected_starts):
        if i and not np.array_equal(start, decode(result["restart_parameters"][i - 1])):
            raise ValueError("Wrong restart derivation.")
        states = [s for s in result["states"] if s["local_index"] == i + 1]
        if (
            not states
            or states[0]["step"] != 0
            or not np.array_equal(decode(states[0]["parameters"]), start)
        ):
            raise ValueError("Wrong actual local optimizer start.")
        if any(s["kind"] != "BFGSState" for s in states):
            raise ValueError("Wrong actual optimizer path.")
    if result["termination"] != {
        "status": "unavailable",
        "reason": "backend_does_not_return_local_optim_results",
    }:
        raise ValueError("Unjustified optimizer termination claim.")
    candidate = {
        "tree": result["tree"],
        "complexity": 13,
        "loss": loss,
        "display_equation": "fixed ringdown diagnostic",
    }
    return diagnose_candidate(candidate, 0, 0, arrays)


def pair_differences(cells):
    if len(cells) != 48 or any(c["status"] != "completed" for c in cells):
        return None
    differences = []
    for i in range(0, 48, 2):
        low, high = sorted(cells[i : i + 2], key=lambda c: c["request"]["iterations"])
        if (
            low["request"]["iterations"] != 20
            or high["request"]["iterations"] != 100
            or any(
                low["request"][key] != high["request"][key] for key in ("seed", "start")
            )
        ):
            raise ValueError("Wrong diagnostic pair identity.")
        for field in ("rng_before", "rng_after", "restart_draws", "restart_parameters"):
            if low["result"][field] != high["result"][field]:
                raise ValueError("Paired RNG or restarts differ.")
        differences.append(
            {
                "start": low["request"]["start"]["name"],
                "seed": low["request"]["seed"],
                "loss_100_minus_20": high["result"]["loss"] - low["result"]["loss"],
                "curve_errors": {
                    grid: {
                        metric: high["diagnosis"]["curve_errors"][grid][metric]
                        - low["diagnosis"]["curve_errors"][grid][metric]
                        for metric in ("relative_rms", "relative_max")
                    }
                    for grid in ("training", "diagnostic")
                },
            }
        )
    return differences
