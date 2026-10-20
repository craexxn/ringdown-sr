"""Reject overlapping initial streams before reserving output or generating data."""

from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from ringdown_sr import background, covariance_pilot
from ringdown_sr.pilot import run_pilot

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("kind", ["white", "ar1"])
@pytest.mark.parametrize("role,role_id", [("validation", 1), ("check", 2)])
def test_colliding_signal_and_background_seeds_are_rejected_before_output_or_data(
    kind, role, role_id, tmp_path, monkeypatch
):
    background_seed = 20261019
    signal_seed = background_seed + role_id * 2**128
    # Independent reproduction of the SeedSequence representation overlap.
    direct = np.random.PCG64(signal_seed)
    child = np.random.PCG64(
        np.random.SeedSequence(background_seed, spawn_key=(role_id,), pool_size=4)
    )
    assert direct.state == child.state
    text = (ROOT / f"configs/pilot_estimated_{kind}.toml").read_text()
    config = tmp_path / "collision.toml"
    config.write_text(text.replace("seed = 42", f"seed = {signal_seed}"))
    output = tmp_path / "must-not-exist"

    def forbidden(*args, **kwargs):
        pytest.fail("Colliding initial states must be rejected before data generation")

    monkeypatch.setattr(covariance_pilot, "sample_times", forbidden)
    monkeypatch.setattr(covariance_pilot, "draw_noise_window", forbidden)
    with pytest.raises(ValueError, match=f"states.*signal.*{role}"):
        run_pilot(config, output)
    assert not output.exists()


@pytest.mark.parametrize("signal_seed", [42, 2**160 + 9])
def test_checked_generators_retain_existing_derivation_and_allow_large_distinct_seeds(
    signal_seed,
):
    before = np.random.get_state()
    generators = background.pilot_generators(signal_seed, 20261019)
    assert set(generators) == {"signal", "train", "validation", "check"}
    assert (
        generators["signal"].bit_generator.state == np.random.PCG64(signal_seed).state
    )
    states = []
    for role, role_id in (("train", 0), ("validation", 1), ("check", 2)):
        expected = np.random.PCG64(
            np.random.SeedSequence(20261019, spawn_key=(role_id,), pool_size=4)
        ).state
        assert generators[role].bit_generator.state == expected
    for rng in generators.values():
        assert all(rng.bit_generator.state != previous for previous in states)
        states.append(rng.bit_generator.state)
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])


def test_collision_between_two_background_roles_is_also_rejected(monkeypatch):
    # Model an erroneous future role mapping; the guard must compare all four
    # states, including pairs that do not involve signal noise.
    monkeypatch.setitem(background.ROLE_IDS, "check", background.ROLE_IDS["train"])
    with pytest.raises(ValueError, match="states.*train.*check"):
        background.pilot_generators(42, 20261019)
