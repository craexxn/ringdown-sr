"""Check estimation and selection against hand-derived covariance references."""

import math
from dataclasses import FrozenInstanceError
from itertools import permutations

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.covariance_estimation import (
    CovarianceEstimationError,
    empirical_covariance,
    estimate_covariance,
)

TRAIN = [[1, 0], [-1, 0], [0, 2], [0, -2]]
VALIDATION = [[1, 0], [0, 2]]


def estimate(train=TRAIN, validation=VALIDATION, alphas=(0, 0.4, 1), kappa=10):
    return estimate_covariance(
        train,
        validation,
        alpha_candidates=alphas,
        kappa_max=kappa,
        mean_mode="known_zero",
    )


def test_nonzero_sample_mean_is_not_subtracted_and_divisor_is_m():
    # Centering would give [[0,0],[0,1]], and M-1 would double the answer.
    train = [[1, 0], [1, 2]]
    expected = [[1, 1], [1, 2]]
    assert_array_equal(empirical_covariance(train, mean_mode="known_zero"), expected)
    assert_array_equal(estimate(train=train, alphas=[0]).raw_covariance, expected)


def test_balanced_hand_matrix_and_fixed_shrinkage_score():
    result = estimate(validation=[[1, 1], [-1, -1]], alphas=[0.4])
    assert_array_equal(result.raw_covariance, np.diag([0.5, 2]))
    assert result.mu == 1.25
    assert_allclose(result.covariance, np.diag([0.8, 1.7]), rtol=2e-15, atol=0)
    candidate = result.candidates[0]
    assert candidate.eligible and candidate.reason is None
    assert candidate.cholesky_success is True
    assert_allclose(candidate.eigenvalues, [0.8, 1.7], rtol=2e-15, atol=0)
    assert_allclose(candidate.condition_number, 17 / 8, rtol=2e-15, atol=0)
    assert_allclose(candidate.log_determinant, math.log(34 / 25), rtol=2e-15, atol=0)
    assert_allclose(candidate.validation_quadratic_mean, 125 / 68, rtol=2e-15, atol=0)
    assert_allclose(candidate.score, math.log(34 / 25) + 125 / 68, rtol=2e-15, atol=0)


@pytest.mark.parametrize("grid", list(permutations([0.0, 0.4, 1.0])))
def test_complete_selector_chooses_full_score_minimum_in_any_grid_order(grid):
    result = estimate(alphas=grid)
    assert result.alpha_selected == 0
    assert_array_equal(result.covariance, np.diag([0.5, 2]))
    assert [c.alpha for c in result.candidates] == [0, 0.4, 1]
    expected_scores = [2, math.log(34 / 25) + 245 / 136, 2 * math.log(5 / 4) + 2]
    assert_allclose(
        [c.score for c in result.candidates], expected_scores, rtol=3e-15, atol=0
    )
    quadratics = [c.validation_quadratic_mean for c in result.candidates]
    assert_allclose(quadratics, [2, 245 / 136, 2], rtol=3e-15, atol=0)
    # Omitting the log determinant would select alpha=0.4 instead.
    assert result.candidates[int(np.argmin(quadratics))].alpha == 0.4


def test_off_diagonal_score_matches_hand_inverse_and_independent_eigen_whitening():
    # S=[[5,3],[3,9]]/2; det(S)=9; inverse(S)=[[9,-3],[-3,5]]/18.
    validation = np.array([[1, 2], [-2, 1]], dtype=float)
    result = estimate(train=[[2, 0], [1, 3]], validation=validation, alphas=[0])
    assert_array_equal(result.covariance, [[2.5, 1.5], [1.5, 4.5]])
    expected_q = 35 / 18
    assert_allclose(
        result.candidates[0].validation_quadratic_mean, expected_q, rtol=2e-15, atol=0
    )
    eigenvalues, eigenvectors = np.linalg.eigh(result.covariance)
    whitened = (validation @ eigenvectors) / np.sqrt(eigenvalues)
    assert_allclose(
        np.mean(np.sum(whitened**2, axis=1)), expected_q, rtol=2e-15, atol=0
    )
    assert_allclose(
        result.candidates[0].score, math.log(9) + expected_q, rtol=2e-15, atol=0
    )


def test_score_averages_windows_and_does_not_divide_by_covariance_dimension():
    result = estimate(validation=[[1, 0]], alphas=[0])
    repeated = estimate(validation=[[1, 0]] * 7, alphas=[0])
    assert_allclose(result.candidates[0].score, 2, rtol=2e-15, atol=0)
    assert_allclose(repeated.candidates[0].score, 2, rtol=2e-15, atol=0)


@pytest.mark.parametrize("grid", [(1, 0.4, 0), (0.1, 0.7, 1)])
def test_exact_isotropic_score_ties_choose_smallest_alpha(grid):
    result = estimate(train=[[1, 0], [-1, 0], [0, 1], [0, -1]], alphas=grid)
    assert result.alpha_selected == min(grid)
    assert_array_equal(result.covariance, np.eye(2) * 0.5)
    assert len({c.score for c in result.candidates}) == 1


