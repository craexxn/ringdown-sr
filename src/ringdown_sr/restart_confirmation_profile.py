"""Frozen independent confirmation inputs and paired search schedule."""

import io

import numpy as np

from . import assessment_sources as sources
from . import global_restarts as restarts
from . import time_budget_profile as native
from .symbolic import ROOT

FORMAT = "ringdown-sr-restart-confirmation-1"
PLAN_COMMIT = "a1f498ac29c8c261422c29daa24f9560359214b2"
PLAN_HASHES = {
    "docs/restart_confirmation_plan.md": "5431b9acd433272ba51e732bf28f92677a1bd0f43c3fc11120b05a91aa6ab89d",
    "data/restart_confirmation_protocol.json": "44d2a73a2189c5b4f06570c6abebcc8edceb2d1669925871c665f51520b1d6f9",
    "data/restart_confirmation_inputs.npz": "02d03ebf37be51613b4e6303a2806dcb308fc344c544e82ff0dfd0d82000c8f2",
    "scripts/prepare_restart_confirmation_inputs.py": "734f6be67af7bd5230be81e94a9584774bf4a406da677853c53112cc24c1b122",
}
BRIDGE = "scripts/restart_confirmation_bridge.py"
LEGACY = "scripts/seed_driver_crosscheck_bridge.py"
FIXTURES = ("fixture_a", "fixture_b")


def configuration():
    for name, digest in PLAN_HASHES.items():
        if sources.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError("Changed frozen confirmation protocol/input: " + name)
    return sources.read_json(
        (ROOT / "data/restart_confirmation_protocol.json").read_bytes()
    )


def names(technical=False):
    return (
        list(FIXTURES) if technical else [s["name"] for s in configuration()["signals"]]
    )


def case(name, technical=False):
    if name not in names(technical):
        raise ValueError("Unknown fixed confirmation signal or scope.")
    if technical:
        index = FIXTURES.index(name)
        return {"name": name, "seeds": [[73 + index, 75 + index]]}
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
    raw = (ROOT / "data/restart_confirmation_inputs.npz").read_bytes()
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
            raise ValueError("Confirmation input/grid role or Float64 bits changed.")
    return arrays, grid


def plans(name, technical=False):
    config = configuration()
    selected = case(name, technical)
    result = []
    for block, seeds in enumerate(selected["seeds"], 1):
        members = [
            ("R", member, seed, 2 if technical else config["restart_iterations"])
            for member, seed in enumerate(seeds)
        ]
        long = ("I", 0, seeds[0], 3 if technical else config["long_iterations"])
        order = [*members, long] if block % 2 else [long, *members]
        for arm, member, seed, iterations in order:
            result.append(
                {
                    "number": len(result) + 1,
                    "signal": name,
                    "block": block,
                    "arm": arm,
                    "member": member,
                    "seed": seed,
                    "condition": "iterations",
                    "niterations": iterations,
                }
            )
    return result


def request_for(plan, inputs_path, commit, technical=False):
    return {
        "format": FORMAT + "-worker-request",
        "scope": "technical" if technical else "scientific",
        "commit": commit,
        "inputs": str(inputs_path),
        "cell": plan,
        "seed": plan["seed"],
        "niterations": plan["niterations"],
        "bridge_sha256": sources.sha256((ROOT / LEGACY).read_bytes()),
        "adapter_sha256": sources.sha256((ROOT / BRIDGE).read_bytes()),
        "protocol_commit": PLAN_COMMIT,
        "protocol_sha256": PLAN_HASHES,
    }


def signal_seconds(technical=False):
    return native.LIMIT_SECONDS if technical else configuration()["signal_seconds"]
