"""Exercise paired block publication and safe whole-case continuation."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_followup as study
from ringdown_sr.pilot import _write_json


def read(path):
    return json.loads(Path(path).read_bytes())


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    """Replace only external input/native gates, retaining real assessments."""
    times = np.arange(9, dtype=np.float64) / 4096
    jitter = times.copy()
    jitter[1:-1] += 0.1 / 4096
    diagnostic = (np.arange(8, dtype=np.float64) + 0.5) / 4096
    irregular = (np.arange(7, dtype=np.float64) + 0.3) / 4096
    common = {
        "time_s": times,
        "signal": np.exp(-4 * times),
        "jitter_time_s": jitter,
        "jitter_signal": np.exp(-4 * jitter),
        "diagnostic_time_s": diagnostic,
        "diagnostic_truth": np.exp(-4 * diagnostic),
        "irregular_time_s": irregular,
        "irregular_truth": np.exp(-4 * irregular),
    }
    software = {"software_commit": "1" * 40, "source_sha256": {"fixture.py": "2" * 64}}
    environment = {"julia": "synthetic", "threads": 1}
    cases = {}
    for model, count in (("ar1", 20), ("white", 6)):
        for index in range(1, count + 1):
            name = f"{model}-{index:02d}"
            noise = np.linspace(-0.05, 0.05, len(times), dtype=np.float64)
            matrix = np.eye(len(times), dtype=np.float64)
            cases[name] = SimpleNamespace(
                spec={
                    "id": name,
                    "noise_model": model,
                    "block": index,
                    "search_seeds": [index * 4 + n for n in range(1, 5)],
                },
                arrays={
                    "noise": noise,
                    "observed": common["signal"] + noise,
                    "covariance_true": matrix * 0.25,
                    "jitter_noise": noise + 0.01,
                    "jitter_observed": common["jitter_signal"] + noise + 0.01,
                    "jitter_covariance_true": matrix * 0.28,
                    "covariance_raw_64s": matrix * 0.30,
                    "covariance_estimated_64s": matrix * 0.30,
                    "covariance_raw_4096s": matrix * 0.35,
                    "covariance_estimated_4096s": matrix * 0.35,
                },
                record={
                    "status": "ready",
                    "arm_status": dict.fromkeys(study.inputs.ARMS, "ready"),
                },
            )
    preparation = tmp_path / "inputs"
    preparation.mkdir()
    source = preparation / "source.txt"
    source.write_text("fixed prospective input and software")
    prepared = SimpleNamespace(
        root=preparation,
        manifest={"technical": False, "purpose": "scientific", "software": software},
        common=common,
        cases={key: case.spec for key, case in cases.items()},
        call={},
    )
    _write_json(preparation / "preparation.json", prepared.manifest)
    technical = tmp_path / "technical"
    diagnostics = tmp_path / "estimators"
    technical_report = {
        "status": "completed",
        "software": software,
        "numerical_environment": environment,
    }
    diagnostic_report = {
        "status": "completed",
        "software": software,
        "cases": 12,
        "estimates": 48,
    }
    for path, report in (
        (technical, technical_report),
        (diagnostics, diagnostic_report),
    ):
        (path / "completion").mkdir(parents=True)
        _write_json(path / "completion" / publication.REPORT, report)
    fixture = SimpleNamespace(
        prepared=prepared,
        preparation=preparation,
        technical=technical,
        diagnostics=diagnostics,
        cases=cases,
        source=source,
        events=[],
        gate_events=[],
        mutate_package=None,
        fail_condition=None,
    )

    def verify_inputs(path, consumed=None):
        assert Path(path) == preparation
        study._read(source, consumed)
        sources._same(
            study._json(preparation / "preparation.json", consumed),
            prepared.manifest,
            "Changed fixture preparation.",
        )
        return prepared

    def read_case(loaded, case_id, consumed=None, **kwargs):
        assert loaded is prepared
        study._read(source, consumed)
        return cases[case_id]

    def gate(path, *, consumed=None, **kwargs):
        fixture.gate_events.append(Path(path).name)
        return study._json(Path(path) / "completion" / publication.REPORT, consumed)

    def run_package(time_s, observed, *, covariance, output, seeds):
        output = Path(output)
        case_id, condition = output.parent.parent.name, output.name
        if condition == fixture.fail_condition:
            output.mkdir(parents=True)
            (output / "partial.log").write_text("original interrupted worker")
            raise KeyboardInterrupt("synthetic interrupted worker")
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        fixture.events.extend((case_id, condition, seed) for seed in seeds)
        selected = {
            "tree": {"kind": "constant", "value_hex": (0.25).hex()},
            "prediction": np.full_like(time_s, 0.25).tolist(),
            "loss": 0.125,
            "complexity": 1,
            "display_equation": "0.25",
        }
        costs = dict.fromkeys(study.COST_FIELDS, 0.0)
        costs["callback_calls_during_fit"] = 100
        report = {
            "package_status": "success",
            "selected_member": 0,
            "selected_candidate": selected,
            "search_calls": 4,
            "members": [
                {
                    "member": n,
                    "seed": seed,
                    "status": "completed",
                    "costs": copy.deepcopy(costs),
                }
                for n, seed in enumerate(seeds)
            ],
            "costs": costs,
            "technical": False,
            "profile": study.search.PROFILE,
            "seeds": list(seeds),
            "software": copy.deepcopy(software),
            "numerical_environment": copy.deepcopy(environment),
            "input_fingerprints": {
                key: sources.fingerprint(value) for key, value in arrays.items()
            },
        }
        if fixture.mutate_package is not None:
            fixture.mutate_package(condition, report)
        (output / "completion").mkdir(parents=True)
        _write_json(output / "completion" / publication.REPORT, report)
        return report

    monkeypatch.setattr(study.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(study.inputs, "read_case", read_case)
    monkeypatch.setattr(study.technical, "verify", gate)
    monkeypatch.setattr(study.diagnostics_module, "verify", gate)
    monkeypatch.setattr(study.search, "run_confirmed_package", run_package)
    monkeypatch.setattr(
        study.search,
        "verify_confirmed_package",
        lambda path: read(Path(path) / "completion" / publication.REPORT),
    )
    return fixture


def run(fixture, output, **kwargs):
    return study.run(
        fixture.preparation,
        fixture.technical,
        output,
        diagnostics=fixture.diagnostics,
        **kwargs,
    )


def verify(fixture, output, **kwargs):
    return study.verify(
        fixture.preparation,
        fixture.technical,
        output,
        diagnostics=fixture.diagnostics,
        **kwargs,
    )


def test_duration_all_packages_and_read_only_replay(boundary, tmp_path):
    output = tmp_path / "duration"
    report = run(boundary, output)
    assert report["new_search_calls"] == 416
    assert report["reused_control_outputs"] == 0
    assert len(report["assessments"]) == 104
    assert len(boundary.events) == 416
    before = study._tree_hashes(output)
    assert verify(boundary, output) == report
    assert study._tree_hashes(output) == before
    assert run(boundary, output) == report
    assert len(boundary.events) == 416
    assert study._tree_hashes(output) == before


def test_sampling_reuses_exact_controls_and_counts_only_new_work(boundary, tmp_path):
    duration, sampling = tmp_path / "duration", tmp_path / "sampling"
    old = run(boundary, duration)
    before = study._tree_hashes(duration)
    report = run(boundary, sampling, block="sampling", uniform=duration)
    assert boundary.gate_events == ["technical", "estimators"] * 2
    assert report["new_search_calls"] == 208
    assert report["reused_control_outputs"] == 52
    assert len(report["assessments"]) == 104
    assert len(boundary.events) == 624
    old_controls = [
        r
        for r in old["assessments"]
        if r["source_identity"]["condition"] in study.inputs.ARMS_A[:2]
    ]
    new_controls = [
        r
        for r in report["assessments"]
        if r["source_identity"]["condition"] in study.inputs.ARMS_A[:2]
    ]
    assert new_controls == old_controls
    assert verify(boundary, sampling, block="sampling", uniform=duration) == report
    assert boundary.gate_events == ["technical", "estimators"] * 3
    assert study._tree_hashes(duration) == before


def test_pause_and_continue_only_whole_cases(boundary, tmp_path):
    output = tmp_path / "duration"
    first = run(boundary, output, max_cases=1)
    assert first["status"] == "paused"
    assert not (output / "completion").exists()
    case_before = study._tree_hashes(output / "cases/ar1-01")
    old_call = (output / "calls/0001.json").read_bytes()
    second = run(boundary, output, max_cases=1)
    assert second["status"] == "paused"
    assert second["new_cases_this_call"] == 1
    assert len(boundary.events) == 32
    assert study._tree_hashes(output / "cases/ar1-01") == case_before
    assert (output / "calls/0001.json").read_bytes() == old_call
    report = run(boundary, output)
    assert report["new_search_calls"] == 416
    assert len(boundary.events) == 416
    assert verify(boundary, output) == report


def test_interrupted_case_never_retried_or_overwritten(boundary, tmp_path):
    output = tmp_path / "duration"
    boundary.fail_condition = "known_covariance"
    with pytest.raises(KeyboardInterrupt):
        run(boundary, output)
    original_case = study._tree_hashes(output / "cases/ar1-01")
    events = len(boundary.events)
    boundary.fail_condition = None
    with pytest.raises((ValueError, FileNotFoundError)):
        run(boundary, output)
    assert len(boundary.events) == events
    assert study._tree_hashes(output / "cases/ar1-01") == original_case
    assert not (output / "completion").exists()
    assert read(output / "calls/0001.json")["status"] == "aborted"


@pytest.mark.parametrize(
    "field,value",
    [
        ("technical", True),
        ("profile", "wrong"),
        ("seeds", [1, 2, 3, 4]),
        ("software", {}),
        ("input_fingerprints", {}),
        ("numerical_environment", {"wrong": 1}),
    ],
)
def test_wrong_package_binding_blocks_case_release(boundary, tmp_path, field, value):
    boundary.mutate_package = lambda condition, report: report.update({field: value})
    output = tmp_path / "duration"
    with pytest.raises(ValueError):
        run(boundary, output, max_cases=1)
    assert read(output / "run_state.json")["status"] == "aborted"
    assert (output / "cases/ar1-01/completion" / publication.LOCK).exists()


@pytest.mark.parametrize("gate_name", ["technical", "diagnostics"])
def test_gate_software_mismatch_prevents_any_search(boundary, tmp_path, gate_name):
    path = getattr(boundary, gate_name) / "completion" / publication.REPORT
    changed = read(path)
    changed["software"] = {"different": "source"}
    _write_json(path, changed)
    with pytest.raises(ValueError, match="different software"):
        run(boundary, tmp_path / "duration")
    assert boundary.events == []


def test_sampling_needs_complete_bound_duration(boundary, tmp_path):
    with pytest.raises(ValueError, match="completed paired duration"):
        run(boundary, tmp_path / "sampling", block="sampling")
    duration = tmp_path / "duration"
    run(boundary, duration, max_cases=1)
    count = len(boundary.events)
    with pytest.raises(ValueError):
        run(boundary, tmp_path / "sampling", block="sampling", uniform=duration)
    assert len(boundary.events) == count


@pytest.mark.parametrize("limit", [True, 0, -1, 27, 1.0])
def test_invalid_pause_limit_has_no_side_effects(boundary, tmp_path, limit):
    output = tmp_path / "duration"
    with pytest.raises(ValueError, match="max_cases"):
        run(boundary, output, max_cases=limit)
    assert not output.exists()
    assert boundary.events == []


def test_changed_continuation_registration_blocks_new_work(boundary, tmp_path):
    output = tmp_path / "duration"
    run(boundary, output, max_cases=1)
    registration = read(output / "registration.json")
    registration["new_conditions"] = ["ordinary"]
    _write_json(output / "registration.json", registration)
    with pytest.raises(ValueError, match="registration"):
        run(boundary, output)
    assert len(boundary.events) == 16


def test_missing_completed_case_costs_prevent_continuation(boundary, tmp_path):
    output = tmp_path / "duration"
    run(boundary, output, max_cases=1)
    (output / "cases/ar1-01-call.json").unlink()
    with pytest.raises(ValueError, match="regular pilot artifact"):
        run(boundary, output)
    assert len(boundary.events) == 16


def test_late_source_mutation_revokes_case_release(boundary, tmp_path, monkeypatch):
    original = publication.publish

    def late(*args, **kwargs):
        report = original(*args, **kwargs)
        boundary.source.write_text("changed after publication")
        return report

    monkeypatch.setattr(publication, "publish", late)
    output = tmp_path / "duration"
    with pytest.raises(ValueError, match="changed"):
        run(boundary, output, max_cases=1)
    assert (output / "cases/ar1-01/completion" / publication.LOCK).exists()


def test_read_only_outer_guard_remains_live(boundary, tmp_path):
    output = tmp_path / "duration"
    run(boundary, output)
    guard = publication.Consumption(publication.Deadline(60))
    verify(boundary, output, consumed=guard)
    (
        output / "cases/ar1-01/symbolic/ordinary/completion" / publication.REPORT
    ).write_text("changed after verification")
    with pytest.raises(ValueError, match="changed"):
        guard.check()


def test_unavailable_estimated_condition_is_retained_without_fallback(
    boundary, tmp_path
):
    boundary.cases["ar1-01"].record["arm_status"]["estimated_64s"] = "not_run"
    boundary.cases["ar1-01"].arrays["covariance_raw_64s"] = None
    boundary.cases["ar1-01"].arrays["covariance_estimated_64s"] = None
    report = run(boundary, tmp_path / "duration")
    unavailable = next(
        r
        for r in report["assessments"]
        if r["source_identity"]["model"] == "ar1"
        and r["source_identity"]["block"] == 1
        and r["source_identity"]["condition"] == "estimated_64s"
    )
    assert unavailable["status"] == "not_run"
    assert unavailable["primary"]["value"] is None
    assert report["new_search_calls"] == 412
    assert report["planned_new_search_calls"] == 416


def test_symlinked_artifact_trees_are_rejected(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "source").write_text("data")
    (root / "link").symlink_to(root / "source")
    with pytest.raises(ValueError, match="regular"):
        study._tree_hashes(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("wall_seconds", 0.0),
        ("cpu_measurement_complete", False),
        ("reused_case_ids", ["ar1-01"]),
        ("new_case_ids", []),
        ("unexpected", 1),
    ],
)
def test_tampered_invocation_costs_block_new_work(boundary, tmp_path, field, value):
    output = tmp_path / "duration"
    run(boundary, output, max_cases=1)
    path = output / "calls/0001.json"
    record = read(path)
    record[field] = value
    _write_json(path, record)
    before = len(boundary.events)
    with pytest.raises(ValueError):
        run(boundary, output, max_cases=1)
    assert len(boundary.events) == before


def test_existing_verification_export_is_untouched(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    (output / "original.txt").write_text("original evidence")
    before = study._tree_hashes(output)
    frozen = publication.Consumption(publication.Deadline(30))
    with pytest.raises(ValueError, match="new assessment directory"):
        study._export(output, {"status": "completed"}, frozen)
    assert study._tree_hashes(output) == before


def test_missing_invocation_history_blocks_work_before_any_new_worker(
    boundary, tmp_path
):
    output = tmp_path / "duration"
    run(boundary, output, max_cases=1)
    (output / "calls/0001.json").unlink()
    with pytest.raises(ValueError, match="cost history"):
        run(boundary, output)
    assert len(boundary.events) == 16


def test_interruption_after_complete_case_can_continue_without_retry(
    boundary, tmp_path, monkeypatch
):
    output = tmp_path / "duration"
    original = study._write_json
    interrupted = False

    def interrupt_once(path, value):
        nonlocal interrupted
        if (
            Path(path) == output / "run_state.json"
            and not interrupted
            and value.get("status") == "running"
            and value["cases"][0]["status"] == "completed"
        ):
            interrupted = True
            raise KeyboardInterrupt("between complete cases")
        return original(path, value)

    monkeypatch.setattr(study, "_write_json", interrupt_once)
    with pytest.raises(KeyboardInterrupt, match="between complete cases"):
        run(boundary, output)
    original_case = study._tree_hashes(output / "cases/ar1-01")
    report = run(boundary, output)
    assert report["new_search_calls"] == 416
    assert len(boundary.events) == 416
    assert study._tree_hashes(output / "cases/ar1-01") == original_case
    assert verify(boundary, output) == report


def test_late_case_failure_replaces_own_completed_costs(
    boundary, tmp_path, monkeypatch
):
    output = tmp_path / "duration"

    def fail_after_cost_write(*args, **kwargs):
        raise ValueError("late case failure")

    monkeypatch.setattr(study, "_case_timing", fail_after_cost_write)
    with pytest.raises(ValueError, match="late case failure"):
        run(boundary, output, max_cases=1)
    assert read(output / "cases/ar1-01-call.json")["status"] == "aborted"
    assert read(output / "calls/0001.json")["status"] == "aborted"
    assert (output / "cases/ar1-01/completion" / publication.LOCK).exists()
    assert (
        read(output / "cases/ar1-01/completion" / publication.REPORT)["status"]
        == "failed"
    )


def test_failure_cost_write_does_not_mask_worker_interruption(
    boundary, tmp_path, monkeypatch
):
    boundary.fail_condition = "ordinary"

    def fail_cost(*args, **kwargs):
        raise OSError("synthetic unwritable cost evidence")

    monkeypatch.setattr(study, "_write_exclusive", fail_cost)
    with pytest.raises(
        KeyboardInterrupt, match="synthetic interrupted worker"
    ) as caught:
        run(boundary, tmp_path / "duration", max_cases=1)
    assert any("case-call costs" in note for note in caught.value.__notes__)
    assert any("series-call costs" in note for note in caught.value.__notes__)


@pytest.mark.parametrize("extra", ["unexpected.txt", "cases/ar1-01/unexpected.txt"])
def test_late_inventory_additions_invalidate_outer_read_guard(
    boundary, tmp_path, extra
):
    output = tmp_path / "duration"
    run(boundary, output)
    guard = publication.Consumption(publication.Deadline(600))
    verify(boundary, output, consumed=guard)
    (output / extra).write_text("late artifact")
    with pytest.raises(ValueError, match="inventory"):
        guard.check()
