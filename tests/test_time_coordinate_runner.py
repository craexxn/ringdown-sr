"""Counterexamples for paired coordinate decisions and complete publication."""

import copy
from contextlib import nullcontext

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import time_coordinate as coordinate
from ringdown_sr import time_coordinate_profile as profile
from ringdown_sr.pilot import _write_json


def cells(name="anchor", technical=False):
    return [
        {
            "plan": plan,
            "status": "completed",
            "A": True,
            "A_and_original_family": True,
            "curve_grade": "A",
            "original_family_status": "proven_member",
            "any_front_A": True,
            "selected": {"loss": 0.01, "complexity": 9},
            "costs": {key: 10 for key in coordinate.previous.COST_FIELDS},
        }
        for plan in profile.plans(name, technical)
    ]


def sections():
    return [
        {
            "signal": name,
            "scope": "scientific",
            "comparison": coordinate.comparison(cells(name), name),
        }
        for name in profile.names()
    ]


@pytest.mark.parametrize(
    "fault", ["missing", "duplicate", "seed", "signal", "order", "unfinished", "arm"]
)
def test_incomplete_or_changed_schedule_cannot_release(fault):
    data = cells()
    if fault == "missing":
        data.pop()
    elif fault == "duplicate":
        data[-1] = copy.deepcopy(data[0])
    elif fault == "seed":
        data[0]["plan"]["seed"] += 1
    elif fault == "signal":
        data[0]["plan"]["signal"] = "variant_low"
    elif fault == "order":
        data[0], data[1] = data[1], data[0]
    elif fault == "arm":
        data[0]["plan"]["arm"] = "R"
    else:
        data[0]["status"] = "running"
    with pytest.raises(ValueError, match="every planned"):
        coordinate.comparison(data, "anchor")


def test_failed_search_stays_in_its_pair_with_unknown_cost_and_no_replacement():
    data = cells("variant_high")
    failed = data[1]
    assert failed["plan"]["arm"] == "U"
    failed.update(status="worker_failed", A=False, A_and_original_family=False)
    failed["costs"]["worker_wall_seconds"] = None
    report = coordinate.comparison(data, "variant_high")
    output = report["pairs"][0]["outputs"]["U"]
    assert output["selected_cell"] is None
    assert output["status"] == "worker_failed"
    assert output["any_front_A"]  # Diagnostic presence never replaces the output.
    totals = report["totals"]["U"]
    assert totals["denominator"] == 4
    assert totals["A"] == 3 and totals["failures"] == 1
    assert totals["costs"]["callback_calls_during_fit"] == 40
    assert totals["costs"]["worker_wall_seconds"] is None
    assert report["all_costs_observed"] is False
    assert report["U_minus_T"]["A"] == {"gains": 0, "losses": 1, "ties": 3}
    assert "descriptive_preference" not in report


def test_physical_proof_resource_limit_is_visible_without_becoming_a_search_failure():
    data = cells()
    limited = data[1]
    limited.update(
        A_and_original_family=False,
        original_family_status="unresolved",
        physical_proof_resource_limited=True,
    )
    report = coordinate.comparison(data, "anchor")
    totals = report["totals"]["U"]
    assert totals["selected_resource_limited"] == 1
    assert totals["A"] == 2 and totals["A_and_original_family"] == 1
    assert totals["failures"] == 0
    assert (
        report["pairs"][0]["outputs"]["U"]["selected_cell"] == limited["plan"]["number"]
    )


@pytest.mark.parametrize("members", [[], [0, 1]])
def test_each_arm_is_one_search_not_a_posthoc_package(members):
    data = cells()
    with pytest.raises(ValueError, match="exactly one search"):
        coordinate.selected_output([data[index] for index in members])


@pytest.mark.parametrize("loss", [float("nan"), float("inf"), -1.0])
def test_nonfinite_or_invalid_native_loss_is_not_selected(loss):
    cell = cells()[0]
    cell["selected"]["loss"] = loss
    assert coordinate.selected_output([cell])["selected_cell"] is None


@pytest.mark.parametrize(
    "arm,expected",
    [("T", "normalization_candidate"), ("U", "raw_coordinate_supported")],
)
def test_directional_rule_requires_a_joint_gain_and_no_signal_endpoint_loss(
    arm, expected
):
    data = sections()
    data[2]["comparison"]["totals"][arm]["A_and_original_family"] -= 1
    assert coordinate.development_decision(data) == expected
    other = "U" if arm == "T" else "T"
    data[0]["comparison"]["totals"][other].update(A=1, A_and_original_family=1)
    assert coordinate.development_decision(data) == "mixed"


