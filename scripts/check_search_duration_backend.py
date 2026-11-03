"""Check ten native grammar profiles and twenty Python search budgets without fit."""

import argparse
from pathlib import Path

from ringdown_sr import search_duration as control
from ringdown_sr import symbolic
from ringdown_sr.pilot import _write_json


def inspect(mode):
    backend = control.load_module(
        Path(__file__).resolve().parent / "grammar_backend.py",
        "duration_grammar_backend",
    )
    for name in ("FORMAT", "SEEDS", "source_hashes"):
        setattr(backend, name, getattr(control, name))
    result = backend.inspect(mode)
    result["search_profiles"] = control.search_profiles() if mode == "options" else []
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("options", "references"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    path = args.output.resolve()
    if path.exists() or any(
        path.is_relative_to(symbolic.ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new preflight output outside sources.")
    result = inspect(args.mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print(f"Search duration {args.mode} passed; no fit/search/optimization.")
