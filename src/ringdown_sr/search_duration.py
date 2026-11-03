"""Frozen outer-search budgets, isolated adapters and descriptive paired endpoints."""

import copy
import importlib.machinery
import importlib.util
import math
from collections import Counter
from dataclasses import asdict
from statistics import median

from . import trigonometric_grammar as grammar
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .symbolic import ROOT, SearchBudget

FORMAT = "ringdown-sr-search-duration-2"
PROFILE_FORMAT = "ringdown-sr-search-duration-profile-2"
PLAN = "docs/search_duration_verification_plan.md"
PLAN_COMMIT = "2a0b50926cd2983d0cd6cc1307ccc28d0a2822fa"
PLAN_SHA256 = "b6f7cef2227eeacccf8156d02e8899e6fc83b7bd1f29735c1a402922a9d83062"
ORIGINAL_PLAN = "docs/search_duration_plan.md"
ORIGINAL_PLAN_SHA256 = (
    "8906a66930848d733e5b2744d40c5fa9c4051db2b876e200908d74ae9ac0b75d"
)
TABLE_NOTE = "docs/search_duration_table_loss_note.md"
TABLE_NOTE_COMMIT = "fee62058992c84a9930aa765233ebdc095c54cb1"
TABLE_NOTE_SHA256 = "56c0807127ff208148df9057607c698218bf87b0cdcf73471b58add14485372c"
SEEDS = (20261103, 20261104, 20261105, 20261106, 20261107)
ITERATIONS = (200, 2000)
CONDITIONS = grammar.CONDITIONS
LIMIT_SECONDS = 7200
WORKER_LIMIT_SECONDS = 600
RUNTIME = {
    **grammar.RUNTIME,
    "grammar_worker.py": "scripts/run_trigonometric_grammar_worker.py",
    "grammar_backend.py": "scripts/check_trigonometric_grammar_backend.py",
    "worker.py": "scripts/run_search_duration_worker.py",
    "backend.py": "scripts/check_search_duration_backend.py",
}


class SourceBytesLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return self.source_to_code(self.get_data(self.path), self.path)


def load_module(path, name):
    """Execute source bytes in a fresh namespace, never cached runtime bytecode."""
    spec = importlib.util.spec_from_file_location(
        name, path, loader=SourceBytesLoader(name, str(path))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_hashes():
    hashes = grammar.source_hashes()
    for name in (
        PLAN,
        ORIGINAL_PLAN,
        TABLE_NOTE,
        *RUNTIME.values(),
        "scripts/run_search_duration.py",
        "scripts/check_search_duration_integration.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen search duration plan changed.")
    if hashes[ORIGINAL_PLAN] != ORIGINAL_PLAN_SHA256:
        raise ValueError("The original search duration plan changed.")
    if hashes[TABLE_NOTE] != TABLE_NOTE_SHA256:
        raise ValueError("The bound CSV loss clarification changed.")
    return dict(sorted(hashes.items()))


def planned_cells():
    combinations = [
        (CONDITIONS[0], 200),
        (CONDITIONS[1], 200),
        (CONDITIONS[0], 2000),
        (CONDITIONS[1], 2000),
    ]
    orders = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1), (0, 1, 3, 2))
    cells = []
    for seed, order in zip(SEEDS, orders, strict=True):
        for index in order:
            condition, iterations = combinations[index]
            number = len(cells) + 1
            cells.append(
                {
                    "number": number,
                    "directory": f"cell-{number:02d}",
                    "condition": condition,
                    "arm": condition,
                    "budget": asdict(SearchBudget(seed=seed, niterations=iterations)),
                    "status": "planned",
                }
            )
    return cells


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or document["condition"] not in CONDITIONS
    ):
        raise ValueError("Invalid search duration grammar profile.")
    return document["condition"]


profile_parameters = grammar.profile_parameters
verify_options = grammar.verify_options
common_options = grammar.common_options
verify_tree_grammar = grammar.verify_tree_grammar
supported_reconstruction = grammar.supported_reconstruction


def search_profiles():
    return [
        {
            "number": cell["number"],
            "condition": cell["condition"],
            "budget": cell["budget"],
            "parameters": profile_parameters(
                SearchBudget(**cell["budget"]), cell["condition"]
            ),
        }
        for cell in planned_cells()
    ]


