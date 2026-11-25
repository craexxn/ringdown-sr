"""Assess fixed main-study selections without changing any candidate choice."""

import copy
import math
from collections import Counter
from fractions import Fraction
from pathlib import PurePosixPath

import numpy as np
from scipy.stats import t as student_t

from . import noise_followup_assessment as followup
from . import noise_pilot_assessment as pilot
from .assessment_sources import fingerprint, json_bytes, read_json
from .losses import CovarianceLoss, mean_squared_error
from .structure import _validated_tree
from .structure_proof import assess_structure

FORMAT = "ringdown-sr-main-study-assessment-1"
SIGNALS = ("signal_200_4ms", "signal_250_6ms")
ARMS = ("ordinary", "known_covariance", "estimated_64s", "estimated_4096s")
PLANNED_BLOCKS = {"ar1": 30, "white": 10}
ROLES = ("training", "main", "support", "endpoints")
PRIMARY_ENDPOINT = "main_relative_l2"
PRIMARY_CONTRAST = "estimated_4096s_minus_estimated_64s"
CONTRASTS = (
    (PRIMARY_CONTRAST, "estimated_4096s", "estimated_64s"),
    ("estimated_64s_minus_ordinary", "estimated_64s", "ordinary"),
    ("estimated_4096s_minus_ordinary", "estimated_4096s", "ordinary"),
    ("estimated_64s_minus_known_covariance", "estimated_64s", "known_covariance"),
    ("estimated_4096s_minus_known_covariance", "estimated_4096s", "known_covariance"),
    ("known_covariance_minus_ordinary", "known_covariance", "ordinary"),
)
MAIN_INTERVAL = (Fraction(0), Fraction(1, 40))
IDENTITY_FIELDS = {
    "signal_id",
    "case_id",
    "model",
    "block",
    "condition",
    "grid",
    "package_sha256",
    "input_sha256",
    "selected_member_path",
}
FAMILY_STATUSES = {"proven_member", "proven_nonmember", "unresolved", "not_assessed"}
DOMAIN_STATUSES = {
    "defined_everywhere",
    "removable_holes",
    "nonremovable_singularities",
    "mixed",
    "nowhere_defined",
    "unresolved",
    "not_assessed",
}


