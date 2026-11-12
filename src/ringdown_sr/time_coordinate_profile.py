"""Frozen paired development inputs in physical and stretched time coordinates."""

import io

import numpy as np

from . import assessment_sources as sources
from . import global_restarts as restarts
from . import time_budget_profile as native
from .symbolic import ROOT

FORMAT = "ringdown-sr-time-coordinate-1"
PLAN_COMMIT = "a77ee404d5d226544c6643d8500a9415631d9e16"
PLAN_HASHES = {
    "docs/time_coordinate_plan.md": "14bec2b231dbcfce279f1a23f0fc282bfc780fbded7a5e0030b4c75956b251cc",
    "data/time_coordinate_protocol.json": "aae61d04ac5ab9eaa0eba12290156ebee1e3a69213df36c8879a1ee53d309985",
    "data/time_coordinate_inputs.npz": "25ea57100763af6385df50c7de41f871e6d53fb76f51fd24b6fd01743085efd1",
    "scripts/prepare_time_coordinate_inputs.py": "fe1a1875e47707a31f932615f51ad242c0bf514f88008565f9294e6652a65691",
}
BRIDGE = "scripts/time_coordinate_bridge.py"
LEGACY = "scripts/seed_driver_crosscheck_bridge.py"
FIXTURES = ("fixture_a", "fixture_b")
SCALES = {"T": 1.0, "U": 32.0}


def configuration():
    for name, digest in PLAN_HASHES.items():
        if sources.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError("Changed frozen coordinate protocol/input: " + name)
    return sources.read_json((ROOT / "data/time_coordinate_protocol.json").read_bytes())


def names(technical=False):
    return (
        list(FIXTURES) if technical else [s["name"] for s in configuration()["signals"]]
    )


def case(name, technical=False):
    if name not in names(technical):
        raise ValueError("Unknown fixed coordinate signal or scope.")
    if technical:
        return {"name": name, "seeds": [73 + FIXTURES.index(name)], "blocks": 1}
    return next(s for s in configuration()["signals"] if s["name"] == name)


def inputs(name, technical=False):
    selected = case(name, technical)
    if technical:
        times = np.arange(8, dtype=np.float64) / 8
        inner = (np.arange(7, dtype=np.float64) + 0.5) / 8
        grid = restarts.grid(True)["time_s"]
        truth = (lambda t: 1 + t) if name == "fixture_a" else (lambda t: 2 - t)
        return (
            {
                "time_s": times,
                "observed": truth(times),
                "diagnostic_time_s": inner,
                "diagnostic_truth": truth(inner),
            },
            {"time_s": grid, "truth": truth(grid)},
        )
    raw = (ROOT / "data/time_coordinate_inputs.npz").read_bytes()
    with np.load(io.BytesIO(raw), allow_pickle=False) as saved:
        arrays = {
            key: saved[key if key.endswith("time_s") else name + "_" + key].copy()
            for key in ("time_s", "observed", "diagnostic_time_s", "diagnostic_truth")
        }
        grid = {
            "time_s": saved["irregular_time_s"].copy(),
            "truth": saved[name + "_irregular_truth"].copy(),
        }
    for actual, expected in ((arrays, selected["arrays"]), (grid, selected["grid"])):
        if {k: sources.fingerprint(v) for k, v in actual.items()} != expected:
            raise ValueError(
                "Coordinate physical input/grid roles or Float64 bits changed."
            )
    return arrays, grid


def search_inputs(name, arm, technical=False):
    if arm not in SCALES:
        raise ValueError("Unknown fixed coordinate arm.")
    arrays, grid = inputs(name, technical)
    result = {key: value.copy() for key, value in arrays.items()}
    if arm == "U":
        for key in ("time_s", "diagnostic_time_s"):
            result[key] = np.ldexp(result[key], 5)
        if not technical:
            expected = case(name)["normalized_times"]
            raw = (ROOT / "data/time_coordinate_inputs.npz").read_bytes()
            with np.load(io.BytesIO(raw), allow_pickle=False) as saved:
                for key, actual in (
                    ("time_u", result["time_s"]),
                    ("diagnostic_time_u", result["diagnostic_time_s"]),
                    ("irregular_time_u", np.ldexp(grid["time_s"], 5)),
                ):
                    if (
                        sources.fingerprint(actual) != expected[key]
                        or sources.fingerprint(saved[key]) != expected[key]
                    ):
                        raise ValueError(
                            "Changed exact coordinate transform or frozen points."
                        )
    for value in result.values():
        value.flags.writeable = False
    return result


def plans(name, technical=False):
    config, selected = configuration(), case(name, technical)
    result = []
    for block, seed in enumerate(selected["seeds"], 1):
        for arm in ("T", "U") if block % 2 else ("U", "T"):
            result.append(
                {
                    "number": len(result) + 1,
                    "signal": name,
                    "block": block,
                    "arm": arm,
                    "member": 0,
                    "seed": seed,
                    "condition": "iterations",
                    "niterations": 2 if technical else config["outer_iterations"],
                }
            )
    return result


def search_path(root, plan):
    if plan["arm"] not in SCALES:
        raise ValueError("Unknown fixed coordinate arm.")
    return root / ("search-" + plan["arm"] + ".npz")


def request_for(plan, inputs_path, commit, technical=False):
    return {
        "format": FORMAT + "-worker-request",
        "scope": "technical" if technical else "scientific",
        "commit": commit,
        "inputs": str(inputs_path),
        "cell": plan,
        "seed": plan["seed"],
        "niterations": plan["niterations"],
        "coordinate": {
            "arm": plan["arm"],
            "scale_hex": SCALES[plan["arm"]].hex(),
            "unit": "s",
            "physical_rule": "q(scale*t)",
        },
        "bridge_sha256": sources.sha256((ROOT / LEGACY).read_bytes()),
        "adapter_sha256": sources.sha256((ROOT / BRIDGE).read_bytes()),
        "protocol_commit": PLAN_COMMIT,
        "protocol_sha256": PLAN_HASHES,
    }


def signal_seconds(technical=False):
    return native.LIMIT_SECONDS if technical else configuration()["signal_seconds"]