def verify_manifest(directory, runtime):
    # Keep the existing strict manifest contract in a separate namespace.
    module = load_module(
        ROOT / "src/ringdown_sr/trigonometric_grammar.py",
        "ringdown_sr._duration_manifest",
    )
    module.FORMAT = FORMAT
    module.source_hashes = source_hashes
    module.RUNTIME = RUNTIME
    return module.verify_manifest(directory, runtime)


class SearchInvocationGuard:
    """Pass through the pinned PySR/Julia call unchanged and bind its outer budget."""

    def __init__(self, backend, iterations):
        if type(iterations) is not int or iterations <= 0:
            raise ValueError("Invalid requested search iteration count.")
        self.backend = backend
        self.iterations = iterations
        self.calls = 0
        self.completed = False

    def __getattr__(self, name):
        if name == "equation_search":
            return self
        return getattr(self.backend, name)

    def _jl_call_nogil(self, *args, **kwargs):
        if (
            self.calls != 0
            or len(args) != 2
            or type(kwargs.get("niterations")) is not int
            or kwargs["niterations"] != self.iterations
            or kwargs.get("parallelism") != "serial"
            or kwargs.get("return_state") is not True
            or any(
                key not in kwargs or kwargs[key] is not None
                for key in ("saved_state", "guesses", "weights")
            )
        ):
            raise ValueError("Unexpected actual equation_search invocation.")
        self.calls += 1
        result = self.backend.equation_search._jl_call_nogil(*args, **kwargs)
        self.completed = True
        return result

    def record(self):
        if self.calls != 1 or not self.completed:
            raise ValueError("Missing completed equation_search invocation.")
        return invocation_record(self.iterations)


def invocation_record(iterations):
    return {
        "format": FORMAT,
        "status": "verified",
        "call_count": 1,
        "niterations": iterations,
        "parallelism": "serial",
        "return_state": True,
        "saved_state": None,
        "guesses": None,
        "weights": None,
        "arguments_and_result": "delegated_unchanged",
    }


def common_parameters(parameters):
    return {
        k: v
        for k, v in parameters.items()
        if k not in {"random_state", "nested_constraints", "niterations"}
    }


def selected(cell):
    d = cell["diagnostics"]
    return d["candidates"][d["selected_index"]]


def pair_record(first, second, *, factor, fixed, seed):
    left, right = selected(first), selected(second)
    metrics = {}
    for name, value in _metrics(left).items():
        other = _metrics(right)[name]
        a, b = (
            _metric_availability(left, name, value),
            _metric_availability(right, name, other),
        )
        available = a["status"] == b["status"] == "available"
        difference = other - value if available else None
        available = available and math.isfinite(difference)
        metrics[name] = {
            "first": value,
            "second": other,
            "availability_first": a,
            "availability_second": b,
            "difference": difference if available else None,
            "status": "available" if available else "not_assessed",
            "reason": None if available else "unavailable_or_out_of_range_metric",
        }
    return {
        "factor": factor,
        "fixed": fixed,
        "seed": seed,
        "first_cell": first["number"],
        "second_cell": second["number"],
        "markers_first": _markers(left),
        "markers_second": _markers(right),
        "success_first": left["curve_marker"] == "within_tolerance",
        "success_second": right["curve_marker"] == "within_tolerance",
        "supported_second": supported_reconstruction(right),
        "metrics": metrics,
    }


