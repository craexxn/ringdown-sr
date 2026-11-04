"""Check four tiny outer budgets at fixed 300/5 and a fresh repeat on separate eight-point data."""

import argparse
from pathlib import Path

from run_outer_search_ladder import load_driver

from ringdown_sr import outer_search_ladder as control


def run(output):
    integration = control.load_module(
        control.ROOT / "scripts/check_search_duration_integration.py",
        "ladder_integration",
    )
    integration.driver = load_driver()
    integration.RUNTIME = control.RUNTIME
    integration.source_hashes = control.source_hashes
    integration.planned_cells = control.planned_cells
    integration.TECHNICAL_ITERATIONS = (2, 3, 4, 5, 2)
    integration.TECHNICAL_SCOPE = "five fresh fixed-300/5 workers with outer budgets 2/3/4/5/2 on eight-point y=1+t; no scientific cells"
    integration.run(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
