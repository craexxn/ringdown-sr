"""Check all four local profiles and a fresh repeat on separate eight-point data."""

import argparse
from pathlib import Path

from run_local_optimizer import load_driver

from ringdown_sr import local_optimizer as control


def run(output):
    integration = control.load_module(
        control.ROOT / "scripts/check_search_duration_integration.py",
        "local_integration",
    )
    integration.driver = load_driver()
    integration.RUNTIME = control.RUNTIME
    integration.source_hashes = control.source_hashes
    integration.planned_cells = control.planned_cells
    integration.TECHNICAL_ITERATIONS = (2,) * 5
    integration.TECHNICAL_SCOPE = "four local optimizer profiles and fresh baseline repeat; two outer iterations each on eight-point y=1+t; no scientific cells"
    integration.run(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
