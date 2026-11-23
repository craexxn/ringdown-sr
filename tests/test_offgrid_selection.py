"""Check observation-only selection, independent references and publication integrity."""

import copy
import io
import math

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import offgrid_selection as selection
from ringdown_sr.signals import ringdown_signal


def constant(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


def operator(name, *children):
    names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


def item(identity, tree, complexity):
    return {"id": identity, "tree": tree, "complexity": complexity}


def test_selector_uses_only_noisy_observations_and_stable_ties():
    pool = [item("b", constant(2), 1), item("a", constant(0), 1)]
    before = copy.deepcopy(pool)
    result = selection.select(pool, [0, 1], [1, 1])
    assert result["selected_id"] == "a"
    assert [row["mse"] for row in result["scores"]] == [1, 1]
    assert selection.select(pool, [0, 1], [2, 2])["selected_id"] == "b"
    assert pool == before
    with pytest.raises(ValueError, match="accepts only"):
        selection.select([{**pool[0], "truth": [2, 2]}], [0, 1], [1, 1])
    with pytest.raises(TypeError):
        selection.select(pool, [0, 1], [1, 1], truth=[2, 2])


def test_same_complexity_good_formula_remains_eligible():
    pool = [
        item("bad", operator("+", constant(9), constant(2)), 3),
        item("good", operator("+", constant(1), constant(2)), 3),
    ]
    assert selection.select(pool, [0, 1], [3, 3])["selected_id"] == "good"
    pool[1]["complexity"] = 2
    with pytest.raises(ValueError, match="complexity differs"):
        selection.select(pool, [0, 1], [3, 3])


def test_nonfinite_predictions_and_scores_abstain_without_fallback():
    tree = operator("/", constant(1), {"kind": "variable", "index": 1})
    result = selection.select([item("pole", tree, 3)], [0, 1], [0, 1])
    assert result["status"] == "abstained"
    assert result["selected_id"] is None
    assert result["scores"][0]["mse"] is None
    huge = selection.select(
        [item("overflow", constant(1e308), 1)], [0, 1], [-1e308, -1e308]
    )
    assert huge["status"] == "abstained"
    assert selection._mse(np.array([1e154, -1e154])) == pytest.approx(1e308)


def test_exact_uniform_alias_reference_is_separated_by_new_measurements():
    # cos(2*pi*2*t) and cos(2*pi*10*t) agree at an 8-Hz raster.
    variable = {"kind": "variable", "index": 1}
    pool = [
        item(
            name, operator("cos", operator("*", constant(2 * math.pi * f), variable)), 4
        )
        for name, f in (("low", 2), ("alias", 10))
    ]
    uniform = np.arange(8) / 8
    observed = np.cos(2 * math.pi * 2 * uniform)
    scores = selection.select(pool, uniform, observed)["scores"]
    assert max(row["mse"] for row in scores) < 1e-28
    off_grid = (np.arange(8) + 0.37) / 8
    result = selection.select(pool, off_grid, np.cos(2 * math.pi * 2 * off_grid))
    assert result["selected_id"] == "low"
    assert result["scores"][1]["mse"] > 0.1


def common_fixture():
    axes = {
        "time_s": np.arange(8) / 4096,
        "jitter_time_s": (
            np.arange(8) + np.array([0, 0.1, -0.1, 0.2, -0.2, 0.1, -0.1, 0])
        )
        / 4096,
        "diagnostic_time_s": (np.arange(7) + 0.5) / 4096,
        "irregular_time_s": (np.arange(9) + 0.23) / 9 * (7 / 4096),
    }
    for times, truth in (
        ("time_s", "signal"),
        ("jitter_time_s", "jitter_signal"),
        ("diagnostic_time_s", "diagnostic_truth"),
        ("irregular_time_s", "irregular_truth"),
    ):
        axes[truth] = ringdown_signal(axes[times], **selection.original.SIGNAL)
    return axes


@pytest.mark.parametrize("case", ["ar1-01", "white-01"])
def test_validation_rng_matches_independent_white_or_ou_reference(case):
    common = common_fixture()
    grid = selection.validation_grid(common)
    values, record = selection.validation_observations(case, common, grid)
    union = np.array(record["union_time_s"])
    z = np.random.Generator(
        np.random.PCG64(selection.CASE_SEEDS[case])
    ).standard_normal(len(union))
    expected = selection.original.SIGMA * z
    if case.startswith("ar1"):
        for index in range(1, len(union)):
            correlation = 0.65 ** (4096 * (union[index] - union[index - 1]))
            expected[index] = (
                correlation * expected[index - 1]
                + selection.original.SIGMA * np.sqrt(1 - correlation**2) * z[index]
            )
    np.testing.assert_allclose(record["union_noise"], expected, rtol=5e-14, atol=1e-16)
    assert values["uniform"][0] == values["jitter"][0]
    assert values["uniform"][-1] == values["jitter"][-1]
    again, repeated = selection.validation_observations(case, common, grid)
    assert repeated == record
    np.testing.assert_array_equal(again["off_grid"], values["off_grid"])
    assert record["truth_reference_max_absolute_error_over_amplitude"] < 1e-13


def test_validation_grid_rejects_collision_without_a_replacement_draw():
    common = common_fixture()
    common["irregular_time_s"] = selection.validation_grid(common)
    with pytest.raises(ValueError, match="collides"):
        selection.validation_grid(common)


def _npz(arrays):
    stream = io.BytesIO()
    np.savez(stream, **arrays)
    return stream.getvalue()


@pytest.fixture
def archive_fixture(tmp_path, monkeypatch):
    """A small unrelated candidate archive exercises the real importer/selector."""
    source = tmp_path / "original"
    source.mkdir()
    common = common_fixture()
    files = {
        "inputs/common.npz": _npz(common),
        "inputs/cases/white-01/arrays.npz": _npz(
            {"observed": common["signal"], "jitter_observed": common["jitter_signal"]}
        ),
        "inputs/cases/white-01/record.json": b"{}",
    }
    candidates = [
        {
            "tree": constant(value),
            "complexity": 1,
            "loss": loss,
            "display_equation": str(value),
        }
        for value, loss in ((0, 0.5), (1, 0.2))
    ]
    base = "duration/cases/white-01/symbolic/ordinary"
    package = {
        "package_status": "success",
        "technical": False,
        "search_calls": 4,
        "selected_member": 0,
        "selected_candidate": candidates[1],
    }
    files[base + "/completion/assessment_report.json"] = sources.json_bytes(package)
    for member in range(1, 5):
        prefix = f"{base}/member-{member:02d}"
        documents = {
            "result.json": {"candidates": candidates, "selected_index": 1},
            "request.json": {
                "technical": False,
                "profile": "r4x1000-local300x5-v1",
                "seed": member,
                "budget": {
                    "niterations": 1000,
                    "populations": 2,
                    "population_size": 32,
                    "ncycles_per_iteration": 50,
                    "seed": member,
                },
            },
            "metadata.json": {"phase": "success"},
            "prepared.json": {
                "provenance": {
                    "git": {
                        "commit": "8a1a4a1437f4b01daf1f070b56add248074c5907",
                        "dirty": False,
                    }
                }
            },
        }
        hashes = {}
        for name, document in documents.items():
            raw = sources.json_bytes(document)
            files[prefix + "/" + name] = raw
            hashes[name] = sources.sha256(raw)
        files[prefix + "/checksums.json"] = sources.json_bytes(hashes)
    manifest = sources.json_bytes(
        {
            "part": "fixture",
            "files_sha256": {name: sources.sha256(raw) for name, raw in files.items()},
        }
    )
    files["ARCHIVE-fixture.json"] = manifest
    for name, raw in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    monkeypatch.setattr(selection, "MANIFESTS", {"fixture": sources.sha256(manifest)})
    monkeypatch.setattr(selection, "CASES", ("white-01",))
    monkeypatch.setattr(selection, "ARMS", ("ordinary",))
    monkeypatch.setattr(
        selection,
        "_binding",
        lambda consumed: {"fixture": "technical-only", "provenance": {"fixture": True}},
    )
    monkeypatch.setattr(
        selection.original,
        "case_specs",
        lambda: [{"id": "white-01", "search_seeds": [1, 2, 3, 4]}],
    )
    return source, files


def test_complete_small_export_and_read_only_replay(archive_fixture, tmp_path):
    source, original_bytes = archive_fixture
    output = tmp_path / "comparison"
    report = selection.run(source, output)
    assert report["completed_packages"] == 1
    assert report["records"][0]["pool_size"] == 8
    assert report["records"][0]["original_selection_reproduced"] is True
    assert report["fits"] == report["search_calls"] == 0
    assert selection.verify(source, output)["status"] == "verified"
    assert all(
        (source / name).read_bytes() == raw for name, raw in original_bytes.items()
    )
    assert (output / "white-01-ordinary.png").is_file()
    assert "Originalformeln" in (output / "index.html").read_text()
    assert (output / "white-01-ordinary.formula.txt").read_text().count(
        "Original:"
    ) == 1
    (output / "white-01-ordinary.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="bytes changed"):
        selection.verify(source, output)


def test_source_changes_fail_closed_and_retain_failed_output(archive_fixture, tmp_path):
    source, _ = archive_fixture
    (source / "inputs/common.npz").write_bytes(b"changed")
    output = tmp_path / "failure"
    with pytest.raises(ValueError, match="archive binding differs"):
        selection.run(source, output)
    assert (output / publication.LOCK).exists()
    assert not (output / publication.MANIFEST).exists()


def test_late_output_mutation_is_detected_after_scientific_replay(
    archive_fixture, tmp_path, monkeypatch
):
    source, _ = archive_fixture
    output = tmp_path / "comparison"
    selection.run(source, output)
    original_compute = selection._compute

    def changed_after_replay(*args, **kwargs):
        result = original_compute(*args, **kwargs)
        (output / "white-01-ordinary.png").write_bytes(b"changed during replay")
        return result

    monkeypatch.setattr(selection, "_compute", changed_after_replay)
    with pytest.raises(ValueError, match="bytes changed"):
        selection.verify(source, output)


def test_overlapping_output_is_rejected_before_writing(archive_fixture):
    source, _ = archive_fixture
    with pytest.raises(ValueError, match="separate"):
        selection.run(source, source / "new")
    assert not (source / "new").exists()


def test_unfrozen_plan_is_not_executable(monkeypatch):
    monkeypatch.setattr(selection, "PLAN_SHA256", None)
    with pytest.raises(RuntimeError, match="not been frozen"):
        selection._binding(publication.Consumption(publication.Deadline(30)))


def test_large_finite_statistics_do_not_overflow_intermediate_sums():
    record = selection._statistics([1e308, 1e308])
    assert record == {
        "mean": 1e308,
        "median": 1e308,
        "sd": 0.0,
        "mcse": 0.0,
        "sd_status": "finite",
        "mcse_status": "finite",
    }
    signed = selection._statistics([-1.7e308, 1.7e308])
    assert signed["mean"] == signed["median"] == 0
    assert signed["sd"] is None
    assert signed["sd_status"] == "not_representable"
    assert signed["mcse"] == pytest.approx(1.7e308)
    assert signed["mcse_status"] == "finite"


def _summary_record(case, original_value, same_value, off_value):
    return {
        "case": case,
        "arm": "ordinary",
        "outputs": {
            selector: {
                "metrics": {
                    grid: {"rms_over_amplitude": value, "max_over_amplitude": value}
                    for grid in ("irregular", "diagnostic")
                }
            }
            for selector, value in zip(
                selection.SELECTORS,
                (original_value, same_value, off_value),
                strict=True,
            )
        },
    }


def test_primary_paired_geometry_contrast_keeps_cases_and_large_values():
    records = [_summary_record(f"ar1-{i:02d}", 1e308, 1e308, 5e307) for i in (1, 2)]
    marginal = [
        row
        for row in selection._summaries(records)
        if row["model"] == "ar1"
        and row["arm"] == "ordinary"
        and row["selector"] == "original"
    ]
    assert all(row["mean"] == row["median"] == 1e308 for row in marginal)
    pairs, summaries = selection._contrasts(records)
    primary = [
        row
        for row in summaries
        if row["model"] == "ar1"
        and row["arm"] == "ordinary"
        and row["contrast"] == "off_grid-minus-same_grid"
    ]
    assert len(primary) == 4
    assert all(
        row["priority"] == "primary"
        and row["available_pairs"] == 2
        and row["mean"] == -5e307
        and row["mcse"] == 0
        for row in primary
    )
    assert {row["case"] for row in pairs} == {"ar1-01", "ar1-02"}
    records[1]["outputs"]["off_grid"]["metrics"]["irregular"]["rms_over_amplitude"] = (
        None
    )
    _, summaries = selection._contrasts(records)
    partial = next(
        row
        for row in summaries
        if row["model"] == "ar1"
        and row["arm"] == "ordinary"
        and row["contrast"] == "off_grid-minus-same_grid"
        and row["grid"] == "irregular"
        and row["metric"] == "rms_over_amplitude"
    )
    assert partial["available_pairs"] == 1 and partial["unavailable_pairs"] == 19
    assert partial["mcse"] is None


@pytest.mark.parametrize("sign", [-1, 1])
def test_extreme_plot_is_explicitly_scaled_without_changing_points(sign):
    rows = [
        {
            "selector": selector,
            "grid": "irregular",
            "time_s": t,
            "truth": 0.0,
            "prediction": value,
        }
        for selector in selection.SELECTORS
        for t, value in ((0.0, 1.0), (0.5, sign * 1.7e308), (1.0, 1.0))
    ]
    before = copy.deepcopy(rows)
    images = selection._panel("technical", "ordinary", rows)
    assert images["png"].startswith(b"\x89PNG")
    assert "Beide Anzeigeachsen geteilt" in images["svg"].decode()
    assert rows == before
    metrics = selection._metrics(np.array([1.0, sign * 1.7e308, 1.0]), np.zeros(3))
    assert metrics["rms_over_amplitude"] == pytest.approx(
        (1.7e308 / math.sqrt(3)) / abs(selection.original.SIGNAL["amplitude"])
    )
    assert metrics["max_over_amplitude"] is None


def test_failed_status_cannot_be_verified_even_with_a_matching_manifest(
    archive_fixture, tmp_path
):
    source, _ = archive_fixture
    output = tmp_path / "comparison"
    selection.run(source, output)
    report_path = output / publication.REPORT
    report = sources.read_json(report_path.read_bytes())
    report["status"] = "failed"
    report_path.write_bytes(sources.json_bytes(report))
    manifest_path = output / publication.MANIFEST
    manifest = sources.read_json(manifest_path.read_bytes())
    manifest[publication.REPORT] = sources.sha256(report_path.read_bytes())
    manifest_path.write_bytes(sources.json_bytes(manifest))
    with pytest.raises(ValueError, match="not completed"):
        selection.verify(source, output)


def test_abort_costs_preserve_original_failure(archive_fixture, tmp_path, monkeypatch):
    source, _ = archive_fixture
    output = tmp_path / "failure"
    original_error = RuntimeError("fixed technical failure")

    def fail(*args, **kwargs):
        raise original_error

    monkeypatch.setattr(selection, "_compute", fail)
    with pytest.raises(RuntimeError) as captured:
        selection.run(source, output)
    assert captured.value is original_error
    call = sources.read_json((tmp_path / "failure-call.json").read_bytes())
    assert call["status"] == "aborted" and call["source_report_sha256"] is None
    assert call["wall_seconds"] >= 0 and call["cpu_seconds"] >= 0
    assert call["error"] == "RuntimeError: fixed technical failure"
    assert (output / publication.LOCK).exists()


def test_cost_write_failure_does_not_replace_original_exception(
    archive_fixture, tmp_path, monkeypatch
):
    source, _ = archive_fixture
    output = tmp_path / "failure"
    original_error = RuntimeError("first failure")

    def fail(*args, **kwargs):
        raise original_error

    def cost_failure(*args, **kwargs):
        raise OSError("cost write failed")

    monkeypatch.setattr(selection, "_compute", fail)
    monkeypatch.setattr(selection, "_write_call", cost_failure)
    with pytest.raises(RuntimeError) as captured:
        selection.run(source, output)
    assert captured.value is original_error
    assert any("cost write failed" in note for note in original_error.__notes__)
    failure = sources.read_json((output / publication.REPORT).read_bytes())
    assert failure["error"] == "RuntimeError: first failure"
    assert (output / publication.LOCK).exists()


def test_successful_computation_is_revoked_if_cost_publication_fails(
    archive_fixture, tmp_path, monkeypatch
):
    source, _ = archive_fixture
    output = tmp_path / "comparison"

    def cost_failure(*args, **kwargs):
        raise OSError("cost write failed")

    monkeypatch.setattr(selection, "_write_call", cost_failure)
    with pytest.raises(OSError, match="cost write failed"):
        selection.run(source, output)
    assert (output / publication.LOCK).exists()
    assert not (output / publication.MANIFEST).exists()
