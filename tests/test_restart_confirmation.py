"""Independent counterexamples for the fixed confirmation schedule and release."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import restart_confirmation as confirmation
from ringdown_sr import restart_confirmation_profile as profile
from ringdown_sr.pilot import _write_json


def cells(name="anchor"):
    return [
        {
            "plan": p,
            "status": "completed",
            "A": True,
            "A_and_original_family": True,
            "curve_grade": "A",
            "original_family_status": "proven_member",
            "any_front_A": True,
            "selected": {"loss": 0.01 + p["member"], "complexity": 9},
            "costs": {k: 10 for k in confirmation.previous.COST_FIELDS},
        }
        for p in profile.plans(name)
    ]


def test_all_150_calls_are_new_paired_balanced_and_disjoint():
    old = {
        20261201,
        20261210,
        20261211,
        20261212,
        20261221,
        20261222,
        20261223,
        20261231,
        20261232,
        20261233,
        20261241,
        20261242,
        20261243,
        20261251,
        20261252,
        20261253,
    }
    seen, total = set(), 0
    for name in profile.names():
        planned = profile.plans(name)
        assert len(planned) == 50
        assert [p["number"] for p in planned] == list(range(1, 51))
        first = []
        for block in range(1, 11):
            group = [p for p in planned if p["block"] == block]
            first.append(group[0]["arm"])
            long = [p for p in group if p["arm"] == "I"]
            short = [p for p in group if p["arm"] == "R"]
            assert len(long) == 1 and len(short) == 4
            assert long[0]["seed"] == short[0]["seed"]
            assert long[0]["niterations"] == 2000
            assert [p["niterations"] for p in short] == [500] * 4
            seeds = {p["seed"] for p in short}
            assert len(seeds) == 4 and not seeds & (seen | old)
            seen.update(seeds)
        assert first == ["R", "I"] * 5
        total += len(planned)
    assert total == 150 and len(seen) == 120


def test_frozen_input_roles_anchor_bits_and_isolated_grid_rng():
    np.random.seed(912)
    before = np.random.get_state()
    arrays = [profile.inputs(n) for n in profile.names()]
    after = np.random.get_state()
    assert (
        before[0] == after[0]
        and np.array_equal(before[1], after[1])
        and before[2:] == after[2:]
    )
    with np.load(
        profile.ROOT / "data/transfer_check_inputs.npz", allow_pickle=False
    ) as old:
        assert np.array_equal(arrays[0][0]["observed"], old["observed"][0])
    for inputs, grid in arrays:
        assert set(inputs) == {
            "time_s",
            "observed",
            "diagnostic_time_s",
            "diagnostic_truth",
        }
        assert inputs["observed"].shape == (128,) and inputs[
            "diagnostic_truth"
        ].shape == (889,)
        assert grid["time_s"].shape == (1024,)
        assert np.all(grid["time_s"] > 0) and np.all(grid["time_s"] < 127 / 4096)
        assert all(not float(t * 32768).is_integer() for t in grid["time_s"])
    assert not np.array_equal(arrays[1][0]["observed"], arrays[2][0]["observed"])


@pytest.mark.parametrize(
    "kind", ["missing", "duplicate", "seed", "signal", "order", "unfinished"]
)
def test_changed_or_incomplete_schedule_cannot_release(kind):
    data = cells()
    if kind == "missing":
        data.pop()
    elif kind == "duplicate":
        data[-1] = copy.deepcopy(data[0])
    elif kind == "seed":
        data[0]["plan"]["seed"] += 1
    elif kind == "signal":
        data[0]["plan"]["signal"] = "variant_low"
    elif kind == "order":
        data[0], data[1] = data[1], data[0]
    else:
        data[0]["status"] = "running"
    with pytest.raises(ValueError, match="every planned"):
        confirmation.comparison(data, "anchor")


def test_package_choice_ignores_quality_and_retains_failed_member_costs():
    data = cells()
    members = [c for c in data if c["plan"]["block"] == 1 and c["plan"]["arm"] == "R"]
    members[0].update(status="worker_failed", A=False, A_and_original_family=False)
    members[1].update(
        A=False,
        A_and_original_family=False,
        curve_grade="D",
        original_family_status="unresolved",
    )
    members[1]["selected"]["loss"] = 0.0
    members[0]["costs"]["worker_wall_seconds"] = None
    report = confirmation.comparison(data, "anchor")
    output = report["pairs"][0]["outputs"]["R"]
    assert output["selected_cell"] == members[1]["plan"]["number"]
    assert not output["A"] and output["any_front_A"]
    assert (
        output["failed_members"] == 1
        and output["costs"]["callback_calls_during_fit"] == 40
    )
    totals = report["totals"]["R"]
    assert totals["denominator"] == 10 and totals["A"] == 9 and totals["failures"] == 0
    assert totals["costs"]["worker_wall_seconds"] is None


def test_one_failed_package_is_one_output_and_keeps_all_four_costs():
    data = cells()
    for c in data:
        if c["plan"]["block"] == 1 and c["plan"]["arm"] == "R":
            c.update(status="worker_failed", A=False, A_and_original_family=False)
    r = confirmation.comparison(data, "anchor")
    assert r["totals"]["R"]["failures"] == 1
    assert r["totals"]["R"]["failed_members"] == 4
    assert r["totals"]["R"]["costs"]["callback_calls_during_fit"] == 400


@pytest.mark.parametrize("joint,met", [(7, False), (8, True), (10, True)])
def test_eight_of_ten_is_joint_success_not_merely_curve_class(joint, met):
    data = cells()
    for c in data:
        if c["plan"]["block"] > joint and c["plan"]["arm"] == "R":
            c.update(A_and_original_family=False, original_family_status="unresolved")
    r = confirmation.comparison(data, "anchor")
    assert r["totals"]["R"]["A"] == 10
    assert r["totals"]["R"]["A_and_original_family"] == joint
    assert r["R_meets_signal_threshold"] is met
    assert r["automatic_execution"] is False


def test_uncertainty_does_not_assert_eighty_percent_probability():
    interval = confirmation.binomial_interval(8, 10)
    assert interval["lower"] == pytest.approx(0.4439045377)
    assert interval["upper"] == pytest.approx(0.9747892737)
    assert confirmation.binomial_interval(0, 10)["lower"] == 0
    assert confirmation.binomial_interval(10, 10)["upper"] == 1


def fake_sections(monkeypatch, tmp_path, *, scope="scientific", failing_signal=None):
    monkeypatch.setattr(confirmation, "freeze_software", lambda consumed: {})

    def read(path, consumed, software, temporary):
        n = path.name
        witness = path / "evidence"
        witness.write_text("original")
        consumed.add(witness, b"original")
        data = cells(n)
        if n == failing_signal:
            for c in data:
                if c["plan"]["block"] > 7 and c["plan"]["arm"] == "R":
                    c.update(A=False, A_and_original_family=False)
        return {
            "signal": n,
            "scope": scope,
            "numerical_environment": {},
            "cells": data,
            "comparison": confirmation.comparison(data, n),
            "whole_call_timing": {"wall_seconds": 2},
            "verified_cells": len(data),
        }

    monkeypatch.setattr(confirmation, "read_section", read)
    roots = [tmp_path / n for n in profile.names()]
    for p in roots:
        p.mkdir()
    return roots


@pytest.mark.parametrize(
    "fault", ["missing", "duplicate_signal", "environment", "late_change"]
)
def test_series_cannot_hide_missing_or_changed_sections(monkeypatch, tmp_path, fault):
    roots = fake_sections(monkeypatch, tmp_path)
    read = confirmation.read_section

    def altered(path, *args):
        r = read(path, *args)
        if path == roots[-1]:
            if fault == "duplicate_signal":
                r["signal"] = "anchor"
            elif fault == "environment":
                r["numerical_environment"] = {"different": True}
        return r

    monkeypatch.setattr(confirmation, "read_section", altered)
    if fault == "late_change":
        original = publication.verify_bytes

        def verify_bytes(output, expected, *, locked=True):
            original(output, expected, locked=locked)
            if not locked:
                (roots[0] / "evidence").write_text("changed after unlock")

        monkeypatch.setattr(publication, "verify_bytes", verify_bytes)
    output = tmp_path / "verification"
    with pytest.raises(ValueError):
        confirmation.verify(
            roots[:2] if fault == "missing" else roots, output, complete=True
        )
    assert (output / publication.LOCK).exists()
    assert "transition_criterion_met" not in confirmation.load_json(
        output, publication.REPORT
    )


def test_pilot_threshold_is_per_signal_without_pooling(monkeypatch, tmp_path):
    roots = fake_sections(monkeypatch, tmp_path, failing_signal="variant_low")
    report = confirmation.verify(roots, tmp_path / "verification", complete=True)
    assert report["verified_cells"] == 150 and report["search_calls"] == 0
    assert report["transition_criterion_met"] is False
    assert [
        c["totals"]["R"]["A_and_original_family"] for c in report["comparisons"]
    ] == [10, 7, 10]
    assert report["automatic_execution"] is False


@pytest.mark.parametrize("fault", [None, "source", "interrupt"])
def test_whole_call_late_fault_revokes_section(monkeypatch, tmp_path, fault):
    original = tmp_path / "source"
    original.write_bytes(b"original")

    def execute(destination, name, technical, closing):
        destination.mkdir()
        consumed = publication.Consumption(publication.Deadline(30))
        consumed.add(original, b"original")
        closing.append(consumed)
        _write_json(destination / "run_state.json", {"status": "completed"})
        (destination / "completion").mkdir()
        _write_json(
            destination / "completion" / publication.REPORT,
            {"status": "completed", "comparison": {}},
        )
        _write_json(destination / "completion" / publication.MANIFEST, {})
        return {}

    monkeypatch.setattr(confirmation, "_run", execute)
    write = confirmation._write_json

    def altered(path, value):
        write(path, value)
        if path.name.endswith("-call.json"):
            if fault == "source":
                original.write_bytes(b"changed")
            elif fault == "interrupt":
                raise KeyboardInterrupt("late interrupt")

    monkeypatch.setattr(confirmation, "_write_json", altered)
    output = tmp_path / "run"
    if fault is None:
        confirmation.run(output, "anchor", technical=True)
        assert confirmation.load_json(tmp_path, "run-call.json")["wall_seconds"] > 0
    else:
        with pytest.raises((ValueError, KeyboardInterrupt)):
            confirmation.run(output, "anchor", technical=True)
        assert (output / "completion" / publication.LOCK).exists()
        assert "comparison" not in confirmation.load_json(
            output / "completion", publication.REPORT
        )


def test_confirmation_bridge_binds_signal_scope_and_exact_inputs(monkeypatch, tmp_path):
    bridge = profile.native.load_module(
        profile.ROOT / profile.BRIDGE, "confirmation_test_bridge"
    )
    legacy = profile.native.load_module(
        profile.ROOT / profile.LEGACY, "confirmation_test_legacy"
    )

    class Reader:
        read_json = staticmethod(confirmation.sources.read_json)

    commit = "a" * 40
    monkeypatch.setattr(
        bridge,
        "_provenance",
        lambda: {
            "git": {"available": True, "changes": [], "commit": commit, "dirty": False}
        },
    )
    plan = profile.plans("fixture_a", True)[0]
    inputs = tmp_path / "inputs.npz"
    arrays, _ = profile.inputs("fixture_a", True)
    np.savez(inputs, **arrays)
    path = tmp_path / "request.json"
    request = profile.request_for(plan, inputs, commit, True)
    _write_json(path, request)
    _, actual = bridge.checked_request(path, inputs, "verify", legacy, Reader)
    assert np.array_equal(actual["observed"], 1 + arrays["time_s"])
    assert not actual["observed"].flags.writeable
    wrong, _ = profile.inputs("fixture_b", True)
    np.savez(inputs, **wrong)
    with pytest.raises(ValueError, match="Wrong confirmation signal"):
        bridge.checked_request(path, inputs, "verify", legacy, Reader)
    np.savez(inputs, **arrays)
    for field, value in [
        ("seed", plan["seed"] + 1),
        ("scope", "scientific"),
        ("adapter_sha256", "0" * 64),
        ("protocol_commit", "f" * 40),
    ]:
        changed = {**request, field: value}
        _write_json(path, changed)
        with pytest.raises(ValueError):
            bridge.checked_request(path, inputs, "verify", legacy, Reader)


def test_unweighted_small_profile_cannot_enter_confirmation_plan():
    data = cells()
    data[0]["plan"]["condition"] = "local_20_2"
    with pytest.raises(ValueError, match="every planned"):
        confirmation.comparison(data, "anchor")


def test_nonfinite_member_loss_is_not_selected_and_ties_use_member_order():
    data = cells()[:4]
    data[0]["selected"]["loss"] = float("nan")
    data[1]["selected"] = {"loss": 0.5, "complexity": 7}
    data[2]["selected"] = {"loss": 0.5, "complexity": 6}
    data[3]["selected"] = {"loss": 0.5, "complexity": 6}
    output = confirmation.selected_output(data)
    assert output["selected_cell"] == data[2]["plan"]["number"]


@pytest.mark.parametrize("arm,iterations", [("R", 500), ("I", 2000)])
@pytest.mark.parametrize("finished", [True, False])
def test_both_arms_require_their_regular_iteration_end(
    tmp_path, arm, iterations, finished
):
    bridge = profile.native.load_module(
        profile.ROOT / profile.BRIDGE, "confirmation_stop_test"
    )
    count = 2 * iterations if finished else 7
    record = {
        "format": profile.native.FORMAT,
        "populations": 2,
        "processed_population_cycles": count,
        "checks": count,
        "requested_iterations": iterations,
        "completed_outer_rounds": count // 2,
        "residual_population_cycles": count % 2,
        "iteration_limit_reached": finished,
        "technical_counter_stop": False,
        "affinity": [3],
        "native_start_unix_seconds": 1000.0,
        "loop_entry_unix_seconds": 1000.0,
        "monotonic_to_last_check_seconds": 20.0,
        "elapsed_at_last_check_seconds": 20.0,
        "main_loop_call_wall_seconds": 21.0,
        "clock_difference_seconds": 0.0,
        "timeout_reached": False,
    }
    (tmp_path / "worker").mkdir()
    _write_json(tmp_path / "worker/time_budget_clock.json", record)
    request = {
        "cell": {"condition": "iterations", "arm": arm, "niterations": iterations}
    }
    reader = SimpleNamespace(read_json=confirmation.sources.read_json)
    if finished:
        result = bridge.clock_evidence(tmp_path, request, reader)
        assert result["reason"] == "iteration_limit"
        assert result["clock"]["completed_outer_rounds"] == iterations
    else:
        with pytest.raises(ValueError, match="without its allowed stopping rule"):
            bridge.clock_evidence(tmp_path, request, reader)


@pytest.mark.parametrize("invalid", [True, "1"])
def test_read_verification_rejects_nonnumeric_section_timing(tmp_path, invalid):
    source = tmp_path / "source"
    completion = source / "completion"
    completion.mkdir(parents=True)
    _write_json(
        completion / publication.REPORT,
        {
            "format": confirmation.FORMAT,
            "status": "completed",
            "scope": "technical",
            "signal": "fixture_a",
            "prepublication_wall_seconds": invalid,
        },
    )
    (completion / publication.SUMMARY).write_text("fixture")
    _write_json(completion / "raw_checksums.json", {})
    manifest = {
        p.name: confirmation.sources.sha256(p.read_bytes())
        for p in completion.iterdir()
    }
    _write_json(completion / publication.MANIFEST, manifest)
    _write_json(
        tmp_path / "source-call.json",
        {
            "format": confirmation.FORMAT + "-call-timing",
            "status": "completed",
            "scope": confirmation.CALL_SCOPE,
            "wall_seconds": 100.0,
            "cpu_user_seconds": 80.0,
            "cpu_system_seconds": 2.0,
            "source_report_sha256": manifest[publication.REPORT],
        },
    )
    consumed = publication.Consumption(publication.Deadline(30))
    with pytest.raises(ValueError, match="Invalid confirmation whole-call timing"):
        confirmation.read_section(source, consumed, {}, tmp_path)
