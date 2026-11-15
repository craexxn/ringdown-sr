"""Exercise preflight boundaries without starting a search or a reference fit."""

import copy
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import noise_pilot_technical as technical
from ringdown_sr.pilot import _write_json


@pytest.fixture
def probe(monkeypatch, tmp_path):
    software = {"software_commit": "a" * 40, "source_sha256": {"bound": "b" * 64}}
    environment = {"numerical": "same-native-runtime"}
    covariance = np.eye(128) + 0.2
    case = technical.inputs.PreparedCase(
        {
            "sampling": {"n_samples": 128, "sample_rate_hz": 4096.0},
            "search_seeds": [technical.SEED],
            "niterations": 10,
        },
        {
            "observed": np.arange(128, dtype=float),
            "covariance_true": covariance,
            "covariance_estimated": covariance * 2,
        },
        {"arm_status": {arm: "ready" for arm in technical.ARMS}},
    )
    prepared = technical.inputs.PreparedInputs(
        {
            "technical": True,
            "software": software,
            "planned_search_calls": 3,
        },
        {"time_s": np.arange(128, dtype=float) / 4096},
        {"technical-ar1": case},
        {"wall_seconds": 0.0, "cpu_user_seconds": 0.0, "cpu_system_seconds": 0.0},
    )
    calls, changes = [], {}

    def prepare_inputs(path, *, technical):
        assert technical is True
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

    def prepare_member(path, time_s, observed, *, covariance=None, seed):
        assert time_s.shape == observed.shape == (128,)
        assert seed == technical.SEED
        path.mkdir()
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        _write_json(path / "prepared.json", {"provenance": software})
        _write_json(
            path / "fingerprints.json", technical.confirmed_search._fingerprints(arrays)
        )

    def prepared_files(path):
        return {
            name: (path / name).read_bytes()
            for name in ("prepared.json", "fingerprints.json")
        }

    def check_provenance(actual, expected):
        if actual != expected:
            raise ValueError("Contradictory provenance.")

    def run_member(path, *, deadline):
        assert 0 < deadline - technical.time.monotonic() <= 600
        assert all(
            (path.parent / arm / "prepared.json").is_file() for arm in technical.ARMS
        )
        calls.append(path.name)
        record = {
            "format": technical.profile.NOISE_TECHNICAL_FORMAT,
            "requested_iterations": 10,
            "profile": technical.profile.PROFILE,
            "technical": True,
            "seed": technical.SEED,
            "status": "completed",
            "numerical_environment": environment,
            "provenance": software,
            "input_fingerprints": technical.profile.read(path, "fingerprints.json"),
            "costs": {
                name: 1 if name == "callback_calls_during_fit" else 0.0
                for name in technical.costs.COST_FIELDS
            },
        }
        record.update(changes.get(path.name, {}))
        _write_json(path / "result.json", record)
        return record

    monkeypatch.setattr(technical.inputs, "prepare_inputs", prepare_inputs)
    monkeypatch.setattr(technical.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(
        technical.profile, "prepare_noise_technical_member", prepare_member
    )
    monkeypatch.setattr(
        technical.profile,
        "verify_prepared",
        lambda path: (None, None, technical.profile.read(path, "prepared.json")),
    )
    monkeypatch.setattr(technical.profile, "prepared_files", prepared_files)
    monkeypatch.setattr(technical.profile, "run_member", run_member)
    monkeypatch.setattr(
        technical.profile,
        "verify_member",
        lambda path: technical.profile.read(path, "result.json"),
    )
    monkeypatch.setattr(
        technical.confirmed_search, "_check_provenance", check_provenance
    )
    return tmp_path / "technical", prepared, calls, changes


def test_three_prepared_workers_and_read_only_replay(probe):
    root, prepared, calls, _ = probe
    report = technical.run(root)
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert technical.verify(root) == report
    assert before == {
        path: path.read_bytes() for path in root.rglob("*") if path.is_file()
    }
    assert calls == list(technical.ARMS)
    assert report["software"] == prepared.manifest["software"]
    assert report["status"] == "completed"
    assert report["n_samples"] == 128
    assert report["niterations"] == 10
    assert report["search_calls"] == 3
    assert report["scientific_success_assessed"] is False
    timing = technical.profile.read(root, technical.TIMING)
    assert timing["measurement_scope"] == technical.TIMING_SCOPE
    assert timing["report_sha256"] == technical.sources.sha256(
        (root / "completion" / technical.publication.REPORT).read_bytes()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("format", technical.profile.FORMAT),
        ("requested_iterations", 1),
        ("requested_iterations", 10.0),
        ("seed", technical.SEED + 1),
        ("technical", False),
        ("profile", "different"),
        ("status", "timeout"),
        ("numerical_environment", None),
        ("numerical_environment", {"different": "native-runtime"}),
        ("provenance", {}),
        ("input_fingerprints", {}),
    ],
)
def test_wrong_worker_scope_or_binding_blocks_preflight(probe, field, value):
    root, _, _, changes = probe
    changes["estimated_covariance"] = {field: value}
    with pytest.raises(ValueError):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()
    assert (
        technical.profile.read(root / "completion", technical.publication.REPORT)[
            "status"
        ]
        == "failed"
    )


