"""Frozen development-control data and post-selection diagnostics, without search."""

import math
from collections import Counter
from dataclasses import asdict
from statistics import median

import numpy as np

from .config import SearchBudget
from .parameters import analyze_tree
from .pilot import _json_bytes, _sha256
from .signals import ringdown_signal, sample_times
from .symbolic import evaluate_tree

FORMAT = "ringdown-sr-noiseless-control-1"
PLAN_COMMIT = "a78155cefe52ec39b31794be37044dc418a0a8fd"
PLAN_SHA256 = "be41e704066c4b7c281ee92acb37960bea1f24b0f528aec9adabc4e87672b4dd"
FS = 4096.0
TRUTH = {
    "amplitude": 1.0,
    "frequency_hz": 250.0,
    "decay_time_s": 0.008,
    "phase_rad": 0.0,
}
CURVE_LIMITS = {"relative_rms": 1e-3, "relative_max": 1e-2}
PARAMETER_LIMITS = {
    "frequency": 1e-3,
    "decay_time": 1e-2,
    "amplitude": 1e-2,
    "complex_amplitude": 1e-2,
}


def planned_cells():
    """Return fresh records for the nine reviewed cells, in fixed cyclic order."""
    cells = []
    budgets = (10, 50, 200)
    for block, seed in enumerate((20261020, 20261021, 20261022)):
        for offset in range(3):
            budget = SearchBudget(seed=seed, niterations=budgets[(block + offset) % 3])
            cells.append(
                {
                    "number": len(cells) + 1,
                    "directory": f"cell-{len(cells) + 1:02d}",
                    "budget": asdict(budget),
                    "status": "planned",
                }
            )
    return cells


def frozen_data():
    """Generate each reference vector once; no random source or covariance exists."""
    time = sample_times(128, FS)
    dense = ((np.arange(127)[:, None] + np.arange(1, 8)[None, :] / 8) / FS).ravel()
    arrays = {
        "time_s": time,
        "observed": ringdown_signal(time, **TRUTH),
        "diagnostic_time_s": dense,
        "diagnostic_truth": ringdown_signal(dense, **TRUTH),
    }
    for array in arrays.values():
        array.flags.writeable = False
    return arrays


def fingerprint(values):
    """Identify shape and canonical little-endian Float64 bits."""
    values = np.ascontiguousarray(values, dtype="<f8")
    return {
        "shape": list(values.shape),
        "dtype": "<f8",
        "sha256": _sha256(values.tobytes()),
    }


def curve_errors(prediction, truth):
    """Normalize by truth only, using shared scaling to avoid raw overflow."""
    truth = np.asarray(truth, dtype=np.float64)
    prediction = np.asarray(prediction, dtype=np.float64)
    if truth.ndim != 1 or not truth.size or prediction.shape != truth.shape:
        raise ValueError("Curve errors need equal nonempty vectors.")
    if not np.all(np.isfinite(truth)) or not np.any(truth):
        raise ValueError("Truth must be finite and have nonzero norm.")
    result = {
        "status": "available",
        "reason": None,
        "relative_rms": None,
        "relative_max": None,
    }
    if not np.all(np.isfinite(prediction)):
        return {**result, "status": "not_available", "reason": "nonfinite_prediction"}
    scale = max(float(np.max(np.abs(truth))), float(np.max(np.abs(prediction))))
    with np.errstate(all="ignore"):
        reference = truth / scale
        difference = prediction / scale - reference
    denominator = math.hypot(*reference)
    maximum = float(np.max(np.abs(reference)))
    if denominator == 0 or maximum == 0:
        return {
            **result,
            "status": "numerical_unresolved",
            "reason": "scaled_truth_underflow",
        }
    for name, numerator, divisor in (
        ("relative_rms", math.hypot(*difference), denominator),
        ("relative_max", float(np.max(np.abs(difference))), maximum),
    ):
        value = numerator / divisor
        if math.isfinite(value):
            result[name] = value
        else:
            result.update(
                status="numerical_unresolved", reason="relative_error_out_of_range"
            )
    return result


