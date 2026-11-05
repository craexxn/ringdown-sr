"""Compare two historical worker paths on eight technical points, never anchor data."""

import argparse
from pathlib import Path

import numpy as np

from ringdown_sr.pilot import _write_json
from ringdown_sr.search_duration import load_module
from ringdown_sr.seed_driver_crosscheck import (
    BRIDGE,
    HISTORIES,
    ROOT,
    call_bridge,
    comparison,
    git,
    read_json,
    source_hashes,
)


def run(output):
    output = Path(output).resolve()
    if (
        output.exists()
        or ROOT.is_relative_to(output)
        or any(
            output.is_relative_to(ROOT / n)
            for n in ("src", "scripts", "docs", "data", "julia", ".git")
        )
    ):
        raise ValueError("Use a new technical output outside sources.")
    helper = output.parent / ("." + output.name + "-checkouts")
    if helper.exists():
        raise ValueError("Helper directory already exists.")
    sources = source_hashes()
    bridge = load_module(ROOT / BRIDGE, "technical_crosscheck_bridge")
    driver = load_module(
        ROOT / "scripts/run_trigonometric_grammar.py", "technical_crosscheck_clock"
    )
    output.mkdir(parents=True)
    helper.mkdir()
    inputs = output / "technical.npz"
    np.savez(inputs, **bridge.technical_arrays())
    owned, results = [], []
    try:
        with driver.WallTimeLimit(3600) as clock:
            for kind, spec in HISTORIES.items():
                checkout = helper / kind
                git("worktree", "add", "--detach", str(checkout), spec["commit"])
                owned.append(checkout)
                request = output / (kind + "-request.json")
                _write_json(
                    request,
                    {
                        "scope": "technical",
                        "kind": kind,
                        "commit": spec["commit"],
                        "seed": 73,
                        "niterations": 2,
                        "inputs": str(inputs),
                        "bridge_sha256": sources[BRIDGE],
                    },
                )
                destination = output / kind
                call_bridge(checkout, "prepare", kind, destination, request, clock)
                call_bridge(checkout, "run", kind, destination, request, clock)
                results.append(read_json((destination / "verified.json").read_bytes()))
            compared = comparison(*results)
            if (
                not compared["all_search_features_equal"]
                or not compared["markers_equal"]
            ):
                raise ValueError(
                    "Historical technical worker fronts/options/callbacks differ."
                )
            _write_json(
                output / "technical_report.json",
                {
                    "status": "verified",
                    "scope": "two eight-point y=1+t workers; seed 73; two outer iterations; no scientific crossover",
                    "source_sha256": sources,
                    "comparison": compared,
                },
            )
    finally:
        for checkout in reversed(owned):
            git("worktree", "remove", str(checkout))
        if not any(helper.iterdir()):
            helper.rmdir()
    print(
        "Historical worker crossover integration passed; no scientific series executed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
