"""Export every original follow-up output and its bound numerical plot data."""

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
from . import noise_background_plots as shared
from . import noise_followup_assessment as assessment
from . import noise_followup_inputs as inputs
from .pilot import _utc_now

FORMAT = "ringdown-sr-noise-followup-plots-1"
SECONDS = 14400
LABELS = {
    "ordinary": "O / uniform",
    "known_covariance": "K / uniform",
    "estimated_64s": "E / 64 s",
    "estimated_4096s": "E / 4096 s",
    "jitter_ordinary": "O / ungleichmäßig",
    "jitter_known_covariance": "K / ungleichmäßig",
}
COLORS = ("#2166ac", "#7b3294", "#008837", "#e08214", "#b2182b", "#444444")
SUMMARY = (
    "# Folgestudie: Originalformeln, Plots und Punktdaten\n\n"
    "Alle geplanten Ausgaben einschließlich Ausfällen. Native Trainingswerte "
    "und lesender Originalbaum-Replay auf den bereits gebundenen Zusatzrastern. "
    "Keine neuen Messpunkte, Fits, Suchen, Glättung oder Neuauswahl. "
    "Gemeinsame uniforme Kontrollen im Rasterblock sind Referenzen; ihre "
    "ursprünglichen Suchkosten werden nicht als neue Kosten gezählt.\n\n"
    "index.html enthält die vollständigen Originalformeln und alle Datenlinks. "
    "CSV-Dateien erhalten auch nicht verfügbare Punkte. Rastermaxima sind "
    "keine kontinuierlichen Fehlerschranken.\n"
)
TIMING_SCOPE = (
    "transaction_entry_through_publication_and_handler_teardown_"
    "excluding_timing_write_and_final_rechecks"
)
point_data = shared.point_data


def _conditions(block):
    if block == "duration":
        return tuple(inputs.ARMS_A)
    if block == "sampling":
        return (*inputs.ARMS_A[:2], *inputs.ARMS_B)
    if block == "all":
        return (*inputs.ARMS_A, *inputs.ARMS_B)
    raise ValueError("Unknown follow-up plot block.")


def _referenced(block, condition):
    return block == "sampling" and condition in inputs.ARMS_A[:2]


def _selection(record, case, technical):
    if technical:
        return {"member_position": 1, "seed": case.spec["search_seeds"][0]}
    identity = record["source_identity"]
    path = identity["selected_member_path"]
    if record["original_candidate"] is None:
        if path is not None:
            raise ValueError("Unavailable plot output has a selected member.")
        return {"member_position": None, "seed": None}
    match = re.fullmatch(r"symbolic/([^/]+)/member-(\d{2})/result\.json", str(path))
    if (
        match is None
        or match[1] != identity["condition"]
        or not 1 <= int(match[2]) <= 4
    ):
        raise ValueError("Original plot selection is not bound to its condition.")
    position = int(match[2])
    return {
        "member_position": position,
        "seed": case.spec["search_seeds"][position - 1],
    }


