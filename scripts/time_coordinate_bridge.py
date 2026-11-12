"""Bind both time coordinates to the unchanged PR77 iteration worker."""

import os
from pathlib import Path

import numpy as np

from ringdown_sr import assessment_sources as sources
from ringdown_sr import seed_driver_crosscheck as cross
from ringdown_sr import time_budget_profile as native
from ringdown_sr import time_coordinate_profile as profile
from ringdown_sr.pilot import _provenance
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.symbolic import ROOT

bridge = native.load_module(
    ROOT / "scripts/time_budget_bridge.py", "coordinate_native_bridge"
)
base_context = bridge.context
base_clock_evidence = bridge.clock_evidence


def clock_evidence(output, request, support):
    evidence = base_clock_evidence(output, request, support)
    if (
        request["cell"]["condition"] == "iterations"
        and evidence["reason"] == "iteration_reserve"
    ):
        evidence["reason"] = "iteration_limit"
    return evidence


def checked_request(path, inputs, action, legacy, support):
    request = support.read_json(path.read_bytes())
    if request.get("scope") not in {"technical", "scientific"}:
        raise ValueError("Unknown coordinate scope.")
    technical = request["scope"] == "technical"
    plan = request["cell"]
    if sources.json_bytes(plan) not in [
        sources.json_bytes(p) for p in profile.plans(plan["signal"], technical)
    ]:
        raise ValueError("Unplanned coordinate cell.")
    if sources.json_bytes(request) != sources.json_bytes(
        profile.request_for(plan, request["inputs"], request["commit"], technical)
    ):
        raise ValueError("Changed coordinate request or scaling binding.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": request["commit"],
        "dirty": False,
    }:
        raise ValueError("Expected the exact clean coordinate checkout.")
    if action != "verify":
        if not technical:
            cross.scientific_platform()
        if Path(request["inputs"]) != inputs or len(os.sched_getaffinity(0)) != 1:
            raise ValueError("Changed input path or missing single-CPU limit.")
    with np.load(inputs, allow_pickle=False) as saved:
        arrays = {k: saved[k].copy() for k in saved.files}
    expected = profile.search_inputs(plan["signal"], plan["arm"], technical)
    if {k: sources.fingerprint(v) for k, v in arrays.items()} != {
        k: sources.fingerprint(v) for k, v in expected.items()
    }:
        raise ValueError("Wrong coordinate signal, scale, input roles or Float64 bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def context(request, legacy):
    result = base_context(request, legacy)
    driver = result[1]
    plan = request["cell"]
    technical = request["scope"] == "technical"
    physical, _ = profile.inputs(plan["signal"], technical)
    search = profile.search_inputs(plan["signal"], plan["arm"], technical)
    driver.FS = 1.0 / (search["time_s"][1] - search["time_s"][0])
    cell_for = legacy.cell_for

    def signal_cell(value):
        return {**cell_for(value), "signal": value["cell"]["signal"]}

    def coordinate_diagnosis(candidate, index, selected, arrays, cell):
        if {k: sources.fingerprint(v) for k, v in arrays.items()} != {
            k: sources.fingerprint(v) for k, v in search.items()
        }:
            raise ValueError("Native diagnosis received different search coordinates.")
        diagnosis = diagnose_candidate(
            candidate,
            index,
            selected,
            physical,
            "time_stretch" if plan["arm"] == "U" else "complexity_frequency",
            extended_structure=True,
        )
        diagnosis["parameter_match"] = {
            "status": "not_assessed",
            "reason": "no_coordinate_development_parameter_rule",
        }
        diagnosis["coordinate"] = request["coordinate"]
        return diagnosis

    legacy.cell_for = signal_cell
    driver.diagnose_cell_candidate = coordinate_diagnosis
    return result


if __name__ == "__main__":
    bridge.checked_request = checked_request
    bridge.context = context
    bridge.clock_evidence = clock_evidence
    bridge.main()
