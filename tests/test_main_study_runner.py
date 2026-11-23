"""Check complete section accounting at an isolated native-worker boundary."""

import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import main_study as study
from ringdown_sr.pilot import _write_json


def read(path):
    return json.loads(Path(path).read_bytes())


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    """Stub only expensive input/native gates; retain real assessment/publication."""
    times = np.arange(103, dtype=np.float64) / 4096
    main = (np.arange(1024, dtype=np.float64) + 0.371) * (0.025 / 1024)
    support = (np.arange(1024, dtype=np.float64) + 0.371) * ((102 / 4096) / 1024)
    endpoints = np.array([0.0, 0.025])
    truth = lambda t: np.exp(-100 * t) * np.cos(1300 * t)
    common = {
        "time_s": times,
        "signal": truth(times),
        "main_time_s": main,
        "main_truth": truth(main),
        "support_time_s": support,
        "support_truth": truth(support),
        "endpoint_time_s": endpoints,
        "endpoint_truth": truth(endpoints),
    }
    software = {"software_commit": "1" * 40, "source_sha256": {"fixture.py": "2" * 64}}
    environment = {"julia": "synthetic", "threads": 1}
    cases = {}
    counter = 0
    for signal_id in study.SIGNALS:
        for block in range(1, 31):
            for model in ("ar1", "white") if block <= 10 else ("ar1",):
                counter += 1
                case_id = f"{signal_id}-{model}-{block:02d}"
                cases[case_id] = SimpleNamespace(
                    spec={
                        "id": case_id,
                        "signal_id": signal_id,
                        "noise_model": model,
                        "block": block,
                        "signal": {"amplitude": 1.0},
                        "standard_deviation": 0.05,
                        "search_seeds": [counter * 4 + n for n in range(1, 5)],
                    },
                    record={"arm_status": dict.fromkeys(study.ARMS, "ready")},
                )
    source = tmp_path / "inputs"
    source.mkdir()
    evidence = source / "evidence.txt"
    evidence.write_text("fixed complete 80-case input preparation")
    prepared = SimpleNamespace(
        root=source,
        manifest={"technical": False, "purpose": "scientific", "software": software},
        cases={key: case.spec for key, case in cases.items()},
        common=common,
        call={},
    )
    expected_specs = copy.deepcopy(tuple(prepared.cases.values()))
    _write_json(source / "preparation.json", prepared.manifest)
    technical = tmp_path / "technical"
    (technical / "completion").mkdir(parents=True)
    gate_report = {
        "status": "completed",
        "software": software,
        "numerical_environment": environment,
        "n_samples": 103,
        "niterations": 10,
        "search_calls": 8,
    }
    _write_json(technical / "completion" / publication.REPORT, gate_report)
    result = SimpleNamespace(
        preparation=source,
        technical=technical,
        prepared=prepared,
        cases=cases,
        evidence=evidence,
        events=[],
        mutate_package=None,
        fail_arm=None,
        software=software,
        environment=environment,
    )

    def verify_inputs(path, consumed=None):
        assert Path(path) == source
        study._read(evidence, consumed)
        sources._same(
            study._json(source / "preparation.json", consumed),
            prepared.manifest,
            "Changed prepared inputs.",
        )
        return prepared

    def read_case(loaded, case_id, consumed=None, **kwargs):
        assert loaded is prepared
        study._read(evidence, consumed)
        return cases[case_id]

    def arm_arrays(loaded, case, arm):
        assert loaded is prepared
        matrix = np.eye(103, dtype=np.float64) * 0.0025
        arrays = {
            **common,
            "observed": common["signal"] + 0.01,
            "covariance_true": matrix,
            "covariance": None
            if arm == "ordinary" or case.record["arm_status"][arm] != "ready"
            else matrix * (1 + study.ARMS.index(arm) / 10),
        }
        return arrays

    def gate(path, *, consumed=None):
        return study._json(Path(path) / "completion" / publication.REPORT, consumed)

    def run_package(time_s, observed, *, covariance, output, seeds):
        output = Path(output)
        case_id, arm = output.parent.parent.name, output.name
        if arm == result.fail_arm:
            output.mkdir(parents=True)
            (output / "partial.log").write_text("original interrupted worker")
            raise KeyboardInterrupt("synthetic worker interruption")
        # No truth or evaluation arrays cross the native search boundary.
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        result.events.extend((case_id, arm, seed) for seed in seeds)
        costs = dict.fromkeys(study.COST_FIELDS, 0.0)
        costs["callback_calls_during_fit"] = 100
        selected = {
            "tree": {"kind": "constant", "value_hex": (0.25).hex()},
            "prediction": np.full_like(time_s, 0.25).tolist(),
            "loss": 0.125,
            "complexity": 1,
            "display_equation": "0.25",
        }
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
        if result.mutate_package is not None:
            result.mutate_package(arm, report)
        (output / "completion").mkdir(parents=True)
        _write_json(output / "completion" / publication.REPORT, report)
        return report

    monkeypatch.setattr(study.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(study.inputs, "read_case", read_case)
    monkeypatch.setattr(study.inputs, "arm_arrays", arm_arrays)
    monkeypatch.setattr(study.inputs, "common_for_case", lambda _common, _spec: common)
    monkeypatch.setattr(study.inputs, "case_specs", lambda **kwargs: expected_specs)
    monkeypatch.setattr(study.technical, "verify", gate)
    monkeypatch.setattr(study.search, "run_confirmed_package", run_package)
    monkeypatch.setattr(
        study.search,
        "verify_confirmed_package",
        lambda path: read(Path(path) / "completion" / publication.REPORT),
    )
    return result


def run(fixture, path, signal_id=study.SIGNALS[0], **kwargs):
    return study.run(
        fixture.preparation, fixture.technical, path, signal_id=signal_id, **kwargs
    )


def verify(fixture, path, **kwargs):
    return study.verify(fixture.preparation, fixture.technical, path, **kwargs)


def test_full_first_section_and_readonly_replay(boundary, tmp_path):
    root = tmp_path / "first"
    report = run(boundary, root)
    assert report["search_calls"] == 640
    assert report["planned_outputs"] == 160
    assert report["full_study_planned_outputs"] == 320
    assert len(report["assessments"]) == 160
    normalization = report["signal_normalization"]
    assert normalization["noise_over_amplitude"] == 0.05
    assert normalization["n_samples"] == 103
    assert (
        normalization["rms_reference"] == "clean_signal_equal_weight_training_samples"
    )
    assert len(boundary.events) == 640

    ids = study._section_ids(boundary.prepared, study.SIGNALS[0])
    for position, case_id in enumerate(ids):
        executed = [arm for cid, arm, _ in boundary.events if cid == case_id][::4]
        shift = position % 4
        assert executed == list(study.ARMS[shift:] + study.ARMS[:shift])
    before = study._tree_hashes(root)
    costs = study._call_path(root).read_bytes()
    assert verify(boundary, root) == report
    assert run(boundary, root) == report
    assert study._tree_hashes(root) == before
    assert study._call_path(root).read_bytes() == costs
    assert len(boundary.events) == 640
    exported = tmp_path / "verified"
    assert verify(boundary, root, export=exported) == report
    assert read(study._call_path(exported))["kind"] == "verification"
    assert read(study._call_path(exported))["cpu_measurement_complete"] is True
    assert study._tree_hashes(root) == before

    # Replays reject changed identities, inventories and cost scope without repair.
    registration = root / "registration.json"
    raw = registration.read_bytes()
    changed = read(registration)
    changed["previous_section_report_sha256"] = "f" * 64
    _write_json(registration, changed)
    tampered = study._tree_hashes(root)
    with pytest.raises(ValueError, match="registration"):
        verify(boundary, root)
    assert study._tree_hashes(root) == tampered
    registration.write_bytes(raw)

    call = read(study._call_path(root))
    call["cpu_measurement_complete"] = False
    _write_json(study._call_path(root), call)
    with pytest.raises(ValueError, match="CPU completeness"):
        verify(boundary, root)
    assert read(study._call_path(root))["cpu_measurement_complete"] is False
    study._call_path(root).write_bytes(costs)

    with pytest.raises(ValueError, match="format or identity"):
        verify(boundary, root, signal_id=study.SIGNALS[1])
    with pytest.raises(ValueError, match="separate"):
        verify(boundary, root, export=root / "nested-verification")
    guard = publication.Consumption(publication.Deadline(30))
    forbidden = tmp_path / "external-export"
    with pytest.raises(ValueError, match="externally guarded"):
        verify(boundary, root, export=forbidden, consumed=guard)
    assert not forbidden.exists()
    assert study._tree_hashes(root) == before
    assert study._call_path(root).read_bytes() == costs
    assert len(boundary.events) == 640

    forged = copy.deepcopy(report)
    forged["signal_normalization"]["noise_over_training_signal_rms"] *= 2
    original_documents = study._publication_bytes(report)
    for name, raw in study._publication_bytes(forged).items():
        (root / "completion" / name).write_bytes(raw)
    with pytest.raises(ValueError, match="section replay differs"):
        verify(boundary, root)
    for name, raw in original_documents.items():
        (root / "completion" / name).write_bytes(raw)
    assert study._tree_hashes(root) == before


@pytest.mark.parametrize("scale", [1.0, 1e307])
def test_signal_normalization_has_independent_pythagorean_reference(boundary, scale):
    signal_id = study.SIGNALS[0]
    for spec in boundary.prepared.cases.values():
        if spec["signal_id"] == signal_id:
            spec["signal"]["amplitude"] = 10.0
            spec["standard_deviation"] = 2.0
    truth = np.zeros(103, dtype=np.float64)
    truth[:2] = [3 * scale, 4 * scale]
    boundary.prepared.common["signal"] = truth
    report = study._signal_normalization(boundary.prepared, signal_id)
    # Two nonzero coordinates have exact Euclidean norm five times scale.
    expected_rms = 5 * scale / math.sqrt(103)
    assert report["training_signal_rms"] == pytest.approx(expected_rms, rel=2e-15)
    assert report["noise_over_amplitude"] == 0.2
    assert report["noise_over_training_signal_rms"] == pytest.approx(
        2 / expected_rms, rel=2e-15, abs=0
    )
    assert report["training_signal_fingerprint"] == sources.fingerprint(truth)
    assert report["training_time_s_fingerprint"] == sources.fingerprint(
        boundary.prepared.common["time_s"]
    )
    assert report["interpretation"] == "marginal_noise_ratios_not_detector_snr"


def test_second_section_requires_first_and_counts_only_new_work(boundary, tmp_path):
    with pytest.raises(ValueError, match="completed first signal"):
        run(boundary, tmp_path / "missing-first", study.SIGNALS[1])
    assert boundary.events == []
    first, second = tmp_path / "first", tmp_path / "second"
    first_report = run(boundary, first)
    first_bytes = study._tree_hashes(first)
    second_report = run(boundary, second, study.SIGNALS[1], previous=first)
    assert second_report["search_calls"] == 640
    assert len(boundary.events) == 1280
    assert len(second_report["assessments"]) == 160
    assert second_report["previous_section_report_sha256"] == sources.sha256(
        study._publication_bytes(first_report)[publication.REPORT]
    )
    assert study._tree_hashes(first) == first_bytes
    assert verify(boundary, second, previous=first) == second_report
    assert len(boundary.events) == 1280
    assert study._tree_hashes(first) == first_bytes
    with pytest.raises(ValueError, match="first signal cannot import"):
        verify(boundary, first, previous=second)


def test_interruption_preserves_costs_and_forbids_any_partial_resume(
    boundary, tmp_path
):
    root = tmp_path / "aborted"
    boundary.fail_arm = "known_covariance"
    with pytest.raises(KeyboardInterrupt):
        run(boundary, root)
    before = study._tree_hashes(root)
    count = len(boundary.events)
    assert count == 4
    boundary.fail_arm = None
    with pytest.raises((ValueError, FileNotFoundError)):
        run(boundary, root)
    assert study._tree_hashes(root) == before
    assert len(boundary.events) == count
    call = read(study._call_path(root))
    assert call["status"] == "aborted"
    assert call["cpu_measurement_complete"] is False
    assert call["source_report_sha256"] is None
    first_case = next(iter(boundary.cases))
    case_call = read(root / "cases" / (first_case + "-call.json"))
    assert case_call["status"] == "aborted"
    assert case_call["wall_seconds"] <= call["wall_seconds"]
    assert (
        root / "cases" / first_case / "symbolic/known_covariance/partial.log"
    ).is_file()


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
def test_incorrect_worker_binding_prevents_release(boundary, tmp_path, field, value):
    boundary.mutate_package = lambda arm, report: report.update({field: value})
    root = tmp_path / "bad-binding"
    with pytest.raises(ValueError):
        run(boundary, root)
    assert read(study._call_path(root))["status"] == "aborted"
    first_case = next(iter(boundary.cases))
    assert (root / "cases" / first_case / "completion" / publication.LOCK).exists()
    assert not (root / "completion").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("software", {}),
        ("search_calls", 7),
        ("n_samples", 128),
        ("niterations", 1000),
        ("numerical_environment", None),
    ],
)
def test_invalid_preflight_blocks_all_searches(boundary, tmp_path, field, value):
    path = boundary.technical / "completion" / publication.REPORT
    changed = read(path)
    changed[field] = value
    _write_json(path, changed)
    root = tmp_path / "bad-gate"
    with pytest.raises(ValueError):
        run(boundary, root)
    assert boundary.events == []
    assert read(study._call_path(root))["status"] == "aborted"


