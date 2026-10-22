"""Internal single-arm entry point; use ringdown_sr.symbolic.run_search_arm."""

import sys
from pathlib import Path

from ringdown_sr.symbolic import worker

if __name__ == "__main__":
    worker(Path(sys.argv[1]).resolve())
