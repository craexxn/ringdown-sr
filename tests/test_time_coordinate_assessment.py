"""Physical-coordinate identities, original selection and proof-limit guards."""

import numpy as np
import pytest
from test_structure_proof import T, op, q

from ringdown_sr import assessment_sources as sources
from ringdown_sr import structure_assessment as structure
from ringdown_sr import time_coordinate_assessment as assessment
from ringdown_sr.structure import MAX_TREE_NODES, InvalidTreeError
from ringdown_sr.symbolic import evaluate_tree


def signal(times):
    # Analytic reference in physical seconds, independently specified from q(u).
    return np.exp(-4 * times) * np.cos(64 * times)


def core():
    return op("*", op("exp", op("*", q(-0.125), T)), op("cos", op("*", q(2), T)))


def inputs():
    time = np.arange(128, dtype=np.float64) / 4096
    inner = (np.arange(127, dtype=np.float64) + 0.5) / 4096
    grid = (np.arange(53, dtype=np.float64) + 0.3) / 53 * time[-1]
    return {
        "time_s": time,
        "observed": signal(time),
        "diagnostic_time_s": inner,
        "diagnostic_truth": signal(inner),
    }, {"time_s": grid, "truth": signal(grid)}


def candidate(tree, loss=0.0, complexity=None):
    return {
        "tree": tree,
        "loss": loss,
        "complexity": assessment.node_count(tree) if complexity is None else complexity,
        "unchanged_native_metadata": "kept",
    }


def front(tree):
    return {"selected_index": 0, "candidates": [candidate(tree)]}


def test_physical_ringdown_replays_exactly_and_proves_the_original_family():
    arrays, grid = inputs()
    original = front(core())
    before = sources.json_bytes(original)
    record = assessment.assess_front(original, arrays, grid, 32)[0]
    assert sources.json_bytes(original) == before
    assert record["original_candidate"] == original["candidates"][0]
    model = record["physical_model"]
    assert model["tree_sha256"] != model["source_tree_sha256"]
    assert model["source_tree_sha256"] == sources.sha256(sources.json_bytes(core()))
    assert model["proof_resource_limited"] is False
    assert model["original_nodes"] < model["physical_nodes"] <= MAX_TREE_NODES
    assert model["interval"] == structure.interval_binding(arrays["time_s"])
    for role in ("training", "diagnostic", "irregular"):
        replay = record["coordinate_replay"][role]
        assert replay["status"] == "identical_finite"
        assert replay["physical_prediction"] == replay["search_prediction"]
    proof = record["supplemental"]
    assert proof["curve"]["grade"] == "A"
    assert proof["original_family"]["status"] == "proven_member"
    assert proof["domain"]["status"] == "defined_everywhere"
    assert proof["new_parameter_match"]["status"] == "not_assessed"
    assert proof["remainder"]["status"] == "bound_proven"
    assert proof["remainder"]["evaluation_model"] == assessment.MODEL
    assert proof["remainder"]["physical_model_sha256"] == model["tree_sha256"]
    assert proof["model_binding"]["tree_sha256"] == model["tree_sha256"]
    # A private diagnostic never rewrites the stored native candidate.
    record["original_candidate"]["tree"]["children"][0] = q(1)
    assert sources.json_bytes(original) == before


def test_raw_coordinate_has_no_artificial_multiply_or_complexity_change():
    tree = core()
    transformed = assessment.physical_tree(tree, 1)
    assert transformed == tree
    assert transformed is not tree
    transformed["children"][0] = q(0)
    assert tree == core()


@pytest.mark.parametrize("scale", [0, -32, 2, 0.03125, True, "32", np.float64(32)])
def test_only_the_two_frozen_scales_are_accepted(scale):
    with pytest.raises(ValueError, match="frozen coordinate scales"):
        assessment.physical_tree(core(), scale)


