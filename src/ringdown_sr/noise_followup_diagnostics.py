"""Run and read-verify the fixed covariance-only development comparison."""

import csv
import io
import math
import resource
import signal
import time
import zipfile
from contextlib import ExitStack

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import noise_followup_covariance as covariance
from . import noise_followup_inputs as inputs
from . import noise_pilot_inputs as pilot
from .confirmed_pilot import _snapshot_tree
from .covariance_estimation import CovarianceEstimationError
from .noise_pilot import _identity, _usage
from .pilot import _write_json

FORMAT = "ringdown-sr-noise-followup-diagnostics-1"
SECONDS = 14400
METHODS = ("full_matrix", "welch_toeplitz")
MEMORY_SCOPE = (
    "process lifetime high-water mark in KiB; per-estimate samples after estimation, "
    "whole-call sample after publication; includes earlier work, not isolated method memory"
)
SUMMARY = (
    "# Separate Rauschschätzer-Vorprüfung\n\n"
    "Acht korrelierte und vier weiße Entwicklungsfälle, zwei Dauern und zwei "
    "vorab feste Schätzer. Alle geplanten Schätzungen einschließlich Ausfällen "
    "bleiben enthalten. Keine SR, keine automatische Methodenwahl. "
    "Die wissenschaftliche Suchserie behält den vollen Matrixschätzer.\n"
)


def _json(path, consumed):
    return sources.read_json(inputs._small_read(path, consumed))


def _npz_bytes(arrays):
    """Serialize diagnostic arrays with deterministic names and ZIP metadata."""
    allowed = {"raw_covariance", "covariance", "frequencies_hz", "psd", "acf"}
    if set(arrays) - allowed:
        raise ValueError("Unexpected diagnostic array role.")
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(arrays.items()):
            data = io.BytesIO()
            np.save(data, value, allow_pickle=False)
            info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data.getvalue())
    return stream.getvalue()


def _metrics(matrix, truth, check):
    if matrix is None:
        return {
            key: pilot._diagnostic(reason="covariance_estimation_failed")
            for key in ("relative_frobenius_error", "condition_number", "check_score")
        }
    return {
        "relative_frobenius_error": pilot._diagnostic(
            lambda: pilot._relative_frobenius(matrix, truth)
        ),
        "condition_number": pilot._diagnostic(lambda: pilot._condition_number(matrix)),
        "check_score": pilot._diagnostic(
            lambda: pilot._background_check_score(matrix, check)
        ),
    }


def _estimate(series, validation, truth, check, method):
    """Evaluate one fixed estimator; numerical failures never select a fallback."""
    if method not in METHODS:
        raise ValueError("Unknown diagnostic covariance method.")
    payload = {}
    raw = None
    n_train = len(series) // inputs.N_SAMPLES
    try:
        if method == "full_matrix":
            raw = covariance.empirical_from_series(series)
            rank = n_train
            method_id = covariance.METHOD
        else:
            welch = covariance.welch_covariance(series)
            raw = welch.raw_covariance
            rank = None
            method_id = covariance.WELCH_METHOD
            payload.update(
                frequencies_hz=welch.frequencies_hz,
                psd=welch.psd,
                acf=welch.acf,
            )
        estimate = covariance.estimate_from_raw(
            raw,
            validation,
            n_train=n_train,
            alpha_candidates=inputs.ALPHAS,
            structural_rank_bound=rank,
            method=method_id,
        )
    except CovarianceEstimationError as error:
        record = pilot._estimate_record(error=error)
        record.update(
            method=covariance.METHOD
            if method == "full_matrix"
            else covariance.WELCH_METHOD,
            n_train=n_train,
            n_validation=len(validation),
            error={"type": type(error).__name__, "message": str(error)},
        )
        if raw is None:
            raw = error.raw_covariance
        matrix = None
    else:
        record = pilot._estimate_record(estimate=estimate)
        matrix = estimate.covariance
        payload["covariance"] = matrix
    if raw is not None:
        payload["raw_covariance"] = raw
    return {
        "method": method,
        "estimate": record,
        "raw_diagnostics": _metrics(raw, truth, check),
        "selected_diagnostics": _metrics(matrix, truth, check),
        "true_diagnostics": _metrics(truth, truth, check),
        "independent_training_rows_required": False,
        "changes_scientific_estimator": False,
    }, payload


