"""Frozen untouched inputs and paired confirmation search budgets."""

import io

import numpy as np

from . import assessment_sources as sources
from . import global_restarts as restarts
from . import time_budget_profile as native
from .symbolic import ROOT

FORMAT = "ringdown-sr-restart-budget-confirmation-1"
PLAN_COMMIT = "352b7b5145ad8c8e735eea887a29744c97825c20"
PLAN_HASHES = {
    "docs/restart_budget_confirmation_plan.md": "a543cc6fb2e86a7eeb11ab2aefa977b11359cac2083664913c8b11951f27ad62",
    "data/restart_budget_confirmation_protocol.json": "22b1c960cc3b990139c6788ee3350460818ef8b047a0ae79130ee53fed8bde6d",
    "data/restart_budget_confirmation_inputs.npz": "7992cadd80fecb2a22a604071cf4e7364941218325d26809938f28923f031eb1",
    "scripts/prepare_restart_budget_confirmation_inputs.py": "2f465f6b696c366bf12fad84a6783c80d7f9ee9bea1eb90dd24f77f76f01161e",
}
BRIDGE = "scripts/restart_budget_confirmation_bridge.py"
LEGACY = "scripts/seed_driver_crosscheck_bridge.py"
FIXTURES = ("fixture_a", "fixture_b")


def configuration():
    for name, digest in PLAN_HASHES.items():
        if sources.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError(
                "Changed frozen restart-budget-confirmation protocol/input: " + name
            )
    return sources.read_json(
        (ROOT / "data/restart_budget_confirmation_protocol.json").read_bytes()
    )


def names(technical=False):
    return (
        list(FIXTURES) if technical else [s["name"] for s in configuration()["signals"]]
    )


def case(name, technical=False):
    if name not in names(technical):
        raise ValueError("Unknown fixed restart-budget-confirmation signal or scope.")
    if technical:
        offset = FIXTURES.index(name)
        return {
            "name": name,
            "blocks": 1,
            "seeds": [[73 + offset, 75 + offset, 77 + offset, 79 + offset]],
            "odd_block_order": ["R", "L"],
            "even_block_order": ["L", "R"],
        }
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
    raw = (ROOT / "data/restart_budget_confirmation_inputs.npz").read_bytes()
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
        if {
            key: sources.fingerprint(value) for key, value in actual.items()
        } != expected:
            raise ValueError("Restart-budget input/grid roles or Float64 bits changed.")
    return arrays, grid


def plans(name, technical=False):
    config, selected = configuration(), case(name, technical)
    arms = {arm["name"]: arm for arm in config["arms"]}
    result = []
    for block, seeds in enumerate(selected["seeds"], 1):
        order = selected["odd_block_order" if block % 2 else "even_block_order"]
        for arm in order:
            settings = arms[arm]
            iterations = (
                (1 if arm == "R" else 2) if technical else settings["iterations"]
            )
            for member in settings["seed_slots"]:
                result.append(
                    {
                        "number": len(result) + 1,
                        "signal": name,
                        "block": block,
                        "arm": arm,
                        "member": member,
                        "seed": seeds[member],
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
        "coordinate": configuration()["coordinate"],
        "bridge_sha256": sources.sha256((ROOT / LEGACY).read_bytes()),
        "adapter_sha256": sources.sha256((ROOT / BRIDGE).read_bytes()),
        "protocol_commit": PLAN_COMMIT,
        "protocol_sha256": PLAN_HASHES,
    }


def signal_seconds(technical=False):
    return native.LIMIT_SECONDS if technical else configuration()["signal_seconds"]
