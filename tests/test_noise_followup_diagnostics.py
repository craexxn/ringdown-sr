"""Exercise real bounded diagnostics and publication guards on small fixtures."""

import copy
import csv
import io
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_followup_diagnostics as diagnostics
from ringdown_sr import noise_followup_inputs as inputs


def _read(path):
    return sources.read_json(Path(path).read_bytes())


def _snapshot(path):
    return {
        str(item.relative_to(path)): item.read_bytes()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def _revoked(path):
    assert (path / publication.LOCK).is_file()
    assert not (path / publication.MANIFEST).exists()
    assert _read(path / publication.REPORT)["status"] == "failed"


@pytest.fixture(scope="module")
def fixture_protocol():
    """Retain real calculations; use two unrelated 4-Hz fixture recordings."""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(inputs, "SAMPLE_RATE", 4)
    table = {
        "reserved": {"acquisition_jitter": 101, "evaluation_grid": 102},
        "diagnostic_cases": [
            {
                "id": f"diagnostic-{model}-01",
                "noise_model": model,
                "block": 1,
                "noise_seed": 200 + index,
                "background_seed": 300 + index,
                "search_seeds": [],
            }
            for index, model in enumerate(("ar1", "white"))
        ],
    }
    monkeypatch.setattr(inputs, "_seed_table", lambda: copy.deepcopy(table))
    monkeypatch.setattr(inputs, "_protocol", lambda consumed: {"fixture": True})
    monkeypatch.setattr(inputs, "_freeze_sources", lambda consumed: {"fixture": True})
    monkeypatch.setattr(inputs, "initial_rng_states", lambda: {"fixture": True})
    original = diagnostics.covariance.welch_covariance

    def fixture_welch(series):
        return original(series, sample_rate_hz=4, nperseg=128, noverlap=64)

    monkeypatch.setattr(diagnostics.covariance, "welch_covariance", fixture_welch)
    yield
    monkeypatch.undo()


@pytest.fixture(scope="module")
def baseline(tmp_path_factory, fixture_protocol):
    root = tmp_path_factory.mktemp("small-diagnostics") / "diagnostics"
    report = diagnostics.run(root)
    return SimpleNamespace(root=root, report=report)


@pytest.fixture
def run_copy(tmp_path, baseline):
    root = tmp_path / "diagnostics"
    shutil.copytree(baseline.root, root)
    return root


def test_complete_diagnostics_and_read_only_export_are_byte_identical(
    baseline, tmp_path
):
    root, report = baseline.root, baseline.report
    assert report["planned_cases"] == 2
    assert report["planned_estimates"] == report["completed_estimates"] == 8
    assert report["failed_estimates"] == 0
    assert report["search_calls"] == 0
    assert report["automatic_method_selection"] is False
    before = _snapshot(root)
    export = tmp_path / "verification"
    replay = diagnostics.verify(root, export=export)
    assert replay == report
    assert _snapshot(root) == before
    assert _snapshot(export) == _snapshot(root / "completion")
    assert {p.name for p in root.iterdir()} == {
        "inputs",
        "inputs-call.json",
        "completion",
        "call.json",
    }
    identities = set()
    for record in report["records"]:
        identities.add((record["case"], record["duration_seconds"], record["method"]))
        raw = (root / "completion" / record["arrays_path"]).read_bytes()
        assert sources.sha256(raw) == record["arrays_sha256"]
        with np.load(io.BytesIO(raw), allow_pickle=False) as arrays:
            expected = {"covariance", "raw_covariance"}
            if record["method"] == "welch_toeplitz":
                expected |= {"frequencies_hz", "psd", "acf"}
                assert arrays["frequencies_hz"][-1] == 2
            assert set(arrays.files) == expected
            assert arrays["covariance"].shape == (128, 128)
    assert len(identities) == 8
    call = _read(root / "call.json")
    assert len(call["estimator_measurements"]) == 8
    assert (
        sum(m["wall_seconds"] for m in call["estimator_measurements"])
        <= call["wall_seconds"]
    )


@pytest.mark.parametrize(
    "mutation", ["extra_root", "extra_completion", "missing_array", "symlink"]
)
def test_exact_inventories_and_symlinks_are_rejected(run_copy, mutation):
    completion = run_copy / "completion"
    if mutation == "extra_root":
        (run_copy / "unbound.txt").write_text("unexpected")
    elif mutation == "extra_completion":
        (completion / "unbound.txt").write_text("unexpected")
    elif mutation == "missing_array":
        next(completion.glob("*.npz")).unlink()
    else:
        original = completion / publication.SUMMARY
        moved = run_copy.parent / "moved-summary.md"
        original.rename(moved)
        original.symlink_to(moved)
    with pytest.raises(ValueError):
        diagnostics.verify(run_copy)


@pytest.mark.parametrize(
    "mutation", ["negative", "boolean", "identity", "missing", "contained", "extra"]
)
def test_costs_require_complete_exact_measurements(run_copy, mutation):
    path = run_copy / "call.json"
    call = _read(path)
    if mutation == "negative":
        call["cpu_user_seconds"] = -1
    elif mutation == "boolean":
        call["process_peak_rss_kib"] = True
    elif mutation == "identity":
        call["estimator_measurements"][0]["method"] = "other"
    elif mutation == "missing":
        call["estimator_measurements"].pop()
    elif mutation == "contained":
        call["estimator_measurements"][0]["wall_seconds"] = call["wall_seconds"] + 1
    else:
        call["unbound_measurement"] = 123
    path.write_bytes(sources.json_bytes(call))
    with pytest.raises(ValueError):
        diagnostics.verify(run_copy)


def test_expected_covariance_failure_is_retained_without_replacement(
    tmp_path, fixture_protocol, monkeypatch
):
    original = diagnostics.covariance.empirical_from_series

    def reject_short(series, **kwargs):
        if len(series) == 256:
            raise diagnostics.CovarianceEstimationError("fixture raw moment failed")
        return original(series, **kwargs)

    monkeypatch.setattr(diagnostics.covariance, "empirical_from_series", reject_short)
    root = tmp_path / "failed-estimates"
    report = diagnostics.run(root)
    assert report["planned_estimates"] == 8
    assert report["failed_estimates"] == 2
    assert report["completed_estimates"] == 6
    failures = [r for r in report["records"] if r["estimate"]["status"] == "failed"]
    assert len(failures) == 2
    for record in failures:
        assert record["method"] == "full_matrix" and record["duration_seconds"] == 64
        assert (
            record["selected_diagnostics"]["relative_frobenius_error"]["value"] is None
        )
        with np.load(
            root / "completion" / record["arrays_path"], allow_pickle=False
        ) as arrays:
            assert not arrays.files
    rows = list(
        csv.DictReader(io.StringIO((root / "completion/diagnostics.csv").read_text()))
    )
    assert len(rows) == 8
    assert (
        sum(
            row["status"] == "failed" and row["relative_frobenius_error"] == ""
            for row in rows
        )
        == 2
    )
    assert diagnostics.verify(root) == report


def test_unknown_failure_aborts_and_preserves_call_evidence(
    tmp_path, fixture_protocol, monkeypatch
):
    def unexpected(*args, **kwargs):
        raise RuntimeError("unclassified fixture error")

    monkeypatch.setattr(diagnostics, "_estimate", unexpected)
    root = tmp_path / "aborted"
    with pytest.raises(RuntimeError, match="unclassified fixture error"):
        diagnostics.run(root)
    _revoked(root / "completion")
    call = _read(root / "call.json")
    assert call["status"] == "aborted"
    assert "unclassified fixture error" in call["error"]
    with pytest.raises(ValueError):
        diagnostics.run(root)


@pytest.mark.parametrize("mutation", ["source", "inventory"])
def test_late_source_or_inventory_change_revokes_verification_export(
    run_copy, tmp_path, monkeypatch, mutation
):
    export = tmp_path / "verification"
    original = publication.export_transaction

    def mutate_after_publication(output, *args, **kwargs):
        result = original(output, *args, **kwargs)
        if mutation == "source":
            path = run_copy / "inputs/common.npz"
            path.write_bytes(path.read_bytes() + b"changed")
        else:
            (run_copy / "unexpected.txt").write_text("late change")
        return result

    monkeypatch.setattr(publication, "export_transaction", mutate_after_publication)
    with pytest.raises(ValueError):
        diagnostics.verify(run_copy, export=export)
    _revoked(export)


def test_late_change_after_main_publication_revokes_success(
    tmp_path, fixture_protocol, monkeypatch
):
    root = tmp_path / "late-run"
    original = publication.export_transaction

    def mutate_after_publication(output, *args, **kwargs):
        result = original(output, *args, **kwargs)
        (root / "unexpected.txt").write_text("late change")
        return result

    monkeypatch.setattr(publication, "export_transaction", mutate_after_publication)
    with pytest.raises(ValueError):
        diagnostics.run(root)
    _revoked(root / "completion")
    assert _read(root / "call.json")["status"] == "aborted"


@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds", "disjoint_wall"]
)
def test_input_preparation_is_contained_in_measured_diagnostic_cost(baseline, field):
    call = _read(baseline.root / "call.json")
    prep = baseline.report["preparation_call"]
    if field == "disjoint_wall":
        estimates = sum(item["wall_seconds"] for item in call["estimator_measurements"])
        call["wall_seconds"] = (
            max(prep["wall_seconds"], estimates)
            + min(prep["wall_seconds"], estimates) / 2
        )
    else:
        assert prep[field] > 1e-6
        call[field] = prep[field] / 2
    with pytest.raises(ValueError):
        diagnostics._validate_timing(
            call,
            baseline.report,
            (baseline.root / "completion" / publication.REPORT).read_bytes(),
        )


