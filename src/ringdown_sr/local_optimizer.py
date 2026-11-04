"""Bound unrestricted local-iteration/restart factorial experiment."""

import copy
import re
from collections import Counter
from dataclasses import asdict
from statistics import median

from . import search_duration as prior
from . import trigonometric_grammar as grammar
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .symbolic import ROOT, SearchBudget

FORMAT = "ringdown-sr-local-optimizer-1"
PROFILE_FORMAT = "ringdown-sr-local-optimizer-profile-1"
PLAN = "docs/local_optimizer_plan.md"
PLAN_COMMIT = "e7b457bf8927cdd1b52c51bb3457b54d0c88f066"
PLAN_SHA256 = "793006863a739a973dd3ffcf82c6e665f1a77da7eefee4132555843230df7f47"
SEEDS = (20261120, 20261121, 20261122, 20261123, 20261124)
PROFILES = {
    "local_100_2": (100, 2),
    "local_300_2": (300, 2),
    "local_100_5": (100, 5),
    "local_300_5": (300, 5),
}
CONDITIONS = tuple(PROFILES)
NATIVE_MODULE = "LocalOptimizerBudget"
OBJECTIVE = "Main.LocalOptimizerBudget.objective"
LIMIT_SECONDS, WORKER_LIMIT_SECONDS = 7200, 600
RUNTIME = {
    **prior.RUNTIME,
    "worker.py": "scripts/run_local_optimizer_worker.py",
    "duration_worker.py": "scripts/run_search_duration_worker.py",
    "backend.py": "scripts/check_local_optimizer_backend.py",
    "LocalOptimizerBudget.jl": "julia/src/LocalOptimizerBudget.jl",
}
load_module = prior.load_module
selected = prior.selected
supported_reconstruction = prior.supported_reconstruction
ITERATION_FIELD = r"(?<=[(,])\s*iterations\s*=\s*(\d+)\s*(?=,)"


def source_hashes():
    hashes = prior.source_hashes()
    for name in (
        PLAN,
        *RUNTIME.values(),
        "src/ringdown_sr/local_optimizer.py",
        "scripts/run_local_optimizer.py",
        "scripts/check_local_optimizer_integration.py",
        "scripts/check_local_optimizer_native.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen local optimizer plan changed.")
    return dict(sorted(hashes.items()))


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or not isinstance(document["condition"], str)
        or document["condition"] not in PROFILES
    ):
        raise ValueError("Invalid local optimizer profile.")
    return document["condition"]


def planned_cells():
    orders = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1), (0, 1, 3, 2))
    cells = []
    for seed, order in zip(SEEDS, orders, strict=True):
        for index in order:
            condition = CONDITIONS[index]
            number = len(cells) + 1
            cells.append(
                {
                    "number": number,
                    "directory": f"cell-{number:02d}",
                    "condition": condition,
                    "arm": condition,
                    "grammar": "unrestricted",
                    "budget": asdict(SearchBudget(seed=seed, niterations=200)),
                    "status": "planned",
                }
            )
    return cells


