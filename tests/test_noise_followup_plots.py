"""Audit original follow-up plots, shared controls and fail-closed publication."""

import copy
import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_noise_followup_assessment import arrays, identity, package
from test_structure_proof import T, op, q

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_followup as study
from ringdown_sr import noise_followup_assessment as assessment
from ringdown_sr import noise_followup_plots as plots
from ringdown_sr import noise_followup_technical as technical


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    software = {"software_commit": "a" * 40, "source_sha256": {"fixture": "b" * 64}}
    roots = {
        name: tmp_path / name
        for name in ("inputs", "technical", "duration", "sampling", "diagnostics")
    }
    for root in roots.values():
        (root / "completion").mkdir(parents=True)
        (root / "completion" / publication.REPORT).write_bytes(
            sources.json_bytes({"fixture_source": root.name})
        )
        (root / "original.bin").write_bytes(b"unchanged original")
    cases = {spec["id"]: spec for spec in plots.inputs.case_specs()}
    prepared = plots.inputs.PreparedInputs(
        roots["inputs"], {"software": software}, {}, cases
    )
    records = []
    for spec in cases.values():
        for condition in plots.LABELS:
            data = arrays(jitter=condition.startswith("jitter_"))
            failed = spec["id"] == "ar1-01" and condition == "ordinary"
            original = package(data, status="failed" if failed else "success")
            binding = identity(
                condition,
                model=spec["noise_model"],
                block=spec["block"],
                status="failed" if failed else "success",
            )
            if not failed:
                binding["selected_member_path"] = (
                    f"symbolic/{condition}/member-02/result.json"
                )
            records.append(
                assessment.assess_package(
                    original, data, amplitude=2.0, source_identity=binding
                )
            )
    reports = {}
    for block in ("duration", "sampling"):
        selected = [
            r
            for r in records
            if r["source_identity"]["condition"] in plots._conditions(block)
        ]
        reports[block] = {
            "block": block,
            "software": software,
            "preparation_sha256": "3" * 64,
            "technical_report_sha256": "4" * 64,
            "assessments": selected,
            "summary": assessment.summary(selected, block=block),
            "control_references": {"fixture": {"package_sha256": "1" * 64}}
            if block == "sampling"
            else {},
        }
    calls = []

    def verify(preparation, technical_path, series, **kwargs):
        assert preparation == roots["inputs"]
        assert technical_path == roots["technical"]
        assert kwargs["diagnostics"] == roots["diagnostics"]
        block = kwargs["block"]
        assert series == roots[block]
        assert kwargs["uniform"] == (roots["duration"] if block == "sampling" else None)
        assert kwargs.get("export") is None
        consumed = kwargs["consumed"]
        for root in roots.values():
            path = root / "original.bin"
            consumed.add(path, path.read_bytes())
        calls.append(("verify", block))
        return reports[block]

    def verify_inputs(path, consumed=None, *, regenerate=False):
        assert path == roots["inputs"]
        assert consumed is not None and regenerate is False
        calls.append(("inputs",))
        return prepared

    def read_case(value, case_id, consumed=None, *, regenerate=False):
        assert value is prepared and consumed is not None and regenerate is False
        calls.append(("case", case_id))
        return SimpleNamespace(spec=cases[case_id])

    monkeypatch.setattr(study, "verify", verify)
    monkeypatch.setattr(plots.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(plots.inputs, "read_case", read_case)
    monkeypatch.setattr(
        plots.inputs,
        "arm_arrays",
        lambda prepared, case, condition: arrays(
            jitter=condition.startswith("jitter_")
        ),
    )
    return SimpleNamespace(
        roots=roots,
        prepared=prepared,
        reports=reports,
        records=records,
        calls=calls,
        output=tmp_path / "plots",
    )


def _tiny_render(monkeypatch):
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


def _export(artifacts, block="sampling"):
    roots = artifacts.roots
    return plots.export(
        roots["inputs"],
        roots["technical"],
        roots[block],
        artifacts.output,
        diagnostics=roots["diagnostics"],
        block=block,
        uniform=roots["duration"] if block == "sampling" else None,
    )


def _read(root, name):
    return json.loads((root / name).read_bytes())


@pytest.mark.parametrize("block", ("duration", "sampling"))
def test_full_blocks_keep_original_data_and_costed_control_references(
    artifacts, monkeypatch, block
):
    _tiny_render(monkeypatch)
    before = {
        path: path.read_bytes()
        for root in artifacts.roots.values()
        for path in root.rglob("*")
        if path.is_file()
    }
    report = _export(artifacts, block)
    assert report["planned_outputs"] == len(report["outputs"]) == 104
    assert report["referenced_outputs"] == (52 if block == "sampling" else 0)
    assert report["new_outputs"] == (52 if block == "sampling" else 104)
    assert report["fits_or_searches_executed"] is report["selection_changed"] is False
    assert plots.verify_export(artifacts.output) == report
    assert artifacts.calls.count(("verify", block)) == 1
    assert artifacts.calls.count(("inputs",)) == 1
    assert len([call for call in artifacts.calls if call[0] == "case"]) == 26
    assert all(path.read_bytes() == raw for path, raw in before.items())
    condition = "jitter_known_covariance" if block == "sampling" else "estimated_4096s"
    stem = "ar1-01-" + condition
    metadata = _read(artifacts.output, stem + ".json")
    assert metadata["identity"]["member_position"] == 2
    assert (
        metadata["identity"]["seed"]
        == artifacts.prepared.cases["ar1-01"]["search_seeds"][1]
    )
    assert metadata["candidate"]["tree"] == q(0.125)
    assert (artifacts.output / (stem + ".formula.txt")).read_text() == (
        metadata["candidate"]["display_equation"]
    )
    rows = list(
        csv.DictReader(io.StringIO((artifacts.output / (stem + ".csv")).read_text()))
    )
    assert len(rows) == metadata["point_count"] == 24
    training = [row for row in rows if row["grid"] == "training"]
    heldout = [row for row in rows if row["grid"] == "irregular"]
    expected = arrays(jitter=block == "sampling")
    assert [float(row["time_s"]) for row in training] == expected["time_s"].tolist()
    assert {float(row["prediction"]) for row in training} == {0.5}
    assert [float(row["time_s"]) for row in heldout] == expected[
        "irregular_time_s"
    ].tolist()
    assert {float(row["prediction"]) for row in heldout} == {0.125}
    failed = _read(artifacts.output, "ar1-01-ordinary.json")
    assert failed["candidate"] is None and failed["reason"] == "package_failed"
    assert failed["referenced_control"] is (block == "sampling")
    costs = list(
        csv.DictReader(io.StringIO((artifacts.output / "ar1-overview.csv").read_text()))
    )
    original_calls = sum(int(row["original_search_calls"]) for row in costs)
    new_calls = sum(int(row["new_search_calls"]) for row in costs)
    assert original_calls == 320
    assert new_calls == (160 if block == "sampling" else 320)
    contrasts = _read(artifacts.output, "ar1-contrasts.json")
    assert len(contrasts) == (4 if block == "sampling" else 6)
    assert not (artifacts.output / publication.LOCK).exists()


def test_domain_hole_and_failed_outputs_keep_all_points(artifacts, monkeypatch):
    _tiny_render(monkeypatch)
    data = arrays(jitter=True)
    tree = op("/", q(1), op("-", T, q(float(data["irregular_time_s"][2]))))
    record = assessment.assess_package(
        package(data, tree=tree),
        data,
        amplitude=2.0,
        source_identity=identity("jitter_ordinary"),
    )
    stem, metadata, payloads = plots._output_payload(
        record,
        artifacts.prepared,
        SimpleNamespace(spec=artifacts.prepared.cases["ar1-01"]),
        source={"fixture": True},
        block="sampling",
    )
    rows = list(csv.DictReader(io.StringIO(payloads[stem + ".csv"].decode())))
    missing = [row for row in rows if row["status"] == "not_available"]
    assert len(rows) == 24 and len(missing) == 1
    assert missing[0]["grid"] == "irregular"
    assert missing[0]["reason"] == "original_tree_prediction_nonfinite"
    assert metadata["metrics"]["irregular"]["rms_over_amplitude"] is None
    assert metadata["peaks"]["irregular"]["complete_grid"] is False


@pytest.mark.parametrize("late", ("during_render", "after_transaction"))
def test_late_source_mutation_revokes_release(artifacts, monkeypatch, late):
    _tiny_render(monkeypatch)
    target = artifacts.roots["duration"] / "original.bin"
    if late == "during_render":
        original = plots._curve_plot

        def render(*args):
            target.write_bytes(b"changed shared control")
            return original(*args)

        monkeypatch.setattr(plots, "_curve_plot", render)
    else:
        original = publication.export_transaction

        def transaction(*args, **kwargs):
            result = original(*args, **kwargs)
            target.write_bytes(b"changed after publication")
            return result

        monkeypatch.setattr(publication, "export_transaction", transaction)
    with pytest.raises(ValueError, match="Consumed file changed"):
        _export(artifacts)
    assert (artifacts.output / publication.LOCK).is_file()
    assert _read(artifacts.output, publication.REPORT)["status"] == "failed"
    assert not (artifacts.output / publication.MANIFEST).exists()
    assert _read(artifacts.output.parent, "plots-call.json")["status"] == "aborted"


@pytest.mark.parametrize("kind", ("formula", "reference", "csv", "html", "cost"))
def test_saved_export_rejects_resealed_payload_or_cost_tampering(
    artifacts, monkeypatch, kind
):
    _tiny_render(monkeypatch)
    _export(artifacts)
    stem = "ar1-01-known_covariance"
    if kind == "formula":
        (artifacts.output / (stem + ".formula.txt")).write_text("replacement formula")
    elif kind == "reference":
        path = artifacts.output / (stem + ".json")
        data = _read(artifacts.output, path.name)
        data["referenced_control"] = False
        path.write_bytes(sources.json_bytes(data))
    elif kind == "csv":
        path = artifacts.output / (stem + ".csv")
        path.write_text(path.read_text().replace("stored_native", "replacement"))
    elif kind == "html":
        (artifacts.output / "index.html").write_text("missing original formulas")
    else:
        path = plots._timing_path(artifacts.output)
        value = json.loads(path.read_bytes())
        value["source_report_sha256"] = "0" * 64
        path.write_bytes(sources.json_bytes(value))
    if kind != "cost":
        # Reseal the report and cost binding too: semantic original-data checks
        # must catch these inconsistencies, not merely a stale outer checksum.
        report = _read(artifacts.output, publication.REPORT)
        for name in report["payload_sha256"]:
            report["payload_sha256"][name] = sources.sha256(
                (artifacts.output / name).read_bytes()
            )
        report["outputs"][stem]["metadata_sha256"] = sources.sha256(
            (artifacts.output / (stem + ".json")).read_bytes()
        )
        raw = sources.json_bytes(report)
        (artifacts.output / publication.REPORT).write_bytes(raw)
        timing = plots._timing_path(artifacts.output)
        call = json.loads(timing.read_bytes())
        call["source_report_sha256"] = sources.sha256(raw)
        timing.write_bytes(sources.json_bytes(call))
    manifest = {
        path.name: sources.sha256(path.read_bytes())
        for path in artifacts.output.iterdir()
        if path.name != publication.MANIFEST
    }
    (artifacts.output / publication.MANIFEST).write_bytes(sources.json_bytes(manifest))
    with pytest.raises(
        ValueError,
        match="Original formula|reference-control|point table|gallery differs|Unbound or incomplete",
    ):
        plots.verify_export(artifacts.output)


def test_originals_and_gate_directories_cannot_be_plot_destinations(artifacts):
    artifacts.output = artifacts.roots["diagnostics"] / "plots"
    with pytest.raises(ValueError, match="overlap"):
        _export(artifacts)
    assert not artifacts.output.exists()


@pytest.mark.parametrize("name", (publication.MANIFEST, "index.html"))
def test_export_symlinks_are_rejected_before_reading_the_target(
    artifacts, monkeypatch, name
):
    _tiny_render(monkeypatch)
    _export(artifacts)
    path = artifacts.output / name
    target = artifacts.output.parent / "external.txt"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)
    original = Path.read_bytes

    def read(value):
        if value == path:
            raise AssertionError("Symlink target must not be consumed.")
        return original(value)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="without symlinks"):
        plots.verify_export(artifacts.output)


