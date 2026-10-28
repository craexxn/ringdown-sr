"""Independent metric references and complete/incomplete orchestration contracts."""

import copy
import importlib.util
import json
import math
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_structure import constant, model, operator, time_node

from ringdown_sr import noiseless_control as control
from ringdown_sr import symbolic
from ringdown_sr.parameters import analyze_tree
from ringdown_sr.pilot import _json_bytes, _sha256

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_noiseless_control.py"
SPEC = importlib.util.spec_from_file_location("noiseless_driver", SCRIPT)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


def reference_tree(frequency=250, amplitude=1, phase=0, rate=-125):
    return model(
        amplitude=amplitude,
        exponential=operator("*", constant(rate), time_node()),
        oscillation=operator(
            "+",
            operator("*", constant(2 * math.pi * frequency), time_node()),
            constant(phase),
        ),
    )


def candidate(tree, arrays):
    prediction = symbolic.evaluate_tree(tree, arrays["time_s"])
    residual = arrays["observed"] - prediction

    def nodes(node):
        return 1 + sum(nodes(child) for child in node.get("children", []))

    return {
        "tree": tree,
        "complexity": nodes(tree),
        "loss": float(np.mean(residual**2)),
        "display_equation": "controlled test fixture",
        "prediction": prediction.tolist(),
        "residual": residual.tolist(),
    }


def test_reviewed_cells_have_exact_membership_order_and_balanced_positions():
    cells = control.planned_cells()
    assert [
        (cell["budget"]["seed"], cell["budget"]["niterations"]) for cell in cells
    ] == [
        (20261020, 10),
        (20261020, 50),
        (20261020, 200),
        (20261021, 50),
        (20261021, 200),
        (20261021, 10),
        (20261022, 200),
        (20261022, 10),
        (20261022, 50),
    ]
    for position in range(3):
        assert {
            cells[index]["budget"]["niterations"] for index in range(position, 9, 3)
        } == {10, 50, 200}
    assert all(cell["status"] == "planned" for cell in cells)
    assert len({cell["directory"] for cell in cells}) == 9
    assert all(
        {
            key: value
            for key, value in cell["budget"].items()
            if key not in {"seed", "niterations"}
        }
        == {"populations": 2, "population_size": 32, "ncycles_per_iteration": 50}
        for cell in cells
    )


def test_frozen_grid_independent_integer_construction_and_truth():
    arrays = control.frozen_data()
    np.testing.assert_array_equal(arrays["time_s"], np.arange(128) / 4096)
    expected = np.array([index / 32768 for index in range(1, 1016) if index % 8])
    np.testing.assert_array_equal(arrays["diagnostic_time_s"], expected)
    assert len(expected) == 889
    assert (expected[0], expected[-1]) == (1 / 32768, 1015 / 32768)
    assert not np.intersect1d(expected, arrays["time_s"]).size
    np.testing.assert_array_equal(
        arrays["observed"],
        np.exp(-arrays["time_s"] / 0.008) * np.cos(2 * np.pi * 250 * arrays["time_s"]),
    )
    assert all(
        value.dtype == np.float64 and not value.flags.writeable
        for value in arrays.values()
    )
    assert control.fingerprint(np.array([1.0], dtype=">f8")) == control.fingerprint(
        np.array([1.0], dtype="<f8")
    )


@pytest.mark.parametrize(
    "scale", [1, 1e-300, 1e300, float.fromhex("0x0.0000000000001p-1022")]
)
def test_curve_error_reference_without_unit_floor_and_without_raw_overflow(scale):
    truth = np.array([scale, -scale])
    result = control.curve_errors(-truth, truth)
    assert result == {
        "status": "available",
        "reason": None,
        "relative_rms": 2,
        "relative_max": 2,
    }
    exact = control.curve_errors(truth, truth)
    assert exact["relative_rms"] == exact["relative_max"] == 0


def test_curve_metrics_independent_unequal_reference():
    result = control.curve_errors([2, 2], [1, -2])
    assert result["relative_rms"] == pytest.approx(math.sqrt(17 / 5))
    assert result["relative_max"] == 2


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_predictions_remain_null(bad):
    result = control.curve_errors([bad], [1])
    assert result["status"] == "not_available"
    assert result["relative_rms"] is result["relative_max"] is None
    json.dumps(result, allow_nan=False)


