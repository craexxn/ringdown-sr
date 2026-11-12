"""Check the frozen coordinate experiment against independent physical inputs."""

import importlib
import io
import json
import subprocess
from fractions import Fraction

import numpy as np
import pytest

from ringdown_sr import time_budget_profile as native
from ringdown_sr.symbolic import ROOT


@pytest.fixture
def profile():
    return importlib.import_module("ringdown_sr.time_coordinate_profile")


def generator():
    return native.load_module(
        ROOT / "scripts/prepare_time_coordinate_inputs.py", "coordinate_input_generator"
    )


def test_generator_reproduces_bound_files_without_changing_search_rng():
    configuration = json.loads(
        (ROOT / "data/time_coordinate_protocol.json").read_bytes()
    )
    np.random.seed(912)
    before = np.random.get_state()
    outputs, actual = generator().prepare(ROOT, configuration["base_commit"])
    after = np.random.get_state()
    assert before[0] == after[0]
    assert np.array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert actual == configuration
    for name, raw in outputs.items():
        assert raw == (ROOT / name).read_bytes()
    assert actual["generation"]["truth_regenerated"] is False
    assert [arm["unit"] for arm in actual["arms"]] == ["s", "s"]


def test_inputs_preserve_every_physical_bit_and_scale_all_three_axes_exactly():
    configuration = json.loads(
        (ROOT / "data/time_coordinate_protocol.json").read_bytes()
    )
    source = configuration["source"]
    old = subprocess.check_output(
        ["git", "show", source["commit"] + ":" + source["inputs_path"]], cwd=ROOT
    )
    pairs = (
        ("time_s", "time_u"),
        ("diagnostic_time_s", "diagnostic_time_u"),
        ("irregular_time_s", "irregular_time_u"),
    )
    checked = 0
    with (
        np.load(io.BytesIO(old), allow_pickle=False) as physical,
        np.load(ROOT / "data/time_coordinate_inputs.npz", allow_pickle=False) as new,
    ):
        assert set(new.files) == set(physical.files) | {b for _, b in pairs}
        for name in physical.files:
            assert new[name].dtype == physical[name].dtype
            assert new[name].shape == physical[name].shape
            assert new[name].tobytes() == physical[name].tobytes()
        for original, transformed in pairs:
            for t, u in zip(physical[original], new[transformed], strict=True):
                assert Fraction(float(u)) == 32 * Fraction(float(t))
                checked += 1
            assert (
                np.ldexp(new[transformed], -5).tobytes() == physical[original].tobytes()
            )
        assert new["time_s"][-1] == 127 / 4096
        assert new["time_u"][-1] == 127 / 128
    assert checked == 2041


def test_generator_requires_an_immutable_full_commit():
    with pytest.raises(ValueError, match="complete immutable"):
        generator().prepare(ROOT, "HEAD")


def test_sixteen_calls_are_eight_disjoint_paired_blocks_with_fixed_order(profile):
    expected = {"anchor": 2, "variant_low": 2, "variant_high": 4}
    assert profile.names() == list(expected)
    seeds = set()
    count = 0
    for name, blocks in expected.items():
        plans = profile.plans(name)
        assert len(plans) == 2 * blocks
        assert [p["number"] for p in plans] == list(range(1, len(plans) + 1))
        for block in range(1, blocks + 1):
            group = [p for p in plans if p["block"] == block]
            assert [p["arm"] for p in group] == (
                ["T", "U"] if block % 2 else ["U", "T"]
            )
            assert len({p["seed"] for p in group}) == 1
            seed = group[0]["seed"]
            assert type(seed) is int and 0 < seed < 2**31 and seed not in seeds
            seeds.add(seed)
            assert all(p["niterations"] == 2000 for p in group)
            assert all(p["condition"] == "iterations" for p in group)
            assert all(p["signal"] == name for p in group)
        assert profile.case(name)["seeds"] == [
            plans[2 * block]["seed"] for block in range(blocks)
        ]
        count += len(plans)
    assert count == 16 and len(seeds) == 8


@pytest.mark.parametrize(
    "name,technical", [("fixture_a", False), ("anchor", True), ("other", False)]
)
def test_signal_and_scope_cannot_be_interchanged(profile, name, technical):
    with pytest.raises(ValueError):
        profile.case(name, technical)
    with pytest.raises(ValueError):
        profile.plans(name, technical)
    with pytest.raises(ValueError):
        profile.inputs(name, technical)


def test_technical_controls_have_only_four_tiny_workers(profile):
    plans = [p for name in profile.names(True) for p in profile.plans(name, True)]
    assert len(profile.names(True)) == 2 and len(plans) == 4
    assert all(p["niterations"] == 2 for p in plans)
    assert {p["arm"] for p in plans} == {"T", "U"}
    assert all(p["block"] == 1 for p in plans)
    assert not {p["signal"] for p in plans} & set(profile.names())


@pytest.mark.parametrize("name", ["anchor", "variant_low", "variant_high"])
def test_search_coordinates_keep_truth_bits_and_physical_diagnostic_points(
    profile, name
):
    physical, grid = profile.inputs(name)
    original = {key: value.tobytes() for key, value in physical.items()}
    grid_before = {key: value.tobytes() for key, value in grid.items()}
    raw = profile.search_inputs(name, "T")
    scaled = profile.search_inputs(name, "U")
    assert set(raw) == set(scaled) == set(physical)
    for key in physical:
        assert raw[key].tobytes() == original[key]
        expected = (
            np.ldexp(physical[key], 5) if key.endswith("time_s") else physical[key]
        )
        assert scaled[key].tobytes() == expected.tobytes()
        assert not raw[key].flags.writeable and not scaled[key].flags.writeable
        assert physical[key].tobytes() == original[key]
    assert {key: value.tobytes() for key, value in grid.items()} == grid_before


@pytest.mark.parametrize("role", ["time_u", "diagnostic_time_u", "irregular_time_u"])
@pytest.mark.parametrize("fault", ["missing", "double_scale", "one_bit"])
def test_each_frozen_normalized_axis_is_bound_separately(
    profile, monkeypatch, tmp_path, role, fault
):
    configuration = profile.configuration()
    with np.load(ROOT / "data/time_coordinate_inputs.npz", allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    if fault == "missing":
        arrays.pop(role)
    elif fault == "double_scale":
        arrays[role] *= 32
    else:
        arrays[role][1] = np.nextafter(arrays[role][1], np.inf)
    (tmp_path / "data").mkdir()
    np.savez(tmp_path / "data/time_coordinate_inputs.npz", **arrays)
    # Bypass only the container hash to exercise the independent role bindings.
    monkeypatch.setattr(profile, "configuration", lambda: configuration)
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises((ValueError, KeyError)):
        profile.search_inputs("anchor", "U")


def test_unknown_coordinate_arm_cannot_choose_a_default(profile, tmp_path):
    for arm in ("u", "I", "R", "", None):
        with pytest.raises(ValueError):
            profile.search_inputs("anchor", arm)
        with pytest.raises(ValueError):
            profile.search_path(tmp_path, {"arm": arm})


@pytest.mark.parametrize("fault", ["missing", "changed"])
def test_frozen_protocol_tampering_is_rejected(profile, monkeypatch, tmp_path, fault):
    for name in profile.PLAN_HASHES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    target = tmp_path / "data/time_coordinate_inputs.npz"
    if fault == "missing":
        target.unlink()
    else:
        target.write_bytes(target.read_bytes() + b"changed")
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises((ValueError, OSError)):
        profile.configuration()
