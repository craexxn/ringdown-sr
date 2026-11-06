"""Counterexamples for paired scope, unknown costs and control reuse integrity."""

import copy
import io
import tarfile
from pathlib import Path

import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import iteration_time as comparison
from ringdown_sr import time_budget_profile as profile
from ringdown_sr import time_control_import as controls
from ringdown_sr.pilot import _write_json


def paired_cells():
    return [
        {
            "plan": plan,
            "status": "completed",
            "A": plan["arm"] == "Z",
            "A_and_original_family": False,
            "curve_grade": "A" if plan["arm"] == "Z" else "D",
            "original_family_status": "unresolved",
            "stop": "fixture",
            "costs": {key: 10 for key in comparison.COST_FIELDS},
        }
        for plan in comparison.bridge.cells("fresh_all")
    ]


@pytest.mark.parametrize(
    "change,decision",
    [
        (20, "quality_gain_with_more_cost"),
        (None, "positive_development_signal"),
    ],
)
def test_worker_cost_controls_only_the_fixed_descriptive_interpretation(
    change, decision
):
    cells = paired_cells()
    if change is not None:
        for cell in cells:
            if cell["plan"]["arm"] == "Z":
                cell["costs"]["worker_wall_seconds"] = change
    result = comparison.comparison(cells)
    assert result["interpretation"] == decision
    assert len(result["pairs"]) == 4
    assert (
        result["totals"]["I"]["denominator"]
        == result["totals"]["Z"]["denominator"]
        == 4
    )
    assert result["totals"]["Z"]["A_and_original_family"] == 0


def test_unknown_costs_are_not_zero_and_failed_cases_keep_the_denominator():
    cells = paired_cells()
    failed = next(c for c in cells if c["plan"]["arm"] == "Z")
    failed.update(status="worker_failed", A=False, curve_grade="no_output")
    failed["costs"]["worker_wall_seconds"] = None
    result = comparison.comparison(cells)
    assert result["totals"]["Z"]["A"] == 3
    assert result["totals"]["Z"]["denominator"] == 4
    assert result["totals"]["Z"]["failures"] == 1
    assert result["totals"]["Z"]["costs"]["worker_wall_seconds"] is None
    assert result["interpretation"] == "quality_gain_costs_incomplete"
    assert result["all_costs_observed"] is False


@pytest.mark.parametrize(
    "mutation", ["remove", "duplicate", "wrong_seed", "unfinished"]
)
def test_no_partial_or_selectively_replaced_control_arm(mutation):
    cells = paired_cells()
    if mutation == "remove":
        cells.pop()
    elif mutation == "duplicate":
        cells[-1] = copy.deepcopy(cells[0])
    elif mutation == "wrong_seed":
        cells[-1]["plan"]["seed"] += 100
    else:
        cells[-1]["status"] = "running"
    with pytest.raises(ValueError, match="four fixed cases"):
        comparison.comparison(cells)


@pytest.mark.parametrize("value", [True, -1, float("inf"), float("nan"), "unknown"])
def test_invalid_costs_are_rejected(value):
    cells = paired_cells()
    cells[0]["costs"]["worker_wall_seconds"] = value
    with pytest.raises(ValueError, match="measured cost"):
        comparison.comparison(cells)


def archive(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as output:
        for name, data, kind in entries:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(data)
            output.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_archive_allows_documented_verification_root_without_loading_binary_state():
    root, files = controls.archive_files(
        archive(
            [
                ("run/completion/assessment_report.json", b"{}", tarfile.REGTYPE),
                ("run/worker/checkpoint.pkl", b"never deserialize", tarfile.REGTYPE),
                ("run-verification/assessment_report.json", b"{}", tarfile.REGTYPE),
            ]
        )
    )
    assert root == "run" and len(files) == 3


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escape", tarfile.REGTYPE),
        ("/absolute", tarfile.REGTYPE),
        ("run/link", tarfile.SYMTYPE),
        ("other/file", tarfile.REGTYPE),
        ("run/completion/assessment_report.json", tarfile.REGTYPE),
    ],
)
def test_archive_rejects_paths_links_unknown_roots_and_duplicates(name, kind):
    raw = archive(
        [
            ("run/completion/assessment_report.json", b"{}", tarfile.REGTYPE),
            (name, b"", kind),
        ]
    )
    with pytest.raises(ValueError):
        controls.archive_files(raw)


