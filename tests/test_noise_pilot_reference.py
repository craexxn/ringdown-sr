"""Bound the diagnostic reference route and its fit-free replay."""

import copy
import json
from dataclasses import replace

import numpy as np
import pytest

from ringdown_sr import noise_pilot_reference as reference
from ringdown_sr.losses import CovarianceLoss, mean_squared_error
from ringdown_sr.reference_fit import FitAttempt, ReferenceFit, ReferenceFitError
from ringdown_sr.signals import ringdown_signal


def inputs():
    times = np.arange(24, dtype=np.float64) / 4096
    signal = ringdown_signal(
        times, amplitude=1.25, frequency_hz=256.0, decay_time_s=0.008, phase_rad=0.1
    )
    noise = np.linspace(-0.01, 0.01, len(times))
    covariance = np.eye(len(times)) * 0.01
    covariance[0, 1] = covariance[1, 0] = 0.001
    return {
        "time_s": times,
        "signal": signal,
        "noise": noise,
        "observed": signal + noise,
        "covariance_true": covariance,
        "covariance_estimated": covariance * 1.2,
    }


def fake_fit(times, observed, *, covariance=None, **options):
    assert options == reference.FIT_OPTIONS
    parameters = {
        "amplitude": 1.25,
        "frequency_hz": 256.0,
        "decay_time_s": 0.008,
        "phase_rad": 0.1,
    }
    prediction = ringdown_signal(times, **parameters)
    residual = observed - prediction
    attempts = tuple(
        FitAttempt(*start, True, True, 1, 2, score, reference.SOLVER_MESSAGES[1])
        for start, score in zip(
            reference.FIT_OPTIONS["initial_points"], [0.02, 0.01, 0.01], strict=True
        )
    )
    return ReferenceFit(
        **parameters,
        prediction=prediction,
        residual=residual,
        ordinary_mse=mean_squared_error(residual),
        covariance_mean_squared=None
        if covariance is None
        else CovarianceLoss(covariance).mean_squared(residual),
        selected_start_index=1,
        active_mask=(0, 0),
        nonlinear_jacobian_rank=2,
        attempts=attempts,
    )


@pytest.fixture
def example(monkeypatch):
    monkeypatch.setattr(reference, "fit_ringdown", fake_fit)
    data = inputs()
    return data, reference.fit_reference(data)


def test_existing_options_match_general_pilot_config():
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "configs/pilot_confirmed_ar1.toml").read_text())
    expected = {
        key: value for key, value in config["fit"].items() if key != "weighting"
    }
    assert reference.FIT_OPTIONS == expected


def test_success_serializes_and_verifies_without_calling_fit(example, monkeypatch):
    data, report = example
    stored = json.loads(json.dumps(report, allow_nan=False))
    monkeypatch.setattr(
        reference, "fit_ringdown", lambda *args, **kwargs: pytest.fail("Replay fitted")
    )
    assert reference.verify_reference(stored, data) == stored
    assert list(stored["arms"]) == list(reference.ARMS)
    for arm, result in stored["arms"].items():
        assert result["status"] == "success"
        assert result["fit"]["selected_start_index"] == 1
        np.testing.assert_array_equal(result["prediction"], data["signal"])
        expected = mean_squared_error(data["noise"])
        assert result["objective"]["ordinary_mse"] == pytest.approx(expected)
        assert result["objective"]["mse_to_clean_signal"] == 0.0
        assert (result["objective"]["q_used_per_sample"] is None) == (arm == "ordinary")


def test_actual_small_known_form_fit_and_replay():
    # A separate bounded 24-point technical fixture, never a scientific case.
    data = inputs()
    record = reference.fit_reference(data)
    assert all(arm["status"] == "success" for arm in record["arms"].values())
    assert reference.verify_reference(record, data) == record


def test_each_arm_receives_private_equal_observations_and_correct_covariance(
    monkeypatch,
):
    data = inputs()
    before = {key: value.copy() for key, value in data.items()}
    calls = []

    def fitted(times, observed, *, covariance, **options):
        calls.append(None if covariance is None else covariance.copy())
        np.testing.assert_array_equal(times, data["time_s"])
        np.testing.assert_array_equal(observed, data["observed"])
        result = fake_fit(times, observed, covariance=covariance, **options)
        times[:] = -1
        observed[:] = -1
        if covariance is not None:
            covariance[:] = -1
        return result

    monkeypatch.setattr(reference, "fit_ringdown", fitted)
    reference.fit_reference(data)
    assert calls[0] is None
    np.testing.assert_array_equal(calls[1], before["covariance_true"])
    np.testing.assert_array_equal(calls[2], before["covariance_estimated"])
    for key in data:
        np.testing.assert_array_equal(data[key], before[key])


