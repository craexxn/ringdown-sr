"""Post-selection parameter diagnostics and numerical replay, without fitting."""

import math
from fractions import Fraction
from numbers import Real

import numpy as np

from .aliasing import Phase, angular_frequency_fields, rational_field, reduce_alias
from .losses import _real_array
from .signals import sample_times
from .structure import recognize_ringdown
from .symbolic import _check_prediction_replay, evaluate_tree


def _not_attempted(reason):
    return {"status": "not_attempted", "reason": reason}


def _prediction_replay(original, prediction):
    if not np.all(np.isfinite(prediction)):
        return {"status": "failed", "reason": "nonfinite_replay_prediction"}
    scale = max(float(np.max(np.abs(original))), float(np.max(np.abs(prediction))))
    difference = (
        0.0
        if scale == 0
        else float(np.max(np.abs(original / scale - prediction / scale)))
    )
    diagnostics = {
        "amplitude_scale": scale,
        "max_normalized_difference": difference,
        "rtol": 1e-12,
        "normalized_atol": 1e-14,
        "scale_definition": "max_abs_of_both_predictions_no_floor",
    }
    try:
        # The original tree is the reference (second argument) for relative error.
        _check_prediction_replay(prediction, original)
    except AssertionError:
        return {"status": "failed", "reason": "prediction_mismatch", **diagnostics}
    return {"status": "passed", "reason": None, **diagnostics}


def analyze_tree(tree: dict, time_s, *, sample_rate_hz: float) -> dict:
    """Analyze one tree and replay its raw and, when available, aliased forms.

    Inputs are read-only. No truth, losses, fits, other candidates or random
    states are accepted. Per-field availability certifies numerical conversion;
    the separate replays determine agreement with the original Float64 tree.
    """
    structure = recognize_ringdown(tree)
    times = _real_array(time_s, "time_s").copy()
    if times.ndim != 1 or times.size == 0:
        raise ValueError("time_s must be a nonempty vector.")
    if isinstance(sample_rate_hz, (bool, np.bool_)) or not isinstance(
        sample_rate_hz, Real
    ):
        raise TypeError("sample_rate_hz must be a real scalar, excluding booleans.")
    try:
        fs = float(sample_rate_hz)
    except OverflowError as error:
        raise ValueError("sample_rate_hz exceeds Float64 range.") from error
    if not math.isfinite(fs) or fs <= 0:
        raise ValueError("sample_rate_hz must be a finite positive scalar.")
    report = {
        "format": "ringdown-sr-parameter-analysis-1",
        "structure": structure.to_dict(),
        "parameter_interpretation": "diagnostics_only",
        "raw_parameters": None,
        "raw_replay": _not_attempted("unsupported_structure"),
        "alias": _not_attempted("unsupported_structure"),
        "alias_replay": _not_attempted("unsupported_structure"),
        "identifiability": {
            "physical_identification": "not_assessed",
            "zero_amplitude": None,
            "amplitude_phase_degeneracy": "not_assessed",
        },
    }
    raw = structure.coefficients
    if raw is None:
        return report
    parameters = {
        "amplitude": rational_field(raw.amplitude),
        "exponential_rate_per_s": rational_field(raw.exponential_rate_per_s),
        "angular_frequency_per_s": rational_field(raw.angular_frequency_per_s),
        "phase_rad": rational_field(raw.phase_rad),
    }
    parameters["decay_time_s"] = (
        rational_field(-1 / raw.exponential_rate_per_s)
        if raw.exponential_rate_per_s < 0
        else {
            "value": None,
            "status": "not_applicable",
            "reason": "undamped" if raw.exponential_rate_per_s == 0 else "growing",
        }
    )
    frequencies = angular_frequency_fields(raw.angular_frequency_per_s)
    parameters["frequency_raw_signed_hz"] = frequencies["signed"]
    parameters["frequency_raw_hz"] = frequencies["absolute"]
    report["raw_frequency_pi_terms"] = frequencies["pi_terms"]
    report["raw_parameters"] = parameters
    report["identifiability"]["zero_amplitude"] = raw.amplitude == 0
    try:
        grid_matches = np.array_equal(times, sample_times(times.size, fs))
    except ValueError:
        grid_matches = False
    if grid_matches:
        alias = reduce_alias(
            sample_rate_hz=Fraction.from_float(fs),
            angular_frequency_per_s=raw.angular_frequency_per_s,
            phase=Phase("radian_rational", raw.phase_rad),
        )
        report["alias"] = alias
        report["identifiability"]["amplitude_phase_degeneracy"] = alias["degeneracy"]
    else:
        report["alias"] = _not_attempted("time_axis_not_zero_origin_uniform")
    report["alias_replay"] = _not_attempted("alias_unavailable")
    try:
        original = evaluate_tree(tree, times)
    except ValueError:
        report["raw_replay"] = {
            "status": "failed",
            "reason": "nonfinite_original_prediction",
        }
        if report["alias"]["status"] == "available":
            report["alias_replay"] = {
                "status": "failed",
                "reason": "nonfinite_original_prediction",
            }
        return report
    coefficients_available = all(
        parameters[key]["status"] == "available"
        for key in (
            "amplitude",
            "exponential_rate_per_s",
            "angular_frequency_per_s",
            "phase_rad",
        )
    )
    if coefficients_available:
        amplitude, rate, frequency, phase = [
            parameters[key]["value"]
            for key in (
                "amplitude",
                "exponential_rate_per_s",
                "angular_frequency_per_s",
                "phase_rad",
            )
        ]
        with np.errstate(all="ignore"):
            prediction = (
                amplitude * np.exp(rate * times) * np.cos(frequency * times + phase)
            )
        report["raw_replay"] = _prediction_replay(original, prediction)
    else:
        report["raw_replay"] = _not_attempted("unavailable_raw_coefficient")
    alias = report["alias"]
    if alias["status"] != "available":
        report["alias_replay"] = _not_attempted("alias_unavailable")
    elif not coefficients_available:
        report["alias_replay"] = _not_attempted("unavailable_raw_coefficient")
    else:
        with np.errstate(all="ignore"):
            prediction = (
                amplitude
                * np.exp(rate * times)
                * np.cos(
                    2 * np.pi * alias["frequency_alias_hz"]["value"] * times
                    + alias["phase_alias_rad"]["value"]
                )
            )
        report["alias_replay"] = _prediction_replay(original, prediction)
    return report
