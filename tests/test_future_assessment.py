"""Exercise prospective integration with fixed synthetic worker outputs, never search."""

import math
from pathlib import Path

import numpy as np
import pytest
from test_symbolic_pilot import constant, read, small_config, write_worker

from ringdown_sr import covariance_pilot, pilot, symbolic_pilot
from ringdown_sr import future_assessment as future
from ringdown_sr.assessment_publication import LOCK, PENDING, REPORT
from ringdown_sr.assessment_sources import json_bytes, read_json, sha256
from ringdown_sr.cli import main
from ringdown_sr.config import parse_config
from ringdown_sr.pilot import run_pilot


def rehash(root):
    for directory in sorted((root / "symbolic").iterdir()):
        checks = directory / "checksums.json"
        checks.write_bytes(
            json_bytes(
                {name: sha256((directory / name).read_bytes()) for name in read(checks)}
            )
        )
    for directory in (root / "reference", root):
        path = directory / "metadata.json"
        record = read(path)
        record["artifact_sha256"] = {
            name: sha256((directory / name).read_bytes())
            for name in record["artifact_sha256"]
        }
        path.write_bytes(json_bytes(record))


@pytest.fixture
def software(monkeypatch):
    inventory = future.git("ls-tree", "-r", "-z", "HEAD", "--", "src/ringdown_sr")
    monkeypatch.setattr(future, "git", lambda *args: inventory)
    provenance = pilot._provenance()
    provenance["git"].update(commit="1" * 40, dirty=False, changes=[])
    for module in (pilot, symbolic_pilot, covariance_pilot):
        monkeypatch.setattr(module, "_provenance", lambda: provenance)
    monkeypatch.setattr(
        future.sources,
        "_git_file",
        lambda commit, name: (future.ROOT / name).read_bytes(),
    )

    def freeze(consumed):
        raw = future.POLICY.read_bytes()
        consumed.add(future.POLICY, raw)
        return {
            "software_commit": "1" * 40,
            "source_sha256": {
                **{
                    "src/" + name: digest
                    for name, digest in provenance["python_source_sha256"].items()
                },
                **{
                    name: sha256((future.ROOT / name).read_bytes())
                    for name in future.CONTRACT_FILES
                    + future.ADAPTER_FILES
                    + future.PROJECT_FILES
                },
            },
            "policy": read_json(raw),
            "runtime": {"test_stub": True},
        }

    monkeypatch.setattr(future, "freeze_software", freeze)


@pytest.fixture
def worker(monkeypatch):
    calls = []

    def search(time, observed, **kwargs):
        root = Path(kwargs["output"]).parents[1]
        if (root / future.CONTRACT).exists():
            assert read(root / "metadata_initial.json")["supplemental_assessment"]
            contract = read(root / future.CONTRACT)
            assert contract["inputs_sha256"] == sha256(
                (root / future.INPUTS).read_bytes()
            )
        calls.append(
            (time.copy(), observed.copy(), kwargs["budget"], kwargs["covariance"])
        )
        run = write_worker(time, observed, **kwargs)
        path = run.output_directory / "metadata.json"
        record = read(path)
        record["phase"] = "success"
        record["provenance"] = pilot._provenance()
        record["worker_provenance"] = pilot._provenance()
        adapters = {
            name: sha256((future.ROOT / name).read_bytes())
            for name in future.ADAPTER_FILES
        }
        record["adapter_source_sha256"] = adapters
        record["worker_adapter_source_sha256"] = adapters
        path.write_bytes(json_bytes(record))
        initial = run.output_directory / "metadata_initial.json"
        initial.write_bytes(
            json_bytes(
                {"provenance": record["provenance"], "adapter_source_sha256": adapters}
            )
        )
        for name in ("RingdownSRLoss.jl", "RingdownSRSearch.jl"):
            (run.output_directory / name).write_bytes(
                (future.ROOT / "julia/src" / name).read_bytes()
            )
        result_file = run.output_directory / "result.json"
        result = read(result_file)
        result.update(
            rng={"python_seed": kwargs["budget"].seed}, selection=future.SELECTION
        )
        result_file.write_bytes(json_bytes(result))
        checks = run.output_directory / "checksums.json"
        record = read(checks)
        record["metadata.json"] = sha256(path.read_bytes())
        record["metadata_initial.json"] = sha256(initial.read_bytes())
        for name in ("RingdownSRLoss.jl", "RingdownSRSearch.jl", "result.json"):
            record[name] = sha256((run.output_directory / name).read_bytes())
        checks.write_bytes(json_bytes(record))
        return run

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", search)
    return calls


