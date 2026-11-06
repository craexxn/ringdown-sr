"""Exercise the restart lifecycle on eight technical points; never scientific data."""

import argparse
from pathlib import Path

from ringdown_sr.global_restarts import run, verify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, technical=True)
    verify(args.output, args.output.with_name(args.output.name + "-verification"))
    print("Three technical restart calls and read-only native verification passed.")
