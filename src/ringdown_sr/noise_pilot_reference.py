"""Diagnose prepared noise-pilot inputs with the existing known-form fits."""

import copy
import math
from dataclasses import asdict

import numpy as np

from .assessment_sources import fingerprint, json_bytes
from .losses import CovarianceLoss, mean_squared_error
from .reference_fit import ReferenceFitError, fit_ringdown
from .signals import ringdown_signal

FORMAT = "ringdown-sr-noise-pilot-reference-1"
ARMS = ("ordinary", "known_covariance", "estimated_covariance")
# Preserve the existing general pilot's explicit reference-fit configuration.
FIT_OPTIONS = {
    "frequency_bounds_hz": [100.0, 500.0],
    "decay_time_bounds_s": [0.002, 0.03],
    "initial_points": [[150.0, 0.004], [300.0, 0.015], [450.0, 0.004]],
    "max_nfev": 1000,
}
PARAMETERS = ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
NUMERICAL_TYPES = (
    FloatingPointError,
    OverflowError,
    ZeroDivisionError,
    np.linalg.LinAlgError,
)
NUMERICAL_MESSAGES = {
    "observed must be nonzero; a zero signal has no identifiable f or tau.",
    "Whitened data underflowed the float64 range.",
    "The weighted basis exceeds the float64 range.",
    "The sampled sine/cosine basis is numerically rank deficient.",
    "The fitted amplitude exceeds the float64 range.",
    "The loss exceeds the finite float64 range.",
    "The whitened residual exceeds the finite float64 range.",
    "Signal parameters exceed the numerical range.",
    "residual must contain finite real numbers.",
    "SVD did not converge in Linear Least Squares",
    "SVD did not converge",
    "math range error",
    "array must not contain infs or NaNs",
}
SOLVER_MESSAGES = {
    0: "The maximum number of function evaluations is exceeded.",
    1: "`gtol` termination condition is satisfied.",
    2: "`ftol` termination condition is satisfied.",
    3: "`xtol` termination condition is satisfied.",
    4: "Both `ftol` and `xtol` termination conditions are satisfied.",
}


def _numeric_message(message):
    return type(message) is str and (
        message in NUMERICAL_MESSAGES
        or message.startswith(
            (
                "overflow encountered in ",
                "invalid value encountered in ",
                "divide by zero encountered in ",
                "underflow encountered in ",
            )
        )
    )


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _inputs(arrays):
    names = ("time_s", "signal", "noise", "observed", "covariance_true")
    if not all(name in arrays for name in names):
        raise ValueError("Missing prepared reference inputs.")
    names += ("covariance_estimated",) if "covariance_estimated" in arrays else ()
    data = {}
    for name in names:
        value = np.asarray(arrays[name])
        if value.dtype != np.dtype("float64") or not np.isfinite(value).all():
            raise ValueError("Reference inputs must retain finite Float64 values.")
        data[name] = value.copy()
    times = data["time_s"]
    if (
        times.ndim != 1
        or times.size < 5
        or times[0] != 0
        or np.any(np.diff(times) <= 0)
        or not np.allclose(
            times,
            np.arange(times.size) * times[1],
            rtol=64 * np.finfo(float).eps,
            atol=0,
        )
        or FIT_OPTIONS["frequency_bounds_hz"][1] * times[1] >= 0.5
        or any(
            data[name].shape != times.shape for name in ("signal", "noise", "observed")
        )
    ):
        raise ValueError("Invalid prepared reference sampling or observations.")
    with np.errstate(over="raise", invalid="raise"):
        if not np.array_equal(data["observed"], data["signal"] + data["noise"]):
            raise ValueError("Prepared observations differ from signal plus noise.")
    for name in names:
        if name.startswith("covariance_"):
            if data[name].shape != (times.size, times.size):
                raise ValueError("Reference covariance has the wrong shape.")
            CovarianceLoss(data[name])
        data[name].setflags(write=False)
    return data


