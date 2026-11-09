"""Bind the frozen confirmation cases to the existing PR77 iteration worker."""

import os
from pathlib import Path

import numpy as np

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_confirmation_profile as profile
from ringdown_sr import seed_driver_crosscheck as cross
from ringdown_sr import time_budget_profile as native
from ringdown_sr.pilot import _provenance
from ringdown_sr.symbolic import ROOT

bridge = native.load_module(
    ROOT / "scripts/time_budget_bridge.py", "confirmation_native_bridge"
)
base_context = bridge.context


def checked_request(path, inputs, action, legacy, support):
    request = support.read_json(path.read_bytes())
    if request.get("scope") not in {"technical", "scientific"}:
        raise ValueError("Unknown confirmation scope.")
    technical = request["scope"] == "technical"
    plan = request["cell"]
    if sources.json_bytes(plan) not in [
        sources.json_bytes(p) for p in profile.plans(plan["signal"], technical)
    ]:
        raise ValueError("Unplanned confirmation cell.")
    if sources.json_bytes(request) != sources.json_bytes(
        profile.request_for(plan, request["inputs"], request["commit"], technical)
    ):
        raise ValueError("Changed confirmation request.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": request["commit"],
        "dirty": False,
    }:
        raise ValueError("Expected the exact clean confirmation checkout.")
    if action != "verify":
        if not technical:
            cross.scientific_platform()
        if Path(request["inputs"]) != inputs or len(os.sched_getaffinity(0)) != 1:
            raise ValueError("Changed input path or missing single-CPU limit.")
    with np.load(inputs, allow_pickle=False) as saved:
        arrays = {k: saved[k].copy() for k in saved.files}
    expected, _ = profile.inputs(plan["signal"], technical)
    if {k: sources.fingerprint(v) for k, v in arrays.items()} != {
        k: sources.fingerprint(v) for k, v in expected.items()
    }:
        raise ValueError("Wrong confirmation signal, input roles or Float64 bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def context(request, legacy):
    result = base_context(request, legacy)
    cell_for = legacy.cell_for

    def signal_cell(value):
        return {**cell_for(value), "signal": value["cell"]["signal"]}

    legacy.cell_for = signal_cell
    return result


if __name__ == "__main__":
    bridge.checked_request = checked_request
    bridge.context = context
    bridge.main()
