"""Independent weighted reductions and corruption boundaries, without fits."""

import copy
from fractions import Fraction

import numpy as np
import pytest
from scipy.linalg import solve_triangular
from test_structure import constant as c
from test_structure import operator as op
from test_structure import time_node as t

from ringdown_sr import prediction_reference, symbolic
from ringdown_sr import weighted_replay as replay
from ringdown_sr.losses import CovarianceLoss, mean_squared_error


def arguments(covariance, observed, *, native=None, python=None, tree=None):
    covariance = np.asarray(covariance, dtype=float)
    observed = np.asarray(observed, dtype=float)
    times = np.arange(1, observed.size + 1, dtype=float) / 32
    tree = c(0) if tree is None else tree
    python = symbolic.evaluate_tree(tree, times) if python is None else python
    native = python.copy() if native is None else native
    loss = CovarianceLoss(covariance)
    factor = loss._factor.copy()
    native_whitened = solve_triangular(factor, observed - native, lower=True)
    native_loss = mean_squared_error(native_whitened)
    return {
        "observed": observed,
        "native_prediction": native,
        "python_prediction": python,
        "raw_loss": native_loss,
        "replay_loss": native_loss,
        "table_loss": native_loss,
        "python_loss": loss.mean_squared(observed - python),
        "loss_object": loss,
        "prediction_check": prediction_reference.verify_prediction(
            tree, times, python, native
        ),
        "covariance": covariance,
        "native_factor": factor,
        "native_whitened": native_whitened,
    }


def fraction(record):
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def test_hand_computed_non_diagonal_q_over_n():
    # L = [[2,0],[1,1]], r = [2,3], L^-1 r = [1,2], Q/N = 5/2.
    args = arguments([[4, 2], [2, 2]], [2, 3])
    result = replay.verify_loss_replay(**args)
    assert result["metric"] == "covariance_q_over_n"
    assert fraction(result["native_reduction_reference"]) == Fraction(5, 2)
    assert fraction(result["python_reduction_reference"]) == Fraction(5, 2)
    assert result["native_reduction"] == pytest.approx(2.5)
    assert "no_forward_Q_accuracy" in result["claim"]
    assert result["factor_checks"]["native"]["covariance"] == replay._fingerprint(
        args["covariance"]
    )


@pytest.mark.parametrize("n", [1, 8, 128])
@pytest.mark.parametrize("exponent", [-100, 0, 100])
def test_white_covariance_scales_exact_q_without_an_absolute_tolerance(n, exponent):
    # C = 4 I and all r = 2^k; exact Q/N = 2^(2k-2).
    args = arguments(4 * np.eye(n), np.full(n, 2.0**exponent))
    result = replay.verify_loss_replay(**args)
    assert fraction(result["native_reduction_reference"]) == Fraction(2) ** (
        2 * exponent - 2
    )
    assert fraction(result["reduction_gamma"]) == replay._gamma(n + 2)


@pytest.mark.parametrize("rho", [0.0, 0.7, -0.8])
def test_ar1_whitening_matches_independent_innovations_formula(rho):
    n = 16
    sigma = 0.5
    residual = np.sin(np.arange(n) + 0.5) / 8
    covariance = sigma**2 * rho ** np.abs(np.arange(n)[:, None] - np.arange(n))
    result = replay.verify_loss_replay(**arguments(covariance, residual))
    innovations = np.r_[
        residual[0] / sigma,
        (residual[1:] - rho * residual[:-1]) / (sigma * np.sqrt(1 - rho**2)),
    ]
    reference = sum(Fraction(float(z)) ** 2 for z in innovations) / n
    assert float(fraction(result["native_reduction_reference"])) == pytest.approx(
        float(reference), rel=5e-15, abs=0
    )


def test_mpfr_bound_one_ulp_difference_does_not_compare_tiny_losses_relatively():
    n = 8
    times = np.arange(1, n + 1) / 32
    tree = op("sin", t())
    python = symbolic.evaluate_tree(tree, times)
    intervals = prediction_reference.reference(tree, times)["intervals_hex"]
    native = np.array([float.fromhex(pair[1]) for pair in intervals])
    observed = python + 2.0**-40
    covariance = 0.01 * 0.7 ** np.abs(np.arange(n)[:, None] - np.arange(n))
    args = arguments(covariance, observed, native=native, python=python, tree=tree)
    with pytest.raises(AssertionError):
        symbolic._verify_loss_replay(
            *(
                args[key]
                for key in (
                    "observed",
                    "native_prediction",
                    "python_prediction",
                    "raw_loss",
                    "replay_loss",
                    "table_loss",
                    "python_loss",
                    "loss_object",
                )
            )
        )
    snapshot = {
        key: value.copy()
        for key, value in args.items()
        if isinstance(value, np.ndarray)
    }
    result = replay.verify_loss_replay(**args)
    assert result["status"] == "passed"
    assert result["absolute_loss_difference"] > args["raw_loss"] * 1e-10
    for key, value in snapshot.items():
        np.testing.assert_array_equal(value.view(np.uint64), args[key].view(np.uint64))


