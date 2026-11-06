"""Retrospective curve grades from verified, unchanged original selections."""

import math
import platform
import subprocess
import tarfile
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

from . import assessment_sources as sources
from . import remainder_assessment as remainder
from . import structure_assessment as structure
from .assessment_publication import export_transaction

ROOT = sources.ROOT
POLICY = ROOT / "data/supplemental_assessment_v3.json"
VERSION = "ringdown-sr-supplemental-assessment-3"
SCHEMA = "ringdown-sr-supplemental-record-3"
THRESHOLDS = (("A", 0.001, 0.01), ("B", 0.01, 0.02), ("C", 0.05, 0.10))


def unavailable(reason):
    return {"status": "not_assessable", "grade": None, "reason": reason}


def grade_curve(errors, *, source_verified):
    """Require all four available original metrics; choose the best inclusive grade."""
    if source_verified is not True:
        return unavailable("source_not_verified")
    if not isinstance(errors, dict) or set(errors) != {"training", "diagnostic"}:
        return unavailable("missing_or_wrong_grid_roles")
    values = []
    for grid in ("training", "diagnostic"):
        endpoint = errors[grid]
        if not isinstance(endpoint, dict) or endpoint.get("status") != "available":
            return unavailable(grid + "_endpoint_not_available")
        pair = []
        for metric in ("relative_rms", "relative_max"):
            value = endpoint.get(metric)
            if type(value) not in (int, float) or value < 0:
                return unavailable(grid + "_invalid_" + metric)
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                return unavailable(grid + "_nonfinite_" + metric)
            pair.append(value)
        values.append(pair)
    for grade, rms, maximum in THRESHOLDS:
        if all(pair[0] <= rms and pair[1] <= maximum for pair in values):
            return {"status": "assessed", "grade": grade, "reason": None}
    return {"status": "assessed", "grade": "D", "reason": None}


def record(
    series_id, spec, cell, original=None, *, verification="missing", reason=None
):
    """Keep historical values separate from explicitly unassessed later stages."""
    verified = verification == "verified" and original is not None
    old = original["unchanged_historical"] if verified else None
    curve = (
        grade_curve(old.get("curve_errors"), source_verified=True)
        if verified
        else unavailable(reason or verification)
    )
    identity = {
        "series_id": series_id,
        "cell_id": cell["directory"],
        "original_seed": cell["budget"]["seed"],
        "signal_id": cell.get("signal", "anchor"),
        "condition": cell["condition"],
        "original_cell": cell,
        "archive_sha256": spec["archive_sha256"],
        "execution_commit": spec["execution_commit"],
        "verification_status": verification,
        "original_selected_index": original["original_selected_index"]
        if verified
        else None,
        "source_candidate_sha256": original["source_candidate_sha256"]
        if verified
        else None,
        "source_file_sha256": original["source_file_sha256"] if verified else None,
    }
    result = {
        "schema": SCHEMA,
        "assessment_version": VERSION,
        "source_identity": identity,
        "original_candidate": original["candidate"] if verified else None,
        "grid_binding": original["grid_binding"] if verified else None,
        "unchanged_historical": old,
        "supplemental": {
            "curve": curve,
            **{
                name: {"status": "not_assessed"}
                for name in (
                    "algebraic_identity",
                    "original_family",
                    "continuous_extension",
                    "remainder",
                    "new_parameter_match",
                )
            },
            "domain": {"status": "not_assessed", "interval": None, "exclusions": None},
            "coefficients_exact": None,
            "coefficient_sign_proofs": None,
            "proof_trace": [],
        },
    }
    if verified:
        structure.supplement(result, original["grid_binding"]["structure_interval"])
        remainder.supplement(
            result,
            original["grid_binding"]["structure_interval"],
            remainder.decoded_references(original["assessment_references"]),
        )
    return result