@pytest.fixture
def run_source(tmp_path, software, worker):
    config = tmp_path / "input.toml"
    config.write_text(small_config())
    source, output = tmp_path / "run", tmp_path / "assessment"
    assert run_pilot(config, source, assessment_output=output).status == "success"
    return source, output, config


def test_integration_clean_reference_original_selection_and_no_input_leak(
    run_source, worker, tmp_path
):
    source, output, config = run_source
    records = read(output / "assessment_records.json")
    report = read(output / REPORT)
    assert report["status"] == "completed" and not (output / LOCK).exists()
    assert len(records) == len(worker) == 3
    assert len(report["groups"]) == 3
    assert all(g["planned_denominator"] == 1 for g in report["groups"])
    with np.load(source / future.INPUTS) as data:
        assert data["diagnostic_time_s"].size == 31 * 7
        assert all(np.array_equal(call[0], data["training_time_s"]) for call in worker)
        assert all(
            not np.array_equal(call[1], data["training_truth"]) for call in worker
        )
        for record in records:
            assert record["source_identity"]["original_selected_index"] == 1
            original = read(source / "result.json")["symbolic_arms"][
                record["source_identity"]["arm"]
            ]
            assert record["unchanged_original"] == original
            for grid in ("training", "diagnostic"):
                times = data[grid + "_time_s"]
                truth = data[grid + "_truth"]
                # Independent analytic reference for the fixed synthetic 0.3*exp(-3*t) tree.
                prediction = [0.3 * math.exp(-3 * float(t)) for t in times]
                difference = [
                    p - float(y) for p, y in zip(prediction, truth, strict=True)
                ]
                rms = math.sqrt(
                    math.fsum(d * d for d in difference)
                    / math.fsum(float(y) ** 2 for y in truth)
                )
                maximum = max(map(abs, difference)) / max(map(abs, truth))
                assert record["curve_errors"][grid]["relative_rms"] == pytest.approx(
                    rms, rel=1e-14
                )
                assert record["curve_errors"][grid]["relative_max"] == pytest.approx(
                    maximum, rel=1e-14
                )
            assert record["supplemental"]["domain"]["status"] == "defined_everywhere"
            assert (
                record["supplemental"]["original_family"]["status"]
                == "proven_nonmember"
            )
    assert (output / "original-result.json").read_bytes() == (
        source / "result.json"
    ).read_bytes()
    # The optional wrapper leaves original selection and metrics identical.
    before = worker.copy()
    assert run_pilot(config, tmp_path / "baseline").status == "success"
    assert read(source / "result.json") == read(tmp_path / "baseline/result.json")
    for old, new in zip(before, worker[3:], strict=True):
        for a, b in zip(old[:2], new[:2], strict=True):
            np.testing.assert_array_equal(a, b)
        assert old[2] == new[2]
    for name, digest in read(output / "assessment_checksums.json").items():
        assert sha256((output / name).read_bytes()) == digest