def test_condition_limit_accepts_equality_and_keeps_rejected_candidate_diagnostics():
    result = estimate(train=[[1, 0], [-1, 0]], alphas=[0.4, 0.5], kappa=3)
    rejected, accepted = result.candidates
    assert rejected.reason == "condition_limit_exceeded"
    assert not rejected.eligible and rejected.score is None
    assert rejected.condition_number == 4
    assert rejected.cholesky_success is None
    assert accepted.eligible and accepted.condition_number == 3
    assert result.alpha_selected == 0.5
    assert_array_equal(result.covariance, np.diag([0.75, 0.25]))


def test_rank_deficiency_rejects_raw_matrix_without_hidden_jitter():
    result = estimate(train=[[1, 0], [-1, 0]], alphas=[0, 1])
    assert_array_equal(result.raw_covariance, np.diag([1, 0]))
    assert result.candidates[0].reason == "not_positive_definite"
    assert result.candidates[0].eigenvalues == (0, 1)
    assert result.alpha_selected == 1
    assert_array_equal(result.covariance, np.eye(2) * 0.5)


def test_tiny_explicit_alpha_is_not_lost_by_subtraction_in_diagonal_update():
    # A direct convex sum retains alpha*mu even when 1-alpha rounds to one.
    result = estimate(
        train=[[1, 0], [-1, 0]],
        validation=[[0, 1]],
        alphas=[1e-20],
        kappa=1e25,
    )
    assert result.alpha_selected == 1e-20
    assert_allclose(result.covariance, np.diag([1, 5e-21]), rtol=2e-15, atol=0)
    assert_allclose(result.candidates[0].condition_number, 2e20, rtol=2e-15, atol=0)


def test_all_rejected_candidates_raise_with_raw_matrix_scale_and_sorted_records():
    with pytest.raises(CovarianceEstimationError, match="No alpha") as info:
        estimate(train=[[1, 0], [-1, 0]], alphas=[0.4, 0], kappa=3)
    error = info.value
    assert [c.alpha for c in error.candidates] == [0, 0.4]
    assert [c.reason for c in error.candidates] == [
        "not_positive_definite",
        "condition_limit_exceeded",
    ]
    assert error.mu == 0.5
    assert_array_equal(error.raw_covariance, np.diag([1, 0]))


@pytest.mark.parametrize("scale", [1e-21, 1e21, 1e-150, 1e150])
def test_joint_scale_preserves_selection_condition_and_score_offset(scale):
    baseline = estimate()
    result = estimate(np.asarray(TRAIN) * scale, np.asarray(VALIDATION) * scale)
    assert result.alpha_selected == baseline.alpha_selected
    assert_allclose(
        result.raw_covariance / scale**2, baseline.raw_covariance, rtol=8e-15, atol=0
    )
    assert_allclose(
        result.covariance / scale**2, baseline.covariance, rtol=8e-15, atol=0
    )
    for actual, reference in zip(result.candidates, baseline.candidates):
        assert_allclose(
            actual.condition_number, reference.condition_number, rtol=8e-15, atol=0
        )
        assert_allclose(
            actual.score, reference.score + 4 * math.log(abs(scale)), rtol=8e-15, atol=0
        )


def test_empirical_scaling_avoids_intermediate_square_and_trace_overflow():
    # A single spike has variance 1e310/1000=1e307, which is representable.
    windows = np.zeros((1000, 1))
    windows[0, 0] = 1e155
    assert_allclose(
        empirical_covariance(windows, mean_mode="known_zero"),
        [[1e307]],
        rtol=3e-15,
        atol=0,
    )
    # Both diagonal entries and their mean are finite; their sum overflows.
    large = [[1e154, 1e154], [-1e154, -1e154]]
    result = estimate(large, [[0, 0]], alphas=[0, 1])
    assert not result.candidates[0].eligible
    assert result.alpha_selected == 1
    assert_allclose(result.mu, 1e308, rtol=3e-15, atol=0)
    assert_allclose(result.covariance / 1e308, np.eye(2), rtol=3e-15, atol=0)


def test_different_column_scales_preserve_representable_variances():
    windows = [[1e150, 0], [0, 1e-150]]
    raw = empirical_covariance(windows, mean_mode="known_zero")
    assert_allclose(raw.diagonal(), [5e299, 5e-301], rtol=3e-15, atol=0)
    assert raw[0, 1] == raw[1, 0] == 0


def test_training_and_validation_are_not_modified_or_refitted_together():
    train = np.array(TRAIN, dtype=float)
    validation = np.array(VALIDATION, dtype=float)
    result = estimate(train, validation)
    assert_array_equal(train, TRAIN)
    assert_array_equal(validation, VALIDATION)
    assert result.n_train == 4 and result.n_validation == 2
    assert result.mean_mode == "known_zero"
    assert result.method == "empirical_identity_shrinkage_holdout_v1"
    assert result.kappa_max == 10
    train[:] = 99
    validation[:] = 99
    assert_array_equal(result.raw_covariance, np.diag([0.5, 2]))
    assert_array_equal(result.covariance, np.diag([0.5, 2]))