def groups(records):
    """Retain unavailable cases in each original experimental group's denominator."""
    grouped = {}
    for item in records:
        identity = item["source_identity"]
        cell = identity["original_cell"]
        condition = {
            "series_id": identity["series_id"],
            "signal_id": identity["signal_id"],
            "condition": cell["condition"],
            "arm": cell["arm"],
            "grammar": cell.get("grammar"),
            "budget_without_seed": {
                k: v for k, v in cell["budget"].items() if k != "seed"
            },
        }
        key = sources.json_bytes(condition)
        if key not in grouped:
            grouped[key] = {"condition": condition, "items": []}
        grouped[key]["items"].append(item)
    result = []
    for group in grouped.values():
        items = group["items"]
        counts = Counter(
            item["supplemental"]["curve"]["grade"] or "not_assessable" for item in items
        )
        result.append(
            {
                "condition": group["condition"],
                "planned_denominator": len(items),
                "curve_grade_counts": {
                    key: counts[key] for key in ("A", "B", "C", "D", "not_assessable")
                },
                "source_status_counts": dict(
                    Counter(
                        item["source_identity"]["verification_status"] for item in items
                    )
                ),
                **structure.status_counts(items),
                **remainder.status_counts(items),
            }
        )
    return result


def git(*args):
    return (
        subprocess.check_output(["git", *args], cwd=ROOT, timeout=30).decode().strip()
    )


def freeze_software(consumed):
    """Require a committed contract before reading scientific assessment inputs."""
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Use a clean, committed assessment checkout.")
    commit = git("rev-parse", "HEAD")
    paths = [
        *sorted((ROOT / "src/ringdown_sr").glob("*.py")),
        POLICY,
        sources.CATALOG,
        ROOT / "scripts/export_supplemental_assessment.py",
        ROOT / "docs/supplemental_assessment.md",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        ROOT / ".python-version",
        *(ROOT / name for name in structure.FILES),
        *(ROOT / name for name in remainder.FILES),
    ]
    hashes = {}
    for path in paths:
        consumed.clock.check()
        raw = path.read_bytes()
        name = str(path.relative_to(ROOT))
        if raw != consumed.git_file(commit, name):
            raise ValueError("Assessment software differs from its commit: " + name)
        consumed.add(path, raw)
        hashes[name] = sources.sha256(raw)

    def same_head():
        if git("rev-parse", "HEAD") != commit:
            raise ValueError("Assessment checkout changed during export.")

    consumed.callbacks.append(same_head)
    policy = sources.read_json(consumed.files[POLICY])
    if (
        policy["policy_id"] != VERSION
        or policy["schema"] != SCHEMA
        or policy["stage"] != 3
        or policy["threshold_semantics"]
        != "binary64_inclusive_no_rounding_no_tolerance"
        or policy["grid_roles"] != ["training", "diagnostic"]
        or policy["domain_interval"] != structure.POLICY["interval"]
        or policy["proof_resource_limits"] != structure.POLICY["limits"]
        or policy["structure_proof_policy"] != structure.FILES[0]
        or policy["remainder_rules"] != remainder.FILES[0]
        or policy["planned_selections"] != 78
    ):
        raise ValueError("Unsupported assessment policy.")
    structure.check_policy(consumed.files[ROOT / structure.FILES[0]])
    remainder.check_policy(consumed.files[ROOT / remainder.FILES[0]])
    expected = [
        {
            "grade": grade,
            "relative_rms": rms,
            "relative_max": maximum,
            "rms_hex": rms.hex(),
            "max_hex": maximum.hex(),
        }
        for grade, rms, maximum in THRESHOLDS
    ]
    sources._same(
        policy["thresholds"],
        expected,
        "Policy thresholds disagree with implementation.",
    )
    return {
        "software_commit": commit,
        "source_sha256": hashes,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            **structure.runtime(),
        },
        "policy": policy,
    }


