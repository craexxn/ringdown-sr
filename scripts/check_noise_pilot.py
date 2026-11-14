"""Run or read-only verify the bounded N=128 noise-pilot technical preflight."""

import argparse
from pathlib import Path

from ringdown_sr.noise_pilot_technical import run, verify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
    else:
        run(args.output)
    print(
        "Noise-pilot preflight passed: three N=128 ten-iteration workers and read-only replay."
    )
