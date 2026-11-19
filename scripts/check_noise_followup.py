"""Run or read-only verify the six-worker N128 follow-up technical preflight."""

import argparse
from pathlib import Path


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args(arguments)
    from ringdown_sr import noise_followup_technical as technical

    if args.verify is not None:
        technical.verify(args.verify)
    else:
        technical.run(args.output)
    print(
        "Follow-up technical preflight passed: six N128 ten-iteration workers "
        "and read-only replay."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
