"""Export parameter diagnostics from one completed schema-3 run; never search."""

import argparse
from pathlib import Path

from ringdown_sr.parameter_export import export_parameter_diagnostics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing complete schema-3 run")
    parser.add_argument(
        "--output", type=Path, required=True, help="New external directory"
    )
    args = parser.parse_args(argv)
    output = export_parameter_diagnostics(args.source, args.output)
    print(f"Parameter diagnostics exported: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
