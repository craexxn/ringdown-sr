"""Run one fresh time-budget cell with unchanged tree/loss replay contracts."""

import argparse
import importlib
import json
import os
from pathlib import Path

from ringdown_sr import symbolic
from ringdown_sr import time_budget_profile as control
from ringdown_sr.duration_replay import verify_loss_replay
from ringdown_sr.pilot import _write_json
from ringdown_sr.prediction_reference import (
    PredictionVerificationError,
    verify_prediction,
)


def run(directory):
    directory = Path(directory).resolve()
    runtime = Path(__file__).resolve().parent
    control.verify_manifest(directory, runtime)
    request = json.loads((directory / "request.json").read_bytes())
    budget = symbolic.SearchBudget(**request["budget"])
    if len(os.sched_getaffinity(0)) != 1:
        raise ValueError("Time-budget workers require one allowed CPU.")
    worker = control.load_module(runtime / "grammar_worker.py", "time_grammar_worker")
    for name in (
        "FORMAT",
        "checked_profile",
        "verify_manifest",
        "profile_parameters",
        "NATIVE_MODULE",
    ):
        setattr(worker, name, getattr(control, name))
    worker.SHOULD_SIMPLIFY = False
    worker.NATIVE_FILES += (
        "LocalOptimizerBudget.jl",
        "SearchTimeBudget.jl",
        "SearchBudgetClock.jl",
    )
    original_snapshot = symbolic._environment_snapshot
    original_replay = symbolic._verify_loss_replay
    original_prediction = symbolic._verify_prediction_replay
    module = original_backend = guard = None
    initial_runtime = None

    def snapshot(phase, *, julia_used):
        nonlocal module, original_backend, guard, initial_runtime
        from juliacall import Main as jl

        control.checked_backend_sources(jl)
        actual_runtime = control.checked_runtime(jl)
        if phase == "before_fit":
            if guard is not None:
                raise ValueError("Repeated time-budget fit boundary.")
            module = importlib.import_module("pysr.sr")
            original_backend = module.SymbolicRegression
            guard = control.SearchInvocationGuard(original_backend, budget.niterations)
            module.SymbolicRegression = guard
            jl.SearchBudgetClock.configure()
            initial_runtime = actual_runtime
            _write_json(directory / "time_budget_runtime.json", actual_runtime)
        elif phase == "after_search":
            if guard is None or module.SymbolicRegression is not guard:
                raise ValueError("Missing time-budget invocation guard.")
            if actual_runtime != initial_runtime:
                raise ValueError("Native runtime changed during the search.")
            _write_json(directory / "search_invocation.json", guard.record())
            record = jl.SearchBudgetClock.record()
            _write_json(
                directory / "time_budget_clock.json",
                {
                    "format": control.FORMAT,
                    "affinity": sorted(os.sched_getaffinity(0)),
                    "budget_runtime": actual_runtime,
                    **{str(key): getattr(record, str(key)) for key in jl.keys(record)},
                },
            )
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