def test_unrepresentable_relative_error_is_not_clipped_or_zero():
    result = control.curve_errors([1e308], [1e-300])
    assert result["status"] == "numerical_unresolved"
    assert result["relative_rms"] is result["relative_max"] is None


@pytest.mark.parametrize(
    "truth,prediction", [([0], [1]), ([1], []), ([np.nan], [1]), ([[1]], [[1]])]
)
def test_invalid_reference_or_shape_rejected(truth, prediction):
    with pytest.raises(ValueError):
        control.curve_errors(prediction, truth)


@pytest.mark.parametrize("frequency,visible", [(4346, True), (33018, False)])
def test_both_alias_counterexamples_keep_original_tree_and_no_identification(
    frequency, visible
):
    arrays = control.frozen_data()
    tree = reference_tree(frequency=frequency)
    result = control.diagnose_candidate(candidate(tree, arrays), 0, 0, arrays)
    assert result["analysis"]["raw_replay"]["status"] == "passed"
    assert result["analysis"]["alias_replay"]["status"] == "passed"
    assert result["parameter_match"]["status"] == "matched"
    assert result["curve_errors"]["training"]["relative_rms"] < 1e-10
    dense_error = result["curve_errors"]["diagnostic"]["relative_rms"]
    if visible:
        assert dense_error == pytest.approx(1.5094304541552443, rel=1e-12)
        assert result["curve_marker"] == "outside_tolerance"
    else:
        assert dense_error < 1e-10
        assert result["curve_marker"] == "within_tolerance"
        t = np.array([1 / (16 * 4096)])
        np.testing.assert_allclose(
            symbolic.evaluate_tree(tree, t),
            -symbolic.evaluate_tree(reference_tree(), t),
            rtol=1e-13,
        )
    assert (
        result["physical_identification"]
        == result["parameter_match"]["physical_identification"]
        == "not_assessed"
    )


@pytest.mark.parametrize("amplitude,phase", [(1, 0), (-1, math.pi), (-1, -math.pi)])
def test_signed_amplitude_phase_equivalence_is_not_rewritten(amplitude, phase):
    arrays = control.frozen_data()
    tree = reference_tree(amplitude=amplitude, phase=phase)
    source = copy.deepcopy(tree)
    result = control.diagnose_candidate(candidate(tree, arrays), 0, 0, arrays)
    assert tree == source
    assert result["parameter_match"]["status"] == "matched"
    assert result["analysis"]["raw_parameters"]["amplitude"]["value"] == amplitude
    assert result["parameter_match"]["errors"]["complex_amplitude"] < 1e-14


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"rate": 0}, "not_decaying"),
        ({"rate": 1}, "not_decaying"),
        ({"amplitude": 0}, "zero_amplitude"),
        ({"frequency": 0}, "degenerate_alias"),
    ],
)
def test_parameter_gates(kwargs, reason):
    arrays = control.frozen_data()
    result = control.diagnose_candidate(
        candidate(reference_tree(**kwargs), arrays), 0, 0, arrays
    )
    assert result["parameter_match"]["status"] == "not_assessed"
    assert result["parameter_match"]["reason"] == reason


@pytest.mark.parametrize(
    "field,status,reason",
    [
        ("raw_replay", "failed", "raw_replay_not_passed"),
        ("raw_replay", "not_attempted", "raw_replay_not_passed"),
        ("alias", "numerical_unresolved", "alias_unavailable"),
        ("alias_replay", "failed", "alias_replay_not_passed"),
        ("alias_replay", "not_attempted", "alias_replay_not_passed"),
    ],
)
def test_failed_or_unresolved_analysis_cannot_match(field, status, reason):
    arrays = control.frozen_data()
    analysis = analyze_tree(reference_tree(), arrays["time_s"], sample_rate_hz=4096)
    analysis[field]["status"] = status
    result = control.parameter_match(analysis)
    assert result["status"] == "not_assessed" and result["reason"] == reason


