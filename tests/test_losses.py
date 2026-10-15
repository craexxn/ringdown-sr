"""Verify loss definitions against independently derived analytic cases."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.losses import CovarianceLoss, mean_squared_error


def test_mse_matches_hand_calculated_sum_of_squares():
    assert_allclose(mean_squared_error([1.0, -2.0, 3.0]), 14 / 3, rtol=2e-15, atol=0)


def test_mse_preserves_tiny_nonzero_values():
    assert_allclose(mean_squared_error([1e-21, -2e-21]), 2.5e-42, rtol=2e-15, atol=0)


def test_mse_does_not_overflow_when_only_the_unnormalized_sum_would():
    assert_allclose(mean_squared_error([1e154, -1e154]), 1e308, rtol=2e-15, atol=0)


def test_zero_residual_has_zero_loss():
    loss = CovarianceLoss([[2.0, 1.0], [1.0, 2.0]])
    assert mean_squared_error([0.0, 0.0]) == 0.0
    assert loss.quadratic_form([0.0, 0.0]) == 0.0
    assert loss.mean_squared([0.0, 0.0]) == 0.0


def test_identity_covariance_recovers_ordinary_mse_and_explicit_sum():
    loss = CovarianceLoss(np.eye(3))
    assert loss.n_samples == 3
    assert_allclose(loss.quadratic_form([1.0, -2.0, 3.0]), 14.0, rtol=2e-15, atol=0)
    assert_allclose(loss.mean_squared([1.0, -2.0, 3.0]), 14 / 3, rtol=2e-15, atol=0)


def test_one_sample_covariance_is_supported():
    loss = CovarianceLoss([[4.0]])
    assert_allclose(loss.quadratic_form([2.0]), 1.0, rtol=2e-15, atol=0)
    assert_allclose(loss.mean_squared([2.0]), 1.0, rtol=2e-15, atol=0)


def test_diagonal_covariance_uses_variances_and_sample_count():
    # 2**2 / 4 + 1**2 / 1 = 2; division by N=2 gives 1.
    loss = CovarianceLoss([[4.0, 0.0], [0.0, 1.0]])
    assert_allclose(loss.quadratic_form([2.0, 1.0]), 2.0, rtol=2e-15, atol=0)
    assert_allclose(loss.mean_squared([2.0, 1.0]), 1.0, rtol=2e-15, atol=0)


@pytest.mark.parametrize(
    ("residual", "expected"), [([1.0, 1.0], 2 / 3), ([1.0, -1.0], 2.0)]
)
def test_off_diagonal_covariance_changes_the_relative_penalty(residual, expected):
    # Inverse is (1/3) * [[2, -1], [-1, 2]], computed by hand.
    loss = CovarianceLoss([[2.0, 1.0], [1.0, 2.0]])
    assert_allclose(loss.quadratic_form(residual), expected, rtol=2e-15, atol=0)
    assert_allclose(loss.mean_squared(residual), expected / 2, rtol=2e-15, atol=0)


def test_whitening_uses_the_lower_factor_in_the_correct_direction():
    # L = [[2, 0], [1, 3]], so L @ [1, 1] = [2, 4].
    loss = CovarianceLoss([[4.0, 2.0], [2.0, 10.0]])
    assert_allclose(loss.whiten([2.0, 4.0]), [1.0, 1.0], rtol=2e-15, atol=0)
    assert_allclose(loss.quadratic_form([2.0, 4.0]), 2.0, rtol=2e-15, atol=0)


def test_joint_permutation_of_residual_and_covariance_preserves_loss():
    # Swapping the variables gives C = [[10, 2], [2, 4]] and r = [4, 2].
    loss = CovarianceLoss([[10.0, 2.0], [2.0, 4.0]])
    assert_allclose(loss.quadratic_form([4.0, 2.0]), 2.0, rtol=2e-15, atol=0)


@pytest.mark.parametrize("scale", [2.0, 1e-21, 1e-150, 1e150])
def test_joint_signal_and_covariance_scaling_preserves_dimensionless_loss(scale):
    loss = CovarianceLoss(np.eye(2) * scale**2)
    residual = np.array([2.0, -1.0]) * scale
    assert_allclose(loss.quadratic_form(residual), 5.0, rtol=3e-15, atol=0)
    assert_allclose(loss.mean_squared(residual), 2.5, rtol=3e-15, atol=0)


@pytest.mark.parametrize("rho", [0.5, 1 - 2**-20])
def test_strong_correlation_matches_an_eigenvector_reference(rho):
    # [1, -1] has eigenvalue 1-rho; Q = 2/(1-rho).
    loss = CovarianceLoss([[1.0, rho], [rho, 1.0]])
    condition = (1 + rho) / (1 - rho)
    tolerance = 10 * np.finfo(np.float64).eps * condition
    assert_allclose(
        loss.quadratic_form([1.0, -1.0]), 2 / (1 - rho), rtol=tolerance, atol=0
    )


def test_factor_is_independent_of_later_covariance_mutations():
    covariance = np.eye(2)
    loss = CovarianceLoss(covariance)
    assert_array_equal(covariance, np.eye(2))
    covariance[:] = 0.0
    assert_allclose(loss.quadratic_form([1.0, 2.0]), 5.0, rtol=2e-15, atol=0)


def test_residual_and_cached_factor_are_not_modified_by_evaluation():
    residual = np.array([2.0, 4.0])
    loss = CovarianceLoss([[4.0, 2.0], [2.0, 10.0]])
    transformed = loss.whiten(residual)
    transformed[:] = 0.0
    assert_array_equal(residual, [2.0, 4.0])
    assert_allclose(loss.quadratic_form(residual), 2.0, rtol=2e-15, atol=0)


@pytest.mark.parametrize(
    "residual", [[], 0.0, [[0.0]], [math.nan], [math.inf], [1j], ["0"], [True]]
)
def test_invalid_residuals_are_rejected_by_both_losses(residual):
    with pytest.raises(ValueError, match="residual"):
        mean_squared_error(residual)
    with pytest.raises(ValueError, match="residual"):
        CovarianceLoss([[1.0]]).quadratic_form(residual)


def test_residual_length_must_match_covariance_dimension():
    with pytest.raises(ValueError, match="length"):
        CovarianceLoss(np.eye(2)).mean_squared([1.0])


@pytest.mark.parametrize(
    "covariance",
    [
        [],
        [[]],
        1.0,
        [1.0, 2.0],
        np.ones((2, 3)),
        [[[1.0]]],
        [[math.nan]],
        [[math.inf]],
        [[1j]],
        [["1"]],
        [[True]],
        [[1.0], [1.0, 2.0]],
    ],
)
def test_invalid_covariance_arrays_are_rejected(covariance):
    with pytest.raises(ValueError, match="covariance"):
        CovarianceLoss(covariance)


@pytest.mark.parametrize("scale", [1.0, 1e-42])
def test_asymmetry_is_rejected_even_for_tiny_covariance_values(scale):
    with pytest.raises(ValueError, match="symmetric"):
        CovarianceLoss(np.array([[2.0, 0.0], [1.0, 2.0]]) * scale)


def test_small_asymmetry_is_not_silently_repaired():
    with pytest.raises(ValueError, match="symmetric"):
        CovarianceLoss([[2.0, 1.0], [1.0 + 1e-14, 2.0]])


@pytest.mark.parametrize(
    "covariance",
    [np.zeros((2, 2)), [[1.0, 1.0], [1.0, 1.0]], [[1.0, 2.0], [2.0, 1.0]], -np.eye(2)],
)
def test_singular_and_indefinite_covariances_are_rejected(covariance):
    with pytest.raises(ValueError, match="positive definite"):
        CovarianceLoss(covariance)


def test_unrepresentable_ordinary_loss_is_reported():
    with pytest.raises(ValueError, match="float64 range"):
        mean_squared_error([1e308])


def test_unrepresentable_weighted_loss_is_reported():
    with pytest.raises(ValueError, match="float64 range"):
        CovarianceLoss([[1.0]]).quadratic_form([1e308])


def test_unrepresentable_whitened_residual_is_reported():
    with pytest.raises(ValueError, match="float64 range"):
        CovarianceLoss([[1e-300]]).whiten([1e308])
