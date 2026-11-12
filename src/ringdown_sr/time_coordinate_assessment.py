"""Assess physical compositions while preserving native search selections."""

import copy
from dataclasses import asdict

import numpy as np

from . import assessment_sources as sources
from . import future_assessment as future
from . import iteration_time as previous
from . import remainder_assessment as remainder
from . import structure_assessment as structure
from .structure import MAX_TREE_NODES, _validated_tree
from .structure_algebra import LIMITS
from .supplemental_assessment import grade_curve
from .symbolic import BINARY, evaluate_tree, select_candidate

LIMIT_REASON = "physical_composition_exceeds_exported_tree_limit"
MODEL = "exact_real_physical_composition"


def checked_scale(scale):
    if type(scale) not in (int, float) or scale not in (1, 32):
        raise ValueError("Only the frozen coordinate scales 1 and 32 are allowed.")
    return float(scale)


def physical_tree(tree, scale):
    """Substitute each original variable once, without rewriting any operator."""
    scale = checked_scale(scale)
    _validated_tree(tree)

    def visit(node):
        if node["kind"] == "variable" and scale != 1:
            return {
                "kind": "operator",
                "operator": "*",
                "arity": 2,
                "operator_index": BINARY.index("*") + 1,
                "children": [
                    {"kind": "constant", "value_hex": scale.hex()},
                    copy.deepcopy(node),
                ],
            }
        result = copy.deepcopy(node)
        if node["kind"] == "operator":
            result["children"] = [visit(child) for child in node["children"]]
        return result

    return visit(tree)


def node_count(tree):
    return 1 + sum(node_count(child) for child in tree.get("children", []))


def physical_model(tree, scale, binding):
    scale = checked_scale(scale)
    transformed = physical_tree(tree, scale)
    count = node_count(transformed)
    limited = count > MAX_TREE_NODES
    return {
        "tree": transformed,
        "source_tree_sha256": sources.sha256(sources.json_bytes(tree)),
        "tree_sha256": sources.sha256(sources.json_bytes(transformed)),
        "scale_hex": scale.hex(),
        "rule": "substitute_original_variable_once_with_scale_times_physical_time",
        "physical_time_unit": "seconds",
        "search_time_unit": "seconds",
        "interval": binding,
        "original_nodes": node_count(tree),
        "physical_nodes": count,
        "exported_tree_node_limit": MAX_TREE_NODES,
        "proof_resource_limited": limited,
        "proof_limit_reason": LIMIT_REASON if limited else None,
    }


def paired_endpoint(tree, model, times, truth, scale):
    """Check binary64 replay equivalence before using a physical diagnostic."""
    search_times = np.ldexp(times, 5) if scale == 32 else np.array(times, copy=True)
    predictions, failures = [], []
    for expression, coordinates in ((tree, search_times), (model, times)):
        try:
            predictions.append(evaluate_tree(expression, coordinates))
            failures.append(None)
        except (ValueError, OverflowError, FloatingPointError) as error:
            predictions.append(None)
            failures.append(error)
    if (failures[0] is None) != (failures[1] is None):
        raise ValueError("Physical composition changed prediction availability.")
    evidence = {
        "physical_times": sources.fingerprint(times),
        "search_times": sources.fingerprint(search_times),
        "physical_prediction": None,
        "search_prediction": None,
    }
    if failures[0] is not None:
        evidence["status"] = "both_unavailable"
        return {
            "status": "not_available",
            "reason": str(failures[1]),
            "relative_rms": None,
            "relative_max": None,
        }, evidence
    if sources.fingerprint(predictions[0]) != sources.fingerprint(predictions[1]):
        raise ValueError("Physical composition changed exact prediction bits.")
    evidence.update(
        status="identical_finite",
        physical_prediction=sources.fingerprint(predictions[1]),
        search_prediction=sources.fingerprint(predictions[0]),
    )
    return future.prediction_endpoint(predictions[1], truth), evidence


def supplement(record, binding, references):
    """Use unchanged proof limits and bind their subject to the composition."""
    model = record["physical_model"]
    if model["proof_resource_limited"]:
        proof = {
            "structure_proof_format": structure.FORMAT,
            "limits": asdict(LIMITS),
            **{
                field: {"status": "unresolved", "reason": LIMIT_REASON}
                for field in (
                    "algebraic_identity",
                    "domain",
                    "original_family",
                    "continuous_extension",
                    "remainder",
                )
            },
            "coefficients_exact": None,
            "coefficient_sign_proofs": [],
            "proof_trace": [],
            "new_parameter_match": {"status": "not_assessed"},
        }
        proof["domain"].update(
            interval=binding,
            exclusions=[],
            nonempty_dense_original_domain_proven=False,
        )
        proof["remainder"]["evaluation_model"] = MODEL
        record["supplemental"].update(proof)
    else:
        # The proof helpers accept an original-tree record. Give them a private
        # composition record, then retain only its explicitly bound diagnoses.
        temporary = {
            "original_candidate": {"tree": model["tree"]},
            "supplemental": {},
        }
        structure.supplement(temporary, binding)
        remainder.supplement(temporary, binding, references)
        temporary["supplemental"]["remainder"]["evaluation_model"] = MODEL
        record["supplemental"].update(temporary["supplemental"])
    record["supplemental"]["model_binding"] = {
        "evaluation_model": MODEL,
        "tree_sha256": model["tree_sha256"],
        "source_tree_sha256": model["source_tree_sha256"],
        "scale_hex": model["scale_hex"],
        "interval": binding,
    }
    record["supplemental"]["remainder"]["physical_model_sha256"] = model["tree_sha256"]


