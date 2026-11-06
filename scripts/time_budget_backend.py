"""Inspect one explicit native time profile without fitting or searching."""

import argparse
from functools import partial
from pathlib import Path

from ringdown_sr import time_budget_profile as control
from ringdown_sr.pilot import _write_json
from ringdown_sr.representation_control import diagnose_candidate


def inspect(mode, condition, seed):
    control.checked_profile({"format": control.PROFILE_FORMAT, "condition": condition})
    backend = control.load_module(
        control.ROOT / "scripts/check_trigonometric_grammar_backend.py",
        "time_grammar_backend",
    )
    for name in (
        "FORMAT",
        "NATIVE_MODULE",
        "source_hashes",
        "verify_options",
        "common_options",
    ):
        setattr(backend, name, getattr(control, name))
    backend.CONDITIONS, backend.SEEDS = (condition,), (seed,)
    backend.expected_grammar_cases = lambda: [
        {**case, "condition": condition}
        for case in control.prior.expected_grammar_cases()
    ]
    backend.wrong_condition = lambda _: (
        "time" if condition == "iterations" else "iterations"
    )
    backend.SHOULD_SIMPLIFY = False
    backend.NATIVE_FILES += ("LocalOptimizerBudget.jl", "SearchTimeBudget.jl")
    backend.diagnose_candidate = partial(diagnose_candidate, extended_structure=True)
    jl = backend.native_runtime()
    hashes = control.checked_backend_sources(jl)
    result = backend.inspect(mode)
    if control.checked_backend_sources(jl) != hashes:
        raise ValueError("Native backend sources changed during preparation.")
    result["reviewed_backend_sources"] = hashes
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("options", "references"), required=True)
    parser.add_argument("--condition", choices=tuple(control.LIMITS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _write_json(args.output, inspect(args.mode, args.condition, args.seed))
