"""Independent checks of the frozen pilot's design and numerical identities."""

import csv
import math
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import white_scaling as pilot


def test_design_is_paired_with_one_preselected_repeat():
    cells = pilot.cells()
    primary = [cell for cell in cells if not cell["repeat"]]
    assert len(primary) == 18
    assert len(cells) == 21
    assert len({cell["id"] for cell in cells}) == 21
    for case in (1, 2):
        for seed in pilot.SEARCH_SEEDS:
            assert {
                cell["arm"]
                for cell in primary
                if cell["case"] == case and cell["seed"] == seed
            } == {"ordinary", "scaled", "covariance"}
    assert all(
        cell["case"] == 1 and cell["seed"] == pilot.SEARCH_SEEDS[0]
        for cell in cells
        if cell["repeat"]
    )


def test_data_formula_and_raster_roles_are_independently_reproducible():
    arrays = pilot.data()
    times = arrays["time_s"]
    assert len(times) == 128
    assert np.array_equal(times, np.arange(128) / 4096)
    reference = np.array(
        [
            (11 / 12)
            * math.exp(-150 * float(t))
            * math.cos(530 * math.pi * float(t) + 0.25)
            for t in times
        ]
    )
    np.testing.assert_allclose(arrays["truth"], reference, rtol=1e-13, atol=1e-15)
    assert not np.array_equal(arrays["observed_1"], arrays["observed_2"])
    assert len(arrays["regular_time_s"]) == 889
    assert len(arrays["irregular_time_s"]) == 1024
    assert np.all(np.diff(arrays["irregular_time_s"]) > 0)
    assert not set(times).intersection(arrays["irregular_time_s"])
    assert all(
        np.array_equal(value, pilot.data()[key]) for key, value in arrays.items()
    )


def test_start_policy_has_no_truth_frequency_tuning():
    starts = pilot.starts(np.array([-2.0, 1.0]))
    assert len(starts) == 4
    assert all(start[0] == 2.0 and start[3] == math.pi / 2 for start in starts)
    assert {start[2] / (2 * math.pi) for start in starts} == {128.0, 512.0}
    assert {start[1] for start in starts} == {-256.0, -64.0}


def test_positive_scaling_preserves_fixed_candidate_order():
    residuals = [np.array([0.125, -0.25, 0.5]), np.array([0.5, -1.0, 0.25])]
    scale = 1 / pilot.SIGMA**2
    mse = [math.fsum(float(r) ** 2 for r in residual) / 3 for residual in residuals]
    covariance_loss = [
        math.fsum((float(r) / pilot.SIGMA) ** 2 for r in residual) / 3
        for residual in residuals
    ]
    np.testing.assert_allclose(covariance_loss, np.array(mse) * scale, rtol=5e-16)
    assert np.argmin(mse) == np.argmin(covariance_loss)


def test_offgrid_pole_is_reported_and_finite_points_are_preserved():
    one = {"kind": "constant", "value_hex": (1.0).hex()}
    half = {"kind": "constant", "value_hex": (0.5).hex()}
    variable = {"kind": "variable", "index": 1}
    denominator = {
        "kind": "operator",
        "arity": 2,
        "operator_index": 2,
        "operator": "-",
        "children": [variable, half],
    }
    tree = {
        "kind": "operator",
        "arity": 2,
        "operator_index": 4,
        "operator": "/",
        "children": [one, denominator],
    }
    values, metrics = pilot.evaluate_grid(tree, [0.0, 0.5, 1.0], np.zeros(3))
    assert values[0] == -2 and np.isnan(values[1]) and values[2] == 2
    assert metrics == {
        "status": "nonfinite_prediction",
        "nonfinite_count": 1,
        "rmse_over_a": None,
        "max_over_a": None,
    }
    _, training = pilot.evaluate_grid(tree, [0.0, 1.0], np.zeros(2))
    assert training["status"] == "finite"


def test_large_finite_values_do_not_overflow_by_squaring():
    tree = {"kind": "constant", "value_hex": (1e200).hex()}
    _, metrics = pilot.evaluate_grid(tree, [0.0, 1.0], np.zeros(2))
    assert metrics["status"] == "finite"
    assert math.isclose(metrics["rmse_over_a"], 1e200 / pilot.AMPLITUDE)
    with pytest.raises(ValueError, match="finite"):
        pilot.evaluate_grid({"kind": "constant", "value_hex": "inf"}, [0.0], [0.0])


@pytest.fixture
def export_fixture(tmp_path, monkeypatch):
    """One real formula/plot; native fits are irrelevant to publication integrity."""
    root, destination = tmp_path / "source", tmp_path / "export"
    root.mkdir()
    arrays = pilot.data()
    np.savez(root / "inputs.npz", **arrays)
    pilot._write_json(root / "manifest.json", {"sources": {}})
    cell = {"id": "fixture", "case": 1, "repeat": True}
    directory = root / "search" / cell["id"]
    directory.mkdir(parents=True)
    tree = {"kind": "constant", "value_hex": (0.25).hex()}
    pilot._write_json(
        directory / "result.json",
        {
            "selected_index": 0,
            "candidates": [{"tree": tree, "display_equation": "0.25"}],
        },
    )
    report = {
        "format": pilot.FORMAT,
        "status": "verified",
        "searches": [cell],
        "fixed": [{"fixture": True}],
        "fixed_pairs": [{"fixture": True}],
    }
    monkeypatch.setattr(pilot, "cells", lambda: [cell])
    monkeypatch.setattr(pilot, "_verify_contents", lambda output: report)
    return root, destination


