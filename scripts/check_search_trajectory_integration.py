"""Check passive observation in three fresh tiny off/on/off technical workers."""

import argparse
import copy
from pathlib import Path

import numpy as np
import run_search_trajectory as driver

from ringdown_sr import search_trajectory as policy
from ringdown_sr import symbolic
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
    sources = policy.source_hashes()
    runtime, files = driver.copy_runtime(output, sources)
    support = driver.BASE.load_support()
    probe = support.load_core_probe()
    initial = driver.BASE.core_snapshot(probe)
    tools = support.tool_hashes()
    preflight, consumed = driver.inspect_backend(
        output, runtime, initial, sources, support, probe, lambda: 600
    )
    files.update({name: _sha256(value) for name, value in consumed.items()})

    def unchanged():
        if policy.source_hashes() != sources or any(
            driver.checked_hash(output / name, lambda: None) != digest
            for name, digest in files.items()
        ):
            raise ValueError(
                "Technical observer consumed changed sources or artifacts."
            )

    times = np.arange(8, dtype=np.float64) / 8
    inner = (np.arange(7, dtype=np.float64) + 0.5) / 8
    arrays = {
        "time_s": times,
        "observed": 1 + times,
        "diagnostic_time_s": inner,
        "diagnostic_truth": 1 + inner,
    }
    for value in arrays.values():
        value.flags.writeable = False
    cells = policy.planned_cells()
    sequence = [copy.deepcopy(cells[index]) for index in (0, 1, 0)]
    documents, results = [], []
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
                    "Technical trajectory worker failed; inspect worker.log."
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
                    raise ValueError("Technical input changed before verification.")
                files[relative] = digest
            documents.append(
                support.read_json(
                    (output / cell["directory"] / "result.json").read_bytes()
                )
            )
            results.append(
                {
                    "observed": cell["observed"],
                    "budget": cell["budget"],
                    "candidate_count": diagnosis["candidate_count"],
                    "callback_calls_during_fit": diagnosis["callback_calls_during_fit"],
                    "callback_calls_total": diagnosis["callback_calls_total"],
                    "native_verification": diagnosis["native_verification"],
                    "observation": diagnosis["observation"],
                    "observation_timing_seconds": diagnosis[
                        "observation_timing_seconds"
                    ],
                    "offline_analysis_seconds": diagnosis["offline_analysis_seconds"],
                }
            )
            unchanged()
            print(
                f"Technical trajectory worker verified: observer={cell['observed']}.",
                flush=True,
            )
    finally:
        symbolic._run_worker = original
    pairs = [policy.compare_pair(documents[0], document) for document in documents[1:]]
    if len({row["callback_calls_total"] for row in results}) != 1:
        raise ValueError("Technical observer changed total callback counts.")
    if results[1]["observation"]["event_count"] != 4:
        raise ValueError(
            "Two technical search iterations must produce four observations."
        )
    unchanged()
    _write_json(
        output / "technical_report.json",
        {
            "status": "verified",
            "scope": "three isolated two-search-iteration off/on/off workers on eight-point y=1+t; no scientific control cells",
            "source_sha256": sources,
            "workers": results,
            "pair_comparisons": pairs,
            "off_on_off_exports_equal": True,
        },
    )
    print("Trajectory integration passed; no scientific series executed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