def test_cross_condition_selection_is_rejected(artifacts, monkeypatch):
    _tiny_render(monkeypatch)
    record = artifacts.reports["sampling"]["assessments"][1]
    record["source_identity"]["selected_member_path"] = (
        "symbolic/ordinary/member-02/result.json"
    )
    with pytest.raises(ValueError, match="bound to its condition"):
        _export(artifacts)


def test_actual_renderers_include_dynamic_contrasts_unknown_costs_and_jitter(artifacts):
    record = artifacts.reports["sampling"]["assessments"][2]
    stem, metadata, payloads = plots._output_payload(
        record,
        artifacts.prepared,
        SimpleNamespace(spec=artifacts.prepared.cases["ar1-01"]),
        source={"fixture": True},
        block="sampling",
    )
    assert payloads[stem + ".png"].startswith(b"\x89PNG")
    assert b"<svg" in payloads[stem + ".svg"]
    assert metadata["identity"]["grid"] == "jitter"
    overviews = plots._overview_payloads(artifacts.reports["sampling"], "sampling")
    for model in ("ar1", "white"):
        assert overviews[model + "-overview.png"].startswith(b"\x89PNG")
        assert b"<svg" in overviews[model + "-contrasts.svg"]
        assert len(json.loads(overviews[model + "-contrasts.json"])) == 4


