"""Audit plot numerics, exact formulas, full inventories and late revocation."""

import copy
import csv
import io
import json
import signal
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_noise_pilot_assessment import inputs as small_inputs
from test_structure_proof import T, op, q
from threadpoolctl import threadpool_limits

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_background as study
from ringdown_sr import noise_background_assessment as assessment
from ringdown_sr import noise_background_plots as plots
from ringdown_sr import noise_background_technical as technical


def candidate(arrays, *, tree=None, native=None):
    return {
        "tree": q(0.0) if tree is None else tree,
        "prediction": (
            np.zeros_like(arrays["time_s"]) if native is None else native
        ).tolist(),
        "display_equation": "(-0.0 * t) + 0.0000000000000000",
        "complexity": 1,
        "loss": 0.01,
    }


def test_point_rows_retain_native_values_and_original_tree_at_all_saved_points():
    arrays = small_inputs()
    original = candidate(arrays, native=np.ones_like(arrays["time_s"]) * 0.5)
    before = copy.deepcopy(original)
    rows, metrics, peaks = plots.point_data(original, arrays, 2.0)
    assert len(rows) == 9 + 8 + 7
    native = [row for row in rows if row["grid"] == "training"]
    replay = [row for row in rows if row["grid"] != "training"]
    assert all(row["prediction"] == 0.5 for row in native)
    assert all(row["prediction"] == 0.0 for row in replay)
    assert all(row["prediction_origin"] == "stored_native" for row in native)
    assert all(
        row["prediction_origin"] == "read_only_original_binary_tree" for row in replay
    )
    expected = np.sqrt(np.mean((0.5 - arrays["signal"]) ** 2)) / 2
    assert metrics["training"]["rms_over_amplitude"] == pytest.approx(expected)
    expected = max(abs(arrays["irregular_truth"])) / 2
    assert peaks["irregular"]["absolute_error_over_amplitude"] == pytest.approx(
        expected
    )
    for row in rows:
        assert float.fromhex(row["time_hex"]) == row["time_s"]
        assert float.fromhex(row["prediction_hex"]) == row["prediction"]
    assert original == before


def test_isolated_domain_hole_is_visible_without_deleting_other_saved_points():
    arrays = small_inputs()
    hole = float(arrays["irregular_time_s"][2])
    original = candidate(arrays, tree=op("/", q(1), op("-", T, q(hole))))
    rows, metrics, peaks = plots.point_data(original, arrays, 1.0)
    irregular = [row for row in rows if row["grid"] == "irregular"]
    assert len(irregular) == len(arrays["irregular_time_s"])
    assert irregular[2]["status"] == "not_available"
    assert irregular[2]["prediction"] is None
    assert irregular[2]["reason"] == "original_tree_prediction_nonfinite"
    assert all(
        row["status"] == "available" for i, row in enumerate(irregular) if i != 2
    )
    assert metrics["irregular"]["rms_over_amplitude"] is None
    assert peaks["irregular"]["complete_grid"] is False
    json.dumps({"rows": rows, "metrics": metrics, "peaks": peaks}, allow_nan=False)


def test_no_output_keeps_every_point_and_explicit_failure_reason():
    arrays = small_inputs()
    rows, metrics, peaks = plots.point_data(None, arrays, 1.0, reason="package_not_run")
    assert len(rows) == 24
    assert {row["reason"] for row in rows} == {"package_not_run"}
    assert all(row["prediction"] is None for row in rows)
    assert all(value["rms_over_amplitude"] is None for value in metrics.values())
    assert set(peaks.values()) == {None}


