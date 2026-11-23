"""Frozen small scaling experiment, independent replay and complete exports."""

import csv
import io
import math
import os
import resource
import signal as os_signal
import subprocess
import sys
import time
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import symbolic
from . import white_scaling_fixed as fixed
from . import white_scaling_worker as worker
from .pilot import _provenance, _sha256, _utc_now, _write_json

FORMAT = "ringdown-sr-white-scaling-pilot-1"
PLAN = "docs/white_loss_scaling_plan.md"
PLAN_SHA256 = "3daa4d9c7701a8a99f841a5dc27cc3a7ae3cdbcbde1bbc8cd3f51eef2f202378"
NOISE_SEEDS = (2026112301, 2026112302)
SEARCH_SEEDS = (2026112311, 2026112312, 2026112313)
AMPLITUDE = 11 / 12
SIGMA = AMPLITUDE * 0.05
LIMIT_SECONDS = 21600
EXPORT_SECONDS = 3600
SERIES_WALL_SCOPE = (
    "after_input_preparation_through_terminal_measurement_excluding_status_write"
)
FIXED_WALL_SCOPE = (
    "launcher_entry_through_terminal_measurement_excluding_call_record_write"
)
SERIES_CPU_SCOPE = "self_plus_reaped_children"
FIXED_CPU_SCOPE = "reaped_children"


def signal(times):
    return (
        AMPLITUDE * np.exp(-times / (1 / 150)) * np.cos(2 * np.pi * 265 * times + 0.25)
    )


def data():
    """Generate new development noise and separate truth-only evaluation arrays."""
    times = np.arange(128, dtype=np.float64) / 4096
    regular = np.linspace(times[0], times[-1], 889)
    irregular = np.sort(
        np.random.Generator(np.random.PCG64(2026112391)).uniform(
            times[0], times[-1], 1024
        )
    )
    return {
        "time_s": times,
        "truth": signal(times),
        "regular_time_s": regular,
        "regular_truth": signal(regular),
        "irregular_time_s": irregular,
        "irregular_truth": signal(irregular),
        **{
            f"observed_{i + 1}": signal(times)
            + SIGMA * np.random.Generator(np.random.PCG64(seed)).standard_normal(128)
            for i, seed in enumerate(NOISE_SEEDS)
        },
    }


def starts(observed):
    return [
        [
            float(np.max(np.abs(observed))),
            -1 / tau,
            2 * math.pi * frequency,
            math.pi / 2,
        ]
        for frequency in (128.0, 512.0)
        for tau in ((128 / 4096) / 8, (128 / 4096) / 2)
    ]


def cells():
    result = []
    for case in (1, 2):
        for index, seed in enumerate(SEARCH_SEEDS):
            arms = worker.ARMS[index:] + worker.ARMS[:index]
            for arm in arms:
                result.append(
                    {
                        "id": f"white-{case:02d}-seed-{seed}-{arm}",
                        "case": case,
                        "seed": seed,
                        "arm": arm,
                        "repeat": False,
                    }
                )
    result.extend(
        {**cell, "id": cell["id"] + "-repeat", "repeat": True} for cell in result[:3]
    )
    return result


def _read(path):
    return sources.read_json(Path(path).read_bytes())


def _finite_cost(value, name):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("Expected a finite nonnegative measured cost: " + name)
    return value


def _completed_costs(record, *, wall_scope, cpu_scope):
    """Accept only complete measurements with their actual, declared scopes."""
    if (
        record.get("status") != "completed"
        or record.get("cpu_measurement_complete") is not True
        or record.get("wall_scope") != wall_scope
        or record.get("cpu_scope") != cpu_scope
        or "error" in record
    ):
        raise ValueError("Incomplete or contradictory measured cost scope.")
    dates = []
    for key in ("started_at", "finished_at"):
        value = record.get(key)
        if type(value) is not str:
            raise ValueError("Missing terminal measurement timestamp.")
        try:
            date = datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError("Invalid terminal measurement timestamp.") from error
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError("Measurement timestamps must include their timezone.")
        dates.append(date)
    if dates[1] < dates[0]:
        raise ValueError("Terminal timestamp precedes measurement start.")
    return {
        "wall_seconds": _finite_cost(record.get("wall_seconds"), "wall_seconds"),
        "cpu_user_seconds": _finite_cost(
            record.get("cpu_user_seconds"), "cpu_user_seconds"
        ),
        "cpu_system_seconds": _finite_cost(
            record.get("cpu_system_seconds"), "cpu_system_seconds"
        ),
        "wall_scope": wall_scope,
        "cpu_scope": cpu_scope,
        "cpu_measurement_complete": True,
    }


