"""Compare exact tiny-fixture search prefixes under three stopping profiles."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from ringdown_sr import time_budget_profile as profile
from ringdown_sr.pilot import _write_json
from ringdown_sr.symbolic import ROOT, SearchBudget, _stop_worker


def worker(kind, output):
    import numpy as np
    import pysr
    from juliacall import Main as jl
    from juliacall import convert

    from ringdown_sr.constant_diagnostic import backend_seed

    if len(os.sched_getaffinity(0)) != 1:
        raise ValueError("Prefix probes require one allowed CPU.")
    hashes = profile.checked_backend_sources(jl)
    runtime = profile.checked_runtime(jl)
    for name in (
        "RingdownSRLoss",
        "RingdownSRSearch",
        "RepresentationProfiles",
        "FreeOptimizerBudget",
        "TrigonometricGrammar",
        "LocalOptimizerBudget",
        "SearchTimeBudget",
        "SearchBudgetClock",
        "SearchTrajectory",
    ):
        jl.include(str(ROOT / f"julia/src/{name}.jl"))
    times = np.arange(8, dtype=np.float64) / 8
    array = lambda values: convert(jl.Array[jl.Float64], values)
    jl.RingdownSRSearch.bind_context(array(times), array(1 + times), None)
    budget = SearchBudget(seed=73, niterations=1000000 if kind == "time" else 3)
    if kind == "legacy":
        parameters = profile.prior.profile_parameters(budget, "local_300_5")
        jl.LocalOptimizerBudget.configure(
            "local_300_5", backend_seed(73), should_simplify=False
        )
    else:
        parameters = profile.profile_parameters(budget, kind)
        jl.SearchTimeBudget.configure(kind, backend_seed(73), should_simplify=False)
    jl.seval(r"""
    const PREFIX_EVENTS = String[]
    function capture_budget_prefix(state, options)
        hall = only(state.halls_of_fame)
        record = (;
            index=length(PREFIX_EVENTS) + 1,
            populations=[[SearchTrajectory.raw_member(m, options) for m in p.members]
                for p in only(state.last_pops)],
            hall_of_fame=[(; slot=i, member=SearchTrajectory.raw_member(hall.members[i], options))
                for i in eachindex(hall.exists) if hall.exists[i]],
            native_callbacks=RingdownSRSearch.CALLS[],
        )
        push!(PREFIX_EVENTS, String(SearchTrajectory.json_line(record)))
        return nothing
    end
    """)
    # A deterministic test-only stop after four processed population outputs.
    # All profiles still have a further iteration available at this boundary.
    jl.SearchBudgetClock.configure(
        technical_checks=4, observer=jl.capture_budget_prefix
    )
    model = pysr.PySRRegressor(
        **parameters, output_directory=str(output / "pysr"), run_id="prefix"
    )
    model.fit(
        times[:, None], 1 + times, variable_names=["t"], X_units=["s"], y_units="1"
    )
    clock = jl.SearchBudgetClock.record()
    record = {str(key): getattr(clock, str(key)) for key in jl.keys(clock)}
    if (
        record["checks"] != 4
        or not record["technical_counter_stop"]
        or record["timeout_reached"]
    ):
        raise ValueError("The deterministic probe did not stop at its fixed counter.")
    events = [json.loads(str(event)) for event in jl.PREFIX_EVENTS]
    if len(events) != 4 or profile.checked_backend_sources(jl) != hashes:
        raise ValueError("Invalid or changed deterministic probe evidence.")
    counterchecks = jl.seval("""
    let original = SearchBudgetClock.OBSERVATION[], results = []
        try
            for jump in (0.0, -10.0, 10.0)
                # A private snapshot with exactly one processed population:
                # test both clock directions before the very first check.
                o = typeof(original)((getfield(original, key)
                    for key in fieldnames(typeof(original)))...)
                o.state = (; cycles_remaining=[o.iterations * o.populations - 1])
                o.checks = 1
                o.last_tick = o.first_tick
                o.last_elapsed = o.first_elapsed
                o.loop_start_wall -= jump
                SearchBudgetClock.OBSERVATION[] = o
                accepted = try
                    SearchBudgetClock.record()
                    true
                catch caught
                    occursin("wall clock", sprint(showerror, caught)) || rethrow()
                    false
                end
                accepted == iszero(jump) || error("First-check clock counterexample failed.")
                push!(results, (; jump_seconds=jump, accepted))
            end
        finally
            SearchBudgetClock.OBSERVATION[] = original
        end
        results
    end
    """)
    clock_checks = [
        {str(key): getattr(item, str(key)) for key in jl.keys(item)}
        for item in counterchecks
    ]
    _write_json(
        output / "prefix.json",
        {
            "format": "ringdown-sr-time-prefix-probe-1",
            "scope": "eight_point_linear_technical_fixture_only",
            "profile": kind,
            "parameters": parameters,
            "backend_sources": hashes,
            "runtime": runtime,
            "events": events,
            "clock": record,
            "first_check_clock_counterchecks": clock_checks,
        },
    )


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.environ.update(profile.JULIA_THREADS)
    records = []
    for kind in ("legacy", "iterations", "time"):
        destination = output / kind
        destination.mkdir()
        command = [
            sys.executable,
            str(ROOT / "scripts/run_python.py"),
            str(Path(__file__).resolve()),
            "--worker",
            kind,
            "--output",
            str(destination),
        ]
        with (destination / "worker.log").open("wb") as log:
            child = subprocess.Popen(
                command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
            try:
                if child.wait(timeout=300):
                    raise RuntimeError(
                        "Prefix probe failed; inspect "
                        + str(destination / "worker.log")
                    )
            except BaseException:
                _stop_worker(child)
                raise
        records.append(json.loads((destination / "prefix.json").read_bytes()))
    if not all(record["events"] == records[0]["events"] for record in records[1:]):
        raise ValueError(
            "Time profile or high reserve changed the observed search prefix."
        )
    _write_json(
        output / "comparison.json",
        {
            "status": "verified",
            "scope": "technical_only; no equality claim for timed final fronts",
            "profiles": [record["profile"] for record in records],
            "identical_population_hof_callback_events": 4,
            "search_calls": 3,
        },
    )
    print(
        "Three tiny native prefixes match: populations, Hall of Fame and callback counts."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--worker", choices=("legacy", "iterations", "time"))
    args = parser.parse_args()
    worker(args.worker, args.output) if args.worker else run(args.output)
