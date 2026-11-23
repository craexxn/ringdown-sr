"""Publish all original main-study formulas, grids and failures without selection."""

import copy
import csv
import html
import io
import re
import resource
import time
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import main_study_assessment as assessment
from . import main_study_inputs as inputs
from . import noise_background_plots as shared
from .pilot import _utc_now
from .structure import _validated_tree

FORMAT = "ringdown-sr-main-study-plots-1"
SECONDS = 14400
LABELS = {
    "ordinary": "O / ungewichtet",
    "known_covariance": "K / bekannte Kovarianz",
    "estimated_64s": "E / 64 s",
    "estimated_4096s": "E / 4096 s",
}
COLORS = ("#2166ac", "#7b3294", "#008837", "#e08214")
ROLES = {
    "training": ("time_s", "signal", "Native Trainingsvorhersage", "#2166ac", "o"),
    "main": ("main_time_s", "main_truth", "Hauptraster [0,25 ms]", "#d95f02", "."),
    "support": ("support_time_s", "support_truth", "Messstützbereich", "#7b3294", "+"),
    "endpoints": (
        "endpoint_time_s",
        "endpoint_truth",
        "Endpunktdiagnose",
        "#222222",
        "x",
    ),
}
SUMMARY = (
    "# Hauptserie: Originalformeln, Plots und Punktdaten\n\n"
    "Alle geplanten Ausgaben der ausdrücklich benannten Signalabschnitte einschließlich "
    "Ausfällen. Native Trainingsvorhersagen und lesender Originalbaum-Replay auf "
    "gebundenen Haupt-, Stützbereichs- und Endpunktachsen bleiben getrennt. "
    "Keine Fits, Suchen, Glättung, Ersatzformeln oder Neuauswahl.\n\n"
    "index.html enthält die unveränderten Originalformeln und Datenlinks. "
    "Punkt-CSV erhalten auch nicht verfügbare Vorhersagen. Lineare Vollansichten "
    "zeigen alle endlichen Werte; Rasterwerte beweisen keinen kontinuierlichen "
    "Verlauf und keine überall definierte Originalformel.\n"
)
TIMING_SCOPE = (
    "transaction_entry_through_publication_and_handler_teardown_"
    "excluding_timing_write_and_final_rechecks"
)