def _series_costs(status):
    if (
        set(status)
        != {
            "format",
            "status",
            "completed_fixed",
            "completed_search",
            "stage",
            "current_cell",
            "started_at",
            "finished_at",
            "wall_seconds",
            "wall_scope",
            "cpu_scope",
            "cpu_measurement_complete",
            "cpu_user_seconds",
            "cpu_system_seconds",
        }
        or status.get("format") != FORMAT
        or type(status.get("completed_fixed")) is not int
        or status["completed_fixed"] != 18
        or type(status.get("completed_search")) is not int
        or status["completed_search"] != 21
        or status.get("stage") != "search"
        or status.get("current_cell") != cells()[-1]["id"]
    ):
        raise ValueError(
            "Incomplete pilot terminal record; no completed-series claim is permitted."
        )
    return _completed_costs(
        status, wall_scope=SERIES_WALL_SCOPE, cpu_scope=SERIES_CPU_SCOPE
    )


def _fixed_costs(record):
    if (
        set(record)
        != {
            "format",
            "status",
            "returncode",
            "started_at",
            "finished_at",
            "wall_seconds",
            "wall_scope",
            "cpu_scope",
            "cpu_measurement_complete",
            "cpu_user_seconds",
            "cpu_system_seconds",
        }
        or record.get("format") != FORMAT + "-fixed-call-1"
        or type(record.get("returncode")) is not int
        or record["returncode"] != 0
    ):
        raise ValueError("Incomplete fixed-worker terminal record.")
    return _completed_costs(
        record, wall_scope=FIXED_WALL_SCOPE, cpu_scope=FIXED_CPU_SCOPE
    )


def _source_inventory(root):
    root = Path(root).absolute()
    if root != root.resolve() or not root.is_dir():
        raise ValueError(
            "Expected an existing source directory without symlink parents."
        )
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Source inventory contains a non-regular artifact.")
        result[path.relative_to(root).as_posix()] = (
            "file" if path.is_file() else "directory"
        )
    return result


def _bind_sources(root, consumed):
    """Bind the entire source inventory and exact bytes before verification."""
    root = Path(root).absolute()
    inventory = _source_inventory(root)
    hashes = {}
    for name, kind in inventory.items():
        if kind == "file":
            raw = (root / name).read_bytes()
            consumed.add(root / name, raw)
            hashes[name] = _sha256(raw)

    def inventory_unchanged():
        if _source_inventory(root) != inventory:
            raise ValueError("Source inventory changed during consumption.")

    consumed.callbacks.append(inventory_unchanged)
    manifest = sources.read_json(consumed.files[root / "manifest.json"])
    for name, expected in manifest["sources"].items():
        relative = sources.safe_name(name)
        path = symbolic.ROOT / relative
        if path.is_symlink() or path.resolve() != path:
            raise ValueError("Changed source-code path.")
        raw = path.read_bytes()
        if _sha256(raw) != expected:
            raise ValueError("Changed bound implementation source.")
        consumed.add(path, raw)
    consumed.check()
    return hashes


def evaluate_grid(tree, times, truth):
    """Preserve domain failures as outcomes, without hiding malformed trees."""
    try:
        prediction = symbolic.evaluate_tree(tree, times)
    except ValueError as error:
        if str(error) != "Tree prediction is not finite.":
            raise
        prediction = np.empty(len(times), dtype=np.float64)
        for index, value in enumerate(times):
            try:
                prediction[index] = symbolic.evaluate_tree(tree, [value])[0]
            except ValueError as point_error:
                if str(point_error) != "Tree prediction is not finite.":
                    raise
                prediction[index] = np.nan
    failed = int(np.count_nonzero(~np.isfinite(prediction)))
    record = {
        "status": "nonfinite_prediction" if failed else "finite",
        "nonfinite_count": failed,
        "rmse_over_a": None,
        "max_over_a": None,
    }
    if failed:
        return prediction, record
    with np.errstate(over="ignore", invalid="ignore"):
        residual = prediction - truth
        maximum = float(np.max(np.abs(residual)))
        rmse = (
            0.0
            if maximum == 0
            else maximum
            * math.sqrt(
                math.fsum(float(x) ** 2 for x in residual / maximum) / len(residual)
            )
        )
        metrics = (rmse / AMPLITUDE, maximum / AMPLITUDE)
    if all(math.isfinite(value) for value in metrics):
        record.update(rmse_over_a=metrics[0], max_over_a=metrics[1])
    else:
        record["status"] = "metric_out_of_float64_range"
    return prediction, record


