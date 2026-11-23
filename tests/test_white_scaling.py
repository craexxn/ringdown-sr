"""Independent checks of the frozen pilot's design and numerical identities."""

import math

import numpy as np
import pytest

from ringdown_sr import white_scaling as pilot


def test_design_is_paired_with_one_preselected_repeat():
    cells = pilot.cells()
    primary = [cell for cell in cells if not cell["repeat"]]
    assert len(primary) == 18
    assert len(cells) == 21
    assert len({cell["id"] for cell in cells}) == 21
    for case in (1, 2):
        for seed in pilot.SEARCH_SEEDS:
            assert {
                cell["arm"]
                for cell in primary
                if cell["case"] == case and cell["seed"] == seed
            } == {"ordinary", "scaled", "covariance"}
    assert all(
        cell["case"] == 1 and cell["seed"] == pilot.SEARCH_SEEDS[0]
        for cell in cells
        if cell["repeat"]
    )


def test_data_formula_and_raster_roles_are_independently_reproducible():
    arrays = pilot.data()
    times = arrays["time_s"]
    assert len(times) == 128
    assert np.array_equal(times, np.arange(128) / 4096)
    reference = np.array(
        [
            (11 / 12)
            * math.exp(-150 * float(t))
            * math.cos(530 * math.pi * float(t) + 0.25)
            for t in times
        ]
    )
    np.testing.assert_allclose(arrays["truth"], reference, rtol=1e-13, atol=1e-15)
    assert not np.array_equal(arrays["observed_1"], arrays["observed_2"])
    assert len(arrays["regular_time_s"]) == 889
    assert len(arrays["irregular_time_s"]) == 1024
    assert np.all(np.diff(arrays["irregular_time_s"]) > 0)
    assert not set(times).intersection(arrays["irregular_time_s"])
    assert all(
        np.array_equal(value, pilot.data()[key]) for key, value in arrays.items()
    )


def test_start_policy_has_no_truth_frequency_tuning():
    starts = pilot.starts(np.array([-2.0, 1.0]))
    assert len(starts) == 4
    assert all(start[0] == 2.0 and start[3] == math.pi / 2 for start in starts)
    assert {start[2] / (2 * math.pi) for start in starts} == {128.0, 512.0}
    assert {start[1] for start in starts} == {-256.0, -64.0}


def test_positive_scaling_preserves_fixed_candidate_order():
    residuals = [np.array([0.125, -0.25, 0.5]), np.array([0.5, -1.0, 0.25])]
    scale = 1 / pilot.SIGMA**2
    mse = [math.fsum(float(r) ** 2 for r in residual) / 3 for residual in residuals]
    covariance_loss = [
        math.fsum((float(r) / pilot.SIGMA) ** 2 for r in residual) / 3
        for residual in residuals
    ]
    np.testing.assert_allclose(covariance_loss, np.array(mse) * scale, rtol=5e-16)
    assert np.argmin(mse) == np.argmin(covariance_loss)


def test_offgrid_pole_is_reported_and_finite_points_are_preserved():
    one = {"kind": "constant", "value_hex": (1.0).hex()}
    half = {"kind": "constant", "value_hex": (0.5).hex()}
    variable = {"kind": "variable", "index": 1}
    denominator = {
        "kind": "operator",
        "arity": 2,
        "operator_index": 2,
        "operator": "-",
        "children": [variable, half],
    }
    tree = {
        "kind": "operator",
        "arity": 2,
        "operator_index": 4,
        "operator": "/",
        "children": [one, denominator],
    }
    values, metrics = pilot.evaluate_grid(tree, [0.0, 0.5, 1.0], np.zeros(3))
    assert values[0] == -2 and np.isnan(values[1]) and values[2] == 2
    assert metrics == {
        "status": "nonfinite_prediction",
        "nonfinite_count": 1,
        "rmse_over_a": None,
        "max_over_a": None,
    }
    _, training = pilot.evaluate_grid(tree, [0.0, 1.0], np.zeros(2))
    assert training["status"] == "finite"


def test_large_finite_values_do_not_overflow_by_squaring():
    tree = {"kind": "constant", "value_hex": (1e200).hex()}
    _, metrics = pilot.evaluate_grid(tree, [0.0, 1.0], np.zeros(2))
    assert metrics["status"] == "finite"
    assert math.isclose(metrics["rmse_over_a"], 1e200 / pilot.AMPLITUDE)
    with pytest.raises(ValueError, match="finite"):
        pilot.evaluate_grid({"kind": "constant", "value_hex": "inf"}, [0.0], [0.0])