def _curve_plot(metadata, rows, stem):
    figure = shared._figure((12, 8.5))
    top, bottom = figure.subplots(2, 1, sharex=True)
    for role, (_, _, label, color, marker) in shared.ROLES.items():
        selected = [row for row in rows if row["grid"] == role]
        for axis, field in (
            (top, "prediction"),
            (bottom, "residual_over_amplitude"),
        ):
            axis.scatter(
                [row["time_s"] for row in selected],
                [np.nan if row[field] is None else row[field] for row in selected],
                color=color,
                marker=marker,
                s=12,
                alpha=0.8,
                label=label,
            )
            missing = [r["time_s"] for r in selected if r["status"] != "available"]
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
        [item[0] for item in truth],
        [item[1] for item in truth],
        color="#006837",
        linewidth=1,
        label="Saubere Wahrheit: verbundene gespeicherte Punkte",
    )
    observed = [
        row for row in rows if row["grid"] == "training" and row["observed"] is not None
    ]
    top.scatter(
        [row["time_s"] for row in observed],
        [row["observed"] for row in observed],
        color="#888888",
        marker="x",
        s=14,
        label="Verrauschte Messwerte",
    )
    identity = metadata["identity"]
    suffix = " / referenzierte Kontrolle" if metadata["referenced_control"] else ""
    if metadata["technical"]:
        suffix += " / technischer Vorlauf"
    figure.suptitle(
        f"{identity['case']} / {LABELS[identity['condition']]} / "
        f"{metadata['status']}{suffix}",
        fontsize=12,
    )
    top.set_ylabel("Signalwert (Original-Amplitudeneinheit)")
    bottom.set_ylabel("(Originalvorhersage − saubere Wahrheit) / |A|")
    bottom.set_xlabel("t / Sekunden")
    bottom.axhline(0, color="#777777", linewidth=0.7)
    for axis in (top, bottom):
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7, loc="best")
    figure.text(
        0.025,
        0.015,
        f"Vollständige unveränderte Originalformel: {stem}.formula.txt; "
        f"Originalbaum/Quellen: {stem}.json; Punkte: {stem}.csv\n"
        "Keine Glättung. Verbindungen der Wahrheit sind nur eine Darstellung "
        "gespeicherter Punkte; kein kontinuierlicher Nachweis.",
        fontsize=7,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 0.95))
    return shared._images(figure)


def _output_payload(record, prepared, case, *, source, block, technical=False):
    identity = record["source_identity"]
    condition = identity["condition"]
    if condition not in LABELS:
        raise ValueError("Unknown follow-up plot condition.")
    stem = f"{case.spec['id']}-{condition}"
    sources.safe_name(stem)
    arrays = inputs.arm_arrays(prepared, case, condition)
    candidate = record["original_candidate"]
    reason = record.get("reason") or record.get("primary", {}).get("reason")
    amplitude = abs(float(record.get("amplitude", inputs.SIGNAL["amplitude"])))
    rows, metrics, peaks = point_data(candidate, arrays, amplitude, reason=reason)
    if not technical and candidate is not None:
        for role in shared.ROLES:
            if metrics[role]["rms_over_amplitude"] is not None:
                sources._same(
                    metrics[role],
                    record["amplitude_errors"][role],
                    "Plot norm differs from the verified original assessment.",
                )
    table = shared._csv(rows)
    metadata = {
        "format": FORMAT,
        "technical": technical,
        "scientific_success_assessed": False if technical else None,
        "identity": {
            "case": case.spec["id"],
            **copy.deepcopy(identity),
            **_selection(record, case, technical),
        },
        "source": source,
        "status": record["status"],
        "reason": reason,
        "referenced_control": _referenced(block, condition) and not technical,
        "candidate": copy.deepcopy(candidate),
        "background_duration_seconds": {
            "estimated_64s": 64,
            "estimated_4096s": 4096,
        }.get(condition),
        "units": {"time": "seconds", "signal": "original amplitude unit"},
        "metrics": metrics,
        "peaks": peaks,
        "costs": copy.deepcopy(record["costs"]),
        "cost_scope": "original package costs; reference controls incur no new searches",
        "supplemental": copy.deepcopy(record.get("supplemental")),
        "point_count": len(rows),
        "points_csv_sha256": sources.sha256(table),
        "interpretation": "Saved points only; no smoothing, fitting, reselection or continuous-domain claim.",
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
        **{
            stem + "." + suffix: raw
            for suffix, raw in _curve_plot(metadata, rows, stem).items()
        },
    }
    return stem, metadata, payloads


