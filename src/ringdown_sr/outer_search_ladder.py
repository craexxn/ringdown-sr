"""Bound outer search budgets with one fixed native 300/5 profile."""

import copy
import math
from collections import Counter
from dataclasses import asdict
from statistics import median

from . import local_optimizer as prior
from . import search_duration as duration
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .symbolic import ROOT, SearchBudget

FORMAT = "ringdown-sr-outer-search-ladder-1"
PROFILE_FORMAT = "ringdown-sr-outer-search-ladder-profile-1"
PLAN = "docs/outer_search_ladder_plan.md"
PLAN_COMMIT = "e1ea601286042aadcc5b5291ae72d114c7846dbf"
PLAN_SHA256 = "95aca0069d6b8a6ad0305d5722c558e4bbea1c23e7f3b70630d2eb33e816fa35"
SEEDS = (20261201, 20261202, 20261203, 20261204, 20261205)
ITERATIONS = (200, 500, 2000, 5000)
CONDITIONS = ("local_300_5",)
NATIVE_MODULE, OBJECTIVE = prior.NATIVE_MODULE, prior.OBJECTIVE
LIMIT_SECONDS, WORKER_LIMIT_SECONDS = 14400, 1800
RUNTIME = {
    **prior.RUNTIME,
    "worker.py": "scripts/run_outer_search_ladder_worker.py",
    "backend.py": "scripts/check_outer_search_ladder_backend.py",
}
load_module = prior.load_module
selected = prior.selected
supported_reconstruction = prior.supported_reconstruction


def source_hashes():
    hashes = prior.source_hashes()
    for name in (
        PLAN,
        *RUNTIME.values(),
        "src/ringdown_sr/outer_search_ladder.py",
        "scripts/run_outer_search_ladder.py",
        "scripts/check_outer_search_ladder_integration.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen outer search ladder plan changed.")
    return dict(sorted(hashes.items()))


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or document["condition"] != "local_300_5"
    ):
        raise ValueError("Expected the fixed local 300/5 profile.")
    return "local_300_5"


def planned_cells():
    orders = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1), (0, 1, 3, 2))
    cells = []
    for seed, order in zip(SEEDS, orders, strict=True):
        for index in order:
            number = len(cells) + 1
            cells.append(
                {
                    "number": number,
                    "directory": f"cell-{number:02d}",
                    "condition": "local_300_5",
                    "arm": "local_300_5",
                    "grammar": "unrestricted",
                    "budget": asdict(
                        SearchBudget(seed=seed, niterations=ITERATIONS[index])
                    ),
                    "status": "planned",
                }
            )
    return cells