def test_invalid_tree_is_an_integrity_error_not_an_unavailable_plot_value():
    arrays = small_inputs()
    original = candidate(arrays, tree={"kind": "invalid"})
    with pytest.raises(ValueError):
        plots.point_data(original, arrays, 1.0)


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    arrays = small_inputs()
    common = {
        key: value
        for key, value in arrays.items()
        if key not in {"observed", "covariance_true"}
    }
    software = {"software_commit": "a" * 40, "source_sha256": {"fixture.py": "b" * 64}}
    cases = {}
    for spec in plots.inputs.case_specs():
        diagnoses = {
            arm: {
                "condition_number": {"estimated": {"value": 3.0}},
                "relative_frobenius_error": {"value": 0.2},
                "background_check": {
                    "estimated": {"value": {"score": -2.0}},
                    "true": {"value": {"score": -3.0}},
                },
            }
            for arm in plots.ARMS[2:]
        }
        cases[spec["id"]] = plots.inputs.PreparedCase(
            spec,
            {
                "observed": arrays["observed"],
                "covariance_true": arrays["covariance_true"],
            },
            {
                "arm_status": dict.fromkeys(plots.ARMS, "ready"),
                "covariance_estimation": {
                    arm: {"alpha_selected": 0.5} for arm in plots.ARMS[2:]
                },
                "covariance_diagnostics": diagnoses,
            },
        )
    prepared = plots.inputs.PreparedInputs({"software": software}, common, cases)
    records = []
    for spec in plots.inputs.case_specs():
        for arm in plots.ARMS:
            identity = {
                "model": spec["noise_model"],
                "block": spec["block"],
                "arm": arm,
                "package_sha256": "1" * 64,
                "input_sha256": "2" * 64,
                "selected_member_path": f"symbolic/{arm}/member-02/result.json",
            }
            value = candidate(arrays)
            package = {
                "package_status": "success",
                "selected_candidate": value,
                "costs": {
                    "worker_wall_seconds": None if spec["block"] == 1 else 10.0,
                    "callback_calls_during_fit": 111,
                },
                "search_calls": 4,
            }
            records.append(
                assessment.assess_package(
                    package,
                    arrays,
                    amplitude=plots.inputs.SIGNAL["amplitude"],
                    source_identity=identity,
                )
            )
    # One unavailable original remains a planned output and contrast denominator.
    failed = records[0]
    failed["status"] = "failed"
    failed["original_candidate"] = None
    failed["source_identity"]["selected_member_path"] = None
    failed["primary"] = {
        "status": "not_available",
        "reason": "package_failed",
        "value": None,
    }
    report = {
        "software": software,
        "assessments": records,
        "summary": assessment.summary(records),
    }
    preparation, technical_path, series = (
        tmp_path / name for name in ("inputs", "technical", "series")
    )
    for path in (preparation, technical_path, series):
        (path / "completion").mkdir(parents=True)
        (path / "completion" / publication.REPORT).write_bytes(
            sources.json_bytes({"source": path.name})
        )
        (path / "original.bin").write_bytes(b"unchanged original")
    for path in (preparation, series):
        path.with_name(path.name + "-call.json").write_bytes(b"{}\n")
    calls = []

    def verify(
        preparation_arg, technical_arg, series_arg, *, consumed=None, export=None
    ):
        assert consumed is not None
        assert (preparation_arg, technical_arg, series_arg) == (
            preparation,
            technical_path,
            series,
        )
        assert export is None
        calls.append("full_read_only_verify")
        consumed.check()
        return report

    monkeypatch.setattr(study, "verify", verify)
    monkeypatch.setattr(
        plots.inputs, "verify_inputs", lambda path, consumed=None: prepared
    )
    return SimpleNamespace(
        prepared=prepared,
        report=report,
        preparation=preparation,
        technical=technical_path,
        series=series,
        output=tmp_path / "plots",
        calls=calls,
    )


def _tiny_render(monkeypatch):
    monkeypatch.setattr(
        plots,
        "_curve_plot",
        lambda metadata, rows, stem: {"png": b"PNG fixture", "svg": b"SVG fixture"},
    )
    monkeypatch.setattr(
        plots,
        "_overview_payloads",
        lambda report, prepared: {
            **{
                f"{model}-{kind}.{ext}": b"Overview fixture"
                for model in ("ar1", "white")
                for kind in ("errors-contrasts", "costs-failures", "covariance")
                for ext in ("csv", "png", "svg")
            },
            **{
                f"{model}-errors-contrasts.json": sources.json_bytes(report["summary"])
                for model in ("ar1", "white")
            },
        },
    )


