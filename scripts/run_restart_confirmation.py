"""Run one frozen Manjaro section or read-verify existing confirmation evidence."""

import argparse
from pathlib import Path

from ringdown_sr.restart_confirmation import run, verify
from ringdown_sr.restart_confirmation_profile import names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--signal", choices=names(), required=True)
    single = commands.add_parser("verify")
    single.add_argument("source", type=Path)
    series = commands.add_parser("verify-series")
    series.add_argument("sources", nargs=3, type=Path)
    for command in (execute, single, series):
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "run":
        run(args.output, args.signal)
    elif args.action == "verify":
        verify([args.source], args.output)
    else:
        verify(args.sources, args.output, complete=True)
