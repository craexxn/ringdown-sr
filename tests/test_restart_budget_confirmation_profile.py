"""Independent references for the frozen new-signal confirmation profile."""

import io
import json
import random
import re
import subprocess
from fractions import Fraction

import gmpy2
import mpmath
import numpy as np
import pytest

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_budget_confirmation_profile as profile
from ringdown_sr.symbolic import ROOT

PARAMETERS = ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
SIGNALS = {
    "confirm_low": ("7/12", "685/3", "7/750", "-1/20"),
    "confirm_mid": ("11/12", "265", "1/150", "1/4"),
    "confirm_high": ("3/4", "905/3", "1/125", "-7/20"),
}


def generator():
    return profile.native.load_module(
        ROOT / "scripts/prepare_restart_budget_confirmation_inputs.py",
        "tested_confirmation_input_generator",
    )


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def test_frozen_generator_reproduces_bytes_and_preserves_all_global_random_state():
    config = profile.configuration()
    python_before, numpy_before = random.getstate(), np.random.get_state()
    precision_before = mpmath.mp.dps
    outputs, actual = generator().prepare(ROOT, config["base_commit"])
    numpy_after = np.random.get_state()
    assert random.getstate() == python_before
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert mpmath.mp.dps == precision_before
    assert sources.json_bytes(actual) == sources.json_bytes(config)
    assert set(outputs) == {
        "data/restart_budget_confirmation_protocol.json",
        "data/restart_budget_confirmation_inputs.npz",
    }
    for name, raw in outputs.items():
        assert raw == (ROOT / name).read_bytes()
    assert actual["generation"]["truth_regenerated"] is True
    assert actual["generation"]["grid_regenerated"] is True
    assert actual["generation"]["coordinate_transformed"] is False


@pytest.mark.parametrize("commit", ["HEAD", "16f2e45", profile.PLAN_COMMIT])
def test_generator_requires_the_full_frozen_source_commit(commit):
    with pytest.raises(ValueError, match="frozen complete"):
        generator().prepare(ROOT, commit)


def test_all_120_seeds_are_new_against_every_bound_positive_integer_token():
    config = profile.configuration()
    seed_config = config["seed_generator"]
    tracked = git(
        "grep",
        "-h",
        "-I",
        "-E",
        "[0-9]+",
        config["base_commit"],
        "--",
        "data",
        "docs",
        "src",
        "scripts",
        "tests",
    ).decode()
    excluded = {int(token) for token in re.findall(r"\b\d+\b", tracked)}
    excluded = {value for value in excluded if 0 < value < 2**31}
    assert seed_config["excluded_values"] == len(excluded)
    serialized = (
        json.dumps(sorted(excluded), indent=2, ensure_ascii=False) + "\n"
    ).encode()
    assert seed_config["excluded_values_sha256"] == sources.sha256(serialized)
    seeds = [
        seed for case in config["signals"] for row in case["seeds"] for seed in row
    ]
    assert len(seeds) == len(set(seeds)) == 120
    assert all(type(seed) is int and 0 < seed < 2**31 for seed in seeds)
    assert not set(seeds) & excluded
    assert not set(seeds) & {seed_config["seed"], config["grid"]["seed"]}
    assert seed_config["seed"] != config["grid"]["seed"]
    rng = np.random.Generator(np.random.PCG64(2026111301))
    expected = []
    while len(expected) < 120:
        value = int(rng.integers(1, 2**31))
        if value not in excluded and value not in expected:
            expected.append(value)
    assert seeds == expected


