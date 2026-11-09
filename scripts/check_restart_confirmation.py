"""Exercise two tiny signals and six workers, never confirmation science."""

import argparse
from pathlib import Path

from ringdown_sr.restart_confirmation import run, verify
from ringdown_sr.restart_confirmation_profile import names

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
    if report["verified_cells"] != 6 or report["transition_criterion_met"] is not None:
        raise ValueError("Technical confirmation scope changed.")
    print("Six tiny workers, both signals and read-only series verification passed.")
