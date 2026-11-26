"""Check all eight technical paths, original binding, and abort accounting."""

import copy
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import confirmed_profile as profile
from ringdown_sr import confirmed_search, symbolic
from ringdown_sr import main_study_technical as technical
from ringdown_sr.pilot import _write_json


@pytest.fixture
def probe(monkeypatch, tmp_path):
    software = {"software_commit": "a" * 40, "source_sha256": {"bound": "b" * 64}}
    environment = {"numerical": "same-native-runtime"}
    cases = []
    for index, signal_id in enumerate(technical.SIGNALS):
        cases.append(
            SimpleNamespace(
                spec={
                    "id": signal_id + "-technical-ar1",
                    "signal_id": signal_id,
                    "noise_model": "ar1",
                    "sampling": {"n_samples": 103, "sample_rate_hz": 4096.0},
                    "search_seeds": [123456789 + index],
                    "niterations": 10,
                },
                observed=np.arange(103, dtype=float) + index,
                record={"arm_status": {arm: "ready" for arm in technical.ARMS}},
            )
        )
    prepared = SimpleNamespace(
        manifest={
            "purpose": "technical",
            "technical": True,
            "software": software,
            "planned_search_calls": 8,
        },
        common={"time_s": np.arange(103, dtype=float) / 4096},
        cases={case.spec["id"]: case.spec for case in cases},
        call={"wall_seconds": 0.0, "cpu_user_seconds": 0.0, "cpu_system_seconds": 0.0},
        test_cases=cases,
    )
    expected_specs = copy.deepcopy([case.spec for case in cases])
    calls, changes = [], {}
    root = tmp_path / "technical"

    def prepare_inputs(path, *, purpose):
        assert purpose == "technical"
        path.mkdir()
        _write_json(path / "preparation.json", prepared.manifest)
        (path / "fixed-input.bin").write_bytes(b"bound prospective input")
        _write_json(path.parent / "inputs-call.json", {"preparation": "complete"})
        return prepared.manifest

    def verify_inputs(path, consumed=None):
        if consumed is not None:
            for item in Path(path).iterdir():
                consumed.add(item, item.read_bytes())
        return prepared

    def arm_arrays(prepared, case, arm):
        arrays = {
            "time_s": prepared.common["time_s"],
            "observed": case.observed,
        }
        if arm != "ordinary":
            arrays["covariance"] = (np.eye(103) + 0.2) * technical.ARMS.index(arm)
        return arrays

    def prepare_member(path, time_s, observed, *, covariance=None, seed, technical):
        assert technical is True
        case = next(case for case in cases if case.spec["id"] == path.parent.name)
        assert time_s.shape == observed.shape == (103,)
        assert seed == case.spec["search_seeds"][0]
        path.mkdir(parents=True)
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        _write_json(path / "prepared.json", {"provenance": software})
        _write_json(path / "fingerprints.json", confirmed_search._fingerprints(arrays))

    def prepared_files(path):
        return {
            name: (path / name).read_bytes()
            for name in ("prepared.json", "fingerprints.json")
        }

    def check_provenance(actual, expected):
        if actual != expected:
            raise ValueError("Contradictory provenance.")

    def run_member(path, *, deadline):
        case = next(case for case in cases if case.spec["id"] == path.parent.name)
        assert 0 < deadline - technical.time.monotonic() <= 600
        assert all(
            (
                technical._directory(root, other.spec["id"], arm) / "prepared.json"
            ).is_file()
            for other in cases
            for arm in technical.ARMS
        )
        key = f"{case.spec['id']}/{path.name}"
        calls.append(key)
        record = {
            "format": profile.MAIN_WIDTH_FORMAT,
            "requested_iterations": 10,
            "profile": profile.PROFILE,
            "technical": True,
            "seed": case.spec["search_seeds"][0],
            "status": "completed",
            "numerical_environment": environment,
            "provenance": software,
            "input_fingerprints": profile.read(path, "fingerprints.json"),
            "costs": {
                name: 1 if name == "callback_calls_during_fit" else 0.0
                for name in technical.costs.COST_FIELDS
            },
        }
        record.update(changes.get(key, {}))
        _write_json(path / "result.json", record)
        return record

    monkeypatch.setattr(technical.inputs, "prepare_inputs", prepare_inputs)
    monkeypatch.setattr(technical.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(
        technical.inputs, "case_specs", lambda *, purpose: copy.deepcopy(expected_specs)
    )
    monkeypatch.setattr(
        technical.inputs,
        "read_case",
        lambda prepared, case_id, consumed=None: next(
            case for case in cases if case.spec["id"] == case_id
        ),
    )
    monkeypatch.setattr(technical.inputs, "arm_arrays", arm_arrays)
    monkeypatch.setattr(profile, "prepare_main_width_member", prepare_member)
    monkeypatch.setattr(
        profile,
        "verify_prepared",
        lambda path: (None, None, profile.read(path, "prepared.json")),
    )
    monkeypatch.setattr(profile, "prepared_files", prepared_files)
    monkeypatch.setattr(profile, "run_member", run_member)
    monkeypatch.setattr(
        profile, "verify_member", lambda path: profile.read(path, "result.json")
    )
    monkeypatch.setattr(
        technical.confirmed_search, "_check_provenance", check_provenance
    )
    return root, prepared, calls, changes


def first_key(prepared, arm="ordinary", case_index=0):
    return f"{prepared.test_cases[case_index].spec['id']}/{arm}"


def test_eight_prepared_workers_and_completely_read_only_replay(probe):
    root, prepared, calls, _ = probe
    report = technical.run(root)
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert technical.verify(root) == report
    assert before == {
        path: path.read_bytes() for path in root.rglob("*") if path.is_file()
    }
    assert calls == [
        first_key(prepared, arm, case_index)
        for case_index in range(2)
        for arm in technical.ARMS
    ]
    assert report["n_samples"] == 103
    assert report["niterations"] == 10
    assert report["search_calls"] == 8
    assert report["prediction_failure_policy"] == confirmed_search.WIDTH_POLICY
    preparation = profile.read(root, "preparation.json")
    assert preparation["prediction_failure_policy"] == confirmed_search.WIDTH_POLICY
    assert preparation["member_format"] == profile.MAIN_WIDTH_FORMAT
    assert report["scientific_success_assessed"] is False
    assert len(report["members"]) == 8
    assert report["costs"]["callback_calls_during_fit"] == 8
    assert report["cases"] == [
        technical._case_identity(case) for case in prepared.test_cases
    ]
    timing = profile.read(root, technical.TIMING)
    assert timing["cpu_measurement_complete"] is True
    assert timing["measurement_scope"] == technical.TIMING_SCOPE
    assert timing["report_sha256"] == technical.sources.sha256(
        (root / "completion" / technical.publication.REPORT).read_bytes()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("format", profile.MAIN_TECHNICAL_FORMAT),
        ("format", profile.NOISE_TECHNICAL_FORMAT),
        ("format", profile.FORMAT),
        ("requested_iterations", 1),
        ("requested_iterations", 10.0),
        ("seed", 123456789),
        ("technical", False),
        ("profile", "different"),
        ("status", "timeout"),
        ("status", "reference_width_indeterminate"),
        ("numerical_environment", None),
        ("numerical_environment", {"different": "native-runtime"}),
        ("provenance", {}),
        ("input_fingerprints", {}),
    ],
)
def test_wrong_worker_scope_or_cross_signal_binding_blocks_release(probe, field, value):
    root, prepared, _, changes = probe
    changes[first_key(prepared, "estimated_4096s", 1)] = {field: value}
    with pytest.raises(ValueError):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()
    assert profile.read(root, technical.TIMING)["cpu_measurement_complete"] is False


