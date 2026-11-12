"""Check the frozen budget allocation against source inputs and paired seeds."""

import io
import json
import random
import re
import subprocess

import numpy as np
import pytest

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_budget_profile as profile
from ringdown_sr.symbolic import ROOT


def generator():
    return profile.native.load_module(
        ROOT / "scripts/prepare_restart_budget_inputs.py", "budget_input_generator"
    )


def test_generator_reproduces_frozen_bytes_without_consuming_search_randomness():
    config = profile.configuration()
    python_before, numpy_before = random.getstate(), np.random.get_state()
    outputs, actual = generator().prepare(ROOT, config["base_commit"])
    numpy_after = np.random.get_state()
    assert random.getstate() == python_before
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert actual == config
    assert set(outputs) == {
        "data/restart_budget_protocol.json",
        "data/restart_budget_inputs.npz",
    }
    for name, raw in outputs.items():
        assert raw == (ROOT / name).read_bytes()
    assert actual["generation"]["truth_regenerated"] is False
    assert actual["generation"]["grid_regenerated"] is False
    assert actual["generation"]["coordinate_transformed"] is False


@pytest.mark.parametrize("commit", ["HEAD", "fbdb450", profile.PLAN_COMMIT])
def test_seed_generation_requires_the_exact_immutable_base(commit):
    with pytest.raises(ValueError, match="frozen complete PR84 base"):
        generator().prepare(ROOT, commit)


def test_new_seeds_are_disjoint_from_the_full_documented_exclusion_scope():
    config = profile.configuration()
    commit = config["base_commit"]
    content = subprocess.check_output(
        [
            "git",
            "grep",
            "-h",
            "-I",
            "-E",
            "[0-9]+",
            commit,
            "--",
            "data",
            "docs",
            "src",
            "scripts",
            "tests",
        ],
        cwd=ROOT,
    ).decode()
    excluded = {int(token) for token in re.findall(r"\b\d+\b", content)}
    excluded = {value for value in excluded if 0 < value < 2**31}
    seeds = [
        seed for case in config["signals"] for row in case["seeds"] for seed in row
    ]
    assert len(seeds) == len(set(seeds)) == 32
    assert all(type(seed) is int and 0 < seed < 2**31 for seed in seeds)
    assert not set(seeds) & excluded
    assert config["seed_generator"]["excluded_values"] == len(excluded)
    assert config["seed_generator"]["excluded_values_sha256"] == sources.sha256(
        (json.dumps(sorted(excluded), indent=2, ensure_ascii=False) + "\n").encode()
    )
    for name in ("restart_confirmation", "time_coordinate"):
        previous = json.loads(
            subprocess.check_output(
                ["git", "show", commit + ":data/" + name + "_protocol.json"],
                cwd=ROOT,
            )
        )
        old = {
            seed
            for case in previous["signals"]
            for row in case["seeds"]
            for seed in (row if isinstance(row, list) else [row])
        }
        assert not old & set(seeds)


def test_input_container_and_every_physical_role_are_unchanged():
    config = profile.configuration()
    source = config["source"]
    old = subprocess.check_output(
        ["git", "show", source["commit"] + ":" + source["inputs_path"]], cwd=ROOT
    )
    new = (ROOT / "data/restart_budget_inputs.npz").read_bytes()
    assert new == old
    assert sources.sha256(new) == source["inputs_sha256"] == config["inputs_sha256"]
    with np.load(io.BytesIO(new), allow_pickle=False) as saved:
        assert len(saved.files) == 12
        assert not any(key.endswith("_u") for key in saved.files)
        assert sum(saved[key].size for key in saved.files) == 8164
        assert saved["time_s"].tobytes() == (np.arange(128) / 4096).tobytes()
        assert len(saved["diagnostic_time_s"]) == 889
        assert len(saved["irregular_time_s"]) == 1024
        for case in config["signals"]:
            arrays, grid = profile.inputs(case["name"])
            for key, value in arrays.items():
                original = key if key.endswith("time_s") else case["name"] + "_" + key
                assert value.dtype == saved[original].dtype
                assert value.shape == saved[original].shape
                assert value.tobytes() == saved[original].tobytes()
            assert grid["time_s"].tobytes() == saved["irregular_time_s"].tobytes()
            assert (
                grid["truth"].tobytes()
                == saved[case["name"] + "_irregular_truth"].tobytes()
            )
            assert {key: sources.fingerprint(v) for key, v in arrays.items()} == case[
                "arrays"
            ]
            assert {key: sources.fingerprint(v) for key, v in grid.items()} == case[
                "grid"
            ]