def test_amplitude_phase_and_continuous_errors_prevent_false_match():
    arrays = control.frozen_data()
    result = control.diagnose_candidate(
        candidate(reference_tree(amplitude=-1), arrays), 0, 0, arrays
    )
    assert result["parameter_match"]["errors"]["amplitude"] == 0
    assert result["parameter_match"]["errors"]["complex_amplitude"] == 2
    assert result["parameter_match"]["status"] == "mismatched"
    analysis = result["analysis"]
    analysis["raw_parameters"]["decay_time_s"]["value"] = 1e308
    result = control.parameter_match(analysis)
    assert result["status"] == "not_assessed"
    assert result["errors"]["decay_time"] is None
    assert result["errors"]["amplitude"] == 0


def test_unsupported_sine_can_match_curve_without_parameter_attempt():
    arrays = control.frozen_data()
    tree = operator(
        "*",
        operator("exp", operator("*", constant(-125), time_node())),
        operator(
            "sin",
            operator(
                "+",
                operator("*", constant(2 * math.pi * 250), time_node()),
                constant(math.pi / 2),
            ),
        ),
    )
    result = control.diagnose_candidate(candidate(tree, arrays), 0, 0, arrays)
    assert result["curve_marker"] == "within_tolerance"
    assert result["analysis"]["structure"]["structure_status"] == "not_supported"
    assert result["analysis"]["raw_replay"]["status"] == "not_attempted"
    assert result["parameter_match"]["status"] == "not_assessed"


def test_between_sample_singularity_keeps_nonfinite_reason():
    arrays = control.frozen_data()
    pole = arrays["diagnostic_time_s"][0]
    tree = operator("/", constant(1), operator("-", time_node(), constant(pole)))
    result = control.diagnose_candidate(candidate(tree, arrays), 0, 0, arrays)
    assert result["curve_errors"]["training"]["status"] == "available"
    assert result["curve_errors"]["diagnostic"]["reason"] == "nonfinite_original_tree"
    assert result["curve_marker"] == "not_assessed"


def pools_environment(julia=False):
    roles = ["numpy.libs/libopenblas.so", "scipy.libs/libopenblas.so"]
    if julia:
        roles.append("julia/lib/julia/libopenblas.so")
    return {
        "numerical_libraries": {
            "threadpools": {
                "status": "available",
                "details": [
                    {
                        "filepath": "/fixture/" + role,
                        "user_api": "blas",
                        "internal_api": "openblas",
                        "num_threads": 1,
                        "architecture": "Haswell",
                    }
                    for role in roles
                ],
            }
        }
    }


