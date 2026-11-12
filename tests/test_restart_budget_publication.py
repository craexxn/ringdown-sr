"""Exercise complete package execution and fail-closed publication boundaries."""

import copy
from contextlib import nullcontext

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import restart_budget as budget
from ringdown_sr import restart_budget_profile as profile
from ringdown_sr.pilot import _write_json


def cells(name="fixture_a", technical=True):
    return [
        {
            "plan": plan,
            "status": "completed",
            "A": True,
            "A_and_original_family": True,
            "curve_grade": "A",
            "original_family_status": "proven_member",
            "any_front_A": True,
            "selected": {"loss": 0.01 + plan["member"], "complexity": 9},
            "costs": {field: 10 for field in budget.previous.COST_FIELDS},
        }
        for plan in profile.plans(name, technical)
    ]


def fake_native(monkeypatch, *, failure=None):
    """Replace only native work; retain real inventories and publication."""
    events = []
    monkeypatch.setattr(
        budget, "freeze_software", lambda consumed: {"software_commit": "a" * 40}
    )
    monkeypatch.setattr(budget, "_provenance", lambda: {"fixture": True})
    monkeypatch.setattr(budget.previous, "one_cpu", nullcontext)
    monkeypatch.setattr(budget.cross, "environment_key", lambda value: value)
    monkeypatch.setattr(
        budget, "environment_at", lambda directory: {"environment": {}, "runtime": {}}
    )

    def bridge(action, output, request, inputs, consumed, log, verification=None):
        consumed.check()
        plan = budget.sources.read_json(request.read_bytes())["cell"]
        assert inputs.name == "anchor.npz"
        arrays, _ = profile.inputs(plan["signal"], True)
        budget.previous.require_arrays(
            budget.previous.arrays_from(inputs.read_bytes()), arrays
        )
        assert (output.parent / "irregular.npz").exists()
        events.append((action, plan["number"], plan["arm"], plan["seed"]))
        log.write_text("native fixture only")
        if action == "prepare":
            output.mkdir()
            (output / "runtime.py").write_text("bound runtime fixture")
            _write_json(output / "prepared.json", {"files": ["runtime.py"]})
        elif action == "run":
            assert [event[0] for event in events[:6]] == ["prepare"] * 6
            assert (output.parent / "prepared_bindings.json").exists()
            if failure == "interrupt" and plan["number"] == 2:
                raise KeyboardInterrupt("injected native interruption")
            failed = failure == "numeric" and plan["number"] == 1
            _write_json(
                output / "outcome.json",
                {"status": "worker_failed" if failed else "completed"},
            )
            _write_json(
                output / "verified.json",
                {"environment": {}, "environment_after_search": {}},
            )
        elif verification is not None:
            _write_json(verification, {"status": "verified"})
        consumed.check()
        return 0.25

    def record(directory, plan, arrays, grid):
        cell = cells(plan["signal"])[plan["number"] - 1]
        if failure == "numeric" and plan["number"] == 1:
            cell.update(status="worker_failed", A=False, A_and_original_family=False)
        return cell

    monkeypatch.setattr(budget, "call_bridge", bridge)
    monkeypatch.setattr(budget.previous, "cell_record", record)
    return events


@pytest.mark.parametrize("failure", [None, "numeric"])
def test_all_members_start_fresh_after_full_preparation_even_after_good_output(
    monkeypatch, tmp_path, failure
):
    events = fake_native(monkeypatch, failure=failure)
    source = tmp_path / "run"
    result = budget.run(source, "fixture_a", technical=True)
    assert result["real_new_search_calls"] == 6
    calls = [event for event in events if event[0] == "run"]
    assert [event[1] for event in calls] == list(range(1, 7))
    assert [event[2] for event in calls] == ["R"] * 4 + ["L"] * 2
    assert [event[3] for event in calls[:2]] == [event[3] for event in calls[4:]]
    assert calls[0][1] != calls[4][1]  # A shared seed is still a separate call.
    bound = budget.load_json(source, "prepared_bindings.json")
    assert {"anchor.npz", "irregular.npz"} <= set(bound)
    assert sum(name.endswith("prepared.json") for name in bound) == 6
    assert result["comparison"]["totals"]["R"]["denominator"] == 1
    assert result["comparison"]["totals"]["L"]["denominator"] == 1
    assert result["comparison"]["totals"]["R"]["failed_members"] == int(
        failure == "numeric"
    )
    assert result["algorithm_costs"]["callback_calls_during_fit"] == 60
    verified = budget.verify([source], tmp_path / "verification")
    assert verified["verified_cells"] == 6 and verified["search_calls"] == 0
    assert verified["development_decision"] is None
    assert len([event for event in events if event[0] == "run"]) == 6


