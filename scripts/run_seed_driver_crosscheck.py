"""Run exactly two historical seed/driver crossovers on the original Manjaro host."""

import argparse
from pathlib import Path

from ringdown_sr.seed_driver_crosscheck import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outer-archive", type=Path, required=True)
    parser.add_argument("--transfer-archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.outer_archive, args.transfer_archive, args.output)
    print("Crossover completed: " + report["outcome"])


if __name__ == "__main__":
    main()
