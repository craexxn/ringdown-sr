"""Check Julia loss and constant optimization against independent Python references."""

import os
from pathlib import Path

import numpy as np

from ringdown_sr.losses import CovarianceLoss, mean_squared_error


def check_constant_optimization(jl) -> None:
    cases = jl.ConstantOptimizationChecks.REPLAY_CASES
    assert len(cases) == 12, "Missing constant-optimization reference runs."
    for case in cases:
        time = np.asarray(case.time, dtype=np.float64)
        observed = np.asarray(case.observed, dtype=np.float64)
        model = str(case.model)
        if model == "constant":
            design = np.ones((time.size, 1))
        elif model == "linear":
            design = np.column_stack((np.ones(time.size), time))
        else:
            raise AssertionError(f"Unknown reference model: {model}")
        covariance = (
            np.eye(time.size)
            if case.covariance is None
            else np.asarray(case.covariance, dtype=np.float64)
        )
        # Independent GLS normal equations: no production whitening or optimizer.
        expected = np.linalg.solve(
            design.T @ np.linalg.solve(covariance, design),
            design.T @ np.linalg.solve(covariance, observed),
        )
        expected_residual = observed - design @ expected
        expected_loss = (
            expected_residual @ np.linalg.solve(covariance, expected_residual)
        ) / time.size
        result = case.result
        parameters = np.asarray(result.parameters, dtype=np.float64)
        prediction = np.asarray(result.prediction, dtype=np.float64)
        loss = float(result.loss)
        label = f"{model}/{case.weighting}, start={result.initial_parameters}"
        # Predeclared convergence tolerances; stricter rounding bounds below.
        np.testing.assert_allclose(
            parameters, expected, rtol=0, atol=1e-6, err_msg=label
        )
        np.testing.assert_allclose(
            loss, expected_loss, rtol=0, atol=1e-11, err_msg=label
        )
        np.testing.assert_allclose(
            prediction,
            design @ parameters,
            rtol=32 * np.finfo(np.float64).eps,
            atol=32 * np.finfo(np.float64).eps,
            err_msg=label,
        )
        residual = observed - prediction
        replay = (residual @ np.linalg.solve(covariance, residual)) / time.size
        rtol = 64 * np.finfo(np.float64).eps * np.linalg.cond(covariance)
        np.testing.assert_allclose(loss, replay, rtol=rtol, atol=0, err_msg=label)
        print(f"Optimizer replay {label}: parameters={parameters}, loss={loss:.17g}")
    print(f"Python/Julia constant-optimization replay passed: {len(cases)} cases.")


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
    check_constant_optimization(jl)
    print("Julia loss kernel check passed.")


if __name__ == "__main__":
    main()
