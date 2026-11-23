"""Run or read-only verify the separately frozen candidate-selection pilot."""

import argparse

from ringdown_sr import offgrid_selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    action = (
        offgrid_selection.run
        if arguments.command == "run"
        else offgrid_selection.verify
    )
    report = action(arguments.source, arguments.output)
    print(
        f"Off-grid selection {report['status']}; no fits or searches executed.",
        flush=True,
    )


if __name__ == "__main__":
    main()