@pytest.mark.parametrize("value", [None, 600.000001, float("inf"), True])
def test_missing_or_excessive_worker_cost_blocks_preflight(probe, value):
    root, _, _, changes = probe
    changed = {name: 1 for name in technical.costs.COST_FIELDS}
    changed["worker_wall_seconds"] = value
    changes["ordinary"] = {"costs": changed}
    with pytest.raises((ValueError, TypeError)):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()


def test_unavailable_estimated_covariance_prevents_technical_start(probe):
    root, prepared, calls, _ = probe
    prepared.cases["technical-ar1"].record["arm_status"]["estimated_covariance"] = (
        "not_run"
    )
    with pytest.raises(ValueError, match="three N=128"):
        technical.run(root)
    assert calls == []
    assert not (root / "completion").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("report_sha256", "0" * 64),
        ("measurement_scope", "worker_only"),
        ("wall_seconds", technical.TOTAL_SECONDS),
        ("cpu_user_seconds", -1),
        ("cpu_system_seconds", True),
        ("finished_at_utc", "2000-01-01T00:00:00+00:00"),
    ],
)
def test_invalid_total_call_measurement_is_rejected(probe, field, value):
    root, _, _, _ = probe
    technical.run(root)
    timing = technical.profile.read(root, technical.TIMING)
    timing[field] = value
    _write_json(root / technical.TIMING, timing)
    with pytest.raises(ValueError):
        technical.verify(root)


@pytest.mark.parametrize(
    "artifact",
    [
        "inputs/fixed-input.bin",
        "ordinary/result.json",
        "preparation.json",
        "unexpected.txt",
    ],
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


def test_handler_teardown_remains_inside_release_boundary(probe, monkeypatch):
    root, _, _, _ = probe
    original = technical.ExitStack

    class MutatingStack(original):
        def close(self):
            super().close()
            (root / "ordinary/result.json").write_text("changed during teardown")

    monkeypatch.setattr(technical, "ExitStack", MutatingStack)
    with pytest.raises(ValueError, match="changed"):
        technical.run(root)
    assert (root / "completion" / technical.publication.LOCK).exists()


def test_outer_consumption_detects_mutation_after_read_only_return(probe):
    root, _, _, _ = probe
    technical.run(root)
    consumed = technical.publication.Consumption(technical.publication.Deadline(60))
    technical.verify(root, consumed)
    (root / "ordinary/result.json").write_text("later change")
    with pytest.raises(ValueError, match="changed"):
        consumed.check()


def test_verify_checks_original_inputs_even_if_outer_report_is_resealed(probe):
    root, _, _, _ = probe
    technical.run(root)
    record = copy.deepcopy(technical.profile.read(root / "ordinary", "result.json"))
    record["input_fingerprints"] = {}
    _write_json(root / "ordinary/result.json", record)
    completion = root / "completion"
    checksums = {
        name: technical.sources.sha256(raw)
        for name, raw in technical._raw(root).items()
    }
    _write_json(completion / "raw_checksums.json", checksums)
    manifest = technical.profile.read(completion, technical.publication.MANIFEST)
    manifest["raw_checksums.json"] = technical.sources.sha256(
        (completion / "raw_checksums.json").read_bytes()
    )
    _write_json(completion / technical.publication.MANIFEST, manifest)
    with pytest.raises(ValueError, match="input or covariance"):
        technical.verify(root)


@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds"]
)
def test_full_call_cost_must_include_serial_workers_and_preparation(
    probe, monkeypatch, field
):
    root, prepared, _, changes = probe
    for name in prepared.call:
        prepared.call[name] = 0.25
    for arm in technical.ARMS:
        changes[arm] = {"costs": {name: 1 for name in technical.costs.COST_FIELDS}}
    original = technical._timing

    def measured(*args, **kwargs):
        record = original(*args, **kwargs)
        record.update(wall_seconds=4.0, cpu_user_seconds=4.0, cpu_system_seconds=4.0)
        return record

    monkeypatch.setattr(technical, "_timing", measured)
    technical.run(root)
    timing = technical.profile.read(root, technical.TIMING)
    # The full preparation call is additional to the three serial worker scopes.
    timing[field] = 3.0
    _write_json(root / technical.TIMING, timing)
    with pytest.raises(ValueError, match="below its included parts"):
        technical.verify(root)
    timing[field] = 0.0
    _write_json(root / technical.TIMING, timing)
    with pytest.raises(ValueError, match="below its included parts"):
        technical.verify(root)