@pytest.mark.parametrize(
    "exception",
    [
        FloatingPointError("numerical overflow"),
        OverflowError("math range error"),
        np.linalg.LinAlgError("SVD did not converge"),
    ],
)
def test_numerical_failure_keeps_remaining_arms_and_verifies(monkeypatch, exception):
    calls = 0

    def fitted(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise exception
        return fake_fit(*args, **kwargs)

    monkeypatch.setattr(reference, "fit_ringdown", fitted)
    data = inputs()
    report = reference.fit_reference(data)
    assert calls == 3
    assert report["arms"]["ordinary"]["status"] == "fit_failed"
    assert report["arms"]["known_covariance"]["status"] == "success"
    assert report["arms"]["estimated_covariance"]["status"] == "success"
    monkeypatch.setattr(
        reference, "fit_ringdown", lambda *args, **kwargs: pytest.fail("Replay fitted")
    )
    reference.verify_reference(report, data)


def exhausted(message=None):
    return ReferenceFitError(
        tuple(
            FitAttempt(
                *start,
                False,
                False,
                0,
                1000,
                0.2,
                message or reference.SOLVER_MESSAGES[0],
            )
            for start in reference.FIT_OPTIONS["initial_points"]
        )
    )


def test_exhausted_multistart_is_a_valid_diagnostic_failure(monkeypatch):
    def failed(*args, **kwargs):
        raise exhausted()

    monkeypatch.setattr(reference, "fit_ringdown", failed)
    data = inputs()
    record = reference.fit_reference(data)
    assert all(arm["status"] == "fit_failed" for arm in record["arms"].values())
    reference.verify_reference(record, data)


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("Unexpected actual equation_search invocation."),
        RuntimeError("Unknown failure"),
        KeyboardInterrupt(),
        SystemExit(1),
        exhausted("Unexpected actual equation_search invocation."),
    ],
)
def test_unknown_integrity_and_interrupt_failures_propagate(monkeypatch, exception):
    def failed(*args, **kwargs):
        raise exception

    monkeypatch.setattr(reference, "fit_ringdown", failed)
    with pytest.raises(
        type(exception) if not isinstance(exception, ReferenceFitError) else ValueError
    ):
        reference.fit_reference(inputs())


def test_unknown_swallowed_attempt_is_rejected_even_when_another_start_succeeded(
    monkeypatch,
):
    def fitted(*args, **kwargs):
        result = fake_fit(*args, **kwargs)
        bad = replace(result.attempts[0], usable=False, message="Unexpected invocation")
        return replace(result, attempts=(bad, *result.attempts[1:]))

    monkeypatch.setattr(reference, "fit_ringdown", fitted)
    with pytest.raises(ValueError, match="integrity"):
        reference.fit_reference(inputs())


def test_missing_estimated_covariance_is_explicit_not_run(monkeypatch):
    monkeypatch.setattr(reference, "fit_ringdown", fake_fit)
    data = inputs()
    del data["covariance_estimated"]
    report = reference.fit_reference(data)
    assert [arm["status"] for arm in report["arms"].values()] == [
        "success",
        "success",
        "not_run",
    ]
    reference.verify_reference(report, data)
    report["arms"]["estimated_covariance"]["status"] = "fit_failed"
    with pytest.raises(ValueError, match="not-run"):
        reference.verify_reference(report, data)


@pytest.mark.parametrize(
    "change",
    [
        lambda report: report["arms"]["ordinary"]["prediction"].__setitem__(0, 123.0),
        lambda report: report["arms"]["ordinary"]["objective"].__setitem__(
            "ordinary_mse", 123.0
        ),
        lambda report: report["arms"]["ordinary"]["fit"]["parameters"].__setitem__(
            "frequency_hz", 300.0
        ),
        lambda report: report["arms"]["ordinary"]["fit"].__setitem__(
            "selected_start_index", 2
        ),
        lambda report: report["arms"]["ordinary"]["fit"].__setitem__(
            "selected_start_index", True
        ),
        lambda report: report["arms"]["ordinary"].__setitem__("status", "not_run"),
        lambda report: report["arms"].pop("ordinary"),
        lambda report: report["fit_options"].__setitem__("max_nfev", 2000),
        lambda report: report.__setitem__("scope", "selection"),
    ],
)
def test_changed_reference_evidence_is_rejected(example, change):
    data, report = example
    change(report)
    with pytest.raises(ValueError):
        reference.verify_reference(report, data)


def test_changed_shared_inputs_and_unknown_failure_record_are_rejected(example):
    data, report = example
    changed = copy.deepcopy(data)
    changed["covariance_true"] *= 2
    with pytest.raises(ValueError, match="inputs"):
        reference.verify_reference(report, changed)
    report["arms"]["ordinary"] = {
        "status": "fit_failed",
        "fit": None,
        "prediction": None,
        "objective": None,
        "error": {
            "type": "ValueError",
            "message": "Unexpected actual equation_search invocation.",
            "attempts": [],
        },
    }
    with pytest.raises(ValueError, match="integrity"):
        reference.verify_reference(report, data)


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data["observed"].__setitem__(0, 99.0),
        lambda data: data["time_s"].__setitem__(1, 0.5),
        lambda data: data.__setitem__("observed", data["observed"].astype(np.float32)),
        lambda data: data["covariance_true"].__setitem__((0, 0), -1.0),
    ],
)
def test_invalid_prepared_inputs_are_fatal_before_fitting(monkeypatch, change):
    data = inputs()
    change(data)
    monkeypatch.setattr(
        reference,
        "fit_ringdown",
        lambda *args, **kwargs: pytest.fail("Invalid input fitted"),
    )
    with pytest.raises(ValueError):
        reference.fit_reference(data)
