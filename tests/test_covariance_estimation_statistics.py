"""Check the raw second moment using independent windows and analytic errors."""

import math

import numpy as np
import pytest

from ringdown_sr.covariance_estimation import empirical_covariance
from ringdown_sr.noise import gaussian_ar1_noise


@pytest.mark.parametrize("rho", [-0.65, 0.0, 0.65])
def test_raw_covariance_mean_matches_gaussian_expectation_with_six_standard_errors(rho):
    # R independent estimates, each made from M independent N-component windows.
    n, m, repetitions, sigma = 4, 32, 2000, 0.1
    generator = np.random.Generator(np.random.PCG64(20261020))
    total = np.zeros((n, n))
    for _ in range(repetitions):
        background = np.stack(
            [
                gaussian_ar1_noise(
                    n, standard_deviation=sigma, correlation=rho, rng=generator
                )
                for _ in range(m)
            ]
        )
        total += empirical_covariance(background, mean_mode="known_zero")
    # Reference uses stationarity and Gaussian fourth moments, not the estimator.
    indices = np.arange(n)
    covariance = sigma**2 * rho ** np.abs(indices[:, None] - indices[None, :])
    standard_error = np.sqrt((sigma**4 + covariance**2) / (m * repetitions))
    # Each Gram dot product has M terms; include a fixed floating-point budget.
    eps = np.finfo(np.float64).eps
    gamma_m = m * eps / (1 - m * eps)
    gamma_r = repetitions * eps / (1 - repetitions * eps)
    rounding = 8 * (gamma_m + gamma_r) * sigma**2
    assert np.all(
        np.abs(total / repetitions - covariance) <= 6 * standard_error + rounding
    )
    assert math.isfinite(float(total.sum()))