def _calculate(prepared, consumed, measurements=None):
    if prepared.manifest["purpose"] != "diagnostic":
        raise ValueError("Estimator diagnostics require their separate input purpose.")
    specs = inputs.case_specs(purpose="diagnostic")
    if list(prepared.cases) != [item["id"] for item in specs]:
        raise ValueError("Diagnostic case inventory differs from the frozen plan.")
    records, payloads = [], {}
    for spec in specs:
        consumed.clock.check()
        case_checks = publication.Consumption(consumed.clock)
        case = inputs.read_case(prepared, spec["id"], case_checks, regenerate=True)
        with inputs.open_training(case) as training:
            for duration in inputs.DURATIONS:
                series = training[: duration * inputs.SAMPLE_RATE]
                for method in METHODS:
                    consumed.clock.check()
                    started = time.monotonic()
                    record, arrays = _estimate(
                        series,
                        case.arrays["background_validation"],
                        case.arrays["covariance_true"],
                        case.arrays["background_check"],
                        method,
                    )
                    identity = {
                        "case": spec["id"],
                        "model": spec["noise_model"],
                        "block": spec["block"],
                        "duration_seconds": duration,
                        "method": method,
                    }
                    if measurements is not None:
                        measurements.append(
                            {
                                **identity,
                                "wall_seconds": time.monotonic() - started,
                                "process_peak_rss_kib": resource.getrusage(
                                    resource.RUSAGE_SELF
                                ).ru_maxrss,
                            }
                        )
                    name = f"{spec['id']}--{duration}s--{method}"
                    raw = _npz_bytes(arrays)
                    payloads[f"estimate--{name}.npz"] = raw
                    record.update(
                        **identity,
                        training_samples=len(series),
                        training_prefix_bytes=series.nbytes,
                        shared_training_file_bytes=case.train_path.stat().st_size,
                        input_record_sha256=sources.sha256(
                            sources.json_bytes(case.record)
                        ),
                        arrays_path=f"estimate--{name}.npz",
                        arrays_sha256=sources.sha256(raw),
                        arrays_file_bytes=len(raw),
                    )
                    records.append(record)
        case_checks.check()
    consumed.check()
    report = {
        "format": FORMAT,
        "status": "completed",
        "purpose": "diagnostic",
        "software": prepared.manifest["software"],
        "plan_sha256": inputs.PLAN_SHA256,
        "input_manifest_sha256": sources.sha256(sources.json_bytes(prepared.manifest)),
        "preparation_call": prepared.call,
        "planned_cases": len(specs),
        "planned_estimates": len(specs) * len(inputs.DURATIONS) * len(METHODS),
        "completed_estimates": sum(r["estimate"]["status"] == "ready" for r in records),
        "failed_estimates": sum(r["estimate"]["status"] != "ready" for r in records),
        "records": records,
        "search_calls": 0,
        "scientific_estimator": covariance.METHOD,
        "automatic_method_selection": False,
    }
    payloads.update(_plots(report))
    return report, payloads


