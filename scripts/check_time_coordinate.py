"""Exercise two tiny signals and four workers, never time-coordinate science."""

import argparse
from pathlib import Path

from ringdown_sr.time_coordinate import run, verify
from ringdown_sr.time_coordinate_profile import names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    roots = []
    for name in names(technical=True):
        root = args.output.with_name(args.output.name + "-" + name)
        run(root, name, technical=True)
        verify([root], root.with_name(root.name + "-verification"))
        roots.append(root)
    report = verify(roots, args.output, complete=True)
    if report["verified_cells"] != 4 or report["development_decision"] is not None:
        raise ValueError("Technical time-coordinate scope changed.")
    if any(
        cell["status"] != "completed"
        or cell["stop"] != "iteration_limit"
        or cell["completed_outer_rounds"] != cell["plan"]["niterations"]
        or not cell["costs"]["callback_calls_during_fit"]
        for section in report["sections"]
        for cell in section["cells"]
    ):
        raise ValueError("Every tiny worker must complete its actual iteration budget.")
    print("Four tiny workers, both signals and read-only series verification passed.")
