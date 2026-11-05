"""Check both grammars at two tiny budgets and a repeated fresh control."""

import argparse
import copy
from pathlib import Path

import numpy as np
from run_search_duration import load_driver

from ringdown_sr import symbolic
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.search_duration import RUNTIME, planned_cells, source_hashes

driver = load_driver()
TECHNICAL_ITERATIONS = (2, 2, 3, 3, 2)
TECHNICAL_SCOPE = "five isolated two/three-search-iteration workers on eight-point y=1+t; no scientific control cells"
TECHNICAL_SEQUENCE = (0, 1, 3, 2, 0)


def technical_arrays(cell):
    """Keep integration searches separate from every scientific input bundle."""
    time = np.arange(8, dtype=np.float64) / 8
    inner = (np.arange(7, dtype=np.float64) + 0.5) / 8
    return {
        "time_s": time,
        "observed": 1 + time,
        "diagnostic_time_s": inner,
        "diagnostic_truth": 1 + inner,
    }


def run(output):
    output = Path(output).resolve()
    if (
        output.exists()
        or symbolic.ROOT.is_relative_to(output)
        or any(
            output.is_relative_to(symbolic.ROOT / name)
            for name in ("src", "scripts", "docs", "julia", ".git")
        )
    ):
        raise ValueError("Use a new technical output outside sources.")
    output.mkdir(parents=True)
    runtime = output / "runtime"
    runtime.mkdir()
    sources = source_hashes()
    for name, source in RUNTIME.items():
        (runtime / name).write_bytes((symbolic.ROOT / source).read_bytes())
    support = driver.BASE.load_support()
    probe = support.load_core_probe()
    initial = driver.BASE.core_snapshot(probe)
    tools = support.tool_hashes()
    preflight, consumed = driver.inspect_backend(
        output, runtime, initial, sources, support, probe, lambda: 600
    )
    files = {
        p.relative_to(output).as_posix(): _sha256(p.read_bytes())
        for p in runtime.iterdir()
        if p.is_file()
    }
    files.update({name: _sha256(value) for name, value in consumed.items()})

    def unchanged():
        if source_hashes() != sources or any(
            _sha256((output / name).read_bytes()) != digest
            for name, digest in files.items()
        ):
            raise ValueError("Technical worker consumed changed sources or artifacts.")

    results, signatures = [], []
    cells = planned_cells()
    sequence = [copy.deepcopy(cells[index]) for index in TECHNICAL_SEQUENCE]
    original = symbolic._run_worker
    try:
        for number, cell in enumerate(sequence, 1):
            arrays = technical_arrays(cell)
            for value in arrays.values():
                value.flags.writeable = False
            cell.update(number=number, directory=f"technical-{number:02d}")
            cell["budget"]["niterations"] = TECHNICAL_ITERATIONS[number - 1]
            symbolic._run_worker = driver.dispatch(
                runtime, cell, sources, files, output, lambda: 600, unchanged
            )
            result = symbolic.run_search_arm(
                arrays["time_s"],
                arrays["observed"],
                covariance=None,
                output=output / cell["directory"],
                budget=symbolic.SearchBudget(**cell["budget"]),
            )
            if result.status != "success":
                raise RuntimeError(
                    "Technical search duration worker failed; inspect worker.log."
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
            for name, digest in diagnosis["source_file_sha256"].items():
                relative = f"{cell['directory']}/{name}"
                if relative in files and files[relative] != digest:
                    raise ValueError("Technical input was changed.")
                files[relative] = digest
            signatures.append(
                support.signature(
                    support.read_json(
                        (output / cell["directory"] / "result.json").read_bytes()
                    )
                )
            )
            results.append(
                {
                    "condition": cell["condition"],
                    "budget": cell["budget"],
                    "candidate_count": diagnosis["candidate_count"],
                    "callback_calls_during_fit": diagnosis["callback_calls_during_fit"],
                    "callback_calls_total": diagnosis["callback_calls_total"],
                    "native_verification": diagnosis["native_verification"],
                    "search_invocation": diagnosis["search_invocation"],
                }
            )
            unchanged()
            print(
                f"Technical search duration worker verified: {cell['condition']}.",
                flush=True,
            )
    finally:
        symbolic._run_worker = original
    if signatures[0] != signatures[-1]:
        raise ValueError(
            "Repeated-control isolation changed the repeated unrestricted technical result."
        )
    unchanged()
    _write_json(
        output / "technical_report.json",
        {
            "status": "verified",
            "scope": TECHNICAL_SCOPE,
            "source_sha256": sources,
            "workers": results,
            "repeated_control_signature_equal": True,
        },
    )
    print("Search duration integration passed; no scientific series executed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
