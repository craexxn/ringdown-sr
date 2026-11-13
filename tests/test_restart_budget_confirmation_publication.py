"""Exercise complete execution and revocation without scientific searches."""

import copy
from contextlib import nullcontext

import numpy as np
import pytest
from test_restart_budget_confirmation import cells

from ringdown_sr import assessment_publication as publication
from ringdown_sr import restart_budget_confirmation as confirmation
from ringdown_sr import restart_budget_confirmation_profile as profile
from ringdown_sr.pilot import _write_json


def fake_native(monkeypatch, failure=None):
    """Stub only native execution, retaining files, bindings and publication."""
    events = []
    monkeypatch.setattr(
        confirmation, "freeze_software", lambda consumed: {"software_commit": "a" * 40}
    )
    monkeypatch.setattr(confirmation, "_provenance", lambda: {"fixture": True})
    monkeypatch.setattr(confirmation.previous, "one_cpu", nullcontext)
    monkeypatch.setattr(confirmation.cross, "scientific_platform", lambda: None)
    monkeypatch.setattr(confirmation.cross, "environment_key", lambda value: value)
    monkeypatch.setattr(
        confirmation,
        "environment_at",
        lambda directory: {"environment": {}, "runtime": {}},
    )

    def bridge(action, output, request, inputs, consumed, log, verification=None):
        consumed.check()
        document = confirmation.sources.read_json(request.read_bytes())
        plan = document["cell"]
        technical = document["scope"] == "technical"
        arrays, _ = profile.inputs(plan["signal"], technical)
        confirmation.previous.require_arrays(
            confirmation.previous.arrays_from(inputs.read_bytes()), arrays
        )
        events.append(
            (action, plan["signal"], plan["number"], plan["arm"], plan["seed"])
        )
        log.write_text("synthetic native execution")
        if action == "prepare":
            output.mkdir()
            (output / "runtime.py").write_text("bound runtime fixture")
            _write_json(output / "prepared.json", {"files": ["runtime.py"]})
        elif action == "run":
            assert (output.parent / "prepared_bindings.json").exists()
            assert (output.parent / "irregular.npz").exists()
            prepared = [
                e for e in events if e[0] == "prepare" and e[1] == plan["signal"]
            ]
            assert len(prepared) == len(profile.plans(plan["signal"], technical))
            if failure == "interrupt" and plan["number"] == 2:
                raise KeyboardInterrupt("synthetic worker interruption")
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
        technical = plan["signal"] in profile.names(True)
        cell = cells(plan["signal"], technical)[plan["number"] - 1]
        if failure == "numeric" and plan["number"] == 1:
            cell.update(status="worker_failed", A=False, A_and_original_family=False)
        return cell

    monkeypatch.setattr(confirmation, "call_bridge", bridge)
    monkeypatch.setattr(confirmation.previous, "cell_record", record)
    return events


@pytest.mark.parametrize("failure", [None, "numeric"])
def test_every_member_runs_before_partial_read_verification_without_release(
    monkeypatch, tmp_path, failure
):
    events = fake_native(monkeypatch, failure)
    source = tmp_path / "run"
    result = confirmation.run(source, "fixture_a", technical=True)
    calls = [event for event in events if event[0] == "run"]
    assert [event[2] for event in calls] == list(range(1, 7))
    assert [event[3] for event in calls] == ["R"] * 4 + ["L"] * 2
    assert [event[4] for event in calls[:2]] == [event[4] for event in calls[4:]]
    assert result["real_new_search_calls"] == 6
    assert result["algorithm_outputs"] == 2
    assert result["comparison"]["totals"]["R"]["failed_members"] == int(
        failure == "numeric"
    )
    verified = confirmation.verify([source], tmp_path / "verification")
    assert verified["verified_cells"] == 6 and verified["search_calls"] == 0
    assert verified["transition_criterion_met"] is None
    assert verified["L_control_criterion_met"] is None
    assert len([event for event in events if event[0] == "run"]) == 6


