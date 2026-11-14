"""Validate opt-in fixed-profile configuration without altering older schemas."""

from pathlib import Path

import pytest

from ringdown_sr.config import (
    CONFIRMED_PROFILE,
    ConfirmedPilotConfig,
    load_config,
    parse_config,
)
from ringdown_sr.pilot import run_pilot
from ringdown_sr.symbolic_pilot import _reference_toml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "configs/pilot_confirmed_ar1.toml"


def test_fixed_profile_has_only_named_contract_and_four_seeds():
    config = load_config(EXAMPLE)
    assert isinstance(config, ConfirmedPilotConfig)
    assert config.schema_version == 4
    assert config.confirmed_search.profile == CONFIRMED_PROFILE
    assert config.confirmed_search.seeds == (
        2026111401,
        2026111402,
        2026111403,
        2026111404,
    )
    assert set(config.to_dict()["confirmed_search"]) == {"profile", "seeds"}
    reference = load_config(ROOT / "configs/pilot_estimated_ar1.toml")
    assert config.reference_config() == reference
    assert parse_config(_reference_toml(config.reference_config())) == reference


@pytest.mark.parametrize(
    "replacement",
    [
        "[1, 2, 3]",
        "[1, 2, 3, 4, 5]",
        "[1, 2, 3, 3]",
        "[0, 2, 3, 4]",
        "[-1, 2, 3, 4]",
        "[true, 2, 3, 4]",
        "[1.0, 2, 3, 4]",
        "[2147483648, 2, 3, 4]",
        "[42, 2, 3, 4]",
        "[20261019, 2, 3, 4]",
        '"1234"',
    ],
)
def test_bad_seed_blocks_never_reserve_output(tmp_path, replacement):
    raw = EXAMPLE.read_text().replace(
        "[2026111401, 2026111402, 2026111403, 2026111404]", replacement
    )
    path = tmp_path / "config.toml"
    path.write_text(raw)
    with pytest.raises((ValueError, TypeError)):
        run_pilot(path, tmp_path / "result")
    assert not (tmp_path / "result").exists()


@pytest.mark.parametrize(
    "old,new",
    [
        ('profile = "r4x1000-local300x5-v1"', 'profile = "r4x2000-local300x5-v1"'),
        (
            'profile = "r4x1000-local300x5-v1"',
            'profile = "r4x1000-local300x5-v1"\nniterations = 1',
        ),
        (
            'profile = "r4x1000-local300x5-v1"',
            'profile = "r4x1000-local300x5-v1"\nshould_simplify = true',
        ),
        (
            'profile = "r4x1000-local300x5-v1"',
            'profile = "r4x1000-local300x5-v1"\ntechnical = true',
        ),
        ("standard_deviation = 0.1", "standard_deviation = 0.0"),
        ("standard_deviation = 0.1", "standard_deviation = 1e-300"),
    ],
)
def test_profile_tuning_and_degenerate_covariance_are_rejected(old, new):
    with pytest.raises((ValueError, TypeError)):
        parse_config(EXAMPLE.read_text().replace(old, new).encode())


def test_schema3_stays_opt_in_to_its_original_budget():
    for name in ("white", "ar1"):
        config = load_config(ROOT / f"configs/pilot_sr_{name}.toml")
        assert config.schema_version == 3
        assert config.symbolic_search.niterations == 10
        assert "confirmed_search" not in config.to_dict()


def test_schema4_cannot_enter_historical_supplemental_route(tmp_path):
    with pytest.raises(ValueError, match="schema-3"):
        run_pilot(
            EXAMPLE, tmp_path / "result", assessment_output=tmp_path / "assessment"
        )
    assert not (tmp_path / "result").exists()