@pytest.mark.parametrize(
    "value", [None, 600.0, np.nextafter(600.0, np.inf), float("inf"), True]
)
def test_missing_or_excessive_worker_cost_blocks_preflight(probe, value):
    root, prepared, _, changes = probe
    changed = {name: 1 for name in technical.costs.COST_FIELDS}
    changed["worker_wall_seconds"] = value
    changes[first_key(prepared)] = {"costs": changed}
    with pytest.raises((ValueError, TypeError)):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()


@pytest.mark.parametrize("case_index", [0, 1])
@pytest.mark.parametrize("arm", technical.ARMS)
def test_unavailable_any_arm_prevents_all_technical_searches(probe, arm, case_index):
    root, prepared, calls, _ = probe
    prepared.test_cases[case_index].record["arm_status"][arm] = "not_run"
    with pytest.raises(ValueError, match="four N103 arms"):
        technical.run(root)
    assert calls == []
    assert not (root / "completion").exists()


@pytest.mark.parametrize(
    "field,value", [("niterations", 1000), ("noise_model", "white")]
)
def test_not_the_frozen_technical_case_prevents_all_searches(probe, field, value):
    root, prepared, calls, _ = probe
    prepared.test_cases[1].spec[field] = value
    with pytest.raises(ValueError, match="four N103 arms"):
        technical.run(root)
    assert calls == []