def test_preparation_is_saved_before_first_reference_fit(
    tmp_path, software, monkeypatch
):
    def fail(config, original, filename, output, **kwargs):
        parent = output.parent
        assert (parent / future.INPUTS).is_file()
        assert read(parent / "metadata_initial.json")["supplemental_assessment"]
        contract = read(parent / future.CONTRACT)
        assert contract["software"]["policy"]["stage"] == 2
        assert contract["structure_interval"]["closed"] == [True, True]
        assert contract["software"]["policy"]["proof_resource_limits"][
            "precisions"
        ] == [128, 256, 512, 1024]
        with np.load(parent / future.INPUTS, allow_pickle=False) as arrays:
            from fractions import Fraction

            bounds = tuple(
                Fraction(
                    int(value["numerator_hex"], 16), int(value["denominator_hex"], 16)
                )
                for value in contract["structure_interval"]["endpoints"]
            )
            assert bounds == tuple(
                Fraction.from_float(float(value))
                for value in arrays["training_time_s"][[0, -1]]
            )
        raise RuntimeError("synthetic preparation stop")

    monkeypatch.setattr(symbolic_pilot, "run_covariance_pilot", fail)
    config = tmp_path / "input.toml"
    config.write_text(small_config())
    with pytest.raises(ValueError, match="successful"):
        run_pilot(config, tmp_path / "run", assessment_output=tmp_path / "assessment")
    assert (tmp_path / "assessment" / LOCK).exists()
    assert read(tmp_path / "assessment" / REPORT)["groups"] == []


def test_saved_export_is_read_only_and_needs_no_archive_or_worker(
    run_source, tmp_path, monkeypatch
):
    source, _, _ = run_source
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    monkeypatch.setattr(
        symbolic_pilot, "run_search_arm", lambda *a, **k: pytest.fail("Search called")
    )
    assert main(["assess", str(source), "--output", str(tmp_path / "again")]) == 0
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "change",
    [
        "index",
        "summary",
        "request",
        "prediction",
        "residual",
        "worker_status",
        "binding",
        "grid",
        "truth",
        "policy",
        "origin",
        "loss",
        "self_manifest",
        "missing_snapshot",
        "duplicate_json",
    ],
)
def test_consistently_rehashed_source_corruption_is_blocked(
    run_source, tmp_path, change
):
    source, _, _ = run_source
    arm = source / "symbolic/ordinary"
    path = arm / "result.json"
    record = read(path)
    if change == "index":
        record["selected_index"] = 0
    elif change == "loss":
        record["candidates"][1]["loss"] *= 2
        result = read(source / "result.json")
        result["symbolic_arms"]["ordinary"]["selected"]["training_loss"] = record[
            "candidates"
        ][1]["loss"]
        (source / "result.json").write_bytes(json_bytes(result))
    elif change in ("prediction", "residual"):
        record["candidates"][1][change][0] += 0.5
    path.write_bytes(json_bytes(record))
    if change in ("request", "worker_status"):
        path = arm / ("request.json" if change == "request" else "metadata.json")
        record = read(path)
        if change == "request":
            record["budget"]["seed"] += 1
        else:
            record["phase"] = "running"
        path.write_bytes(json_bytes(record))
    if change == "summary":
        path = source / "result.json"
        record = read(path)
        record["symbolic_arms"]["ordinary"]["selected"]["index"] = 0
        path.write_bytes(json_bytes(record))
    if change == "binding":
        path = source / "metadata_initial.json"
        record = read(path)
        record["supplemental_assessment"][future.INPUTS] = "0" * 64
        path.write_bytes(json_bytes(record))
    if change in ("grid", "truth", "policy", "origin"):
        contract = read(source / future.CONTRACT)
        if change == "policy":
            contract["software"]["policy"]["reference"] = "observed"
        elif change == "origin":
            contract["software"]["source_sha256"]["src/ringdown_sr/signals.py"] = (
                "0" * 64
            )
        else:
            with np.load(source / future.INPUTS) as npz:
                arrays = {name: npz[name].copy() for name in npz.files}
            key = "diagnostic_time_s" if change == "grid" else "training_truth"
            arrays[key][0] += 0.00001
            np.savez(source / future.INPUTS, **arrays)
            contract["inputs_sha256"] = sha256((source / future.INPUTS).read_bytes())
            contract["arrays"][key] = future.sources.fingerprint(arrays[key])
        (source / future.CONTRACT).write_bytes(json_bytes(contract))
        for filename in ("metadata.json", "metadata_initial.json"):
            path = source / filename
            record = read(path)
            record["supplemental_assessment"] = {
                name: sha256((source / name).read_bytes())
                for name in (future.INPUTS, future.CONTRACT)
            }
            path.write_bytes(json_bytes(record))
    if change == "duplicate_json":
        (arm / "result.json").write_bytes(b'{"selected_index": 1, "selected_index": 0}')
    rehash(source)
    if change == "self_manifest":
        path = source / "metadata.json"
        record = read(path)
        record["artifact_sha256"]["metadata.json"] = "0" * 64
        path.write_bytes(json_bytes(record))
    if change == "missing_snapshot":
        (source / future.INPUTS).unlink()
    destination = tmp_path / "bad"
    with pytest.raises((ValueError, KeyError, OSError, AssertionError)):
        future.export_assessment(source, destination)
    assert (destination / LOCK).exists()
    assert read(destination / REPORT)["status"] == "failed"
    assert read(destination / REPORT)["groups"] == []


