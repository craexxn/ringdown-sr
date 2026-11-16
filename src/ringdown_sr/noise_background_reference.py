"""Run the five diagnostic fits once and reuse the strict existing read-only replay."""

import copy
from dataclasses import asdict

from . import noise_pilot_reference as pilot
from .assessment_sources import fingerprint, json_bytes
from .noise_background_assessment import ARMS

FORMAT = "ringdown-sr-noise-background-reference-1"
FIT_OPTIONS = copy.deepcopy(pilot.FIT_OPTIONS)
fit_ringdown = pilot.fit_ringdown
ESTIMATED_ARMS = ARMS[2:]


def _views(arrays):
    if "covariance_estimated" in arrays:
        raise ValueError(
            "The background study requires explicitly named covariance levels."
        )
    common = pilot._inputs(arrays)
    views = {}
    for arm in ESTIMATED_ARMS:
        name = "covariance_" + arm
        data = {
            **common,
            **({"covariance_estimated": arrays[name]} if name in arrays else {}),
        }
        views[arm] = pilot._inputs(data)
    data = dict(common)
    for arm, view in views.items():
        if "covariance_estimated" in view:
            data["covariance_" + arm] = view["covariance_estimated"]
    return data, views


def _header(data):
    return {
        "format": FORMAT,
        "method": "separable_known_ringdown",
        "scope": "diagnostic_only",
        "prediction_basis": "canonical_parameters",
        "fit_options": copy.deepcopy(FIT_OPTIONS),
        "input_fingerprints": {
            name: fingerprint(value) for name, value in data.items()
        },
    }


def _legacy_report(record, view, arm):
    return {
        **_header(view),
        "format": pilot.FORMAT,
        "arms": {
            "ordinary": record["arms"]["ordinary"],
            "known_covariance": record["arms"]["known_covariance"],
            "estimated_covariance": record["arms"][arm],
        },
    }


def fit_reference(arrays):
    """Fit each available weighting once; numerical failures retain every other arm."""
    data, views = _views(arrays)
    report = {**_header(data), "arms": {}}
    for arm in ARMS:
        estimated = arm in ESTIMATED_ARMS
        view = views[arm] if estimated else data
        legacy_arm = "estimated_covariance" if estimated else arm
        if estimated and "covariance_estimated" not in view:
            report["arms"][arm] = pilot._not_run()
            continue
        covariance = pilot._covariance(view, legacy_arm)
        try:
            fitted = fit_ringdown(
                view["time_s"].copy(),
                view["observed"].copy(),
                covariance=None if covariance is None else covariance.copy(),
                **copy.deepcopy(FIT_OPTIONS),
            )
            attempts = pilot._attempts([asdict(attempt) for attempt in fitted.attempts])
            parameters = {name: getattr(fitted, name) for name in pilot.PARAMETERS}
            prediction, objective = pilot._prediction(parameters, view, legacy_arm)
        except (pilot.ReferenceFitError, ValueError, *pilot.NUMERICAL_TYPES) as error:
            report["arms"][arm] = {
                "status": "fit_failed",
                "fit": None,
                "prediction": None,
                "objective": None,
                "error": pilot._failure(error),
            }
            continue
        report["arms"][arm] = {
            "status": "success",
            "fit": {
                "parameters": parameters,
                "selected_start_index": fitted.selected_start_index,
                "active_mask": list(fitted.active_mask),
                "nonlinear_jacobian_rank": fitted.nonlinear_jacobian_rank,
                "attempts": attempts,
            },
            "prediction": prediction,
            "objective": objective,
            "error": None,
        }
    return verify_reference(report, arrays)


def verify_reference(record, arrays):
    """Replay five fits without an optimizer; shared O/K evidence is never refitted."""
    data, views = _views(arrays)
    expected = _header(data)
    if (
        type(record) is not dict
        or set(record) != {*expected, "arms"}
        or json_bytes({key: record[key] for key in expected}) != json_bytes(expected)
        or type(record["arms"]) is not dict
        or set(record["arms"]) != set(ARMS)
    ):
        raise ValueError("Changed five-arm reference inputs, options or inventory.")
    for arm, view in views.items():
        pilot.verify_reference(_legacy_report(record, view, arm), view)
    return copy.deepcopy(record)
