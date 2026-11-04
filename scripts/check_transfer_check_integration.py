"""Verify changed training data and a fresh repeat in three tiny technical workers."""

import argparse
from pathlib import Path

from run_transfer_check import load_driver

from ringdown_sr import transfer_check as control


def run(output):
    integration = control.load_module(
        control.ROOT / "scripts/check_search_duration_integration.py",
        "transfer_integration",
    )
    integration.driver = load_driver()
    integration.RUNTIME = control.RUNTIME
    integration.source_hashes = control.source_hashes
    integration.planned_cells = control.planned_cells
    integration.TECHNICAL_ITERATIONS = (2, 2, 2)
    integration.TECHNICAL_SEQUENCE = (0, 4, 0)
    integration.TECHNICAL_SCOPE = "three fresh fixed-300/5 two-iteration workers on separate eight-point y=1+t / 0.4+2t / 1+t; no scientific cells"
    original_arrays = integration.technical_arrays

    def arrays(cell):
        data = original_arrays(cell)
        if cell["signal"] == "amplitude":
            data["observed"] = 0.4 + 2 * data["time_s"]
            data["diagnostic_truth"] = 0.4 + 2 * data["diagnostic_time_s"]
        return data

    integration.technical_arrays = arrays
    integration.run(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