def test_late_source_mutation_revokes_publication(run_source, tmp_path, monkeypatch):
    source, _, _ = run_source
    original = Path.write_bytes

    def write(path, data):
        result = original(path, data)
        if path.name == PENDING:
            (source / future.INPUTS).write_bytes(b"late mutation")
        return result

    monkeypatch.setattr(Path, "write_bytes", write)
    destination = tmp_path / "late"
    with pytest.raises(ValueError, match="Consumed file changed"):
        future.export_assessment(source, destination)
    assert (destination / LOCK).exists()
    assert read(destination / REPORT)["groups"] == []


@pytest.mark.parametrize(
    "tree,truth",
    [
        (constant(0), [0, 0]),
        (constant(float.fromhex("0x1.fffffffffffffp+1023")), [1e-300, 1e-300]),
    ],
)
def test_unavailable_metrics_are_never_grade_d(tree, truth):
    errors = future.endpoint(tree, np.array([0.0, 1.0]), np.array(truth))
    assert (
        future.grade_curve(
            {"training": errors, "diagnostic": errors}, source_verified=True
        )["status"]
        == "not_assessable"
    )


def test_original_division_hole_is_not_simplified():
    time = {"kind": "variable", "index": 1}
    tree = {
        "kind": "operator",
        "operator": "/",
        "arity": 2,
        "operator_index": 4,
        "children": [time, time],
    }
    errors = future.endpoint(tree, np.array([0.0, 1.0]), np.ones(2))
    assert errors["status"] == "not_available"


def test_fixed_grid_has_seven_inner_points_and_no_extrapolation():
    config = parse_config(
        small_config().replace("n_samples = 32", "n_samples = 128").encode()
    )
    arrays = future.planned_arrays(config)
    assert len(arrays["diagnostic_time_s"]) == 889
    fs = config.sampling.sample_rate_hz
    expected = np.array(
        [(8 * k + j) / (8 * fs) for k in range(127) for j in range(1, 8)]
    )
    np.testing.assert_array_equal(arrays["diagnostic_time_s"], expected)
    assert (
        arrays["training_time_s"][0]
        < expected[0]
        < expected[-1]
        < arrays["training_time_s"][-1]
    )


def test_output_overlap_is_rejected_before_any_worker(run_source, worker):
    source, _, config = run_source
    calls = len(worker)
    with pytest.raises(ValueError, match="separate"):
        run_pilot(config, source, assessment_output=source / "assessment")
    assert len(worker) == calls