@pytest.fixture
def fake_runtime(monkeypatch):
    support = DRIVER.load_support()
    probe = support.load_core_probe()
    initial = {
        "provenance": {"git": {"commit": "test-fixture", "dirty": False}},
        "adapter_source_sha256": {"fixture": "hash"},
        "environment": pools_environment(),
    }
    for key in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        monkeypatch.setenv(key, "1")
    monkeypatch.setenv("OPENBLAS_CORETYPE", "Haswell")
    monkeypatch.setattr(probe, "metadata", lambda: copy.deepcopy(initial))
    monkeypatch.setattr(support, "load_core_probe", lambda: probe)
    monkeypatch.setattr(DRIVER, "load_support", lambda: support)
    state = SimpleNamespace(
        support=support, probe=probe, initial=initial, calls=[], hook=None
    )

    def search(time, observed, *, covariance, output, budget):
        assert covariance is None
        assert not time.flags.writeable and not observed.flags.writeable
        state.calls.append((time.copy(), observed.copy(), budget, output))
        number = len(state.calls)
        output.mkdir()
        np.savez(output / "inputs.npz", time_s=time, observed=observed)
        arrays = {"time_s": time, "observed": observed}
        front = [
            candidate(constant(0), arrays),
            candidate(reference_tree(amplitude=3), arrays),
        ]
        metadata = {
            "phase": "success",
            "provenance": initial["provenance"],
            "worker_provenance": initial["provenance"],
            "adapter_source_sha256": initial["adapter_source_sha256"],
            "worker_adapter_source_sha256": initial["adapter_source_sha256"],
            "environment": pools_environment(True),
            "environment_after_search": pools_environment(True),
        }
        control_record = {
            "format": support.CONTROL_FORMAT,
            "status": "verified",
            "required_openblas_core": "Haswell",
            "tool_source_sha256": support.tool_hashes(),
            "snapshots": {},
        }
        for phase, field in (
            ("before_fit", "environment"),
            ("after_search", "environment_after_search"),
        ):
            environment = metadata[field]
            control_record["snapshots"][phase] = {
                "environment": environment,
                "openblas_coretype_environment": "Haswell",
                "blas_control": probe.verify_blas_control(
                    environment, "Haswell", require_julia=True
                ),
            }
        documents = {
            "request.json": {"format": symbolic.FORMAT, "budget": asdict(budget)},
            "status.json": {"status": "success"},
            "metadata_initial.json": {"provenance": initial["provenance"]},
            "metadata.json": metadata,
            "pysr_parameters.json": {
                **symbolic.search_parameters(budget),
                "output_directory": str(output / "pysr"),
            },
            "backend_options.json": [
                {"name": key, "type": "fixture", "value": str(value)}
                for key, value in {
                    "seed": budget.seed + 10,
                    "niterations": budget.niterations,
                    "maxsize": 20,
                }.items()
            ],
            "result.json": {
                "format": symbolic.FORMAT,
                "evaluation_scope": "fitted_samples_only",
                "selection": "minimum_training_loss_then_complexity",
                "candidates": front,
                "selected_index": 0,
                "rng": {"python_seed": budget.seed, "backend_seed": budget.seed + 10},
                "timing_seconds": {"fixture": 0},
                "backend_evaluation_counter": {"status": "unavailable"},
            },
            "blas_control.json": control_record,
        }
        if state.hook:
            state.hook(number, output, documents)
        for name, value in documents.items():
            (output / name).write_bytes(_json_bytes(value))
        (output / "worker.log").write_text("Mocked worker: no Julia/search executed.\n")
        (output / "checksums.json").write_bytes(
            _json_bytes(
                {
                    path.name: _sha256(path.read_bytes())
                    for path in output.iterdir()
                    if path.name not in {"status.json", "worker.log"}
                }
            )
        )
        return symbolic.SearchRun(output, "success")

    monkeypatch.setattr(symbolic, "run_search_arm", search)
    return state


def load_report(output):
    return json.loads((output / "report.json").read_text())


def test_complete_orchestration_preserves_all_candidates_selection_and_input_bits(
    fake_runtime, tmp_path
):
    output = tmp_path / "control"
    original_dispatch = symbolic._run_worker
    report = DRIVER.run_control(output, label="unit-test fixture")
    assert symbolic._run_worker is original_dispatch
    assert report["status"] == "completed" and report["cell_states"] == {"completed": 9}
    assert report["started_count"] == len(fake_runtime.calls) == 9
    for time, observed, budget, directory in fake_runtime.calls:
        np.testing.assert_array_equal(
            time.view(np.uint64), fake_runtime.calls[0][0].view(np.uint64)
        )
        np.testing.assert_array_equal(
            observed.view(np.uint64), fake_runtime.calls[0][1].view(np.uint64)
        )
    for cell in report["cells"]:
        diagnosis = cell["diagnostics"]
        assert diagnosis["selected_index"] == 0
        assert diagnosis["front_has_recognized"]
        assert [item["source_index"] for item in diagnosis["candidates"]] == [0, 1]
        assert (
            diagnosis["candidates"][0]["analysis"]["structure"]["structure_status"]
            == "not_supported"
        )
        assert diagnosis["rng"]["backend_seed"] == cell["budget"]["seed"] + 10
        assert diagnosis["blas_control"]["status"] == "verified"
    assert all(
        summary["status"] == "complete"
        for summary in report["budget_summaries"].values()
    )
    metadata = json.loads((output / "metadata.json").read_text())
    for name, digest in metadata["artifact_sha256"].items():
        assert _sha256((output / name).read_bytes()) == digest
    assert "Achtelraster" in (output / "summary.md").read_text()