def point_data(candidate, arrays, amplitude, *, reason=None):
    """Keep native training values and every original replay point, including holes."""
    if not shared._finite(amplitude) or amplitude <= 0:
        raise ValueError("Plot amplitude must be finite and positive.")
    if candidate is not None:
        _validated_tree(candidate["tree"])
        if type(candidate.get("display_equation")) is not str:
            raise ValueError("Original formula text is missing.")
    predictions = (
        assessment.prediction_by_role(candidate, arrays)
        if candidate is not None
        else {
            role: {"prediction": None, "reason": reason or "no_original_output"}
            for role in ROLES
        }
    )
    rows, metrics, peaks = [], {}, {}
    for role, (time_key, truth_key, *_display) in ROLES.items():
        times, truth = np.asarray(arrays[time_key]), np.asarray(arrays[truth_key])
        if (
            times.dtype != np.dtype("float64")
            or truth.dtype != np.dtype("float64")
            or times.ndim != 1
            or times.shape != truth.shape
            or not times.size
            or not np.isfinite(times).all()
            or not np.isfinite(truth).all()
        ):
            raise ValueError("Plot references require finite bound Float64 vectors.")
        metric_prediction = predictions[role]["prediction"]
        metric_reason = predictions[role]["reason"]
        if candidate is None:
            metric_reason = reason or "no_original_output"
            prediction = np.full(times.shape, np.nan)
            reasons = [metric_reason] * len(times)
        elif role == "training":
            prediction = np.asarray(candidate["prediction"], dtype=np.float64)
            if prediction.shape != times.shape or not np.isfinite(prediction).all():
                raise ValueError(
                    "Native selected predictions changed or are nonfinite."
                )
            reasons = [None] * len(times)
        else:
            prediction, reasons = shared._replay(candidate["tree"], times)
        metrics[role] = assessment.curve_metrics(
            metric_prediction, truth, amplitude, reason=metric_reason
        )
        complete = bool(np.isfinite(prediction).all())
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            residual = prediction - truth
            normalized = residual / amplitude
        peak = None
        for index, time_s in enumerate(times):
            value, error, scaled = (
                shared._number(prediction[index]),
                shared._number(residual[index]),
                shared._number(normalized[index]),
            )
            observed = (
                shared._number(arrays["observed"][index])
                if role == "training" and "observed" in arrays
                else None
            )
            point_reason = reasons[index]
            if point_reason is None and (error is None or scaled is None):
                point_reason = "residual_or_normalization_out_of_range"
            rows.append(
                {
                    "grid": role,
                    "index_zero_based": index,
                    "time_s": float(time_s),
                    "time_hex": float(time_s).hex(),
                    "truth": float(truth[index]),
                    "truth_hex": float(truth[index]).hex(),
                    "observed": observed,
                    "observed_hex": shared._hex(observed),
                    "prediction": value,
                    "prediction_hex": shared._hex(value),
                    "prediction_origin": "stored_native"
                    if role == "training"
                    else "read_only_original_binary_tree",
                    "residual": error,
                    "residual_over_amplitude": scaled,
                    "status": "available" if point_reason is None else "not_available",
                    "reason": point_reason,
                }
            )
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
    figure = shared._figure((12, 8.5))
    top, bottom = figure.subplots(2, 1, sharex=True)
    for role, (_time, _truth, label, color, marker) in ROLES.items():
        selected = [row for row in rows if row["grid"] == role]
        for axis, field in ((top, "prediction"), (bottom, "residual_over_amplitude")):
            axis.scatter(
                [row["time_s"] for row in selected],
                [np.nan if row[field] is None else row[field] for row in selected],
                color=color,
                marker=marker,
                s=12,
                alpha=0.8,
                label=label,
            )
            missing = [
                row["time_s"] for row in selected if row["status"] != "available"
            ]
            if missing:
                axis.scatter(
                    missing,
                    np.full(len(missing), 0.025),
                    transform=axis.get_xaxis_transform(),
                    color="red",
                    marker="x",
                    label=f"{role}: {len(missing)} nicht verfügbar",
                )
    truth = sorted((row["time_s"], row["truth"]) for row in rows)
    top.plot(
        *zip(*truth, strict=True),
        color="#006837",
        linewidth=1,
        label="Saubere Wahrheit: verbundene gespeicherte Punkte",
    )
    observed = [row for row in rows if row["observed"] is not None]
    top.scatter(
        [row["time_s"] for row in observed],
        [row["observed"] for row in observed],
        marker="x",
        color="#888888",
        s=14,
        label="Verrauschte Messwerte",
    )
    identity = metadata["identity"]
    suffix = " / technischer Vorlauf" if metadata["technical"] else ""
    figure.suptitle(
        f"{identity['case_id']} / {LABELS[identity['condition']]} / "
        f"{metadata['status']}{suffix}",
        fontsize=11,
    )
    top.set_ylabel("Signalwert / dimensionslos")
    bottom.set_ylabel("(Originalvorhersage − saubere Wahrheit) / |A|")
    bottom.set_xlabel("t / Sekunden")
    bottom.axhline(0, color="#777777", linewidth=0.7)
    for axis in (top, bottom):
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7, loc="best")
    figure.text(
        0.025,
        0.015,
        f"Unveränderte Originalformel: {stem}.formula.txt; "
        f"Originalbaum/Quellen: {stem}.json; sämtliche Punkte: {stem}.csv\n"
        "Lineare Vollansicht; keine Glättung. Punkte und Verbindungen der Wahrheit "
        "belegen keinen kontinuierlichen Verlauf oder Definitionsbereich.",
        fontsize=7,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 0.95))
    return shared._images(figure)


def _selection(record, case, technical):
    if technical:
        return {"member_position": 1, "seed": case.spec["search_seeds"][0]}
    identity = record["source_identity"]
    path = identity["selected_member_path"]
    if record["original_candidate"] is None:
        if path is not None:
            raise ValueError("Unavailable output has a selected member.")
        return {"member_position": None, "seed": None}
    match = re.fullmatch(r"symbolic/([^/]+)/member-(\d{2})/result\.json", str(path))
    if (
        match is None
        or match[1] != identity["condition"]
        or not 1 <= int(match[2]) <= 4
    ):
        raise ValueError("Original selection is not bound to its condition.")
    position = int(match[2])
    return {
        "member_position": position,
        "seed": case.spec["search_seeds"][position - 1],
    }


def _output_payload(record, prepared, case, *, source, technical=False):
    identity = record["source_identity"]
    condition = identity["condition"]
    if condition not in LABELS or identity["case_id"] != case.spec["id"]:
        raise ValueError("Unknown plot condition or case.")
    stem = case.spec["id"] + "-" + condition
    sources.safe_name(stem)
    arrays = inputs.arm_arrays(prepared, case, condition)
    candidate = record["original_candidate"]
    reason = record.get("reason") or record.get("primary", {}).get("reason")
    amplitude = abs(float(case.spec["signal"]["amplitude"]))
    rows, metrics, peaks = point_data(candidate, arrays, amplitude, reason=reason)
    if not technical and candidate is not None:
        sources._same(
            metrics,
            record["errors"],
            "Plot errors differ from the verified assessment.",
        )
    table = shared._csv(rows)
    metadata = {
        "format": FORMAT,
        "technical": technical,
        "scientific_success_assessed": False,
        "identity": {**copy.deepcopy(identity), **_selection(record, case, technical)},
        "source": source,
        "status": record["status"],
        "reason": reason,
        "candidate": copy.deepcopy(candidate),
        "amplitude": amplitude,
        "units": {"time": "seconds", "signal": "dimensionless"},
        "metrics": metrics,
        "peaks": peaks,
        "costs": copy.deepcopy(record["costs"]),
        "cost_scope": "Original worker costs; do not add to enclosing package or section costs.",
        "supplemental": copy.deepcopy(record.get("supplemental")),
        "topology_descriptor": copy.deepcopy(record.get("topology_descriptor")),
        "point_count": len(rows),
        "reference_binding": {
            role: {
                "time_s": sources.fingerprint(arrays[time_key]),
                "truth": sources.fingerprint(arrays[truth_key]),
            }
            for role, (time_key, truth_key, *_display) in ROLES.items()
        },
        "grid_point_counts": {
            role: len(arrays[values[0]]) for role, values in ROLES.items()
        },
        "points_csv_sha256": sources.sha256(table),
        "interpretation": "Bound saved points; no smoothing, fit, reselection or continuous-domain claim.",
    }
    equation = (
        candidate["display_equation"]
        if candidate is not None
        else "Keine Originalformel verfügbar: " + str(reason)
    )
    payloads = {
        stem + ".json": sources.json_bytes(metadata),
        stem + ".csv": table,
        stem + ".formula.txt": equation.encode(),
    }
    payloads.update(
        {
            stem + "." + ext: raw
            for ext, raw in _curve_plot(metadata, rows, stem).items()
        }
    )
    return stem, metadata, payloads