def test_full_export_keeps_130_slots_exact_formula_seed_binding_and_original_bytes(
    artifacts, monkeypatch
):
    _tiny_render(monkeypatch)
    original = {
        path: path.read_bytes()
        for root in (artifacts.preparation, artifacts.technical, artifacts.series)
        for path in root.rglob("*")
        if path.is_file()
    }
    report = plots.export(
        artifacts.preparation, artifacts.technical, artifacts.series, artifacts.output
    )
    assert report["planned_outputs"] == len(report["outputs"]) == 130
    assert report["fits_or_searches_executed"] is False
    assert artifacts.calls == ["full_read_only_verify"]
    assert all(path.read_bytes() == raw for path, raw in original.items())
    stem = "ar1-01-estimated_1024"
    metadata = json.loads((artifacts.output / (stem + ".json")).read_bytes())
    assert metadata["identity"]["member_position"] == 2
    assert (
        metadata["identity"]["seed"]
        == artifacts.prepared.cases["ar1-01"].spec["search_seeds"][1]
    )
    assert metadata["background_training_windows"] == 1024
    assert (artifacts.output / (stem + ".formula.txt")).read_text() == metadata[
        "candidate"
    ]["display_equation"]
    assert metadata["candidate"]["tree"] == q(0.0)
    rows = list(
        csv.DictReader(io.StringIO((artifacts.output / (stem + ".csv")).read_text()))
    )
    assert len(rows) == metadata["point_count"] == 24
    failed = json.loads((artifacts.output / "ar1-01-ordinary.json").read_bytes())
    assert failed["status"] == "failed" and failed["candidate"] is None
    manifest = json.loads((artifacts.output / publication.MANIFEST).read_bytes())
    assert manifest == {
        path.name: sources.sha256(path.read_bytes())
        for path in artifacts.output.iterdir()
        if path.name != publication.MANIFEST
    }
    assert not (artifacts.output / publication.LOCK).exists()


@pytest.mark.parametrize("late", ["during_render", "after_unlock", "after_transaction"])
def test_late_source_changes_revoke_the_entire_plot_release(
    artifacts, monkeypatch, late
):
    _tiny_render(monkeypatch)
    target = artifacts.series / "original.bin"
    if late == "during_render":
        original = plots._curve_plot

        def render(*args):
            target.write_bytes(b"changed during drawing")
            return original(*args)

        monkeypatch.setattr(plots, "_curve_plot", render)
    elif late == "after_unlock":
        original = Path.unlink

        def unlink(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == artifacts.output / publication.LOCK:
                target.write_bytes(b"changed after unlock")
            return result

        monkeypatch.setattr(Path, "unlink", unlink)
    else:
        original = publication.export_transaction

        def transaction(*args, **kwargs):
            result = original(*args, **kwargs)
            target.write_bytes(b"changed after transaction returned")
            return result

        monkeypatch.setattr(publication, "export_transaction", transaction)
    with pytest.raises(ValueError, match="Consumed file changed"):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
        )
    assert (artifacts.output / publication.LOCK).is_file()
    assert (
        json.loads((artifacts.output / publication.REPORT).read_bytes())["status"]
        == "failed"
    )
    assert not (artifacts.output / publication.MANIFEST).exists()


def test_interruption_after_unlock_revokes_plot_aggregates(artifacts, monkeypatch):
    _tiny_render(monkeypatch)
    original = Path.unlink

    def unlink(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path == artifacts.output / publication.LOCK:
            signal.raise_signal(signal.SIGINT)
        return result

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises(InterruptedError):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
        )
    assert (artifacts.output / publication.LOCK).is_file()
    assert not (artifacts.output / publication.MANIFEST).exists()


