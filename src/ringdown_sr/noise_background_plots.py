"""Export bound plots and exact original formulas without fitting or selecting."""

import copy
import csv
import io
import math
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import noise_background_assessment as assessment
from . import noise_background_inputs as inputs
from . import noise_pilot_assessment as pilot_assessment
from .confirmed_pilot import _snapshot_tree
from .pilot import _utc_now
from .structure import _validated_tree
from .symbolic import evaluate_tree

FORMAT = "ringdown-sr-noise-background-plots-1"
SECONDS = 14400
ARMS = assessment.ARMS
LABELS = dict(zip(ARMS, ("O", "K", "E64", "E256", "E1024"), strict=True))
COLORS = ("#2166ac", "#7b3294", "#008837", "#e08214", "#b2182b")
ROLES = {
    "training": ("time_s", "signal", "native Trainingsvorhersage", "#2166ac", "o"),
    "diagnostic": (
        "diagnostic_time_s",
        "diagnostic_truth",
        "Replay: feste Zwischenpunkte",
        "#7b3294",
        "+",
    ),
    "irregular": (
        "irregular_time_s",
        "irregular_truth",
        "Replay: unregelmäßiges Raster",
        "#d95f02",
        ".",
    ),
}
SUMMARY = (
    "# Hintergrundstudie: gebundene Plots und Originalformeln\n\n"
    "Alle geplanten Ausgaben einschließlich Ausfällen. Nur gespeicherte Punkte; "
    "keine Suchen, Fits, Neuauswahl oder Glättung. Native Trainingsvorhersagen "
    "und lesender Originalbaum-Replay sind getrennt gekennzeichnet.\n\n"
    "Die CSV-Dateien enthalten alle Punkte samt Fehlanzeigen; JSON bindet "
    "Originalbaum, unveränderte Formel, Konstanten, Quelle und Kosten. "
    "TXT enthält den vollständigen Originalformeltext. PNG/SVG sind Darstellungen, "
    "kein Definitionsnachweis oder Nachweis des Verlaufs zwischen den Punkten.\n"
)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _csv(rows):
    stream = io.StringIO(newline="")
    if not rows:
        raise ValueError("Plot tables cannot silently omit all planned rows.")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _figure(size=(12, 7)):
    figure = Figure(figsize=size)
    FigureCanvasAgg(figure)
    return figure


def _images(figure):
    result = {}
    try:
        # Fixed metadata removes timestamps, without promising renderer-byte identity.
        for suffix in ("png", "svg"):
            stream = io.BytesIO()
            figure.savefig(
                stream,
                format=suffix,
                dpi=120,
                metadata={"Date": None} if suffix == "svg" else {},
            )
            result[suffix] = stream.getvalue()
    finally:
        figure.clear()
    return result


def _replay(tree, times):
    """Keep every bound point, including isolated nonfinite predictions."""
    _validated_tree(tree)
    try:
        return evaluate_tree(tree, times), [None] * len(times)
    except ValueError as error:
        if str(error) != "Tree prediction is not finite.":
            raise
    values, reasons = [], []
    # This is the same original tree at the same saved points, never a new grid.
    for point in times:
        try:
            value = float(evaluate_tree(tree, np.array([point], dtype=np.float64))[0])
        except ValueError as error:
            if str(error) != "Tree prediction is not finite.":
                raise
            values.append(np.nan)
            reasons.append("original_tree_prediction_nonfinite")
        else:
            values.append(value)
            reasons.append(None)
    return np.asarray(values), reasons


def _number(value):
    return float(value) if math.isfinite(float(value)) else None


def _hex(value):
    return None if value is None else float(value).hex()


