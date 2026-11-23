"""Run or read-only verify eight N103 main-study technical workers."""

import argparse
from pathlib import Path


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args(arguments)
    from ringdown_sr import main_study_technical as technical

    if args.verify is not None:
        technical.verify(args.verify)
    else:
        technical.run(args.output)
    print(
        "Main-study technical preflight passed: eight N103 ten-iteration workers "
        "and read-only replay."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