def _assert_failed_export(destination, error_text):
    report = pilot._read(destination / "report.json")
    assert report["status"] == "failed" and report["release"] == "locked"
    assert error_text in report["error"]
    assert (destination / pilot.publication.LOCK).is_file()
    assert (destination / "export_failure.json").is_file()
    assert not (destination / "checksums.json").exists()
    assert not (destination / "report.json.tmp").exists()
    cost = pilot._read(destination.with_name(destination.name + "-call.json"))
    assert cost["status"] == "aborted"
    assert cost["wall_seconds"] >= 0
    assert error_text in cost["error"]


def test_export_binds_every_source_and_publishes_report_after_plots(
    export_fixture, monkeypatch
):
    from matplotlib.figure import Figure

    root, destination = export_fixture
    original = Figure.savefig
    saw_plot = []

    def savefig(self, *args, **kwargs):
        assert not (destination / "report.json").exists()
        assert (destination / pilot.publication.LOCK).is_file()
        saw_plot.append(True)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Figure, "savefig", savefig)
    report = pilot.export(root, destination)
    assert saw_plot and report["status"] == "verified"
    assert report["source_inventory_sha256"] == {
        path.relative_to(root).as_posix(): pilot._sha256(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
    }
    manifest = pilot._read(destination / "checksums.json")
    assert manifest == {
        path.name: pilot._sha256(path.read_bytes())
        for path in destination.iterdir()
        if path.name != "checksums.json"
    }
    assert not (destination / pilot.publication.LOCK).exists()
    cost = pilot._read(destination.with_name(destination.name + "-call.json"))
    assert cost["status"] == "completed"
    assert cost["cpu_measurement_complete"] is True
    assert all(
        cost[name] >= 0
        for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds")
    )


@pytest.mark.parametrize(
    "mutation", ["bytes", "new_file", "new_directory", "deleted_file"]
)
def test_export_rejects_source_change_between_verification_and_plotting(
    export_fixture, monkeypatch, mutation
):
    root, destination = export_fixture
    original = pilot._render_export

    def render(*args):
        result = original(*args)
        if mutation == "bytes":
            (root / "manifest.json").write_text('{"sources":{},"changed":true}\n')
        elif mutation == "new_file":
            (root / "unexpected.log").write_text("late output")
        elif mutation == "new_directory":
            (root / "unexpected").mkdir()
        else:
            (root / "search/fixture/result.json").unlink()
        return result

    monkeypatch.setattr(pilot, "_render_export", render)
    with pytest.raises((ValueError, FileNotFoundError)):
        pilot.export(root, destination)
    _assert_failed_export(destination, "")
    assert (destination / "fixture-formula.json").is_file()
    assert (destination / "fixture-points.csv").is_file()
    cost = pilot._read(destination.with_name(destination.name + "-call.json"))
    assert cost["cpu_measurement_complete"] is False
    assert cost["cpu_user_seconds"] >= 0 and cost["cpu_system_seconds"] >= 0


def test_plot_failure_preserves_partial_evidence_and_never_releases_success(
    export_fixture, monkeypatch
):
    from matplotlib.figure import Figure

    root, destination = export_fixture

    def fail_plot(self, filename, **kwargs):
        Path(filename).write_bytes(b"partial image")
        raise RuntimeError("injected plot failure")

    monkeypatch.setattr(Figure, "savefig", fail_plot)
    with pytest.raises(RuntimeError, match="injected plot failure"):
        pilot.export(root, destination)
    _assert_failed_export(destination, "injected plot failure")
    assert (destination / "fixture.png").read_bytes() == b"partial image"
    assert (destination / "fixture-formula.json").is_file()
    assert (destination / "fixture-points.csv").is_file()


def test_report_rename_or_handler_teardown_failure_revokes_release(
    export_fixture, monkeypatch
):
    root, destination = export_fixture
    active = pilot.publication.Deadline.active

    @contextmanager
    def fail_after_teardown(self):
        with active(self):
            yield self
        assert pilot._read(destination / "report.json")["status"] == "verified"
        raise RuntimeError("injected handler teardown failure")

    monkeypatch.setattr(pilot.publication.Deadline, "active", fail_after_teardown)
    with pytest.raises(RuntimeError, match="injected handler teardown failure"):
        pilot.export(root, destination)
    _assert_failed_export(destination, "injected handler teardown failure")


def test_export_rejects_output_inside_original_source(export_fixture):
    root, _ = export_fixture
    with pytest.raises(ValueError, match="separate sibling"):
        pilot.export(root, root / "plots")
    assert not (root / "plots").exists()


def test_verification_rechecks_complete_source_inventory(export_fixture, monkeypatch):
    root, _ = export_fixture
    original = pilot._verify_contents

    def mutate(path):
        report = original(path)
        (root / "late.json").write_text("{}")
        return report

    monkeypatch.setattr(pilot, "_verify_contents", mutate)
    with pytest.raises(ValueError, match="inventory changed"):
        pilot.verify(root)


def test_renderer_uses_snapshot_and_rejects_later_replaced_tree(
    export_fixture, monkeypatch
):
    root, destination = export_fixture
    original = pilot._render_export

    def replace_tree(*args):
        pilot._write_json(
            root / "search/fixture/result.json",
            {
                "selected_index": 0,
                "candidates": [
                    {"tree": {"kind": "constant", "value_hex": (9.0).hex()}}
                ],
            },
        )
        return original(*args)

    monkeypatch.setattr(pilot, "_render_export", replace_tree)
    with pytest.raises(ValueError, match="Consumed file changed"):
        pilot.export(root, destination)
    _assert_failed_export(destination, "Consumed file changed")
    with (destination / "fixture-points.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert rows and all(float(row["prediction"]) == 0.25 for row in rows)


@pytest.mark.parametrize("invalid_stage", ["series", "fixed"])
def test_actual_verifier_rejects_bad_cost_before_consulting_worker_results(
    tmp_path, monkeypatch, invalid_stage
):
    root = tmp_path / "source"
    root.mkdir()
    np.savez(root / "inputs.npz", **pilot.data())
    pilot._write_json(
        root / "manifest.json",
        {
            "format": pilot.FORMAT,
            "sources": {},
            "cells": pilot.cells(),
            "input_sha256": pilot._sha256((root / "inputs.npz").read_bytes()),
        },
    )
    monkeypatch.setattr(pilot, "_sources", dict)
    costs = {
        "status": "completed",
        "started_at": "2026-11-23T01:00:00+00:00",
        "finished_at": "2026-11-23T01:00:01+00:00",
        "wall_seconds": 1.0,
        "cpu_user_seconds": 0.25,
        "cpu_system_seconds": 0.125,
        "cpu_measurement_complete": True,
    }
    status = {
        **costs,
        "format": pilot.FORMAT,
        "completed_fixed": 18,
        "completed_search": 21,
        "stage": "search",
        "current_cell": pilot.cells()[-1]["id"],
        "wall_scope": pilot.SERIES_WALL_SCOPE,
        "cpu_scope": pilot.SERIES_CPU_SCOPE,
    }
    if invalid_stage == "series":
        status["wall_seconds"] = -1
    else:
        directory = root / "fixed" / pilot.cells()[0]["id"]
        directory.mkdir(parents=True)
        pilot._write_json(
            directory / "call.json",
            {
                **costs,
                "format": pilot.FORMAT + "-fixed-call-1",
                "returncode": 0,
                "wall_scope": pilot.FIXED_WALL_SCOPE,
                "cpu_scope": pilot.FIXED_CPU_SCOPE,
                "cpu_measurement_complete": False,
            },
        )
    pilot._write_json(root / "status.json", status)

    def must_not_read_worker(directory):
        pytest.fail(
            "Invalid costs must be rejected before worker evidence is consumed."
        )

    monkeypatch.setattr(pilot.fixed, "verify_fixed", must_not_read_worker)
    with pytest.raises(
        ValueError, match="finite nonnegative|Incomplete or contradictory"
    ):
        pilot.verify(root)


def test_secondary_cost_failure_preserves_original_plot_error_and_partial_costs(
    export_fixture, monkeypatch
):
    root, destination = export_fixture
    cost_path = destination.with_name(destination.name + "-call.json")
    original_error = RuntimeError("original plot failure")
    measurements = iter([(4.0, 1.0), (6.0, 1.5)])
    monkeypatch.setattr(pilot, "_cpu_snapshot", lambda: next(measurements))

    def fail_plot(*args):
        cost_path.write_bytes(b"colliding unrelated artifact")
        raise original_error

    monkeypatch.setattr(pilot, "_render_export", fail_plot)
    with pytest.raises(RuntimeError, match="original plot failure") as raised:
        pilot.export(root, destination)
    assert raised.value is original_error
    assert cost_path.read_bytes() == b"colliding unrelated artifact"
    failure = pilot._read(destination / "report.json")
    assert failure["status"] == "failed"
    assert failure["error"] == "RuntimeError: original plot failure"
    assert failure["secondary_errors"][0]["operation"] == "write cost record"
    assert failure["secondary_errors"][0]["error"].startswith("FileExistsError:")
    assert failure["cost_record"]["cpu_measurement_complete"] is False
    assert failure["cost_record"]["cpu_user_seconds"] == 2.0
    assert failure["cost_record"]["cpu_system_seconds"] == 0.5
    assert (destination / pilot.publication.LOCK).exists()
    assert not (destination / "checksums.json").exists()
