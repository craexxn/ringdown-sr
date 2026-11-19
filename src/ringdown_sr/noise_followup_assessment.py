"""Assess original duration/sampling outputs without changing their selections."""

import copy
import math
from collections import Counter
from pathlib import PurePosixPath

import numpy as np

from . import noise_background_assessment as background
from . import noise_followup_inputs as inputs
from . import noise_pilot_assessment as pilot
from .assessment_sources import fingerprint
from .losses import mean_squared_error
from .structure import _validated_tree

FORMAT = "ringdown-sr-noise-followup-assessment-1"
ARMS = (*inputs.ARMS_A, *inputs.ARMS_B)
PLANNED_BLOCKS = {"ar1": 20, "white": 6}
ROLES = pilot.ROLES
PRIMARY_ENDPOINT = "irregular_rms_over_amplitude"
PRIMARY_CONTRASTS = {
    "duration": "estimated_4096s_minus_estimated_64s",
    "sampling": "jitter_known_covariance_minus_known_covariance",
}
CONTRASTS = {
    "duration": (
        (PRIMARY_CONTRASTS["duration"], "estimated_4096s", "estimated_64s"),
        ("estimated_64s_minus_ordinary", "estimated_64s", "ordinary"),
        ("estimated_4096s_minus_ordinary", "estimated_4096s", "ordinary"),
        (
            "estimated_64s_minus_known_covariance",
            "estimated_64s",
            "known_covariance",
        ),
        (
            "estimated_4096s_minus_known_covariance",
            "estimated_4096s",
            "known_covariance",
        ),
        ("known_covariance_minus_ordinary", "known_covariance", "ordinary"),
    ),
    "sampling": (
        (
            PRIMARY_CONTRASTS["sampling"],
            "jitter_known_covariance",
            "known_covariance",
        ),
        ("jitter_ordinary_minus_ordinary", "jitter_ordinary", "ordinary"),
        ("known_covariance_minus_ordinary", "known_covariance", "ordinary"),
        (
            "jitter_known_covariance_minus_jitter_ordinary",
            "jitter_known_covariance",
            "jitter_ordinary",
        ),
    ),
}
IDENTITY_FIELDS = {
    "model",
    "block",
    "condition",
    "grid",
    "package_sha256",
    "input_sha256",
    "selected_member_path",
}


def conditions(block):
    """Return the exact output inventory, including referenced sampling controls."""
    if block == "duration":
        return inputs.ARMS_A
    if block == "sampling":
        return ("ordinary", "known_covariance", *inputs.ARMS_B)
    if block == "all":
        return ARMS
    raise ValueError("Unknown follow-up block; expected duration, sampling or all.")


