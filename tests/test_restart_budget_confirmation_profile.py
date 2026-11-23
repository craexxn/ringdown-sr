"""Independent references for the frozen new-signal confirmation profile."""

import copy
import io
import json
import random
import re
import subprocess
import zipfile
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


def _method_without_evaluated_signal_bits(document):
    """Remove only data-dependent outputs, keeping every method field exact."""
    result = copy.deepcopy(document)
    result.pop("inputs_sha256")
    result["generation"]["independent_check"].pop("max_absolute_error_over_amplitude")
    for case in result["signals"]:
        for role in ("observed", "diagnostic_truth"):
            case["arrays"][role].pop("sha256")
        case["grid"]["truth"].pop("sha256")
    return result


def _check_signal_reference(name, values):
    """Check either archive or local regeneration against the original MPFR bound."""
    expected = tuple(float(Fraction(value)) for value in SIGNALS[name])
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
        assert values[0][0][0] == 0.0
        assert abs(
            gmpy2.mpfr(float(values[0][1][0])) / amplitude - gmpy2.cos(phase)
        ) < gmpy2.mpfr("3e-16")


def test_frozen_generator_keeps_archival_bits_and_repeats_local_values_without_rng_mutation():
    config = profile.configuration()
    python_before, numpy_before = random.getstate(), np.random.get_state()
    precision_before = mpmath.mp.dps
    build = generator()
    outputs, actual = build.prepare(ROOT, config["base_commit"])
    repeated_outputs, repeated = build.prepare(ROOT, config["base_commit"])
    numpy_after = np.random.get_state()
    assert random.getstate() == python_before
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert mpmath.mp.dps == precision_before
    assert outputs == repeated_outputs
    assert sources.json_bytes(actual) == sources.json_bytes(repeated)
    # NumPy's supported exp/cos SIMD paths can differ in their last bits. The
    # archived payload remains the only accepted scientific input; regeneration
    # must repeat locally and satisfy the original independent analytic bound.
    assert sources.json_bytes(
        _method_without_evaluated_signal_bits(actual)
    ) == sources.json_bytes(_method_without_evaluated_signal_bits(config))
    assert set(outputs) == {
        "data/restart_budget_confirmation_protocol.json",
        "data/restart_budget_confirmation_inputs.npz",
    }
    for name, expected_hash in profile.PLAN_HASHES.items():
        assert sources.sha256((ROOT / name).read_bytes()) == expected_hash
    protocol_path = "data/restart_budget_confirmation_protocol.json"
    input_path = "data/restart_budget_confirmation_inputs.npz"
    assert sources.json_bytes(
        sources.read_json(outputs[protocol_path])
    ) == sources.json_bytes(actual)
    check = actual["generation"]["independent_check"]
    assert 0 <= check["max_absolute_error_over_amplitude"] < check["bound"] == 1e-13
    assert sources.sha256(outputs[input_path]) == actual["inputs_sha256"]
    archived_raw = (ROOT / input_path).read_bytes()
    assert sources.sha256(archived_raw) == config["inputs_sha256"]
    with (
        np.load(io.BytesIO(archived_raw), allow_pickle=False) as saved,
        np.load(io.BytesIO(outputs[input_path]), allow_pickle=False) as regenerated,
    ):
        assert regenerated.files == saved.files
        archived_arrays = {name: saved[name] for name in saved.files}
        # Exact reserialization checks container determinism without pretending
        # transcendental evaluation is bitwise identical across CPU dispatches.
        assert build.npz_bytes(archived_arrays) == archived_raw
        assert (
            build.npz_bytes({name: regenerated[name] for name in regenerated.files})
            == outputs[input_path]
        )
        for name in saved.files:
            assert regenerated[name].dtype == saved[name].dtype == np.dtype("<f8")
            assert regenerated[name].shape == saved[name].shape
            if name.endswith("time_s"):
                assert regenerated[name].tobytes() == saved[name].tobytes()
        for case in actual["signals"]:
            name = case["name"]
            for role, fingerprint in case["arrays"].items():
                key = role if role.endswith("time_s") else name + "_" + role
                assert sources.fingerprint(regenerated[key]) == fingerprint
            assert case["grid"] == {
                "time_s": sources.fingerprint(regenerated["irregular_time_s"]),
                "truth": sources.fingerprint(regenerated[name + "_irregular_truth"]),
            }
            _check_signal_reference(
                name,
                [
                    (regenerated["time_s"], regenerated[name + "_observed"]),
                    (
                        regenerated["diagnostic_time_s"],
                        regenerated[name + "_diagnostic_truth"],
                    ),
                    (
                        regenerated["irregular_time_s"],
                        regenerated[name + "_irregular_truth"],
                    ),
                ],
            )
    for raw in (archived_raw, outputs[input_path]):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == [name + ".npy" for name in archived_arrays]
            for member in archive.infolist():
                assert member.date_time == (1980, 1, 1, 0, 0, 0)
                assert member.compress_type == zipfile.ZIP_STORED
                assert member.external_attr == 0o600 << 16
                with archive.open(member) as stream:
                    assert np.lib.format.read_magic(stream) == (1, 0)
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
    _check_signal_reference(name, values)


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