def _overview_payloads(report):
    signal_id = report["signal_id"]
    payloads = {signal_id + "-summary.json": sources.json_bytes(report["summary"])}
    for model in assessment.PLANNED_BLOCKS:
        records = [
            r for r in report["assessments"] if r["source_identity"]["model"] == model
        ]
        rows = []
        figure = shared._figure((13, 7))
        error_axis, cost_axis = figure.subplots(1, 2)
        for condition, color in zip(LABELS, COLORS, strict=True):
            group = [
                r for r in records if r["source_identity"]["condition"] == condition
            ]
            for record in group:
                identity = record["source_identity"]
                supplemental = record.get("supplemental") or {}
                rows.append(
                    {
                        "signal_id": signal_id,
                        "model": model,
                        "block": identity["block"],
                        "condition": condition,
                        "status": record["status"],
                        "primary_status": record["primary"]["status"],
                        "primary_reason": record["primary"]["reason"],
                        "relative_l2_main": record["primary"]["value"],
                        "original_worker_wall_seconds": record["costs"].get(
                            "worker_wall_seconds"
                        ),
                        "search_calls": record["search_calls"],
                        "original_family": supplemental.get("original_family", {}).get(
                            "status"
                        ),
                        "original_domain": supplemental.get("domain", {}).get("status"),
                    }
                )
            for axis, getter in (
                (error_axis, lambda r: r["primary"]["value"]),
                (cost_axis, lambda r: r["costs"].get("worker_wall_seconds")),
            ):
                axis.plot(
                    [r["source_identity"]["block"] for r in group],
                    [np.nan if getter(r) is None else getter(r) for r in group],
                    linestyle="none",
                    marker="o",
                    color=color,
                    label=LABELS[condition],
                )
                missing = [
                    r["source_identity"]["block"] for r in group if getter(r) is None
                ]
                if missing:
                    axis.scatter(
                        missing,
                        np.full(len(missing), 0.025),
                        transform=axis.get_xaxis_transform(),
                        marker="x",
                        color=color,
                        label=f"{LABELS[condition]}: {len(missing)} fehlen",
                    )
        error_axis.set_ylabel("Relativer L2-Fehler auf gebundenem Hauptraster")
        cost_axis.set_ylabel("Gemessene Workerzeit / s")
        for axis in (error_axis, cost_axis):
            axis.set_xlabel("Unabhängiger Fallblock")
            axis.grid(alpha=0.2)
            axis.legend(fontsize=7)
        figure.suptitle(f"{signal_id} / {model}: alle geplanten Ausgaben")
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        stem = f"{signal_id}-{model}-overview"
        payloads[stem + ".csv"] = shared._csv(rows)
        payloads.update(
            {stem + "." + ext: raw for ext, raw in shared._images(figure).items()}
        )

        contrasts = report["summary"]["signals"][signal_id]["models"][model][
            "contrasts"
        ]
        contrast_rows, summary_rows = [], []
        figure = shared._figure((15, 8))
        axis, interval_axis = figure.subplots(1, 2)
        for index, (name, contrast) in enumerate(contrasts.items()):
            entries, interval = contrast["values"], contrast["interval"]
            axis.plot(
                [entry["block"] for entry in entries],
                [
                    np.nan if entry["value"] is None else entry["value"]
                    for entry in entries
                ],
                marker="o",
                linestyle="none",
                label=name,
            )
            missing = [entry["block"] for entry in entries if entry["value"] is None]
            if missing:
                axis.scatter(
                    missing,
                    np.full(len(missing), 0.025 + index * 0.025),
                    transform=axis.get_xaxis_transform(),
                    marker="x",
                    label=f"{name}: {len(missing)} Paare fehlen",
                )
            contrast_rows.extend({"contrast": name, **entry} for entry in entries)
            summary_rows.append(
                {
                    "contrast": name,
                    "primary": contrast["is_primary"],
                    "mean": contrast["mean"],
                    "sample_sd": contrast["sample_sd"],
                    "mcse": contrast["mcse"],
                    **{"interval_" + key: value for key, value in interval.items()},
                }
            )
            if contrast["mean"] is not None:
                interval_axis.plot(contrast["mean"], index, marker="o", color="#2166ac")
            if interval["status"] == "available":
                interval_axis.plot(
                    [interval["lower"], interval["upper"]],
                    [index, index],
                    color="#2166ac",
                )
            else:
                interval_axis.text(
                    0.02,
                    index,
                    "Intervall nicht verfügbar",
                    transform=interval_axis.get_yaxis_transform(),
                    fontsize=7,
                )
        axis.axhline(0, color="#777777", linewidth=0.7)
        axis.set_xlabel("Gepaarter Fallblock")
        axis.set_ylabel("Differenz des relativen L2-Fehlers")
        axis.grid(alpha=0.2)
        axis.legend(fontsize=6)
        interval_axis.set_yticks(range(len(contrasts)), contrasts, fontsize=6)
        interval_axis.axvline(0, color="#777777", linewidth=0.7)
        interval_axis.set_xlabel("Mittelwert / approximatives t-Intervall")
        interval_axis.set_title(
            "Primär 97,5 %; sekundär 95 % deskriptiv\nFehlende Paare: nur bedingte Deskription",
            fontsize=9,
        )
        interval_axis.grid(alpha=0.2)
        figure.suptitle(f"{signal_id} / {model}: vorab festgelegte gepaarte Kontraste")
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        stem = f"{signal_id}-{model}-contrasts"
        payloads[stem + ".csv"] = shared._csv(contrast_rows)
        payloads[stem + "-summary.csv"] = shared._csv(summary_rows)
        payloads[stem + ".json"] = sources.json_bytes(contrasts)
        payloads.update(
            {stem + "." + ext: raw for ext, raw in shared._images(figure).items()}
        )
    return payloads