def test_matrix_symmetry_is_exact_and_result_cannot_be_mutated():
    result = estimate(train=[[2, 0], [1, 3]], alphas=[0.4])
    for matrix in (result.raw_covariance, result.covariance):
        assert_array_equal(matrix, matrix.T)
        with pytest.raises(ValueError):
            matrix[0, 0] = 0
        with pytest.raises(ValueError):
            matrix.setflags(write=True)
    with pytest.raises(FrozenInstanceError):
        result.alpha_selected = 1
    with pytest.raises(FrozenInstanceError):
        result.candidates[0].score = 0


def test_global_random_state_is_not_used():
    before = np.random.get_state()
    first, second = estimate(), estimate()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])
    assert_array_equal(first.covariance, second.covariance)
    assert first.candidates == second.candidates


def test_one_window_one_feature_and_zero_validation_are_supported():
    result = estimate(train=[[2]], validation=[[0]], alphas=[1, 0])
    assert_array_equal(result.raw_covariance, [[4]])
    assert_array_equal(result.covariance, [[4]])
    assert result.alpha_selected == 0
    assert_allclose(result.candidates[0].score, math.log(4), rtol=2e-15, atol=0)


@pytest.mark.parametrize(
    "values",
    [
        [],
        [[]],
        [1, 2],
        1,
        [[[1]]],
        [[1, 2], [1]],
        [[True]],
        [["1"]],
        [[1j]],
        [[math.nan]],
        [[math.inf]],
    ],
)
@pytest.mark.parametrize("role", ["train", "validation"])
def test_invalid_window_arrays_are_rejected(values, role):
    kwargs = {role: values}
    with pytest.raises(ValueError, match="background_" + role):
        estimate(**kwargs)
    if role == "train":
        with pytest.raises(ValueError, match="background_train"):
            empirical_covariance(values, mean_mode="known_zero")


def test_validation_window_dimension_must_match_training():
    with pytest.raises(ValueError, match="dimensions must match"):
        estimate(validation=[[1]])


@pytest.mark.parametrize(
    "grid",
    [
        [],
        0.5,
        [[0.5]],
        [True],
        ["0.5"],
        [1j],
        [math.nan],
        [math.inf],
        [-0.1],
        [1.1],
        [0.4, 0.4],
        [-0.0, 0.0],
    ],
)
def test_invalid_alpha_grids_are_rejected(grid):
    with pytest.raises(ValueError, match="alpha_candidates"):
        estimate(alphas=grid)


@pytest.mark.parametrize(
    ("kappa", "error"),
    [
        (True, TypeError),
        (np.bool_(False), TypeError),
        ("10", TypeError),
        (1j, TypeError),
        (math.nan, ValueError),
        (math.inf, ValueError),
        (10**500, ValueError),
        (-1, ValueError),
        (0, ValueError),
        (1, ValueError),
    ],
)
def test_invalid_condition_limits_are_rejected(kappa, error):
    with pytest.raises(error, match="kappa_max"):
        estimate(kappa=kappa)


@pytest.mark.parametrize("mode", [None, True, "centered", "", ["known_zero"]])
def test_other_mean_modes_are_not_silently_enabled(mode):
    with pytest.raises(ValueError, match="mean_mode"):
        empirical_covariance(TRAIN, mean_mode=mode)
    with pytest.raises(ValueError, match="mean_mode"):
        estimate_covariance(
            TRAIN, VALIDATION, alpha_candidates=[1], kappa_max=10, mean_mode=mode
        )


def test_zero_raw_second_moment_is_allowed_but_cannot_be_used_for_weighting():
    assert_array_equal(
        empirical_covariance([[0, 0]], mean_mode="known_zero"), np.zeros((2, 2))
    )
    with pytest.raises(CovarianceEstimationError, match="mean variance") as info:
        estimate(train=[[0, 0]])
    assert info.value.candidates == () and info.value.mu == 0


@pytest.mark.parametrize("train", [[[1e308]], [[1e-200]]])
def test_unrepresentable_positive_variances_raise_instead_of_becoming_zero_or_infinite(
    train,
):
    with pytest.raises(CovarianceEstimationError, match="float64"):
        estimate(train=train, validation=[[0]], alphas=[1])


@pytest.mark.parametrize("amplitude", [1e150, 1e308])
def test_unrepresentable_validation_score_preserves_failed_candidate(amplitude):
    with pytest.raises(CovarianceEstimationError, match="No alpha") as info:
        estimate(train=[[1e-150]], validation=[[amplitude]], alphas=[1])
    candidate = info.value.candidates[0]
    assert candidate.reason == "validation_score_out_of_range"
    assert candidate.cholesky_success is True
    assert candidate.score is None and not candidate.eligible


def test_cholesky_failure_is_reported_without_repair_or_fallback(monkeypatch):
    def failed(*args, **kwargs):
        raise np.linalg.LinAlgError("unusable factor")

    monkeypatch.setattr("ringdown_sr.covariance_estimation.cholesky", failed)
    with pytest.raises(CovarianceEstimationError) as info:
        estimate(alphas=[1])
    assert info.value.candidates[0].reason == "cholesky_failed"
    assert info.value.candidates[0].cholesky_success is False