def test_other_signal_input_change_already_blocks_first_section(boundary, tmp_path):
    spec = next(
        value
        for value in boundary.prepared.cases.values()
        if value["signal_id"] == study.SIGNALS[1]
    )
    spec["search_seeds"][0] += 1
    with pytest.raises(ValueError, match="complete 80-case"):
        run(boundary, tmp_path / "unbound")
    assert boundary.events == []


def test_covariance_failure_does_not_replace_or_remove_arm(
    boundary, tmp_path, monkeypatch
):
    # Stop after the first complete case: its assessment must retain all slots.
    first_id = next(iter(boundary.cases))
    boundary.cases[first_id].record["arm_status"]["estimated_64s"] = "not_run"
    saved = study._run_case
    captured = []

    def first_only(prepared, case_id, gates, output):
        if captured:
            raise InterruptedError("bounded fixture ends after one case")
        pair = saved(prepared, case_id, gates, output)
        captured.append(pair)
        return pair

    monkeypatch.setattr(study, "_run_case", first_only)
    with pytest.raises(InterruptedError):
        run(boundary, tmp_path / "missing-estimator")
    report, _ = captured[0]
    assert report["planned_search_calls"] == 16
    assert report["search_calls"] == 12
    record = next(
        item
        for item in report["assessments"]
        if item["source_identity"]["condition"] == "estimated_64s"
    )
    assert record["status"] == "not_run"
    assert record["planned_members"] == 4
    assert record["search_calls"] == 0
    assert {arm for _, arm, _ in boundary.events} == set(study.ARMS) - {"estimated_64s"}


