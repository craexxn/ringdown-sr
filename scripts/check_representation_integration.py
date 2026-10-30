"""Exercise three tiny profile workers on a linear signal, never the control series."""

import argparse
import importlib.util
from pathlib import Path

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _write_json
from ringdown_sr.representation_control import planned_cells, search_coordinates
from ringdown_sr.representation_profiles import RUNTIME_FILES, source_hashes

ROOT = symbolic.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if output.exists():
        raise FileExistsError(output)
    if ROOT.is_relative_to(output) or any(
        output.is_relative_to(ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Output must not overlap sources.")
    spec = importlib.util.spec_from_file_location(
        "representation_driver", ROOT / "scripts/run_representation_control.py"
    )
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    support = driver.BASE.load_support()
    probe = support.load_core_probe()
    initial = driver.BASE.core_snapshot(probe)
    sources, tools = source_hashes(), support.tool_hashes()
    output.mkdir(parents=True, exist_ok=False)
    runtime = output / "runtime"
    runtime.mkdir()
    for name, source in RUNTIME_FILES.items():
        (runtime / name).write_bytes((ROOT / source).read_bytes())
    original = symbolic._run_worker
    preflight = driver.inspect_backend(
        output, runtime, original, initial, sources, support, probe
    )
    # Acquisition grids only; a linear technical target replaces ringdown observations.
    grids = frozen_data()
    arrays = {
        "time_s": grids["time_s"],
        "diagnostic_time_s": grids["diagnostic_time_s"],
        "observed": 1 + grids["time_s"],
        "diagnostic_truth": 1 + grids["diagnostic_time_s"],
    }
    for value in arrays.values():
        value.flags.writeable = False
    results = []
    try:
        for cell in planned_cells()[:3]:
            cell["budget"]["niterations"] = 2
            symbolic._run_worker = driver.dispatch(runtime, cell, sources, original)
            values = search_coordinates(arrays, cell["condition"])
            run = symbolic.run_search_arm(
                values["time_s"],
                values["observed"],
                output=output / cell["directory"],
                budget=symbolic.SearchBudget(**cell["budget"]),
            )
            if run.status != "success":
                raise RuntimeError(
                    f"Technical profile worker failed: {run.output_directory}"
                )
            diagnosis = driver.verify_cell(
                output / cell["directory"],
                cell,
                arrays,
                support,
                probe,
                initial,
                tools,
                sources,
                preflight,
            )
            results.append(
                {
                    "condition": cell["condition"],
                    "budget": cell["budget"],
                    "candidate_count": diagnosis["candidate_count"],
                    "callback_calls_during_fit": diagnosis["callback_calls_during_fit"],
                    "backend_policy_verification": diagnosis[
                        "backend_policy_verification"
                    ],
                }
            )
            print(f"Technical profile worker verified: {cell['condition']}", flush=True)
    finally:
        symbolic._run_worker = original
    if source_hashes() != sources:
        raise ValueError("Technical integration sources changed.")
    _write_json(
        output / "technical_report.json",
        {
            "status": "verified",
            "scope": "three isolated two-iteration workers on y=1+t; no scientific control series",
            "source_sha256": sources,
            "workers": results,
        },
    )
    print("Representation integration passed; no scientific control cells executed.")


if __name__ == "__main__":
    main()