def test_forty_eight_calls_form_eight_disjoint_fresh_four_vs_two_packages(tmp_path):
    all_seeds, calls, outputs = set(), 0, 0
    expected = {"anchor": 2, "variant_low": 2, "variant_high": 4}
    assert profile.names() == list(expected)
    for name, blocks in expected.items():
        plans = profile.plans(name)
        assert [p["number"] for p in plans] == list(range(1, 6 * blocks + 1))
        for block in range(1, blocks + 1):
            group = [p for p in plans if p["block"] == block]
            assert [p["arm"] for p in group] == (
                ["R"] * 4 + ["L"] * 2 if block % 2 else ["L"] * 2 + ["R"] * 4
            )
            arms = {arm: [p for p in group if p["arm"] == arm] for arm in ("R", "L")}
            r_seeds = [p["seed"] for p in arms["R"]]
            assert r_seeds == profile.case(name)["seeds"][block - 1]
            assert not all_seeds & set(r_seeds)
            all_seeds.update(r_seeds)
            assert [p["seed"] for p in arms["L"]] == r_seeds[:2]
            for arm, size, iterations in (("R", 4, 1000), ("L", 2, 2000)):
                members = arms[arm]
                assert [p["member"] for p in members] == list(range(size))
                assert all(
                    p["signal"] == name and p["condition"] == "iterations"
                    for p in members
                )
                assert all(p["niterations"] == iterations for p in members)
                assert sum(p["niterations"] for p in members) == 4000
                outputs += 1
            for r, long in zip(arms["R"][:2], arms["L"], strict=True):
                assert r["number"] != long["number"]
                requests = [
                    profile.request_for(p, tmp_path / "anchor.npz", "a" * 40)
                    for p in (r, long)
                ]
                assert requests[0]["seed"] == requests[1]["seed"]
                assert requests[0]["niterations"] == 1000
                assert requests[1]["niterations"] == 2000
                assert all(
                    request["cell"] == p
                    for request, p in zip(requests, (r, long), strict=True)
                )
                assert not any(
                    key in request
                    for request in requests
                    for key in ("resume", "checkpoint", "reuse", "warm_start")
                )
            calls += len(group)
    assert (calls, outputs, len(all_seeds)) == (48, 16, 32)


def test_twelve_technical_workers_exercise_all_four_and_two_members():
    total = []
    for name in profile.names(True):
        plans = profile.plans(name, True)
        assert len(plans) == 6
        assert [p["arm"] for p in plans] == ["R"] * 4 + ["L"] * 2
        assert [p["member"] for p in plans] == [0, 1, 2, 3, 0, 1]
        assert [p["niterations"] for p in plans] == [1] * 4 + [2] * 2
        assert [p["seed"] for p in plans[4:]] == [p["seed"] for p in plans[:2]]
        assert len({p["seed"] for p in plans}) == 4
        assert all(p["block"] == 1 and p["condition"] == "iterations" for p in plans)
        total.extend(plans)
    assert len(total) == 12
    assert len({p["seed"] for p in total}) == 8
    assert not {p["signal"] for p in total} & set(profile.names())


@pytest.mark.parametrize(
    "name,technical", [("fixture_a", False), ("anchor", True), ("other", False)]
)
def test_signal_and_scope_cannot_be_interchanged(name, technical):
    for function in (profile.case, profile.plans, profile.inputs):
        with pytest.raises(ValueError):
            function(name, technical)


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
def test_all_six_input_roles_keep_independent_bit_bindings(monkeypatch, tmp_path, role):
    config = profile.configuration()
    with np.load(ROOT / "data/restart_budget_inputs.npz", allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    original = role if role.endswith("time_s") else "anchor_" + role
    arrays[original][1] = np.nextafter(arrays[original][1], np.inf)
    (tmp_path / "data").mkdir()
    np.savez(tmp_path / "data/restart_budget_inputs.npz", **arrays)
    # Bypass the container hash only, so the role-level binding is exercised.
    monkeypatch.setattr(profile, "configuration", lambda: config)
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="input|grid|Float64"):
        profile.inputs("anchor")


@pytest.mark.parametrize("name", list(profile.PLAN_HASHES))
def test_every_frozen_method_file_is_bound(monkeypatch, tmp_path, name):
    for path in profile.PLAN_HASHES:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    target = tmp_path / name
    target.write_bytes(target.read_bytes() + b"changed")
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="frozen"):
        profile.configuration()