def _sources():
    if _sha256((symbolic.ROOT / PLAN).read_bytes()) != PLAN_SHA256:
        raise ValueError("The frozen scaling protocol changed.")
    return worker.source_hashes()


def prepare(output):
    """Exclusively reserve every input before the first scientific operation."""
    output = Path(output).resolve()
    provenance = _provenance()
    if provenance["git"]["dirty"]:
        raise ValueError(
            "Commit the implementation before preparing scientific inputs."
        )
    sources = _sources()
    output.mkdir(parents=True, exist_ok=False)
    arrays = data()
    np.savez(output / "inputs.npz", **arrays)
    manifest = {
        "format": FORMAT,
        "created_at": _utc_now(),
        "plan_sha256": PLAN_SHA256,
        "sources": sources,
        "provenance": provenance,
        "cells": cells(),
        "input_sha256": _sha256((output / "inputs.npz").read_bytes()),
        "sigma_hex": SIGMA.hex(),
        "scale_hex": (1 / (SIGMA * SIGMA)).hex(),
    }
    for cell in cells():
        for stage in ("search",) if cell["repeat"] else ("fixed", "search"):
            directory = output / stage / cell["id"]
            worker.prepare_member(
                directory,
                arrays["time_s"],
                arrays[f"observed_{cell['case']}"],
                arm=cell["arm"],
                sigma=SIGMA,
                seed=cell["seed"],
            )
            if stage == "fixed":
                _write_json(
                    directory / "fixed_request.json",
                    {
                        "format": "ringdown-sr-white-scaling-fixed-1",
                        "starts": [
                            {"name": f"start-{i + 1}", "parameters": values}
                            for i, values in enumerate(
                                starts(arrays[f"observed_{cell['case']}"])
                            )
                        ],
                    },
                )
                _write_json(
                    directory / "fixed_prepared.json",
                    {
                        "request_sha256": _sha256(
                            (directory / "fixed_request.json").read_bytes()
                        ),
                        "source_sha256": worker.source_hashes(),
                        "prepared_sha256": _sha256(
                            (directory / "prepared.json").read_bytes()
                        ),
                    },
                )
    _write_json(output / "manifest.json", manifest)
    return manifest