def point_data(candidate, arrays, amplitude, *, reason=None):
    """Return transparent point rows and norms without replacing native predictions."""
    if not _finite(amplitude) or amplitude <= 0:
        raise ValueError("Plot amplitude must be finite and positive.")
    if candidate is not None:
        _validated_tree(candidate["tree"])
        if type(candidate.get("display_equation")) is not str:
            raise ValueError("Original formula text is missing.")
    rows, metrics, peaks = [], {}, {}
    for role, (time_key, truth_key, *_display) in ROLES.items():
        times, truth = np.asarray(arrays[time_key]), np.asarray(arrays[truth_key])
        if (
            times.dtype != np.dtype("float64")
            or truth.dtype != np.dtype("float64")
            or times.ndim != 1
            or times.shape != truth.shape
            or not times.size
            or not np.all(np.isfinite(times))
            or not np.all(np.isfinite(truth))
        ):
            raise ValueError(
                "Plot references must retain finite bound Float64 vectors."
            )
        if candidate is None:
            prediction = np.full(times.shape, np.nan)
            reasons = [reason or "no_original_output"] * len(times)
        elif role == "training":
            prediction = np.asarray(candidate["prediction"], dtype=np.float64)
            if prediction.shape != times.shape or not np.all(np.isfinite(prediction)):
                raise ValueError(
                    "Native selected predictions changed or are nonfinite."
                )
            reasons = [None] * len(times)
        else:
            prediction, reasons = _replay(candidate["tree"], times)
        complete = bool(np.all(np.isfinite(prediction)))
        metrics[role] = (
            pilot_assessment._amplitude_errors(prediction, truth, amplitude)
            if complete
            else pilot_assessment._unavailable(
                reason or "one_or_more_original_predictions_unavailable", amplitude=True
            )
        )
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            residual = prediction - truth
            normalized = residual / amplitude
        peak = None
        for index, time_s in enumerate(times):
            value, error, scaled = (
                _number(prediction[index]),
                _number(residual[index]),
                _number(normalized[index]),
            )
            observed = None
            if role == "training" and "observed" in arrays:
                observed = _number(arrays["observed"][index])
            point_reason = reasons[index]
            if point_reason is None and (error is None or scaled is None):
                point_reason = "residual_or_normalization_out_of_range"
            row = {
                "grid": role,
                "index_zero_based": index,
                "time_s": float(time_s),
                "time_hex": float(time_s).hex(),
                "truth": float(truth[index]),
                "truth_hex": float(truth[index]).hex(),
                "observed": observed,
                "observed_hex": _hex(observed),
                "prediction": value,
                "prediction_hex": _hex(value),
                "prediction_origin": "stored_native"
                if role == "training"
                else "read_only_original_binary_tree",
                "residual": error,
                "residual_over_amplitude": scaled,
                "status": "available" if point_reason is None else "not_available",
                "reason": point_reason,
            }
            rows.append(row)
            if scaled is not None and (
                peak is None or abs(scaled) > peak["absolute_error_over_amplitude"]
            ):
                peak = {
                    "grid": role,
                    "index_zero_based": index,
                    "time_s": float(time_s),
                    "absolute_error_over_amplitude": abs(scaled),
                    "prediction": value,
                    "truth": float(truth[index]),
                    "complete_grid": complete,
                }
        peaks[role] = peak
    return rows, metrics, peaks


def _curve_plot(metadata, rows, stem):
    figure = _figure((12, 8.5))
    top, bottom = figure.subplots(2, 1, sharex=True)
    for role, (_time, _truth, label, color, marker) in ROLES.items():
        selected = [row for row in rows if row["grid"] == role]
        times = [row["time_s"] for row in selected]
        predictions = [
            np.nan if row["prediction"] is None else row["prediction"]
            for row in selected
        ]
        errors = [
            np.nan
            if row["residual_over_amplitude"] is None
            else row["residual_over_amplitude"]
            for row in selected
        ]
        top.scatter(
            times, predictions, color=color, marker=marker, s=12, alpha=0.8, label=label
        )
        bottom.scatter(
            times, errors, color=color, marker=marker, s=12, alpha=0.8, label=label
        )
        missing = [row["time_s"] for row in selected if row["status"] != "available"]
        if missing:
            for axis in (top, bottom):
                axis.scatter(
                    missing,
                    np.full(len(missing), 0.025),
                    transform=axis.get_xaxis_transform(),
                    marker="x",
                    color="red",
                    s=20,
                    label=f"{role}: {len(missing)} nicht verfügbar",
                )
    truth = sorted((row["time_s"], row["truth"]) for row in rows)
    top.plot(
        [v[0] for v in truth],
        [v[1] for v in truth],
        color="#006837",
        lw=1.0,
        label="Saubere Wahrheit: verbundene gespeicherte Punkte",
    )
    observations = [
        row for row in rows if row["grid"] == "training" and row["observed"] is not None
    ]
    top.scatter(
        [row["time_s"] for row in observations],
        [row["observed"] for row in observations],
        color="#888888",
        marker="x",
        s=14,
        label="Verrauschte Trainingsdaten",
    )
    peaks = [peak for peak in metadata["peaks"].values() if peak is not None]
    if peaks:
        peak = max(peaks, key=lambda item: item["absolute_error_over_amplitude"])
        top.scatter(
            [peak["time_s"]], [peak["prediction"]], color="red", marker="^", s=45
        )
        top.annotate(
            f"Max. gespeicherter Rasterfehler: {peak['absolute_error_over_amplitude']:.6g} A\nt={peak['time_s']:.9g} s ({peak['grid']})",
            xy=(peak["time_s"], peak["prediction"]),
            xycoords="data",
            xytext=(0.03, 0.94),
            textcoords="axes fraction",
            va="top",
            fontsize=8,
            arrowprops={"arrowstyle": "->", "color": "red"},
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
    identity = metadata["identity"]
    title = f"{identity['case']} / {LABELS[identity['arm']]} / {metadata['status']}"
    if metadata["technical"]:
        title += " — technischer Vorlauf, kein Qualitätskriterium"
    figure.suptitle(title, fontsize=12)
    top.set_ylabel("Signalwert (Original-Amplitudeneinheit)")
    bottom.set_ylabel("(Originalvorhersage − saubere Wahrheit) / |A|")
    bottom.set_xlabel("t / Sekunden")
    bottom.axhline(0, color="#777777", lw=0.7)
    for axis in (top, bottom):
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7, loc="best")
    notes = [
        f"Unveränderte vollständige Originalformel: {stem}.formula.txt; Originalbaum und Bindung: {stem}.json",
        "Keine Glättung; Linien der Wahrheit verbinden nur gespeicherte Punkte. Keine Aussage zwischen allen Punkten.",
    ]
    if metadata["candidate"] is None:
        notes.append("Keine Originalausgabe: " + str(metadata["reason"]))
    figure.text(0.03, 0.02, "\n".join(notes), fontsize=8)
    figure.tight_layout(rect=(0, 0.08, 1, 0.96))
    return _images(figure)


