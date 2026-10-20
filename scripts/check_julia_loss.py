"""Run deterministic Julia loss tests and replay residuals against Python."""

import os
from pathlib import Path

import numpy as np

from ringdown_sr.losses import CovarianceLoss, mean_squared_error


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = root / "julia"
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(project):
        raise SystemExit("Run this check through scripts/run_python.py.")

    import pysr
    from juliacall import Main as jl
    from juliacall import convert as jl_convert

    active = Path(str(jl.seval("Base.active_project()"))).resolve()
    if active != project / "Project.toml":
        raise SystemExit(f"Unexpected Julia project: {active}")
    print("PySR:", pysr.__version__)
    print("Julia:", jl.seval("string(VERSION)"))
    print("Julia project:", active)
    jl.include(str(project / "test" / "runtests.jl"))
    kernel = jl.RingdownSRLoss

    def array(values):
        return jl_convert(jl.Array[jl.Float64], np.asarray(values, dtype=np.float64))

    covariance = np.array([[2.5, 1.5], [1.5, 4.5]])
    coupled = np.array([[2.0, 1.0], [1.0, 2.0]])
    rho = 0.999
    cases = [
        ("orientation", [1.0, 0.0], covariance),
        ("same_sign", [1.0, 1.0], coupled),
        ("opposite_sign", [1.0, -1.0], coupled),
        ("ordinary", [2.0, 4.0], None),
        ("zero", [0.0, 0.0], covariance),
        ("large_finite_mean", [1e154, 1e154], None),
        ("strong_correlation", [1.0, -1.0], [[1.0, rho], [rho, 1.0]]),
        (
            "three_samples",
            [0.3, -0.7, 1.2],
            [[4.0, 2.0, 0.0], [2.0, 5.0, 1.0], [0.0, 1.0, 3.0]],
        ),
        ("small_amplitude", [1e-21, 0.0], covariance * 1e-42),
        ("large_amplitude", [1e21, 0.0], covariance * 1e42),
    ]
    for name, residual_values, matrix_values in cases:
        residual = np.asarray(residual_values, dtype=np.float64)
        matrix = (
            None
            if matrix_values is None
            else np.asarray(matrix_values, dtype=np.float64)
        )
        context = kernel.FixedWindowLoss(
            array(np.arange(residual.size)),
            array(np.zeros(residual.size)),
            covariance=None if matrix is None else array(matrix),
        )
        actual = float(kernel.residual_loss(context, array(residual)))
        expected = (
            mean_squared_error(residual)
            if matrix is None
            else CovarianceLoss(matrix).mean_squared(residual)
        )
        condition = 1.0 if matrix is None else float(np.linalg.cond(matrix))
        rtol = 16 * residual.size * np.finfo(np.float64).eps * condition
        assert np.isfinite(actual) and np.isfinite(expected), name
        np.testing.assert_allclose(actual, expected, rtol=rtol, atol=0, err_msg=name)
        print(f"Replay {name}: {actual:.17g}")
    print(f"Python/Julia residual replay passed: {len(cases)} cases.")
    print("Julia loss kernel check passed.")


if __name__ == "__main__":
    main()