def test_both_technical_signals_produce_four_packages_without_scientific_decision(
    monkeypatch, tmp_path
):
    roots = []
    for name in profile.names(True):
        fake_native(monkeypatch)
        root = tmp_path / name
        budget.run(root, name, technical=True)
        roots.append(root)
    result = budget.verify(roots, tmp_path / "verify", complete=True)
    assert result["complete_series"] is True
    assert result["verified_cells"] == 12 and result["search_calls"] == 0
    assert result["development_decision"] is None
    assert (
        sum(
            total["denominator"]
            for item in result["comparisons"]
            for total in item["totals"].values()
        )
        == 4
    )


def test_interruption_is_not_recorded_as_a_completed_numeric_failure(
    monkeypatch, tmp_path
):
    events = fake_native(monkeypatch, failure="interrupt")
    output = tmp_path / "run"
    with pytest.raises(KeyboardInterrupt, match="injected"):
        budget.run(output, "fixture_a", technical=True)
    assert len([event for event in events if event[0] == "run"]) == 2
    assert budget.load_json(output, "run_state.json")["status"] == "aborted"
    assert (output / "completion" / publication.LOCK).exists()
    assert "comparison" not in budget.load_json(
        output / "completion", publication.REPORT
    )


def reseal_raw(source):
    bound = budget.load_json(source, "prepared_bindings.json")
    for name in bound:
        bound[name] = budget.sources.sha256((source / name).read_bytes())
    _write_json(source / "prepared_bindings.json", bound)
    completion = source / "completion"
    raw = budget.restarts.raw_files(source)
    _write_json(
        completion / "raw_checksums.json",
        {name: budget.sources.sha256(value) for name, value in raw.items()},
    )
    manifest = budget.load_json(completion, publication.MANIFEST)
    manifest["raw_checksums.json"] = budget.sources.sha256(
        (completion / "raw_checksums.json").read_bytes()
    )
    _write_json(completion / publication.MANIFEST, manifest)


@pytest.mark.parametrize("fault", ["time", "truth", "grid", "seed", "member"])
def test_resealed_changes_still_fail_fixed_input_and_schedule_contracts(
    monkeypatch, tmp_path, fault
):
    fake_native(monkeypatch)
    source = tmp_path / "run"
    budget.run(source, "fixture_a", technical=True)
    if fault in {"seed", "member"}:
        request = budget.load_json(source, "request-05.json")
        request["cell"][fault] += 1
        _write_json(source / "request-05.json", request)
    else:
        arrays, grid = profile.inputs("fixture_a", True)
        if fault == "grid":
            changed = {key: value.copy() for key, value in grid.items()}
            changed["time_s"][0] = np.nextafter(changed["time_s"][0], np.inf)
            target = source / "irregular.npz"
        else:
            changed = {key: value.copy() for key, value in arrays.items()}
            key = "time_s" if fault == "time" else "observed"
            changed[key][0] = np.nextafter(changed[key][0], np.inf)
            target = source / "anchor.npz"
        np.savez(target, **changed)
    reseal_raw(source)
    with pytest.raises(ValueError):
        budget.verify([source], tmp_path / "verify")
    assert (tmp_path / "verify" / publication.LOCK).exists()


def fake_sections(monkeypatch, tmp_path):
    monkeypatch.setattr(budget, "freeze_software", lambda consumed: {})

    def read(path, consumed, software, temporary):
        name = path.name
        witness = path / "evidence"
        witness.write_text("original")
        consumed.add(witness, b"original")
        data = cells(name, False)
        return {
            "signal": name,
            "scope": "scientific",
            "numerical_environment": {},
            "cells": data,
            "comparison": budget.comparison(data, name),
            "algorithm_outputs": 2 * len(profile.case(name)["seeds"]),
            "whole_call_timing": {"wall_seconds": 2},
            "verified_cells": len(data),
        }

    monkeypatch.setattr(budget, "read_section", read)
    roots = [tmp_path / name for name in profile.names()]
    for root in roots:
        root.mkdir()
    return roots