def comparison(cells, *, final_verified):
    result = {"summaries": None, "pair_differences": None, "comparison": None}
    expected = planned_cells()
    if (
        not final_verified
        or len(cells) != len(expected)
        or any(c["status"] != "completed" for c in cells)
    ):
        return result
    for cell, planned in zip(cells, expected, strict=True):
        if any(
            cell[key] != planned[key]
            for key in ("number", "directory", "condition", "arm", "budget")
        ):
            raise ValueError("Wrong completed search-duration cell identity or order.")
    costs = (
        "timing_seconds",
        "worker_wall_seconds",
        "callback_calls_during_fit",
        "callback_calls_total",
        "backend_evaluation_counter",
    )
    summaries = {}
    for condition in CONDITIONS:
        for iterations in ITERATIONS:
            group = [
                c
                for c in cells
                if c["condition"] == condition
                and c["budget"]["niterations"] == iterations
            ]
            chosen = [selected(c) for c in group]
            statistics = {}
            for name in _metrics(chosen[0]):
                values = [
                    v
                    for candidate in chosen
                    if _metric_availability(
                        candidate, name, v := _metrics(candidate)[name]
                    )["status"]
                    == "available"
                ]
                statistics[name] = {
                    "finite_count": len(values),
                    "planned_count": 5,
                    "minimum": min(values) if values else None,
                    "median": median(values) if values else None,
                    "maximum": max(values) if values else None,
                }
            summaries[f"{condition}/{iterations}"] = {
                "condition": condition,
                "niterations": iterations,
                "count": 5,
                "statistics": statistics,
                "curve_successes": sum(
                    c["curve_marker"] == "within_tolerance" for c in chosen
                ),
                "supported_reconstructions": sum(map(supported_reconstruction, chosen)),
                "markers": {
                    key: dict(Counter(_markers(c)[key] for c in chosen))
                    for key in ("curve", "structure", "parameters")
                },
                "cost_by_seed": [
                    {
                        "seed": c["budget"]["seed"],
                        **{k: c["diagnostics"].get(k) for k in costs},
                    }
                    for c in group
                ],
                "unselected_curve_successes": sum(
                    d["curve_marker"] == "within_tolerance" and not d["is_selected"]
                    for c in group
                    for d in c["diagnostics"]["candidates"]
                ),
            }

    def find(condition, iterations, seed):
        return next(
            c
            for c in cells
            if c["condition"] == condition
            and c["budget"]["niterations"] == iterations
            and c["budget"]["seed"] == seed
        )

    pairs = [
        pair_record(
            find(g, 200, seed),
            find(g, 2000, seed),
            factor="search_iterations",
            fixed=g,
            seed=seed,
        )
        for g in CONDITIONS
        for seed in SEEDS
    ]
    pairs += [
        pair_record(
            find(CONDITIONS[0], b, seed),
            find(CONDITIONS[1], b, seed),
            factor="grammar",
            fixed=b,
            seed=seed,
        )
        for b in ITERATIONS
        for seed in SEEDS
    ]
    budgets = {}
    for g in CONDITIONS:
        c_low, c_high = [summaries[f"{g}/{b}"]["curve_successes"] for b in ITERATIONS]
        paired = [
            p for p in pairs if p["factor"] == "search_iterations" and p["fixed"] == g
        ]
        new_supported = sum(
            not p["success_first"] and p["success_second"] and p["supported_second"]
            for p in paired
        )
        budgets[g] = {
            "C_200": c_low,
            "C_2000": c_high,
            "difference": c_high - c_low,
            "transitions": transition_counts(paired),
            "new_supported_gains": new_supported,
            "development_signal": "supported_structure_gain"
            if c_high > c_low and new_supported
            else "approximation_gain_only"
            if c_high > c_low
            else "hypothesis_not_supported",
        }
    grammar_differences = {
        str(b): summaries[f"{CONDITIONS[1]}/{b}"]["curve_successes"]
        - summaries[f"{CONDITIONS[0]}/{b}"]["curve_successes"]
        for b in ITERATIONS
    }
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "by_grammar": budgets,
            "grammar_count_differences": grammar_differences,
            "grammar_transitions": {
                str(b): transition_counts(
                    p for p in pairs if p["factor"] == "grammar" and p["fixed"] == b
                )
                for b in ITERATIONS
            },
            "count_interaction": budgets[CONDITIONS[1]]["difference"]
            - budgets[CONDITIONS[0]]["difference"],
            "scope": "five new seeds on one known development signal; no general validation or physical identification",
        },
    )
    return copy.deepcopy(result)


def transition_counts(pairs):
    counts = Counter(
        f"{int(p['success_first'])}->{int(p['success_second'])}" for p in pairs
    )
    return {key: counts[key] for key in ("0->0", "0->1", "1->0", "1->1")}
