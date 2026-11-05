"""Run one transfer cell with unchanged duration replay checks."""

import argparse
from pathlib import Path

from ringdown_sr import transfer_check as control


def run(directory):
    runtime = Path(__file__).resolve().parent
    control.verify_manifest(directory, runtime)
    worker = control.load_module(
        runtime / "duration_worker.py", "transfer_duration_worker"
    )
    worker.run(directory, control=control)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)