def test_partial_unknown_cost_does_not_erase_other_known_lower_bounds(probe):
    root, prepared, _, _ = probe
    report = technical.run(root)
    report["members"]["ordinary"]["costs"]["cpu_user_seconds"] = None
    report["members"]["known_covariance"]["costs"]["cpu_user_seconds"] = 0.5
    report["members"]["estimated_covariance"]["costs"]["cpu_user_seconds"] = 0.5
    raw = technical.sources.json_bytes(report)
    timing = technical.profile.read(root, technical.TIMING)
    timing["report_sha256"] = technical.sources.sha256(raw)
    timing["cpu_user_seconds"] = 0.0
    with pytest.raises(ValueError, match="below its included parts"):
        technical._verify_timing(timing, raw, prepared.call)
    timing["cpu_user_seconds"] = 1.0
    technical._verify_timing(timing, raw, prepared.call)


def test_cost_rounding_allowance_is_only_one_microsecond(probe):
    root, prepared, _, _ = probe
    report = technical.run(root)
    report["members"]["ordinary"]["costs"]["cpu_user_seconds"] = 1.0
    raw = technical.sources.json_bytes(report)
    timing = technical.profile.read(root, technical.TIMING)
    timing["report_sha256"] = technical.sources.sha256(raw)
    timing["cpu_user_seconds"] = 1.0 - 0.5e-6
    technical._verify_timing(timing, raw, prepared.call)
    timing["cpu_user_seconds"] = 1.0 - 2e-6
    with pytest.raises(ValueError, match="below its included parts"):
        technical._verify_timing(timing, raw, prepared.call)


@pytest.mark.parametrize("stage", ["inputs", "worker"])
def test_interrupted_call_retains_observed_costs_without_release(
    probe, monkeypatch, stage
):
    root, _, _, _ = probe

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("cancelled technical preflight")

    if stage == "inputs":
        monkeypatch.setattr(technical.inputs, "prepare_inputs", stop)
    else:
        monkeypatch.setattr(technical.profile, "run_member", stop)
    with pytest.raises(KeyboardInterrupt):
        technical.run(root)
    timing = technical.profile.read(root, technical.TIMING)
    assert timing["status"] == "aborted"
    assert "KeyboardInterrupt" in timing["error"]
    assert timing["report_sha256"] is None
    assert timing["cpu_scope"] == "self_plus_reaped_children"
    assert timing["wall_seconds"] >= 0
    assert timing["cpu_user_seconds"] >= 0
    assert timing["cpu_system_seconds"] >= 0
    if stage == "worker":
        assert (root / "completion" / technical.publication.LOCK).exists()
    with pytest.raises(ValueError):
        technical.verify(root)


def test_failed_cost_write_preserves_and_annotates_original_interruption(
    probe, monkeypatch
):
    root, _, _, _ = probe
    original = technical._write_json

    def write(path, document):
        if path.name == technical.TIMING:
            raise OSError("cost evidence cannot be written")
        original(path, document)

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("original interruption")

    monkeypatch.setattr(technical, "_write_json", write)
    monkeypatch.setattr(technical.profile, "run_member", stop)
    with pytest.raises(KeyboardInterrupt, match="original interruption") as caught:
        technical.run(root)
    assert any(
        "cost evidence cannot be written" in note for note in caught.value.__notes__
    )
    assert (root / "completion" / technical.publication.LOCK).exists()