def test_technical_export_keeps_all_six_original_workers(artifacts, monkeypatch):
    _tiny_render(monkeypatch)
    spec = plots.inputs.case_specs(technical=True)[0]
    case = SimpleNamespace(spec=spec)
    prepared = plots.inputs.PreparedInputs(
        artifacts.roots["technical"] / "inputs",
        artifacts.prepared.manifest,
        {},
        {spec["id"]: spec},
    )
    report = {
        "software": artifacts.prepared.manifest["software"],
        "members": {
            condition: {
                "selected": package(arrays())["selected_candidate"],
                "costs": {"worker_wall_seconds": 0.1},
            }
            for condition in plots.LABELS
        },
    }
    original = copy.deepcopy(report)
    calls = []

    def verify(path, consumed=None):
        assert path == artifacts.roots["technical"] and consumed is not None
        calls.append("verify")
        return report

    monkeypatch.setattr(technical, "verify", verify)
    monkeypatch.setattr(plots.inputs, "verify_inputs", lambda *args, **kwargs: prepared)
    monkeypatch.setattr(plots.inputs, "read_case", lambda *args, **kwargs: case)
    result = plots.export_technical(artifacts.roots["technical"], artifacts.output)
    assert result["planned_outputs"] == result["new_outputs"] == 6
    assert result["referenced_outputs"] == 0 and result["technical"] is True
    assert calls == ["verify"] and report == original
    assert plots.verify_export(artifacts.output) == result
    for condition in plots.LABELS:
        value = _read(artifacts.output, spec["id"] + "-" + condition + ".json")
        assert value["scientific_success_assessed"] is False
        assert value["identity"]["seed"] == spec["search_seeds"][0]
        assert value["candidate"] == original["members"][condition]["selected"]
