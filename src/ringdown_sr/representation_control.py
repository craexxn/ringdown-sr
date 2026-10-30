"""Frozen coordinate controls and post-selection physical diagnostics, without search."""

import copy
import math
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction

import numpy as np

from .aliasing import rational_field
from .config import SearchBudget
from .noiseless_control import (
    CURVE_LIMITS,
    FS,
    _finite_median,
    curve_errors,
    parameter_match,
)
from .parameters import _prediction_replay, analyze_tree
from .pilot import _json_bytes, _sha256
from .symbolic import evaluate_tree

FORMAT = "ringdown-sr-representation-control-1"
PLAN_COMMIT = "311f87d2df9e47d3e326f24709b8085569f7b5f3"
PLAN_SHA256 = "16cfe818c312fb5bb0a6c594505ad76ba41e41bd7f4a37decc245677c6b8ad86"
CONDITIONS = ("baseline", "time_stretch", "complexity_frequency")
SEEDS = (20261020, 20261021, 20261022)


def condition_settings(condition):
    """Derive the sole scale from acquisition metadata, never from signal truth."""
    if condition not in CONDITIONS:
        raise ValueError("Unknown reviewed representation condition.")
    return {
        "condition": condition,
        "time_scale": 1.0 / (128 / FS) if condition == "time_stretch" else 1.0,
        "use_frequency": condition == "complexity_frequency",
        "use_frequency_in_tournament": condition == "complexity_frequency",
        "time_unit": "s",
    }


def planned_cells():
    cells = []
    for block, seed in enumerate(SEEDS):
        for offset in range(3):
            condition = CONDITIONS[(block + offset) % 3]
            cells.append(
                {
                    "number": len(cells) + 1,
                    "directory": f"cell-{len(cells) + 1:02d}",
                    "budget": asdict(SearchBudget(seed=seed, niterations=200)),
                    "condition": condition,
                    "settings": condition_settings(condition),
                    "status": "planned",
                }
            )
    return cells


def search_coordinates(arrays, condition):
    """Return immutable derived times; keep physical observations bitwise unchanged."""
    scale = condition_settings(condition)["time_scale"]
    coordinates = {
        "time_s": arrays["time_s"] * scale,
        "diagnostic_time_s": arrays["diagnostic_time_s"] * scale,
        "observed": arrays["observed"],
        "diagnostic_truth": arrays["diagnostic_truth"],
    }
    for values in coordinates.values():
        values.flags.writeable = False
    return coordinates


def _scale_field(field, factor):
    """Never turn unavailable source fields or a range failure into available data."""
    if field["status"] != "available" or factor == 1:
        return copy.deepcopy(field)
    value = field["value"]
    if not math.isfinite(value) or (value != 0 and abs(value) < sys.float_info.min):
        return {
            "status": "numerical_unresolved",
            "value": None,
            "reason": "source_conversion_range",
        }
    converted = rational_field(Fraction.from_float(value) * Fraction.from_float(factor))
    if converted["status"] != "available":
        converted["reason"] = "coordinate_" + converted["reason"]
    return converted