@pytest.mark.parametrize(
    "error,status",
    [
        (RuntimeError("fixture failure"), "failed"),
        (KeyboardInterrupt("fixture abort"), "aborted"),
    ],
)
def test_failure_and_abort_keep_planned_cells_artifacts_and_restore_dispatch(
    fake_runtime, tmp_path, error, status
):
    def interrupt(number, directory, documents):
        if number == 2:
            (directory / "partial.log").write_text("retained")
            raise error

    fake_runtime.hook = interrupt
    output = tmp_path / "control"
    original = symbolic._run_worker
    with pytest.raises(type(error)):
        DRIVER.run_control(output, label="fixture")
    assert symbolic._run_worker is original
    report = load_report(output)
    assert report["status"] == status
    assert [cell["status"] for cell in report["cells"]] == ["completed", status] + [
        "planned"
    ] * 7
    assert report["started_count"] == 2
    assert all(
        summary["statistics"] is None for summary in report["budget_summaries"].values()
    )
    assert (output / "cell-02/partial.log").read_text() == "retained"
    assert (output / "metadata.json").exists()


@pytest.mark.parametrize(
    "fault", ["selection", "covariance", "parameters", "backend", "core", "provenance"]
)
def test_internally_checksummed_but_wrong_worker_rejected(
    fake_runtime, tmp_path, fault
):
    def alter(number, directory, docs):
        if number != 2:
            return
        if fault == "selection":
            docs["result.json"]["selected_index"] = 1
        elif fault == "covariance":
            with np.load(directory / "inputs.npz") as data:
                arrays = {key: data[key] for key in data.files}
            np.savez(directory / "inputs.npz", **arrays, covariance=np.eye(128))
        elif fault == "parameters":
            docs["pysr_parameters.json"]["niterations"] = 999
        elif fault == "backend":
            docs["backend_options.json"][-1]["value"] = "19"
        elif fault == "core":
            docs["blas_control.json"]["snapshots"].pop("after_search")
        else:
            docs["metadata.json"]["worker_provenance"] = {"changed": True}

    fake_runtime.hook = alter
    output = tmp_path / "control"
    with pytest.raises(ValueError):
        DRIVER.run_control(output, label="fixture")
    assert load_report(output)["status"] == "failed"
    assert len(fake_runtime.calls) == 2


def test_diagnostic_truth_does_not_enter_worker_or_change_original_selection(
    fake_runtime, monkeypatch, tmp_path
):
    original = control.frozen_data()
    changed = {key: value.copy() for key, value in original.items()}
    changed["diagnostic_truth"][:] = 9
    changed["diagnostic_time_s"] += 0.000001
    for value in changed.values():
        value.flags.writeable = False
    monkeypatch.setattr(DRIVER, "frozen_data", lambda: changed)
    report = DRIVER.run_control(tmp_path / "changed", label="fixture")
    for time, observed, budget, directory in fake_runtime.calls:
        np.testing.assert_array_equal(time, original["time_s"])
        np.testing.assert_array_equal(observed, original["observed"])
    assert all(cell["diagnostics"]["selected_index"] == 0 for cell in report["cells"])


def test_exclusive_outputs_and_invalid_profile_fail_without_search(
    fake_runtime, monkeypatch, tmp_path
):
    existing = tmp_path / "exists"
    existing.mkdir()
    (existing / "keep").write_text("unchanged")
    with pytest.raises(FileExistsError):
        DRIVER.run_control(existing, label="fixture")
    assert (existing / "keep").read_text() == "unchanged"
    monkeypatch.delenv("OPENBLAS_CORETYPE")
    output = tmp_path / "invalid"
    with pytest.raises(ValueError, match="OPENBLAS_CORETYPE"):
        DRIVER.run_control(output, label="fixture")
    assert not output.exists() and not fake_runtime.calls


def test_source_tampering_after_completed_worker_prevents_success(
    fake_runtime, tmp_path
):
    def tamper(number, directory, docs):
        if number == 2:
            first = directory.parent / "cell-01/result.json"
            first.write_bytes(first.read_bytes() + b"\n")

    fake_runtime.hook = tamper
    output = tmp_path / "control"
    with pytest.raises(ValueError, match="diagnosed source"):
        DRIVER.run_control(output, label="fixture")
    report = load_report(output)
    assert report["status"] == "failed" and "final_verification_error" in report