def _index(metadata, signal_ids, technical, normalizations=None):
    parts = [
        '<!doctype html><html lang="de"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Hauptserie: unveränderte Originalausgaben</title>",
        (
            "<style>body{font:16px system-ui;max-width:1200px;margin:auto;padding:20px}"
            "img{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
            "article{border-top:1px solid #aaa;padding:20px 0}a{margin-right:12px}</style>"
        ),
        "<h1>Hauptserie: unveränderte Originalausgaben</h1>",
        (
            "<p>Vollständige Originalformeln und alle gespeicherten Punkte einschließlich "
            "Ausfällen. Keine Neuauswahl, Fits, Suchen oder Glättung. Lineare Vollansichten; "
            "Rasterwerte belegen keinen kontinuierlichen Verlauf oder gültigen Definitionsbereich.</p>"
        ),
        (
            "<p>t in Sekunden; Signalwerte dimensionslos. Familiennachweis und richtige "
            "physikalische Parameter sind getrennte Fragen.</p>"
        ),
    ]
    if technical:
        parts.append(
            "<p>Acht technische Zehn-Iterationen-Worker; keine wissenschaftliche Erfolgsbewertung.</p>"
        )
    else:
        if type(normalizations) is not dict or set(normalizations) != set(signal_ids):
            raise ValueError("Plot noise normalization omits a signal section.")
        parts.append(
            "<p>Enthaltene Signalabschnitte: "
            + html.escape(", ".join(signal_ids))
            + ".</p>"
        )
        for signal_id in signal_ids:
            normalization = normalizations[signal_id]
            if (
                type(normalization) is not dict
                or normalization.get("signal_id") != signal_id
                or normalization.get("rms_reference")
                != "clean_signal_equal_weight_training_samples"
                or normalization.get("n_samples") != inputs.N_SAMPLES
                or normalization.get("signal_unit") != "dimensionless"
                or normalization.get("time_unit") != "s"
                or normalization.get("interpretation")
                != "marginal_noise_ratios_not_detector_snr"
                or any(
                    not shared._finite(normalization.get(key))
                    or normalization[key] <= 0
                    for key in (
                        "amplitude",
                        "noise_standard_deviation",
                        "noise_over_amplitude",
                        "training_signal_rms",
                        "noise_over_training_signal_rms",
                    )
                )
            ):
                raise ValueError("Missing or invalid bound signal normalization.")
            parts.append(
                f"<p><strong>{html.escape(signal_id)}:</strong> "
                f"σ / |A| = {normalization['noise_over_amplitude']:.8g}; "
                f"σ / RMS(s) = {normalization['noise_over_training_signal_rms']:.8g}. "
                f"RMS(s) = {normalization['training_signal_rms']:.8g}, "
                f"σ = {normalization['noise_standard_deviation']:.8g}, "
                f"jeweils dimensionslos. RMS aus den {normalization['n_samples']} "
                "gleich gewichteten sauberen Werten auf dem ursprünglichen "
                "Messraster; kein Detektor-SNR.</p>"
            )
            parts.append(
                f'<p><a href="{signal_id}-summary.json">{signal_id}: vollständige Statistik JSON</a></p>'
            )
            for model in assessment.PLANNED_BLOCKS:
                for kind in ("overview", "contrasts"):
                    stem = f"{signal_id}-{model}-{kind}"
                    parts.append(
                        f'<p><a href="{stem}.png">{stem} PNG</a>'
                        f'<a href="{stem}.svg">SVG</a><a href="{stem}.csv">CSV</a></p>'
                    )
                    if kind == "contrasts":
                        parts.append(
                            f'<p><a href="{stem}-summary.csv">Kontraststatistik / Intervalle CSV</a>'
                            f'<a href="{stem}.json">Kontraststatistik JSON</a></p>'
                        )
    for stem, record in sorted(metadata.items()):
        candidate = record["candidate"]
        equation = (
            candidate["display_equation"]
            if candidate is not None
            else "Keine Originalformel verfügbar: " + str(record["reason"])
        )
        supplemental = record.get("supplemental") or {}
        family = supplemental.get("original_family", {}).get("status", "not_assessed")
        domain = supplemental.get("domain", {}).get("status", "not_assessed")
        parts.extend(
            [
                f'<article id="{html.escape(stem)}"><h2>{html.escape(stem)}</h2>',
                (
                    f"<p>Status: {html.escape(record['status'])}; Originalfamilie: {html.escape(family)}; "
                    f"Originaldomain: {html.escape(domain)}.</p>"
                ),
                f"<pre>{html.escape(equation)}</pre>",
                "<p>"
                + "".join(
                    f'<a href="{stem}.{ext}">{label}</a>'
                    for ext, label in (
                        ("formula.txt", "Originalformel"),
                        ("json", "Originalbaum / Quellen / Befunde"),
                        ("csv", "Alle Punktdaten"),
                        ("png", "PNG"),
                        ("svg", "SVG"),
                    )
                )
                + "</p>",
                f'<img loading="lazy" src="{stem}.png" alt="{html.escape(stem)}"></article>',
            ]
        )
    return "\n".join([*parts, "</html>"]).encode()


