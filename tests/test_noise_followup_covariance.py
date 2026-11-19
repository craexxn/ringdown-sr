"""Independent matrix and spectrum references for the duration study."""

import numpy as np
import pytest
from scipy.linalg import toeplitz
from scipy.signal import welch

from ringdown_sr.covariance_estimation import (
    CovarianceEstimationError,
    estimate_covariance,
)
from ringdown_sr.noise_followup_covariance import (
    METHOD,
    WELCH_METHOD,
    empirical_from_series,
    estimate_from_raw,
    welch_covariance,
)


def test_chunked_second_moment_matches_direct_outer_product():
    series = np.linspace(-3.0, 2.0, 180, dtype=np.float64)
    rows = series.reshape(60, 3)
    expected = sum(np.outer(row, row) for row in rows) / len(rows)
    for chunk_samples in (3, 9, 60, 300):
        actual = empirical_from_series(series, n_samples=3, chunk_samples=chunk_samples)
        np.testing.assert_allclose(actual, expected, rtol=3e-15, atol=1e-15)
        assert np.array_equal(actual, actual.T)
        with pytest.raises(ValueError):
            actual.setflags(write=True)


def test_prefix_second_moment_does_not_read_later_samples():
    values = np.array([1.0, 2, -1, 2, np.nan, np.nan])
    actual = empirical_from_series(values[:4], n_samples=2, chunk_samples=2)
    np.testing.assert_array_equal(actual, np.diag([1.0, 4.0]))


@pytest.mark.parametrize(
    "values,kwargs",
    [
        (np.ones(3), {"n_samples": 2, "chunk_samples": 2}),
        (np.ones(4), {"n_samples": 2, "chunk_samples": 3}),
        (np.ones((2, 2)), {"n_samples": 2, "chunk_samples": 2}),
        (np.ones(4, dtype=np.float32), {"n_samples": 2, "chunk_samples": 2}),
        (np.array([np.inf, 1]), {"n_samples": 2, "chunk_samples": 2}),
    ],
)
def test_invalid_stream_geometry_or_data_rejected(values, kwargs):
    with pytest.raises(ValueError):
        empirical_from_series(values, **kwargs)


def test_unchanged_shrinkage_rule_matches_old_estimator():
    train = np.array([[2.0, 1], [-1, 3], [3, -2], [1, 1], [-2, -1]])
    validation = np.array([[1.0, 0], [-1, 1], [1, -1], [0, 1]])
    options = {
        "alpha_candidates": [0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1],
        "kappa_max": 1e8,
        "mean_mode": "known_zero",
    }
    original = estimate_covariance(train, validation, **options)
    raw = empirical_from_series(train.ravel(), n_samples=2, chunk_samples=4)
    actual = estimate_from_raw(
        raw, validation, n_train=5, structural_rank_bound=5, **options
    )
    assert actual.method == METHOD
    assert actual.alpha_selected == original.alpha_selected
    assert actual.n_train == 5
    np.testing.assert_allclose(actual.covariance, original.covariance, rtol=1e-14)
    np.testing.assert_allclose(
        [candidate.score for candidate in actual.candidates],
        [candidate.score for candidate in original.candidates],
        rtol=1e-14,
    )


def test_identity_ties_prefer_smallest_alpha_and_no_variance_fallback():
    result = estimate_from_raw(
        np.eye(2), np.eye(2), n_train=2, alpha_candidates=[1, 0.2, 0]
    )
    assert result.alpha_selected == 0
    with pytest.raises(CovarianceEstimationError):
        estimate_from_raw(
            np.zeros((2, 2)), np.eye(2), n_train=2, alpha_candidates=[0, 1]
        )


def test_full_matrix_rank_bound_is_not_applied_to_toeplitz_segment_count():
    full = estimate_from_raw(
        np.eye(3),
        np.eye(3),
        n_train=1,
        structural_rank_bound=1,
        alpha_candidates=[0, 1],
    )
    assert full.candidates[0].reason == "structurally_singular"
    stationary = estimate_from_raw(
        np.eye(3),
        np.eye(3),
        n_train=1,
        alpha_candidates=[0, 1],
        method=WELCH_METHOD,
    )
    assert stationary.candidates[0].eligible
    assert stationary.alpha_selected == 0


def test_stream_welch_matches_independent_batched_reference():
    t = np.arange(160, dtype=np.float64)
    values = np.sin(2 * np.pi * t / 11) + 0.3 * np.cos(t / 7) + 0.2
    actual = welch_covariance(
        values, n_samples=7, sample_rate_hz=64, nperseg=32, noverlap=16
    )
    frequency, expected_psd = welch(
        values,
        fs=64,
        window="hann_periodic",
        nperseg=32,
        noverlap=16,
        detrend=False,
        scaling="density",
        average="mean",
    )
    np.testing.assert_array_equal(actual.frequencies_hz, frequency)
    np.testing.assert_allclose(actual.psd, expected_psd, rtol=5e-15, atol=1e-17)
    two_sided = expected_psd.copy()
    two_sided[1:-1] /= 2
    # A direct cosine sum checks the inverse FFT normalization independently.
    k = np.arange(7)
    expected_acf = (
        64
        / 32
        * (
            two_sided[0]
            + two_sided[-1] * (-1.0) ** k
            + 2
            * np.sum(
                two_sided[1:-1, None]
                * np.cos(2 * np.pi * np.arange(1, 16)[:, None] * k / 32),
                axis=0,
            )
        )
    )
    np.testing.assert_allclose(actual.acf, expected_acf, atol=3e-16, rtol=4e-15)
    np.testing.assert_allclose(
        actual.raw_covariance, toeplitz(expected_acf), atol=3e-16, rtol=4e-15
    )
    assert actual.segments == 9
    assert actual.n_train_samples == 160


def test_welch_dc_is_not_removed_or_recalibrated():
    actual = welch_covariance(np.full(64, 2.0), n_samples=4, nperseg=32, noverlap=16)
    assert actual.acf[0] == pytest.approx(4.0, rel=1e-15)
    assert actual.psd[0] > 0
    assert actual.method == WELCH_METHOD


def test_welch_rejects_partial_or_nonfinite_segments():
    with pytest.raises(ValueError):
        welch_covariance(np.ones(65), n_samples=4, nperseg=32, noverlap=16)
    values = np.ones(64)
    values[-1] = np.nan
    with pytest.raises(ValueError):
        welch_covariance(values, n_samples=4, nperseg=32, noverlap=16)