def _attempts(records):
    if type(records) is not list or len(records) != len(FIT_OPTIONS["initial_points"]):
        raise ValueError("Incomplete reference-fit start inventory.")
    fields = {
        "initial_frequency_hz",
        "initial_decay_time_s",
        "converged",
        "usable",
        "status",
        "nfev",
        "scaled_mse",
        "message",
    }
    for record, start in zip(records, FIT_OPTIONS["initial_points"], strict=True):
        if (
            type(record) is not dict
            or set(record) != fields
            or json_bytes(
                [record["initial_frequency_hz"], record["initial_decay_time_s"]]
            )
            != json_bytes(start)
            or type(record["converged"]) is not bool
            or type(record["usable"]) is not bool
            or (
                record["status"] is not None
                and (
                    type(record["status"]) is not int
                    or record["status"] not in SOLVER_MESSAGES
                )
            )
            or (
                record["nfev"] is not None
                and (
                    type(record["nfev"]) is not int
                    or not 0 < record["nfev"] <= FIT_OPTIONS["max_nfev"]
                )
            )
            or (
                record["scaled_mse"] is not None
                and (not _finite(record["scaled_mse"]) or record["scaled_mse"] < 0)
            )
        ):
            raise ValueError("Invalid reference-fit attempt diagnostics.")
        status = record["status"]
        if record["converged"] != (status in (1, 2, 3, 4)) or (status is None) != (
            record["nfev"] is None
        ):
            raise ValueError("Contradictory reference-fit termination evidence.")
        if record["usable"]:
            if (
                not record["converged"]
                or record["scaled_mse"] is None
                or record["message"] != SOLVER_MESSAGES[status]
            ):
                raise ValueError("Invalid usable reference-fit attempt.")
        elif not (
            _numeric_message(record["message"])
            or (status == 0 and record["message"] == SOLVER_MESSAGES[0])
        ):
            raise ValueError("Unknown or integrity failure in reference-fit attempts.")
    return records


def _failure(error):
    if type(error) is ReferenceFitError:
        attempts = _attempts([asdict(attempt) for attempt in error.attempts])
        if any(attempt["usable"] for attempt in attempts):
            raise ValueError("Failed reference fit contains a usable attempt.")
    elif type(error) in NUMERICAL_TYPES or (
        type(error) is ValueError and _numeric_message(str(error))
    ):
        attempts = []
    else:
        raise error
    return {"type": type(error).__name__, "message": str(error), "attempts": attempts}


def _covariance(data, arm):
    return (
        None
        if arm == "ordinary"
        else data[
            "covariance_true" if arm == "known_covariance" else "covariance_estimated"
        ]
    )


def _prediction(parameters, data, arm):
    if (
        type(parameters) is not dict
        or set(parameters) != set(PARAMETERS)
        or not all(_finite(value) for value in parameters.values())
        or parameters["amplitude"] < 0
        or not FIT_OPTIONS["frequency_bounds_hz"][0]
        <= parameters["frequency_hz"]
        <= FIT_OPTIONS["frequency_bounds_hz"][1]
        or not FIT_OPTIONS["decay_time_bounds_s"][0]
        <= parameters["decay_time_s"]
        <= FIT_OPTIONS["decay_time_bounds_s"][1]
        or not -math.pi <= parameters["phase_rad"] < math.pi
    ):
        raise ValueError("Invalid canonical reference-fit parameters.")
    prediction = ringdown_signal(data["time_s"], **parameters)
    with np.errstate(over="raise", invalid="raise"):
        residual = data["observed"] - prediction
        clean_residual = prediction - data["signal"]
    covariance = _covariance(data, arm)
    objective = {
        "ordinary_mse": mean_squared_error(residual),
        "q_used_per_sample": None
        if covariance is None
        else CovarianceLoss(covariance).mean_squared(residual),
        "mse_to_clean_signal": mean_squared_error(clean_residual),
        "q_true_per_sample": CovarianceLoss(data["covariance_true"]).mean_squared(
            residual
        ),
    }
    return prediction.tolist(), objective


def _not_run():
    return {
        "status": "not_run",
        "fit": None,
        "prediction": None,
        "objective": None,
        "error": {
            "type": "CovarianceUnavailable",
            "message": "The prepared estimated covariance is unavailable.",
            "attempts": [],
        },
    }