@pytest.mark.parametrize(
    "fault", ["raw_and_reimport", "raw", "reimport", "python", "table"]
)
def test_loss_tampering_cannot_hide_behind_prediction_agreement(fault):
    args = arguments([[4, 2], [2, 2]], [2, 3])
    fields = {
        "raw_and_reimport": ("raw_loss", "replay_loss", "table_loss"),
        "raw": ("raw_loss",),
        "reimport": ("replay_loss",),
        "python": ("python_loss",),
        "table": ("table_loss",),
    }[fault]
    for name in fields:
        args[name] *= 1 + (1e-6 if fault == "table" else 1e-11)
    with pytest.raises((AssertionError, ValueError)):
        replay.verify_loss_replay(**args)


@pytest.mark.parametrize(
    "fault", ["covariance", "factor", "whitening", "python_factor"]
)
def test_self_consistent_wrong_weighting_is_rejected(fault):
    args = arguments([[4, 2], [2, 2]], [2, 3])
    if fault == "covariance":
        args["covariance"] *= 2
    elif fault == "factor":
        args["native_factor"] *= 2
        args["native_whitened"] /= 2
    elif fault == "whitening":
        args["native_whitened"] *= 2
    else:
        args["loss_object"] = CovarianceLoss(2 * args["covariance"])
        args["python_loss"] = args["loss_object"].mean_squared(args["observed"])
    for name in ("raw_loss", "replay_loss", "table_loss"):
        args[name] = mean_squared_error(args["native_whitened"])
    with pytest.raises(ValueError, match="backward-error"):
        replay.verify_loss_replay(**args)


def test_exact_zero_residual_requires_exact_zero_losses():
    args = arguments([[4, 2], [2, 2]], [0, 0])
    assert replay.verify_loss_replay(**args)["native_reduction"] == 0
    args.update(raw_loss=1e-30, replay_loss=1e-30, table_loss=1e-30)
    with pytest.raises(ValueError, match="own residual"):
        replay.verify_loss_replay(**args)


def test_factor_cache_is_bound_to_all_covariance_and_factor_bits():
    args = arguments([[4, 2], [2, 2]], [2, 3])
    first = replay.verify_loss_replay(**args)
    first["factor_checks"]["native"]["status"] = "corrupted_by_caller"
    assert (
        replay.verify_loss_replay(**args)["factor_checks"]["native"]["status"]
        == "passed"
    )
    args["native_factor"][1, 0] += 1e-8
    with pytest.raises(ValueError, match="backward-error"):
        replay.verify_loss_replay(**args)


def test_mutated_covariance_wrong_shape_and_failed_factor_are_never_cached(monkeypatch):
    replay._FACTOR_CACHE.clear()
    args = arguments([[4, 2], [2, 2]], [2, 3])
    product_certificate = replay._product_certificate
    factor_checks = []

    def tracked(a, b, target):
        if b.ndim == 2:
            factor_checks.append(target.copy())
        return product_certificate(a, b, target)

    monkeypatch.setattr(replay, "_product_certificate", tracked)
    replay.verify_loss_replay(**args)
    # Identical native/Python factors share their fully bit-bound certificate.
    assert len(factor_checks) == 1
    replay.verify_loss_replay(**args)
    assert len(factor_checks) == 1
    original_covariance = args["covariance"].copy()
    args["covariance"][1, 1] += 1e-8
    for _ in range(2):
        with pytest.raises(ValueError, match="backward-error"):
            replay.verify_loss_replay(**args)
    assert len(factor_checks) == 3
    args["covariance"] = original_covariance.reshape(1, 4)
    with pytest.raises(ValueError, match="shape"):
        replay.verify_loss_replay(**args)
    assert len(factor_checks) == 3


def test_product_certificate_encloses_exact_rational_residual_with_cancellation():
    factor = np.array([[1, 0, 0], [1, 2.0**-15, 0], [-1, 2.0**-15, 1]])
    covariance = factor @ factor.T
    result = replay._product_certificate(factor, factor.T, covariance)
    exact_relative = []
    for i in range(3):
        for j in range(3):
            terms = [
                Fraction(float(factor[i, k])) * Fraction(float(factor[j, k]))
                for k in range(3)
            ]
            absolute = sum(abs(term) for term in terms)
            if absolute:
                exact_relative.append(
                    abs(sum(terms) - Fraction(float(covariance[i, j]))) / absolute
                )
    assert max(exact_relative) <= Fraction(
        result["max_relative_residual_upper_on_positive_product_lower_bounds"]
    )
    assert Fraction(
        result["max_relative_residual_upper_on_positive_product_lower_bounds"]
    ) <= fraction(result["backward_error_gamma"])


