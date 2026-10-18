"""Cross-check the full nonlinear weighted fit using another parameterization."""

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.optimize import least_squares

from ringdown_sr.reference_fit import fit_ringdown


@pytest.mark.parametrize("rho", [0.0, 0.65, -0.5])
@pytest.mark.parametrize(
    ("frequency", "tau", "phase", "amplitude"),
    [(180.0, 0.009, -2.4, 0.7), (330.0, 0.018, 1.2, 1.3), (240.0, 0.006, 3.0, 1.0)],
)
def test_nonlinear_correlated_fit_matches_direct_four_parameter_reference(
    rho, frequency, tau, phase, amplitude
):
    # Independent data construction, symmetric eigen-whitening, and direct
    # optimization of all four parameters; production uses variable projection
    # and lower-triangular Cholesky whitening. Both searches remain local.
    time = np.arange(96) / 2048
    sigma = 0.04
    covariance = sigma**2 * rho ** np.abs(
        np.arange(96)[:, None] - np.arange(96)[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    whitening = (eigenvectors / np.sqrt(eigenvalues)) @ eigenvectors.T
    clean = (
        amplitude * np.exp(-time / tau) * np.cos(2 * np.pi * frequency * time + phase)
    )
    rng = np.random.Generator(np.random.PCG64(20261018))
    observed = clean + (eigenvectors * np.sqrt(eigenvalues)) @ rng.standard_normal(
        len(time)
    )
    options = {
        "frequency_bounds_hz": (100.0, 450.0),
        "decay_time_bounds_s": (0.003, 0.04),
        "initial_points": [(130.0, 0.005), (270.0, 0.012), (410.0, 0.03)],
    }
    fit = fit_ringdown(time, observed, covariance=covariance, **options)

    def residual(parameters):
        a, b, f, log_tau = parameters
        curve = np.exp(-time / np.exp(log_tau)) * (
            a * np.cos(2 * np.pi * f * time) + b * np.sin(2 * np.pi * f * time)
        )
        return whitening @ (curve - observed)

    references = []
    for initial in [
        (0.7, 0.3, 130.0, np.log(0.005)),
        (-0.4, 0.7, 270.0, np.log(0.012)),
        (0.5, -0.5, 410.0, np.log(0.03)),
    ]:
        solution = least_squares(
            residual,
            initial,
            bounds=(
                [-np.inf, -np.inf, 100.0, np.log(0.003)],
                [np.inf, np.inf, 450.0, np.log(0.04)],
            ),
            jac="3-point",
            x_scale=[1, 1, 200, 1],
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
            max_nfev=3000,
        )
        if solution.success:
            references.append(solution)
    assert references
    best = min(references, key=lambda result: result.fun @ result.fun)
    q_reference = best.fun @ best.fun
    q_fit = fit.residual @ np.linalg.solve(covariance, fit.residual)
    # Cross-implementation numerical tolerances; not scientific accuracy targets.
    assert_allclose(q_fit, q_reference, rtol=1e-6, atol=1e-6)
    assert_allclose(fit.frequency_hz, best.x[2], rtol=0, atol=1e-3)
    assert_allclose(fit.decay_time_s, np.exp(best.x[3]), rtol=0, atol=1e-6)
    assert_allclose(fit.covariance_mean_squared, q_fit / len(time), rtol=1e-12, atol=0)
    scaled = fit_ringdown(time, observed, covariance=37 * covariance, **options)
    assert_allclose(scaled.prediction, fit.prediction, rtol=0, atol=1e-6)
