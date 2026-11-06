"""Prepare, run or read-verify one bound iteration/time-budget worker."""

import argparse
import math
import os
import resource
import signal
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ringdown_sr import seed_driver_crosscheck as cross
from ringdown_sr import symbolic
from ringdown_sr import time_budget_profile as control
from ringdown_sr.noiseless_control import fingerprint
from ringdown_sr.pilot import _json_bytes, _provenance, _sha256, _write_json

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "scripts/seed_driver_crosscheck_bridge.py"
FAILURES = control.load_module(
    ROOT / "scripts/global_restart_bridge.py", "time_failure_guards"
)


def cells(mode, technical=False):
    config = control.configuration()
    if mode not in ("reuse_pr76", "fresh_all"):
        raise ValueError("Choose one explicit frozen execution mode.")
    if technical:
        triples = (
            [("Z", "technical_timeout", 1000000)]
            if mode == "reuse_pr76"
            else [
                ("I", "iterations", 2),
                ("Z", "technical_timeout", 1000000),
                ("Z", "technical_reserve", 1),
                ("I", "iterations", 2),
            ]
        )
        return [
            {
                "number": i + 1,
                "block": 0,
                "seed": 73,
                "arm": arm,
                "condition": condition,
                "niterations": iterations,
            }
            for i, (arm, condition, iterations) in enumerate(triples)
        ]
    result = []
    for block, seed in enumerate(config["seeds"]):
        order = ("Z",) if mode == "reuse_pr76" else config["fresh_orders"][block]
        for arm in order:
            result.append(
                {
                    "number": len(result) + 1,
                    "block": block + 1,
                    "seed": seed,
                    "arm": arm,
                    "condition": "iterations" if arm == "I" else "time",
                    "niterations": config["iterations"]
                    if arm == "I"
                    else config["iteration_reserve"],
                }
            )
    return result


def request_for(cell, inputs, mode, commit, technical=False):
    return {
        "format": control.FORMAT,
        "scope": "technical" if technical else "scientific",
        "mode": mode,
        "commit": commit,
        "inputs": str(inputs),
        "cell": cell,
        "seed": cell["seed"],
        "niterations": cell["niterations"],
        "bridge_sha256": _sha256(LEGACY.read_bytes()),
        "adapter_sha256": _sha256(Path(__file__).read_bytes()),
        "protocol_commit": control.PLAN_COMMIT,
        "protocol_sha256": {
            control.PLAN: control.PLAN_SHA256,
            control.CONFIGURATION: control.CONFIGURATION_SHA256,
        },
    }