def test_the_180_calls_retain_thirty_balanced_fresh_four_vs_two_pairs(tmp_path):
    assert profile.names() == list(SIGNALS)
    seen, calls, packages, total_iterations = set(), 0, 0, 0
    for name in SIGNALS:
        plans = profile.plans(name)
        assert [p["number"] for p in plans] == list(range(1, 61))
        for block in range(1, 11):
            group = [p for p in plans if p["block"] == block]
            assert [p["arm"] for p in group] == (
                ["R"] * 4 + ["L"] * 2 if block % 2 else ["L"] * 2 + ["R"] * 4
            )
            arms = {arm: [p for p in group if p["arm"] == arm] for arm in ("R", "L")}
            new = [p["seed"] for p in arms["R"]]
            assert new == profile.case(name)["seeds"][block - 1]
            assert len(set(new)) == 4 and not seen & set(new)
            seen.update(new)
            assert [p["seed"] for p in arms["L"]] == new[:2]
            for arm, size, iterations in (("R", 4, 1000), ("L", 2, 2000)):
                members = arms[arm]
                assert [p["member"] for p in members] == list(range(size))
                assert all(
                    p["signal"] == name and p["condition"] == "iterations"
                    for p in members
                )
                assert all(p["niterations"] == iterations for p in members)
                assert sum(p["niterations"] for p in members) == 4000
                packages += 1
            for first, second in zip(arms["R"][:2], arms["L"], strict=True):
                assert first["number"] != second["number"]
                requests = [
                    profile.request_for(p, tmp_path / "anchor.npz", "a" * 40)
                    for p in (first, second)
                ]
                assert requests[0]["seed"] == requests[1]["seed"]
                assert [r["niterations"] for r in requests] == [1000, 2000]
                assert all(
                    r["coordinate"]
                    == {"name": "t", "scale_hex": (1.0).hex(), "unit": "s"}
                    for r in requests
                )
                assert all(
                    r["protocol_commit"] == profile.PLAN_COMMIT
                    and r["protocol_sha256"] == profile.PLAN_HASHES
                    for r in requests
                )
                assert not any(
                    key in request
                    for request in requests
                    for key in ("resume", "checkpoint", "reuse", "warm_start")
                )
            calls += len(group)
            total_iterations += sum(p["niterations"] for p in group)
    assert (calls, packages, len(seen), total_iterations) == (180, 60, 120, 240000)


def test_technical_scope_keeps_twelve_tiny_workers_and_four_outputs():
    plans = [p for name in profile.names(True) for p in profile.plans(name, True)]
    assert len(plans) == 12
    assert not set(profile.names(True)) & set(SIGNALS)
    for name in profile.names(True):
        group = [p for p in plans if p["signal"] == name]
        assert [p["arm"] for p in group] == ["R"] * 4 + ["L"] * 2
        assert [p["member"] for p in group] == [0, 1, 2, 3, 0, 1]
        assert [p["niterations"] for p in group] == [1] * 4 + [2] * 2
        assert [p["seed"] for p in group[4:]] == [p["seed"] for p in group[:2]]
        assert all(p["block"] == 1 and p["condition"] == "iterations" for p in group)
    assert profile.signal_seconds() == 60 * 1800 + 7200
    assert profile.signal_seconds(True) < profile.signal_seconds()


@pytest.mark.parametrize(
    "name,technical",
    [("fixture_a", False), ("confirm_low", True), ("anchor", False), ("other", False)],
)
def test_old_cases_and_wrong_scope_cannot_enter_the_new_confirmation(name, technical):
    for function in (profile.case, profile.plans, profile.inputs):
        with pytest.raises(ValueError):
            function(name, technical)


