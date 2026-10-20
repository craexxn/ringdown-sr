"""Reject ambiguous schema mixing and invalid background/selection inputs."""

from pathlib import Path

import pytest

from ringdown_sr.config import CovariancePilotConfig, load_config, parse_config
from ringdown_sr.pilot import run_pilot

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = (ROOT / "configs/pilot_estimated_ar1.toml").read_text()


@pytest.mark.parametrize("name", ["white", "ar1"])
def test_schema_two_examples_resolve_all_explicit_background_and_selection_fields(name):
    config = load_config(ROOT / f"configs/pilot_estimated_{name}.toml")
    assert isinstance(config, CovariancePilotConfig) and config.schema_version == 2
    assert config.fit.weighting == "compare_covariances"
    assert (
        config.background.n_train,
        config.background.n_validation,
        config.background.n_check,
    ) == (64, 128, 256)
    assert config.background.seed == 20261019 and config.noise.seed == 42
    assert config.covariance_estimation.mean_mode == "known_zero"
    assert config.covariance_estimation.alpha_candidates == (
        0,
        0.001,
        0.01,
        0.05,
        0.1,
        0.2,
        0.5,
        1,
    )
    assert config.covariance_estimation.kappa_max == 1e8


@pytest.mark.parametrize(
    "old,new",
    [
        ("schema_version = 2", "schema_version = 1"),
        ("schema_version = 2", "schema_version = 3"),
        ('weighting = "compare_covariances"', 'weighting = "estimated_covariance"'),
        ("n_train = 64", "n_train = 0"),
        ("n_validation = 128", "n_validation = -1"),
        ("n_check = 256", "n_check = true"),
        ("n_train = 64", "n_train = 64.0"),
        ("seed = 20261019", "seed = -1"),
        ('stream_scheme = "seedsequence_role_v1"', 'stream_scheme = "unspecified"'),
        ('mean_mode = "known_zero"', 'mean_mode = "centered"'),
        ("kappa_max = 1e8", "kappa_max = 1.0"),
        ("kappa_max = 1e8", "kappa_max = true"),
        ("kappa_max = 1e8", "kappa_max = inf"),
        ("standard_deviation = 0.1", "standard_deviation = 0.0"),
        ("standard_deviation = 0.1", "standard_deviation = 1e-200"),
        ("kappa_max = 1e8", "unknown = 3\nkappa_max = 1e8"),
        ("[background]", "[other_background]"),
        ("[covariance_estimation]", "[other_estimator]"),
    ],
)
def test_invalid_schema_two_input_is_rejected_before_creating_output(
    tmp_path, old, new
):
    config = tmp_path / "bad.toml"
    config.write_text(EXAMPLE.replace(old, new))
    output = tmp_path / "must-not-exist"
    with pytest.raises((ValueError, TypeError)):
        run_pilot(config, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "grid", ["[]", "[0.5, 0.5]", "[true, 0.5]", "[-0.1, 1]", "[0, 1.1]", "[nan]", "0.5"]
)
def test_invalid_selection_grid_is_not_normalized_or_repaired(grid):
    text = EXAMPLE.replace("[0.0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]", grid)
    with pytest.raises((ValueError, TypeError)):
        parse_config(text.encode())