def test_all_180_synthetic_calls_produce_60_outputs_and_require_joint_verification(
    monkeypatch, tmp_path
):
    events = fake_native(monkeypatch)
    roots = []
    for name in profile.names():
        root = tmp_path / name
        report = confirmation.run(root, name)
        assert report["real_new_search_calls"] == 60
        assert report["algorithm_outputs"] == 20
        assert "transition_criterion_met" not in report
        roots.append(root)
    partial = confirmation.verify([roots[0]], tmp_path / "partial")
    assert partial["transition_criterion_met"] is None
    assert partial["L_control_criterion_met"] is None
    report = confirmation.verify(roots, tmp_path / "complete", complete=True)
    assert report["verified_cells"] == 180
    assert report["algorithm_outputs"] == 60
    assert report["transition_criterion_met"] is True
    assert report["L_control_criterion_met"] is True
    assert report["search_calls"] == 0 and report["automatic_execution"] is False
    assert len([event for event in events if event[0] == "run"]) == 180
    assert report["sum_section_call_wall_seconds_excluding_pauses"] > 0


def test_both_technical_sections_verify_without_scientific_confirmation(
    monkeypatch, tmp_path
):
    fake_native(monkeypatch)
    roots = []
    for name in profile.names(True):
        root = tmp_path / name
        confirmation.run(root, name, technical=True)
        roots.append(root)
    report = confirmation.verify(roots, tmp_path / "complete", complete=True)
    assert report["verified_cells"] == 12 and report["algorithm_outputs"] == 4
    assert report["transition_criterion_met"] is None
    assert report["L_control_criterion_met"] is None


def test_interruption_retains_partial_state_and_blocks_completion(
    monkeypatch, tmp_path
):
    events = fake_native(monkeypatch, "interrupt")
    root = tmp_path / "run"
    with pytest.raises(KeyboardInterrupt, match="synthetic"):
        confirmation.run(root, "fixture_a", technical=True)
    assert len([event for event in events if event[0] == "run"]) == 2
    assert confirmation.load_json(root, "run_state.json")["status"] == "aborted"
    assert (root / "completion" / publication.LOCK).exists()
    assert "comparison" not in confirmation.load_json(
        root / "completion", publication.REPORT
    )


def reseal(source):
    bound = confirmation.load_json(source, "prepared_bindings.json")
    for name in bound:
        bound[name] = confirmation.sources.sha256((source / name).read_bytes())
    _write_json(source / "prepared_bindings.json", bound)
    completion = source / "completion"
    raw = confirmation.restarts.raw_files(source)
    _write_json(
        completion / "raw_checksums.json",
        {name: confirmation.sources.sha256(value) for name, value in raw.items()},
    )
    manifest = confirmation.load_json(completion, publication.MANIFEST)
    manifest["raw_checksums.json"] = confirmation.sources.sha256(
        (completion / "raw_checksums.json").read_bytes()
    )
    _write_json(completion / publication.MANIFEST, manifest)


@pytest.mark.parametrize(
    "fault", ["time", "truth", "grid", "seed", "member", "provenance"]
)
def test_resealed_raw_changes_cannot_replace_frozen_evidence(
    monkeypatch, tmp_path, fault
):
    fake_native(monkeypatch)
    source = tmp_path / "run"
    confirmation.run(source, "fixture_a", technical=True)
    if fault in {"seed", "member"}:
        request = confirmation.load_json(source, "request-05.json")
        request["cell"][fault] += 1
        _write_json(source / "request-05.json", request)
    elif fault == "provenance":
        prepared = confirmation.load_json(source, "preparation.json")
        prepared["provenance"] = {"wrong": True}
        _write_json(source / "preparation.json", prepared)
    else:
        arrays, grid = profile.inputs("fixture_a", True)
        target = source / ("irregular.npz" if fault == "grid" else "anchor.npz")
        changed = grid if fault == "grid" else arrays
        key = "observed" if fault == "truth" else "time_s"
        changed[key][0] = np.nextafter(changed[key][0], np.inf)
        np.savez(target, **changed)
    reseal(source)
    with pytest.raises(ValueError):
        confirmation.verify([source], tmp_path / "verify")
    assert (tmp_path / "verify" / publication.LOCK).exists()


