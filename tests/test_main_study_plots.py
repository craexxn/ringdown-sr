"""Protect original formulas, complete grids, failure slots and read-only exports."""

import copy
import csv
import io
import json
from types import SimpleNamespace

import pytest
from test_main_study_assessment import arrays as reference_arrays
from test_main_study_assessment import width_failure_fields
from test_structure_proof import T, op, q

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import main_study as study
from ringdown_sr import main_study_assessment as assessment
from ringdown_sr import main_study_plots as plots
from ringdown_sr import main_study_technical as technical


def arrays(signal_id="signal_200_4ms"):
    result = reference_arrays()
    if signal_id == "signal_250_6ms":
        for key in ("signal", "main_truth", "support_truth", "endpoint_truth"):
            result[key] *= 0.5
    result["observed"] = result["signal"] + 0.1
    return result


def candidate(tree=None):
    return {
        "tree": q(0.125) if tree is None else tree,
        "prediction": [0.5] * 103,
        "display_equation": "0.12500000000000000",
        "complexity": 1,
        "loss": 0.25,
    }


def record(spec, arm, *, status="success", tree=None):
    package = {
        "package_status": status,
        "search_calls": 0 if status == "not_run" else 4,
        "costs": {
            "worker_wall_seconds": 10.0,
            "fit_wall_seconds": 8.0,
            "callback_calls_during_fit": 100,
        },
        "selected_candidate": candidate(tree) if status == "success" else None,
    }
    if status == "failed":
        package.update(width_failure_fields())
    identity = {
        "signal_id": spec["signal_id"],
        "case_id": spec["id"],
        "model": spec["noise_model"],
        "block": spec["block"],
        "condition": arm,
        "grid": "uniform",
        "package_sha256": None if status == "not_run" else "1" * 64,
        "input_sha256": "2" * 64,
        "selected_member_path": f"symbolic/{arm}/member-02/result.json"
        if status == "success"
        else None,
    }
    return assessment.assess_package(
        package, arrays(spec["signal_id"]), amplitude=1.0, source_identity=identity
    )


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(assessment, "PLANNED_BLOCKS", {"ar1": 1, "white": 1})
    software = {"software_commit": "a" * 40, "source_sha256": {"fixture": "b" * 64}}
    signal_ids = tuple(plots.inputs.SIGNALS)
    roots = {name: tmp_path / name for name in ("inputs", "technical", *signal_ids)}
    for root in roots.values():
        (root / "completion").mkdir(parents=True)
        (root / "completion" / publication.REPORT).write_bytes(
            sources.json_bytes({"fixture_source": root.name})
        )
        (root / "original.bin").write_bytes(b"unchanged original")
    specs = [
        {
            "id": f"{signal_id}-{model}-01",
            "signal_id": signal_id,
            "noise_model": model,
            "block": 1,
            "search_seeds": [101, 102, 103, 104],
            "signal": {"amplitude": 1.0},
            "sampling": {"n_samples": 103},
        }
        for signal_id in signal_ids
        for model in ("ar1", "white")
    ]
    monkeypatch.setattr(plots.inputs, "case_specs", lambda **kwargs: specs)
    prepared = plots.inputs.PreparedInputs(
        roots["inputs"], {"software": software}, {}, {s["id"]: s for s in specs}
    )
    records = []
    for spec in specs:
        for arm in plots.LABELS:
            status = (
                "not_run" if spec == specs[0] and arm == "estimated_64s" else "success"
            )
            if spec == specs[1] and arm == "estimated_64s":
                status = "failed"
            records.append(record(spec, arm, status=status))
    reports = {}
    for signal_id in signal_ids:
        selected = [
            r for r in records if r["source_identity"]["signal_id"] == signal_id
        ]
        reports[signal_id] = {
            "signal_id": signal_id,
            "software": software,
            "preparation_sha256": "3" * 64,
            "technical_report_sha256": "4" * 64,
            "assessments": selected,
            "summary": assessment.summary(selected, signal_id=signal_id),
            "signal_normalization": {
                "signal_id": signal_id,
                "amplitude": 1.0,
                "noise_standard_deviation": 0.05,
                "noise_over_amplitude": 0.05,
                "training_signal_rms": 1.0 if signal_id == signal_ids[0] else 0.5,
                "noise_over_training_signal_rms": 0.05
                if signal_id == signal_ids[0]
                else 0.1,
                "rms_reference": "clean_signal_equal_weight_training_samples",
                "n_samples": 103,
                "signal_unit": "dimensionless",
                "time_unit": "s",
                "training_time_s_fingerprint": sources.fingerprint(
                    arrays(signal_id)["time_s"]
                ),
                "training_signal_fingerprint": sources.fingerprint(
                    arrays(signal_id)["signal"]
                ),
                "interpretation": "marginal_noise_ratios_not_detector_snr",
            },
        }
    calls = []

    def verify(preparation, technical_path, series, **kwargs):
        assert preparation == roots["inputs"]
        assert technical_path == roots["technical"]
        signal_id = kwargs["signal_id"]
        assert series == roots[signal_id]
        assert kwargs["previous"] == (
            None if signal_id == signal_ids[0] else roots[signal_ids[0]]
        )
        assert kwargs.get("export") is None
        consumed = kwargs["consumed"]
        for root in roots.values():
            path = root / "original.bin"
            consumed.add(path, path.read_bytes())
        calls.append(("verify", signal_id))
        return reports[signal_id]

    def verify_inputs(path, consumed=None, *, regenerate=False):
        assert path == roots["inputs"] and consumed is not None and regenerate is False
        return prepared

    def read_case(value, case_id, consumed=None, *, regenerate=False):
        assert value is prepared and consumed is not None and regenerate is False
        calls.append(("case", case_id))
        return SimpleNamespace(spec=prepared.cases[case_id])

    monkeypatch.setattr(study, "verify", verify)
    monkeypatch.setattr(plots.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(plots.inputs, "read_case", read_case)
    monkeypatch.setattr(
        plots.inputs,
        "arm_arrays",
        lambda prepared, case, arm: arrays(case.spec["signal_id"]),
    )
    return SimpleNamespace(
        roots=roots,
        prepared=prepared,
        specs=specs,
        reports=reports,
        records=records,
        calls=calls,
        signal_ids=signal_ids,
        output=tmp_path / "plots",
    )


def tiny_render(monkeypatch):
    monkeypatch.setattr(
        plots,
        "_curve_plot",
        lambda *args: {"png": b"PNG fixture", "svg": b"SVG fixture"},
    )
    monkeypatch.setattr(
        plots.shared,
        "_images",
        lambda figure: {"png": b"PNG fixture", "svg": b"SVG fixture"},
    )


def run_export(artifacts, *, both=True):
    keys = artifacts.signal_ids if both else artifacts.signal_ids[:1]
    return plots.export(
        artifacts.roots["inputs"],
        artifacts.roots["technical"],
        {key: artifacts.roots[key] for key in keys},
        artifacts.output,
    )


@pytest.mark.parametrize("both", (False, True))
def test_complete_declared_sections_keep_exact_formulas_all_grids_and_failures(
    artifacts, monkeypatch, both
):
    tiny_render(monkeypatch)
    before = {
        path: path.read_bytes()
        for root in artifacts.roots.values()
        for path in root.rglob("*")
        if path.is_file()
    }
    report = run_export(artifacts, both=both)
    assert report["planned_outputs"] == (16 if both else 8)
    assert report["signal_ids"] == list(
        artifacts.signal_ids if both else artifacts.signal_ids[:1]
    )
    assert report["selection_changed"] is report["fits_or_searches_executed"] is False
    assert plots.verify_export(artifacts.output) == report
    assert all(path.read_bytes() == raw for path, raw in before.items())
    stem = artifacts.specs[0]["id"] + "-ordinary"
    metadata = json.loads((artifacts.output / (stem + ".json")).read_bytes())
    rows = list(
        csv.DictReader(io.StringIO((artifacts.output / (stem + ".csv")).read_text()))
    )
    assert len(rows) == 2153
    assert (
        metadata["identity"]["member_position"] == 2
        and metadata["identity"]["seed"] == 102
    )
    assert (
        artifacts.output / (stem + ".formula.txt")
    ).read_text() == "0.12500000000000000"
    assert metadata["candidate"]["tree"] == q(0.125)
    assert {float(r["prediction"]) for r in rows if r["grid"] == "training"} == {0.5}
    assert {float(r["prediction"]) for r in rows if r["grid"] != "training"} == {0.125}
    assert metadata["metrics"]["main"]["relative_l2"] == 0.875
    missing = json.loads(
        (
            artifacts.output / (artifacts.specs[0]["id"] + "-estimated_64s.json")
        ).read_bytes()
    )
    assert missing["candidate"] is None and missing["point_count"] == 2153
    assert missing["status"] == "not_run"
    assert (artifacts.output.parent / "plots-call.json").is_file()


def test_verified_plot_export_keeps_width_failure_and_rejects_changed_reason(
    artifacts, monkeypatch
):
    tiny_render(monkeypatch)
    report = run_export(artifacts, both=False)
    assert plots.verify_export(artifacts.output) == report
    width_stem = artifacts.specs[1]["id"] + "-estimated_64s"
    width = json.loads((artifacts.output / (width_stem + ".json")).read_bytes())
    reason = "reference_width_exceeds_bound"
    assert width["status"] == "failed" and width["reason"] == reason
    assert width["candidate"] is width["identity"]["member_position"] is None
    assert reason in (artifacts.output / (width_stem + ".formula.txt")).read_text()
    width_rows = list(
        csv.DictReader(
            io.StringIO((artifacts.output / (width_stem + ".csv")).read_text())
        )
    )
    assert len(width_rows) == 2153
    assert {
        (row["prediction"], row["status"], row["reason"]) for row in width_rows
    } == {("", "not_available", reason)}
    overview = artifacts.output / (artifacts.signal_ids[0] + "-white-overview.csv")
    overview_row = next(
        row
        for row in csv.DictReader(io.StringIO(overview.read_text()))
        if row["condition"] == "estimated_64s"
    )
    assert (
        overview_row["primary_reason"] == reason
        and overview_row["relative_l2_main"] == ""
    )
    assert overview_row["search_calls"] == "4"
    assert float(overview_row["original_worker_wall_seconds"]) == 21.0

    width_rows[0]["reason"] = "package_failed"
    changed = plots.shared._csv(width_rows)
    width["points_csv_sha256"] = sources.sha256(changed)
    with pytest.raises(ValueError, match="unavailable original output"):
        plots._verify_points(width, changed, artifacts.specs[1])


def test_partial_nonfinite_grid_keeps_finite_points_without_changing_denominator():
    data = arrays()
    pole = float(data["main_time_s"][0])
    selected = candidate(op("/", q(1), op("-", T, q(pole))))
    rows, metrics, peaks = plots.point_data(selected, data, 1.0)
    main = [r for r in rows if r["grid"] == "main"]
    assert len(main) == 1024 and main[0]["prediction"] is None
    assert main[1]["prediction"] == pytest.approx(1 / (data["main_time_s"][1] - pole))
    assert metrics["main"]["relative_l2"] is None
    assert peaks["main"]["complete_grid"] is False
    assert sum(r["status"] == "not_available" for r in rows) == 1


@pytest.mark.parametrize("field", ("time_hex", "truth", "prediction_origin"))
def test_point_table_rejects_changed_reference_or_native_provenance(
    artifacts, monkeypatch, field
):
    tiny_render(monkeypatch)
    case = SimpleNamespace(spec=artifacts.specs[0])
    stem, metadata, payloads = plots._output_payload(
        artifacts.records[0], artifacts.prepared, case, source={}
    )
    rows = list(csv.DictReader(io.StringIO(payloads[stem + ".csv"].decode())))
    rows[0][field] = (
        "0x1.0p+0" if field == "time_hex" else "2.0" if field == "truth" else "new_fit"
    )
    table = plots.shared._csv(rows)
    metadata["points_csv_sha256"] = sources.sha256(table)
    with pytest.raises(ValueError):
        plots._verify_points(metadata, table, case.spec)


@pytest.mark.parametrize("late", ("during_render", "after_transaction"))
def test_late_source_change_revokes_export_and_keeps_failure_cost(
    artifacts, monkeypatch, late
):
    tiny_render(monkeypatch)
    target = artifacts.roots["inputs"] / "original.bin"
    if late == "during_render":
        original = plots._curve_plot

        def render(*args):
            target.write_bytes(b"changed source")
            return original(*args)

        monkeypatch.setattr(plots, "_curve_plot", render)
    else:
        original = publication.export_transaction

        def transaction(*args, **kwargs):
            result = original(*args, **kwargs)
            target.write_bytes(b"changed source after publication")
            return result

        monkeypatch.setattr(publication, "export_transaction", transaction)
    with pytest.raises(ValueError, match="Consumed file changed"):
        run_export(artifacts, both=False)
    assert (artifacts.output / publication.LOCK).is_file()
    assert not (artifacts.output / publication.MANIFEST).exists()
    assert (
        json.loads((artifacts.output.parent / "plots-call.json").read_bytes())["status"]
        == "aborted"
    )


@pytest.mark.parametrize("change", ("missing_slot", "duplicate_slot", "cross_signal"))
def test_invalid_scientific_inventory_never_publishes(artifacts, monkeypatch, change):
    tiny_render(monkeypatch)
    report = artifacts.reports[artifacts.signal_ids[0]]
    if change == "missing_slot":
        report["assessments"].pop()
    elif change == "duplicate_slot":
        report["assessments"].append(copy.deepcopy(report["assessments"][0]))
    else:
        report["assessments"][0]["source_identity"]["signal_id"] = artifacts.signal_ids[
            1
        ]
    with pytest.raises(ValueError):
        run_export(artifacts)
    assert not (artifacts.output / publication.MANIFEST).exists()


def test_formula_corruption_rejected_even_with_updated_payload_manifest(
    artifacts, monkeypatch
):
    tiny_render(monkeypatch)
    report = run_export(artifacts)
    payloads = {
        p.name: p.read_bytes() for p in artifacts.output.iterdir() if p.is_file()
    }
    stem = next(iter(report["outputs"]))
    payloads[stem + ".formula.txt"] = b"smoothed replacement"
    report["payload_sha256"][stem + ".formula.txt"] = sources.sha256(
        payloads[stem + ".formula.txt"]
    )
    with pytest.raises(ValueError, match="Original formula text changed"):
        plots._verify_payloads(report, payloads)


def test_real_curve_render_preserves_extreme_finite_point_in_linear_limits(
    artifacts, monkeypatch
):
    captured = {}

    def images(figure):
        captured["limits"] = [axis.get_ylim() for axis in figure.axes]
        captured["scales"] = [axis.get_yscale() for axis in figure.axes]
        return {"png": b"captured", "svg": b"captured"}

    monkeypatch.setattr(plots.shared, "_images", images)
    selected = candidate(q(1e10))
    rows, metrics, peaks = plots.point_data(selected, arrays(), 1.0)
    plots._curve_plot(
        {
            "identity": {"case_id": "case", "condition": "ordinary"},
            "status": "success",
            "technical": False,
            "metrics": metrics,
            "peaks": peaks,
        },
        rows,
        "case",
    )
    assert captured["scales"] == ["linear", "linear"]
    assert captured["limits"][0][1] > 1e10
    assert captured["limits"][1][1] > 1e10 - 1


def test_technical_export_requires_and_retains_eight_workers(artifacts, monkeypatch):
    tiny_render(monkeypatch)
    specs = [copy.deepcopy(s) for s in artifacts.specs if s["noise_model"] == "ar1"]
    for spec in specs:
        spec["id"] = spec["signal_id"] + "-technical-ar1"
        spec["search_seeds"] = [121]
    prepared = plots.inputs.PreparedInputs(
        artifacts.roots["technical"] / "inputs",
        artifacts.prepared.manifest,
        {},
        {s["id"]: s for s in specs},
    )
    members = {
        spec["id"] + "/" + arm: {
            "selected": candidate(),
            "costs": {"worker_wall_seconds": 1.0},
        }
        for spec in specs
        for arm in plots.LABELS
    }
    report = {"software": prepared.manifest["software"], "members": members}
    monkeypatch.setattr(technical, "verify", lambda *args, **kwargs: report)
    monkeypatch.setattr(plots.inputs, "verify_inputs", lambda *args, **kwargs: prepared)
    monkeypatch.setattr(
        plots.inputs,
        "read_case",
        lambda value, case_id, **kwargs: SimpleNamespace(spec=value.cases[case_id]),
    )
    monkeypatch.setattr(plots.inputs, "case_specs", lambda **kwargs: specs)
    exported = plots.export_technical(artifacts.roots["technical"], artifacts.output)
    assert exported["technical"] is True and exported["planned_outputs"] == 8
    assert plots.verify_export(artifacts.output) == exported
    assert not list(artifacts.output.glob("*-summary.json"))


def test_output_cannot_overlap_original_source(artifacts):
    with pytest.raises(ValueError):
        plots.export(
            artifacts.roots["inputs"],
            artifacts.roots["technical"],
            {artifacts.signal_ids[0]: artifacts.roots[artifacts.signal_ids[0]]},
            artifacts.roots["inputs"] / "plots",
        )


def test_signal_noise_normalizations_are_preserved_and_visible(artifacts, monkeypatch):
    tiny_render(monkeypatch)
    exported = run_export(artifacts)
    expected = {
        signal_id: report["signal_normalization"]
        for signal_id, report in artifacts.reports.items()
    }
    assert exported["signal_normalization"] == expected
    for signal_id, normalization in expected.items():
        assert exported["source"][signal_id]["signal_normalization"] == normalization
    gallery = (artifacts.output / "index.html").read_text()
    assert "σ / |A| = 0.05" in gallery
    assert "σ / RMS(s) = 0.05" in gallery
    assert "σ / RMS(s) = 0.1" in gallery
    assert "103 gleich gewichteten sauberen Werten" in gallery
    assert "kein Detektor-SNR" in gallery
    assert plots.verify_export(artifacts.output) == exported
    changed = copy.deepcopy(exported)
    changed["signal_normalization"][artifacts.signal_ids[0]]["noise_over_amplitude"] = (
        0.2
    )
    payloads = {
        path.name: path.read_bytes()
        for path in artifacts.output.iterdir()
        if path.is_file()
    }
    with pytest.raises(ValueError, match="normalization differs from its source"):
        plots._verify_payloads(changed, payloads)


def test_missing_signal_noise_normalization_cannot_publish(artifacts, monkeypatch):
    tiny_render(monkeypatch)
    artifacts.reports[artifacts.signal_ids[0]].pop("signal_normalization")
    with pytest.raises(
        ValueError, match="Missing or invalid bound signal normalization"
    ):
        run_export(artifacts, both=False)
    assert not (artifacts.output / publication.MANIFEST).exists()
