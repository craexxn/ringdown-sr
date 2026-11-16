"""Check five real weighting roles, shared-control accounting and fit-free replay."""

import copy
import json

import numpy as np
import pytest
from test_noise_pilot_reference import exhausted, fake_fit
from test_noise_pilot_reference import inputs as pilot_inputs

from ringdown_sr import noise_background_reference as reference
from ringdown_sr import noise_pilot_reference as pilot


def inputs():
    data = pilot_inputs()
    estimated = data.pop("covariance_estimated")
    for factor, arm in zip((1.0, 1.1, 1.2), reference.ESTIMATED_ARMS, strict=True):
        data["covariance_" + arm] = estimated * factor
    return data


@pytest.fixture
def example(monkeypatch):
    monkeypatch.setattr(reference, "fit_ringdown", fake_fit)
    data = inputs()
    return data, reference.fit_reference(data)


def test_exactly_five_private_fits_share_controls_once_and_preserve_all_original_arrays(
    monkeypatch,
):
    data = inputs()
    before = {key: value.copy() for key, value in data.items()}
    calls = []

    def fit(times, observed, *, covariance, **options):
        calls.append(None if covariance is None else covariance.copy())
        np.testing.assert_array_equal(times, before["time_s"])
        np.testing.assert_array_equal(observed, before["observed"])
        assert options == pilot.FIT_OPTIONS
        fitted = fake_fit(times, observed, covariance=covariance, **options)
        times[:] = -1
        observed[:] = -1
        if covariance is not None:
            covariance[:] = -1
        return fitted

    monkeypatch.setattr(reference, "fit_ringdown", fit)
    record = reference.fit_reference(data)
    assert len(calls) == 5
    assert calls[0] is None
    for actual, expected in zip(
        calls[1:],
        [
            before["covariance_true"],
            *(before["covariance_" + arm] for arm in reference.ESTIMATED_ARMS),
        ],
        strict=True,
    ):
        np.testing.assert_array_equal(actual, expected)
    for key, values in data.items():
        np.testing.assert_array_equal(values, before[key])
    assert list(record["arms"]) == list(reference.ARMS)
    assert record["format"] != pilot.FORMAT
    assert pilot.ARMS == ("ordinary", "known_covariance", "estimated_covariance")


def test_read_only_replay_never_calls_any_fit_and_preserves_canonical_predictions(
    example, monkeypatch
):
    data, record = example
    stored = json.loads(json.dumps(record, allow_nan=False))
    monkeypatch.setattr(
        reference, "fit_ringdown", lambda *a, **k: pytest.fail("Replay fitted")
    )
    monkeypatch.setattr(
        pilot, "fit_ringdown", lambda *a, **k: pytest.fail("Legacy replay fitted")
    )
    assert reference.verify_reference(stored, data) == stored
    for arm, result in stored["arms"].items():
        assert result["status"] == "success"
        assert result["fit"]["selected_start_index"] == 1
        np.testing.assert_array_equal(result["prediction"], data["signal"])
        assert (result["objective"]["q_used_per_sample"] is None) == (arm == "ordinary")


@pytest.mark.parametrize("missing", [("estimated_256",), reference.ESTIMATED_ARMS])
def test_missing_covariance_levels_only_disable_their_own_fits(monkeypatch, missing):
    data = inputs()
    for arm in missing:
        data.pop("covariance_" + arm)
    calls = []

    def fit(*args, **kwargs):
        calls.append(kwargs["covariance"])
        return fake_fit(*args, **kwargs)

    monkeypatch.setattr(reference, "fit_ringdown", fit)
    record = reference.fit_reference(data)
    assert len(calls) == 5 - len(missing)
    for arm in reference.ARMS:
        assert record["arms"][arm]["status"] == (
            "not_run" if arm in missing else "success"
        )
    assert reference.verify_reference(record, data) == record


@pytest.mark.parametrize(
    "error",
    [
        FloatingPointError("overflow"),
        np.linalg.LinAlgError("SVD did not converge"),
        exhausted(),
    ],
)
def test_one_numerical_fit_failure_keeps_four_remaining_arms_and_verifies(
    monkeypatch, error
):
    calls = 0

    def fit(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise error
        return fake_fit(*args, **kwargs)

    monkeypatch.setattr(reference, "fit_ringdown", fit)
    data = inputs()
    record = reference.fit_reference(data)
    assert calls == 5
    assert record["arms"]["estimated_64"]["status"] == "fit_failed"
    assert all(
        record["arms"][arm]["status"] == "success"
        for arm in reference.ARMS
        if arm != "estimated_64"
    )
    assert reference.verify_reference(record, data) == record


@pytest.mark.parametrize(
    "error",
    [
        ValueError("Unexpected actual equation_search invocation."),
        RuntimeError("Unknown failure"),
        KeyboardInterrupt(),
        SystemExit(1),
    ],
)
def test_integrity_and_interrupt_errors_propagate(monkeypatch, error):
    def failed(*args, **kwargs):
        raise error

    monkeypatch.setattr(reference, "fit_ringdown", failed)
    with pytest.raises(type(error)):
        reference.fit_reference(inputs())


@pytest.mark.parametrize("arm", reference.ARMS)
@pytest.mark.parametrize("change", ["prediction", "selection", "integrity_failure"])
def test_every_arm_is_bound_and_replayed(example, arm, change):
    data, record = example
    result = record["arms"][arm]
    if change == "prediction":
        result["prediction"][0] = 123
    elif change == "selection":
        result["fit"]["selected_start_index"] = 2
    else:
        record["arms"][arm] = {
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
    with pytest.raises(ValueError):
        reference.verify_reference(record, data)


@pytest.mark.parametrize(
    "change",
    ["matrix", "missing_arm", "format", "fit_options", "legacy_covariance", "noise"],
)
def test_source_format_inventory_and_option_changes_are_fatal(example, change):
    data, record = example
    if change == "matrix":
        data["covariance_estimated_1024"] *= 2
    elif change == "missing_arm":
        record["arms"].pop("estimated_256")
    elif change == "format":
        record["format"] = pilot.FORMAT
    elif change == "fit_options":
        record["fit_options"]["max_nfev"] = 2000
    elif change == "legacy_covariance":
        data["covariance_estimated"] = data["covariance_estimated_64"]
    else:
        data["noise"][0] += 1
    with pytest.raises(ValueError):
        reference.verify_reference(record, data)


def test_returned_records_and_sources_do_not_alias(example):
    data, record = example
    before = copy.deepcopy(record)
    replay = reference.verify_reference(record, data)
    replay["arms"]["ordinary"]["prediction"][0] += 1
    assert record == before