@pytest.mark.parametrize("fault", ["missing", "wrong_format", "failed"])
def test_bounded_mpfr_prediction_proof_is_mandatory(fault):
    args = arguments(np.eye(2), [1, 2])
    if fault == "missing":
        args["prediction_check"] = None
    else:
        args["prediction_check"]["format" if fault == "wrong_format" else "status"] = (
            "wrong"
        )
    with pytest.raises(ValueError, match="bounded prediction"):
        replay.verify_loss_replay(**args)


@pytest.mark.parametrize(
    "fault",
    ["nonsymmetric", "upper", "negative_diag", "missing_factor", "missing_whitening"],
)
def test_malformed_weighting_evidence_fails_closed(fault):
    args = arguments([[4, 2], [2, 2]], [2, 3])
    if fault == "nonsymmetric":
        args["covariance"][0, 1] += 1
    elif fault == "upper":
        args["native_factor"][0, 1] = 1
    elif fault == "negative_diag":
        args["native_factor"][0, 0] *= -1
    elif fault == "missing_factor":
        args["native_factor"] = None
    else:
        args["native_whitened"] = None
    with pytest.raises(ValueError):
        replay.verify_loss_replay(**args)


@pytest.mark.parametrize("factor", [2.0**-520, 2.0**520])
def test_nonzero_or_overflowing_product_cannot_be_claimed_as_zero(factor):
    with pytest.raises(ValueError, match="backward-error|finite Float64"):
        replay._product_certificate(
            np.array([[factor]]), np.array([[factor]]), np.zeros((1, 1))
        )


def test_subnormal_factor_entries_have_a_derived_underflow_bound():
    subnormal = float.fromhex("0x0.0000000000001p-1022")
    args = arguments([[1, subnormal], [subnormal, 1]], [1, 2])
    result = replay.verify_loss_replay(**args)
    evidence = result["factor_checks"]["native"]
    expected = 2 * Fraction(1, 2**1075) / (1 - 2 * Fraction(1, 2**53))
    assert fraction(evidence["product_underflow_bound"]) == expected
    assert fraction(evidence["backward_error_underflow_bound"]) == 2 * expected
    assert evidence["entries_without_positive_product_lower_bound"] == 2
    args["native_factor"][1, 0] = 1000 * subnormal
    with pytest.raises(ValueError, match="backward-error"):
        replay.verify_loss_replay(**args)


def test_underflow_probe_checks_actual_numpy_blas_products():
    replay._check_gradual_underflow()
    tiny = np.finfo(np.float64).tiny
    a = np.array([[tiny]])
    b = np.array([[0.5]])
    exact = Fraction(float(a[0, 0])) * Fraction(float(b[0, 0]))
    assert Fraction(float((a @ b)[0, 0])) == exact
    certificate = replay._product_certificate(a, b, a @ b)
    assert certificate["status"] == "passed"


def test_subnormal_whitened_squares_fail_closed():
    args = arguments(np.eye(2), [2.0**-520, 2.0**-520])
    with pytest.raises(ValueError, match="normal Float64"):
        replay.verify_loss_replay(**args)


@pytest.mark.parametrize(
    "fault", ["prediction", "table", "native_whitened", "covariance"]
)
def test_reading_parent_recomputes_mpfr_and_weighted_evidence(fault):
    args = arguments([[4, 2], [2, 2]], [2, 3])
    candidate = {
        "tree": c(0),
        "prediction": args["native_prediction"].tolist(),
        "native_whitened_residual": args["native_whitened"].tolist(),
        "loss": args["raw_loss"],
        "julia_reimport_loss": args["replay_loss"],
        "python_loss": args["python_loss"],
        "loss_replay": replay.verify_loss_replay(**args),
    }
    times = np.arange(1, 3) / 32
    actual = replay.candidate_evidence(
        candidate,
        times,
        args["observed"],
        args["covariance"],
        native_factor=args["native_factor"],
    )
    assert actual == candidate["loss_replay"]
    changed = copy.deepcopy(candidate)
    covariance = args["covariance"].copy()
    if fault == "prediction":
        changed["prediction"][0] = 1e-30
    elif fault == "table":
        changed["loss_replay"]["table_loss"] *= 1 + 1e-6
    elif fault == "native_whitened":
        changed["native_whitened_residual"][0] += 1e-8
    else:
        covariance *= 2
    with pytest.raises((ValueError, AssertionError)):
        replay.candidate_evidence(
            changed,
            times,
            args["observed"],
            covariance,
            native_factor=args["native_factor"],
        )


def test_unweighted_path_retains_the_existing_mpfr_reduction_contract():
    args = arguments(np.eye(2), [1, 2])
    args.update(
        loss_object=None, covariance=None, native_factor=None, native_whitened=None
    )
    result = replay.verify_loss_replay(**args)
    assert result["format"] == "ringdown-sr-duration-loss-replay-2"
    assert result["metric"] == "ordinary_mse"
    args["native_factor"] = np.eye(2)
    with pytest.raises(ValueError, match="must not carry"):
        replay.verify_loss_replay(**args)