def _selection(record, case, *, technical):
    identity = record["source_identity"]
    if technical:
        return {"member_position": 1, "seed": case.spec["search_seeds"][0]}
    path = identity.get("selected_member_path")
    if record["original_candidate"] is None:
        if path is not None:
            raise ValueError("Unavailable output has a selected member path.")
        return {"member_position": None, "seed": None}
    match = re.fullmatch(r"symbolic/([^/]+)/member-(\d{2})/result\.json", str(path))
    if match is None or match[1] != identity["arm"] or not 1 <= int(match[2]) <= 4:
        raise ValueError("Original selected member cannot be bound to its arm.")
    position = int(match[2])
    return {
        "member_position": position,
        "seed": case.spec["search_seeds"][position - 1],
    }


def _output_payload(record, prepared, case, *, technical, series_identity):
    identity = record["source_identity"]
    case_id = case.spec["id"]
    arm = identity["arm"]
    if arm not in ARMS:
        raise ValueError("Unexpected plot arm.")
    stem = f"{case_id}-{arm}"
    sources.safe_name(stem)
    arrays = {**prepared.common, **case.arrays}
    candidate = record["original_candidate"]
    rows, metrics, peaks = point_data(
        candidate,
        arrays,
        inputs.SIGNAL["amplitude"],
        reason=record.get("reason") or record.get("primary", {}).get("reason"),
    )
    if not technical and candidate is not None:
        for role in ROLES:
            # Unavailable roles preserve assessment reasons; finite norms must agree.
            if metrics[role]["rms_over_amplitude"] is not None:
                sources._same(
                    metrics[role],
                    record["amplitude_errors"][role],
                    "Plot norm differs from the verified original assessment.",
                )
    metadata = {
        "format": FORMAT,
        "technical": technical,
        "scientific_success_assessed": False if technical else None,
        "identity": {
            "case": case_id,
            **copy.deepcopy(identity),
            **_selection(record, case, technical=technical),
        },
        "series": series_identity,
        "status": record["status"],
        "reason": record.get("reason") or record.get("primary", {}).get("reason"),
        "candidate": copy.deepcopy(candidate),
        "background_training_windows": int(arm.rsplit("_", 1)[1])
        if arm.startswith("estimated_")
        else None,
        "signal_hex": {name: value.hex() for name, value in inputs.SIGNAL.items()},
        "units": {
            "time": "seconds",
            "signal": "original signal-amplitude unit",
            "residual": "amplitude normalized",
        },
        "metrics": metrics,
        "peaks": peaks,
        "costs": copy.deepcopy(record["costs"]),
        "supplemental": copy.deepcopy(record.get("supplemental")),
        "point_count": len(rows),
        "points_csv_sha256": sources.sha256(_csv(rows)),
        "interpretation": "Saved points only; no smoothing, fitting, reselection or continuous-domain claim.",
    }
    equation = (
        candidate["display_equation"]
        if candidate is not None
        else "Keine Originalformel verfügbar: " + str(metadata["reason"])
    )
    payloads = {
        f"{stem}.csv": _csv(rows),
        f"{stem}.json": sources.json_bytes(metadata),
        f"{stem}.formula.txt": equation.encode(),
    }
    payloads.update(
        {
            f"{stem}.{suffix}": raw
            for suffix, raw in _curve_plot(metadata, rows, stem).items()
        }
    )
    return stem, metadata, payloads