def render_summary(report):
    lines = [
        "# Ergänzende Kurven-, Struktur- und Zusatztermbewertung – Stufe 3",
        "",
        "Retrospektiv; ausschließlich ursprüngliche Auswahlen. Keine neue Suche oder Auswahl.",
        "Keine gemeinsame Erfolgsquote über die unterschiedlichen Versuchsbedingungen.",
        "Identität, Originaldomain, Fortsetzung und Zusatzterme getrennt; neue Parametermatches: not_assessed.",
        "Nur zusammen mit vollständigem Manifest, completed-Bericht und ohne ASSESSMENT_LOCKED gültig.",
        "",
        "| Serie | Quellenstatus | Geplant | Verifiziert |",
        "| --- | --- | ---: | ---: |",
    ]
    for series in report["series"]:
        lines.append(
            f"| {series['series_id']} | {series['verification_status']} | {series['planned']} | {series['verified']} |"
        )
    lines += [
        "",
        "| Serie / Signal / Bedingung / äußere Iterationen | Nenner | A | B | C | D | Nicht bewertbar |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in report["groups"]:
        c = group["condition"]
        counts = group["curve_grade_counts"]
        label = f"{c['series_id']} / {c['signal_id']} / {c['condition']} / {c['budget_without_seed']['niterations']}"
        lines.append(
            "| "
            + label
            + " | "
            + str(group["planned_denominator"])
            + " | "
            + " | ".join(str(counts[k]) for k in ("A", "B", "C", "D", "not_assessable"))
            + " |"
        )
    lines += [
        "",
        "Kurvenklasse A entspricht bei denselben gültigen Kennzahlen dem bisherigen Kurvenkriterium C.",
        "Die neue Klasse C ist kein historischer C-Erfolgszähler. Punktweise Güte beweist keine Definitionslückenfreiheit.",
        "Fehlende oder gesperrte Originale liefern keine historische Neubewertung; ihre geplanten Fälle bleiben im Nenner.",
    ]
    lines += [
        "",
        "| Serie / Bedingung | Nenner | Identität | Originaldomain | Originalfamilie | Fortsetzung |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for group in report["groups"]:
        c = group["condition"]
        counts = [
            str(group[name + "_status_counts"])
            for name in (
                "algebraic_identity",
                "domain",
                "original_family",
                "continuous_extension",
            )
        ]
        lines.append(
            f"| {c['series_id']} / {c['signal_id']} / {c['condition']} / {c['budget_without_seed']['niterations']} | {group['planned_denominator']} | "
            + " | ".join(counts)
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_assessment(archives, consumed):
    software = freeze_software(consumed)
    catalog = sources.contracts()
    if set(archives) - catalog.keys():
        raise ValueError("Unknown original series requested.")
    results, records, payloads = [], [], {}
    for name, spec in catalog.items():
        consumed.check()
        state, reason, originals = "missing", "missing_original_archive", None
        if name in archives:
            path = Path(archives[name]).absolute()
            try:
                # Freeze before validation; failed supplied inputs also remain bound.
                raw = sources.bounded_read(path)
                consumed.add_archive(path, raw)
                verified = sources.read_verified_series(
                    path,
                    name,
                    check=consumed.clock.check,
                    contents=raw,
                    git_file=consumed.git_file,
                )
                originals = [sources.read_json(raw) for raw in verified.records]
                payloads[name + "-historical-report.json"] = verified.files[
                    "report.json"
                ]
                state, reason = "verified", None
            except (TimeoutError, InterruptedError):
                raise
            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
                tarfile.TarError,
                zipfile.BadZipFile,
                subprocess.SubprocessError,
            ) as error:
                state, reason = "failed", f"{type(error).__name__}: {error}"
        series_records = [
            record(
                name,
                spec,
                cell,
                originals[i] if originals is not None else None,
                verification=state,
                reason=reason,
            )
            for i, cell in enumerate(spec["cells"])
        ]
        records.extend(series_records)
        results.append(
            {
                "series_id": name,
                "verification_status": state,
                "reason": reason,
                "archive_sha256": spec["archive_sha256"],
                "planned": len(spec["cells"]),
                "verified": len(series_records) if state == "verified" else 0,
                "release": "separate_verified_series"
                if state == "verified"
                else "locked",
                "unchanged_historical_report": name + "-historical-report.json"
                if state == "verified"
                else None,
            }
        )
    report = {
        "format": VERSION,
        "schema": SCHEMA,
        "stage": 3,
        "software": software,
        "corpus_status": "complete"
        if all(s["verification_status"] == "verified" for s in results)
        else "incomplete",
        "release": "separate_verified_series_only",
        "series": results,
        "groups": groups(records),
    }
    consumed.check()
    payloads["assessment_records.json"] = sources.json_bytes(records)
    return (
        report,
        render_summary(report) + "\n".join(remainder.summary_lines(records)) + "\n",
        payloads,
    )


def run(archives, output, *, seconds=300):
    return export_transaction(
        output, lambda consumed: build_assessment(archives, consumed), seconds=seconds
    )