def test_late_mutation_revokes_released_case(boundary, tmp_path, monkeypatch):
    original = publication.publish

    def altered(output, *args, **kwargs):
        result = original(output, *args, **kwargs)
        if output.parent.name == next(iter(boundary.cases)):
            boundary.evidence.write_text("changed after publication")
        return result

    monkeypatch.setattr(publication, "publish", altered)
    root = tmp_path / "late-mutation"
    with pytest.raises(ValueError, match="Consumed file changed"):
        run(boundary, root)
    case_root = root / "cases" / next(iter(boundary.cases))
    assert (case_root / "completion" / publication.LOCK).exists()
    assert read(study._call_path(case_root))["status"] == "aborted"
    assert read(study._call_path(root))["status"] == "aborted"


def test_existing_alarm_is_not_replaced_or_creates_output(
    boundary, tmp_path, monkeypatch
):
    monkeypatch.setattr(study.signal, "getitimer", lambda _: (2.0, 0.0))
    root = tmp_path / "alarm"
    with pytest.raises(RuntimeError, match="existing alarm"):
        run(boundary, root)
    assert not root.exists()
    assert not study._call_path(root).exists()
    assert boundary.events == []


def test_consumed_input_output_overlap_has_no_side_effects(boundary):
    before = study._tree_hashes(boundary.preparation)
    with pytest.raises(ValueError, match="separate"):
        run(boundary, boundary.preparation / "forbidden")
    assert study._tree_hashes(boundary.preparation) == before
    assert boundary.events == []


def test_second_section_rejects_first_from_other_preparation(
    boundary, tmp_path, monkeypatch
):
    # The verifier receives the active complete preparation, never an old hash.
    called = []

    def reject(prepared, gates, root, signal_id, previous_hash, consumed):
        called.append((prepared, signal_id, previous_hash))
        raise ValueError("Changed main-study section registration.")

    monkeypatch.setattr(study, "_verify_bound", reject)
    previous = tmp_path / "different-first"
    previous.mkdir()
    with pytest.raises(ValueError, match="registration"):
        run(boundary, tmp_path / "second", study.SIGNALS[1], previous=previous)
    assert called == [(boundary.prepared, study.SIGNALS[0], None)]
    assert boundary.events == []