def test_equal_counts_and_curve_only_gain_do_not_create_new_success_threshold():
    data = sections()
    assert coordinate.development_decision(data) == "unchanged_counts"
    for arm in ("T", "U"):
        data[2]["comparison"]["totals"][arm]["A_and_original_family"] = 3
    data[2]["comparison"]["totals"]["T"]["A"] = 3
    assert coordinate.development_decision(data) == "mixed"


@pytest.mark.parametrize("fault", ["missing", "technical", "denominator", "count"])
def test_development_decision_requires_complete_scientific_counts(fault):
    data = sections()
    if fault == "missing":
        data.pop()
    elif fault == "technical":
        data[0]["scope"] = "technical"
    elif fault == "denominator":
        data[2]["comparison"]["totals"]["T"]["denominator"] = 8
    else:
        data[0]["comparison"]["totals"]["T"]["A"] = True
    with pytest.raises(ValueError):
        coordinate.development_decision(data)


def fake_native_lifecycle(monkeypatch):
    """Replace native execution only; keep inventories and publication real."""
    events = []
    software = {"software_commit": "a" * 40}
    monkeypatch.setattr(coordinate, "freeze_software", lambda consumed: software)
    monkeypatch.setattr(coordinate, "_provenance", lambda: {"fixture": True})
    monkeypatch.setattr(coordinate.previous, "one_cpu", nullcontext)
    monkeypatch.setattr(coordinate.cross, "environment_key", lambda value: value)
    monkeypatch.setattr(
        coordinate,
        "environment_at",
        lambda directory: {"environment": {}, "runtime": {}},
    )

    def bridge(action, output, request, inputs, consumed, log, verification=None):
        consumed.check()
        plan = coordinate.sources.read_json(request.read_bytes())["cell"]
        assert inputs.name == "search-" + plan["arm"] + ".npz"
        expected = profile.search_inputs(plan["signal"], plan["arm"], True)
        coordinate.previous.require_arrays(
            coordinate.previous.arrays_from(inputs.read_bytes()), expected
        )
        parent = output.parent
        # Both coordinate files must already exist even during the first prepare.
        assert (parent / "search-T.npz").exists()
        assert (parent / "search-U.npz").exists()
        events.append((action, plan["arm"]))
        log.write_text("native fixture only")
        if action == "prepare":
            output.mkdir()
            (output / "runtime.py").write_text("bound runtime fixture")
            _write_json(output / "prepared.json", {"files": ["runtime.py"]})
        elif action == "run":
            assert events[:2] == [("prepare", "T"), ("prepare", "U")]
            assert (parent / "prepared_bindings.json").exists()
            _write_json(output / "outcome.json", {"status": "completed"})
            _write_json(
                output / "verified.json",
                {"environment": {}, "environment_after_search": {}},
            )
        elif verification is not None:
            _write_json(verification, {"status": "verified"})
        consumed.check()
        return 0.25

    monkeypatch.setattr(coordinate, "call_bridge", bridge)
    monkeypatch.setattr(
        coordinate.assessment,
        "cell_record",
        lambda directory, plan, arrays, grid: cells(plan["signal"], True)[
            plan["number"] - 1
        ],
    )
    return events


def test_both_search_coordinates_are_bound_before_any_search_and_read_verified(
    monkeypatch, tmp_path
):
    events = fake_native_lifecycle(monkeypatch)
    source = tmp_path / "run"
    report = coordinate.run(source, "fixture_a", technical=True)
    assert report["real_new_search_calls"] == 2
    assert events == [
        ("prepare", "T"),
        ("prepare", "U"),
        ("run", "T"),
        ("verify", "T"),
        ("run", "U"),
        ("verify", "U"),
    ]
    bound = coordinate.load_json(source, "prepared_bindings.json")
    assert {"anchor.npz", "irregular.npz", "search-T.npz", "search-U.npz"} <= set(bound)
    verified = coordinate.verify([source], tmp_path / "verification")
    assert verified["verified_cells"] == 2 and verified["search_calls"] == 0
    assert verified["development_decision"] is None
    assert events[-2:] == [("verify", "T"), ("verify", "U")]


def test_complete_technical_series_has_four_cells_and_no_development_decision(
    monkeypatch, tmp_path
):
    roots = []
    for name in profile.names(True):
        fake_native_lifecycle(monkeypatch)
        root = tmp_path / name
        coordinate.run(root, name, technical=True)
        roots.append(root)
    report = coordinate.verify(roots, tmp_path / "verification", complete=True)
    assert report["complete_series"] is True
    assert report["verified_cells"] == 4
    assert report["search_calls"] == 0
    assert report["development_decision"] is None