def _overview_payloads(report, prepared):
    """Display all planned blocks; do not turn missing values into zero costs."""
    payloads = {}
    by_identity = {
        (
            r["source_identity"]["model"],
            r["source_identity"]["block"],
            r["source_identity"]["arm"],
        ): r
        for r in report["assessments"]
    }
    for model, group in report["summary"]["models"].items():
        blocks = assessment.PLANNED_BLOCKS[model]
        figure = _figure((14, 7))
        error_axis, contrast_axis = figure.subplots(1, 2)
        rows = []
        for arm, color in zip(ARMS, COLORS, strict=True):
            stat = group["arms"][arm]["primary"]
            values = stat["values"]
            error_axis.plot(
                [v["block"] for v in values],
                [np.nan if v["value"] is None else v["value"] for v in values],
                marker="o",
                ms=4,
                color=color,
                label=f"{LABELS[arm]}: {stat['available']}/{stat['planned']}",
            )
            rows.extend(
                {
                    "kind": "primary",
                    "name": arm,
                    "block": value["block"],
                    "value": value["value"],
                    "status": value["status"],
                    "reason": value["reason"],
                }
                for value in values
            )
        names = list(group["contrasts"])
        labels = []
        for position, name in enumerate(names):
            stat = group["contrasts"][name]
            labels.append(
                f"{LABELS[stat['left']]} − {LABELS[stat['right']]} ({stat['available']}/{stat['planned']})"
            )
            values = stat["values"]
            for value in values:
                if value["value"] is not None:
                    contrast_axis.scatter(
                        value["value"],
                        position
                        + 0.32 * ((value["block"] - 1) / max(1, blocks - 1) - 0.5),
                        s=14,
                        color="#555555",
                        alpha=0.65,
                    )
            mean = stat["mean"]
            interval = stat["interval_95"]
            if mean is not None:
                contrast_axis.scatter(
                    [mean], [position], marker="D", color="#b2182b", s=24
                )
            if interval["lower"] is not None and interval["upper"] is not None:
                contrast_axis.plot(
                    [interval["lower"], interval["upper"]],
                    [position, position],
                    color="#b2182b",
                    lw=2,
                )
            rows.extend(
                {
                    "kind": "contrast",
                    "name": name,
                    "block": value["block"],
                    "value": value["value"],
                    "status": value["status"],
                    "reason": value["reason"],
                }
                for value in values
            )
        error_axis.set(
            xlabel="Vorab festgelegter Block",
            ylabel="RMSE / |A| auf unregelmäßigem Raster",
            title=f"{model}: alle geplanten Ausgaben",
        )
        error_axis.legend(fontsize=8)
        contrast_axis.set(
            yticks=range(len(names)),
            yticklabels=labels,
            xlabel="Gepaarte Differenz RMSE / |A|",
            title="Einzelwerte, Mittel und approximatives 95-%-Intervall",
        )
        contrast_axis.axvline(0, color="#777777", lw=0.7)
        for axis in (error_axis, contrast_axis):
            axis.grid(alpha=0.2)
        figure.text(
            0.03,
            0.02,
            "Keine Poolung. Intervalle marginal und nur für vollständige Paarungen; kein Freigabetest. Fehlende Werte bleiben im Nenner.\nPrimär: E1024 − O unter AR(1); alle anderen Kontraste deskriptiv. Linien verbinden nur nummerierte Blöcke.",
            fontsize=8,
        )
        figure.tight_layout(rect=(0, 0.08, 1, 1))
        stem = f"{model}-errors-contrasts"
        payloads.update({f"{stem}.{ext}": raw for ext, raw in _images(figure).items()})
        payloads[f"{stem}.csv"] = _csv(rows)
        payloads[f"{stem}.json"] = sources.json_bytes(group)
        figure = _figure((12, 7))
        cost_axis, failure_axis = figure.subplots(1, 2)
        cost_rows = []
        for arm, color in zip(ARMS, COLORS, strict=True):
            values, available = [], 0
            for block in range(1, blocks + 1):
                record = by_identity[model, block, arm]
                value = record["costs"].get("worker_wall_seconds")
                values.append(np.nan if value is None else value)
                available += value is not None
                cost_rows.append(
                    {
                        "block": block,
                        "arm": arm,
                        "package_status": record["status"],
                        "worker_wall_seconds": value,
                        "cost_status": "unknown" if value is None else "known",
                    }
                )
            cost_axis.plot(
                range(1, blocks + 1),
                values,
                marker="o",
                ms=4,
                color=color,
                label=f"{LABELS[arm]}: Kosten {available}/{blocks}",
            )
        failures = [group["arms"][arm]["failed_or_not_run"] for arm in ARMS]
        failure_axis.bar([LABELS[arm] for arm in ARMS], failures, color=COLORS)
        for index, count in enumerate(failures):
            failure_axis.text(
                index, count, f"{count}/{blocks}", ha="center", va="bottom"
            )
        cost_axis.set(
            xlabel="Block",
            ylabel="Gemessene Workerzeit / s",
            title=f"{model}: enthaltene Workerzeiten je Paket",
        )
        cost_axis.legend(fontsize=8)
        failure_axis.set(
            ylabel="Ausgefallen oder nicht ausgeführt",
            title="Geplanter Nenner bleibt erhalten",
        )
        failure_axis.set_ylim(0, max(1, max(failures) * 1.2))
        figure.text(
            0.03,
            0.02,
            "Unbekannte Kosten werden nicht als null ersetzt. Workerzeiten sind Teil der vollständigen Aufrufkosten; nicht addieren.\nFeste Armpositionen begrenzen Laufzeitvergleiche. O und K wurden nur einmal je Block berechnet.",
            fontsize=8,
        )
        figure.tight_layout(rect=(0, 0.08, 1, 1))
        stem = f"{model}-costs-failures"
        payloads.update({f"{stem}.{ext}": raw for ext, raw in _images(figure).items()})
        payloads[f"{stem}.csv"] = _csv(cost_rows)
        covariance_rows = []
        for case in prepared.cases.values():
            if case.spec["noise_model"] != model:
                continue
            for arm in ARMS[2:]:
                estimate = case.record["covariance_estimation"][arm]
                diagnostic = case.record["covariance_diagnostics"][arm]
                covariance_rows.append(
                    {
                        "block": case.spec["block"],
                        "arm": arm,
                        "status": case.record["arm_status"][arm],
                        "alpha": None
                        if estimate is None
                        else estimate["alpha_selected"],
                        "condition_number": diagnostic["condition_number"]["estimated"][
                            "value"
                        ],
                        "relative_frobenius_error": diagnostic[
                            "relative_frobenius_error"
                        ]["value"],
                        "check_score": diagnostic["background_check"]["estimated"][
                            "value"
                        ],
                        "true_check_score": diagnostic["background_check"]["true"][
                            "value"
                        ],
                    }
                )
        figure = _figure((12, 8))
        axes = figure.subplots(2, 2).flat
        for axis, (key, label) in zip(
            axes,
            (
                ("alpha", "Validierungsgewähltes Alpha"),
                ("condition_number", "Konditionszahl"),
                ("relative_frobenius_error", "Relativer Frobenius-Matrixfehler"),
                ("check_score", "Unabhängiger Gauß-Kontrollscore"),
            ),
            strict=True,
        ):
            for arm, color in zip(ARMS[2:], COLORS[2:], strict=True):
                chosen = [row for row in covariance_rows if row["arm"] == arm]
                count = sum(row[key] is not None for row in chosen)
                axis.plot(
                    [row["block"] for row in chosen],
                    [np.nan if row[key] is None else row[key] for row in chosen],
                    marker="o",
                    ms=4,
                    color=color,
                    label=f"{LABELS[arm]}: {count}/{blocks}",
                )
            if key == "check_score":
                chosen = [row for row in covariance_rows if row["arm"] == ARMS[2]]
                axis.plot(
                    [row["block"] for row in chosen],
                    [
                        np.nan
                        if row["true_check_score"] is None
                        else row["true_check_score"]
                        for row in chosen
                    ],
                    color=COLORS[1],
                    linestyle="--",
                    label="Bekannte wahre Kovarianz",
                )
            axis.set(xlabel="Block", title=label)
            axis.legend(fontsize=7)
            axis.grid(alpha=0.2)
        figure.suptitle(f"{model}: Hintergrunddiagnosen, keine SR-Auswahlregel")
        figure.tight_layout(rect=(0, 0, 1, 0.95))
        stem = f"{model}-covariance"
        payloads.update({f"{stem}.{ext}": raw for ext, raw in _images(figure).items()})
        payloads[f"{stem}.csv"] = _csv(covariance_rows)
    return payloads