def test_only_regular_time_axes_are_reused_and_new_grid_covers_every_stratum():
    config = profile.configuration()
    source = config["source"]
    raw = git("show", source["commit"] + ":" + source["inputs_path"])
    assert sources.sha256(raw) == source["inputs_sha256"]
    new = (ROOT / "data/restart_budget_confirmation_inputs.npz").read_bytes()
    assert sources.sha256(new) == config["inputs_sha256"]
    with (
        np.load(io.BytesIO(raw), allow_pickle=False) as old,
        np.load(io.BytesIO(new), allow_pickle=False) as saved,
    ):
        assert set(saved.files) == {
            "time_s",
            "diagnostic_time_s",
            "irregular_time_s",
        } | {
            name + "_" + role
            for name in SIGNALS
            for role in ("observed", "diagnostic_truth", "irregular_truth")
        }
        assert all(saved[key].dtype == np.dtype("<f8") for key in saved.files)
        assert sum(saved[key].size for key in saved.files) == 8164
        assert saved["time_s"].tobytes() == old["time_s"].tobytes()
        assert (
            saved["diagnostic_time_s"].tobytes() == old["diagnostic_time_s"].tobytes()
        )
        assert [Fraction(float(t)) for t in saved["time_s"]] == [
            Fraction(i, 4096) for i in range(128)
        ]
        assert [Fraction(float(t)) for t in saved["diagnostic_time_s"]] == [
            Fraction(i * 8 + j, 32768) for i in range(127) for j in range(1, 8)
        ]
        irregular = saved["irregular_time_s"]
        assert len(set(irregular)) == len(irregular) == 1024
        assert not set(irregular) & set(old["irregular_time_s"])
        end = Fraction(127, 4096)
        for index, value in enumerate(irregular):
            t = Fraction(float(value))
            assert Fraction(index, 1024) * end < t < Fraction(index + 1, 1024) * end
            assert (t * 32768).denominator != 1
        for name in SIGNALS:
            physical, grid = profile.inputs(name)
            for key, value in physical.items():
                original = key if key.endswith("time_s") else name + "_" + key
                assert value.tobytes() == saved[original].tobytes()
            assert grid["time_s"].tobytes() == irregular.tobytes()
            assert grid["truth"].tobytes() == saved[name + "_irregular_truth"].tobytes()


@pytest.mark.parametrize("name", list(SIGNALS))
def test_all_new_signal_values_match_an_independent_mpfr_analytic_reference(name):
    case = profile.case(name)
    expected = tuple(float(Fraction(value)) for value in SIGNALS[name])
    assert tuple(case["truth"][key] for key in PARAMETERS) == expected
    assert case["truth_hex"] == dict(
        zip(PARAMETERS, (value.hex() for value in expected), strict=True)
    )
    physical, grid = profile.inputs(name)
    values = [
        (physical["time_s"], physical["observed"]),
        (physical["diagnostic_time_s"], physical["diagnostic_truth"]),
        (grid["time_s"], grid["truth"]),
    ]
    with gmpy2.context(gmpy2.get_context(), precision=350):
        amplitude, frequency, decay, phase = map(gmpy2.mpfr, expected)
        pi = gmpy2.const_pi()
        checked = 0
        for times, truth in values:
            for time, observed in zip(times, truth, strict=True):
                t = gmpy2.mpfr(float(time))
                reference = (
                    amplitude
                    * gmpy2.exp(-t / decay)
                    * gmpy2.cos(2 * pi * frequency * t + phase)
                )
                assert abs(
                    gmpy2.mpfr(float(observed)) - reference
                ) / amplitude < gmpy2.mpfr("1e-13")
                checked += 1
        assert checked == 2041
        assert physical["time_s"][0] == 0.0
        assert abs(
            gmpy2.mpfr(float(physical["observed"][0])) / amplitude - gmpy2.cos(phase)
        ) < gmpy2.mpfr("3e-16")


@pytest.mark.parametrize(
    "role",
    [
        "time_s",
        "observed",
        "diagnostic_time_s",
        "diagnostic_truth",
        "irregular_time_s",
        "irregular_truth",
    ],
)
def test_each_new_signal_role_has_its_own_bit_binding(monkeypatch, tmp_path, role):
    config = profile.configuration()
    with np.load(
        ROOT / "data/restart_budget_confirmation_inputs.npz", allow_pickle=False
    ) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    key = role if role.endswith("time_s") else "confirm_low_" + role
    arrays[key][1] = np.nextafter(arrays[key][1], np.inf)
    (tmp_path / "data").mkdir()
    np.savez(tmp_path / "data/restart_budget_confirmation_inputs.npz", **arrays)
    # Isolate the role-level guard from the already tested container hash.
    monkeypatch.setattr(profile, "configuration", lambda: config)
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="input|grid|Float64"):
        profile.inputs("confirm_low")


@pytest.mark.parametrize("name", list(profile.PLAN_HASHES))
def test_every_frozen_method_file_is_hash_bound(monkeypatch, tmp_path, name):
    for path in profile.PLAN_HASHES:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    target = tmp_path / name
    target.write_bytes(target.read_bytes() + b"changed")
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="frozen"):
        profile.configuration()