def test_output_never_overlaps_originals_even_before_reservation(artifacts):
    path = artifacts.preparation / "new-plots"
    with pytest.raises(ValueError, match="overlap"):
        plots.export(artifacts.preparation, artifacts.technical, artifacts.series, path)
    assert not path.exists()


def test_member_binding_rejects_cross_arm_paths(artifacts, monkeypatch):
    _tiny_render(monkeypatch)
    artifacts.report["assessments"][1]["source_identity"]["selected_member_path"] = (
        "symbolic/ordinary/member-02/result.json"
    )
    with pytest.raises(ValueError, match="bound to its arm"):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
        )
    assert (artifacts.output / publication.LOCK).exists()


def test_actual_renderers_produce_plots_and_auditable_overviews(artifacts):
    record = artifacts.report["assessments"][1]
    case = artifacts.prepared.cases["ar1-01"]
    stem, metadata, payloads = plots._output_payload(
        record,
        artifacts.prepared,
        case,
        technical=False,
        series_identity={"run_id": "synthetic"},
    )
    assert payloads[stem + ".png"].startswith(b"\x89PNG")
    assert b"<svg" in payloads[stem + ".svg"]
    assert metadata["peaks"]["irregular"]["complete_grid"] is True
    overviews = plots._overview_payloads(artifacts.report, artifacts.prepared)
    for model in ("ar1", "white"):
        assert overviews[model + "-errors-contrasts.png"].startswith(b"\x89PNG")
        assert b"<svg" in overviews[model + "-covariance.svg"]
        rows = list(
            csv.DictReader(
                io.StringIO(overviews[model + "-costs-failures.csv"].decode())
            )
        )
        unknown = [row for row in rows if row["block"] == "1"]
        assert len(unknown) == 5
        assert all(
            row["worker_wall_seconds"] == "" and row["cost_status"] == "unknown"
            for row in unknown
        )


def test_covariance_overview_uses_real_held_out_scores_and_preserves_missing_values(
    artifacts,
):
    expected = {}
    original_records = {}
    with threadpool_limits(limits=1):
        common, _ = plots.inputs.derive_common_inputs()
        for model in ("ar1", "white"):
            case_id = f"{model}-01"
            spec = artifacts.prepared.cases[case_id].spec
            case = plots.inputs.derive_case(spec, common)
            artifacts.prepared.cases[case_id] = case
            original_records[case_id] = copy.deepcopy(case.record)
            windows = case.arrays["background_check"]

            def independent_score(matrix, windows):
                sign, logdet = np.linalg.slogdet(matrix)
                assert sign == 1
                whitened = np.linalg.solve(matrix, windows.T).T
                return logdet + np.mean(np.sum(windows * whitened, axis=1))

            expected[model] = {
                "true": independent_score(case.arrays["covariance_true"], windows)
            }
            for arm in plots.ARMS[2:]:
                size = arm.removeprefix("estimated_")
                expected[model][arm] = independent_score(
                    case.arrays[f"covariance_estimated_{size}"], windows
                )

            # Exercise the production unavailable records as well as ready values.
            failed = artifacts.prepared.cases[f"{model}-02"].record
            failed["arm_status"]["estimated_64"] = "not_run"
            failed["covariance_estimation"]["estimated_64"] = {"alpha_selected": None}
            failed["covariance_diagnostics"] = plots.inputs.covariance_diagnostics(
                case.arrays, failed["arm_status"], "covariance_failed"
            )
            missing = artifacts.prepared.cases[f"{model}-03"].record
            missing["arm_status"] = dict.fromkeys(plots.ARMS, "not_run")
            missing["covariance_estimation"] = dict.fromkeys(plots.ARMS[2:])
            missing["covariance_diagnostics"] = plots.inputs.covariance_diagnostics(
                {}, missing["arm_status"], "data_failed"
            )

    overviews = plots._overview_payloads(artifacts.report, artifacts.prepared)
    for model, blocks in (("ar1", 20), ("white", 6)):
        assert overviews[f"{model}-covariance.png"].startswith(b"\x89PNG")
        assert b"<svg" in overviews[f"{model}-covariance.svg"]
        rows = list(
            csv.DictReader(io.StringIO(overviews[f"{model}-covariance.csv"].decode()))
        )
        assert len(rows) == 3 * blocks
        for row in rows:
            if row["block"] == "1":
                assert float(row["check_score"]) == pytest.approx(
                    expected[model][row["arm"]], rel=1e-12
                )
                assert float(row["true_check_score"]) == pytest.approx(
                    expected[model]["true"], rel=1e-12
                )
            elif row["block"] == "2" and row["arm"] == "estimated_64":
                assert row["status"] == "not_run"
                assert row["alpha"] == row["check_score"] == ""
                assert float(row["true_check_score"]) == pytest.approx(
                    expected[model]["true"], rel=1e-12
                )
            elif row["block"] == "3":
                assert row["status"] == "not_run"
                assert row["alpha"] == row["check_score"] == ""
                assert row["true_check_score"] == ""
        assert (
            artifacts.prepared.cases[f"{model}-01"].record
            == original_records[f"{model}-01"]
        )