def _identity(identity, status):
    if (
        type(identity) is not dict
        or set(identity) != IDENTITY_FIELDS
        or identity["signal_id"] not in SIGNALS
        or identity["model"] not in PLANNED_BLOCKS
        or type(identity["block"]) is not int
        or not 1 <= identity["block"] <= PLANNED_BLOCKS[identity["model"]]
        or identity["case_id"]
        != f"{identity['signal_id']}-{identity['model']}-{identity['block']:02d}"
        or identity["condition"] not in ARMS
        or identity["grid"] != "uniform"
    ):
        raise ValueError("Invalid main-study source identity.")
    for key in ("package_sha256", "input_sha256"):
        value = identity[key]
        if value is None and status == "not_run":
            continue
        if (
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("Main-study identity requires canonical source hashes.")
    path = identity["selected_member_path"]
    if status != "success":
        if path is not None:
            raise ValueError("An unavailable output cannot have a selected member.")
    elif (
        type(path) is not str
        or not path
        or path == "."
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or str(PurePosixPath(path)) != path
    ):
        raise ValueError("Invalid selected-member source path.")


def _references(arrays):
    references = {}
    for role, time_key, truth_key in (
        ("training", "time_s", "signal"),
        ("main", "main_time_s", "main_truth"),
        ("support", "support_time_s", "support_truth"),
        ("endpoints", "endpoint_time_s", "endpoint_truth"),
    ):
        times = pilot._vector(arrays[time_key], time_key)
        truth = pilot._vector(arrays[truth_key], truth_key)
        if times.shape != truth.shape or not np.all(times[1:] > times[:-1]):
            raise ValueError("Reference dimensions or ordered axes differ.")
        if not np.any(truth != 0):
            raise ValueError("A relative L2 reference must have a positive norm.")
        references[role] = {"time_s": times, "truth": truth}
    training = references["training"]["time_s"]
    if not np.array_equal(training, np.arange(103, dtype=np.float64) / 4096):
        raise ValueError("The main-study acquisition must use the bound N103 axis.")
    for role, end in (("main", 0.025), ("support", 102 / 4096)):
        times = references[role]["time_s"]
        if (
            times.size != 1024
            or times[0] <= 0
            or times[-1] >= end
            or np.isin(times, training).any()
        ):
            raise ValueError("Main-study diagnostic axes must be open held-out grids.")
    if not np.array_equal(references["endpoints"]["time_s"], [0.0, 0.025]):
        raise ValueError("Endpoint diagnostics must retain both nominal endpoints.")
    return references


def _inputs(arrays):
    references = _references(arrays)
    observed = pilot._vector(arrays["observed"], "observed")
    if observed.shape != references["training"]["truth"].shape:
        raise ValueError("Observed and signal dimensions differ.")
    covariance = np.asarray(arrays["covariance_true"])
    if covariance.dtype != np.dtype("float64"):
        raise ValueError("True covariance must use Float64.")
    objective = CovarianceLoss(covariance)
    if objective.n_samples != observed.size:
        raise ValueError("True covariance and observation dimensions differ.")
    return references, observed, objective


def _unavailable(reason):
    return {
        "status": "not_available",
        "reason": reason,
        "relative_l2": None,
        "relative_l2_reason": reason,
        "rms_over_amplitude": None,
        "max_over_amplitude": None,
    }


def _norm_ratio(numerator, scale, denominator, reference_scale):
    if numerator == 0:
        return 0.0
    a, ae = math.frexp(numerator)
    b, be = math.frexp(scale)
    c, ce = math.frexp(denominator)
    d, de = math.frexp(reference_scale)
    try:
        result = math.ldexp((a * b) / (c * d), ae + be - ce - de)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def curve_metrics(prediction, truth, amplitude, *, reason=None):
    """Compute discrete equal-weight errors without overflowing differences/squares.

    A nonfinite original tree invalidates the whole grid endpoint. Finite point
    fragments may still be plotted, but never become a smaller error denominator.
    """
    truth = pilot._vector(truth, "truth")
    if not pilot._finite(amplitude) or amplitude == 0:
        raise ValueError("Amplitude must be finite and nonzero.")
    amplitude = abs(float(amplitude))
    reference_maximum = float(np.max(np.abs(truth)))
    if reference_maximum == 0:
        raise ValueError("A relative L2 reference must have a positive norm.")
    if prediction is None:
        if type(reason) is not str or not reason:
            raise ValueError("Unavailable predictions require an explicit reason.")
        return _unavailable(reason)
    prediction = pilot._vector(prediction, "prediction")
    if prediction.shape != truth.shape:
        raise ValueError("Prediction and truth dimensions differ.")
    # Power-of-two scaling avoids an extra rounded division before subtracting
    # nearby Binary64 values, while keeping even opposite extreme values safe.
    reference_scale = math.ldexp(1.0, math.frexp(reference_maximum)[1] - 1)
    maximum_magnitude = max(float(np.max(np.abs(prediction))), reference_maximum)
    scale = math.ldexp(1.0, math.frexp(maximum_magnitude)[1] - 1)
    difference = prediction / scale - truth / scale
    norm = math.hypot(*difference)
    reference_norm = math.hypot(*(truth / reference_scale))
    relative = _norm_ratio(norm, scale, reference_norm, reference_scale)
    rms = pilot._scaled_ratio(norm / math.sqrt(truth.size), scale, amplitude)
    maximum = pilot._scaled_ratio(float(np.max(np.abs(difference))), scale, amplitude)
    complete = all(value is not None for value in (relative, rms, maximum))
    return {
        "status": "available" if complete else "numerical_unresolved",
        "reason": None if complete else "one_or_more_error_metrics_out_of_range",
        "relative_l2": relative,
        "relative_l2_reason": None
        if relative is not None
        else "relative_l2_out_of_range",
        "rms_over_amplitude": rms,
        "max_over_amplitude": maximum,
    }


def prediction_by_role(selected, arrays):
    """Replay the unchanged selected tree, retaining its native training vector."""
    _validated_tree(selected["tree"])
    references = _references(arrays)
    native = pilot._vector(selected["prediction"], "selected native prediction")
    if native.shape != references["training"]["truth"].shape:
        raise ValueError("Selected native prediction differs from training dimensions.")
    result = {}
    for role, reference in references.items():
        prediction, reason = (
            (native, None)
            if role == "training"
            else pilot._prediction(selected["tree"], reference["time_s"])
        )
        result[role] = {"prediction": prediction, "reason": reason}
    return result


def topology_descriptor(tree):
    """Replace only constant values; preserve ordered original syntax exactly."""
    _validated_tree(tree)

    def visit(node):
        if node["kind"] == "constant":
            return {"kind": "constant", "value": "*"}
        if node["kind"] == "variable":
            return copy.deepcopy(node)
        return {
            **{key: value for key, value in node.items() if key != "children"},
            "children": [visit(child) for child in node["children"]],
        }

    return visit(tree)


def assess_package(verified_report, arrays, *, amplitude, source_identity):
    """Assess one already verified original scientific package without reselection."""
    status = verified_report["package_status"]
    if status not in {"success", "failed", "not_run"}:
        raise ValueError("An assessment requires a completed package outcome.")
    _identity(source_identity, status)
    if not pilot._finite(amplitude) or amplitude == 0:
        raise ValueError("Generating amplitude must be finite and nonzero.")
    amplitude = abs(float(amplitude))
    calls = verified_report["search_calls"]
    if type(calls) is not int or calls != (0 if status == "not_run" else 4):
        raise ValueError("Scientific packages retain their four planned searches.")
    costs = followup._costs(verified_report)
    selected = verified_report["selected_candidate"]
    if (status == "success") != (selected is not None):
        raise ValueError("Package status and original candidate disagree.")
    references = observed = objective = None
    if arrays is not None:
        references, observed, objective = _inputs(arrays)
    elif status != "not_run":
        raise ValueError("An executed package requires original input arrays.")
    reason = None if status == "success" else "package_" + status
    if status == "failed":
        reason = verified_report.get("failure_reason", reason)
    record = {
        "format": FORMAT,
        "source_identity": copy.deepcopy(source_identity),
        "status": status,
        "original_candidate": copy.deepcopy(selected),
        "planned_members": 4,
        "search_calls": calls,
        "costs": copy.deepcopy(costs),
        "amplitude": amplitude,
        "background_duration_seconds": {
            "estimated_64s": 64,
            "estimated_4096s": 4096,
        }.get(source_identity["condition"]),
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary": {"status": "not_available", "reason": reason, "value": None},
        "errors": {role: _unavailable(reason) for role in ROLES},
        "diagnostics": {
            key: {"status": "not_available", "reason": reason, "value": None}
            for key in ("ordinary_mse", "q_true_per_sample")
        },
        "prediction_evaluation": {
            "training": "verified_native_selected_prediction",
            **{role: "original_binary_tree_float64_python" for role in ROLES[1:]},
            "purpose": "post_selection_only",
        },
        "reference_binding": None
        if references is None
        else {
            role: {key: fingerprint(value) for key, value in reference.items()}
            for role, reference in references.items()
        },
        "supplemental": {
            key: {"status": "not_assessed"}
            for key in (
                "algebraic_identity",
                "domain",
                "original_family",
                "continuous_extension",
                "remainder",
                "new_parameter_match",
                "physical_identification",
            )
        },
        "topology_descriptor": None,
    }
    if status != "success":
        return record
    predictions = prediction_by_role(selected, arrays)
    for role, reference in references.items():
        record["errors"][role] = curve_metrics(
            predictions[role]["prediction"],
            reference["truth"],
            amplitude,
            reason=predictions[role]["reason"],
        )
    endpoint = record["errors"]["main"]
    record["primary"] = {
        "status": "available"
        if endpoint["relative_l2"] is not None
        else "not_available",
        "reason": endpoint["relative_l2_reason"],
        "value": endpoint["relative_l2"],
    }
    native = predictions["training"]["prediction"]
    with np.errstate(over="ignore", invalid="ignore"):
        residual = native - observed
    record["diagnostics"] = {
        "ordinary_mse": pilot._scalar_diagnostic(mean_squared_error, residual),
        "q_true_per_sample": pilot._scalar_diagnostic(objective.mean_squared, residual),
    }
    # Canonical JSON removes native tuple/list representation differences before
    # these records enter the immutable publication and independent replay.
    proof = read_json(json_bytes(assess_structure(selected["tree"], MAIN_INTERVAL)))
    record["supplemental"] = {
        **proof,
        "physical_identification": {"status": "not_assessed"},
    }
    record["topology_descriptor"] = topology_descriptor(selected["tree"])
    return record


def _validate_record(record):
    status = record.get("status")
    if record.get("format") != FORMAT or status not in {"success", "failed", "not_run"}:
        raise ValueError("Invalid main-study assessment record.")
    identity = record["source_identity"]
    _identity(identity, status)
    if record.get("primary_endpoint") != PRIMARY_ENDPOINT:
        raise ValueError("The main endpoint must be the bound relative L2 error.")
    if type(record.get("planned_members")) is not int or record["planned_members"] != 4:
        raise ValueError("Scientific packages require four planned members.")
    if type(record.get("search_calls")) is not int or record["search_calls"] != (
        0 if status == "not_run" else 4
    ):
        raise ValueError("Invalid scientific search-call accounting.")
    duration = {"estimated_64s": 64, "estimated_4096s": 4096}.get(identity["condition"])
    if record.get("background_duration_seconds") != duration:
        raise ValueError("Background duration differs from the assigned arm.")
    if (status == "success") != (record.get("original_candidate") is not None):
        raise ValueError("Assessment status and original candidate disagree.")
    primary = record["primary"]
    if type(primary) is not dict or set(primary) != {"status", "reason", "value"}:
        raise ValueError("Invalid primary endpoint fields.")
    if primary["status"] == "available":
        if (
            status != "success"
            or not pilot._finite(primary["value"])
            or primary["value"] < 0
            or primary["reason"] is not None
        ):
            raise ValueError("Invalid available primary endpoint.")
    elif (
        primary["status"] != "not_available"
        or primary["value"] is not None
        or type(primary["reason"]) is not str
        or not primary["reason"]
    ):
        raise ValueError("Invalid unavailable primary endpoint.")
    endpoint = record["errors"]["main"]
    if (
        primary["value"] != endpoint["relative_l2"]
        or primary["reason"] != endpoint["relative_l2_reason"]
    ):
        raise ValueError("Primary endpoint differs from its stored main-grid errors.")
    if not pilot._finite(record.get("amplitude")) or record["amplitude"] <= 0:
        raise ValueError("Assessment amplitude must be finite and positive.")
    for key, permitted in (
        ("original_family", FAMILY_STATUSES),
        ("domain", DOMAIN_STATUSES),
    ):
        state = record["supplemental"][key]["status"]
        if state not in permitted or (state == "not_assessed") != (status != "success"):
            raise ValueError("Invalid supplemental assessment status.")
    if status == "success":
        if record.get("topology_descriptor") != topology_descriptor(
            record["original_candidate"]["tree"]
        ):
            raise ValueError("Topology descriptor differs from the original tree.")
    elif record.get("topology_descriptor") is not None:
        raise ValueError("Missing outputs cannot be counted as formula types.")
    followup._costs(record)
    return (
        identity["signal_id"],
        identity["model"],
        identity["block"],
        identity["condition"],
    )


def _paired_stats(entries, planned, *, primary):
    stats = pilot._stats(entries, planned)
    complete = stats["available"] == planned and stats["sample_sd"] is not None
    confidence = 0.975 if primary else 0.95
    interval = {
        "confidence": confidence,
        "method": "student_t_mean_approximate",
        "degrees_of_freedom": planned - 1,
        "critical_value": None,
        "lower": None,
        "upper": None,
        "status": "not_available",
        "reason": "requires_all_planned_pairs_and_finite_sample_sd",
        "simultaneous_family_size": 2 if primary else None,
        "family_confidence": 0.95 if primary else None,
        "multiplicity": "bonferroni_two_predeclared_signal_contrasts"
        if primary
        else "none_secondary_descriptive",
        "scope": "fixed_signal_and_grid_noise_background_and_search_variation",
        "decision_rule": False,
    }
    mcse = None
    if complete:
        mcse = stats["sample_sd"] / math.sqrt(planned)
        critical = float(student_t.ppf((1 + confidence) / 2, planned - 1))
        width = critical * mcse
        lower, upper = stats["mean"] - width, stats["mean"] + width
        if all(math.isfinite(v) for v in (critical, width, lower, upper)):
            interval.update(
                status="available",
                critical_value=critical,
                lower=lower,
                upper=upper,
                reason="approximation_may_be_poor_for_skewness_spikes_or_small_n",
            )
        else:
            interval["reason"] = "interval_out_of_range"
    stats.update(
        mcse=mcse,
        interval=interval,
        mcse_reason="finite_replication_estimate_only"
        if complete
        else "requires_all_planned_pairs_and_finite_sample_sd",
        denominator_scope="all_planned_pairs"
        if complete
        else "available_pairs_conditional_on_both_endpoints",
    )
    return stats


def _contrasts(indexed, signal_id, model, planned):
    result = {}
    for name, left, right in CONTRASTS:
        entries, availability = [], Counter()
        for block in range(1, planned + 1):
            a, b = (
                indexed[signal_id, model, block, arm]["primary"]
                for arm in (left, right)
            )
            available_a, available_b = (
                item["status"] == "available" for item in (a, b)
            )
            availability[
                "both_available"
                if available_a and available_b
                else "only_left_available"
                if available_a
                else "only_right_available"
                if available_b
                else "both_unavailable"
            ] += 1
            value = a["value"] - b["value"] if available_a and available_b else None
            reason = (
                None if value is not None else "one_or_both_pair_endpoints_unavailable"
            )
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
        primary = model == "ar1" and name == PRIMARY_CONTRAST
        result[name] = {
            **_paired_stats(entries, planned, primary=primary),
            "left": left,
            "right": right,
            "is_primary": primary,
            "pair_availability": {
                key: availability[key]
                for key in (
                    "both_available",
                    "only_left_available",
                    "only_right_available",
                    "both_unavailable",
                )
            },
        }
    return result


def _structure_counts(group, planned):
    result = {}
    for field in ("original_family", "domain"):
        counts = Counter(record["supplemental"][field]["status"] for record in group)
        result[field] = {"counts": dict(sorted(counts.items())), "planned": planned}
    descriptors = Counter(
        json_bytes(record["topology_descriptor"])
        for record in group
        if record["topology_descriptor"] is not None
    )
    maximum = max(descriptors.values(), default=0)
    result["topology"] = {
        "planned": planned,
        "available": sum(descriptors.values()),
        "missing_outputs": planned - sum(descriptors.values()),
        "distinct_descriptors": len(descriptors),
        "most_frequent_count": maximum,
        "most_frequent_fraction_of_planned": maximum / planned,
        "frequencies": [
            {"descriptor": read_json(key), "count": count}
            for key, count in sorted(descriptors.items())
        ],
        "semantic_or_physical_identity_assessed": False,
    }
    return result


def summary(records, *, signal_id=None):
    """Require every planned slot and retain model/signal strata and failed outputs."""
    if signal_id is not None and signal_id not in SIGNALS:
        raise ValueError("Unknown main-study signal section.")
    signals = SIGNALS if signal_id is None else (signal_id,)
    indexed = {}
    for record in records:
        key = _validate_record(record)
        if key in indexed:
            raise ValueError("Duplicate main-study signal/model/block/arm output.")
        indexed[key] = record
    expected = {
        (signal, model, block, arm)
        for signal in signals
        for model, planned in PLANNED_BLOCKS.items()
        for block in range(1, planned + 1)
        for arm in ARMS
    }
    if set(indexed) != expected:
        raise ValueError(
            "Assessment inventory differs from all planned main-study slots."
        )
    result = {}
    for signal in signals:
        models = {}
        for model, planned in PLANNED_BLOCKS.items():
            groups = {}
            for arm in ARMS:
                group = [
                    indexed[signal, model, block, arm]
                    for block in range(1, planned + 1)
                ]
                entries = [
                    {"block": r["source_identity"]["block"], **r["primary"]}
                    for r in group
                ]
                groups[arm] = {
                    "primary": pilot._stats(entries, planned),
                    "package_status_counts": dict(Counter(r["status"] for r in group)),
                    "failure_denominator": planned,
                    "failed_or_not_run": sum(r["status"] != "success" for r in group),
                    "failure_fraction": sum(r["status"] != "success" for r in group)
                    / planned,
                    "unavailable_primary_endpoints": sum(
                        r["primary"]["status"] != "available" for r in group
                    ),
                    "new_search_calls": sum(r["search_calls"] for r in group),
                    "original_package_costs": followup._cost_summary(group),
                    "structure": _structure_counts(group, planned),
                }
            models[model] = {
                "conditions": groups,
                "contrasts": _contrasts(indexed, signal, model, planned),
            }
        result[signal] = {"models": models}
    return {
        "format": FORMAT,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary_model": "ar1",
        "primary_contrasts": [
            {"signal_id": signal, "model": "ar1", "contrast": PRIMARY_CONTRAST}
            for signal in signals
        ],
        "primary_family_size": 2,
        "planned_blocks_per_model_per_signal": dict(PLANNED_BLOCKS),
        "planned_packages": len(expected),
        "planned_new_search_calls": 4 * len(expected),
        "new_search_calls": sum(r["search_calls"] for r in indexed.values()),
        "new_package_costs": followup._cost_summary(list(indexed.values())),
        "signals": result,
        "pooled": False,
        "automatic_arm_selection": False,
        "cost_scope": "Contained original package costs only; enclosing case/section, preparation, technical, verification and export costs remain separate.",
        "decision": "prespecified_effect_estimation_no_automatic_method_choice",
    }
