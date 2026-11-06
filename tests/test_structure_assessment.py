"""End-to-end interval/proof policy binding, including legacy and publication cases."""

import subprocess
from pathlib import Path

import pytest
import test_future_assessment as fixtures
import test_symbolic_pilot as worker_fixtures
from test_future_assessment import rehash
from test_structure_proof import q, unresolved_pole_tree
from test_symbolic_pilot import read

from ringdown_sr import future_assessment as future
from ringdown_sr.assessment_publication import LOCK, PENDING, REPORT
from ringdown_sr.assessment_sources import json_bytes, sha256
from ringdown_sr.pilot import run_pilot

software = fixtures.software
worker = fixtures.worker
run_source = fixtures.run_source
replay_source = fixtures.replay_source
LEGACY_COMMIT = "e09ab286fc853fe2991f070c4d96d9f070b55d9d"


def test_completed_export_cannot_claim_pole_from_unresolved_original_domain(
    tmp_path, software, worker, monkeypatch
):
    tree = unresolved_pole_tree(0.001)
    # The fixed counterexample wins against a deliberately poor baseline;
    # preserve the ordinary selection rule and all numeric artifact checks.
    monkeypatch.setattr(worker_fixtures, "candidate_tree", lambda: tree)
    monkeypatch.setattr(worker_fixtures, "constant", lambda value: q(1e6))
    write_worker = fixtures.write_worker

    def counterexample_worker(*args, **kwargs):
        run = write_worker(*args, **kwargs)
        path = run.output_directory / "result.json"
        result = read(path)
        result["candidates"][1]["complexity"] = 17
        path.write_bytes(json_bytes(result))
        checks = run.output_directory / "checksums.json"
        checks.write_bytes(
            json_bytes({**read(checks), "result.json": sha256(path.read_bytes())})
        )
        return run

    monkeypatch.setattr(fixtures, "write_worker", counterexample_worker)
    config = tmp_path / "input.toml"
    config.write_text(worker_fixtures.small_config())
    source, output = tmp_path / "run", tmp_path / "assessment"
    assert run_pilot(config, source, assessment_output=output).status == "success"
    assert read(output / REPORT)["status"] == "completed"
    assert not (output / LOCK).exists()
    records = read(output / "assessment_records.json")
    assert len(records) == len(worker) == 3
    for record in records:
        assert record["source_identity"]["original_selected_index"] == 1
        assert record["original_candidate"]["tree"] == tree
        proof = record["supplemental"]
        assert proof["domain"]["status"] == "unresolved"
        assert proof["domain"]["nonempty_dense_original_domain_proven"] is False
        assert proof["domain"]["exclusions"][0]["kind"] == "unresolved"
        assert proof["continuous_extension"]["status"] == "unresolved"


def bind_root_contract(source):
    binding = {
        name: sha256((source / name).read_bytes())
        for name in (future.INPUTS, future.CONTRACT)
    }
    for name in ("metadata.json", "metadata_initial.json"):
        path = source / name
        document = read(path)
        document["supplemental_assessment"] = binding
        path.write_bytes(json_bytes(document))
    rehash(source)


@pytest.mark.parametrize(
    "change",
    ["nominal_end", "open_end", "missing_interval", "units", "resources", "downgrade"],
)
def test_consistently_rehashed_structure_contract_cannot_change_the_method(
    replay_source, tmp_path, change
):
    source, _, _ = replay_source
    path = source / future.CONTRACT
    contract = read(path)
    if change == "nominal_end":
        contract["structure_interval"]["endpoints"][1] = {
            "numerator_hex": "0x1",
            "denominator_hex": "0x1",
        }
    elif change == "open_end":
        contract["structure_interval"]["closed"][1] = False
    elif change == "missing_interval":
        del contract["structure_interval"]
    elif change == "units":
        contract["structure_interval"]["unit"] = "samples"
    elif change == "resources":
        contract["software"]["policy"]["proof_resource_limits"]["precisions"].append(
            2048
        )
    else:
        contract["format"] = "ringdown-sr-future-assessment-1"
        del contract["structure_interval"]
    path.write_bytes(json_bytes(contract))
    bind_root_contract(source)
    output = tmp_path / "invalid-proof-contract"
    with pytest.raises((ValueError, KeyError)):
        future.export_assessment(source, output)
    assert (output / LOCK).exists()
    assert read(output / REPORT)["groups"] == []