def test_n128_inputs_cannot_enter_new_n103_preflight(probe):
    root, prepared, calls, _ = probe
    prepared.common["time_s"] = np.arange(128, dtype=float) / 4096
    with pytest.raises(ValueError):
        technical.run(root)
    assert calls == []


def test_all_eight_original_input_fingerprints_are_distinct(probe):
    root, prepared, _, _ = probe
    report = technical.run(root)
    identities = []
    for case in prepared.test_cases:
        for arm in technical.ARMS:
            expected = technical._arrays(prepared, case, arm)
            actual = report["members"][f"{case.spec['id']}/{arm}"]["input_fingerprints"]
            assert actual == technical.confirmed_search._fingerprints(expected)
            identities.append(str(actual))
    assert len(set(identities)) == 8


def reseal_raw(root):
    completion = root / "completion"
    _write_json(completion / "raw_checksums.json", technical._raw_hashes(root))
    manifest = profile.read(completion, technical.publication.MANIFEST)
    manifest["raw_checksums.json"] = technical.sources.sha256(
        (completion / "raw_checksums.json").read_bytes()
    )
    _write_json(completion / technical.publication.MANIFEST, manifest)


def test_resealed_preparation_cannot_downgrade_the_prediction_policy(probe):
    root, _, _, _ = probe
    technical.run(root)
    preparation = profile.read(root, "preparation.json")
    del preparation["prediction_failure_policy"]
    _write_json(root / "preparation.json", preparation)
    reseal_raw(root)
    with pytest.raises(ValueError, match="Changed technical preflight preparation"):
        technical.verify(root)


@pytest.mark.parametrize("wrong", ["background", "signal"])
def test_resealed_worker_cannot_substitute_another_background_or_signal(probe, wrong):
    root, prepared, _, _ = probe
    technical.run(root)
    first, second = [case.spec["id"] for case in prepared.test_cases]
    target = technical._directory(root, second, "estimated_4096s")
    source = technical._directory(
        root,
        second if wrong == "background" else first,
        "known_covariance" if wrong == "background" else "estimated_4096s",
    )
    record = profile.read(target, "result.json")
    record["input_fingerprints"] = profile.read(source, "result.json")[
        "input_fingerprints"
    ]
    _write_json(target / "result.json", record)
    reseal_raw(root)
    with pytest.raises(ValueError, match="input or covariance"):
        technical.verify(root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("report_sha256", "0" * 64),
        ("measurement_scope", "worker_only"),
        ("wall_seconds", technical.TOTAL_SECONDS),
        ("cpu_user_seconds", -1),
        ("cpu_system_seconds", True),
        ("cpu_measurement_complete", False),
        ("finished_at_utc", "2000-01-01T00:00:00+00:00"),
    ],
)
def test_invalid_full_call_measurement_is_rejected(probe, field, value):
    root, _, _, _ = probe
    technical.run(root)
    timing = profile.read(root, technical.TIMING)
    timing[field] = value
    _write_json(root / technical.TIMING, timing)
    with pytest.raises(ValueError):
        technical.verify(root)