def _validate_output(output, roots):
    output = publication.validate_output(output)
    for root in roots:
        path = Path(root).absolute()
        if path != path.resolve() or not path.is_dir():
            raise ValueError(
                "Plot inputs must be existing directories without symlinks."
            )
        if output.is_relative_to(path) or path.is_relative_to(output):
            raise ValueError("Plot export must not overlap original artifacts.")
    return output


def _hold(roots, consumed, *, adjacent=()):
    binding = {}
    for name, root in roots.items():
        root = Path(root).absolute()
        _snapshot_tree(root, consumed)
        binding[name] = {
            path.relative_to(root).as_posix(): sources.sha256(raw)
            for path, raw in consumed.files.items()
            if path.is_relative_to(root)
        }
    for path in adjacent:
        path = Path(path).absolute()
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing original whole-call timing.")
        raw = path.read_bytes()
        consumed.add(path, raw)
        binding[path.name] = sources.sha256(raw)
    return binding


TIMING_SCOPE = (
    "transaction_entry_through_publication_and_handler_teardown_"
    "excluding_timing_write_and_final_rechecks"
)


def _timing_path(root):
    return Path(root).with_name(Path(root).name + "-call.json")


def _call_record(started_at, started, usage, report_raw, *, error=None):
    after = inputs._cpu_usage()
    return {
        "format": FORMAT + "-call",
        "status": "completed" if error is None else "aborted",
        "error": None if error is None else f"{type(error).__name__}: {error}",
        "source_report_sha256": None
        if report_raw is None
        else sources.sha256(report_raw),
        "started_at_utc": started_at,
        "finished_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": after[0] - usage[0],
        "cpu_system_seconds": after[1] - usage[1],
        "cpu_scope": "self_plus_reaped_children",
        "measurement_scope": TIMING_SCOPE
        if error is None
        else "transaction_entry_through_abort_and_revocation_excluding_timing_write",
    }


