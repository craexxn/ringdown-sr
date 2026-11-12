"""Frozen physical inputs and paired four-versus-two search budgets."""

import io

import numpy as np

from . import assessment_sources as sources
from . import global_restarts as restarts
from . import time_budget_profile as native
from .symbolic import ROOT

FORMAT = "ringdown-sr-restart-budget-1"
PLAN_COMMIT = "2cb96a7fef73a05e6c45564292dbce2c3d7f1583"
PLAN_HASHES = {
    "docs/restart_budget_plan.md": "c39861094e13f8cd3c261fb0fe20027ab0c4b888461cc0b7606861a5578ec3e3",
    "data/restart_budget_protocol.json": "fa83e312d2e4cf78c624a55ee9471a8cc2892ad6682034995bab7602c7e36f8a",
    "data/restart_budget_inputs.npz": "02d03ebf37be51613b4e6303a2806dcb308fc344c544e82ff0dfd0d82000c8f2",
    "scripts/prepare_restart_budget_inputs.py": "75b802ebaa98f745c3cd557f84e080ec17fe82da1450f7b35fea5fefe6f6e825",
}
BRIDGE = "scripts/restart_budget_bridge.py"
LEGACY = "scripts/seed_driver_crosscheck_bridge.py"
FIXTURES = ("fixture_a", "fixture_b")


def configuration():
    for name, digest in PLAN_HASHES.items():
        if sources.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError("Changed frozen restart-budget protocol/input: " + name)
    return sources.read_json((ROOT / "data/restart_budget_protocol.json").read_bytes())


def names(technical=False):
    return (
        list(FIXTURES) if technical else [s["name"] for s in configuration()["signals"]]
    )


def case(name, technical=False):
    if name not in names(technical):
        raise ValueError("Unknown fixed restart-budget signal or scope.")
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
    raw = (ROOT / "data/restart_budget_inputs.npz").read_bytes()
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