def _plots(report):
    """Export every diagnostic point without filtering failed estimates."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    columns = (
        "case",
        "model",
        "block",
        "duration_seconds",
        "method",
        "status",
        "alpha",
        "relative_frobenius_error",
        "condition_number",
        "check_score",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    rows = []
    for record in report["records"]:
        row = {key: record[key] for key in columns[:5]}
        row.update(
            status=record["estimate"]["status"],
            alpha=record["estimate"]["alpha_selected"],
        )
        for key in columns[7:]:
            metric = record["selected_diagnostics"][key]
            value = metric["value"]
            if key == "check_score" and value is not None:
                value = value["score"]
            row[key] = value
        writer.writerow(row)
        rows.append(row)
    payloads = {"diagnostics.csv": stream.getvalue().encode()}
    with plt.rc_context({"svg.hashsalt": FORMAT}):
        for model in ("ar1", "white"):
            fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
            for axis, key, label in zip(
                axes,
                ("relative_frobenius_error", "check_score"),
                ("Relativer Frobeniusfehler", "Gauß-Score auf Kontrollfenstern"),
                strict=True,
            ):
                for method in METHODS:
                    for duration in inputs.DURATIONS:
                        group = [
                            row
                            for row in rows
                            if row["model"] == model
                            and row["method"] == method
                            and row["duration_seconds"] == duration
                        ]
                        finite = [row for row in group if row[key] is not None]
                        axis.plot(
                            [row["block"] for row in finite],
                            [row[key] for row in finite],
                            marker="o",
                            linestyle="none",
                            label=f"{method}, {duration} s ({len(finite)}/{len(group)})",
                        )
                axis.set(xlabel="Entwicklungsfall", ylabel=label)
                axis.grid(alpha=0.3)
                axis.legend(fontsize=7)
            fig.suptitle(f"Separate Schätzerdiagnostik: {model}; keine SR-Auswahl")
            for suffix in ("png", "svg"):
                output = io.BytesIO()
                metadata = {"Date": None} if suffix == "svg" else {"Software": FORMAT}
                fig.savefig(output, format=suffix, dpi=130, metadata=metadata)
                payloads[f"diagnostics-{model}.{suffix}"] = output.getvalue()
            plt.close(fig)
    return payloads


def _timing(started, before, report_raw, measurements, *, error=None):
    after = _usage()
    return {
        "format": FORMAT + "-call",
        "status": "completed" if error is None else "aborted",
        "source_report_sha256": None
        if report_raw is None
        else sources.sha256(report_raw),
        "scope": "entry_through_publication_and_handler_teardown_excluding_call_write_and_final_rechecks",
        "wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": sum(
            a.ru_utime - b.ru_utime for a, b in zip(after, before, strict=True)
        ),
        "cpu_system_seconds": sum(
            a.ru_stime - b.ru_stime for a, b in zip(after, before, strict=True)
        ),
        "cpu_scope": "self_plus_reaped_children",
        "cpu_measurement_complete": error is None,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "memory_scope": MEMORY_SCOPE,
        "estimator_measurements": measurements,
        "contained_costs_note": "Preparation and estimator times are contained, never add them to whole-call wall time.",
        "error": None if error is None else f"{type(error).__name__}: {error}",
    }


def _documents(report, payloads):
    documents = {
        **payloads,
        publication.REPORT: sources.json_bytes(report),
        publication.SUMMARY: SUMMARY.encode(),
    }
    return {
        **documents,
        publication.MANIFEST: sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in documents.items()}
        ),
    }


def run(output):
    """Prepare and evaluate the twelve separate noise-estimator cases."""
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, before = time.monotonic(), _usage()
    root = publication.validate_output(output)
    clock = publication.Deadline(SECONDS)
    consumed = publication.Consumption(clock)
    measurements, expected = [], {}
    root.mkdir(parents=True)
    try:
        with ExitStack() as stack:

            def interrupted(signum, frame):
                raise InterruptedError(
                    "Estimator diagnostics interrupted: " + str(signum)
                )

            for sig in (signal.SIGINT, signal.SIGTERM):
                previous = signal.signal(sig, interrupted)
                stack.callback(signal.signal, sig, previous)
            inputs.prepare_inputs(root / "inputs", purpose="diagnostic")
            prepared = inputs.verify_inputs(root / "inputs", consumed)
            clock.check()

            def build(checks):
                checks.callbacks.append(consumed.check)
                report, payloads = _calculate(prepared, checks, measurements)
                expected.update(_documents(report, payloads))
                return report, SUMMARY, payloads

            report = publication.export_transaction(
                root / "completion", build, seconds=SECONDS
            )
            consumed.check()
            publication.verify_bytes(root / "completion", expected, locked=False)
        clock.check()
        call = _timing(started, before, expected[publication.REPORT], measurements)
        _write_json(root / "call.json", call)
        consumed.add(root / "call.json", sources.json_bytes(call))
        consumed.callbacks.append(lambda: _root_inventory(root))
        _validate_timing(call, report, expected[publication.REPORT])
        consumed.check()
        publication.verify_bytes(root / "completion", expected, locked=False)
        return report
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, clock)
        _write_json(
            root / "call.json",
            _timing(started, before, None, measurements, error=error),
        )
        raise


def _validate_timing(call, report, report_raw):
    if (
        set(call)
        != {
            "format",
            "status",
            "source_report_sha256",
            "scope",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "cpu_scope",
            "cpu_measurement_complete",
            "process_peak_rss_kib",
            "memory_scope",
            "estimator_measurements",
            "contained_costs_note",
            "error",
        }
        or call.get("format") != FORMAT + "-call"
        or call.get("status") != "completed"
        or call.get("cpu_measurement_complete") is not True
        or call.get("error") is not None
        or call.get("source_report_sha256") != sources.sha256(report_raw)
        or call.get("cpu_scope") != "self_plus_reaped_children"
        or call.get("memory_scope") != MEMORY_SCOPE
        or type(call.get("process_peak_rss_kib")) is not int
        or call.get("scope")
        != "entry_through_publication_and_handler_teardown_excluding_call_write_and_final_rechecks"
    ):
        raise ValueError("Missing or inconsistent estimator-call evidence.")
    for key in (
        "wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "process_peak_rss_kib",
    ):
        value = call.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid measured estimator cost.")
    if call["wall_seconds"] >= SECONDS:
        raise ValueError("Estimator diagnostics exceeded the frozen deadline.")
    expected = [
        {
            key: record[key]
            for key in ("case", "model", "block", "duration_seconds", "method")
        }
        for record in report["records"]
    ]
    actual = call.get("estimator_measurements")
    if not isinstance(actual, list) or len(actual) != len(expected):
        raise ValueError("Incomplete estimator measurement inventory.")
    previous_peak = 0
    for item, identity in zip(actual, expected, strict=True):
        if not isinstance(item, dict) or set(item) != {
            *identity,
            "wall_seconds",
            "process_peak_rss_kib",
        }:
            raise ValueError("Unexpected estimator measurement fields.")
        if {key: item[key] for key in identity} != identity:
            raise ValueError("Estimator measurement identity changed.")
        value = item["wall_seconds"]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid measured estimator duration.")
        peak = item["process_peak_rss_kib"]
        if (
            type(peak) is not int
            or peak < previous_peak
            or peak > call["process_peak_rss_kib"]
        ):
            raise ValueError("Invalid cumulative process memory measurement.")
        previous_peak = peak
    if sum(item["wall_seconds"] for item in actual) > call["wall_seconds"]:
        raise ValueError("Contained estimator times exceed whole-call duration.")
    for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if call[key] + 1e-6 < report["preparation_call"][key]:
            raise ValueError("Estimator call costs are below their input preparation.")
    if (
        sum(item["wall_seconds"] for item in actual)
        + report["preparation_call"]["wall_seconds"]
        > call["wall_seconds"] + 1e-6
    ):
        raise ValueError("Disjoint preparation and estimator costs exceed call cost.")


def _root_inventory(root):
    if root.is_symlink() or {path.name for path in root.iterdir()} != {
        "inputs",
        "inputs-call.json",
        "completion",
        "call.json",
    }:
        raise ValueError("Unexpected diagnostic-root inventory.")
    if any(path.is_symlink() for path in root.iterdir()):
        raise ValueError("Diagnostic evidence cannot contain symlinks.")


def verify(output, *, export=None, consumed=None):
    """Read-only replay of all forty-eight predeclared estimates."""
    root = _identity(output)
    if consumed is not None and export is not None:
        raise ValueError(
            "Externally guarded verification cannot publish a nested export."
        )
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(SECONDS))
    _root_inventory(root)
    consumed.callbacks.append(lambda: _root_inventory(root))
    _snapshot_tree(root / "completion", consumed)
    original_raw = inputs._small_read(
        root / "completion" / publication.REPORT, consumed
    )
    original = sources.read_json(original_raw)
    prepared = inputs.verify_inputs(root / "inputs", consumed)
    report, payloads = _calculate(prepared, consumed)
    sources._same(
        original, report, "Replayed estimator diagnostics differ from publication."
    )
    expected = _documents(report, payloads)
    publication.verify_bytes(root / "completion", expected, locked=False)
    consumed.callbacks.append(
        lambda: publication.verify_bytes(root / "completion", expected, locked=False)
    )
    call = _json(root / "call.json", consumed)
    _validate_timing(call, report, original_raw)
    consumed.check()
    if export is not None:

        def build(checks):
            checks.callbacks.append(consumed.check)
            return report, SUMMARY, payloads

        target = publication.validate_output(export)
        published = False
        try:
            publication.export_transaction(target, build, seconds=SECONDS)
            published = True
            consumed.check()
            publication.verify_bytes(target, expected, locked=False)
        except BaseException as error:
            if published:
                publication.revoke(target, error, consumed.clock)
            raise
    return report