def test_technical_export_uses_all_five_original_workers_without_quality_selection(
    artifacts, monkeypatch
):
    _tiny_render(monkeypatch)
    spec = plots.inputs.case_specs(technical=True)[0]
    base = artifacts.prepared.cases["ar1-01"]
    case = plots.inputs.PreparedCase(spec, base.arrays, base.record)
    prepared = plots.inputs.PreparedInputs(
        artifacts.prepared.manifest, artifacts.prepared.common, {"technical-ar1": case}
    )
    report = {
        "software": prepared.manifest["software"],
        "members": {
            arm: {
                "selected": candidate({**prepared.common, **case.arrays}),
                "seed": spec["search_seeds"][0],
                "costs": {"worker_wall_seconds": 2.0},
            }
            for arm in plots.ARMS
        },
    }
    calls = []

    def verify(path, consumed=None):
        assert path == artifacts.technical and consumed is not None
        calls.append("technical_read_only_verify")
        return report

    monkeypatch.setattr(technical, "verify", verify)
    monkeypatch.setattr(
        plots.inputs, "verify_inputs", lambda path, consumed=None: prepared
    )
    exported = plots.export_technical(artifacts.technical, artifacts.output)
    assert exported["planned_outputs"] == len(exported["outputs"]) == 5
    assert exported["scientific_success_assessed"] is False
    assert plots.verify_export(artifacts.output) == exported
    assert calls == ["technical_read_only_verify"]
    assert all(
        value["identity"]["seed"] == spec["search_seeds"][0]
        for value in exported["outputs"].values()
    )


def test_export_cost_sidecar_is_real_separate_and_read_only_verifiable(
    artifacts, monkeypatch
):
    _tiny_render(monkeypatch)
    exported = plots.export(
        artifacts.preparation, artifacts.technical, artifacts.series, artifacts.output
    )
    timing = plots._timing_path(artifacts.output)
    record = json.loads(timing.read_bytes())
    assert record["status"] == "completed"
    assert record["wall_seconds"] > 0
    assert record["cpu_user_seconds"] >= 0
    assert record["cpu_system_seconds"] >= 0
    assert record["measurement_scope"] == plots.TIMING_SCOPE
    assert record["source_report_sha256"] == sources.sha256(
        (artifacts.output / publication.REPORT).read_bytes()
    )
    before = {path: path.read_bytes() for path in artifacts.output.iterdir()}
    before[timing] = timing.read_bytes()
    assert plots.verify_export(artifacts.output) == exported
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_preexisting_timing_sidecar_is_not_overwritten_or_reserved(
    artifacts, monkeypatch
):
    _tiny_render(monkeypatch)
    timing = plots._timing_path(artifacts.output)
    timing.write_bytes(b"original partial cost evidence")
    with pytest.raises(ValueError, match="new assessment directory"):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
        )
    assert not artifacts.output.exists()
    assert timing.read_bytes() == b"original partial cost evidence"
    assert artifacts.calls == []


