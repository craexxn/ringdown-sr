"""Audit controls, execute the frozen Manjaro comparison, or verify read-only."""

import argparse
from pathlib import Path

from ringdown_sr.iteration_time import run, verify
from ringdown_sr.time_control_import import audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    execute = commands.add_parser("run")
    execute.add_argument(
        "--mode", choices=("reuse_pr76", "fresh_all"), default="reuse_pr76"
    )
    execute.add_argument("--reason", required=True)
    check = commands.add_parser("verify")
    check.add_argument("source", type=Path)
    inspect = commands.add_parser("audit-controls")
    for command in (execute, check, inspect):
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--archive", type=Path, required=command is inspect)
        command.add_argument("--archive-sha256", required=command is inspect)
    args = parser.parse_args()
    if args.action == "run":
        run(
            args.output,
            mode=args.mode,
            reason=args.reason,
            archive=args.archive,
            archive_sha256=args.archive_sha256,
        )
    elif args.action == "verify":
        verify(
            args.source,
            args.output,
            archive=args.archive,
            archive_sha256=args.archive_sha256,
        )
    else:
        audit(args.archive, args.archive_sha256, args.output)