def _overview_payloads(report, block):
    payloads = {}
    conditions = _conditions(block)
    for model in assessment.PLANNED_BLOCKS:
        records = [
            r for r in report["assessments"] if r["source_identity"]["model"] == model
        ]
        rows = []
        figure = shared._figure((13, 7))
        error_axis, cost_axis = figure.subplots(1, 2)
        for condition, color in zip(conditions, COLORS, strict=False):
            group = [
                r for r in records if r["source_identity"]["condition"] == condition
            ]
            for record in group:
                identity = record["source_identity"]
                value = record["primary"]["value"]
                wall = record["costs"].get("worker_wall_seconds")
                reference = _referenced(block, condition)
                rows.append(
                    {
                        "model": model,
                        "block": identity["block"],
                        "condition": condition,
                        "grid": identity["grid"],
                        "status": record["status"],
                        "primary_status": record["primary"]["status"],
                        "primary_reason": record["primary"]["reason"],
                        "irregular_rms_over_amplitude": value,
                        "original_worker_wall_seconds": wall,
                        "original_search_calls": record["search_calls"],
                        "new_search_calls": 0 if reference else record["search_calls"],
                        "referenced_control": reference,
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
                    markerfacecolor="none" if _referenced(block, condition) else color,
                    color=color,
                    label=LABELS[condition]
                    + (" (Referenz)" if _referenced(block, condition) else ""),
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
        error_axis.set_ylabel("Unregelmäßiger Raster-RMSE / |A|")
        cost_axis.set_ylabel("Ursprüngliche Workerzeit / s (Referenzen nicht addieren)")
        for axis in (error_axis, cost_axis):
            axis.set_xlabel("Vorab festgelegter Fallblock")
            axis.grid(alpha=0.2)
            axis.legend(fontsize=7)
        figure.suptitle(f"{model} / {block}: alle geplanten Ausgaben und Fehlanzeigen")
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        stem = model + "-overview"
        payloads[stem + ".csv"] = shared._csv(rows)
        payloads.update(
            {stem + "." + ext: raw for ext, raw in shared._images(figure).items()}
        )

        contrasts = report["summary"]["models"][model]["contrasts"]
        contrast_rows, summary_rows = [], []
        figure = shared._figure((15, 8))
        axis, interval_axis = figure.subplots(1, 2)
        for index, (name, contrast) in enumerate(contrasts.items()):
            entries = contrast["values"]
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
            for entry in entries:
                contrast_rows.append({"contrast": name, **entry})
            interval = contrast["interval_95"]
            mean = contrast["mean"]
            summary_rows.append(
                {
                    "contrast": name,
                    "left": contrast["left"],
                    "right": contrast["right"],
                    "planned_pairs": assessment.PLANNED_BLOCKS[model],
                    "available_pairs": contrast["available"],
                    "denominator_scope": contrast["denominator_scope"],
                    "mean": mean,
                    "sample_sd": contrast["sample_sd"],
                    "mcse": contrast["mcse"],
                    **{"interval_95_" + key: value for key, value in interval.items()},
                }
            )
            if mean is not None:
                interval_axis.plot(mean, index, marker="o", color="#2166ac")
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
                    "95%-Intervall nicht verfügbar",
                    transform=interval_axis.get_yaxis_transform(),
                    fontsize=7,
                )
        axis.axhline(0, color="#777777", linewidth=0.7)
        axis.set_xlabel("Gepaarter Fallblock")
        axis.set_ylabel("Differenz des unregelmäßigen Raster-RMSE / |A|")
        axis.grid(alpha=0.2)
        axis.legend(fontsize=6)
        interval_axis.set_yticks(range(len(contrasts)), contrasts, fontsize=6)
        interval_axis.axvline(0, color="#777777", linewidth=0.7)
        interval_axis.set_xlabel("Mittelwert und marginales 95%-Intervall")
        interval_axis.set_title(
            "Deskriptiv; keine automatische Erfolgsentscheidung", fontsize=9
        )
        interval_axis.grid(alpha=0.2)
        figure.suptitle(f"{model} / {block}: vorab festgelegte gepaarte Kontraste")
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        stem = model + "-contrasts"
        payloads[stem + ".csv"] = shared._csv(contrast_rows)
        payloads[stem + "-summary.csv"] = shared._csv(summary_rows)
        payloads[stem + ".json"] = sources.json_bytes(contrasts)
        payloads.update(
            {stem + "." + ext: raw for ext, raw in shared._images(figure).items()}
        )
    return payloads


def _index(metadata, block, technical):
    parts = [
        '<!doctype html><html lang="de"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Folgestudie: Originalausgaben</title>",
        (
            "<style>body{font:16px system-ui;max-width:1200px;margin:auto;padding:20px}"
            "img{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
            "article{border-top:1px solid #aaa;padding:20px 0}a{margin-right:12px}</style>"
        ),
        "<h1>Folgestudie: Originalausgaben</h1>",
        (
            "<p>Vollständige unveränderte Formeln und alle gespeicherten Punkte. "
            "Keine Neuauswahl, Glättung, Fits oder Suchläufe. "
            "Rasterwerte belegen keinen kontinuierlichen Kurvenverlauf.</p>"
        ),
    ]
    if technical:
        parts.append(
            "<p>Technischer Vorlauf; keine wissenschaftliche Erfolgsbewertung.</p>"
        )
    else:
        parts.append(f"<p>Versuchsblock: {html.escape(block)}.</p>")
        if block == "sampling":
            parts.append(
                "<p>Uniforme O-/K-Ausgaben sind vorab gebundene gemeinsame Kontrollen. "
                "Ihre Formeln und ursprünglichen Kosten bleiben erhalten; sie zählen "
                "nicht als neue Suchen.</p>"
            )
        for model in assessment.PLANNED_BLOCKS:
            for kind in ("overview", "contrasts"):
                stem = f"{model}-{kind}"
                parts.append(
                    f'<p><a href="{stem}.png">{stem} PNG</a>'
                    f'<a href="{stem}.svg">SVG</a><a href="{stem}.csv">CSV</a></p>'
                )
                if kind == "contrasts":
                    parts.append(
                        f'<p><a href="{stem}-summary.csv">Kontraststatistik und Intervalle CSV</a>'
                        f'<a href="{stem}.json">Vollständige Kontraststatistik JSON</a></p>'
                    )
    for stem, record in sorted(metadata.items()):
        candidate = record["candidate"]
        equation = (
            candidate["display_equation"]
            if candidate is not None
            else ("Keine Originalformel verfügbar: " + str(record["reason"]))
        )
        parts.extend(
            [
                f'<article id="{html.escape(stem)}"><h2>{html.escape(stem)}</h2>',
                (
                    f"<p>Status: {html.escape(record['status'])}; "
                    f"Quelle: {'referenzierte Kontrolle' if record['referenced_control'] else 'Originalausgabe'}.</p>"
                ),
                f"<pre>{html.escape(equation)}</pre>",
                "<p>"
                + "".join(
                    f'<a href="{stem}.{extension}">{label}</a>'
                    for extension, label in (
                        ("formula.txt", "Originalformel"),
                        ("json", "Originalbaum / Metadaten"),
                        ("csv", "Alle Punktdaten"),
                        ("png", "PNG"),
                        ("svg", "SVG"),
                    )
                )
                + "</p>",
                f'<img loading="lazy" src="{stem}.png" alt="{html.escape(stem)}"></article>',
            ]
        )
    parts.append("</html>")
    return "\n".join(parts).encode()


def _validate_output(output, roots):
    return shared._validate_output(output, (root for root in roots if root is not None))


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
            "measurement_scope",
        }
        or record.get("format") != FORMAT + "-call"
        or record.get("status") != "completed"
        or record.get("error") is not None
        or record.get("source_report_sha256") != sources.sha256(report_raw)
        or record.get("cpu_scope") != "self_plus_reaped_children"
        or record.get("measurement_scope") != TIMING_SCOPE
    ):
        raise ValueError("Unbound or incomplete follow-up plot call.")
    try:
        start, finish = (
            datetime.fromisoformat(record[key])
            for key in ("started_at_utc", "finished_at_utc")
        )
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid follow-up plot call timestamps.") from error
    if (
        start.utcoffset() != timedelta(0)
        or finish.utcoffset() != timedelta(0)
        or finish < start
    ):
        raise ValueError("Invalid follow-up plot UTC time order.")
    for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if not shared._finite(record.get(key)) or record[key] < 0:
            raise ValueError("Invalid follow-up plot call cost.")
    if record["wall_seconds"] >= SECONDS:
        raise ValueError("Follow-up plot export exceeded its operational deadline.")


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
        "diagnostics_report_sha256": report.get("diagnostics_report_sha256"),
    }