@pytest.mark.parametrize("mutation", ["cost_inflation", "source_change", "interrupt"])
def test_timing_write_changes_revoke_the_export_and_retain_aborted_costs(
    artifacts, monkeypatch, mutation
):
    _tiny_render(monkeypatch)
    original = Path.write_bytes
    timing = plots._timing_path(artifacts.output)

    def write(path, raw):
        completed = path == timing and json.loads(raw)["status"] == "completed"
        if completed and mutation == "cost_inflation":
            changed = json.loads(raw)
            changed["wall_seconds"] += 1
            return original(path, sources.json_bytes(changed))
        result = original(path, raw)
        if completed and mutation == "source_change":
            (artifacts.series / "original.bin").write_bytes(
                b"source changed during cost write"
            )
        if completed and mutation == "interrupt":
            raise KeyboardInterrupt("interrupted after plot timing write")
        return result

    monkeypatch.setattr(Path, "write_bytes", write)
    with pytest.raises((ValueError, KeyboardInterrupt)):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
        )
    assert (artifacts.output / publication.LOCK).is_file()
    assert not (artifacts.output / publication.MANIFEST).exists()
    partial = json.loads(timing.read_bytes())
    assert partial["status"] == "aborted"
    assert partial["error"]
    assert partial["wall_seconds"] >= 0
    assert partial["cpu_user_seconds"] >= 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("wall_seconds", -1.0),
        ("cpu_system_seconds", True),
        ("wall_seconds", 14400),
        ("source_report_sha256", "0" * 64),
        ("finished_at_utc", "bad date"),
    ],
)
def test_plot_cost_verification_rejects_invalid_values_or_binding(
    artifacts, monkeypatch, field, value
):
    _tiny_render(monkeypatch)
    plots.export(
        artifacts.preparation, artifacts.technical, artifacts.series, artifacts.output
    )
    timing = plots._timing_path(artifacts.output)
    record = json.loads(timing.read_bytes())
    record[field] = value
    timing.write_bytes(sources.json_bytes(record))
    with pytest.raises(ValueError):
        plots.verify_export(artifacts.output)


@pytest.mark.parametrize(
    "mutation",
    [
        "remove_csv",
        "remove_png",
        "remove_overview",
        "metadata_seed",
        "csv",
        "formula",
        "overview",
        "image",
    ],
)
def test_resealed_manifest_cannot_replace_report_bound_plot_payloads(
    artifacts, monkeypatch, mutation
):
    _tiny_render(monkeypatch)
    plots.export(
        artifacts.preparation, artifacts.technical, artifacts.series, artifacts.output
    )
    manifest_path = artifacts.output / publication.MANIFEST
    manifest = json.loads(manifest_path.read_bytes())
    stem = "ar1-01-estimated_1024"
    if mutation.startswith("remove_"):
        name = {
            "remove_csv": stem + ".csv",
            "remove_png": stem + ".png",
            "remove_overview": "white-errors-contrasts.json",
        }[mutation]
        (artifacts.output / name).unlink()
        del manifest[name]
    else:
        name = {
            "metadata_seed": stem + ".json",
            "csv": stem + ".csv",
            "formula": stem + ".formula.txt",
            "overview": "ar1-costs-failures.csv",
            "image": stem + ".png",
        }[mutation]
        path = artifacts.output / name
        if mutation == "metadata_seed":
            value = json.loads(path.read_bytes())
            value["identity"]["seed"] += 1
            path.write_bytes(sources.json_bytes(value))
        else:
            path.write_bytes(path.read_bytes() + b"changed")
        manifest[name] = sources.sha256(path.read_bytes())
    manifest_path.write_bytes(sources.json_bytes(manifest))
    with pytest.raises(ValueError):
        plots.verify_export(artifacts.output)