def synthetic_sections(monkeypatch, tmp_path):
    monkeypatch.setattr(confirmation, "freeze_software", lambda consumed: {})

    def read(path, consumed, software, temporary):
        witness = path / "evidence"
        witness.write_text("original")
        consumed.add(witness, b"original")
        data = cells(path.name)
        return {
            "signal": path.name,
            "scope": "scientific",
            "numerical_environment": {},
            "cells": data,
            "comparison": confirmation.comparison(data, path.name),
            "algorithm_outputs": 20,
            "whole_call_timing": {"wall_seconds": 2},
            "verified_cells": 60,
        }

    monkeypatch.setattr(confirmation, "read_section", read)
    roots = [tmp_path / name for name in profile.names()]
    for root in roots:
        root.mkdir()
    return roots


@pytest.mark.parametrize(
    "fault",
    ["missing", "duplicate", "scope", "environment", "after_unlock", "after_return"],
)
def test_partial_mixed_or_late_changed_series_cannot_release(
    monkeypatch, tmp_path, fault
):
    roots = synthetic_sections(monkeypatch, tmp_path)
    read = confirmation.read_section

    def changed(path, *args):
        report = read(path, *args)
        if path == roots[-1]:
            if fault == "duplicate":
                report["signal"] = profile.names()[0]
            elif fault == "scope":
                report["scope"] = "technical"
            elif fault == "environment":
                report["numerical_environment"] = {"changed": True}
        return report

    monkeypatch.setattr(confirmation, "read_section", changed)
    if fault == "after_unlock":
        original = publication.verify_bytes

        def altered(output, expected, *, locked=True):
            original(output, expected, locked=locked)
            if not locked:
                (roots[0] / "evidence").write_text("changed after unlock")

        monkeypatch.setattr(publication, "verify_bytes", altered)
    elif fault == "after_return":
        original = publication.export_transaction

        def altered(*args, **kwargs):
            result = original(*args, **kwargs)
            (roots[0] / "evidence").write_text("changed after publication")
            return result

        monkeypatch.setattr(publication, "export_transaction", altered)
    target = tmp_path / "verify"
    with pytest.raises(ValueError):
        confirmation.verify(
            roots[:2] if fault == "missing" else roots, target, complete=True
        )
    assert (target / publication.LOCK).exists()
    report = confirmation.load_json(target, publication.REPORT)
    assert "transition_criterion_met" not in report
    assert "L_control_criterion_met" not in report


@pytest.mark.parametrize("fault", ["source", "interrupt", "deadline"])
def test_late_call_fault_revokes_previously_completed_section(
    monkeypatch, tmp_path, fault
):
    fake_native(monkeypatch)
    write = confirmation._write_json

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

    monkeypatch.setattr(confirmation, "_write_json", altered)
    root = tmp_path / "run"
    with pytest.raises((ValueError, KeyboardInterrupt, TimeoutError)):
        confirmation.run(root, "fixture_a", technical=True)
    assert (root / "completion" / publication.LOCK).exists()
    assert confirmation.load_json(root, "run_state.json")["status"] == "aborted"
    assert "comparison" not in confirmation.load_json(
        root / "completion", publication.REPORT
    )


def test_hash_resealing_cannot_change_the_original_package_selection(
    monkeypatch, tmp_path
):
    fake_native(monkeypatch)
    source = tmp_path / "run"
    confirmation.run(source, "fixture_a", technical=True)
    completion = source / "completion"
    report = copy.deepcopy(confirmation.load_json(completion, publication.REPORT))
    report["comparison"]["pairs"][0]["outputs"]["L"]["selected_cell"] = 6
    _write_json(completion / publication.REPORT, report)
    manifest = confirmation.load_json(completion, publication.MANIFEST)
    manifest[publication.REPORT] = confirmation.sources.sha256(
        (completion / publication.REPORT).read_bytes()
    )
    _write_json(completion / publication.MANIFEST, manifest)
    path = source.with_name(source.name + "-call.json")
    timing = confirmation.sources.read_json(path.read_bytes())
    timing["source_report_sha256"] = manifest[publication.REPORT]
    _write_json(path, timing)
    with pytest.raises(ValueError, match="result differs"):
        confirmation.verify([source], tmp_path / "verify")
