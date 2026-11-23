"""Run one separately bound white-noise scaling arm in a fresh Julia process."""

import argparse
import os
from pathlib import Path

from ringdown_sr.white_scaling_worker import worker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    allowed = os.sched_getaffinity(0)
    os.sched_setaffinity(0, {min(allowed)})
    worker(args.directory)
