"""Evaluate residual losses with a fixed, explicitly supplied covariance."""

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import LinAlgError, cholesky, norm, solve_triangular


def _real_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """Require finite real numeric input without accepting strings or booleans."""
    try:
        array = np.asarray(values)
        if not np.issubdtype(array.dtype, np.number) or np.iscomplexobj(array):
            raise ValueError(f"{name} must contain real numbers.")
        with np.errstate(over="raise", invalid="raise"):
            array = array.astype(np.float64, copy=False)
    except (TypeError, ValueError, FloatingPointError, OverflowError) as error:
        raise ValueError(f"{name} must contain finite real numbers.") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite real numbers.")
    return array


def _residual_vector(residual: ArrayLike) -> NDArray[np.float64]:
    values = _real_array(residual, "residual")
    if values.ndim != 1 or values.size == 0:
        raise ValueError("residual must be a nonempty one-dimensional array.")
    return values


def _squared_norm(values: NDArray[np.float64], divisor: int) -> float:
    """Use the scaled BLAS norm and divide before squaring."""
    value = float(norm(values, check_finite=False)) / math.sqrt(divisor)
    result = value * value
    if not math.isfinite(result):
        raise ValueError("The loss exceeds the finite float64 range.")
    return result


def mean_squared_error(residual: ArrayLike) -> float:
    """Return sum(residual**2) / N for an explicitly supplied residual vector."""
    values = _residual_vector(residual)
    return _squared_norm(values, values.size)


class CovarianceLoss:
    """Cache a Cholesky factor for a fixed positive-definite covariance.

    Covariance must be a finite, nonempty, real square matrix with exactly
    symmetric float64 entries. No symmetrization, regularization, matrix
    inversion, or data-dependent covariance estimation is performed.
    The caller chooses explicitly between the quadratic form and its
    value per sample. A new covariance requires a new instance.
    """

    def __init__(self, covariance: ArrayLike) -> None:
        matrix = _real_array(covariance, "covariance")
        if (
            matrix.ndim != 2
            or matrix.shape[0] == 0
            or matrix.shape[0] != matrix.shape[1]
        ):
            raise ValueError("covariance must be a nonempty square matrix.")
        if not np.array_equal(matrix, matrix.T):
            raise ValueError("covariance must be symmetric.")
        try:
            self._factor = cholesky(
                matrix, lower=True, overwrite_a=False, check_finite=False
            )
        except LinAlgError as error:
            raise ValueError("covariance must be positive definite.") from error
        if not np.all(np.isfinite(self._factor)):
            raise ValueError("The covariance factor exceeds the finite float64 range.")
        self._factor.setflags(write=False)

    @property
    def n_samples(self) -> int:
        """Return the dimension of the covariance matrix."""
        return self._factor.shape[0]

    def whiten(self, residual: ArrayLike) -> NDArray[np.float64]:
        """Return z solving L @ z = residual, where covariance = L @ L.T."""
        values = _residual_vector(residual)
        if values.size != self.n_samples:
            raise ValueError("residual length must match the covariance dimension.")
        transformed = solve_triangular(
            self._factor, values, lower=True, overwrite_b=False, check_finite=False
        )
        if not np.all(np.isfinite(transformed)):
            raise ValueError("The whitened residual exceeds the finite float64 range.")
        return transformed

    def quadratic_form(self, residual: ArrayLike) -> float:
        """Return residual.T @ inv(covariance) @ residual without inversion."""
        return _squared_norm(self.whiten(residual), 1)

    def mean_squared(self, residual: ArrayLike) -> float:
        """Return the covariance quadratic form divided by the sample count."""
        return _squared_norm(self.whiten(residual), self.n_samples)