@pytest.mark.parametrize(
    "fault", [None, "missing", "duplicate", "scope", "environment", "late_change"]
)
def test_scientific_decision_requires_all_sections_and_unchanged_evidence(
    monkeypatch, tmp_path, fault
):
    roots = fake_sections(monkeypatch, tmp_path)
    read = budget.read_section

    def altered(path, *args):
        result = read(path, *args)
        if path == roots[-1]:
            if fault == "duplicate":
                result["signal"] = "anchor"
            elif fault == "scope":
                result["scope"] = "technical"
            elif fault == "environment":
                result["numerical_environment"] = {"changed": True}
        return result

    monkeypatch.setattr(budget, "read_section", altered)
    if fault == "late_change":
        original = publication.verify_bytes

        def verify_bytes(output, expected, *, locked=True):
            original(output, expected, locked=locked)
            if not locked:
                (roots[0] / "evidence").write_text("changed after unlock")

        monkeypatch.setattr(publication, "verify_bytes", verify_bytes)
    output = tmp_path / "verify"
    if fault is None:
        result = budget.verify(roots, output, complete=True)
        assert result["verified_cells"] == 48 and result["search_calls"] == 0
        assert result["development_decision"] == "unchanged_counts"
        assert result["automatic_execution"] is False
        assert [c["totals"]["R"]["denominator"] for c in result["comparisons"]] == [
            2,
            2,
            4,
        ]
    else:
        with pytest.raises(ValueError):
            budget.verify(
                roots[:2] if fault == "missing" else roots, output, complete=True
            )
        assert (output / publication.LOCK).exists()
        assert "development_decision" not in budget.load_json(
            output, publication.REPORT
        )


@pytest.mark.parametrize("fault", ["source", "interrupt", "deadline"])
def test_late_whole_call_fault_revokes_completed_section(monkeypatch, tmp_path, fault):
    fake_native(monkeypatch)
    write = budget._write_json

    def altered(path, value):
        write(path, value)
        if path.name.endswith("-call.json"):
            if fault == "source":
                (tmp_path / "run/anchor.npz").write_bytes(b"changed after completion")
            elif fault == "interrupt":
                raise KeyboardInterrupt("late interrupt")
            else:
                monkeypatch.setattr(
                    profile, "signal_seconds", lambda technical=False: 0.0
                )

    monkeypatch.setattr(budget, "_write_json", altered)
    output = tmp_path / "run"
    with pytest.raises((ValueError, KeyboardInterrupt, TimeoutError)):
        budget.run(output, "fixture_a", technical=True)
    assert (output / "completion" / publication.LOCK).exists()
    assert budget.load_json(output, "run_state.json")["status"] == "aborted"
    assert "comparison" not in budget.load_json(
        output / "completion", publication.REPORT
    )


def test_external_report_edits_cannot_be_promoted_by_hash_resealing(
    monkeypatch, tmp_path
):
    fake_native(monkeypatch)
    source = tmp_path / "run"
    budget.run(source, "fixture_a", technical=True)
    completion = source / "completion"
    report = budget.load_json(completion, publication.REPORT)
    changed = copy.deepcopy(report)
    changed["comparison"]["pairs"][0]["outputs"]["L"]["selected_cell"] = 6
    _write_json(completion / publication.REPORT, changed)
    manifest = budget.load_json(completion, publication.MANIFEST)
    manifest[publication.REPORT] = budget.sources.sha256(
        (completion / publication.REPORT).read_bytes()
    )
    _write_json(completion / publication.MANIFEST, manifest)
    call_path = source.with_name(source.name + "-call.json")
    call = budget.sources.read_json(call_path.read_bytes())
    call["source_report_sha256"] = manifest[publication.REPORT]
    _write_json(call_path, call)
    with pytest.raises(ValueError, match="result differs"):
        budget.verify([source], tmp_path / "verify")
    assert (tmp_path / "verify" / publication.LOCK).exists()