def _verify_call(record, report_raw):
    expected_keys = {
        "format",
        "status",
        "error",
        "source_report_sha256",
        "started_at_utc",
        "finished_at_utc",
        "wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "cpu_scope",
        "measurement_scope",
    }
    if (
        type(record) is not dict
        or set(record) != expected_keys
        or record["format"] != FORMAT + "-call"
        or record["status"] != "completed"
        or record["error"] is not None
        or record["cpu_scope"] != "self_plus_reaped_children"
        or record["measurement_scope"] != TIMING_SCOPE
        or record["source_report_sha256"] != sources.sha256(report_raw)
        or not all(
            type(record[key]) is str and record[key]
            for key in ("started_at_utc", "finished_at_utc")
        )
    ):
        raise ValueError("Unbound or incomplete plot-export call costs.")
    try:
        start, finish = (
            datetime.fromisoformat(record[key])
            for key in ("started_at_utc", "finished_at_utc")
        )
    except ValueError as error:
        raise ValueError("Invalid plot-export UTC timestamps.") from error
    if (
        start.utcoffset() != timedelta(0)
        or finish.utcoffset() != timedelta(0)
        or finish < start
    ):
        raise ValueError("Invalid plot-export UTC time order.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if not _finite(record[name]) or record[name] < 0:
            raise ValueError("Invalid measured plot-export cost.")
    if record["wall_seconds"] >= SECONDS:
        raise ValueError("Plot export exceeded its complete-call deadline.")


def _verify_payload_binding(report, payloads):
    """Require the promised slots and bind each table/formula to its metadata."""
    technical = report.get("technical")
    if type(technical) is not bool:
        raise ValueError("Plot export lacks its scientific/technical identity.")
    specs = inputs.case_specs(technical=technical)
    slots = {f"{spec['id']}-{arm}": (spec, arm) for spec in specs for arm in ARMS}
    outputs = report.get("outputs")
    if (
        type(outputs) is not dict
        or set(outputs) != set(slots)
        or type(report.get("planned_outputs")) is not int
        or report["planned_outputs"] != len(slots)
    ):
        raise ValueError("Plot output inventory differs from the frozen planned slots.")
    required = {publication.REPORT, publication.SUMMARY, publication.MANIFEST}
    required.update(
        f"{stem}.{suffix}"
        for stem in slots
        for suffix in ("csv", "json", "formula.txt", "png", "svg")
    )
    if not technical:
        for model in assessment.PLANNED_BLOCKS:
            for kind in ("errors-contrasts", "costs-failures", "covariance"):
                required.update(
                    f"{model}-{kind}.{ext}" for ext in ("csv", "png", "svg")
                )
            required.add(f"{model}-errors-contrasts.json")
    if set(payloads) != required or payloads[publication.SUMMARY] != SUMMARY.encode():
        raise ValueError("Plot payload inventory or summary is incomplete or changed.")
    data_names = required - {
        publication.REPORT,
        publication.SUMMARY,
        publication.MANIFEST,
    }
    if report.get("payload_sha256") != {
        name: sources.sha256(payloads[name]) for name in sorted(data_names)
    }:
        raise ValueError("Plot payloads contradict their original completion report.")
    for stem, (spec, arm) in slots.items():
        declared = outputs[stem]
        raw = payloads[stem + ".json"]
        metadata = sources.read_json(raw)
        if (
            type(declared) is not dict
            or set(declared) != {"identity", "status", "metadata_sha256"}
            or declared["metadata_sha256"] != sources.sha256(raw)
            or metadata.get("format") != FORMAT
            or metadata.get("technical") is not technical
            or metadata.get("status") != declared["status"]
            or metadata.get("identity") != declared["identity"]
            or metadata.get("series") != report.get("source")
        ):
            raise ValueError(
                "Plot metadata contradicts its original completion report."
            )
        identity = metadata["identity"]
        if type(identity) is not dict or any(
            identity.get(key) != value
            for key, value in {
                "case": spec["id"],
                "model": spec["noise_model"],
                "block": spec["block"],
                "arm": arm,
            }.items()
        ):
            raise ValueError("Plot metadata has a different case or arm identity.")
        table = payloads[stem + ".csv"]
        if metadata.get("points_csv_sha256") != sources.sha256(table):
            raise ValueError("Plot CSV differs from its bound numerical data.")
        rows = list(csv.DictReader(io.StringIO(table.decode())))
        if (
            type(metadata.get("point_count")) is not int
            or len(rows) != metadata["point_count"]
        ):
            raise ValueError("Plot CSV point count differs from its metadata.")
        candidate = metadata.get("candidate")
        equation = (
            candidate["display_equation"]
            if candidate is not None
            else "Keine Originalformel verfügbar: " + str(metadata.get("reason"))
        )
        if payloads[stem + ".formula.txt"] != equation.encode():
            raise ValueError("Plot formula differs from the unchanged original text.")


def _verify_export(root, consumed):
    root = Path(root).absolute()
    if root != root.resolve() or not root.is_dir():
        raise ValueError("Expected an existing regular plot export.")
    _snapshot_tree(root, consumed)
    raw_manifest = (root / publication.MANIFEST).read_bytes()
    manifest = sources.read_json(raw_manifest)
    if type(manifest) is not dict:
        raise ValueError("Plot manifest must bind a complete payload inventory.")
    for name in manifest:
        if len(sources.safe_name(name).parts) != 1 or name in {
            publication.MANIFEST,
            publication.LOCK,
        }:
            raise ValueError("Unsafe or recursive plot manifest entry.")
    expected = {name: (root / name).read_bytes() for name in manifest}
    if manifest != {name: sources.sha256(raw) for name, raw in expected.items()}:
        raise ValueError("Plot payload checksum differs.")
    expected[publication.MANIFEST] = raw_manifest
    publication.verify_bytes(root, expected, locked=False)
    consumed.callbacks.append(
        lambda: publication.verify_bytes(root, expected, locked=False)
    )
    report_raw = expected[publication.REPORT]
    report = sources.read_json(report_raw)
    if report.get("format") != FORMAT or report.get("status") != "completed":
        raise ValueError("Plot export is incomplete or revoked.")
    _verify_payload_binding(report, expected)
    timing = _timing_path(root)
    if timing.is_symlink() or not timing.is_file():
        raise ValueError("Plot-export cost sidecar is missing or unsafe.")
    raw = timing.read_bytes()
    consumed.add(timing, raw)
    _verify_call(sources.read_json(raw), report_raw)
    consumed.check()
    return report


def verify_export(output, consumed=None):
    """Read-check the complete plot payload inventory and separately bound costs.

    This checks saved output bytes, not a new renderer or a new scientific run.
    Scientific source verification is performed before each original export.
    """
    if consumed is not None:
        return _verify_export(output, consumed)
    consumed = publication.Consumption(publication.Deadline(SECONDS))
    with consumed.clock.active():
        report = _verify_export(output, consumed)
    consumed.check()
    return report


def _transaction(output, build):
    started_at, started, usage = _utc_now(), time.monotonic(), inputs._cpu_usage()
    timing = publication.validate_output(_timing_path(output))
    closing, active = [], []

    def assemble(consumed):
        active.append(consumed)
        report, payloads = build(consumed)
        report = {
            **report,
            "payload_sha256": {
                name: sources.sha256(raw) for name, raw in sorted(payloads.items())
            },
        }
        expected = {
            **payloads,
            publication.REPORT: sources.json_bytes({**report, "status": "completed"}),
            publication.SUMMARY: SUMMARY.encode(),
        }
        expected[publication.MANIFEST] = sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in expected.items()}
        )
        closing.append(expected)
        return report, SUMMARY, payloads

    try:
        report = publication.export_transaction(output, assemble, seconds=SECONDS)
        consumed, expected = active[0], closing[0]
        record = _call_record(started_at, started, usage, expected[publication.REPORT])
        _verify_call(record, expected[publication.REPORT])
        raw = sources.json_bytes(record)
        timing.write_bytes(raw)
        consumed.add(timing, raw)
        # Handler teardown and timing publication retain source/output guards.
        destination = Path(output)
        for name, contents in expected.items():
            consumed.add(destination / name, contents)
        consumed.callbacks.append(
            lambda: publication.verify_bytes(destination, expected, locked=False)
        )
        consumed.check()
        return report
    except BaseException as error:
        path = Path(output)
        if active and path.is_dir():
            publication.revoke(path, error, active[0].clock)
            try:
                report_raw = closing[0][publication.REPORT] if closing else None
                timing.write_bytes(
                    sources.json_bytes(
                        _call_record(
                            started_at, started, usage, report_raw, error=error
                        )
                    )
                )
            except BaseException as cost_error:  # noqa: BLE001 -- Preserve the initiating failure.
                error.add_note(
                    "Could not retain aborted plot-export costs: "
                    + f"{type(cost_error).__name__}: {cost_error}"
                )
        raise