def test_thread_evidence_is_required_for_all_four_controls_even_when_they_failed(
    monkeypatch, tmp_path
):
    _write_json(tmp_path / "preparation.json", {"scope": "scientific"})
    monkeypatch.setattr(controls.cross, "environment_key", lambda value: value)
    for number, seed in zip((2, 7, 12, 17), profile.SEEDS, strict=True):
        _write_json(
            tmp_path / f"request-{number:02d}.json",
            {"cell": {"seed": seed, "niterations": 2000}},
        )
        directory = tmp_path / f"cell-{number:02d}"
        directory.mkdir()
        _write_json(directory / "options.json", {"initial": {"environment": {}}})
        _write_json(directory / "outcome.json", {"status": "worker_failed"})
    result = controls.eligibility(tmp_path, {"archive_sha256": "fixture"})
    assert result["eligible"] is False
    assert len(result["controls"]) == len(result["reasons"]) == 4
    assert result["quality_used_for_eligibility"] is False
    assert result["automatic_fallback"] is False
    assert all(c["status"] == "worker_failed" for c in result["controls"])


def test_unconfirmed_reuse_never_starts_or_automatically_switches_mode(tmp_path):
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="no automatic fallback"):
        comparison.run(output, reason="reuse", technical=True)
    assert not output.exists()
    with pytest.raises(ValueError, match="mode reason"):
        comparison.run(output, mode="fresh_all", technical=True)
    assert not output.exists()


@pytest.mark.parametrize("late", [False, True])
def test_changed_raw_evidence_revokes_the_entire_release(monkeypatch, tmp_path, late):
    root, output = tmp_path / "raw", tmp_path / "release"
    root.mkdir()
    original = root / "original.json"
    original.write_bytes(b"original")
    unlink = Path.unlink
    if late:

        def changed(path, *args, **kwargs):
            result = unlink(path, *args, **kwargs)
            if path == output / publication.LOCK:
                original.write_bytes(b"changed after unlocking")
            return result

        monkeypatch.setattr(Path, "unlink", changed)

    def build(consumed):
        comparison.hold_inventory(consumed, root, {"original.json": b"original"})
        if not late:
            (root / "extra.json").write_bytes(b"late addition")
        return {"format": "fixture", "comparison": {"A": 4}}, "fixture", {}

    with pytest.raises(ValueError, match="changed"):
        publication.export_transaction(output, build)
    assert (output / publication.LOCK).exists()
    assert not (output / publication.MANIFEST).exists()
    assert "comparison" not in comparison.load_json(output, publication.REPORT)


def test_failed_costs_use_actual_status_measurement_and_keep_missing_fit_cpu(tmp_path):
    worker = tmp_path / "worker"
    worker.mkdir()
    _write_json(
        tmp_path / "outcome.json",
        {"status": "worker_failed", "failure_kind": "fit_error"},
    )
    _write_json(tmp_path / "timing.json", {"run_seconds": 30})
    _write_json(worker / "metadata.json", {"phase": "failed"})
    _write_json(worker / "status.json", {"status": "failed", "total_wall_seconds": 24})
    cell = comparison.cell_record(tmp_path, {"arm": "I"}, {}, {}, reused=True)
    assert cell["costs"]["worker_wall_seconds"] == 24
    assert cell["costs"]["fit_wall_seconds"] is None
    assert cell["costs"]["cpu_user_seconds"] is None
    assert cell["A"] is False and cell["stop"] == "fit_error"