def _source(root, report, prepared, consumed):
    path = Path(root) / "completion" / publication.REPORT
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing original completion report.")
    raw = path.read_bytes()
    consumed.add(path, raw)
    return {
        "run_id": Path(root).name,
        "execution_software": report["software"],
        "verification_software": prepared.manifest["software"],
        "source_report_sha256": sources.sha256(raw),
        "preparation_sha256": report.get("preparation_sha256"),
        "technical_report_sha256": report.get("technical_report_sha256"),
        "signal_normalization": copy.deepcopy(report.get("signal_normalization")),
    }


def _build_report(metadata, source, signal_ids, *, technical=False):
    return {
        "format": FORMAT,
        "technical": technical,
        "signal_ids": list(signal_ids),
        "source": source,
        "signal_normalization": None
        if technical
        else {
            key: copy.deepcopy(source[key]["signal_normalization"])
            for key in signal_ids
        },
        "planned_outputs": len(metadata),
        "outputs": {
            stem: {
                "identity": item["identity"],
                "status": item["status"],
                "metadata_sha256": sources.sha256(sources.json_bytes(item)),
            }
            for stem, item in metadata.items()
        },
        "renderer": {
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "backend": "Agg",
            "points_only": True,
            "linear_full_range": True,
        },
        "selection_changed": False,
        "fits_or_searches_executed": False,
    }


def export(preparation, technical_path, series_paths, output, *, previous=None):
    """Verify one or both complete sections, then publish every original slot."""
    from . import main_study as study

    specs = inputs.case_specs(purpose="scientific")
    known = tuple(dict.fromkeys(spec["signal_id"] for spec in specs))
    if (
        type(series_paths) is not dict
        or not series_paths
        or not set(series_paths) <= set(known)
    ):
        raise ValueError("Expected explicit known signal sections to export.")
    signal_ids = [key for key in known if key in series_paths]
    output = shared._validate_output(
        output,
        [
            preparation,
            technical_path,
            *series_paths.values(),
            *([] if previous is None else [previous]),
        ],
    )
    if previous is not None and known[0] in series_paths:
        raise ValueError(
            "Use the included first section instead of a second previous source."
        )

    def build(consumed):
        prepared = inputs.verify_inputs(preparation, consumed, regenerate=False)
        payloads, metadata, section_sources = {}, {}, {}
        for signal_id in signal_ids:
            prior = (
                None if signal_id == known[0] else series_paths.get(known[0], previous)
            )
            report = study.verify(
                preparation,
                technical_path,
                series_paths[signal_id],
                signal_id=signal_id,
                previous=prior,
                consumed=consumed,
            )
            sources._same(
                report["summary"],
                assessment.summary(report["assessments"], signal_id=signal_id),
                "Plot source summary changed.",
            )
            source = _source(series_paths[signal_id], report, prepared, consumed)
            section_sources[signal_id] = source
            indexed = {}
            for record in report["assessments"]:
                identity = record["source_identity"]
                key = identity["case_id"], identity["condition"]
                if identity["signal_id"] != signal_id or key in indexed:
                    raise ValueError("Duplicate or cross-signal original plot slot.")
                indexed[key] = record
            selected_specs = [
                spec
                for spec in prepared.cases.values()
                if spec["signal_id"] == signal_id
            ]
            expected = {(spec["id"], arm) for spec in selected_specs for arm in LABELS}
            if set(indexed) != expected:
                raise ValueError("Plot inventory omits planned cases or arms.")
            for spec in selected_specs:
                case = inputs.read_case(
                    prepared, spec["id"], consumed=consumed, regenerate=False
                )
                for arm in LABELS:
                    consumed.clock.check()
                    stem, entry, files = _output_payload(
                        indexed[spec["id"], arm], prepared, case, source=source
                    )
                    metadata[stem] = entry
                    payloads.update(files)
            payloads.update(_overview_payloads(report))
        normalizations = {
            key: section_sources[key]["signal_normalization"] for key in signal_ids
        }
        payloads["index.html"] = _index(metadata, signal_ids, False, normalizations)
        return _build_report(metadata, section_sources, signal_ids), payloads

    return _transaction(output, build)


