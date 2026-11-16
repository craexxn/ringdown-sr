"""Assess the frozen five-arm study without changing any original selection."""

import copy
import math
from collections import Counter

from scipy.stats import t as student_t

from . import noise_pilot_assessment as pilot
from . import remainder_assessment as remainder
from . import structure_assessment as structure

FORMAT = "ringdown-sr-noise-background-assessment-1"
ARMS = (
    "ordinary",
    "known_covariance",
    "estimated_64",
    "estimated_256",
    "estimated_1024",
)
PLANNED_BLOCKS = {"ar1": 20, "white": 6}
PRIMARY_ENDPOINT = "irregular_rms_over_amplitude"
PRIMARY_CONTRAST = "estimated_1024_minus_ordinary"
SECONDARY_CONTRAST = "estimated_1024_minus_estimated_64"
CONTRASTS = (
    (PRIMARY_CONTRAST, "estimated_1024", "ordinary"),
    (SECONDARY_CONTRAST, "estimated_1024", "estimated_64"),
    ("estimated_64_minus_ordinary", "estimated_64", "ordinary"),
    ("estimated_256_minus_ordinary", "estimated_256", "ordinary"),
    ("estimated_64_minus_known", "estimated_64", "known_covariance"),
    ("estimated_256_minus_known", "estimated_256", "known_covariance"),
    ("estimated_1024_minus_known", "estimated_1024", "known_covariance"),
    ("known_minus_ordinary", "known_covariance", "ordinary"),
)
ROLES = pilot.ROLES


def _legacy_identity(identity, status):
    """Validate the new identity before adapting it for shared pure diagnostics."""
    if (
        type(identity) is not dict
        or set(identity) != pilot.IDENTITY_FIELDS
        or type(identity["model"]) is not str
        or identity["model"] not in PLANNED_BLOCKS
        or type(identity["arm"]) is not str
        or identity["arm"] not in ARMS
        or type(identity["block"]) is not int
        or not 1 <= identity["block"] <= PLANNED_BLOCKS[identity["model"]]
    ):
        raise ValueError("Invalid noise-background source identity.")
    adapted = copy.deepcopy(identity)
    if adapted["arm"].startswith("estimated_"):
        adapted["arm"] = "estimated_covariance"
    pilot._identity(adapted, status)
    return adapted


def training_windows(arm):
    """Return the prospectively assigned training size, never a fitted choice."""
    if arm not in ARMS:
        raise ValueError("Unknown noise-background weighting arm.")
    return int(arm.removeprefix("estimated_")) if arm.startswith("estimated_") else None


def assess_package(verified_report, arrays, *, amplitude, source_identity):
    """Reuse historical diagnostics while making only the new grid endpoint primary.

    The caller must verify and bind the package and input sources. The original
    candidate, native predictions, proofs and historical A-D rules are retained.
    """
    adapted = _legacy_identity(source_identity, verified_report["package_status"])
    record = pilot.assess_package(
        verified_report, arrays, amplitude=amplitude, source_identity=adapted
    )
    record.update(
        format=FORMAT,
        source_identity=copy.deepcopy(source_identity),
        background_training_windows=training_windows(source_identity["arm"]),
        primary_endpoint=PRIMARY_ENDPOINT,
    )
    endpoint = record["amplitude_errors"]["irregular"]
    value = endpoint["rms_over_amplitude"]
    record["primary"] = {
        "status": "available" if value is not None else endpoint["status"],
        "reason": None if value is not None else endpoint["reason"],
        "value": value,
    }
    return record


def _paired_stats(entries, planned):
    stats = pilot._stats(entries, planned)
    complete = stats["available"] == planned and stats["sample_sd"] is not None
    uncertainty = {
        "method": "student_t_mean_approximate_marginal",
        "confidence_level": 0.95,
        "degrees_of_freedom": planned - 1,
        "critical_value": None,
        "lower": None,
        "upper": None,
        "status": "not_available",
        "reason": "requires_all_planned_pairs_and_finite_sample_sd",
        "scope": "fixed_signal_and_grid_noise_background_and_search_variation",
        "simultaneous": False,
        "decision_rule": False,
    }
    mcse = None
    if complete:
        mcse = stats["sample_sd"] / math.sqrt(planned)
        critical = float(student_t.ppf(0.975, planned - 1))
        width = critical * mcse
        lower, upper = stats["mean"] - width, stats["mean"] + width
        if not all(math.isfinite(value) for value in (critical, width, lower, upper)):
            uncertainty["reason"] = "interval_out_of_range"
        else:
            uncertainty.update(
                critical_value=critical,
                lower=lower,
                upper=upper,
                status="available",
                reason="approximation_may_be_poor_for_skewness_spikes_or_small_n",
            )
    stats.update(
        mcse=mcse,
        mcse_reason="finite_replication_estimate_only"
        if complete
        else "requires_all_planned_pairs_and_finite_sample_sd",
        interval_95=uncertainty,
        denominator_scope="all_planned_pairs"
        if complete
        else "available_pairs_conditional_on_both_endpoints",
    )
    return stats


