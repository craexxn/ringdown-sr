"""Check the known-form fit against analytic signals and weighted normal equations."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.reference_fit import ReferenceFitError, fit_ringdown
from ringdown_sr.signals import ringdown_signal, sample_times


def hand_data():
    # cos(pi*k/2) + sin(pi*k/2) = 1, 1, -1, -1, ...; decay is 2**(-k).
    indices = np.arange(20)
    return indices / 1024, np.ldexp(np.resize([1.0, 1.0, -1.0, -1.0], 20), -indices)


def hand_fit(time, observed, **overrides):
    options = {
        "frequency_bounds_hz": (180.0, 350.0),
        "decay_time_bounds_s": (0.0005, 0.006),
        "initial_points": [(210.0, 0.0009), (320.0, 0.003)],
    }
    options.update(overrides)
    return fit_ringdown(time, observed, **options)


@pytest.mark.parametrize("scale", [1.0, -2.0, 1e-21, 1e21])
def test_recovers_hand_calculated_signal_without_true_start_parameters(scale):
    time, values = hand_data()
    result = hand_fit(time, values * scale)
    expected_phase = -math.pi / 4 if scale > 0 else 3 * math.pi / 4
    assert_allclose(result.frequency_hz, 256.0, rtol=1e-6, atol=0)
    assert_allclose(result.decay_time_s, 1 / (1024 * math.log(2)), rtol=1e-6, atol=0)
    assert_allclose(result.amplitude, math.sqrt(2) * abs(scale), rtol=1e-6, atol=0)
    assert_allclose(result.phase_rad, expected_phase, rtol=0, atol=1e-6)
    assert_allclose(result.prediction / scale, values, rtol=1e-6, atol=0)
    assert result.attempts[result.selected_start_index].scaled_mse < 1e-14
    assert result.covariance_mean_squared is None
    assert result.active_mask == (0, 0)
    assert result.nonlinear_jacobian_rank == 2
    assert all(attempt.usable for attempt in result.attempts)


def noisy_example():
    time = sample_times(128, 4096.0)
    signal = ringdown_signal(
        time, amplitude=1.0, frequency_hz=250.0, decay_time_s=0.008, phase_rad=0.4
    )
    noise = np.random.Generator(np.random.PCG64(73)).normal(0, 0.05, len(time))
    return time, signal + noise


def example_fit(time, observed, **overrides):
    options = {
        "frequency_bounds_hz": (100.0, 500.0),
        "decay_time_bounds_s": (0.002, 0.03),
        "initial_points": [(150.0, 0.004), (300.0, 0.015), (450.0, 0.004)],
    }
    options.update(overrides)
    return fit_ringdown(time, observed, **options)


def test_white_covariance_preserves_fit_and_scales_loss():
    time, observed = noisy_example()
    ordinary = example_fit(time, observed)
    weighted = example_fit(time, observed, covariance=0.01 * np.eye(len(time)))
    for name in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad"):
        assert_allclose(
            getattr(weighted, name), getattr(ordinary, name), rtol=1e-6, atol=1e-8
        )
    assert_allclose(
        weighted.covariance_mean_squared,
        weighted.ordinary_mse / 0.01,
        rtol=2e-14,
        atol=0,
    )


@pytest.mark.parametrize("scale", [1.0, 1e-21])
def test_full_covariance_matches_hand_solved_linear_problem(scale):
    # f=1, tau=.25/log(2) give columns [1,0,-1/4,0,1/16] and [0,1/2,0,-1/8,0].
    # C has [[2,1],[1,2]] as its first block and identity elsewhere.
    # H.T C^-1 H = [[563/768,-1/6],[-1/6,35/192]], H.T C^-1 y = [2/3,-1/6].
    # Hence a=4608/5203, b=-544/5203, minimum Q=306/5203.
    time = np.arange(5) / 4
    tau = 0.25 / math.log(2)
    covariance = np.eye(5)
    covariance[:2, :2] = [[2, 1], [1, 2]]
    result = fit_ringdown(
        time,
        np.array([1, 0, 0, 0, 0]) * scale,
        frequency_bounds_hz=(1 - 1e-9, 1 + 1e-9),
        decay_time_bounds_s=(tau * (1 - 1e-9), tau * (1 + 1e-9)),
        initial_points=[(1.0, tau)],
        covariance=covariance * scale**2,
    )
    # The narrow but nonzero bounds perturb the fixed-basis reference by O(1e-9).
    assert_allclose(
        result.amplitude * math.cos(result.phase_rad) / scale,
        4608 / 5203,
        rtol=2e-7,
        atol=0,
    )
    assert_allclose(
        -result.amplitude * math.sin(result.phase_rad) / scale,
        -544 / 5203,
        rtol=2e-7,
        atol=0,
    )
    assert_allclose(result.covariance_mean_squared, 306 / (5203 * 5), rtol=2e-7, atol=0)


def test_canonical_parameters_predict_the_returned_curve():
    time, observed = noisy_example()
    result = example_fit(time, observed)
    curve = ringdown_signal(
        time,
        amplitude=result.amplitude,
        frequency_hz=result.frequency_hz,
        decay_time_s=result.decay_time_s,
        phase_rad=result.phase_rad,
    )
    assert_allclose(curve, result.prediction, rtol=0, atol=2e-14)
    assert_allclose(observed - result.prediction, result.residual, rtol=0, atol=0)
    assert result.amplitude >= 0
    assert -math.pi <= result.phase_rad < math.pi


def test_multistart_keeps_convergence_and_exhaustion_diagnostics_separate():
    time = sample_times(256, 4096.0)
    observed = ringdown_signal(
        time, amplitude=1.0, frequency_hz=250.0, decay_time_s=0.03, phase_rad=0.4
    )
    result = fit_ringdown(
        time,
        observed,
        frequency_bounds_hz=(100.0, 1000.0),
        decay_time_bounds_s=(0.003, 0.08),
        # An exact start tests stopping semantics; recovery tests above use other starts.
        initial_points=[(250.0, 0.03), (900.0, 0.03)],
        max_nfev=2,
    )
    assert_allclose(result.frequency_hz, 250.0, rtol=1e-6, atol=0)
    assert result.selected_start_index == 0
    assert result.attempts[0].usable
    assert result.attempts[0].scaled_mse < 1e-14
    assert not result.attempts[1].converged
    assert not result.attempts[1].usable
    assert result.attempts[1].status == 0


def test_multiple_converged_starts_select_the_smallest_scaled_loss():
    time, observed = noisy_example()
    result = example_fit(time, observed)
    candidates = [
        (attempt.scaled_mse, index)
        for index, attempt in enumerate(result.attempts)
        if attempt.usable
    ]
    assert len(candidates) >= 2
    assert result.selected_start_index == min(candidates)[1]


def test_time_rescaling_preserves_the_same_sampled_curve():
    time, observed = hand_data()
    ordinary = hand_fit(time, observed)
    rescaled = fit_ringdown(
        time * 1000,
        observed,
        frequency_bounds_hz=(0.18, 0.35),
        decay_time_bounds_s=(0.5, 6.0),
        initial_points=[(0.21, 0.9), (0.32, 3.0)],
    )
    assert_allclose(
        rescaled.frequency_hz * 1000, ordinary.frequency_hz, rtol=1e-6, atol=0
    )
    assert_allclose(
        rescaled.decay_time_s / 1000, ordinary.decay_time_s, rtol=1e-6, atol=0
    )
    assert_allclose(rescaled.prediction, ordinary.prediction, rtol=1e-6, atol=0)


def test_frequency_bound_is_reported_when_true_frequency_is_outside_search():
    time, observed = noisy_example()
    result = example_fit(
        time,
        observed,
        frequency_bounds_hz=(200.0, 240.0),
        initial_points=[(210.0, 0.006), (230.0, 0.012)],
    )
    assert_allclose(result.frequency_hz, 240.0, rtol=1e-8, atol=0)
    assert result.active_mask[0] == 1


def test_exhausted_budget_preserves_each_failed_attempt():
    time, observed = hand_data()
    with pytest.raises(ReferenceFitError) as caught:
        hand_fit(time, observed, max_nfev=1)
    assert len(caught.value.attempts) == 2
    for attempt in caught.value.attempts:
        assert not attempt.converged and not attempt.usable
        assert attempt.status == 0
        assert attempt.nfev == 1


def test_rank_deficient_sampled_basis_is_reported_without_a_fake_fit():
    time, observed = hand_data()
    with pytest.raises(ReferenceFitError) as caught:
        hand_fit(
            time,
            observed,
            decay_time_bounds_s=(1e-300, 1e-290),
            initial_points=[(210.0, 1e-295)],
        )
    attempt = caught.value.attempts[0]
    assert not attempt.usable
    assert attempt.status is None and attempt.nfev is None
    assert "rank deficient" in attempt.message


def test_inputs_are_preserved_and_returned_arrays_are_read_only():
    time, observed = hand_data()
    original_time, original_observed = time.copy(), observed.copy()
    covariance = np.eye(len(time))
    result = hand_fit(time, observed, covariance=covariance)
    assert_array_equal(time, original_time)
    assert_array_equal(observed, original_observed)
    assert_array_equal(covariance, np.eye(len(time)))
    assert not result.prediction.flags.writeable
    assert not result.residual.flags.writeable


@pytest.mark.parametrize(
    "time",
    [
        [],
        [0, 1, 2, 3],
        [[0, 1, 2, 3, 4]],
        [1, 2, 3, 4, 5],
        [0, 1, 1, 3, 4],
        [0, 1, 2, 4, 5],
        [0, 1, 2, 3, math.nan],
        [0, 1, 2, 3, math.inf],
        [0, 1, 2, 3, 1j],
    ],
)
def test_invalid_time_axes_are_rejected(time):
    with pytest.raises(ValueError, match="time_s|observed"):
        hand_fit(time, np.ones(np.asarray(time).shape))


@pytest.mark.parametrize(
    "observed",
    [
        [],
        1.0,
        np.ones((20, 1)),
        [math.nan] * 20,
        [math.inf] * 20,
        [1j] * 20,
        [True] * 20,
        ["1"] * 20,
        np.zeros(20),
    ],
)
def test_invalid_observations_are_rejected(observed):
    time, _ = hand_data()
    with pytest.raises(ValueError, match="observed"):
        hand_fit(time, observed)


@pytest.mark.parametrize(
    ("name", "bounds"),
    [
        ("frequency_bounds_hz", (0, 350)),
        ("frequency_bounds_hz", (-1, 350)),
        ("frequency_bounds_hz", (350, 180)),
        ("frequency_bounds_hz", (1, 512)),
        ("frequency_bounds_hz", (1, 700)),
        ("frequency_bounds_hz", (1, math.inf)),
        ("decay_time_bounds_s", (0, 0.006)),
        ("decay_time_bounds_s", (0.006, 0.006)),
        ("decay_time_bounds_s", (0.001, math.nan)),
        ("decay_time_bounds_s", [0.001]),
    ],
)
def test_invalid_bounds_are_rejected(name, bounds):
    time, observed = hand_data()
    with pytest.raises(ValueError, match=name):
        hand_fit(time, observed, **{name: bounds})


@pytest.mark.parametrize(
    "starts",
    [
        [],
        [210, 0.001],
        [[210, 0.001, 3]],
        [[180, 0.001]],
        [[350, 0.001]],
        [[210, 0.0005]],
        [[210, 0.006]],
        [[210, math.nan]],
        [[210, 1j]],
    ],
)
def test_invalid_or_boundary_starts_are_rejected(starts):
    time, observed = hand_data()
    with pytest.raises(ValueError, match="initial_points"):
        hand_fit(time, observed, initial_points=starts)


@pytest.mark.parametrize("budget", [0, -1, False, 1.5, None])
def test_invalid_budgets_are_rejected(budget):
    time, observed = hand_data()
    with pytest.raises((ValueError, TypeError), match="max_nfev"):
        hand_fit(time, observed, max_nfev=budget)


def test_covariance_must_match_samples_and_be_positive_definite():
    time, observed = hand_data()
    with pytest.raises(ValueError, match="dimension"):
        hand_fit(time, observed, covariance=np.eye(2))
    with pytest.raises(ValueError, match="positive definite"):
        hand_fit(time, observed, covariance=np.zeros((len(time), len(time))))