@pytest.mark.parametrize("fault", ["swap", "double_scale", "truth"])
def test_resealed_coordinate_changes_are_rejected_by_read_verification(
    monkeypatch, tmp_path, fault
):
    fake_native_lifecycle(monkeypatch)
    source = tmp_path / "run"
    coordinate.run(source, "fixture_a", technical=True)
    target = source / "search-U.npz"
    arrays = profile.search_inputs("fixture_a", "T" if fault == "swap" else "U", True)
    arrays = {key: value.copy() for key, value in arrays.items()}
    if fault == "double_scale":
        arrays["time_s"] *= 32
    elif fault == "truth":
        arrays["observed"][0] += 1
    np.savez(target, **arrays)
    bound = coordinate.load_json(source, "prepared_bindings.json")
    bound[target.name] = coordinate.sources.sha256(target.read_bytes())
    _write_json(source / "prepared_bindings.json", bound)
    completion = source / "completion"
    raw = coordinate.restarts.raw_files(source)
    _write_json(
        completion / "raw_checksums.json",
        {name: coordinate.sources.sha256(value) for name, value in raw.items()},
    )
    manifest = coordinate.load_json(completion, publication.MANIFEST)
    manifest["raw_checksums.json"] = coordinate.sources.sha256(
        (completion / "raw_checksums.json").read_bytes()
    )
    _write_json(completion / publication.MANIFEST, manifest)
    with pytest.raises(ValueError):
        coordinate.verify([source], tmp_path / "verification")
    assert (tmp_path / "verification" / publication.LOCK).exists()


def fake_sections(monkeypatch, tmp_path):
    monkeypatch.setattr(coordinate, "freeze_software", lambda consumed: {})

    def read(path, consumed, software, temporary):
        name = path.name
        witness = path / "evidence"
        witness.write_text("original")
        consumed.add(witness, b"original")
        data = cells(name)
        return {
            "signal": name,
            "scope": "scientific",
            "numerical_environment": {},
            "cells": data,
            "comparison": coordinate.comparison(data, name),
            "whole_call_timing": {"wall_seconds": 2},
            "verified_cells": len(data),
        }

    monkeypatch.setattr(coordinate, "read_section", read)
    roots = [tmp_path / name for name in profile.names()]
    for root in roots:
        root.mkdir()
    return roots


@pytest.mark.parametrize(
    "fault", [None, "missing", "duplicate_signal", "environment", "late_change"]
)
def test_series_decision_requires_all_signals_and_unchanged_evidence(
    monkeypatch, tmp_path, fault
):
    roots = fake_sections(monkeypatch, tmp_path)
    read = coordinate.read_section

    def altered(path, *args):
        result = read(path, *args)
        if path == roots[-1]:
            if fault == "duplicate_signal":
                result["signal"] = "anchor"
            elif fault == "environment":
                result["numerical_environment"] = {"changed": True}
        return result

    monkeypatch.setattr(coordinate, "read_section", altered)
    if fault == "late_change":
        original = publication.verify_bytes

        def verify_bytes(output, expected, *, locked=True):
            original(output, expected, locked=locked)
            if not locked:
                (roots[0] / "evidence").write_text("changed after unlock")

        monkeypatch.setattr(publication, "verify_bytes", verify_bytes)
    output = tmp_path / "verification"
    if fault is None:
        report = coordinate.verify(roots, output, complete=True)
        assert report["verified_cells"] == 16
        assert report["development_decision"] == "unchanged_counts"
        assert report["automatic_execution"] is False
        assert [
            item["totals"]["T"]["denominator"] for item in report["comparisons"]
        ] == [2, 2, 4]
    else:
        with pytest.raises(ValueError):
            coordinate.verify(
                roots[:2] if fault == "missing" else roots, output, complete=True
            )
        assert (output / publication.LOCK).exists()
        assert "development_decision" not in coordinate.load_json(
            output, publication.REPORT
        )


@pytest.mark.parametrize("fault", ["source", "interrupt", "deadline"])
def test_late_whole_call_fault_revokes_completed_section(monkeypatch, tmp_path, fault):
    fake_native_lifecycle(monkeypatch)
    write = coordinate._write_json

    def altered(path, value):
        write(path, value)
        if path.name.endswith("-call.json"):
            if fault == "source":
                (tmp_path / "run/search-U.npz").write_bytes(b"changed after completion")
            elif fault == "interrupt":
                raise KeyboardInterrupt("late interrupt")
            else:
                monkeypatch.setattr(
                    profile, "signal_seconds", lambda technical=False: 0.0
                )

    monkeypatch.setattr(coordinate, "_write_json", altered)
    output = tmp_path / "run"
    with pytest.raises((ValueError, KeyboardInterrupt, TimeoutError)):
        coordinate.run(output, "fixture_a", technical=True)
    assert (output / "completion" / publication.LOCK).exists()
    assert coordinate.load_json(output, "run_state.json")["status"] == "aborted"
    assert "comparison" not in coordinate.load_json(
        output / "completion", publication.REPORT
    )