def export_technical(technical_path, output):
    """Publish all eight original short workers without a scientific quality gate."""
    from . import main_study_technical as technical

    output = shared._validate_output(output, (technical_path,))

    def build(consumed):
        report = technical.verify(technical_path, consumed=consumed)
        prepared = inputs.verify_inputs(
            Path(technical_path) / "inputs", consumed, regenerate=False
        )
        specs = list(prepared.cases.values())
        expected = {spec["id"] + "/" + arm for spec in specs for arm in LABELS}
        if len(specs) != 2 or set(report["members"]) != expected:
            raise ValueError(
                "Technical plots require exactly two cases and eight workers."
            )
        source = _source(technical_path, report, prepared, consumed)
        payloads, metadata = {}, {}
        signal_ids = []
        for spec in specs:
            signal_ids.append(spec["signal_id"])
            case = inputs.read_case(
                prepared, spec["id"], consumed=consumed, regenerate=False
            )
            for arm in LABELS:
                consumed.clock.check()
                member = report["members"][spec["id"] + "/" + arm]
                record = {
                    "status": "success" if member["selected"] is not None else "failed",
                    "reason": None
                    if member["selected"] is not None
                    else "technical_worker_no_selected_candidate",
                    "source_identity": {
                        "case_id": spec["id"],
                        "signal_id": spec["signal_id"],
                        "model": spec["noise_model"],
                        "block": spec["block"],
                        "condition": arm,
                        "grid": "uniform",
                        "selected_member_path": f"workers/{spec['id']}/{arm}/result.json",
                    },
                    "original_candidate": member["selected"],
                    "costs": member["costs"],
                }
                stem, entry, files = _output_payload(
                    record, prepared, case, source=source, technical=True
                )
                metadata[stem] = entry
                payloads.update(files)
        payloads["index.html"] = _index(metadata, signal_ids, True)
        return _build_report(metadata, source, signal_ids, technical=True), payloads

    return _transaction(output, build)


def _timing_path(root):
    return Path(root).with_name(Path(root).name + "-call.json")


def _usage():
    values = [
        resource.getrusage(scope)
        for scope in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
    ]
    return tuple(
        sum(getattr(value, field) for value in values)
        for field in ("ru_utime", "ru_stime")
    )


def _call_record(started_at, started, usage, report_raw, *, error=None):
    after = _usage()
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
        "cpu_measurement_complete": error is None,
        "measurement_scope": TIMING_SCOPE
        if error is None
        else "entry_through_abort_excluding_call_write",
    }


def _verify_call(record, report_raw):
    if (
        type(record) is not dict
        or set(record)
        != {
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
            "cpu_measurement_complete",
            "measurement_scope",
        }
        or record.get("format") != FORMAT + "-call"
        or record.get("status") != "completed"
        or record.get("error") is not None
        or record.get("source_report_sha256") != sources.sha256(report_raw)
        or record.get("cpu_scope") != "self_plus_reaped_children"
        or record.get("cpu_measurement_complete") is not True
        or record.get("measurement_scope") != TIMING_SCOPE
    ):
        raise ValueError("Unbound or incomplete main-study plot call.")
    try:
        start, finish = (
            datetime.fromisoformat(record[key])
            for key in ("started_at_utc", "finished_at_utc")
        )
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid main-study plot call timestamps.") from error
    if (
        start.utcoffset() != timedelta(0)
        or finish.utcoffset() != timedelta(0)
        or finish < start
    ):
        raise ValueError("Invalid main-study plot UTC time order.")
    for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if not shared._finite(record.get(key)) or record[key] < 0:
            raise ValueError("Invalid main-study plot call cost.")
    if record["wall_seconds"] >= SECONDS:
        raise ValueError("Main-study plot export exceeded its operational deadline.")


