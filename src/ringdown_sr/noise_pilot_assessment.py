"""Diagnose verified original noise-pilot selections without selecting or fitting."""

import copy
import math
import statistics
from collections import Counter
from pathlib import PurePosixPath

import numpy as np

from . import remainder_assessment as remainder
from . import structure_assessment as structure
from .assessment_sources import fingerprint
from .losses import CovarianceLoss, mean_squared_error
from .noiseless_control import curve_errors
from .structure import _validated_tree
from .supplemental_assessment import grade_curve
from .symbolic import evaluate_tree

FORMAT = "ringdown-sr-noise-pilot-assessment-1"
MODELS = ("white", "ar1")
ARMS = ("ordinary", "known_covariance", "estimated_covariance")
CONTRASTS = (
    ("estimated_minus_ordinary", "estimated_covariance", "ordinary"),
    ("known_minus_ordinary", "known_covariance", "ordinary"),
    ("estimated_minus_known", "estimated_covariance", "known_covariance"),
)
ROLES = ("training", "diagnostic", "irregular")
IDENTITY_FIELDS = {
    "model",
    "block",
    "arm",
    "package_sha256",
    "input_sha256",
    "selected_member_path",
}


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _identity(identity, status):
    if (
        type(identity) is not dict
        or set(identity) != IDENTITY_FIELDS
        or identity["model"] not in MODELS
        or identity["arm"] not in ARMS
        or type(identity["block"]) is not int
        or identity["block"] < 1
    ):
        raise ValueError("Invalid noise-pilot source identity.")
    for key in ("package_sha256", "input_sha256"):
        value = identity[key]
        if value is None and status == "not_run":
            continue
        if (
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("Missing canonical source SHA-256.")
    path = identity["selected_member_path"]
    if status != "success":
        if path is not None:
            raise ValueError("An unavailable output cannot have a selected member.")
    elif (
        type(path) is not str
        or not path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or str(PurePosixPath(path)) != path
    ):
        raise ValueError("Invalid selected-member source path.")


def _vector(values, name):
    values = np.asarray(values)
    if (
        values.dtype != np.dtype("float64")
        or values.ndim != 1
        or not values.size
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("Expected finite nonempty Float64 vector: " + name)
    return values


def _inputs(arrays):
    references = {}
    for role, time_key, truth_key in (
        ("training", "time_s", "signal"),
        ("diagnostic", "diagnostic_time_s", "diagnostic_truth"),
        ("irregular", "irregular_time_s", "irregular_truth"),
    ):
        times, truth = (
            _vector(arrays[time_key], time_key),
            _vector(arrays[truth_key], truth_key),
        )
        if times.shape != truth.shape or not np.all(times[1:] > times[:-1]):
            raise ValueError("Reference shapes or time ordering differ.")
        references[role] = {"time_s": times, "truth": truth}
    binding = structure.interval_binding(references["training"]["time_s"])
    first, last = references["training"]["time_s"][[0, -1]]
    if first < 0 or any(
        np.any(
            (references[role]["time_s"] < first) | (references[role]["time_s"] > last)
        )
        for role in ("diagnostic", "irregular")
    ):
        raise ValueError("Diagnostic points leave the original training interval.")
    observed = _vector(arrays["observed"], "observed")
    if observed.shape != references["training"]["truth"].shape:
        raise ValueError("Observed and signal shapes differ.")
    covariance = np.asarray(arrays["covariance_true"])
    if covariance.dtype != np.dtype("float64"):
        raise ValueError("True covariance must use Float64.")
    objective = CovarianceLoss(covariance)
    if objective.n_samples != observed.size:
        raise ValueError("True covariance and observation dimensions differ.")
    return references, binding, observed, objective


def _unavailable(reason, *, amplitude=False):
    fields = (
        ("rms_over_amplitude", "max_over_amplitude")
        if amplitude
        else ("relative_rms", "relative_max")
    )
    return {"status": "not_available", "reason": reason, **dict.fromkeys(fields)}


def _scaled_ratio(value, scale, amplitude):
    if value == 0:
        return 0.0
    a, ae = math.frexp(value)
    b, be = math.frexp(scale)
    c, ce = math.frexp(amplitude)
    try:
        result = math.ldexp(a * b / c, ae + be - ce)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _amplitude_errors(prediction, truth, amplitude):
    scale = max(
        float(np.max(np.abs(prediction))), float(np.max(np.abs(truth))), amplitude
    )
    difference = prediction / scale - truth / scale
    rms = _scaled_ratio(
        math.hypot(*difference) / math.sqrt(truth.size), scale, amplitude
    )
    maximum = _scaled_ratio(float(np.max(np.abs(difference))), scale, amplitude)
    return {
        "status": "available"
        if rms is not None and maximum is not None
        else "numerical_unresolved",
        "reason": None
        if rms is not None and maximum is not None
        else "amplitude_error_out_of_range",
        "rms_over_amplitude": rms,
        "max_over_amplitude": maximum,
    }


def _prediction(tree, times):
    # Tree metadata is checked before this call. Only a known evaluation failure
    # is diagnostic unavailability; an unknown ValueError remains an error.
    try:
        return evaluate_tree(tree, times), None
    except ValueError as error:
        if str(error) != "Tree prediction is not finite.":
            raise
        return None, "nonfinite_original_tree_prediction"
    except (OverflowError, FloatingPointError):
        return None, "original_tree_evaluation_out_of_range"


def _scalar_diagnostic(function, residual):
    if not np.all(np.isfinite(residual)):
        return {
            "status": "not_available",
            "reason": "residual_out_of_range",
            "value": None,
        }
    try:
        value = function(residual)
    except ValueError as error:
        if str(error) not in {
            "The loss exceeds the finite float64 range.",
            "The whitened residual exceeds the finite float64 range.",
        }:
            raise
        return {"status": "numerical_unresolved", "reason": str(error), "value": None}
    if not _finite(value) or value < 0:
        raise ValueError("Invalid post-selection loss diagnostic.")
    return {"status": "available", "reason": None, "value": value}


def assess_package(verified_report, arrays, *, amplitude, source_identity):
    """Assess a previously verified package, retaining its native original choice.

    The caller owns source verification and binds these inputs into its guarded
    publication. This pure function never treats validation errors as fit errors.
    A planned not-run package may lack arrays and source hashes.
    """
    status = verified_report["package_status"]
    if status not in {"success", "failed", "not_run"}:
        raise ValueError("Unfinished or invalid package outcome.")
    _identity(source_identity, status)
    if not _finite(amplitude) or amplitude == 0:
        raise ValueError("The generating amplitude must be finite and nonzero.")
    amplitude = abs(float(amplitude))
    calls = verified_report["search_calls"]
    if type(calls) is not int or (calls != 0 if status == "not_run" else calls != 4):
        raise ValueError("Package search-call accounting differs.")
    costs = verified_report["costs"]
    if type(costs) is not dict or any(
        value is not None and (not _finite(value) or value < 0)
        for value in costs.values()
    ):
        raise ValueError("Invalid package costs; unknown values must remain null.")
    selected = verified_report["selected_candidate"]
    if (status == "success") != (selected is not None):
        raise ValueError("Package outcome and original selection disagree.")
    references = binding = observed = objective = None
    if arrays is not None:
        references, binding, observed, objective = _inputs(arrays)
    elif status != "not_run":
        raise ValueError("An executed package needs its original bound inputs.")
    reason = None if status == "success" else "package_" + status
    record = {
        "format": FORMAT,
        "source_identity": copy.deepcopy(source_identity),
        "status": status,
        "original_candidate": copy.deepcopy(selected),
        "planned_members": 4,
        "search_calls": calls,
        "costs": copy.deepcopy(costs),
        "amplitude": amplitude,
        "prediction_evaluation": {
            "training": "verified_native_selected_prediction",
            "diagnostic": "original_binary_tree_float64_python",
            "irregular": "original_binary_tree_float64_python",
            "purpose": "post_selection_only",
        },
        "reference_binding": None
        if references is None
        else {
            role: {key: fingerprint(value) for key, value in values.items()}
            for role, values in references.items()
        },
        "primary": {"status": "not_available", "reason": reason, "value": None},
        "amplitude_errors": {
            role: _unavailable(reason, amplitude=True) for role in ROLES
        },
        "curve_errors": {role: _unavailable(reason) for role in ROLES[:2]},
        "diagnostics": {
            name: {"status": "not_available", "reason": reason, "value": None}
            for name in ("ordinary_mse", "q_true_per_sample")
        },
        "supplemental": {
            "curve": {"status": "not_assessable", "grade": None, "reason": reason},
            **{
                name: {"status": "not_assessed"}
                for name in (
                    "algebraic_identity",
                    "domain",
                    "original_family",
                    "continuous_extension",
                    "remainder",
                    "new_parameter_match",
                )
            },
        },
    }
    if status != "success":
        return record
    _validated_tree(selected["tree"])
    native = _vector(selected["prediction"], "selected prediction")
    if native.shape != observed.shape:
        raise ValueError("Selected prediction and training inputs differ.")
    for role, reference in references.items():
        prediction, failure = (
            (native, None)
            if role == "training"
            else _prediction(selected["tree"], reference["time_s"])
        )
        if prediction is None:
            record["amplitude_errors"][role] = _unavailable(failure, amplitude=True)
            if role != "irregular":
                record["curve_errors"][role] = _unavailable(failure)
            continue
        record["amplitude_errors"][role] = _amplitude_errors(
            prediction, reference["truth"], amplitude
        )
        if role != "irregular":
            record["curve_errors"][role] = curve_errors(prediction, reference["truth"])
    primary = record["amplitude_errors"]["training"]
    record["primary"] = {
        "status": "available"
        if primary["rms_over_amplitude"] is not None
        else primary["status"],
        "reason": None
        if primary["rms_over_amplitude"] is not None
        else primary["reason"],
        "value": primary["rms_over_amplitude"],
    }
    with np.errstate(over="ignore", invalid="ignore"):
        residual = observed - native
    record["diagnostics"] = {
        "ordinary_mse": _scalar_diagnostic(mean_squared_error, residual),
        "q_true_per_sample": _scalar_diagnostic(objective.mean_squared, residual),
    }
    record["supplemental"]["curve"] = grade_curve(
        record["curve_errors"], source_verified=True
    )
    structure.supplement(record, binding)
    remainder.supplement(
        record, binding, {role: references[role] for role in ROLES[:2]}
    )
    return record


def _stats(entries, planned):
    values = [entry["value"] for entry in entries if entry["value"] is not None]
    result = {
        "planned": planned,
        "available": len(values),
        "unavailable": planned - len(values),
        "values": entries,
        "mean": None,
        "median": None,
        "minimum": None,
        "maximum": None,
        "sample_sd": None,
        "summary_reason": "no_available_values",
    }
    if not values:
        return result
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else statistics.mean(ordered[middle - 1 : middle + 1])
    )
    result.update(
        mean=statistics.mean(values),
        median=median,
        minimum=min(values),
        maximum=max(values),
        summary_reason=None,
    )
    if len(values) > 1:
        try:
            deviation = statistics.stdev(values)
            if not math.isfinite(deviation):
                raise OverflowError
            result["sample_sd"] = deviation
        except OverflowError:
            result["summary_reason"] = "sample_sd_out_of_range"
    return result


def summary(records, planned_blocks=6):
    """Summarize the exact planned inventory, keeping failures and model strata."""
    if type(planned_blocks) is not int or planned_blocks < 1:
        raise ValueError("The planned block count must be a positive integer.")
    indexed = {}
    for record in records:
        status = record["status"]
        if record.get("format") != FORMAT or status not in {
            "success",
            "failed",
            "not_run",
        }:
            raise ValueError("Invalid package assessment record.")
        identity = record["source_identity"]
        _identity(identity, status)
        key = identity["model"], identity["block"], identity["arm"]
        if key in indexed:
            raise ValueError("Duplicate model/block/arm assessment.")
        primary = record["primary"]
        value = primary["value"]
        if primary["status"] == "available":
            if status != "success" or not _finite(value) or value < 0:
                raise ValueError("Invalid available primary endpoint.")
        elif (
            value is not None
            or primary["status"] not in {"not_available", "numerical_unresolved"}
            or not primary.get("reason")
        ):
            raise ValueError("Invalid unavailable primary endpoint.")
        indexed[key] = record
    expected = {
        (model, block, arm)
        for model in MODELS
        for block in range(1, planned_blocks + 1)
        for arm in ARMS
    }
    if set(indexed) != expected:
        raise ValueError(
            "Assessment inventory differs from all planned model/block/arm slots."
        )
    models = {}
    for model in MODELS:
        arms = {}
        for arm in ARMS:
            group = [
                indexed[model, block, arm] for block in range(1, planned_blocks + 1)
            ]
            entries = [
                {"block": r["source_identity"]["block"], **r["primary"]} for r in group
            ]
            arms[arm] = {
                "primary": _stats(entries, planned_blocks),
                "package_status_counts": dict(Counter(r["status"] for r in group)),
                "failure_denominator": planned_blocks,
                "failed_or_not_run": sum(r["status"] != "success" for r in group),
                "failure_fraction": sum(r["status"] != "success" for r in group)
                / planned_blocks,
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
            for block in range(1, planned_blocks + 1):
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
            stats = _stats(entries, planned_blocks)
            complete = (
                planned_blocks == 6
                and stats["available"] == 6
                and stats["sample_sd"] is not None
            )
            stats.update(
                left=left,
                right=right,
                mcse=stats["sample_sd"] / math.sqrt(6) if complete else None,
                mcse_reason="small_n_estimate_only"
                if complete
                else "requires_all_six_pairs_and_finite_sample_sd",
                denominator_scope="available_pairs_conditional_on_both_endpoints",
            )
            contrasts[name] = stats
        models[model] = {"arms": arms, "contrasts": contrasts}
    return {
        "format": FORMAT,
        "planned_blocks_per_model": planned_blocks,
        "planned_packages": 6 * planned_blocks,
        "models": models,
        "pooled": False,
        "automatic_arm_selection": False,
    }