def _build_report(metadata, source, block, *, technical=False):
    return {
        "format": FORMAT,
        "technical": technical,
        "block": block,
        "source": source,
        "planned_outputs": len(metadata),
        "referenced_outputs": sum(
            item["referenced_control"] for item in metadata.values()
        ),
        "new_outputs": sum(
            not item["referenced_control"] for item in metadata.values()
        ),
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
        },
        "selection_changed": False,
        "fits_or_searches_executed": False,
    }


def export(
    preparation,
    technical_path,
    series,
    output,
    *,
    diagnostics,
    block=None,
    uniform=None,
):
    """Read-verify a complete block, then export every original output and reference."""
    from . import noise_followup as study

    output = _validate_output(
        output, (preparation, technical_path, series, uniform, diagnostics)
    )

    def build(consumed):
        report = study.verify(
            preparation,
            technical_path,
            series,
            diagnostics=diagnostics,
            block=block,
            uniform=uniform,
            consumed=consumed,
        )
        actual_block = report["block"]
        conditions = _conditions(actual_block)
        prepared = inputs.verify_inputs(preparation, consumed, regenerate=False)
        source = _source(series, report, prepared, consumed)
        source["control_references"] = copy.deepcopy(
            report.get("control_references", {})
        )
        sources._same(
            report["summary"],
            assessment.summary(report["assessments"], block=actual_block),
            "Plot source summary changed.",
        )
        indexed = {}
        for record in report["assessments"]:
            identity = record["source_identity"]
            case_id = f"{identity['model']}-{identity['block']:02d}"
            key = case_id, identity["condition"]
            if key in indexed:
                raise ValueError("Duplicate original plot slot.")
            indexed[key] = record
        expected = {
            (case_id, condition)
            for case_id in prepared.cases
            for condition in conditions
        }
        if set(indexed) != expected:
            raise ValueError(
                "Plot inventory does not cover every planned case and condition."
            )
        payloads, metadata = {}, {}
        for case_id in prepared.cases:
            case = inputs.read_case(
                prepared, case_id, consumed=consumed, regenerate=False
            )
            for condition in conditions:
                consumed.clock.check()
                stem, entry, files = _output_payload(
                    indexed[case_id, condition],
                    prepared,
                    case,
                    source=source,
                    block=actual_block,
                )
                metadata[stem] = entry
                payloads.update(files)
        payloads.update(_overview_payloads(report, actual_block))
        payloads["index.html"] = _index(metadata, actual_block, False)
        return _build_report(metadata, source, actual_block), payloads

    return _transaction(output, build)


