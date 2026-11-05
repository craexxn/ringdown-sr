"""Counterexamples for the three prospective-assessment provenance review findings."""

import subprocess

import pytest
import test_future_assessment as fixtures
from test_future_assessment import rehash
from test_symbolic_pilot import read, small_config

from ringdown_sr import future_assessment as future
from ringdown_sr import symbolic_pilot
from ringdown_sr.assessment_publication import LOCK, REPORT
from ringdown_sr.assessment_sources import json_bytes, sha256
from ringdown_sr.pilot import run_pilot

software = fixtures.software
worker = fixtures.worker
run_source = fixtures.run_source

CASES = (
    "worker_commit",
    "worker_dirty",
    "worker_sources",
    "worker_project",
    "worker_missing",
    "adapter_changed",
    "adapter_missing",
    "adapter_copy",
    "seed_changed",
    "seed_bool",
    "selection_changed",
    "selection_missing",
)


def mutate_arm(directory, case):
    meta_path = directory / "metadata.json"
    meta = read(meta_path)
    front_path = directory / "result.json"
    front = read(front_path)
    if case == "worker_commit":
        meta["worker_provenance"]["git"]["commit"] = "2" * 40
    elif case == "worker_dirty":
        meta["worker_provenance"]["git"]["dirty"] = True
        meta["worker_provenance"]["git"]["changes"] = [" M src/ringdown_sr/symbolic.py"]
    elif case == "worker_sources":
        provenance = meta["worker_provenance"]
        provenance["python_source_sha256"]["ringdown_sr/symbolic.py"] = "0" * 64
        provenance["python_source_set_sha256"] = sha256(
            json_bytes(provenance["python_source_sha256"])
        )
    elif case == "worker_project":
        meta["worker_provenance"]["project_file_sha256"]["julia/Manifest.toml"] = (
            "0" * 64
        )
    elif case == "worker_missing":
        del meta["worker_provenance"]
    elif case == "adapter_changed":
        meta["worker_adapter_source_sha256"]["julia/src/RingdownSRSearch.jl"] = "0" * 64
    elif case == "adapter_missing":
        del meta["worker_adapter_source_sha256"]
    elif case == "adapter_copy":
        path = directory / "RingdownSRSearch.jl"
        path.write_bytes(path.read_bytes() + b"\n# changed executed adapter\n")
    elif case == "seed_changed":
        front["rng"]["python_seed"] += 1
    elif case == "seed_bool":
        front["rng"]["python_seed"] = True
    elif case == "selection_changed":
        front["selection"] = "best_clean_signal_error"
    elif case == "selection_missing":
        del front["selection"]
    meta_path.write_bytes(json_bytes(meta))
    front_path.write_bytes(json_bytes(front))
    checksums_path = directory / "checksums.json"
    checksums_path.write_bytes(
        json_bytes(
            {
                name: sha256((directory / name).read_bytes())
                for name in read(checksums_path)
            }
        )
    )


def assert_locked(output):
    assert (output / LOCK).exists()
    report = read(output / REPORT)
    assert report["status"] == "failed" and report["groups"] == []
    assert not (output / "assessment_checksums.json").exists()


@pytest.mark.parametrize("case", CASES)
def test_rehashed_worker_counterexamples_block_saved_export(run_source, tmp_path, case):
    source, _, _ = run_source
    mutate_arm(source / "symbolic/estimated_covariance", case)
    rehash(source)
    output = tmp_path / "rejected"
    with pytest.raises((ValueError, KeyError)):
        future.export_assessment(source, output)
    assert_locked(output)


@pytest.mark.parametrize("case", CASES)
def test_actual_worker_counterexamples_block_automatic_publication(
    tmp_path, software, worker, monkeypatch, case
):
    original = symbolic_pilot.run_search_arm

    def search(*args, **kwargs):
        result = original(*args, **kwargs)
        if result.output_directory.name == "known_covariance":
            mutate_arm(result.output_directory, case)
        return result

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", search)
    config = tmp_path / "config.toml"
    config.write_text(
        small_config().replace("seed = 20261020", "seed = 1")
        if case == "seed_bool"
        else small_config()
    )
    output = tmp_path / "assessment"
    with pytest.raises((ValueError, KeyError)):
        run_pilot(config, tmp_path / "source", assessment_output=output)
    assert_locked(output)
    # The original worker checks passed: the new assessment must catch the discrepancy.
    assert read(tmp_path / "source/result.json")["status"] == "success"


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_consistently_rewritten_python_sets_must_equal_git_inventory(
    run_source, tmp_path, change
):
    source, _, _ = run_source
    contract = read(source / future.CONTRACT)
    name = (
        "ringdown_sr/future_assessment.py"
        if change == "missing"
        else "ringdown_sr/invented.py"
    )
    if change == "missing":
        del contract["software"]["source_sha256"]["src/" + name]
    else:
        contract["software"]["source_sha256"]["src/" + name] = "0" * 64
    (source / future.CONTRACT).write_bytes(json_bytes(contract))
    binding = {
        name: sha256((source / name).read_bytes())
        for name in (future.INPUTS, future.CONTRACT)
    }
    for path in source.rglob("metadata*.json"):
        document = read(path)
        for key in ("provenance", "worker_provenance"):
            if key not in document:
                continue
            provenance = document[key]
            if change == "missing":
                del provenance["python_source_sha256"][name]
            else:
                provenance["python_source_sha256"][name] = "0" * 64
            provenance["python_source_set_sha256"] = sha256(
                json_bytes(provenance["python_source_sha256"])
            )
        if path.parent == source:
            document["supplemental_assessment"] = binding
        path.write_bytes(json_bytes(document))
    rehash(source)
    output = tmp_path / "subset"
    with pytest.raises(ValueError, match="Incomplete preparation source binding"):
        future.export_assessment(source, output)
    assert_locked(output)


def test_source_inventory_is_taken_from_the_preparation_commit(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    names = {"src/ringdown_sr/first.py", "src/ringdown_sr/nested/worker.py"}
    for name in names | {"src/ringdown_sr/data.json", "unrelated.py"}:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic\n")
    git("add", ".")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Test inventory",
    )
    commit = git("rev-parse", "HEAD")
    (tmp_path / "src/ringdown_sr/first.py").unlink()
    (tmp_path / "src/ringdown_sr/uncommitted.py").write_text("not in preparation\n")
    monkeypatch.setattr(future, "git", git)
    assert future.python_source_names(commit) == names


def test_report_retains_verified_recorded_seed_and_rule(run_source):
    source, output, _ = run_source
    for record in read(output / "assessment_records.json"):
        identity = record["source_identity"]
        front = read(source / "symbolic" / identity["arm"] / "result.json")
        assert identity["original_seed"] == front["rng"]["python_seed"]
        assert identity["original_rng"] == front["rng"]
        assert identity["original_selection_rule"] == front["selection"]