@pytest.mark.parametrize(
    "artifact", ["inputs/fixed-input.bin", "preparation.json", "unexpected.txt"]
)
def test_changed_or_added_evidence_is_rejected(probe, artifact):
    root, _, _, _ = probe
    technical.run(root)
    (root / artifact).write_text("changed")
    with pytest.raises(ValueError):
        technical.verify(root)


def test_late_mutation_after_publication_revokes_release(probe, monkeypatch):
    root, _, _, _ = probe
    original = technical.publication.publish

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        (root / "inputs/fixed-input.bin").write_bytes(b"changed after unlock")
        return result

    monkeypatch.setattr(technical.publication, "publish", mutate)
    with pytest.raises(ValueError, match="changed"):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()


def test_outer_guard_catches_mutation_after_read_only_return(probe):
    root, prepared, _, _ = probe
    technical.run(root)
    consumed = technical.publication.Consumption(technical.publication.Deadline(60))
    technical.verify(root, consumed)
    path = technical._directory(root, prepared.test_cases[1].spec["id"], "ordinary")
    (path / "result.json").write_text("later change")
    with pytest.raises(ValueError, match="changed"):
        consumed.check()


@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds"]
)
def test_full_call_includes_preparation_and_all_eight_serial_workers(
    probe, monkeypatch, field
):
    root, prepared, _, changes = probe
    for name in prepared.call:
        prepared.call[name] = 0.25
    for case_index in range(2):
        for arm in technical.ARMS:
            changes[first_key(prepared, arm, case_index)] = {
                "costs": {name: 1 for name in technical.costs.COST_FIELDS}
            }
    original = technical._timing

    def measured(*args, **kwargs):
        record = original(*args, **kwargs)
        record.update(wall_seconds=9.0, cpu_user_seconds=9.0, cpu_system_seconds=9.0)
        return record

    monkeypatch.setattr(technical, "_timing", measured)
    technical.run(root)
    timing = profile.read(root, technical.TIMING)
    timing[field] = 8.0
    _write_json(root / technical.TIMING, timing)
    with pytest.raises(ValueError, match="below its included parts"):
        technical.verify(root)


@pytest.mark.parametrize("stage", ["inputs", "worker"])
def test_interrupt_retains_partial_costs_and_never_releases(probe, monkeypatch, stage):
    root, _, _, _ = probe

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("cancelled technical preflight")

    monkeypatch.setattr(
        technical.inputs if stage == "inputs" else profile,
        "prepare_inputs" if stage == "inputs" else "run_member",
        stop,
    )
    with pytest.raises(KeyboardInterrupt):
        technical.run(root)
    timing = profile.read(root, technical.TIMING)
    assert timing["status"] == "aborted"
    assert "KeyboardInterrupt" in timing["error"]
    assert timing["cpu_measurement_complete"] is False
    assert timing["report_sha256"] is None
    assert timing["wall_seconds"] >= 0
    if stage == "worker":
        assert (root / "completion" / technical.publication.LOCK).exists()
    with pytest.raises(ValueError):
        technical.verify(root)


def main_request():
    return {
        "format": profile.MAIN_TECHNICAL_FORMAT,
        "profile": profile.PROFILE,
        "seed": 2026111413,
        "technical": True,
        "budget": asdict(symbolic.SearchBudget(seed=2026111413, niterations=10)),
    }


def prepare_main_member(tmp_path):
    directory = tmp_path / "member"
    profile.prepare_main_technical_member(
        directory, np.arange(103) / 4096, np.ones(103), seed=2026111413
    )
    return directory