def export_technical(technical_path, output):
    """Export all six short technical workers, without a scientific success claim."""
    from . import noise_followup_technical as technical

    output = _validate_output(output, (technical_path,))

    def build(consumed):
        report = technical.verify(technical_path, consumed=consumed)
        prepared = inputs.verify_inputs(
            Path(technical_path) / "inputs", consumed, regenerate=False
        )
        if len(prepared.cases) != 1 or set(report["members"]) != set(LABELS):
            raise ValueError(
                "Technical plots require exactly one case and six workers."
            )
        case = inputs.read_case(
            prepared, next(iter(prepared.cases)), consumed=consumed, regenerate=False
        )
        source = _source(technical_path, report, prepared, consumed)
        payloads, metadata = {}, {}
        for condition in (*inputs.ARMS_A, *inputs.ARMS_B):
            consumed.clock.check()
            member = report["members"][condition]
            record = {
                "status": "success" if member["selected"] is not None else "failed",
                "reason": None
                if member["selected"] is not None
                else "technical_worker_no_selected_candidate",
                "source_identity": {
                    "model": case.spec["noise_model"],
                    "block": case.spec["block"],
                    "condition": condition,
                    "grid": "jitter" if condition in inputs.ARMS_B else "uniform",
                    "selected_member_path": condition + "/result.json",
                },
                "original_candidate": member["selected"],
                "costs": member["costs"],
            }
            stem, entry, files = _output_payload(
                record, prepared, case, source=source, block="all", technical=True
            )
            metadata[stem] = entry
            payloads.update(files)
        payloads["index.html"] = _index(metadata, "technical", True)
        return _build_report(metadata, source, "technical", technical=True), payloads

    return _transaction(output, build)