def parameter_match(analysis):
    """Compare available alias-class fields, preserving signed amplitude and phase."""
    result = {
        "status": "not_assessed",
        "reason": None,
        "errors": dict.fromkeys(PARAMETER_LIMITS),
        "physical_identification": "not_assessed",
    }
    structure = analysis["structure"]
    gates = (
        (structure["structure_status"] == "recognized", "unsupported_structure"),
        (structure["exponential_status"] == "decaying", "not_decaying"),
        (structure["amplitude_status"] == "nonzero", "zero_amplitude"),
        (analysis["raw_replay"]["status"] == "passed", "raw_replay_not_passed"),
        (analysis["alias"]["status"] == "available", "alias_unavailable"),
        (analysis["alias"].get("degeneracy") == "none", "degenerate_alias"),
        (analysis["alias_replay"]["status"] == "passed", "alias_replay_not_passed"),
    )
    for passed, reason in gates:
        if not passed:
            return {**result, "reason": reason}
    raw, alias = analysis["raw_parameters"], analysis["alias"]
    fields = (
        raw["amplitude"],
        raw["decay_time_s"],
        alias["frequency_alias_hz"],
        alias["phase_alias_rad"],
    )
    if any(
        field["status"] != "available" or not math.isfinite(field["value"])
        for field in fields
    ):
        return {**result, "reason": "unavailable_parameter_field"}
    amplitude, decay, frequency, phase = [field["value"] for field in fields]
    # A0=1 and phi0=0 are frozen by this control; do not rewrite the source fields.
    errors = {
        "frequency": abs(frequency - TRUTH["frequency_hz"]) / TRUTH["frequency_hz"],
        "decay_time": abs(decay - TRUTH["decay_time_s"]) / TRUTH["decay_time_s"],
        "amplitude": abs(abs(amplitude) - 1),
        "complex_amplitude": math.hypot(
            amplitude * math.cos(phase) - 1, amplitude * math.sin(phase)
        ),
    }
    result["errors"] = {
        key: value if math.isfinite(value) else None for key, value in errors.items()
    }
    if any(value is None for value in result["errors"].values()):
        return {**result, "reason": "parameter_error_out_of_range"}
    result["status"] = (
        "matched"
        if all(errors[key] <= bound for key, bound in PARAMETER_LIMITS.items())
        else "mismatched"
    )
    return result


def diagnose_candidate(candidate, index, selected_index, arrays):
    """Evaluate the full original tree on both grids, after selection is frozen."""
    analysis = analyze_tree(candidate["tree"], arrays["time_s"], sample_rate_hz=FS)
    curves = {}
    for name, times, truth in (
        ("training", "time_s", "observed"),
        ("diagnostic", "diagnostic_time_s", "diagnostic_truth"),
    ):
        try:
            prediction = evaluate_tree(candidate["tree"], arrays[times])
        except ValueError:
            curves[name] = {
                "status": "not_available",
                "reason": "nonfinite_original_tree",
                "relative_rms": None,
                "relative_max": None,
            }
        else:
            curves[name] = curve_errors(prediction, arrays[truth])
    marker = "not_assessed"
    if all(curve["status"] == "available" for curve in curves.values()):
        marker = (
            "within_tolerance"
            if all(
                curve[key] <= limit
                for curve in curves.values()
                for key, limit in CURVE_LIMITS.items()
            )
            else "outside_tolerance"
        )
    return {
        "source_index": index,
        "is_selected": index == selected_index,
        "source_candidate_sha256": _sha256(_json_bytes(candidate)),
        "complexity": candidate["complexity"],
        "training_loss": candidate["loss"],
        "display_equation": candidate["display_equation"],
        "curve_errors": curves,
        "curve_marker": marker,
        "analysis": analysis,
        "parameter_match": parameter_match(analysis),
        "physical_identification": "not_assessed",
    }


def budget_summaries(cells):
    """Describe complete three-start groups only; retain finite-value denominators."""
    summaries = {}
    for iterations in (10, 50, 200):
        group = [cell for cell in cells if cell["budget"]["niterations"] == iterations]
        states = Counter(cell["status"] for cell in group)
        complete = len(group) == 3 and states["completed"] == 3
        summary = {
            "status": "complete" if complete else "incomplete",
            "planned_count": 3,
            "cell_states": dict(states),
            "statistics": None,
            "selected_diagnoses": None,
        }
        if complete:
            chosen = [
                cell["diagnostics"]["candidates"][cell["diagnostics"]["selected_index"]]
                for cell in group
            ]
            statistics = {}
            for grid in ("training", "diagnostic"):
                statistics[grid] = {}
                for metric in CURVE_LIMITS:
                    values = [
                        item["curve_errors"][grid][metric]
                        for item in chosen
                        if item["curve_errors"][grid][metric] is not None
                    ]
                    statistics[grid][metric] = {
                        "finite_count": len(values),
                        "planned_count": 3,
                        "minimum": min(values) if values else None,
                        "median": median(values) if values else None,
                        "maximum": max(values) if values else None,
                    }
            summary.update(
                statistics=statistics,
                selected_diagnoses={
                    "structure": dict(
                        Counter(
                            item["analysis"]["structure"]["structure_status"]
                            for item in chosen
                        )
                    ),
                    "curve_marker": dict(
                        Counter(item["curve_marker"] for item in chosen)
                    ),
                    "parameter_match": dict(
                        Counter(item["parameter_match"]["status"] for item in chosen)
                    ),
                },
            )
        summaries[str(iterations)] = summary
    return summaries