@pytest.mark.parametrize(
    "tree",
    [
        {"kind": "variable", "index": 2},
        {"kind": "variable", "index": True},
        {"kind": "constant", "value_hex": "nan"},
        {**op("*", T, q(1)), "operator_index": 1},
    ],
)
def test_original_tree_integrity_errors_are_not_downgraded_to_unknown_proofs(tree):
    with pytest.raises(InvalidTreeError):
        assessment.physical_tree(tree, 32)


def test_domain_gap_moves_to_its_physical_location_without_cancellation():
    arrays, grid = inputs()
    # u=1/2 corresponds to t=1/64, inside the original physical interval.
    tree = op("/", q(1), op("-", T, q(0.5)))
    record = assessment.assess_front(front(tree), arrays, grid, 32)[0]
    proof = record["supplemental"]
    assert proof["original_family"]["status"] == "proven_nonmember"
    assert proof["domain"]["exclusions"]
    assert record["coordinate_replay"]["training"]["status"] == "both_unavailable"
    assert record["curve_errors"]["training"]["status"] == "not_available"
    assert proof["curve"]["status"] == "not_assessable"
    with pytest.raises(ValueError, match="not finite"):
        evaluate_tree(record["physical_model"]["tree"], np.array([1 / 64]))
    # Interpreting q as an unscaled physical formula would miss this hole.
    raw = assessment.assess_front(front(tree), arrays, grid, 1)[0]
    assert raw["supplemental"]["domain"]["status"] == "defined_everywhere"
    assert raw["coordinate_replay"]["training"]["status"] == "identical_finite"


def test_replay_rejects_double_scaling_even_when_both_models_are_finite():
    arrays, _ = inputs()
    wrong = assessment.physical_tree(T, 32)
    wrong["children"][0] = q(1024)
    with pytest.raises(ValueError, match="exact prediction bits"):
        assessment.paired_endpoint(T, wrong, arrays["time_s"], arrays["observed"], 32)


def test_replay_rejects_changed_availability():
    times = np.array([0.0, 0.5])
    with pytest.raises(ValueError, match="prediction availability"):
        assessment.paired_endpoint(T, op("/", q(1), T), times, np.ones(2), 32)


def test_native_loss_then_original_complexity_and_index_remain_the_selection():
    arrays, grid = inputs()
    good = candidate(core(), loss=2.0)
    bad = candidate(T, loss=1.0)
    original = {"selected_index": 1, "candidates": [good, bad]}
    records = assessment.assess_front(original, arrays, grid, 32)
    assert records[0]["supplemental"]["curve"]["grade"] == "A"
    assert records[1]["supplemental"]["curve"]["grade"] != "A"
    assert records[1]["source_identity"]["original_selected_index"] == 1
    assert records[1]["original_candidate"]["complexity"] == 1
    assert records[1]["physical_model"]["physical_nodes"] == 3
    original["selected_index"] = 0
    with pytest.raises(ValueError, match="native-loss selection"):
        assessment.assess_front(original, arrays, grid, 32)
    # Equal native losses/complexities retain the first original front entry.
    tied = {"selected_index": 0, "candidates": [candidate(T), candidate(q(1))]}
    records = assessment.assess_front(tied, arrays, grid, 32)
    assert records[0]["source_identity"]["original_selected_index"] == 0


def test_composition_node_limit_preserves_curve_and_explicitly_unknown_proofs():
    arrays, grid = inputs()
    tree = op("+", op("+", core(), op("*", q(0), T)), op("*", q(0), T))
    assert assessment.node_count(tree) == 17
    record = assessment.assess_front(front(tree), arrays, grid, 32)[0]
    model = record["physical_model"]
    assert MAX_TREE_NODES == model["exported_tree_node_limit"] == 20
    assert model["physical_nodes"] == 25
    assert model["proof_resource_limited"] is True
    assert model["proof_limit_reason"] == assessment.LIMIT_REASON
    assert record["supplemental"]["curve"]["grade"] == "A"
    for field in ("domain", "original_family", "continuous_extension", "remainder"):
        proof = record["supplemental"][field]
        assert proof["status"] == "unresolved"
        assert proof["reason"] == assessment.LIMIT_REASON
    assert record["supplemental"]["new_parameter_match"]["status"] == "not_assessed"
    # This is a limit on proving the derived model, not an invalid native q.
    enlarged = op("+", tree, op("*", q(0), T))
    assert assessment.node_count(enlarged) == 21
    with pytest.raises(InvalidTreeError, match="20-node"):
        assessment.physical_tree(enlarged, 32)


