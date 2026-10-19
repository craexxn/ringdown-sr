"""Check stationary AR(1) draws against hand calculations and Gaussian moments."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.losses import CovarianceLoss
from ringdown_sr.noise import ar1_covariance, gaussian_ar1_noise


def rng(seed=42):
    return np.random.Generator(np.random.PCG64(seed))


class FixedNormals(np.random.Generator):
    """Supply specified independent-normal inputs for an exact arithmetic reference."""

    def __init__(self):
        super().__init__(np.random.PCG64(0))
        self.calls = []

    def standard_normal(self, size, dtype):
        self.calls.append((size, dtype))
        return np.array([1.0, 2.0, -1.0, 0.0], dtype=dtype)


@pytest.mark.parametrize(
    ("rho", "expected"), [(0.6, [5.0, 11.0, 2.6, 1.56]), (-0.6, [5.0, 5.0, -7.0, 4.2])]
)
def test_hand_calculated_recursion_and_stationary_whitening(rho, expected):
    # sigma=5, |rho|=3/5 give innovation standard deviation 4.
    generator = FixedNormals()
    values = gaussian_ar1_noise(
        4, standard_deviation=5.0, correlation=rho, rng=generator
    )
    assert_allclose(values, expected, rtol=2e-15, atol=0)
    assert generator.calls == [(4, np.float64)]
    covariance = ar1_covariance(4, standard_deviation=5.0, correlation=rho)
    hand = np.array(
        [[25, 15, 9, 5.4], [15, 25, 15, 9], [9, 15, 25, 15], [5.4, 9, 15, 25]]
    )
    if rho < 0:
        signs = np.array([1, -1, 1, -1])
        hand = hand * signs[:, None] * signs[None, :]
    assert_allclose(covariance, hand, rtol=2e-15, atol=0)
    loss = CovarianceLoss(covariance)
    assert_allclose(loss.whiten(values), [1, 2, -1, 0], rtol=0, atol=1e-15)
    assert_allclose(loss.quadratic_form(values), 6.0, rtol=2e-15, atol=0)


@pytest.mark.parametrize("rho", [-0.65, 0.0, 0.65])
def test_independent_short_windows_have_stationary_mean_and_covariance(rho):
    # Independent windows avoid treating correlated samples as independent.
    # For zero-mean jointly Gaussian X,Y, Var(XY)=Var(X)Var(Y)+Cov(X,Y)**2.
    windows, n, sigma = 20_000, 6, 2.0
    generator = rng(73)
    values = (
        np.stack(
            [
                gaussian_ar1_noise(
                    n, standard_deviation=sigma, correlation=rho, rng=generator
                )
                for _ in range(windows)
            ]
        )
        / sigma
    )
    expected = rho ** np.abs(np.arange(n)[:, None] - np.arange(n)[None, :])
    assert np.all(np.abs(values.mean(axis=0)) < 6 / math.sqrt(windows))
    observed = values.T @ values / windows
    standard_error = np.sqrt((1 + expected**2) / windows)
    assert np.all(np.abs(observed - expected) < 6 * standard_error)
    # In particular, variance at sample zero is tested, ruling out a zero start.


@pytest.mark.parametrize("rho", [-0.8, 0.0, 0.8])
@pytest.mark.parametrize("sigma", [0.0, 1e-21, 2.0])
def test_reproducibility_and_exact_rng_call_schedule(rho, sigma):
    generator = rng()
    first = gaussian_ar1_noise(
        32, standard_deviation=sigma, correlation=rho, rng=generator
    )
    reference = rng()
    reference.standard_normal(32, dtype=np.float64)
    assert generator.bit_generator.state == reference.bit_generator.state
    assert_array_equal(
        first,
        gaussian_ar1_noise(32, standard_deviation=sigma, correlation=rho, rng=rng()),
    )
    assert first.shape == (32,) and first.dtype == np.float64
    if sigma == 0:
        assert_array_equal(first, np.zeros(32))
    else:
        assert np.any(first != 0)
    second = gaussian_ar1_noise(
        32, standard_deviation=sigma, correlation=rho, rng=generator
    )
    reference.standard_normal(32, dtype=np.float64)
    assert generator.bit_generator.state == reference.bit_generator.state
    if sigma:
        assert not np.array_equal(first, second)


def test_zero_correlation_is_independent_gaussian_noise():
    values = gaussian_ar1_noise(128, standard_deviation=2.0, correlation=0.0, rng=rng())
    assert_array_equal(values, 2 * rng().standard_normal(128, dtype=np.float64))
    assert_array_equal(
        ar1_covariance(5, standard_deviation=2.0, correlation=0.0), 4 * np.eye(5)
    )


def test_single_sample_has_stationary_scale_and_zero_sigma_has_zero_covariance():
    expected = 3 * rng().standard_normal(1, dtype=np.float64)
    assert_array_equal(
        gaussian_ar1_noise(1, standard_deviation=3.0, correlation=-0.9, rng=rng()),
        expected,
    )
    assert_array_equal(
        ar1_covariance(1, standard_deviation=3.0, correlation=-0.9), [[9.0]]
    )
    assert_array_equal(
        ar1_covariance(4, standard_deviation=0.0, correlation=0.9), np.zeros((4, 4))
    )


def test_generator_does_not_use_global_state_or_force_sample_moments():
    before = np.random.get_state()
    values = gaussian_ar1_noise(8, standard_deviation=2.0, correlation=0.6, rng=rng())
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])
    assert abs(values.mean()) > 1e-10
    assert abs(values.std(ddof=1) - 2) > 1e-10


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("n_samples", 0),
        ("n_samples", 1.5),
        ("n_samples", True),
        ("standard_deviation", -1),
        ("standard_deviation", math.nan),
        ("standard_deviation", True),
        ("standard_deviation", "1"),
        ("correlation", -1),
        ("correlation", 1),
        ("correlation", math.inf),
        ("correlation", math.nan),
        ("correlation", True),
        ("correlation", 1j),
    ],
)
def test_invalid_parameters_are_rejected_before_drawing(name, value):
    parameters = {"n_samples": 8, "standard_deviation": 1.0, "correlation": 0.5}
    parameters[name] = value
    generator = rng()
    before = generator.bit_generator.state
    with pytest.raises((ValueError, TypeError)):
        gaussian_ar1_noise(**parameters, rng=generator)
    assert generator.bit_generator.state == before
    with pytest.raises((ValueError, TypeError)):
        ar1_covariance(**parameters)


@pytest.mark.parametrize("generator", [None, 42, np.random.RandomState(42)])
def test_invalid_rng_is_rejected(generator):
    with pytest.raises(TypeError, match="rng"):
        gaussian_ar1_noise(8, standard_deviation=1.0, correlation=0.5, rng=generator)


@pytest.mark.parametrize("sigma", [1e-200, 1e200])
def test_covariance_rejects_unrepresentable_positive_variance(sigma):
    with pytest.raises(ValueError, match="variance"):
        ar1_covariance(5, standard_deviation=sigma, correlation=0.5)


@pytest.mark.parametrize("rho", [np.nextafter(-1.0, 0.0), np.nextafter(1.0, 0.0)])
def test_strictly_stationary_boundary_values_generate_finite_samples(rho):
    values = gaussian_ar1_noise(128, standard_deviation=1.0, correlation=rho, rng=rng())
    assert np.all(np.isfinite(values))


def test_overflow_is_reported():
    with pytest.raises(ValueError, match="float64"):
        gaussian_ar1_noise(
            128, standard_deviation=np.finfo(float).max, correlation=0.5, rng=rng()
        )