def checked_request(path, inputs, action, legacy, support):
    request = support.read_json(path.read_bytes())
    if request.get("scope") not in ("technical", "scientific"):
        raise ValueError("Unknown budget-comparison scope.")
    technical = request["scope"] == "technical"
    if _json_bytes(request.get("cell")) not in [
        _json_bytes(c) for c in cells(request["mode"], technical)
    ]:
        raise ValueError("Unplanned iteration/time cell.")
    if _json_bytes(request) != _json_bytes(
        request_for(
            request["cell"],
            request["inputs"],
            request["mode"],
            request["commit"],
            technical,
        )
    ):
        raise ValueError("Changed time-budget request.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": request["commit"],
        "dirty": False,
    }:
        raise ValueError(
            "Time-budget execution sources differ from the clean preparation."
        )
    if action != "verify":
        if not technical:
            cross.scientific_platform()
        if Path(request["inputs"]) != inputs or len(os.sched_getaffinity(0)) != 1:
            raise ValueError("Changed time input path or missing single-CPU limit.")
    with np.load(inputs, allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    expected = (
        {key: fingerprint(value) for key, value in legacy.technical_arrays().items()}
        if technical
        else {
            key: {"shape": shape, "dtype": "<f8", "sha256": digest}
            for key, (shape, digest) in legacy.ANCHOR.items()
        }
    )
    if {key: fingerprint(value) for key, value in arrays.items()} != expected:
        raise ValueError("Wrong time-budget input roles or Float64 bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def context(request, legacy):
    driver = control.load_driver()
    support = driver.BASE.load_support()
    probe = support.load_core_probe()
    condition = request["cell"]["condition"]
    backend = control.load_module(
        ROOT / "scripts/time_budget_backend.py", "time_preflight"
    )

    def cell_for(value):
        return {
            "number": 1,
            "directory": "worker",
            "condition": condition,
            "arm": condition,
            "grammar": "unrestricted",
            "signal": "anchor",
            "status": "planned",
            "budget": asdict(
                symbolic.SearchBudget(
                    seed=value["seed"], niterations=value["niterations"]
                )
            ),
        }

    def verify_preflight(
        options,
        references,
        initial,
        sources,
        current,
        current_driver,
        current_support,
        current_probe,
        seed,
    ):
        for mode, record in (("options", options), ("references", references)):
            if any(
                record[key] != expected
                for key, expected in {
                    "format": control.FORMAT,
                    "mode": mode,
                    "status": "verified",
                    "source_sha256": sources,
                    "reviewed_backend_sources": control.configuration()[
                        "reviewed_backend_sources"
                    ],
                }.items()
            ):
                raise ValueError("Invalid time-budget native preflight.")
            driver.verify_snapshots(record, initial, probe)
        if options["callback_calls"] != 0 or len(options["profiles"]) != 1:
            raise ValueError("Incomplete time-budget options coverage.")
        record = options["profiles"][0]
        if record["python_seed"] != seed:
            raise ValueError("Wrong time-budget seed.")
        control.verify_options(record, seed, condition, driver.BASE, support)
        expected_cases = [
            {**case, "condition": condition}
            for case in control.prior.expected_grammar_cases()
        ]
        if (
            len(references["cases"]) != 3
            or references["grammar_cases"] != expected_cases
            or {
                (case["condition"], case["frequency_hz"])
                for case in references["cases"]
            }
            != {(condition, f) for f in (250, 4346, 33018)}
        ):
            raise ValueError("Incomplete fixed time-budget references.")

    legacy.cell_for = cell_for
    legacy.inspect = lambda current, seed, mode: backend.inspect(mode, condition, seed)
    legacy.verify_preflight = verify_preflight
    return control, driver, support, probe


def clock_evidence(output, request, support):
    record = support.read_json((output / "worker/time_budget_clock.json").read_bytes())
    plan = request["cell"]
    count, populations = record["processed_population_cycles"], record["populations"]
    if (
        record["format"] != control.FORMAT
        or populations != 2
        or type(count) is not int
        or not 0 < count <= 2 * plan["niterations"]
        or record["checks"] != count
        or record["requested_iterations"] != plan["niterations"]
        or record["completed_outer_rounds"] != count // 2
        or record["residual_population_cycles"] != count % 2
        or record["iteration_limit_reached"] is not (count == 2 * plan["niterations"])
        or record["technical_counter_stop"] is not False
        or len(record["affinity"]) != 1
        or type(record["affinity"][0]) is not int
    ):
        raise ValueError("Invalid native time-budget counter or affinity evidence.")
    elapsed = record["elapsed_at_last_check_seconds"]
    for key in (
        "native_start_unix_seconds",
        "elapsed_at_last_check_seconds",
        "main_loop_call_wall_seconds",
    ):
        value = record[key]
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid observed native time.")
    drift = record["clock_difference_seconds"]
    if type(drift) not in (int, float) or not math.isfinite(drift) or abs(drift) > 1:
        raise ValueError("Native wall clock drift invalidates comparison.")
    limit = control.LIMITS[plan["condition"]]
    if record["timeout_reached"] is not (limit is not None and elapsed > limit):
        raise ValueError("Unconfirmed native search timeout.")
    if record["iteration_limit_reached"]:
        reason = "iteration_limit" if plan["arm"] == "I" else "iteration_reserve"
    elif record["timeout_reached"]:
        reason = "regular_timeout"
    else:
        raise ValueError("Native search stopped without its allowed stopping rule.")
    return {
        "reason": reason,
        "clock": record,
        "overshoot_seconds": max(0.0, elapsed - limit) if limit is not None else None,
    }


def verify_result(output, request, arrays, prepared, legacy, ctx):
    _, _driver, support, _ = ctx
    outcome = support.read_json((output / "outcome.json").read_bytes())
    if outcome["status"] == "worker_failed":
        FAILURES.verify_failed_worker(
            output,
            arrays,
            prepared,
            ctx,
            outcome["failure_kind"],
            condition=request["cell"]["condition"],
        )
    elif outcome["status"] == "completed":
        FAILURES.verify_result(output, request, arrays, prepared, legacy, ctx)
        if outcome["stop"] != clock_evidence(output, request, support):
            raise ValueError("Changed stopping evidence.")
    else:
        raise ValueError("Unfinished time-budget worker.")
    resources = support.read_json((output / "worker_resources.json").read_bytes())
    if (
        set(resources)
        != {"scope", "process_wall_seconds", "cpu_user_seconds", "cpu_system_seconds"}
        or resources["scope"] != "worker_launcher_and_waited_descendants"
    ):
        raise ValueError("Invalid worker resource scope.")
    if any(
        type(v) not in (int, float) or not math.isfinite(v) or v < 0
        for k, v in resources.items()
        if k != "scope"
    ):
        raise ValueError("Invalid worker resource measurement.")
    if resources != outcome["resources"]:
        raise ValueError("Worker resource binding changed.")
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("prepare", "run", "verify"), required=True)
    for name in ("output", "request", "inputs"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--verification", type=Path)
    parser.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args()
    remaining = args.deadline - time.monotonic()
    if not math.isfinite(remaining) or not 0 < remaining <= control.LIMIT_SECONDS:
        raise ValueError("Invalid time-budget total deadline.")
    legacy = control.load_module(LEGACY, "time_single_cell")
    initial_support = control.prior.load_module(
        ROOT / "scripts/repeat_symbolic_arm.py", "time_reader"
    )
    request, arrays = checked_request(
        args.request, args.inputs, args.action, legacy, initial_support
    )
    ctx = context(request, legacy)
    _, driver, support, _ = ctx
    with driver.WallTimeLimit(remaining) as clock:

        def interrupted(signum, frame):
            raise InterruptedError(
                f"Time-budget adapter interrupted by signal {signum}."
            )

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, interrupted)
        if args.action == "prepare":
            legacy.prepare(args.output, request, args.request, *ctx)
            return
        prepared = FAILURES.verify_prepared(
            args.output, args.request, args.inputs, request, legacy, ctx
        )
        if args.action == "verify":
            if args.verification is None or args.verification.exists():
                raise ValueError("Use a new verification destination.")
            outcome = verify_result(args.output, request, arrays, prepared, legacy, ctx)
            FAILURES.verify_prepared(
                args.output, args.request, args.inputs, request, legacy, ctx
            )
            clock.check()
            _write_json(args.verification, outcome)
            return
        if (args.output / "worker").exists():
            raise ValueError("Refuse to repeat a planned budget search.")
        launch = driver.launch
        measurements = []

        def measured_launch(*values, **keywords):
            if measurements:
                raise ValueError("More than one worker launch.")
            started, before = (
                time.monotonic(),
                resource.getrusage(resource.RUSAGE_CHILDREN),
            )
            try:
                return launch(*values, **keywords)
            finally:
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                measurements.append(
                    {
                        "scope": "worker_launcher_and_waited_descendants",
                        "process_wall_seconds": time.monotonic() - started,
                        "cpu_user_seconds": after.ru_utime - before.ru_utime,
                        "cpu_system_seconds": after.ru_stime - before.ru_stime,
                    }
                )
                _write_json(args.output / "worker_resources.json", measurements[0])

        driver.launch = measured_launch
        started = time.monotonic()
        try:
            legacy.run_cell(args.output, request, arrays, args.request, *ctx, clock)
            outcome = {
                "status": "completed",
                "stop": clock_evidence(args.output, request, support),
            }
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            metadata = support.read_json(
                (args.output / "worker/metadata.json").read_bytes()
            )
            kind = FAILURES.failure_kind(error, metadata)
            if kind is None:
                raise
            FAILURES.verify_failed_worker(
                args.output,
                arrays,
                prepared,
                ctx,
                kind,
                condition=request["cell"]["condition"],
            )
            outcome = {
                "status": "worker_failed",
                "failure_kind": kind,
                "error": f"{type(error).__name__}: {error}",
            }
        if len(measurements) != 1:
            raise ValueError("Missing actual worker resource evidence.")
        outcome.update(
            resources=measurements[0],
            adapter_run_wall_seconds=time.monotonic() - started,
        )
        FAILURES.verify_prepared(
            args.output, args.request, args.inputs, request, legacy, ctx
        )
        clock.check()
        _write_json(args.output / "outcome.json", outcome)


if __name__ == "__main__":
    main()
