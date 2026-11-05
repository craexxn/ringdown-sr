"""Independent boundary/norm oracles and unchanged historical-selection tests."""

import copy
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from test_assessment_sources import change_report
from test_assessment_sources import synthetic as _synthetic

from ringdown_sr import assessment_sources as sources
from ringdown_sr import supplemental_assessment as assessment
from ringdown_sr.assessment_publication import Consumption, Deadline
from ringdown_sr.noiseless_control import CURVE_LIMITS, curve_errors

synthetic = _synthetic


def errors(values):
    return {
        grid: {
            "status": "available",
            "reason": None,
            "relative_rms": values[2 * i],
            "relative_max": values[2 * i + 1],
        }
        for i, grid in enumerate(("training", "diagnostic"))
    }


FIXTURES = sources.read_json(
    (
        Path(__file__).parent / "fixtures/assessment/preparation_curve_cases.json"
    ).read_bytes()
)["cases"]


@pytest.mark.parametrize("case", FIXTURES, ids=lambda case: case["id"])
def test_preparation_references(case):
    values = [
        float(value["nonfinite"]) if isinstance(value, dict) else value
        for value in case["values"]
    ]
    metrics = errors(values)
    for i, status in enumerate(case["endpoint_statuses"]):
        if status != "available":
            metrics[("training", "diagnostic")[i // 2]]["status"] = status
    result = assessment.grade_curve(metrics, source_verified=case["source_verified"])
    assert result["grade"] == case["expected"]["grade"]
    assert result["status"] == case["expected"]["status"]
    if result["grade"] is None:
        assert result["reason"]


@pytest.mark.parametrize(
    "thresholds,next_grade",
    [((0.001, 0.01), "B"), ((0.01, 0.02), "C"), ((0.05, 0.10), "D")],
)
@pytest.mark.parametrize("endpoint", range(4))
@pytest.mark.parametrize("direction", [-math.inf, 0, math.inf])
def test_every_boundary_with_exact_binary64_fraction_oracle(
    thresholds, next_grade, endpoint, direction
):
    values = list(thresholds) * 2
    if direction:
        values[endpoint] = math.nextafter(values[endpoint], direction)
    # Fraction compares exact rational values represented by each Float64, independently of grading code.
    oracle = "D"
    for grade, rms, maximum in (
        ("A", 1 / 1000, 1 / 100),
        ("B", 1 / 100, 1 / 50),
        ("C", 1 / 20, 1 / 10),
    ):
        if all(
            Fraction(v) <= Fraction((rms, maximum)[i % 2]) for i, v in enumerate(values)
        ):
            oracle = grade
            break
    assert (
        assessment.grade_curve(errors(values), source_verified=True)["grade"] == oracle
    )
    if direction == math.inf:
        assert oracle == next_grade
    old_c = all(
        values[i] <= CURVE_LIMITS[("relative_rms", "relative_max")[i % 2]]
        for i in range(4)
    )
    assert (oracle == "A") == old_c


@pytest.mark.parametrize(
    "value",
    [None, True, False, -0.001, math.nan, math.inf, -math.inf, "0", {}, [], 10**1000],
)
@pytest.mark.parametrize("endpoint", range(4))
def test_invalid_endpoint_cannot_be_grade_d(value, endpoint):
    values = [0.0] * 4
    values[endpoint] = value
    result = assessment.grade_curve(errors(values), source_verified=True)
    assert result["grade"] is None and result["status"] == "not_assessable"
    assert result["reason"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m.pop("training"),
        lambda m: m.pop("diagnostic"),
        lambda m: m.update(intermediate=m.pop("diagnostic")),
        lambda m: m["training"].pop("relative_rms"),
        lambda m: m["diagnostic"].update(status="numerical_unresolved"),
        lambda m: m["diagnostic"].update(status="failed"),
        lambda m: m["training"].pop("status"),
        lambda m: m.update(diagnostic=None),
    ],
)
def test_endpoint_state_overrides_available_numbers(mutate):
    metrics = errors([0.0] * 4)
    mutate(metrics)
    assert assessment.grade_curve(metrics, source_verified=True)["grade"] is None


def test_own_grid_normalization_and_zero_crossings():
    # ||(0,4)||/||(3,0)|| = 4/3; max ratio = 4/3, not pointwise division by zero.
    training = curve_errors(np.array([3.0, 4.0]), np.array([3.0, 0.0]))
    assert training["relative_rms"] == training["relative_max"] == 4 / 3
    # ||(0,3,0)||/||(0,3,4)|| = 3/5; max ratio = 3/4, own grid norm.
    diagnostic = curve_errors(np.array([0.0, 6.0, 4.0]), np.array([0.0, 3.0, 4.0]))
    # The historical scaled algorithm incurs one rounding step beyond the exact ratio.
    assert abs(diagnostic["relative_rms"] - 3 / 5) <= math.ulp(3 / 5)
    assert diagnostic["relative_max"] == 3 / 4
    for truth in (np.zeros(2), np.array([1.0, math.inf])):
        with pytest.raises(ValueError, match="Truth"):
            curve_errors(np.ones(2), truth)


def test_all_planned_groups_remain_separate_and_missing_stays_in_denominator():
    records = [
        assessment.record(name, spec, cell)
        for name, spec in sources.contracts().items()
        for cell in spec["cells"]
    ]
    assert len(records) == 78
    groups = assessment.groups(records)
    assert len(groups) == 18  # Three four-condition series and six transfer signals.
    assert (
        sorted(group["planned_denominator"] for group in groups) == [3] * 6 + [5] * 12
    )
    for group in groups:
        assert (
            group["curve_grade_counts"]["not_assessable"]
            == group["planned_denominator"]
        )
        assert sum(group["curve_grade_counts"].values()) == group["planned_denominator"]
    for record in records:
        assert record["original_candidate"] is None
        assert record["unchanged_historical"] is None
        extra = record["supplemental"]
        assert extra["curve"]["grade"] is None
        for name in (
            "algebraic_identity",
            "domain",
            "original_family",
            "continuous_extension",
            "remainder",
            "new_parameter_match",
        ):
            assert extra[name]["status"] == "not_assessed"
        assert extra["domain"]["interval"] is None


def prepare_build(monkeypatch):
    monkeypatch.setattr(
        assessment, "freeze_software", lambda consumed: {"synthetic": True}
    )
    return Consumption(Deadline(60))


def test_complete_synthetic_export_preserves_selection_and_old_fields(
    synthetic, monkeypatch
):
    write, path, _, original = synthetic
    consumed = prepare_build(monkeypatch)
    report, summary, payloads = assessment.build_assessment(
        {"synthetic-series": write()}, consumed
    )
    assert report["corpus_status"] == "complete"
    records = sources.read_json(payloads["assessment_records.json"])
    assert (
        payloads["synthetic-series-historical-report.json"]
        == sources.archive_files(path.read_bytes(), "synthetic-series")["report.json"]
    )
    for item, cell in zip(records, original["cells"], strict=True):
        assert item["source_identity"]["original_selected_index"] == 1
        assert item["unchanged_historical"] == cell["diagnostics"]["candidates"][1]
        assert item["supplemental"]["curve"]["grade"] == "D"
    assert report["groups"][0]["curve_grade_counts"]["D"] == 2
    assert "synthetic-series" in summary
    consumed.check()


def test_invalid_archive_releases_no_series_or_grades(synthetic, monkeypatch):
    write, _, _, _ = synthetic
    path = write(lambda files: change_report(files, lambda r: r["cells"].pop()))
    report, _, payloads = assessment.build_assessment(
        {"synthetic-series": path}, prepare_build(monkeypatch)
    )
    assert report["corpus_status"] == "incomplete"
    assert report["series"][0]["release"] == "locked"
    assert report["series"][0]["verification_status"] == "failed"
    assert all(
        r["supplemental"]["curve"]["grade"] is None
        for r in sources.read_json(payloads["assessment_records.json"])
    )
    assert report["groups"][0]["planned_denominator"] == 2


def test_missing_originals_never_read_documentation_metrics(monkeypatch):
    consumed = prepare_build(monkeypatch)
    monkeypatch.setattr(
        sources,
        "read_verified_series",
        lambda *a, **k: pytest.fail("No original supplied."),
    )
    report, _, payloads = assessment.build_assessment({}, consumed)
    assert report["corpus_status"] == "incomplete"
    assert len(sources.read_json(payloads["assessment_records.json"])) == 78
    assert all(
        s["verified"] == 0 and s["release"] == "locked" for s in report["series"]
    )


@pytest.mark.parametrize(
    "error", [InterruptedError("signal"), TimeoutError("deadline"), KeyboardInterrupt()]
)
def test_import_cancellation_is_not_swallowed_as_invalid_series(
    synthetic, monkeypatch, error
):
    write, _, _, _ = synthetic
    consumed = prepare_build(monkeypatch)

    def abort(*args, **kwargs):
        raise error

    monkeypatch.setattr(sources, "read_verified_series", abort)
    with pytest.raises(type(error)):
        assessment.build_assessment({"synthetic-series": write()}, consumed)


def test_records_do_not_mutate_inputs_or_use_truth_parameters(synthetic):
    write, _, spec, _ = synthetic
    verified = sources.read_verified_series(write(), "synthetic-series")
    original = sources.read_json(verified.records[0])
    before = copy.deepcopy(original)
    first = assessment.record(
        "synthetic-series", spec, original["cell"], original, verification="verified"
    )
    assert original == before
    original["unchanged_historical"]["parameter_match"] = {
        "status": "matched",
        "truth": "different",
    }
    second = assessment.record(
        "synthetic-series", spec, original["cell"], original, verification="verified"
    )
    assert first["supplemental"] == second["supplemental"]


def test_policy_document_matches_confirmed_float64_contract():
    policy = sources.read_json(assessment.POLICY.read_bytes())
    assert (
        policy["threshold_semantics"] == "binary64_inclusive_no_rounding_no_tolerance"
    )
    assert policy["planned_selections"] == 78
    for threshold, (grade, rms, maximum) in zip(
        policy["thresholds"], assessment.THRESHOLDS, strict=True
    ):
        assert threshold == {
            "grade": grade,
            "relative_rms": rms,
            "relative_max": maximum,
            "rms_hex": rms.hex(),
            "max_hex": maximum.hex(),
        }


@pytest.fixture
def software(tmp_path, monkeypatch):
    original_policy = sources.read_json(assessment.POLICY.read_bytes())
    paths = [
        "data/supplemental_assessment_v1.json",
        "data/supplemental_series.json",
        "scripts/export_supplemental_assessment.py",
        "docs/supplemental_assessment.md",
        "uv.lock",
        "pyproject.toml",
        ".python-version",
    ]
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic software")
    policy = tmp_path / paths[0]
    policy.write_bytes(sources.json_bytes(original_policy))
    monkeypatch.setattr(assessment, "ROOT", tmp_path)
    monkeypatch.setattr(assessment, "POLICY", policy)
    monkeypatch.setattr(sources, "CATALOG", tmp_path / paths[1])
    monkeypatch.setattr(
        assessment, "git", lambda *args: "" if args[0] == "status" else "1" * 40
    )
    monkeypatch.setattr(
        sources, "_git_file", lambda commit, name: (tmp_path / name).read_bytes()
    )
    return policy, original_policy


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(policy_id="unknown"),
        lambda p: p.update(schema="unknown"),
        lambda p: p.update(stage=2),
        lambda p: p.update(threshold_semantics="decimal_exact"),
        lambda p: p.update(grid_roles=["diagnostic", "training"]),
        lambda p: p.update(domain_interval=[0, 1]),
        lambda p: p.update(planned_selections=58),
        lambda p: p["thresholds"][0].update(relative_rms=0.002),
        lambda p: p["thresholds"][0].update(rms_hex=(0.002).hex()),
    ],
)
def test_unknown_or_inconsistent_policy_is_rejected(software, mutate):
    path, policy = software
    mutate(policy)
    path.write_bytes(sources.json_bytes(policy))
    with pytest.raises(ValueError):
        assessment.freeze_software(Consumption(Deadline(60)))


def test_sources_are_frozen_before_consumption_and_rechecked(software):
    path, _ = software
    consumed = Consumption(Deadline(60))
    provenance = assessment.freeze_software(consumed)
    assert provenance["source_sha256"][
        "data/supplemental_assessment_v1.json"
    ] == sources.sha256(path.read_bytes())
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="Consumed file changed"):
        consumed.check()


def test_changed_git_head_and_uncommitted_work_are_rejected(software, monkeypatch):
    consumed = Consumption(Deadline(60))
    assessment.freeze_software(consumed)
    monkeypatch.setattr(assessment, "git", lambda *args: "2" * 40)
    with pytest.raises(ValueError, match="checkout changed"):
        consumed.check()
    with pytest.raises(ValueError, match="clean, committed"):
        assessment.freeze_software(Consumption(Deadline(60)))
