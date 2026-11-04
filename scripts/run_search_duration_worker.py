"""Delegate the grammar worker while verifying its actual outer search invocation."""

import argparse
import importlib
import json
from pathlib import Path

from ringdown_sr import search_duration as control
from ringdown_sr import symbolic
from ringdown_sr.duration_replay import verify_loss_replay
from ringdown_sr.pilot import _write_json
from ringdown_sr.prediction_reference import (
    PredictionVerificationError,
    verify_prediction,
)


def run(directory, control=control):
    directory = Path(directory).resolve()
    runtime = Path(__file__).resolve().parent
    control.verify_manifest(directory, runtime)
    request = json.loads((directory / "request.json").read_bytes())
    budget = symbolic.SearchBudget(**request["budget"])
    worker = control.load_module(
        runtime / "grammar_worker.py", "duration_grammar_worker"
    )
    for name in ("FORMAT", "checked_profile", "verify_manifest", "profile_parameters"):
        setattr(worker, name, getattr(control, name))
    worker.SHOULD_SIMPLIFY = False
    if hasattr(control, "NATIVE_MODULE"):
        worker.NATIVE_MODULE = control.NATIVE_MODULE
        worker.NATIVE_FILES += (control.NATIVE_MODULE + ".jl",)
    original_snapshot = symbolic._environment_snapshot
    original_replay = symbolic._verify_loss_replay
    original_prediction = symbolic._verify_prediction_replay
    module = original_backend = guard = None

    def snapshot(phase, *, julia_used):
        nonlocal module, original_backend, guard
        if phase == "before_fit":
            if guard is not None:
                raise ValueError("Repeated before-fit snapshot.")
            module = importlib.import_module("pysr.sr")
            original_backend = module.SymbolicRegression
            guard = control.SearchInvocationGuard(original_backend, budget.niterations)
            module.SymbolicRegression = guard
        elif phase == "after_search":
            if guard is None or module.SymbolicRegression is not guard:
                raise ValueError("Missing or replaced equation_search guard.")
            _write_json(directory / "search_invocation.json", guard.record())
            module.SymbolicRegression = original_backend
        return original_snapshot(phase, julia_used=julia_used)

    symbolic._environment_snapshot = snapshot
    symbolic._verify_loss_replay = verify_loss_replay
    symbolic._verify_prediction_replay = verify_prediction
    try:
        worker.run(directory)
    except PredictionVerificationError as error:
        _write_json(directory / "prediction_failure.json", error.evidence)
        raise
    finally:
        symbolic._environment_snapshot = original_snapshot
        symbolic._verify_loss_replay = original_replay
        symbolic._verify_prediction_replay = original_prediction
        if module is not None:
            module.SymbolicRegression = original_backend


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)