@pytest.mark.parametrize(
    "stage, legacy_commit",
    [(1, LEGACY_COMMIT), (2, "7b7b9dfb9117b4202522cd620c90d0ec861ccc65")],
)
def test_approved_earlier_snapshot_upgrades_explicitly_retrospectively(
    run_source, tmp_path, monkeypatch, stage, legacy_commit
):
    source, _, _ = run_source

    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=future.ROOT, text=True
        ).strip()

    def blob(commit, name):
        if commit == legacy_commit:
            return subprocess.check_output(
                ["git", "show", f"{commit}:{name}"], cwd=future.ROOT
            )
        return (future.ROOT / name).read_bytes()

    monkeypatch.setattr(future, "git", git)
    monkeypatch.setattr(future.sources, "_git_file", blob)
    names = future.preparation_source_names(legacy_commit, stage)
    hashes = {name: sha256(blob(legacy_commit, name)) for name in names}
    path = source / future.CONTRACT
    contract = read(path)
    contract["format"] = f"ringdown-sr-future-assessment-{stage}"
    if stage == 1:
        del contract["structure_interval"]
    contract["software"].update(
        software_commit=legacy_commit,
        source_sha256=hashes,
        policy=future.sources.read_json(
            blob(legacy_commit, future.STAGE_CONTRACTS[stage][0])
        ),
    )
    path.write_bytes(json_bytes(contract))
    for path in source.rglob("metadata*.json"):
        document = read(path)
        for key in ("provenance", "worker_provenance"):
            if key not in document:
                continue
            provenance = document[key]
            provenance["git"].update(commit=legacy_commit, dirty=False, changes=[])
            python = {
                name.removeprefix("src/"): digest
                for name, digest in hashes.items()
                if name.startswith("src/") and name.endswith(".py")
            }
            provenance["python_source_sha256"] = python
            provenance["python_source_set_sha256"] = sha256(json_bytes(python))
            provenance["project_file_sha256"] = {
                name: hashes[name] for name in future.PROJECT_FILES
            }
        path.write_bytes(json_bytes(document))
    bind_root_contract(source)
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    output = tmp_path / "legacy-upgrade"
    report = future.export_assessment(source, output)
    assert report["structure_policy_timing"] == (
        "retrospective_upgrade_of_stage1_snapshot" if stage == 1 else "before_first_fit"
    )
    assert (
        report["remainder_policy_timing"]
        == f"retrospective_upgrade_of_stage{stage}_snapshot"
    )
    assert report["status"] == "completed"
    assert all(
        r["supplemental"]["domain"]["status"] == "defined_everywhere"
        for r in read(output / "assessment_records.json")
    )
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }


def test_late_proof_record_mutation_revokes_stage2_release(
    replay_source, tmp_path, monkeypatch
):
    source, _, _ = replay_source
    output = tmp_path / "late-proof"
    write = Path.write_bytes

    def mutate(path, raw):
        result = write(path, raw)
        if path.name == PENDING:
            target = output / "assessment_records.json"
            records = read(target)
            records[0]["supplemental"]["original_family"]["status"] = "proven_member"
            write(target, json_bytes(records))
        return result

    monkeypatch.setattr(Path, "write_bytes", mutate)
    with pytest.raises(ValueError, match="artifact changed"):
        future.export_assessment(source, output)
    assert (output / LOCK).exists()
    assert read(output / REPORT)["groups"] == []