def test_final_core_failure_cannot_leave_success_marker(
    fake_runtime, monkeypatch, tmp_path
):
    calls = []
    original = fake_runtime.probe.metadata

    def snapshot():
        calls.append(1)
        if len(calls) == 2:
            raise ValueError("final pool failure fixture")
        return original()

    monkeypatch.setattr(fake_runtime.probe, "metadata", snapshot)
    output = tmp_path / "control"
    with pytest.raises(ValueError, match="final pool"):
        DRIVER.run_control(output, label="fixture")
    assert load_report(output)["status"] == "failed"
    assert all(
        summary["statistics"] is None
        for summary in load_report(output)["budget_summaries"].values()
    )
    assert json.loads((output / "metadata.json").read_text())["status"] == "failed"


def test_unavailable_parameter_field_cannot_be_assessed():
    arrays = control.frozen_data()
    analysis = analyze_tree(reference_tree(), arrays["time_s"], sample_rate_hz=4096)
    analysis["raw_parameters"]["amplitude"].update(
        status="numerical_unresolved", value=None
    )
    result = control.parameter_match(analysis)
    assert result["status"] == "not_assessed"
    assert result["reason"] == "unavailable_parameter_field"


def test_worker_failure_status_is_retained_without_retry(
    fake_runtime, monkeypatch, tmp_path
):
    search = symbolic.run_search_arm

    def failed(*args, **kwargs):
        run = search(*args, **kwargs)
        return symbolic.SearchRun(run.output_directory, "failed")

    monkeypatch.setattr(symbolic, "run_search_arm", failed)
    output = tmp_path / "control"
    with pytest.raises(RuntimeError, match="Worker failed"):
        DRIVER.run_control(output, label="fixture")
    report = load_report(output)
    assert report["cells"][0]["search_status"] == "failed"
    assert report["cells"][0]["status"] == "failed"
    assert len(fake_runtime.calls) == 1
    assert all(cell["status"] == "planned" for cell in report["cells"][1:])


def test_worker_checksum_mismatch_rejected(fake_runtime, monkeypatch, tmp_path):
    search = symbolic.run_search_arm

    def corrupt(*args, **kwargs):
        run = search(*args, **kwargs)
        path = run.output_directory / "result.json"
        path.write_bytes(path.read_bytes() + b"\n")
        return run

    monkeypatch.setattr(symbolic, "run_search_arm", corrupt)
    with pytest.raises(ValueError, match="checksum"):
        DRIVER.run_control(tmp_path / "control", label="fixture")
    assert len(fake_runtime.calls) == 1


def test_changed_method_plan_and_source_overlap_rejected_before_reserving_output(
    fake_runtime, monkeypatch, tmp_path
):
    changed = tmp_path / "plan.md"
    changed.write_bytes(DRIVER.PLAN.read_bytes() + b"\n")
    monkeypatch.setattr(DRIVER, "PLAN", changed)
    output = tmp_path / "control"
    with pytest.raises(ValueError, match="method plan"):
        DRIVER.run_control(output, label="fixture")
    assert not output.exists()
    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(DRIVER.ROOT / "scripts", target_is_directory=True)
    with pytest.raises(ValueError, match="overlap"):
        DRIVER.run_control(source_alias / "uncreated-control", label="fixture")
    assert not (source_alias / "uncreated-control").exists()
    assert not fake_runtime.calls


def test_changed_frozen_diagnostic_file_prevents_completion(fake_runtime, tmp_path):
    def tamper(number, directory, docs):
        if number == 2:
            (directory.parent / "diagnostic.npz").write_bytes(b"changed")

    fake_runtime.hook = tamper
    output = tmp_path / "control"
    with pytest.raises(ValueError, match="changed"):
        DRIVER.run_control(output, label="fixture")
    report = load_report(output)
    assert report["status"] == "failed"
    assert len(fake_runtime.calls) == 2
    assert all(
        summary["statistics"] is None for summary in report["budget_summaries"].values()
    )
