"""Inspect five native seeds at fixed local 300/5 and fixed references without fitting."""

import argparse
from functools import partial
from pathlib import Path

from ringdown_sr import outer_search_ladder as control
from ringdown_sr.pilot import _write_json
from ringdown_sr.representation_control import diagnose_candidate


def inspect(mode):
    runtime = Path(__file__).resolve().parent
    path = runtime / "grammar_backend.py"
    if not path.exists():
        path = control.ROOT / "scripts/check_trigonometric_grammar_backend.py"
    backend = control.load_module(path, "ladder_grammar_backend")
    for name in (
        "FORMAT",
        "CONDITIONS",
        "SEEDS",
        "NATIVE_MODULE",
        "source_hashes",
        "verify_options",
        "common_options",
        "expected_grammar_cases",
    ):
        setattr(backend, name, getattr(control, name))
    backend.wrong_condition = lambda condition: "local_100_2"
    backend.SHOULD_SIMPLIFY = False
    backend.NATIVE_FILES += (control.NATIVE_MODULE + ".jl",)
    backend.diagnose_candidate = partial(diagnose_candidate, extended_structure=True)
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
        path.is_relative_to(control.ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new preflight output outside sources.")
    result = inspect(args.mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print(f"Outer ladder {args.mode} passed; no fit/search/optimization.")