def _validate_record(record):
    status = record.get("status")
    if (
        record.get("format") != FORMAT
        or record.get("primary_endpoint") != PRIMARY_ENDPOINT
        or status not in {"success", "failed", "not_run"}
    ):
        raise ValueError("Invalid noise-background assessment record.")
    identity = record["source_identity"]
    _legacy_identity(identity, status)
    expected_windows = training_windows(identity["arm"])
    windows = record.get("background_training_windows")
    if windows != expected_windows or (
        windows is not None and type(windows) is not int
    ):
        raise ValueError("Assessment background size differs from its assigned arm.")
    if type(record.get("planned_members")) is not int or record["planned_members"] != 4:
        raise ValueError("Assessment must retain its four planned members.")
    calls = record.get("search_calls")
    if type(calls) is not int or calls != (0 if status == "not_run" else 4):
        raise ValueError("Assessment search-call accounting differs.")
    primary = record["primary"]
    if type(primary) is not dict or set(primary) != {"status", "reason", "value"}:
        raise ValueError("Invalid primary endpoint fields.")
    value = primary["value"]
    if primary["status"] == "available":
        if (
            status != "success"
            or not pilot._finite(value)
            or value < 0
            or primary["reason"] is not None
        ):
            raise ValueError("Invalid available primary endpoint.")
    elif (
        value is not None
        or primary["status"] not in {"not_available", "numerical_unresolved"}
        or type(primary["reason"]) is not str
        or not primary["reason"]
    ):
        raise ValueError("Invalid unavailable primary endpoint.")
    costs = record["costs"]
    if type(costs) is not dict or any(
        value is not None and (not pilot._finite(value) or value < 0)
        for value in costs.values()
    ):
        raise ValueError("Invalid assessment costs; unknown costs must remain null.")
    return identity["model"], identity["block"], identity["arm"]


def summary(records):
    """Keep all 130 planned outputs and eight contrasts, stratified by noise model."""
    indexed = {}
    for record in records:
        key = _validate_record(record)
        if key in indexed:
            raise ValueError("Duplicate model/block/arm assessment.")
        indexed[key] = record
    expected = {
        (model, block, arm)
        for model, planned in PLANNED_BLOCKS.items()
        for block in range(1, planned + 1)
        for arm in ARMS
    }
    if set(indexed) != expected:
        raise ValueError("Assessment inventory differs from the 130 planned outputs.")
    models = {}
    for model, planned in PLANNED_BLOCKS.items():
        arms = {}
        for arm in ARMS:
            group = [indexed[model, block, arm] for block in range(1, planned + 1)]
            entries = [
                {"block": r["source_identity"]["block"], **r["primary"]} for r in group
            ]
            arms[arm] = {
                "primary": pilot._stats(entries, planned),
                "package_status_counts": dict(Counter(r["status"] for r in group)),
                "failure_denominator": planned,
                "failed_or_not_run": sum(r["status"] != "success" for r in group),
                "failure_fraction": sum(r["status"] != "success" for r in group)
                / planned,
                "planned_search_calls": 4 * planned,
                "search_calls": sum(r["search_calls"] for r in group),
                "curve_grade_counts": dict(
                    Counter(
                        r["supplemental"]["curve"]["grade"] or "not_assessable"
                        for r in group
                    )
                ),
                **structure.status_counts(group),
                **remainder.status_counts(group),
            }
        contrasts = {}
        for name, left, right in CONTRASTS:
            entries = []
            for block in range(1, planned + 1):
                a, b = (
                    indexed[model, block, left]["primary"],
                    indexed[model, block, right]["primary"],
                )
                available = a["status"] == b["status"] == "available"
                value = a["value"] - b["value"] if available else None
                reason = None if available else "one_or_both_pair_endpoints_unavailable"
                if value is not None and not math.isfinite(value):
                    value, reason = None, "paired_difference_out_of_range"
                entries.append(
                    {
                        "block": block,
                        "status": "available" if value is not None else "not_available",
                        "reason": reason,
                        "value": value,
                    }
                )
            contrasts[name] = {
                **_paired_stats(entries, planned),
                "left": left,
                "right": right,
            }
        models[model] = {"arms": arms, "contrasts": contrasts}
    return {
        "format": FORMAT,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary_model": "ar1",
        "primary_contrast": PRIMARY_CONTRAST,
        "secondary_contrast": SECONDARY_CONTRAST,
        "planned_blocks_per_model": dict(PLANNED_BLOCKS),
        "planned_packages": 130,
        "planned_search_calls": 520,
        "models": models,
        "pooled": False,
        "automatic_arm_selection": False,
    }
