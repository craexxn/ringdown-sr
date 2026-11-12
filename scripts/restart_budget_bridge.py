"""Bind both restart packages to the unchanged PR77 iteration worker."""

import os
from pathlib import Path

import numpy as np

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_budget_profile as profile
from ringdown_sr import seed_driver_crosscheck as cross
from ringdown_sr import time_budget_profile as native
from ringdown_sr.pilot import _provenance
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.symbolic import ROOT

bridge = native.load_module(
    ROOT / "scripts/time_budget_bridge.py", "restart_budget_native_bridge"
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
        raise ValueError("Unknown restart-budget scope.")
    technical = request["scope"] == "technical"
    plan = request["cell"]
    if sources.json_bytes(plan) not in [
        sources.json_bytes(value) for value in profile.plans(plan["signal"], technical)
    ]:
        raise ValueError("Unplanned restart-budget cell.")
    if sources.json_bytes(request) != sources.json_bytes(
        profile.request_for(plan, request["inputs"], request["commit"], technical)
    ):
        raise ValueError("Changed restart-budget request or coordinate binding.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": request["commit"],
        "dirty": False,
    }:
        raise ValueError("Expected the exact clean restart-budget checkout.")
    if action != "verify":
        if not technical:
            cross.scientific_platform()
        if Path(request["inputs"]) != inputs or len(os.sched_getaffinity(0)) != 1:
            raise ValueError("Changed input path or missing single-CPU limit.")
    with np.load(inputs, allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    expected, _ = profile.inputs(plan["signal"], technical)
    if {key: sources.fingerprint(value) for key, value in arrays.items()} != {
        key: sources.fingerprint(value) for key, value in expected.items()
    }:
        raise ValueError("Wrong restart-budget signal, input roles or Float64 bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def context(request, legacy):
    result = base_context(request, legacy)
    driver = result[1]
    plan = request["cell"]
    physical, _ = profile.inputs(plan["signal"], request["scope"] == "technical")
    driver.FS = 1.0 / (physical["time_s"][1] - physical["time_s"][0])
    cell_for = legacy.cell_for

    def signal_cell(value):
        return {**cell_for(value), "signal": value["cell"]["signal"]}

    def physical_diagnosis(candidate, index, selected, arrays, cell):
        if {key: sources.fingerprint(value) for key, value in arrays.items()} != {
            key: sources.fingerprint(value) for key, value in physical.items()
        }:
            raise ValueError("Native diagnosis received different physical inputs.")
        diagnosis = diagnose_candidate(
            candidate,
            index,
            selected,
            physical,
            "complexity_frequency",
            extended_structure=True,
        )
        diagnosis["parameter_match"] = {
            "status": "not_assessed",
            "reason": "no_restart_budget_parameter_rule",
        }
        diagnosis["coordinate"] = request["coordinate"]
        return diagnosis

    legacy.cell_for = signal_cell
    driver.diagnose_cell_candidate = physical_diagnosis
    return result


if __name__ == "__main__":
    bridge.checked_request = checked_request
    bridge.context = context
    bridge.clock_evidence = clock_evidence
    bridge.main()