def profile_parameters(budget, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return prior.profile_parameters(budget, condition)


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


def verify_options(record, seed, condition, base, support):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return prior.verify_options(record, seed, condition, base, support)


def common_parameters(parameters):
    return {
        k: v for k, v in parameters.items() if k not in {"random_state", "niterations"}
    }


def common_options(record, support):
    checked_profile({"format": PROFILE_FORMAT, "condition": record["condition"]})
    return prior.common_options(record, support)


def verify_tree_grammar(tree, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return prior.verify_tree_grammar(tree, condition)


def expected_grammar_cases():
    return [
        c for c in prior.expected_grammar_cases() if c["condition"] == "local_300_5"
    ]


def verify_manifest(directory, runtime):
    module = load_module(
        ROOT / "src/ringdown_sr/trigonometric_grammar.py",
        "ringdown_sr._ladder_manifest",
    )
    module.FORMAT, module.source_hashes, module.RUNTIME = FORMAT, source_hashes, RUNTIME
    return module.verify_manifest(directory, runtime)


def invocation_record(iterations):
    return {**prior.invocation_record(iterations), "format": FORMAT}


class SearchInvocationGuard(prior.SearchInvocationGuard):
    def record(self):
        return {**super().record(), "format": FORMAT}


def _cost_change(first, second):
    def finite(x):
        return type(x) in (int, float) and math.isfinite(x)

    difference = second - first if finite(first) and finite(second) else None
    ratio = second / first if finite(first) and finite(second) and first > 0 else None
    return {
        "first": first,
        "second": second,
        "difference": difference if finite(difference) else None,
        "ratio": ratio if finite(ratio) else None,
        "difference_status": "available" if finite(difference) else "not_assessed",
        "ratio_status": "available" if finite(ratio) else "not_assessed",
    }


def _transitions(pairs, first, second):
    return {
        f"{a}->{b}": sum(p[first] == bool(a) and p[second] == bool(b) for p in pairs)
        for a in (0, 1)
        for b in (0, 1)
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
            raise ValueError("Wrong completed outer ladder cell identity or order.")
    summaries = {}
    for iterations in ITERATIONS:
        group = [c for c in cells if c["budget"]["niterations"] == iterations]
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
        summaries[str(iterations)] = {
            "grammar": "unrestricted",
            "niterations": iterations,
            "optimizer_iterations": 300,
            "optimizer_nrestarts": 5,
            "count": 5,
            "curve_successes": sum(
                c["curve_marker"] == "within_tolerance" for c in chosen
            ),
            "supported_reconstructions": sum(map(supported_reconstruction, chosen)),
            "markers": {
                k: dict(Counter(_markers(c)[k] for c in chosen))
                for k in ("curve", "structure", "parameters")
            },
            "statistics": statistics,
            "cost_by_seed": [
                {"seed": c["budget"]["seed"], **prior._costs(c)} for c in group
            ],
            "unselected_curve_successes": sum(
                d["curve_marker"] == "within_tolerance" and not d["is_selected"]
                for c in group
                for d in c["diagnostics"]["candidates"]
            ),
        }
    indexed = {(c["budget"]["niterations"], c["budget"]["seed"]): c for c in cells}
    pairs, contrasts = [], {}
    for low, high in ((200, 500), (500, 2000), (2000, 5000), (200, 2000), (200, 5000)):
        name = f"{high}_minus_{low}"
        paired = []
        for seed in SEEDS:
            left, right = indexed[low, seed], indexed[high, seed]
            costs = {"first": prior._costs(left), "second": prior._costs(right)}
            paired.append(
                {
                    "contrast": name,
                    **duration.pair_record(
                        left,
                        right,
                        factor="niterations",
                        fixed="local_300_5",
                        seed=seed,
                    ),
                    "supported_first": supported_reconstruction(selected(left)),
                    "costs": costs,
                    "cost_changes": {
                        "worker_wall_seconds": _cost_change(
                            costs["first"]["worker_wall_seconds"],
                            costs["second"]["worker_wall_seconds"],
                        ),
                        "fit_including_jit_and_python_exports": _cost_change(
                            *[
                                (costs[side]["timing_seconds"] or {}).get(
                                    "fit_including_jit_and_python_exports"
                                )
                                for side in ("first", "second")
                            ]
                        ),
                        "callback_calls_during_fit": _cost_change(
                            costs["first"]["callback_calls_during_fit"],
                            costs["second"]["callback_calls_during_fit"],
                        ),
                    },
                }
            )
        a, b = summaries[str(low)], summaries[str(high)]
        dc, ds = (b[k] - a[k] for k in ("curve_successes", "supported_reconstructions"))
        contrasts[name] = {
            "niterations_first": low,
            "niterations_second": high,
            "C_first": a["curve_successes"],
            "C_second": b["curve_successes"],
            "S_first": a["supported_reconstructions"],
            "S_second": b["supported_reconstructions"],
            "curve_difference": dc,
            "supported_difference": ds,
            "curve_transitions": _transitions(
                paired, "success_first", "success_second"
            ),
            "supported_transitions": _transitions(
                paired, "supported_first", "supported_second"
            ),
            "count_outcome": "curve_and_supported_count_gain"
            if dc > 0 and ds > 0
            else "supported_count_gain_only"
            if ds > 0
            else "curve_count_gain_only"
            if dc > 0
            else "no_count_gain",
        }
        pairs.extend(paired)
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "contrasts": contrasts,
            "baseline_contrasts": ["500_minus_200", "2000_minus_200", "5000_minus_200"],
            "adjacent_contrasts": [
                "500_minus_200",
                "2000_minus_500",
                "5000_minus_2000",
            ],
            "scope": "five fresh paired seeds on one adaptively studied signal; fixed local 300/5; separate curve and supported-selection counts; no automatic winner or physical identification",
        },
    )
    return copy.deepcopy(result)