def write(directory, name, value):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(sources.json_bytes(value))


def artifacts(directory, tree=None, status="completed"):
    write(directory, "worker/metadata.json", {"fit_wall_seconds": 10.0})
    write(directory, "worker/status.json", {"total_wall_seconds": 12.0})
    write(directory, "timing.json", {"run_seconds": 14.0})
    write(
        directory,
        "outcome.json",
        {
            "status": status,
            "failure_kind": "fit_error" if status == "worker_failed" else None,
            "resources": {"cpu_user_seconds": 8.0, "cpu_system_seconds": 1.0},
            "stop": {
                "reason": "iteration_limit",
                "clock": {"completed_outer_rounds": 2},
            },
        },
    )
    if tree is not None:
        write(directory, "worker/result.json", front(tree))
        write(directory, "verified.json", {"callback_calls_during_fit": 45})


def test_cell_record_keeps_original_and_costs_and_reports_proof_limits(tmp_path):
    arrays, grid = inputs()
    tree = op("+", op("+", core(), op("*", q(0), T)), op("*", q(0), T))
    artifacts(tmp_path, tree)
    saved = (tmp_path / "worker/result.json").read_bytes()
    record = assessment.cell_record(tmp_path, {"arm": "U"}, arrays, grid)
    assert record["A"] is True and record["A_and_original_family"] is False
    assert record["physical_proof_resource_limited"] is True
    assert record["front_physical_proof_resource_limited"] == 1
    assert record["selected"] == front(tree)["candidates"][0]
    assert record["completed_outer_rounds"] == 2
    assert record["costs"] == {
        "worker_wall_seconds": 12.0,
        "fit_wall_seconds": 10.0,
        "cpu_user_seconds": 8.0,
        "cpu_system_seconds": 1.0,
        "callback_calls_during_fit": 45,
        "adapter_call_wall_seconds": 14.0,
    }
    assert (tmp_path / "worker/result.json").read_bytes() == saved


def test_failed_cell_retains_unknown_cost_and_no_success(tmp_path):
    arrays, grid = inputs()
    artifacts(tmp_path, status="worker_failed")
    write(tmp_path, "worker/metadata.json", {})
    record = assessment.cell_record(tmp_path, {"arm": "T"}, arrays, grid)
    assert record["status"] == "worker_failed"
    assert record["A"] is False and record["A_and_original_family"] is False
    assert record["costs"]["fit_wall_seconds"] is None
    assert record["costs"]["callback_calls_during_fit"] is None
    assert record["costs"]["worker_wall_seconds"] == 12
    assert record["stop"] == "fit_error"
    assert record["original_family_status"] == "no_output"


@pytest.mark.parametrize("status", ["planned", "aborted", "running"])
def test_unfinished_cells_cannot_be_reported_as_failures(tmp_path, status):
    arrays, grid = inputs()
    artifacts(tmp_path, status=status)
    with pytest.raises(ValueError, match="Incomplete planned"):
        assessment.cell_record(tmp_path, {"arm": "T"}, arrays, grid)


def test_invalid_cost_remains_a_release_error(tmp_path):
    arrays, grid = inputs()
    artifacts(tmp_path, status="worker_failed")
    write(tmp_path, "timing.json", {"run_seconds": -1})
    with pytest.raises(ValueError, match="Invalid measured cost"):
        assessment.cell_record(tmp_path, {"arm": "T"}, arrays, grid)
