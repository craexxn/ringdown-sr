"""Check noise reproducibility and analytic Gaussian reference properties."""

import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from ringdown_sr.noise import gaussian_white_noise


def make_rng(seed=42):
    return np.random.Generator(np.random.PCG64(seed))


@pytest.mark.parametrize("n_samples", [1, np.int64(128)])
def test_noise_has_requested_length_and_float64_dtype(n_samples):
    values = gaussian_white_noise(n_samples, standard_deviation=1.0, rng=make_rng())
    assert values.shape == (n_samples,)
    assert values.dtype == np.float64


def test_fresh_generators_with_the_same_seed_repeat_the_noise():
    first = gaussian_white_noise(128, standard_deviation=2.0, rng=make_rng(42))
    second = gaussian_white_noise(128, standard_deviation=2.0, rng=make_rng(42))
    assert_array_equal(first, second)


def test_different_seeds_produce_different_noise():
    first = gaussian_white_noise(128, standard_deviation=2.0, rng=make_rng(42))
    second = gaussian_white_noise(128, standard_deviation=2.0, rng=make_rng(43))
    assert not np.array_equal(first, second)


def test_reusing_a_generator_advances_its_state_reproducibly():
    first_rng = make_rng(42)
    first = gaussian_white_noise(128, standard_deviation=1.0, rng=first_rng)
    second = gaussian_white_noise(128, standard_deviation=1.0, rng=first_rng)
    assert not np.array_equal(first, second)

    repeated_rng = make_rng(42)
    assert_array_equal(
        first, gaussian_white_noise(128, standard_deviation=1.0, rng=repeated_rng)
    )
    assert_array_equal(
        second, gaussian_white_noise(128, standard_deviation=1.0, rng=repeated_rng)
    )


def test_zero_standard_deviation_produces_the_noiseless_reference():
    values = gaussian_white_noise(128, standard_deviation=0.0, rng=make_rng())
    assert_array_equal(values, np.zeros(128))


@pytest.mark.parametrize("standard_deviation", [0.25, 2.0, 1e-21])
def test_noise_matches_analytic_gaussian_moments_and_central_probability(
    standard_deviation,
):
    n_samples = 200_000
    values = gaussian_white_noise(
        n_samples, standard_deviation=standard_deviation, rng=make_rng(42)
    )
    standardized = values / standard_deviation

    # Analytic standard errors for the mean and unbiased normal variance.
    assert abs(standardized.mean()) < 6 / math.sqrt(n_samples)
    variance_error = math.sqrt(2 / (n_samples - 1))
    assert abs(standardized.var(ddof=1) - 1.0) < 6 * variance_error

    # P(-1 <= Z <= 1) = erf(1/sqrt(2)) for a standard normal variable.
    expected_probability = math.erf(1 / math.sqrt(2))
    observed_probability = np.mean(np.abs(standardized) <= 1.0)
    probability_error = math.sqrt(
        expected_probability * (1 - expected_probability) / n_samples
    )
    assert abs(observed_probability - expected_probability) < 6 * probability_error


@pytest.mark.parametrize("lag", [1, 2, 10, 100])
def test_noise_has_small_off_diagonal_covariance_at_selected_lags(lag):
    n_samples = 200_000
    values = gaussian_white_noise(n_samples, standard_deviation=1.0, rng=make_rng(42))
    # For independent unit normals, E[Z_i * Z_j] = 0 when i != j.
    covariance = np.mean(values[:-lag] * values[lag:])
    assert abs(covariance) < 6 / math.sqrt(n_samples - lag)


def test_short_realizations_are_not_forced_to_exact_sample_moments():
    values = gaussian_white_noise(8, standard_deviation=2.0, rng=make_rng(42))
    assert abs(values.mean()) > 1e-10
    assert abs(values.std(ddof=1) - 2.0) > 1e-10


def test_legacy_global_random_state_is_unchanged():
    before = np.random.get_state()
    gaussian_white_noise(128, standard_deviation=1.0, rng=make_rng(42))
    after = np.random.get_state()
    assert before[0] == after[0]
    assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize(
    ("n_samples", "error"),
    [
        (0, ValueError),
        (-1, ValueError),
        (1.5, TypeError),
        (True, TypeError),
        (np.bool_(True), TypeError),
    ],
)
def test_invalid_sample_counts_are_rejected(n_samples, error):
    with pytest.raises(error, match="n_samples"):
        gaussian_white_noise(n_samples, standard_deviation=1.0, rng=make_rng())


@pytest.mark.parametrize(
    ("standard_deviation", "error"),
    [
        (-1.0, ValueError),
        (math.nan, ValueError),
        (math.inf, ValueError),
        (True, TypeError),
        (np.bool_(True), TypeError),
        ("1.0", TypeError),
        (1j, TypeError),
    ],
)
def test_invalid_standard_deviations_are_rejected(standard_deviation, error):
    with pytest.raises(error, match="standard_deviation"):
        gaussian_white_noise(8, standard_deviation=standard_deviation, rng=make_rng())


@pytest.mark.parametrize("rng", [None, 42, np.random.RandomState(42)])
def test_invalid_random_number_generators_are_rejected(rng):
    with pytest.raises(TypeError, match="rng"):
        gaussian_white_noise(8, standard_deviation=1.0, rng=rng)


def test_invalid_parameters_do_not_advance_the_generator():
    rng = make_rng(42)
    before = rng.bit_generator.state
    with pytest.raises(ValueError, match="standard_deviation"):
        gaussian_white_noise(8, standard_deviation=-1.0, rng=rng)
    assert rng.bit_generator.state == before


def test_overflow_is_reported_instead_of_returning_infinite_noise():
    with pytest.raises(ValueError, match="non-finite"):
        gaussian_white_noise(
            128, standard_deviation=np.finfo(np.float64).max, rng=make_rng(42)
        )