def test_late_cost_file_change_revokes_main_publication(
    tmp_path, fixture_protocol, monkeypatch
):
    root = tmp_path / "late-cost"
    original = diagnostics._write_json

    def change_saved_call(path, document):
        original(path, document)
        if Path(path) == root / "call.json" and document.get("status") == "completed":
            changed = copy.deepcopy(document)
            changed["cpu_user_seconds"] += 1
            Path(path).write_bytes(sources.json_bytes(changed))

    monkeypatch.setattr(diagnostics, "_write_json", change_saved_call)
    with pytest.raises(ValueError):
        diagnostics.run(root)
    _revoked(root / "completion")
    assert _read(root / "call.json")["status"] == "aborted"


def test_raw_trajectory_symlink_is_rejected(run_copy):
    train = next((run_copy / "inputs/cases").glob("*/background_train.npy"))
    target = run_copy.parent / "raw.npy"
    train.rename(target)
    train.symlink_to(target)
    with pytest.raises(ValueError):
        diagnostics.verify(run_copy)


def test_external_consumption_retains_streamed_trajectory_guard(run_copy):
    consumed = publication.Consumption(publication.Deadline(120))
    diagnostics.verify(run_copy, consumed=consumed)
    train = next((run_copy / "inputs/cases").glob("*/background_train.npy"))
    assert train.absolute() not in consumed.files
    with train.open("r+b") as stream:
        stream.seek(-1, 2)
        original = stream.read(1)
        stream.seek(-1, 2)
        stream.write(bytes([original[0] ^ 1]))
    with pytest.raises(ValueError, match="changed after consumption"):
        consumed.check()