def _transaction(output, build):
    started_at, started, usage = _utc_now(), time.monotonic(), _usage()
    timing = publication.validate_output(_timing_path(output))
    state = {}

    def assemble(consumed):
        state["consumed"] = consumed
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
        state["expected"] = expected
        return report, SUMMARY, payloads

    try:
        report = publication.export_transaction(output, assemble, seconds=SECONDS)
        expected, consumed = state["expected"], state["consumed"]
        raw = sources.json_bytes(
            _call_record(started_at, started, usage, expected[publication.REPORT])
        )
        _verify_call(sources.read_json(raw), expected[publication.REPORT])
        timing.write_bytes(raw)
        consumed.add(timing, raw)
        consumed.callbacks.append(
            lambda: publication.verify_bytes(Path(output), expected, locked=False)
        )
        consumed.check()
        return report
    except BaseException as error:
        if "consumed" in state and Path(output).is_dir():
            publication.revoke(Path(output), error, state["consumed"].clock)
            try:
                timing.write_bytes(
                    sources.json_bytes(
                        _call_record(
                            started_at,
                            started,
                            usage,
                            state.get("expected", {}).get(publication.REPORT),
                            error=error,
                        )
                    )
                )
            except BaseException as cost_error:  # noqa: BLE001 -- Keep the initiating failure.
                error.add_note("Could not retain plot call costs: " + str(cost_error))
        raise


def _verify_points(entry, table, spec):
    rows = list(csv.DictReader(io.StringIO(table.decode())))
    counts = {
        "training": spec["sampling"]["n_samples"],
        "main": inputs.EVALUATION_POINTS,
        "support": inputs.EVALUATION_POINTS,
        "endpoints": 2,
    }
    if (
        entry.get("points_csv_sha256") != sources.sha256(table)
        or entry.get("point_count") != len(rows)
        or entry.get("grid_point_counts") != counts
        or len(rows) != sum(counts.values())
        or set(entry.get("reference_binding", {})) != set(ROLES)
    ):
        raise ValueError(
            "Plot points differ from their original binding or planned grids."
        )
    if any(row.get("grid") not in ROLES for row in rows):
        raise ValueError("Unknown point grid.")
    for role, count in counts.items():
        selected = [row for row in rows if row["grid"] == role]
        if len(selected) != count or [
            row["index_zero_based"] for row in selected
        ] != list(map(str, range(count))):
            raise ValueError("Missing, reordered or duplicated plot points.")
        for field in ("time", "truth", "observed", "prediction"):
            column = "time_s" if field == "time" else field
            for row in selected:
                value = None if row[column] == "" else float(row[column])
                hexadecimal = row[field + "_hex"]
                if value is None:
                    if hexadecimal != "" or field in {"time", "truth"}:
                        raise ValueError(
                            "A missing plot value has an invalid exact representation."
                        )
                elif not shared._finite(value) or hexadecimal != value.hex():
                    raise ValueError("Plot decimal and exact binary values disagree.")
        expected_origin = (
            "stored_native" if role == "training" else "read_only_original_binary_tree"
        )
        if any(row["prediction_origin"] != expected_origin for row in selected):
            raise ValueError("Native and replay plot provenance changed.")
        bound = entry["reference_binding"][role]
        for field, column in (("time_s", "time_s"), ("truth", "truth")):
            values = np.asarray(
                [float(row[column]) for row in selected], dtype=np.float64
            )
            if bound.get(field) != sources.fingerprint(values):
                raise ValueError("Plot reference axis or truth changed.")
        candidate = entry["candidate"]
        if (
            candidate is not None
            and role == "training"
            and [float(row["prediction"]) for row in selected]
            != candidate["prediction"]
        ):
            raise ValueError("Stored native predictions changed in the point table.")
        if candidate is None and any(
            row["prediction"] or row["status"] != "not_available" for row in selected
        ):
            raise ValueError("Unavailable original output acquired a plot prediction.")


