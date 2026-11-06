"""Remainder exports bind original selections, references, sources and publication."""

from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import test_future_assessment as fixtures
import test_symbolic_pilot as worker_fixtures
from test_remainder_proof import core
from test_structure_assessment import bind_root_contract
from test_structure_proof import op, q
from test_symbolic_pilot import read, small_config

from ringdown_sr import future_assessment as future
from ringdown_sr.assessment_publication import LOCK, PENDING, REPORT
from ringdown_sr.assessment_sources import json_bytes, sha256
from ringdown_sr.pilot import run_pilot
from ringdown_sr.remainder_proof import _fraction

software = fixtures.software
worker = fixtures.worker


@pytest.fixture
def selected_remainder(tmp_path, software, worker, monkeypatch):
    tree = op("+", core(), q(0.5))
    monkeypatch.setattr(worker_fixtures, "candidate_tree", lambda: tree)
    monkeypatch.setattr(worker_fixtures, "constant", lambda value: q(1e6))
    write_worker = fixtures.write_worker

    def fixed_worker(*args, **kwargs):
        run = write_worker(*args, **kwargs)
        path = run.output_directory / "result.json"
        result = read(path)
        result["candidates"][1]["complexity"] = 11
        path.write_bytes(json_bytes(result))
        return run

    monkeypatch.setattr(fixtures, "write_worker", fixed_worker)
    config = tmp_path / "config.toml"
    config.write_text(small_config())
    source, output = tmp_path / "source", tmp_path / "assessment"
    assert run_pilot(config, source, assessment_output=output).status == "success"
    return source, output


def test_automatic_and_saved_exports_prove_bounds_from_the_same_original(
    selected_remainder, tmp_path
):
    source, automatic = selected_remainder
    later = tmp_path / "retrospective"
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    report = future.export_assessment(source, later)
    assert (
        report["stage"] == 3 and report["remainder_policy_timing"] == "before_first_fit"
    )
    assert read(automatic / "assessment_records.json") == read(
        later / "assessment_records.json"
    )
    with np.load(source / future.INPUTS, allow_pickle=False) as arrays:
        for record in read(later / "assessment_records.json"):
            front = read(
                source / "symbolic" / record["source_identity"]["arm"] / "result.json"
            )
            assert (
                record["source_identity"]["original_selected_index"]
                == front["selected_index"]
                == 1
            )
            assert record["original_candidate"] == front["candidates"][1]
            c = record["supplemental"]["remainder"]["components"][0]
            assert _fraction(c["bound"]["upper"]) == Fraction(1, 2)
            for grid in ("training", "diagnostic"):
                y = [Fraction.from_float(float(v)) for v in arrays[grid + "_truth"]]
                ms = sum(v * v for v in y) / len(y)
                relative = c["relative_contribution_bounds"][grid]
                rms = _fraction(relative["relative_rms_upper"])
                assert rms * rms * ms >= Fraction(1, 4)
                assert _fraction(relative["relative_max_upper"]) == Fraction(
                    1, 2
                ) / max(map(abs, y))
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }


def test_late_remainder_bound_change_revokes_publication(
    selected_remainder, tmp_path, monkeypatch
):
    source, _ = selected_remainder
    output = tmp_path / "late"
    write = Path.write_bytes

    def mutate(path, raw):
        result = write(path, raw)
        if path.name == PENDING:
            target = output / "assessment_records.json"
            records = read(target)
            records[0]["supplemental"]["remainder"]["components"][0]["bound"]["upper"][
                "numerator_hex"
            ] = "0x0"
            write(target, json_bytes(records))
        return result

    monkeypatch.setattr(Path, "write_bytes", mutate)
    with pytest.raises(ValueError, match="artifact changed"):
        future.export_assessment(source, output)
    assert (output / LOCK).exists()
    assert read(output / REPORT)["groups"] == []


@pytest.mark.parametrize(
    "name",
    [
        "src/ringdown_sr/remainder_proof.py",
        "src/ringdown_sr/remainder_assessment.py",
        "data/remainder_assessment_v1.json",
        "docs/supplemental_remainder.md",
    ],
)
def test_consistently_rehashed_preparation_cannot_omit_new_bindings(
    selected_remainder, tmp_path, name
):
    source, _ = selected_remainder
    contract = read(source / future.CONTRACT)
    del contract["software"]["source_sha256"][name]
    (source / future.CONTRACT).write_bytes(json_bytes(contract))
    if name.startswith("src/"):
        for path in source.rglob("metadata*.json"):
            data = read(path)
            for key in ("provenance", "worker_provenance"):
                if key in data:
                    p = data[key]
                    del p["python_source_sha256"][name.removeprefix("src/")]
                    p["python_source_set_sha256"] = sha256(
                        json_bytes(p["python_source_sha256"])
                    )
            path.write_bytes(json_bytes(data))
    bind_root_contract(source)
    output = tmp_path / "subset"
    with pytest.raises(ValueError, match="Incomplete preparation source binding"):
        future.export_assessment(source, output)
    assert (output / LOCK).exists()


def test_remainder_contract_is_persisted_before_the_first_fit(
    tmp_path, software, worker, monkeypatch
):
    from ringdown_sr import symbolic_pilot

    def before_fit(config, directory):
        contract = read(Path(directory).parent / future.CONTRACT)
        assert contract["software"]["policy"]["stage"] == 3
        for name in future.remainder.FILES:
            assert contract["software"]["source_sha256"][name] == sha256(
                (future.ROOT / name).read_bytes()
            )
        raise RuntimeError("intentional stop before first fit")

    monkeypatch.setattr(symbolic_pilot, "run_covariance_pilot", before_fit)
    config = tmp_path / "config.toml"
    config.write_text(small_config())
    with pytest.raises(ValueError, match="successful"):
        run_pilot(
            config, tmp_path / "source", assessment_output=tmp_path / "assessment"
        )
    assert (tmp_path / "assessment" / LOCK).exists()