def fit_reference(arrays):
    """Fit each available weighting arm; numerical diagnostic failures stay local."""
    data = _inputs(arrays)
    report = {
        "format": FORMAT,
        "method": "separable_known_ringdown",
        "scope": "diagnostic_only",
        # Canonical conversion rounds phase and amplitude; replay that declared
        # curve explicitly instead of inventing a tolerance to the solver basis.
        "prediction_basis": "canonical_parameters",
        "fit_options": copy.deepcopy(FIT_OPTIONS),
        "input_fingerprints": {
            name: fingerprint(value) for name, value in data.items()
        },
        "arms": {},
    }
    for arm in ARMS:
        if arm == "estimated_covariance" and "covariance_estimated" not in data:
            report["arms"][arm] = _not_run()
            continue
        covariance = _covariance(data, arm)
        try:
            fitted = fit_ringdown(
                data["time_s"].copy(),
                data["observed"].copy(),
                covariance=None if covariance is None else covariance.copy(),
                **copy.deepcopy(FIT_OPTIONS),
            )
            attempts = _attempts([asdict(attempt) for attempt in fitted.attempts])
            parameters = {name: getattr(fitted, name) for name in PARAMETERS}
            prediction, objective = _prediction(parameters, data, arm)
        except (ReferenceFitError, ValueError, *NUMERICAL_TYPES) as error:
            report["arms"][arm] = {
                "status": "fit_failed",
                "fit": None,
                "prediction": None,
                "objective": None,
                "error": _failure(error),
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
    """Recompute declared predictions and objectives; never call an optimizer."""
    data = _inputs(arrays)
    expected = {
        "format": FORMAT,
        "method": "separable_known_ringdown",
        "scope": "diagnostic_only",
        "prediction_basis": "canonical_parameters",
        "fit_options": FIT_OPTIONS,
        "input_fingerprints": {
            name: fingerprint(value) for name, value in data.items()
        },
    }
    if (
        type(record) is not dict
        or set(record) != {*expected, "arms"}
        or json_bytes({key: record[key] for key in expected}) != json_bytes(expected)
    ):
        raise ValueError("Changed reference-fit inputs, options or format.")
    if type(record["arms"]) is not dict or set(record["arms"]) != set(ARMS):
        raise ValueError("Incomplete reference-fit arm inventory.")
    for arm, result in record["arms"].items():
        if type(result) is not dict or set(result) != {
            "status",
            "fit",
            "prediction",
            "objective",
            "error",
        }:
            raise ValueError("Invalid reference-fit result fields.")
        if arm == "estimated_covariance" and "covariance_estimated" not in data:
            if json_bytes(result) != json_bytes(_not_run()):
                raise ValueError(
                    "Unavailable covariance must retain its not-run reference."
                )
            continue
        if result["status"] == "fit_failed":
            error = result["error"]
            if (
                any(
                    result[key] is not None
                    for key in ("fit", "prediction", "objective")
                )
                or type(error) is not dict
                or set(error) != {"type", "message", "attempts"}
                or type(error["message"]) is not str
            ):
                raise ValueError("Invalid failed reference-fit evidence.")
            if error["type"] == "ReferenceFitError":
                attempts = _attempts(error["attempts"])
                if any(attempt["usable"] for attempt in attempts) or error[
                    "message"
                ] != str(ReferenceFitError(())):
                    raise ValueError("Contradictory exhausted reference fit.")
            elif error["attempts"] != [] or not (
                error["type"] in {kind.__name__ for kind in NUMERICAL_TYPES}
                or (
                    error["type"] == "ValueError" and _numeric_message(error["message"])
                )
            ):
                raise ValueError(
                    "Unknown or integrity failure cannot be a diagnostic fit failure."
                )
            continue
        if result["status"] != "success" or result["error"] is not None:
            raise ValueError("Unexpected reference-fit status.")
        fitted = result["fit"]
        if type(fitted) is not dict or set(fitted) != {
            "parameters",
            "selected_start_index",
            "active_mask",
            "nonlinear_jacobian_rank",
            "attempts",
        }:
            raise ValueError("Invalid successful reference-fit fields.")
        attempts = _attempts(fitted["attempts"])
        usable = [index for index, attempt in enumerate(attempts) if attempt["usable"]]
        selected = fitted["selected_start_index"]
        if (
            not usable
            or type(selected) is not int
            or selected != min(usable, key=lambda index: attempts[index]["scaled_mse"])
            or type(fitted["active_mask"]) is not list
            or len(fitted["active_mask"]) != 2
            or any(
                type(value) is not int or value not in (-1, 0, 1)
                for value in fitted["active_mask"]
            )
            or type(fitted["nonlinear_jacobian_rank"]) is not int
            or not 0 <= fitted["nonlinear_jacobian_rank"] <= 2
        ):
            raise ValueError("Changed reference-fit selection or convergence evidence.")
        prediction, objective = _prediction(fitted["parameters"], data, arm)
        if json_bytes(result["prediction"]) != json_bytes(prediction) or json_bytes(
            result["objective"]
        ) != json_bytes(objective):
            raise ValueError("Changed canonical reference-fit prediction or objective.")
    return copy.deepcopy(record)