def assess_front(front, arrays, grid, scale):
    """Retain native identities and selections; diagnose their physical models."""
    scale = checked_scale(scale)
    selected = front["selected_index"]
    if type(selected) is not int or selected != select_candidate(front["candidates"]):
        raise ValueError("Original native-loss selection changed.")
    binding = structure.interval_binding(arrays["time_s"])
    references = {
        "training": {"time_s": arrays["time_s"], "truth": arrays["observed"]},
        "diagnostic": {
            "time_s": arrays["diagnostic_time_s"],
            "truth": arrays["diagnostic_truth"],
        },
    }
    records = []
    for index, candidate in enumerate(front["candidates"]):
        model = physical_model(candidate["tree"], scale, binding)
        endpoints, replay = {}, {}
        for role, values in {**references, "irregular": grid}.items():
            endpoints[role], replay[role] = paired_endpoint(
                candidate["tree"],
                model["tree"],
                values["time_s"],
                values["truth"],
                scale,
            )
        errors = {role: endpoints[role] for role in references}
        record = {
            "source_identity": {
                "original_index": index,
                "original_selected_index": selected,
                "source_candidate_sha256": sources.sha256(
                    sources.json_bytes(candidate)
                ),
            },
            "original_candidate": copy.deepcopy(candidate),
            "physical_model": model,
            "coordinate_replay": replay,
            "curve_errors": errors,
            "irregular_errors": endpoints["irregular"],
            "supplemental": {"curve": grade_curve(errors, source_verified=True)},
        }
        supplement(record, binding, references)
        records.append(record)
    return records


def cell_record(directory, plan, arrays, grid):
    """Read all original outcome and cost fields before physical assessment."""
    if plan["arm"] not in ("T", "U"):
        raise ValueError("Unknown time-coordinate arm.")
    outcome = previous.load_json(directory, "outcome.json")
    metadata = previous.load_json(directory, "worker/metadata.json")
    status = previous.load_json(directory, "worker/status.json")
    costs = {field: None for field in previous.COST_FIELDS}
    costs.update(
        worker_wall_seconds=status.get("total_wall_seconds"),
        fit_wall_seconds=metadata.get("fit_wall_seconds"),
        adapter_call_wall_seconds=previous.load_json(directory, "timing.json")[
            "run_seconds"
        ],
    )
    resource = outcome["resources"]
    costs.update(
        {key: resource[key] for key in ("cpu_user_seconds", "cpu_system_seconds")}
    )
    record = {
        "plan": plan,
        "reused": False,
        "status": outcome["status"],
        "outcome": outcome,
        "costs": costs,
        "worker_process_resources": resource,
        "cost_scope": "worker/status.json total_wall_seconds: parent setup, worker launch/wait and result read; excludes adapter diagnostics",
        "compilation_seconds": "not_observed",
        "completed_outer_rounds": None,
        "stop": outcome.get("failure_kind"),
        "A": False,
        "A_and_original_family": False,
        "curve_grade": "no_output",
        "original_family_status": "no_output",
        "physical_proof_resource_limited": False,
        "front_physical_proof_resource_limited": 0,
    }
    if outcome["status"] == "completed":
        verified = previous.load_json(directory, "verified.json")
        front = previous.load_json(directory, "worker/result.json")
        assessments = assess_front(front, arrays, grid, 32 if plan["arm"] == "U" else 1)
        index = front["selected_index"]
        selected = assessments[index]
        grade = selected["supplemental"]["curve"]["grade"]
        family = selected["supplemental"]["original_family"]["status"]
        record.update(
            selected=front["candidates"][index],
            selected_assessment=selected,
            front_assessments=assessments,
            curve_grade=grade,
            original_family_status=family,
            A=grade == "A",
            A_and_original_family=grade == "A" and family == "proven_member",
            any_front_A=any(
                r["supplemental"]["curve"]["grade"] == "A" for r in assessments
            ),
            source_result_sha256=sources.sha256(
                (directory / "worker/result.json").read_bytes()
            ),
            stop=outcome["stop"]["reason"],
            completed_outer_rounds=outcome["stop"]["clock"]["completed_outer_rounds"],
            physical_proof_resource_limited=selected["physical_model"][
                "proof_resource_limited"
            ],
            front_physical_proof_resource_limited=sum(
                r["physical_model"]["proof_resource_limited"] for r in assessments
            ),
        )
        costs["callback_calls_during_fit"] = verified["callback_calls_during_fit"]
    elif outcome["status"] != "worker_failed":
        raise ValueError("Incomplete planned time-coordinate cell.")
    previous.cost_totals([record])
    return record