def profile_parameters(budget, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    iterations, restarts = PROFILES[condition]
    return {
        **prior.profile_parameters(budget, "unrestricted"),
        "loss_function": OBJECTIVE,
        "optimizer_iterations": iterations,
        "optimizer_nrestarts": restarts,
    }


def search_profiles():
    return [
        {
            "number": c["number"],
            "condition": c["condition"],
            "budget": c["budget"],
            "parameters": profile_parameters(
                SearchBudget(**c["budget"]), c["condition"]
            ),
        }
        for c in planned_cells()
    ]


def _normalized(record, condition, support):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    iterations, restarts = PROFILES[condition]
    fields = support.backend_without_output(record["backend_options"])
    names = (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    if (
        record.get("condition") != condition
        or record["optimizer_settings"].get("iterations") != str(iterations)
        or fields.get("optimizer_nrestarts")
        != {"type": "Int64", "value": str(restarts)}
        or re.findall(
            ITERATION_FIELD, fields.get("optimizer_options", {}).get("value", "")
        )
        != [str(iterations)]
        or fields.get("loss_function")
        not in [{"type": f"typeof({name})", "value": name} for name in names]
    ):
        raise ValueError("Wrong native local optimizer profile or objective.")
    normalized = copy.deepcopy(record)
    normalized["condition"] = "unrestricted"
    normalized["optimizer_settings"]["iterations"] = "100"
    for field in normalized["backend_options"]:
        if field["name"] == "optimizer_options":
            field["value"] = re.sub(
                ITERATION_FIELD, " iterations = 100", field["value"]
            )
        elif field["name"] == "optimizer_nrestarts":
            field["value"] = "2"
        elif field["name"] == "loss_function":
            field.update(type=f"typeof({grammar.OBJECTIVE})", value=grammar.OBJECTIVE)
    return normalized


def verify_options(record, seed, condition, base, support):
    normalized = _normalized(record, condition, support)
    return prior.verify_options(normalized, seed, "unrestricted", base, support)


def common_options(record, support):
    return prior.common_options(
        _normalized(record, record["condition"], support), support
    )


def common_parameters(parameters):
    return {
        k: v
        for k, v in parameters.items()
        if k not in {"random_state", "optimizer_iterations", "optimizer_nrestarts"}
    }


def verify_tree_grammar(tree, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return grammar.verify_tree_grammar(tree, "unrestricted")


def expected_grammar_cases():
    return [
        {**case, "condition": condition}
        for condition in CONDITIONS
        for case in grammar.expected_grammar_cases()
        if case["condition"] == "unrestricted"
    ]


def verify_manifest(directory, runtime):
    module = load_module(
        ROOT / "src/ringdown_sr/trigonometric_grammar.py", "ringdown_sr._local_manifest"
    )
    module.FORMAT, module.source_hashes, module.RUNTIME = FORMAT, source_hashes, RUNTIME
    return module.verify_manifest(directory, runtime)


def invocation_record(iterations):
    return {**prior.invocation_record(iterations), "format": FORMAT}


class SearchInvocationGuard(prior.SearchInvocationGuard):
    def record(self):
        return {**super().record(), "format": FORMAT}


def _costs(cell):
    return {
        "worker_wall_seconds_scope": "worker_launch_and_parent_verification",
        **{
            key: cell["diagnostics"].get(key)
            for key in (
                "timing_seconds",
                "worker_wall_seconds",
                "callback_calls_during_fit",
                "callback_calls_total",
                "backend_evaluation_counter",
            )
        },
    }


def comparison(cells, *, final_verified):
    result = {"summaries": None, "pair_differences": None, "comparison": None}
    if (
        not final_verified
        or len(cells) != 20
        or any(c["status"] != "completed" for c in cells)
    ):
        return result
    for cell, expected in zip(cells, planned_cells(), strict=True):
        if any(
            cell[k] != expected[k]
            for k in ("number", "directory", "condition", "arm", "grammar", "budget")
        ):
            raise ValueError("Wrong completed local optimizer cell identity or order.")
    summaries = {}
    for condition, (iterations, restarts) in PROFILES.items():
        group = [c for c in cells if c["condition"] == condition]
        chosen = [selected(c) for c in group]
        statistics = {}
        for name in _metrics(chosen[0]):
            values = [
                v
                for c in chosen
                if _metric_availability(c, name, v := _metrics(c)[name])["status"]
                == "available"
            ]
            statistics[name] = {
                "finite_count": len(values),
                "planned_count": 5,
                "minimum": min(values) if values else None,
                "median": median(values) if values else None,
                "maximum": max(values) if values else None,
            }
        summaries[condition] = {
            "grammar": "unrestricted",
            "niterations": 200,
            "optimizer_iterations": iterations,
            "optimizer_nrestarts": restarts,
            "count": 5,
            "statistics": statistics,
            "curve_successes": sum(
                c["curve_marker"] == "within_tolerance" for c in chosen
            ),
            "supported_reconstructions": sum(map(supported_reconstruction, chosen)),
            "markers": {
                k: dict(Counter(_markers(c)[k] for c in chosen))
                for k in ("curve", "structure", "parameters")
            },
            "cost_by_seed": [{"seed": c["budget"]["seed"], **_costs(c)} for c in group],
            "unselected_curve_successes": sum(
                d["curve_marker"] == "within_tolerance" and not d["is_selected"]
                for c in group
                for d in c["diagnostics"]["candidates"]
            ),
        }
    indexed = {(c["condition"], c["budget"]["seed"]): c for c in cells}
    b, i, r, x = CONDITIONS
    definitions = (
        ("iterations_at_2_restarts", b, i, "optimizer_iterations", 2),
        ("iterations_at_5_restarts", r, x, "optimizer_iterations", 5),
        ("restarts_at_100_iterations", b, r, "optimizer_nrestarts", 100),
        ("restarts_at_300_iterations", i, x, "optimizer_nrestarts", 300),
        ("combined_vs_baseline", b, x, "combined_profile", None),
    )
    pairs, contrasts = [], {}
    for name, left, right, factor, fixed in definitions:
        paired = [
            {
                "contrast": name,
                **prior.pair_record(
                    indexed[left, seed],
                    indexed[right, seed],
                    factor=factor,
                    fixed=fixed,
                    seed=seed,
                ),
                "costs": {
                    "first": _costs(indexed[left, seed]),
                    "second": _costs(indexed[right, seed]),
                },
            }
            for seed in SEEDS
        ]
        low, high = (summaries[k]["curve_successes"] for k in (left, right))
        gained = sum(
            not p["success_first"] and p["success_second"] and p["supported_second"]
            for p in paired
        )
        contrasts[name] = {
            "first_profile": left,
            "second_profile": right,
            "C_first": low,
            "C_second": high,
            "difference": high - low,
            "transitions": prior.transition_counts(paired),
            "new_supported_gains": gained,
            "development_signal": "supported_structure_gain"
            if high > low and gained
            else "approximation_gain_only"
            if high > low
            else "hypothesis_not_supported",
        }
        pairs.extend(paired)
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "contrasts": contrasts,
            "baseline_contrasts": [
                "iterations_at_2_restarts",
                "restarts_at_100_iterations",
                "combined_vs_baseline",
            ],
            "count_interaction": contrasts["iterations_at_5_restarts"]["difference"]
            - contrasts["iterations_at_2_restarts"]["difference"],
            "scope": "five fresh paired seeds on one adaptively studied signal; fixed outer budget 200; no general validation or physical identification",
        },
    )
    return copy.deepcopy(result)
