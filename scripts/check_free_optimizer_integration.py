"""Check budget profiles and fresh 20-100-20 workers on a separate linear signal."""

import argparse
import copy
from pathlib import Path

import numpy as np
import run_free_optimizer_budget as driver

from ringdown_sr import symbolic
from ringdown_sr.free_optimizer_budget import RUNTIME, planned_cells, source_hashes
from ringdown_sr.pilot import _sha256, _write_json


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
    }
    files.update({name: _sha256(value) for name, value in consumed.items()})

    def unchanged():
        if source_hashes() != sources or any(
            _sha256((output / name).read_bytes()) != digest
            for name, digest in files.items()
        ):
            raise ValueError("Technical worker consumed changed sources or artifacts.")

    time = np.arange(8, dtype=np.float64) / 8
    inner = (np.arange(7, dtype=np.float64) + 0.5) / 8
    arrays = {
        "time_s": time,
        "observed": 1 + time,
        "diagnostic_time_s": inner,
        "diagnostic_truth": 1 + inner,
    }
    for value in arrays.values():
        value.flags.writeable = False
    results, signatures = [], []
    cells = planned_cells()
    sequence = [copy.deepcopy(cells[index]) for index in (0, 1, 0)]
    original = symbolic._run_worker
    try:
        for number, cell in enumerate(sequence, 1):
            cell.update(number=number, directory=f"technical-{number:02d}")
            cell["budget"]["niterations"] = 2
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
                    "Technical free-budget worker failed; inspect worker.log."
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
                    "iterations": cell["iterations"],
                    "budget": cell["budget"],
                    "candidate_count": diagnosis["candidate_count"],
                    "callback_calls_during_fit": diagnosis["callback_calls_during_fit"],
                    "callback_calls_total": diagnosis["callback_calls_total"],
                    "native_verification": diagnosis["native_verification"],
                }
            )
            unchanged()
            print(
                f"Technical free-budget worker verified: {cell['iterations']} iterations.",
                flush=True,
            )
    finally:
        symbolic._run_worker = original
    if signatures[0] != signatures[2]:
        raise ValueError(
            "A-B-A isolation changed the repeated 20-iteration technical result."
        )
    unchanged()
    _write_json(
        output / "technical_report.json",
        {
            "status": "verified",
            "scope": "three isolated two-search-iteration workers on eight-point y=1+t; no scientific control cells",
            "source_sha256": sources,
            "workers": results,
            "repeated_20_signature_equal": True,
        },
    )
    print("Free optimizer-budget integration passed; no scientific series executed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