def export(preparation, technical_path, series, output):
    """Verify the whole scientific series, then export every original output."""
    from . import noise_background as study

    roots = {"inputs": preparation, "technical": technical_path, "series": series}
    output = _validate_output(output, roots.values())

    def build(consumed):
        binding = _hold(
            roots,
            consumed,
            adjacent=(
                Path(preparation).with_name(Path(preparation).name + "-call.json"),
                Path(series).with_name(Path(series).name + "-call.json"),
            ),
        )
        report = study.verify(preparation, technical_path, series, consumed=consumed)
        prepared = inputs.verify_inputs(preparation, consumed)
        source = {
            "run_id": Path(series).name,
            "execution_software": report["software"],
            "verification_software": prepared.manifest["software"],
            "source_report_sha256": sources.sha256(
                (Path(series) / "completion" / publication.REPORT).read_bytes()
            ),
        }
        records = report["assessments"]
        if len(records) != 130:
            raise ValueError(
                "The scientific plot export requires all 130 planned outputs."
            )
        payloads, outputs = {}, {}
        for record in records:
            consumed.check()
            identity = record["source_identity"]
            case_id = f"{identity['model']}-{identity['block']:02d}"
            stem, metadata, files = _output_payload(
                record,
                prepared,
                prepared.cases[case_id],
                technical=False,
                series_identity=source,
            )
            if stem in outputs:
                raise ValueError("Duplicate plot output identity.")
            outputs[stem] = {
                "identity": metadata["identity"],
                "status": metadata["status"],
                "metadata_sha256": sources.sha256(files[stem + ".json"]),
            }
            payloads.update(files)
        payloads.update(_overview_payloads(report, prepared))
        consumed.check()
        return {
            "format": FORMAT,
            "technical": False,
            "source": source,
            "source_artifact_sha256": binding,
            "outputs": outputs,
            "planned_outputs": 130,
            "renderer": {
                "matplotlib": matplotlib.__version__,
                "numpy": np.__version__,
                "backend": "Agg",
                "points_only": True,
            },
            "selection_changed": False,
            "fits_or_searches_executed": False,
        }, payloads

    return _transaction(output, build)