def _verify_payloads(report, payloads):
    technical = report.get("technical")
    if type(technical) is not bool:
        raise ValueError("Missing scientific/technical plot identity.")
    if (
        report.get("selection_changed") is not False
        or report.get("fits_or_searches_executed") is not False
        or (technical and report.get("block") != "technical")
    ):
        raise ValueError("Plot export contradicts its read-only scope.")
    specs = inputs.case_specs(technical=technical)
    conditions = (
        (*inputs.ARMS_A, *inputs.ARMS_B)
        if technical
        else _conditions(report.get("block"))
    )
    slots = {
        f"{spec['id']}-{condition}": (spec, condition)
        for spec in specs
        for condition in conditions
    }
    if set(report.get("outputs", {})) != set(slots) or report.get(
        "planned_outputs"
    ) != len(slots):
        raise ValueError("Incomplete original plot output inventory.")
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
        for model in assessment.PLANNED_BLOCKS:
            required.update(
                f"{model}-{kind}.{ext}"
                for kind in ("overview", "contrasts")
                for ext in ("csv", "png", "svg")
            )
            required.add(model + "-contrasts.json")
            required.add(model + "-contrasts-summary.csv")
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
    for stem, (spec, condition) in slots.items():
        raw = payloads[stem + ".json"]
        entry = sources.read_json(raw)
        declared = report["outputs"][stem]
        if declared != {
            "identity": entry.get("identity"),
            "status": entry.get("status"),
            "metadata_sha256": sources.sha256(raw),
        }:
            raise ValueError("Plot metadata binding changed.")
        expected_identity = {
            "case": spec["id"],
            "model": spec["noise_model"],
            "block": spec["block"],
            "condition": condition,
            "grid": "jitter" if condition in inputs.ARMS_B else "uniform",
        }
        if any(
            entry.get("identity", {}).get(key) != value
            for key, value in expected_identity.items()
        ):
            raise ValueError("Plot condition or case identity changed.")
        if (
            entry.get("format") != FORMAT
            or entry.get("technical") is not technical
            or entry.get("source") != report.get("source")
            or (technical and entry.get("scientific_success_assessed") is not False)
        ):
            raise ValueError("Plot source or format changed.")
        expected_reference = not technical and _referenced(report["block"], condition)
        if entry.get("referenced_control") is not expected_reference:
            raise ValueError("Plot reference-control accounting changed.")
        table = payloads[stem + ".csv"]
        rows = list(csv.DictReader(io.StringIO(table.decode())))
        if entry.get("points_csv_sha256") != sources.sha256(table) or entry.get(
            "point_count"
        ) != len(rows):
            raise ValueError("Plot point table differs from its original binding.")
        candidate = entry.get("candidate")
        equation = (
            candidate["display_equation"]
            if candidate is not None
            else "Keine Originalformel verfügbar: " + str(entry.get("reason"))
        )
        if payloads[stem + ".formula.txt"] != equation.encode():
            raise ValueError("Original formula text changed.")
        metadata[stem] = entry
    referenced = sum(entry["referenced_control"] for entry in metadata.values())
    if (
        report.get("referenced_outputs") != referenced
        or report.get("new_outputs") != len(metadata) - referenced
    ):
        raise ValueError("Plot output/control accounting changed.")
    if payloads["index.html"] != _index(metadata, report["block"], technical):
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
