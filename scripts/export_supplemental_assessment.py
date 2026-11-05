"""Export retrospective curve grades without starting scientific workers."""

import argparse
from pathlib import Path

from ringdown_sr.supplemental_assessment import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", action="append", default=[], metavar="SERIES=PATH")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    args = parser.parse_args()
    archives = {}
    for item in args.archive:
        name, separator, path = item.partition("=")
        if not separator or not name or not path or name in archives:
            parser.error("Each --archive requires a distinct SERIES=PATH.")
        archives[name] = Path(path)
    result = run(archives, args.output, seconds=args.timeout_seconds)
    print(
        f"Assessment export completed; corpus {result['corpus_status']}; see {args.output}."
    )


if __name__ == "__main__":
    main()
