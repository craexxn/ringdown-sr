"""Execute the frozen Manjaro comparison or verify an existing result read-only."""

import argparse
from pathlib import Path

from ringdown_sr.global_restarts import run, verify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("source", type=Path)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "run":
        run(args.output)
    else:
        verify(args.source, args.output)