def test_interruption_leaves_locked_assessment_without_grades(
    tmp_path, software, monkeypatch
):
    def stop(*args, **kwargs):
        raise KeyboardInterrupt("synthetic stop")

    monkeypatch.setattr(symbolic_pilot, "run_covariance_pilot", stop)
    config = tmp_path / "input.toml"
    config.write_text(small_config())
    destination = tmp_path / "assessment"
    with pytest.raises(KeyboardInterrupt):
        run_pilot(config, tmp_path / "run", assessment_output=destination)
    assert (destination / LOCK).exists()
    assert read(destination / REPORT)["groups"] == []


def test_no_assessment_snapshot_is_invented_for_old_runs(tmp_path, software, worker):
    config = tmp_path / "input.toml"
    config.write_text(small_config())
    source = tmp_path / "old"
    run_pilot(config, source)
    destination = tmp_path / "assessment"
    assert main(["assess", str(source), "--output", str(destination)]) == 2
    assert (destination / LOCK).exists()
    assert not (source / future.INPUTS).exists()


def test_presearch_bytes_remain_bound_through_run(
    tmp_path, software, worker, monkeypatch
):
    original = symbolic_pilot.run_search_arm

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        root = result.output_directory.parents[1]
        path = root / future.CONTRACT
        path.write_bytes(path.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", mutate)
    config = tmp_path / "input.toml"
    config.write_text(small_config())
    with pytest.raises(ValueError, match="Consumed file changed"):
        run_pilot(config, tmp_path / "run", assessment_output=tmp_path / "assessment")
    assert read(tmp_path / "assessment" / REPORT)["groups"] == []


@pytest.mark.parametrize("change", ["none", "policy", "source", "dirty"])
def test_software_and_policy_are_committed_before_use(tmp_path, monkeypatch, change):
    from ringdown_sr.assessment_publication import Consumption, Deadline

    names = [
        *future.CONTRACT_FILES,
        *future.ADAPTER_FILES,
        *future.PROJECT_FILES,
        "src/ringdown_sr/example.py",
    ]
    raw_policy = future.POLICY.read_bytes()
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw_policy if name == names[0] else b"synthetic source")
    (tmp_path / future.structure.FILES[0]).write_bytes(
        json_bytes(future.structure.POLICY)
    )
    monkeypatch.setattr(future, "ROOT", tmp_path)
    monkeypatch.setattr(future, "POLICY", tmp_path / names[0])
    monkeypatch.setattr(
        future,
        "git",
        lambda *args: (
            "100644 blob " + "2" * 40 + "\tsrc/ringdown_sr/example.py\0"
            if args[0] == "ls-tree"
            else ("dirty" if change == "dirty" else "")
            if args[0] == "status"
            else "1" * 40
        ),
    )
    monkeypatch.setattr(
        future.sources,
        "_git_file",
        lambda commit, name: (
            b"different" if change == "source" else (tmp_path / name).read_bytes()
        ),
    )
    if change == "policy":
        (tmp_path / names[0]).write_bytes(
            raw_policy.replace(b"seven", b"eight") + b"\n"
        )
    consumed = Consumption(Deadline(30))
    if change == "none":
        future.freeze_software(consumed)
        (tmp_path / names[-1]).write_bytes(b"late source")
        with pytest.raises(ValueError, match="Consumed file changed"):
            consumed.check()
    else:
        with pytest.raises(ValueError):
            future.freeze_software(consumed)


def test_cli_replay_failure_reports_export_error_and_keeps_lock(run_source, tmp_path):
    source, _, _ = run_source
    path = source / "symbolic/ordinary/result.json"
    front = read(path)
    front["candidates"][1]["prediction"][0] += 0.25
    path.write_bytes(json_bytes(front))
    rehash(source)
    destination = tmp_path / "bad-replay"
    assert main(["assess", str(source), "--output", str(destination)]) == 2
    assert (destination / LOCK).exists()
    assert read(destination / REPORT)["groups"] == []