def physical_analysis(search_analysis, tree, physical_times, scale):
    """Convert separate numeric fields and replay against q(scale*t), preserving source."""
    source = search_analysis
    structure = {
        key: copy.deepcopy(source["structure"][key])
        for key in (
            "structure_status",
            "reason",
            "exponential_status",
            "amplitude_status",
        )
    }
    result = {
        "format": "ringdown-sr-physical-coordinate-analysis-1",
        "structure": structure,
        "structure_source": "search_analysis.structure; exact coefficients remain there",
        "raw_parameters": None,
        "raw_replay": {"status": "not_attempted", "reason": "unsupported_structure"},
        "alias": copy.deepcopy(source["alias"]),
        "alias_replay": {"status": "not_attempted", "reason": "unsupported_structure"},
        "time_scale": scale,
        "sample_rate_hz": FS,
        "physical_identification": "not_assessed",
    }
    if source["raw_parameters"] is None:
        return result
    factors = {
        "amplitude": 1.0,
        "exponential_rate_per_s": scale,
        "angular_frequency_per_s": scale,
        "phase_rad": 1.0,
        "decay_time_s": 1.0 / scale,
        "frequency_raw_signed_hz": scale,
        "frequency_raw_hz": scale,
    }
    raw = {
        key: _scale_field(source["raw_parameters"][key], factor)
        for key, factor in factors.items()
    }
    result["raw_parameters"] = raw
    alias = source["alias"]
    if alias["status"] == "available":
        frequency = _scale_field(alias["frequency_alias_hz"], scale)
        result["alias"] = {
            "status": "available"
            if frequency["status"] == "available"
            else "numerical_unresolved",
            "reason": frequency["reason"],
            "frequency_alias_hz": frequency,
            "phase_alias_rad": copy.deepcopy(alias["phase_alias_rad"]),
            "degeneracy": alias["degeneracy"],
            "sample_rate_hz": FS,
            "source": "search_analysis.alias; exact folding record remains there",
        }
    else:
        result["alias"] = {"status": alias["status"], "reason": alias["reason"]}
    for name in ("raw_replay", "alias_replay"):
        result[name] = {
            "status": "not_attempted",
            "reason": "search_" + name + "_not_passed",
        }
    try:
        original = evaluate_tree(tree, physical_times * scale)
    except ValueError:
        for name in ("raw_replay", "alias_replay"):
            result[name] = {
                "status": "failed",
                "reason": "nonfinite_original_prediction",
            }
        return result
    required = (
        "amplitude",
        "exponential_rate_per_s",
        "angular_frequency_per_s",
        "phase_rad",
    )
    if not all(raw[key]["status"] == "available" for key in required):
        for name in ("raw_replay", "alias_replay"):
            result[name] = {
                "status": "not_attempted",
                "reason": "unavailable_converted_coefficient",
            }
        return result
    amplitude, rate, frequency, phase = [raw[key]["value"] for key in required]
    with np.errstate(all="ignore"):
        if source["raw_replay"]["status"] == "passed":
            prediction = (
                amplitude
                * np.exp(rate * physical_times)
                * np.cos(frequency * physical_times + phase)
            )
            result["raw_replay"] = _prediction_replay(original, prediction)
        if (
            source["alias_replay"]["status"] == "passed"
            and result["alias"]["status"] == "available"
        ):
            prediction = (
                amplitude
                * np.exp(rate * physical_times)
                * np.cos(
                    2
                    * np.pi
                    * result["alias"]["frequency_alias_hz"]["value"]
                    * physical_times
                    + result["alias"]["phase_alias_rad"]["value"]
                )
            )
            result["alias_replay"] = _prediction_replay(original, prediction)
    return result


def diagnose_candidate(candidate, index, selected_index, arrays, condition):
    settings = condition_settings(condition)
    scale = settings["time_scale"]
    coordinates = search_coordinates(arrays, condition)
    source = analyze_tree(
        candidate["tree"], coordinates["time_s"], sample_rate_hz=FS / scale
    )
    physical = physical_analysis(source, candidate["tree"], arrays["time_s"], scale)
    curves = {}
    for grid, times, truth in (
        ("training", "time_s", "observed"),
        ("diagnostic", "diagnostic_time_s", "diagnostic_truth"),
    ):
        try:
            prediction = evaluate_tree(candidate["tree"], coordinates[times])
        except ValueError:
            curves[grid] = {
                "status": "not_available",
                "reason": "nonfinite_original_tree",
                "relative_rms": None,
                "relative_max": None,
            }
        else:
            curves[grid] = curve_errors(prediction, arrays[truth])
    marker = "not_assessed"
    if all(value["status"] == "available" for value in curves.values()):
        marker = (
            "within_tolerance"
            if all(
                value[key] <= limit
                for value in curves.values()
                for key, limit in CURVE_LIMITS.items()
            )
            else "outside_tolerance"
        )
    match = parameter_match(physical)
    if (
        match["status"] != "not_assessed"
        and physical["raw_parameters"] is not None
        and any(
            field["status"] != "available"
            for field in physical["raw_parameters"].values()
        )
    ):
        match.update(status="not_assessed", reason="unavailable_physical_parameter")
    return {
        "source_index": index,
        "is_selected": index == selected_index,
        "source_candidate_sha256": _sha256(_json_bytes(candidate)),
        "complexity": candidate["complexity"],
        "training_loss": candidate["loss"],
        "display_equation": candidate["display_equation"],
        "search_analysis": source,
        "physical_analysis": physical,
        "curve_errors": curves,
        "curve_marker": marker,
        "parameter_match": match,
        "physical_identification": "not_assessed",
    }


def _selected(cell):
    if cell is None or cell["status"] != "completed":
        return None
    diagnosis = cell["diagnostics"]
    return diagnosis["candidates"][diagnosis["selected_index"]]


def _metrics(candidate):
    values = {"training_mse": candidate["training_loss"]}
    values.update(
        {
            f"{grid}/{name}": value
            for grid, errors in candidate["curve_errors"].items()
            for name, value in errors.items()
            if name in CURVE_LIMITS
        }
    )
    values.update(
        {
            "parameter/" + name: value
            for name, value in candidate["parameter_match"]["errors"].items()
        }
    )
    return values