def _identity(identity, status):
    if (
        type(identity) is not dict
        or set(identity) != IDENTITY_FIELDS
        or identity["model"] not in PLANNED_BLOCKS
        or type(identity["block"]) is not int
        or not 1 <= identity["block"] <= PLANNED_BLOCKS[identity["model"]]
        or identity["condition"] not in ARMS
        or identity["grid"]
        != ("jitter" if identity["condition"] in inputs.ARMS_B else "uniform")
    ):
        raise ValueError("Invalid follow-up source identity or acquisition grid.")
    for name in ("package_sha256", "input_sha256"):
        value = identity[name]
        if value is None and status == "not_run":
            continue
        if (
            type(value) is not str
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("Follow-up identity needs bound source SHA-256 values.")
    path = identity["selected_member_path"]
    if status != "success":
        if path is not None:
            raise ValueError("Unavailable follow-up output has a selected-member path.")
    elif (
        type(path) is not str
        or not path
        or path == "."
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or str(PurePosixPath(path)) != path
    ):
        raise ValueError("Invalid selected-member source path.")


def _costs(record):
    values = record.get("costs")
    if type(values) is not dict or any(
        value is not None and (not pilot._finite(value) or value < 0)
        for value in values.values()
    ):
        raise ValueError("Invalid follow-up costs; unknown values must remain null.")
    return values


def assess_package(verified_report, arrays, *, amplitude, source_identity):
    """Evaluate only the verified selected tree on the prospectively bound grids.

    Inputs and package provenance are verified by the caller. Training values
    remain the original native predictions, while both held-out grids replay
    the unchanged binary tree. No family, domain or parameter claim is added.
    """
    status = verified_report["package_status"]
    if status not in {"success", "failed", "not_run"}:
        raise ValueError("An assessment requires a completed package outcome.")
    _identity(source_identity, status)
    if not pilot._finite(amplitude) or amplitude == 0:
        raise ValueError("Generating amplitude must be finite and nonzero.")
    amplitude = abs(float(amplitude))
    calls = verified_report["search_calls"]
    if type(calls) is not int or calls != (0 if status == "not_run" else 4):
        raise ValueError("Follow-up packages retain their four planned searches.")
    costs = _costs(verified_report)
    selected = verified_report["selected_candidate"]
    if (status == "success") != (selected is not None):
        raise ValueError("Package status and original selected candidate disagree.")
    references = observed = objective = None
    if arrays is not None:
        references, _, observed, objective = pilot._inputs(arrays)
    elif status != "not_run":
        raise ValueError("An executed package requires its original input arrays.")
    reason = None if status == "success" else "package_" + status
    condition = source_identity["condition"]
    duration = (
        64
        if condition == "estimated_64s"
        else 4096
        if condition == "estimated_4096s"
        else None
    )
    record = {
        "format": FORMAT,
        "source_identity": copy.deepcopy(source_identity),
        "status": status,
        "original_candidate": copy.deepcopy(selected),
        "planned_members": 4,
        "search_calls": calls,
        "costs": copy.deepcopy(costs),
        "amplitude": amplitude,
        "background_duration_seconds": duration,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary": {"status": "not_available", "reason": reason, "value": None},
        "amplitude_errors": {
            role: pilot._unavailable(reason, amplitude=True) for role in ROLES
        },
        "diagnostics": {
            name: {"status": "not_available", "reason": reason, "value": None}
            for name in ("ordinary_mse", "q_true_per_sample")
        },
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
        "supplemental": {
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
    }
    if status != "success":
        return record
    _validated_tree(selected["tree"])
    native = pilot._vector(selected["prediction"], "selected native prediction")
    if native.shape != observed.shape:
        raise ValueError("Selected native prediction differs from training dimensions.")
    for role, reference in references.items():
        prediction, failure = (
            (native, None)
            if role == "training"
            else pilot._prediction(selected["tree"], reference["time_s"])
        )
        record["amplitude_errors"][role] = (
            pilot._unavailable(failure, amplitude=True)
            if prediction is None
            else pilot._amplitude_errors(prediction, reference["truth"], amplitude)
        )
    endpoint = record["amplitude_errors"]["irregular"]
    value = endpoint["rms_over_amplitude"]
    record["primary"] = {
        "status": "available" if value is not None else endpoint["status"],
        "reason": None if value is not None else endpoint["reason"],
        "value": value,
    }
    with np.errstate(over="ignore", invalid="ignore"):
        residual = observed - native
    record["diagnostics"] = {
        "ordinary_mse": pilot._scalar_diagnostic(mean_squared_error, residual),
        "q_true_per_sample": pilot._scalar_diagnostic(objective.mean_squared, residual),
    }
    return record


def _validate_record(record):
    status = record.get("status")
    if (
        record.get("format") != FORMAT
        or record.get("primary_endpoint") != PRIMARY_ENDPOINT
        or status not in {"success", "failed", "not_run"}
    ):
        raise ValueError("Invalid follow-up assessment record.")
    identity = record["source_identity"]
    _identity(identity, status)
    condition = identity["condition"]
    duration = {"estimated_64s": 64, "estimated_4096s": 4096}.get(condition)
    if record.get("background_duration_seconds") != duration or (
        duration is not None and type(record["background_duration_seconds"]) is not int
    ):
        raise ValueError("Assessment duration differs from the assigned condition.")
    if type(record.get("planned_members")) is not int or record["planned_members"] != 4:
        raise ValueError("Follow-up assessment must retain four planned members.")
    if type(record.get("search_calls")) is not int or record["search_calls"] != (
        0 if status == "not_run" else 4
    ):
        raise ValueError("Invalid follow-up search-call accounting.")
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
        primary["value"] is not None
        or primary["status"] not in {"not_available", "numerical_unresolved"}
        or type(primary["reason"]) is not str
        or not primary["reason"]
    ):
        raise ValueError("Invalid unavailable primary endpoint.")
    if (status == "success") != (record.get("original_candidate") is not None):
        raise ValueError("Assessment status and retained original candidate disagree.")
    _costs(record)
    return identity["model"], identity["block"], condition


def _cost_summary(records):
    fields = sorted({field for record in records for field in record["costs"]})
    result = {}
    for field in fields:
        values = [record["costs"].get(field) for record in records]
        known = [value for value in values if value is not None]
        try:
            subtotal = (
                sum(known)
                if all(type(value) is int for value in known)
                else math.fsum(known)
            )
        except OverflowError:
            subtotal = None
        result[field] = {
            "total": subtotal if len(known) == len(values) else None,
            "known_subtotal": subtotal,
            "missing_packages": len(values) - len(known),
            "package_count": len(values),
            "reason": "sum_out_of_range"
            if subtotal is None
            else None
            if len(known) == len(values)
            else "one_or_more_package_costs_unknown",
        }
    return result


def _contrasts(indexed, model, planned, block):
    definitions = (
        tuple(dict.fromkeys((*CONTRASTS["duration"], *CONTRASTS["sampling"])))
        if block == "all"
        else CONTRASTS[block]
    )
    result = {}
    for name, left, right in definitions:
        entries = []
        for index in range(1, planned + 1):
            a, b = (
                indexed[model, index, left]["primary"],
                indexed[model, index, right]["primary"],
            )
            available = a["status"] == b["status"] == "available"
            value = a["value"] - b["value"] if available else None
            reason = None if available else "one_or_both_pair_endpoints_unavailable"
            if value is not None and not math.isfinite(value):
                value, reason = None, "paired_difference_out_of_range"
            entries.append(
                {
                    "block": index,
                    "status": "available" if value is not None else "not_available",
                    "reason": reason,
                    "value": value,
                }
            )
        stats = background._paired_stats(entries, planned)
        stats["interval_95"]["scope"] = (
            "fixed_signal_and_predeclared_acquisition_grids_"
            "noise_background_and_search_variation"
        )
        result[name] = {**stats, "left": left, "right": right}
    return result


def summary(records, *, block="all"):
    """Summarize exact planned inventories, retaining failures and shared controls.

    Sampling contains the original uniform O/K assessments by reference. Their
    metrics participate in paired contrasts, but neither their searches nor
    their costs are counted as new sampling work. The all-block view requires
    exactly 156 distinct original outputs, never 208 duplicated references.
    """
    arms = conditions(block)
    indexed = {}
    for record in records:
        key = _validate_record(record)
        if key in indexed:
            raise ValueError("Duplicate follow-up model/block/condition output.")
        indexed[key] = record
    expected = {
        (model, index, arm)
        for model, planned in PLANNED_BLOCKS.items()
        for index in range(1, planned + 1)
        for arm in arms
    }
    if set(indexed) != expected:
        raise ValueError("Follow-up assessment inventory differs from the fixed block.")
    reused = {"ordinary", "known_covariance"} if block == "sampling" else set()
    models = {}
    for model, planned in PLANNED_BLOCKS.items():
        groups = {}
        for arm in arms:
            group = [indexed[model, index, arm] for index in range(1, planned + 1)]
            entries = [
                {"block": record["source_identity"]["block"], **record["primary"]}
                for record in group
            ]
            calls = sum(record["search_calls"] for record in group)
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
                "reused_control": arm in reused,
                "planned_new_search_calls": 0 if arm in reused else 4 * planned,
                "new_search_calls": 0 if arm in reused else calls,
                "referenced_search_calls": calls if arm in reused else 0,
                "original_package_costs": _cost_summary(group),
                "cost_role": "reference_only_do_not_add_to_new_block_costs"
                if arm in reused
                else "contained_original_package_costs",
            }
        models[model] = {
            "conditions": groups,
            "contrasts": _contrasts(indexed, model, planned, block),
        }
    new_records = [
        record for (_, _, arm), record in indexed.items() if arm not in reused
    ]
    references = [record for (_, _, arm), record in indexed.items() if arm in reused]
    return {
        "format": FORMAT,
        "block": block,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary_model": "ar1",
        "primary_contrasts": copy.deepcopy(PRIMARY_CONTRASTS)
        if block == "all"
        else {block: PRIMARY_CONTRASTS[block]},
        "planned_blocks_per_model": dict(PLANNED_BLOCKS),
        "planned_packages": len(expected),
        "planned_new_packages": len(new_records),
        "referenced_packages": len(references),
        "planned_new_search_calls": 4 * len(new_records),
        "planned_reference_search_calls": 4 * len(references),
        "new_search_calls": sum(record["search_calls"] for record in new_records),
        "referenced_search_calls": sum(record["search_calls"] for record in references),
        "new_package_costs": _cost_summary(new_records),
        "referenced_package_costs": _cost_summary(references),
        "models": models,
        "pooled": False,
        "automatic_arm_selection": False,
        "shared_controls_independent_between_blocks": False,
        "cost_scope": (
            "Original package costs only; preparation, technical preflight, "
            "verification and enclosing block costs remain separate. Sampling "
            "control references never count as new work."
        ),
        "decision": "descriptive_prespecified_comparisons_no_automatic_method_choice",
    }