def export_technical(technical_path, output):
    """Plot the five verified tiny workers, without scientific success assessment."""
    from . import noise_background_technical as technical

    output = _validate_output(output, (technical_path,))

    def build(consumed):
        binding = _hold({"technical": technical_path}, consumed)
        report = technical.verify(technical_path, consumed=consumed)
        prepared = inputs.verify_inputs(Path(technical_path) / "inputs", consumed)
        case = prepared.cases["technical-ar1"]
        source = {
            "run_id": Path(technical_path).name,
            "execution_software": report["software"],
            "verification_software": prepared.manifest["software"],
            "source_report_sha256": sources.sha256(
                (Path(technical_path) / "completion" / publication.REPORT).read_bytes()
            ),
        }
        payloads, outputs = {}, {}
        if set(report["members"]) != set(ARMS):
            raise ValueError("The technical plot export requires all five workers.")
        for arm in ARMS:
            consumed.check()
            member = report["members"][arm]
            record = {
                "status": "success" if member["selected"] is not None else "failed",
                "source_identity": {
                    "model": "ar1",
                    "block": 0,
                    "arm": arm,
                    "selected_member_path": f"{arm}/result.json",
                },
                "original_candidate": member["selected"],
                "costs": member["costs"],
            }
            stem, metadata, files = _output_payload(
                record, prepared, case, technical=True, series_identity=source
            )
            outputs[stem] = {
                "identity": metadata["identity"],
                "status": metadata["status"],
                "metadata_sha256": sources.sha256(files[stem + ".json"]),
            }
            payloads.update(files)
        consumed.check()
        return {
            "format": FORMAT,
            "technical": True,
            "scientific_success_assessed": False,
            "source": source,
            "source_artifact_sha256": binding,
            "outputs": outputs,
            "planned_outputs": 5,
            "renderer": {
                "matplotlib": matplotlib.__version__,
                "numpy": np.__version__,
                "backend": "Agg",
                "points_only": True,
            },
            "selection_changed": False,
            "fits_or_searches_executed": False,
        }, payloads

    return _transaction(output, build)