def test_main_probe_uses_ten_iterations_with_unchanged_300x5_options():
    budget = profile.checked_request(main_request())
    actual = profile.parameters(budget)
    assert actual["niterations"] == 10
    assert actual["optimizer_iterations"] == 300
    assert actual["optimizer_nrestarts"] == 5
    assert actual["should_simplify"] is False
    assert actual["loss_function"] == "Main.SearchTimeBudget.objective"
    assert actual["timeout_in_seconds"] is None


@pytest.mark.parametrize("iterations", [1, 9, 11, 1000, True, 10.0])
def test_main_probe_rejects_changed_iteration_count(iterations):
    document = main_request()
    document["budget"]["niterations"] = iterations
    with pytest.raises(ValueError):
        profile.checked_request(document)


def test_main_member_binds_own_plan_and_exact_grid(tmp_path):
    directory = prepare_main_member(tmp_path)
    request, arrays, manifest = profile.verify_prepared(directory)
    assert request == main_request()
    assert np.array_equal(arrays["time_s"], np.arange(103) / 4096)
    assert manifest["sources"][profile.MAIN_PLAN] == profile.MAIN_PLAN_SHA256
    assert profile.NOISE_PLAN not in manifest["sources"]
    assert manifest["format"] == profile.MAIN_TECHNICAL_FORMAT


@pytest.mark.parametrize("times", [np.arange(128) / 4096, np.arange(103) / 4097])
def test_main_member_rejects_wrong_grid_before_creating_output(tmp_path, times):
    with pytest.raises(ValueError, match="N103 grid"):
        profile.prepare_main_technical_member(
            tmp_path / "member", times, np.ones(times.size), seed=2026111413
        )
    assert not (tmp_path / "member").exists()


def test_changed_main_plan_is_rejected_without_affecting_legacy_plan(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    path = tmp_path / profile.MAIN_PLAN
    path.parent.mkdir()
    path.write_text("Changed main plan.\n")
    with pytest.raises(ValueError, match="frozen main-study"):
        profile.source_hashes(request=main_request())


def test_resealed_main_member_cannot_change_its_exact_acquisition_grid(tmp_path):
    directory = prepare_main_member(tmp_path)
    arrays = {"time_s": np.arange(103) / 4097, "observed": np.ones(103)}
    np.savez(directory / "inputs.npz", **arrays)
    manifest = profile.read(directory, "prepared.json")
    manifest["input_fingerprints"] = {
        name: profile.sources.fingerprint(array) for name, array in arrays.items()
    }
    manifest["files"]["inputs.npz"] = profile._sha256(
        (directory / "inputs.npz").read_bytes()
    )
    _write_json(directory / "prepared.json", manifest)
    with pytest.raises(ValueError, match="N103 grid"):
        profile.verify_prepared(directory)


def test_failed_main_worker_preserves_own_format_and_rejects_relabelling(tmp_path):
    directory = prepare_main_member(tmp_path)
    metadata = profile.read(directory, "metadata_initial.json")
    metadata["phase"] = "worker_start"
    _write_json(directory / "metadata.json", metadata)
    _write_json(
        directory / "outcome.json",
        {
            "format": profile.MAIN_TECHNICAL_FORMAT,
            "status": "timeout",
            "returncode": -15,
            "timed_out": True,
            "worker_wall_seconds": 600.0,
            "adapter_call_wall_seconds": 600.0,
            "cpu_user_seconds": None,
            "cpu_system_seconds": None,
        },
    )
    _write_json(directory / "member_checksums.json", profile._inventory(directory))
    before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    result = profile.verify_member(directory)
    assert result["format"] == profile.MAIN_TECHNICAL_FORMAT
    assert result["requested_iterations"] == 10
    assert result["status"] == "timeout"
    assert result["costs"]["cpu_user_seconds"] is None
    assert before == {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    metadata["format"] = profile.NOISE_TECHNICAL_FORMAT
    _write_json(directory / "metadata.json", metadata)
    _write_json(directory / "member_checksums.json", profile._inventory(directory))
    with pytest.raises(ValueError, match="parent provenance"):
        profile.verify_member(directory)