def _markers(candidate):
    if candidate is None:
        return None
    return {
        "curve": candidate["curve_marker"],
        "structure": candidate["search_analysis"]["structure"]["structure_status"],
        "parameters": candidate["parameter_match"]["status"],
    }


def _metric_availability(candidate, name, value):
    if name == "training_mse":
        source = {"status": "available", "reason": None}
    elif name.startswith("parameter/"):
        source = candidate["parameter_match"]
    else:
        source = candidate["curve_errors"][name.split("/", 1)[0]]
    available = (
        value is not None
        and math.isfinite(value)
        and source["status"] in {"available", "matched", "mismatched"}
    )
    return {
        "status": "available" if available else "not_assessed",
        "source_status": source["status"],
        "reason": None if available else source.get("reason") or "unavailable_metric",
    }


def seed_differences(cells, *, final_verified=True):
    """Preserve per-seed inputs and signed differences; missing never means zero."""
    lookup = {}
    for cell in cells:
        key = (cell["budget"]["seed"], cell["condition"])
        if key in lookup:
            raise ValueError("Duplicate seed/condition cell.")
        lookup[key] = cell
    reports = []
    for seed in SEEDS:
        for condition in CONDITIONS[1:]:
            base, variant = (
                lookup.get((seed, "baseline")),
                lookup.get((seed, condition)),
            )
            first, second = _selected(base), _selected(variant)
            reason = (
                "final_verification_failed"
                if not final_verified
                else "incomplete_pair"
                if first is None or second is None
                else None
            )
            report = {
                "seed": seed,
                "condition": condition,
                "baseline_cell": base["number"] if base else None,
                "variant_cell": variant["number"] if variant else None,
                "baseline_markers": _markers(first),
                "variant_markers": _markers(second),
                "status": "not_assessed" if reason else "available",
                "reason": reason,
                "metrics": None,
            }
            if reason is None:
                report["metrics"] = {}
                for name, value in _metrics(first).items():
                    other = _metrics(second)[name]
                    first_status = _metric_availability(first, name, value)
                    second_status = _metric_availability(second, name, other)
                    available = (
                        first_status["status"] == second_status["status"] == "available"
                    )
                    delta = other - value if available else None
                    available = available and math.isfinite(delta)
                    report["metrics"][name] = {
                        "baseline": value,
                        "variant": other,
                        "baseline_availability": first_status,
                        "variant_availability": second_status,
                        "difference": delta if available else None,
                        "status": "available" if available else "not_assessed",
                        "reason": None
                        if available
                        else "unavailable_or_out_of_range_metric",
                    }
                report["cost"] = {
                    "baseline": {
                        key: base["diagnostics"].get(key)
                        for key in ("timing_seconds", "callback_calls_during_fit")
                    },
                    "variant": {
                        key: variant["diagnostics"].get(key)
                        for key in ("timing_seconds", "callback_calls_during_fit")
                    },
                }
            reports.append(report)
    return reports


def condition_summaries(cells, *, final_verified=True):
    summaries = {}
    for condition in CONDITIONS:
        group = [cell for cell in cells if cell["condition"] == condition]
        complete = (
            len(group) == 3
            and {cell["budget"]["seed"] for cell in group} == set(SEEDS)
            and all(cell["status"] == "completed" for cell in group)
        )
        summary = {
            "status": "not_assessed"
            if not final_verified
            else "complete"
            if complete
            else "incomplete",
            "statistics": None,
            "selected_diagnoses": None,
            "cell_states": dict(Counter(cell["status"] for cell in group)),
            "planned_count": 3,
        }
        if complete and final_verified:
            chosen = [_selected(cell) for cell in group]
            metrics = [_metrics(item) for item in chosen]
            summary["statistics"] = {}
            for name in metrics[0]:
                values = [
                    item[name]
                    for candidate, item in zip(chosen, metrics, strict=True)
                    if _metric_availability(candidate, name, item[name])["status"]
                    == "available"
                ]
                summary["statistics"][name] = {
                    "finite_count": len(values),
                    "planned_count": 3,
                    "minimum": min(values) if values else None,
                    "median": _finite_median(values) if values else None,
                    "maximum": max(values) if values else None,
                }
            summary["selected_diagnoses"] = {
                "structure": dict(
                    Counter(
                        item["search_analysis"]["structure"]["structure_status"]
                        for item in chosen
                    )
                ),
                "curve_marker": dict(Counter(item["curve_marker"] for item in chosen)),
                "parameter_match": dict(
                    Counter(item["parameter_match"]["status"] for item in chosen)
                ),
            }
        summaries[condition] = summary
    return summaries