def _verify_payloads(report, payloads):
    technical = report.get("technical")
    if (
        type(technical) is not bool
        or report.get("selection_changed") is not False
        or report.get("fits_or_searches_executed") is not False
    ):
        raise ValueError("Plot export contradicts its read-only scope.")
    specs = inputs.case_specs(purpose="technical" if technical else "scientific")
    known = tuple(dict.fromkeys(spec["signal_id"] for spec in specs))
    signal_ids = report.get("signal_ids")
    if (
        type(signal_ids) is not list
        or not signal_ids
        or signal_ids != [key for key in known if key in signal_ids]
        or (technical and signal_ids != list(known))
    ):
        raise ValueError("Unknown, duplicated or out-of-order plot signal sections.")
    slots = {
        spec["id"] + "-" + arm: (spec, arm)
        for spec in specs
        if spec["signal_id"] in signal_ids
        for arm in LABELS
    }
    if set(report.get("outputs", {})) != set(slots) or report.get(
        "planned_outputs"
    ) != len(slots):
        raise ValueError("Incomplete original plot inventory.")
    required = {
        publication.REPORT,
        publication.SUMMARY,
        publication.MANIFEST,
        "index.html",
    }
    required.update(
        f"{stem}.{ext}"
        for stem in slots
        for ext in ("csv", "json", "formula.txt", "png", "svg")
    )
    if not technical:
        for signal_id in signal_ids:
            required.add(signal_id + "-summary.json")
            for model in assessment.PLANNED_BLOCKS:
                required.update(
                    f"{signal_id}-{model}-{kind}.{ext}"
                    for kind in ("overview", "contrasts")
                    for ext in ("csv", "png", "svg")
                )
                required.add(f"{signal_id}-{model}-contrasts.json")
                required.add(f"{signal_id}-{model}-contrasts-summary.csv")
        if set(report.get("source", {})) != set(signal_ids):
            raise ValueError("Plot sources omit a section.")
        if report.get("signal_normalization") != {
            key: report["source"][key].get("signal_normalization") for key in signal_ids
        }:
            raise ValueError("Plot noise normalization differs from its source.")
    elif report.get("signal_normalization") is not None:
        raise ValueError("Technical plots cannot invent a scientific normalization.")
    if set(payloads) != required or payloads[publication.SUMMARY] != SUMMARY.encode():
        raise ValueError("Plot payload inventory or summary changed.")
    data_names = required - {
        publication.REPORT,
        publication.SUMMARY,
        publication.MANIFEST,
    }
    if report.get("payload_sha256") != {
        name: sources.sha256(payloads[name]) for name in sorted(data_names)
    }:
        raise ValueError("Plot payloads contradict their completion report.")
    metadata = {}
    for stem, (spec, arm) in slots.items():
        raw = payloads[stem + ".json"]
        entry = sources.read_json(raw)
        if report["outputs"][stem] != {
            "identity": entry.get("identity"),
            "status": entry.get("status"),
            "metadata_sha256": sources.sha256(raw),
        }:
            raise ValueError("Plot metadata binding changed.")
        expected_identity = {
            "case_id": spec["id"],
            "signal_id": spec["signal_id"],
            "model": spec["noise_model"],
            "block": spec["block"],
            "condition": arm,
            "grid": "uniform",
        }
        if any(
            entry.get("identity", {}).get(key) != value
            for key, value in expected_identity.items()
        ):
            raise ValueError("Plot condition or case identity changed.")
        source = report["source"] if technical else report["source"][spec["signal_id"]]
        if (
            entry.get("format") != FORMAT
            or entry.get("technical") is not technical
            or entry.get("source") != source
            or entry.get("scientific_success_assessed") is not False
        ):
            raise ValueError("Plot source or format changed.")
        if entry.get("units") != {
            "time": "seconds",
            "signal": "dimensionless",
        } or entry.get("amplitude") != abs(spec["signal"]["amplitude"]):
            raise ValueError("Plot units or amplitude changed.")
        _verify_points(entry, payloads[stem + ".csv"], spec)
        candidate = entry.get("candidate")
        if candidate is not None:
            _validated_tree(candidate["tree"])
        equation = (
            candidate["display_equation"]
            if candidate is not None
            else "Keine Originalformel verfügbar: " + str(entry.get("reason"))
        )
        if payloads[stem + ".formula.txt"] != equation.encode():
            raise ValueError("Original formula text changed.")
        metadata[stem] = entry
    if payloads["index.html"] != _index(
        metadata, signal_ids, technical, report.get("signal_normalization")
    ):
        raise ValueError("Plot gallery differs from its bound original formulas.")


def verify_export(output, consumed=None):
    """Check saved plot bytes and costs, without rerendering or repeating searches."""
    external = consumed is not None
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(SECONDS))

    def verify():
        root = Path(output).absolute()
        if root != root.resolve() or not root.is_dir():
            raise ValueError("Expected an existing plot export without symlinks.")
        manifest_path = root / publication.MANIFEST
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise ValueError("Expected a regular plot manifest without symlinks.")
        raw = manifest_path.read_bytes()
        manifest = sources.read_json(raw)
        if type(manifest) is not dict:
            raise ValueError("Invalid plot manifest.")
        for name in manifest:
            if len(sources.safe_name(name).parts) != 1 or name in {
                publication.MANIFEST,
                publication.LOCK,
            }:
                raise ValueError("Unsafe plot manifest entry.")
        payloads = {}
        for name in manifest:
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("Expected regular plot payloads without symlinks.")
            payloads[name] = path.read_bytes()
        if manifest != {
            name: sources.sha256(value) for name, value in payloads.items()
        }:
            raise ValueError("Plot checksum differs.")
        payloads[publication.MANIFEST] = raw
        publication.verify_bytes(root, payloads, locked=False)
        report = sources.read_json(payloads[publication.REPORT])
        if report.get("format") != FORMAT or report.get("status") != "completed":
            raise ValueError("Plot export is incomplete or revoked.")
        _verify_payloads(report, payloads)
        path = _timing_path(root)
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing plot call costs.")
        raw = path.read_bytes()
        _verify_call(sources.read_json(raw), payloads[publication.REPORT])
        consumed.add(path, raw)
        consumed.callbacks.append(
            lambda: publication.verify_bytes(root, payloads, locked=False)
        )
        consumed.check()
        return report

    if external:
        return verify()
    with consumed.clock.active():
        report = verify()
    consumed.check()
    return report