def _fixed(directory, deadline):
    started = time.monotonic()
    started_at = _utc_now()
    environment = os.environ.copy()
    environment.update(worker.native.JULIA_THREADS)
    environment.update(
        {
            name: "1"
            for name in (
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    environment["OPENBLAS_CORETYPE"] = "Haswell"
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    outcome = {
        "format": FORMAT + "-fixed-call-1",
        "status": "aborted",
        "started_at": started_at,
        "wall_scope": FIXED_WALL_SCOPE,
        "cpu_scope": FIXED_CPU_SCOPE,
        "cpu_measurement_complete": False,
        "returncode": None,
    }
    primary_error = None
    try:
        with (directory / "worker.log").open("xb") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(symbolic.ROOT / "scripts/run_python.py"),
                    str(symbolic.ROOT / "scripts/run_white_scaling_fixed.py"),
                    str(directory),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=environment,
                start_new_session=True,
            )
            try:
                code = process.wait(timeout=min(1800, deadline - time.monotonic()))
                outcome["returncode"] = code
            except BaseException:
                symbolic._stop_worker(process)
                outcome["returncode"] = process.returncode
                raise
        if code != 0:
            raise RuntimeError(f"Fixed scaling worker failed ({code}): {directory}")
        outcome.update(status="completed", cpu_measurement_complete=True)
    except BaseException as error:
        primary_error = error
        outcome["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        outcome.update(
            wall_seconds=time.monotonic() - started,
            finished_at=_utc_now(),
            cpu_user_seconds=after.ru_utime - before.ru_utime,
            cpu_system_seconds=after.ru_stime - before.ru_stime,
        )
        _write_terminal_cost(directory / "call.json", outcome, primary_error)


def run(output):
    output = Path(output).resolve()
    manifest = prepare(output)
    started = time.monotonic()
    before = _cpu_snapshot()
    deadline = started + LIMIT_SECONDS
    outcome = {
        "format": FORMAT,
        "status": "running",
        "completed_fixed": 0,
        "completed_search": 0,
        "started_at": _utc_now(),
        "wall_scope": SERIES_WALL_SCOPE,
        "cpu_scope": SERIES_CPU_SCOPE,
        "cpu_measurement_complete": False,
    }
    primary_error = None
    try:
        for stage in ("fixed", "search"):
            planned = [
                cell for cell in cells() if stage != "fixed" or not cell["repeat"]
            ]
            for index, cell in enumerate(planned, 1):
                if time.monotonic() >= deadline:
                    raise TimeoutError("The frozen pilot deadline expired.")
                if (
                    manifest["sources"] != _sources()
                    or manifest["provenance"] != _provenance()
                ):
                    raise ValueError("Pilot implementation changed during execution.")
                outcome.update(stage=stage, current_cell=cell["id"])
                _write_json(output / "status.json", outcome)
                print(f"[{stage} {index}/{len(planned)}] {cell['id']}", flush=True)
                directory = output / stage / cell["id"]
                if stage == "fixed":
                    _fixed(directory, deadline)
                else:
                    report = worker.run_member(directory, deadline=deadline)
                    if report.get("status") != "completed":
                        raise ValueError("Scientific scaling worker did not complete.")
                outcome[f"completed_{stage}"] += 1
        outcome["status"] = "completed"
        outcome["cpu_measurement_complete"] = True
    except BaseException as error:
        primary_error = error
        outcome["status"] = "aborted"
        outcome["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        outcome["wall_seconds"] = time.monotonic() - started
        outcome["finished_at"] = _utc_now()
        after = _cpu_snapshot()
        outcome["cpu_user_seconds"] = after[0] - before[0]
        outcome["cpu_system_seconds"] = after[1] - before[1]
        _write_terminal_cost(output / "status.json", outcome, primary_error)
    return outcome


def _cpu_snapshot():
    usages = [
        resource.getrusage(who)
        for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
    ]
    return tuple(
        sum(getattr(usage, name) for usage in usages)
        for name in ("ru_utime", "ru_stime")
    )


def _write_terminal_cost(path, outcome, primary_error):
    """Never replace the worker exception with a secondary record-write error."""
    try:
        _write_json(path, outcome)
    except BaseException as secondary:
        if primary_error is None:
            raise
        detail = f"{type(secondary).__name__}: {secondary}"
        primary_error.add_note("Secondary cost-record write failure: " + detail)
        failure = {
            "format": FORMAT + "-cost-write-failure-1",
            "status": "aborted",
            "error": f"{type(primary_error).__name__}: {primary_error}",
            "secondary_error": detail,
            "cost_record": outcome,
        }
        try:
            with path.with_name(path.stem + "-write-failure.json").open("xb") as handle:
                handle.write(sources.json_bytes(failure))
        except BaseException as fallback_error:  # noqa: BLE001 -- Preserve the primary exception even if no artifact can be written.
            primary_error.add_note(
                f"Secondary failure-evidence write failure: {type(fallback_error).__name__}: {fallback_error}"
            )


def verify(output):
    """Verify a complete source snapshot without executing any new fits."""
    output = Path(output).absolute()
    clock = publication.Deadline(EXPORT_SECONDS)
    with clock.active():
        consumed = publication.Consumption(clock)
        hashes = _bind_sources(output, consumed)
        report = _verify_contents(output)
        consumed.check()
    consumed.check()
    return {**report, "source_inventory_sha256": hashes}


def _verify_contents(output):
    """Read existing outputs, regenerate input bits, never execute native fits."""
    output = Path(output).resolve()
    manifest = _read(output / "manifest.json")
    if (
        manifest.get("format") != FORMAT
        or manifest["sources"] != _sources()
        or manifest["cells"] != cells()
    ):
        raise ValueError("Changed pilot manifest or source coverage.")
    if _sha256((output / "inputs.npz").read_bytes()) != manifest["input_sha256"]:
        raise ValueError("Changed pilot inputs.")
    with np.load(output / "inputs.npz", allow_pickle=False) as saved:
        expected = data()
        if set(saved.files) != set(expected) or any(
            not np.array_equal(saved[k], v) for k, v in expected.items()
        ):
            raise ValueError("Inputs do not reproduce the frozen generator.")
    status = _read(output / "status.json")
    series_costs = _series_costs(status)
    rows = []
    fixed_rows = []
    fixed_records = {}
    fixed_costs = {}
    for cell in cells():
        if cell["repeat"]:
            continue
        directory = output / "fixed" / cell["id"]
        fixed_costs[cell["id"]] = _fixed_costs(_read(directory / "call.json"))
        report = fixed.verify_fixed(directory)
        fixed_costs[cell["id"]]["local_optimization_sum_seconds"] = (
            _contained_wall_seconds(
                [record["optimization_seconds"] for record in report["records"]],
                fixed_costs[cell["id"]]["wall_seconds"],
                "Local optimization sum exceeds its fixed worker time.",
            )
        )
        _, inputs, _ = worker.verify_prepared(directory)
        _check_cell_inputs(cell, report["request"], inputs, expected)
        fixed_records[cell["id"]] = report["records"]
        for record in report["records"]:
            fixed_rows.append(
                {
                    **cell,
                    "start": record["start"]["name"],
                    "initial_parameters": record["initial_parameters"],
                    "parameters": record["parameters"],
                    "native_loss": record["loss"],
                    "mse": math.fsum(
                        float(x) ** 2 for x in fixed.decode(record["residual"])
                    )
                    / 128,
                    "fit_callback_count": record["fit_callback_count"],
                    "local_steps": record["local_steps"],
                    "optimization_seconds": record["optimization_seconds"],
                    "formula": record["display_equation"],
                }
            )
    fixed_pairs = []
    for case in (1, 2):
        for seed in SEARCH_SEEDS:
            by_arm = {
                arm: fixed_records[f"white-{case:02d}-seed-{seed}-{arm}"]
                for arm in worker.ARMS
            }
            for start in range(4):
                for left, right in (("ordinary", "scaled"), ("scaled", "covariance")):
                    a, b = by_arm[left][start], by_arm[right][start]
                    for key in (
                        "initial_parameters",
                        "rng_before",
                        "rng_after",
                        "restart_draws",
                        "restart_parameters",
                    ):
                        if a[key] != b[key]:
                            raise ValueError(
                                "Fixed loss arms did not receive identical optimizer starts/randomness."
                            )
                    trace_a = [
                        (s["local_index"], s["step"], s["parameters"])
                        for s in a["states"]
                    ]
                    trace_b = [
                        (s["local_index"], s["step"], s["parameters"])
                        for s in b["states"]
                    ]
                    first = next(
                        (i for i, (x, y) in enumerate(zip(trace_a, trace_b)) if x != y),
                        None,
                    )
                    if first is None and len(trace_a) != len(trace_b):
                        first = min(len(trace_a), len(trace_b))
                    fixed_pairs.append(
                        {
                            "case": case,
                            "seed": seed,
                            "start": a["start"]["name"],
                            "contrast": right + "-" + left,
                            "identical_initial_and_restart_values": True,
                            "same_parameter_trace": trace_a == trace_b,
                            "first_parameter_trace_difference": first,
                            "same_final_parameters": a["parameters"] == b["parameters"],
                            "mse_difference": math.fsum(
                                float(x) ** 2 for x in fixed.decode(b["residual"])
                            )
                            / 128
                            - math.fsum(
                                float(x) ** 2 for x in fixed.decode(a["residual"])
                            )
                            / 128,
                        }
                    )
    search_costs = {}
    for cell in cells():
        directory = output / "search" / cell["id"]
        search_costs[cell["id"]] = worker.verify_member(directory)["costs"]
        _contained_wall_seconds(
            [search_costs[cell["id"]]["fit_wall_seconds"]],
            search_costs[cell["id"]]["worker_wall_seconds"],
            "Search fit exceeds its worker time.",
        )
        request, inputs, _ = worker.verify_prepared(directory)
        _check_cell_inputs(cell, request, inputs, expected)
        result = _read(directory / "result.json")
        selected = result["candidates"][result["selected_index"]]
        row = {
            **cell,
            "candidate_count": len(result["candidates"]),
            "selected_index": result["selected_index"],
            "complexity": selected["complexity"],
            "native_loss": selected["loss"],
            "baseline_loss": result["baseline_loss"],
            "cost_normalization": result["cost_normalization"],
            "callback_calls": result["callback_calls_during_fit"],
            "formula": selected["display_equation"],
        }
        for name, times, truth in (
            ("training", expected["time_s"], expected[f"observed_{cell['case']}"]),
            ("regular", expected["regular_time_s"], expected["regular_truth"]),
            ("irregular", expected["irregular_time_s"], expected["irregular_truth"]),
        ):
            _, metrics = evaluate_grid(selected["tree"], times, truth)
            row.update({f"{name}_{key}": value for key, value in metrics.items()})
        rows.append(row)
        if cell["repeat"]:
            original = _read(
                output / "search" / cell["id"].removesuffix("-repeat") / "result.json"
            )
            for key in ("candidates", "selected_index", "callback_calls_during_fit"):
                if original[key] != result[key]:
                    raise ValueError(
                        f"Fresh-process repeat differs: {cell['id']} / {key}"
                    )
    sequential_wall = _contained_wall_seconds(
        [cost["wall_seconds"] for cost in fixed_costs.values()]
        + [cost["worker_wall_seconds"] for cost in search_costs.values()],
        series_costs["wall_seconds"],
        "Sequential worker time sum exceeds the series time.",
    )
    return {
        "format": FORMAT,
        "status": "verified",
        "source_manifest_sha256": _sha256((output / "manifest.json").read_bytes()),
        "searches": rows,
        "fixed": fixed_rows,
        "fixed_pairs": fixed_pairs,
        "wall_seconds": series_costs["wall_seconds"],
        "series_costs": series_costs,
        "fixed_worker_costs": fixed_costs,
        "search_worker_costs": search_costs,
        "sequential_worker_wall_sum_seconds": sequential_wall,
    }


def _contained_wall_seconds(parts, enclosing, message):
    """Compare only monotonic wall intervals whose measured scopes are nested."""
    enclosing = _finite_cost(enclosing, "enclosing_wall_seconds")
    values = [_finite_cost(value, "nested_wall_seconds") for value in parts]
    try:
        total = math.fsum(values)
    except OverflowError as error:
        raise ValueError(message) from error
    if total > enclosing:
        raise ValueError(message)
    return total


def _check_cell_inputs(cell, request, arrays, expected):
    if (
        request["arm"] != cell["arm"]
        or request["budget"]["seed"] != cell["seed"]
        or request["sigma_hex"] != SIGMA.hex()
        or request["technical"]
        or not np.array_equal(arrays["time_s"], expected["time_s"])
        or not np.array_equal(arrays["observed"], expected[f"observed_{cell['case']}"])
    ):
        raise ValueError("Pilot cell does not match the predeclared data/arm/seed.")


def _render_export(output, destination, report, consumed):
    """Build partial artifacts using only the previously bound source bytes."""
    for name in ("searches", "fixed", "fixed_pairs"):
        with (destination / f"{name}.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(report[name][0]))
            writer.writeheader()
            writer.writerows(report[name])
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with np.load(
        io.BytesIO(consumed.files[output / "inputs.npz"]), allow_pickle=False
    ) as saved:
        arrays = {name: saved[name].copy() for name in saved.files}
    selections = []
    for row in report["searches"]:
        result = sources.read_json(
            consumed.files[output / "search" / row["id"] / "result.json"]
        )
        selections.append((row, result["candidates"][result["selected_index"]]))
    for cell in cells():
        if cell["repeat"]:
            continue
        for record in sources.read_json(
            consumed.files[output / "fixed" / cell["id"] / "fixed_result.json"]
        )["records"]:
            selections.append(
                (
                    {
                        **cell,
                        "id": "fixed-" + cell["id"] + "-" + record["start"]["name"],
                    },
                    record,
                )
            )
    for row, selected in selections:
        consumed.clock.check()
        _write_json(destination / (row["id"] + "-formula.json"), selected)
        fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
        with (destination / (row["id"] + "-points.csv")).open(
            "w", newline=""
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["grid", "time_s", "truth", "prediction", "observed", "grid_status"]
            )
            for name, times, truth in (
                ("training", arrays["time_s"], arrays["truth"]),
                ("regular", arrays["regular_time_s"], arrays["regular_truth"]),
                ("irregular", arrays["irregular_time_s"], arrays["irregular_truth"]),
            ):
                prediction, metrics = evaluate_grid(selected["tree"], times, truth)
                observed = (
                    arrays[f"observed_{row['case']}"]
                    if name == "training"
                    else [""] * len(times)
                )
                writer.writerows(
                    zip(
                        [name] * len(times),
                        times,
                        truth,
                        prediction,
                        observed,
                        [metrics["status"]] * len(times),
                        strict=True,
                    )
                )
                representable = np.all(
                    np.abs(prediction[np.isfinite(prediction)]) < 1e100
                )
                if not representable or metrics["status"] != "finite":
                    axes[0].text(
                        0.01,
                        {"training": 0.95, "regular": 0.89, "irregular": 0.83}[name],
                        f"{name}: {metrics['status']}; nichtendliche Werte: {metrics['nonfinite_count']}; Punktdaten vollständig",
                        transform=axes[0].transAxes,
                        fontsize=7,
                    )
                if not representable:
                    axes[0].text(
                        0.01,
                        0.74,
                        "Werte außerhalb des Plotbereichs; siehe unveränderte CSV.",
                        transform=axes[0].transAxes,
                    )
                    continue
                if name == "regular":
                    axes[0].plot(times, truth, color="black", label="Wahrheit")
                    axes[0].plot(times, prediction, label="Originalformel")
                if name != "training":
                    axes[1].plot(
                        times,
                        (prediction - truth) / AMPLITUDE,
                        ".",
                        markersize=2,
                        label=name,
                    )
        axes[0].scatter(
            arrays["time_s"],
            arrays[f"observed_{row['case']}"],
            s=7,
            label="Beobachtung",
        )
        axes[0].set_ylabel("Amplitude / 1")
        axes[1].set_ylabel("Fehler / A")
        axes[1].set_xlabel("Zeit / s")
        axes[0].legend()
        axes[1].legend()
        fig.suptitle(row["id"])
        fig.tight_layout()
        try:
            fig.savefig(destination / (row["id"] + ".png"), dpi=120)
        finally:
            plt.close(fig)
    return {
        path.name: path.read_bytes()
        for path in sorted(destination.iterdir())
        if path.name != publication.LOCK
    }


def _publish_export(destination, report, payloads, consumed):
    """Publish the verified report last, then recheck sources and all artifacts."""
    documents = {**payloads, "report.json": sources.json_bytes(report)}
    checksums = sources.json_bytes(
        {name: _sha256(raw) for name, raw in documents.items()}
    )
    expected = {**documents, "checksums.json": checksums}
    consumed.check()
    publication.verify_bytes(destination, payloads)
    (destination / "checksums.json").write_bytes(checksums)
    pending = destination / "report.json.tmp"
    pending.write_bytes(documents["report.json"])
    consumed.check()
    publication.verify_bytes(
        destination,
        {
            **payloads,
            "checksums.json": checksums,
            "report.json.tmp": documents["report.json"],
        },
    )
    pending.replace(destination / "report.json")
    consumed.check()
    publication.verify_bytes(destination, expected)
    (destination / publication.LOCK).unlink()
    consumed.check()
    publication.verify_bytes(destination, expected, locked=False)
    return expected


def _revoke_export(destination, error, clock, *, secondary_errors=(), cost_record=None):
    """Keep partial evidence while retracting every positive release marker."""
    clock.cancel()
    failure = {
        "format": FORMAT + "-export-1",
        "status": "failed",
        "release": "locked",
        "error": f"{type(error).__name__}: {error}",
        "cleanup_errors": [],
        "deferred_signals": [],
        "secondary_errors": list(secondary_errors),
    }
    if cost_record is not None:
        failure["cost_record"] = cost_record
    mask = os_signal.pthread_sigmask(
        os_signal.SIG_BLOCK, {os_signal.SIGINT, os_signal.SIGTERM}
    )
    with ExitStack() as stack:
        stack.callback(os_signal.pthread_sigmask, os_signal.SIG_SETMASK, mask)

        def defer(signum, frame):
            failure["deferred_signals"].append(signum)

        for sig in (os_signal.SIGINT, os_signal.SIGTERM):
            previous = os_signal.signal(sig, defer)
            stack.callback(os_signal.signal, sig, previous)
        os_signal.pthread_sigmask(os_signal.SIG_SETMASK, mask)

        def attempt(name, action):
            for _ in range(2):
                try:
                    action()
                    return
                except BaseException as cleanup_error:  # noqa: BLE001 -- Revoke all markers despite another cleanup failure.
                    failure["cleanup_errors"].append(
                        {
                            "operation": name,
                            "error": f"{type(cleanup_error).__name__}: {cleanup_error}",
                        }
                    )

        attempt(
            "lock",
            lambda: (destination / publication.LOCK).write_text(
                "Export release revoked.\n", encoding="utf-8"
            ),
        )
        for name in ("report.json", "report.json.tmp", "checksums.json"):
            attempt(
                "remove " + name,
                lambda n=name: (destination / n).unlink(missing_ok=True),
            )
        for name in ("report.json", "export_failure.json"):
            attempt(
                "write " + name,
                lambda n=name: (destination / n).write_bytes(
                    sources.json_bytes(failure)
                ),
            )


def export(output, destination):
    """Snapshot, verify and transactionally export all original selections."""
    started = time.monotonic()
    before = _cpu_snapshot()
    output, destination = Path(output).absolute(), Path(destination).absolute()
    if destination.is_relative_to(output) or output.is_relative_to(destination):
        raise ValueError("Use a separate sibling destination outside the source run.")
    cost_path = destination.with_name(destination.name + "-call.json")
    if cost_path.exists() or cost_path.is_symlink():
        raise ValueError("Export cost record already exists.")
    clock = publication.Deadline(EXPORT_SECONDS)
    consumed = publication.Consumption(clock)
    owned = None
    primary_error = None
    outcome = {
        "format": FORMAT + "-export-call-1",
        "status": "aborted",
        "started_at": _utc_now(),
        "wall_scope": "entry_through_publication_and_handler_teardown_excluding_call_record_write_and_final_rechecks",
        "cpu_scope": SERIES_CPU_SCOPE,
        "cpu_measurement_complete": False,
    }
    try:
        with clock.active():
            owned = publication.reserve_output(destination)
            hashes = _bind_sources(output, consumed)
            report = {**_verify_contents(output), "source_inventory_sha256": hashes}
            consumed.check()
            payloads = _render_export(output, owned, report, consumed)
            expected = _publish_export(owned, report, payloads, consumed)
        outcome.update(status="completed", cpu_measurement_complete=True)
    except BaseException as error:
        primary_error = error
        if owned is not None:
            _revoke_export(owned, error, clock)
        outcome["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        if owned is not None:
            after = _cpu_snapshot()
            outcome.update(
                finished_at=_utc_now(),
                wall_seconds=time.monotonic() - started,
                cpu_user_seconds=after[0] - before[0],
                cpu_system_seconds=after[1] - before[1],
            )
            try:
                with cost_path.open("xb") as handle:
                    handle.write(sources.json_bytes(outcome))
            except BaseException as error:
                if primary_error is None:
                    outcome.update(
                        status="aborted", error=f"{type(error).__name__}: {error}"
                    )
                    _revoke_export(owned, error, clock, cost_record=outcome)
                    raise
                # Preserve the original exception and measured partial costs even
                # when the separate cost artifact cannot be created.
                _revoke_export(
                    owned,
                    primary_error,
                    clock,
                    secondary_errors=[
                        {
                            "operation": "write cost record",
                            "error": f"{type(error).__name__}: {error}",
                        }
                    ],
                    cost_record=outcome,
                )
    try:
        consumed.check()
        publication.verify_bytes(owned, expected, locked=False)
    except BaseException as error:
        _revoke_export(owned, error, clock)
        # The completed measurement does not imply successful final rechecks.
        outcome.update(status="aborted", error=f"{type(error).__name__}: {error}")
        try:
            _write_json(cost_path, outcome)
        except BaseException as secondary:  # noqa: BLE001 -- Preserve and re-raise the primary verification failure.
            _revoke_export(
                owned,
                error,
                clock,
                secondary_errors=[
                    {
                        "operation": "update cost record",
                        "error": f"{type(secondary).__name__}: {secondary}",
                    }
                ],
                cost_record=outcome,
            )
        raise
    return report
