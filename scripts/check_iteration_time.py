"""Check four tiny technical workers and read verification, never ringdown science."""

import argparse
from pathlib import Path

from ringdown_sr.iteration_time import run, verify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(
        args.output,
        mode="fresh_all",
        reason="Separate eight-point technical fixture",
        technical=True,
    )
    verify(args.output, args.output.with_name(args.output.name + "-verification"))
    print(
        "Four technical workers, stopping reasons, repeat control and read verification passed."
    )
