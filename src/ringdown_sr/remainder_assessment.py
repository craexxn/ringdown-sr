"""Bind the remainder contract, original reference vectors and separate counts."""

from collections import Counter
from dataclasses import asdict

import gmpy2
import numpy as np

from .remainder_proof import FORMAT, MAX_DEPTH, MAX_LEAVES, assess_remainder
from .structure_algebra import LIMITS
from .structure_assessment import bound_interval

FILES = ("data/remainder_assessment_v1.json", "docs/supplemental_remainder.md")
POLICY = {
    "format": FORMAT,
    "interval": "closed_verified_training_span_in_physical_seconds",
    "constants": "exact_binary64_rationals_and_symbolic_real_expressions",
    "components": "all_certified_affine_mode_groups_without_ranking",
    "domain_requirement": "complete_nonempty_dense_original_domain",
    "bound": "directed_mpfr_absolute_interval_enclosure",
    "subdivision": {
        "rule": "exact_midpoint_on_unproved_finite_bound_left_first",
        "max_depth": MAX_DEPTH,
        "max_leaves": MAX_LEAVES,
        "stop_at_first_finite_bound": True,
    },
    "limits": {**asdict(LIMITS), "precisions": list(LIMITS.precisions)},
    "budget_scope": "shared_across_all_components_and_reference_normalization_per_original_formula",
    "relative_bounds": {
        "rms": "B/sqrt(sum(y_i^2)/N)",
        "max": "B/max(abs(y_i))",
        "reference": "exact_saved_binary64_values_per_grid",
    },
    "negligible_threshold": None,
    "new_parameter_match": "not_assessed",
}


def check_policy(raw):
    from .assessment_sources import _same, read_json

    _same(read_json(raw), POLICY, "Unsupported remainder proof policy.")


def reference_records(training_time, training_truth, diagnostic_time, diagnostic_truth):
    """JSON-safe exact bits for the already verified historical input vectors."""
    return {
        role: {
            name: [float(x).hex() for x in value]
            for name, value in zip(("time_s", "truth"), pair, strict=True)
        }
        for role, pair in zip(
            ("training", "diagnostic"),
            ((training_time, training_truth), (diagnostic_time, diagnostic_truth)),
            strict=True,
        )
    }


def decoded_references(record):
    if not isinstance(record, dict) or set(record) != {"training", "diagnostic"}:
        raise ValueError("Missing original reference vectors.")
    result = {}
    for role, values in record.items():
        if not isinstance(values, dict) or set(values) != {"time_s", "truth"}:
            raise ValueError("Incomplete original reference grid.")
        result[role] = {}
        for name, raw in values.items():
            if not isinstance(raw, list):
                raise TypeError("Invalid original reference vector.")
            numbers = []
            for value in raw:
                if type(value) is not str:
                    raise ValueError("Noncanonical original reference value.")
                number = float.fromhex(value)
                if not np.isfinite(number) or number.hex() != value:
                    raise ValueError("Noncanonical original reference value.")
                numbers.append(number)
            result[role][name] = np.array(numbers, dtype=np.float64)
    return result


def supplement(record, binding, references):
    from .assessment_sources import fingerprint

    result = assess_remainder(
        record["original_candidate"]["tree"], bound_interval(binding), references
    )
    result["evaluation_model"] = "exact_real_original_tree"
    result["reference_binding"] = {
        grid: {name: fingerprint(values[name]) for name in ("time_s", "truth")}
        for grid, values in references.items()
    }
    record["supplemental"]["remainder"] = result


def status_counts(records):
    values = [r["supplemental"]["remainder"] for r in records]
    components = [c for value in values for c in value.get("components", [])]
    return {
        "remainder_status_counts": dict(Counter(value["status"] for value in values)),
        "remainder_component_count": len(components),
        "remainder_component_bound_status_counts": dict(
            Counter(c["bound"]["status"] for c in components)
        ),
    }


def summary_lines(records):
    """Display every core without ranking; exact certificates remain in JSON."""

    def display(value):
        if value is None:
            return "—"
        number = gmpy2.mpq(
            int(value["numerator_hex"], 16), int(value["denominator_hex"], 16)
        )
        with gmpy2.context(precision=64):
            return format(gmpy2.mpfr(number), ".6g")

    lines = [
        "",
        "## Separate Zusatzterm-Diagnosen",
        "",
        "Alle regelbasierten Grundterme; keine Rangfolge oder neue Erfolgsschwelle.",
        "B begrenzt den exakten reellen Rest Original minus Grundterm; keine Aussage über Grundterm minus Wahrheit oder Float64-Replayfehler.",
        "Zahlenanzeigen gerundet; allein die exakten Schranken und ihre Gültigkeitsbereiche in assessment_records.json sind maßgeblich.",
        "",
        "| Originalauswahl | Komponente | Schranke | B (gerundet) | RMS-Beitrag Training / Diagnose | Max-Beitrag Training / Diagnose |",
        "| --- | ---: | --- | ---: | --- | --- |",
    ]
    for record in records:
        identity = record["source_identity"]
        label = (
            identity.get("arm") or f"{identity['series_id']} / {identity['cell_id']}"
        )
        assessment = record["supplemental"]["remainder"]
        if not assessment.get("components"):
            lines.append(f"| {label} | — | {assessment['status']} | — | — | — |")
        for candidate in assessment.get("components", []):
            relative = candidate.get("relative_contribution_bounds", {})
            values = [
                " / ".join(
                    display(relative.get(g, {}).get(metric))
                    for g in ("training", "diagnostic")
                )
                for metric in ("relative_rms_upper", "relative_max_upper")
            ]
            bound = candidate["bound"]
            lines.append(
                f"| {label} | {candidate['component_index']} | {bound['status']} | {display(bound['upper'])} | {values[0]} | {values[1]} |"
            )
    return lines
