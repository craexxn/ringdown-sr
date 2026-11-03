"""Frozen single-factor grammar comparison and fail-closed profile validation."""

import ast
import copy
import math
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import median

from . import free_optimizer_budget as prior
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .symbolic import ROOT, SearchBudget

FORMAT = "ringdown-sr-trigonometric-grammar-1"
PROFILE_FORMAT = "ringdown-sr-trigonometric-grammar-profile-1"
PLAN = "docs/trigonometric_grammar_plan.md"
PLAN_COMMIT = "5de1a4a0bbb8282ac77f06e21f0314acaa99eade"
PLAN_SHA256 = "e8fe21344cedc93196d77e83918eb989907fe75e7cfa7219ee17d22661be70b5"
SEEDS = (20261020, 20261021, 20261022)
CONDITIONS = ("unrestricted", "no_nested_trig")
LIMIT_SECONDS = 3600
WORKER_LIMIT_SECONDS = 600
OBJECTIVE = "Main.TrigonometricGrammar.objective"
RUNTIME = {
    **prior.RUNTIME,
    "worker.py": "scripts/run_trigonometric_grammar_worker.py",
    "backend.py": "scripts/check_trigonometric_grammar_backend.py",
    "TrigonometricGrammar.jl": "julia/src/TrigonometricGrammar.jl",
}


def source_hashes():
    hashes = prior.source_hashes()
    for name in (
        PLAN,
        *RUNTIME.values(),
        "scripts/run_trigonometric_grammar.py",
        "scripts/check_trigonometric_grammar_integration.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen trigonometric grammar plan changed.")
    return dict(sorted(hashes.items()))


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or document["condition"] not in CONDITIONS
    ):
        raise ValueError("Invalid restricted trigonometric grammar profile.")
    return document["condition"]


def profile_parameters(budget, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    parameters = prior.profile_parameters(budget, 100)
    parameters.update(
        loss_function=OBJECTIVE,
        nested_constraints=None
        if condition == "unrestricted"
        else {
            outer: {inner: 0 for inner in ("sin", "cos")} for outer in ("sin", "cos")
        },
    )
    return parameters


def planned_cells():
    return [
        {
            "number": 2 * block + offset + 1,
            "directory": f"cell-{2 * block + offset + 1:02d}",
            "condition": condition,
            "arm": condition,
            "budget": asdict(SearchBudget(seed=seed, niterations=200)),
            "status": "planned",
        }
        for block, seed in enumerate(SEEDS)
        for offset, condition in enumerate(
            CONDITIONS if block % 2 == 0 else CONDITIONS[::-1]
        )
    ]


def verify_manifest(directory, runtime):
    import json

    manifest = json.loads((directory / "manifest.json").read_bytes())
    if (
        set(manifest) != {"format", "sources", "runtime", "inputs"}
        or manifest["format"] != FORMAT
        or manifest["sources"] != source_hashes()
        or manifest["runtime"]
        != {k: manifest["sources"][v] for k, v in RUNTIME.items()}
        or set(manifest["inputs"]) != {"request.json", "inputs.npz", "profile.json"}
    ):
        raise ValueError("Changed trigonometric grammar manifest.")
    for root, hashes in (
        (Path(runtime), manifest["runtime"]),
        (Path(directory), manifest["inputs"]),
    ):
        for name, digest in hashes.items():
            path = root / name
            if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                raise ValueError("Changed consumed grammar file: " + name)
    return manifest


def verify_nesting_field(field, condition):
    """Validate the native integer representation, retaining all four pairs."""
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    if condition == "unrestricted":
        if field != {"type": "Nothing", "value": "nothing"}:
            raise ValueError("The control grammar must be unrestricted.")
        return
    if not isinstance(field, dict) or field.get("type") != (
        "Vector{Tuple{Int64, Int64, Vector{Tuple{Int64, Int64, Int64}}}}"
    ):
        raise ValueError("Unexpected native nesting field type.")
    try:
        value = ast.literal_eval(field["value"])
        if type(value) is not list or len(value) != 2:
            raise ValueError("Exactly two outer operators are required.")
        rows = []
        for degree, outer, inners in value:
            if type(inners) is not list or len(inners) != 2:
                raise ValueError("Exactly two inner operators are required.")
            for inner_degree, inner, limit in inners:
                row = (degree, outer, inner_degree, inner, limit)
                if any(type(x) is not int for x in row):
                    raise ValueError("Native nesting indices must be integers.")
                rows.append(row)
        if sorted(rows) != [(1, a, 1, b, 0) for a in (2, 3) for b in (2, 3)]:
            raise ValueError("Wrong trig descendant restriction.")
    except (KeyError, TypeError, SyntaxError, ValueError) as error:
        raise ValueError("Invalid native trigonometric constraints.") from error


def verify_options(record, seed, condition, base, support):
    fields = support.backend_without_output(record["backend_options"])
    verify_nesting_field(fields.get("nested_constraints"), condition)
    if record.get("condition") != condition:
        raise ValueError("Wrong native grammar condition.")
    names = (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    if fields.get("loss_function") not in [
        {"type": f"typeof({name})", "value": name} for name in names
    ]:
        raise ValueError("Wrong shared grammar loss guard.")
    # Normalize only individually verified grammar/wrapper fields for the
    # existing absolute 100/2 policy. The source record is never modified.
    normalized = copy.deepcopy(record)
    for field in normalized["backend_options"]:
        if field["name"] == "nested_constraints":
            field.update(type="Nothing", value="nothing")
        elif field["name"] == "loss_function":
            field.update(type=f"typeof({prior.OBJECTIVE})", value=prior.OBJECTIVE)
    return prior.verify_options(normalized, seed, 100, base, support)


def common_options(record, support):
    fields = support.backend_without_output(record["backend_options"])
    return {
        "fields": {
            k: v for k, v in fields.items() if k not in {"seed", "nested_constraints"}
        },
        "optimizer_settings": copy.deepcopy(record["optimizer_settings"]),
        "plugins": copy.deepcopy(record["plugins"]),
    }


def verify_tree_grammar(tree, condition):
    """Check the full exported tree, including nonadjacent trig descendants."""
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})

    def visit(node, inside_trig=False):
        if node["kind"] != "operator":
            return
        trig = node["operator"] in {"sin", "cos"}
        if condition == "no_nested_trig" and trig and inside_trig:
            raise ValueError("Exported candidate violates the trig descendant rule.")
        for child in node["children"]:
            visit(child, inside_trig or trig)

    visit(tree)


supported_reconstruction = prior.supported_reconstruction


def expected_grammar_cases():
    allowed = (
        "linear",
        "cosine",
        "exponential",
        "exp_of_cos",
        "cos_of_exp",
        "trig_siblings",
    )
    forbidden = tuple(
        f"{outer}_{inner}_{wrapper}"
        for outer in ("sin", "cos")
        for inner in ("sin", "cos")
        for wrapper in ("direct", "arithmetic")
    )
    return [
        {
            "condition": condition,
            "case": name,
            "accepted": condition == "unrestricted" or name in allowed,
        }
        for condition in CONDITIONS
        for name in (*allowed, *forbidden)
    ]


def comparison(cells, *, final_verified):
    """Unlock all aggregate endpoints together, using original selections only."""
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
            raise ValueError("Wrong completed cell identity or order.")
    selected = lambda c: c["diagnostics"]["candidates"][
        c["diagnostics"]["selected_index"]
    ]
    summaries = {}
    costs = (
        "timing_seconds",
        "worker_wall_seconds",
        "callback_calls_during_fit",
        "callback_calls_total",
        "backend_evaluation_counter",
    )
    for condition in CONDITIONS:
        group = [c for c in cells if c["condition"] == condition]
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
                "planned_count": 3,
                "minimum": min(values) if values else None,
                "median": median(values) if values else None,
                "maximum": max(values) if values else None,
            }
        summaries[str(condition)] = {
            "count": 3,
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
                    **{key: c["diagnostics"].get(key) for key in costs},
                }
                for c in group
            ],
            "unselected_curve_successes": sum(
                d["curve_marker"] == "within_tolerance" and not d["is_selected"]
                for c in group
                for d in c["diagnostics"]["candidates"]
            ),
        }
    pairs = []
    for seed in SEEDS:
        low, high = [
            next(
                c for c in cells if c["budget"]["seed"] == seed and c["condition"] == i
            )
            for i in CONDITIONS
        ]
        first, second = selected(low), selected(high)
        metrics = {}
        for name, value in _metrics(first).items():
            other = _metrics(second)[name]
            left = _metric_availability(first, name, value)
            right = _metric_availability(second, name, other)
            available = left["status"] == right["status"] == "available"
            delta = other - value if available else None
            available = available and math.isfinite(delta)
            metrics[name] = {
                "unrestricted": value,
                "no_nested_trig": other,
                "availability_K": left,
                "availability_A": right,
                "difference": delta if available else None,
                "status": "available" if available else "not_assessed",
                "reason": None if available else "unavailable_or_out_of_range_metric",
            }
        pairs.append(
            {
                "seed": seed,
                "markers_K": _markers(first),
                "markers_A": _markers(second),
                "metrics": metrics,
                "success_K": first["curve_marker"] == "within_tolerance",
                "success_A": second["curve_marker"] == "within_tolerance",
            }
        )
    c_k, c_a = [summaries[str(i)]["curve_successes"] for i in CONDITIONS]
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "C_K": c_k,
            "C_A": c_a,
            "outcome": "more_successes"
            if c_a > c_k
            else "fewer_successes"
            if c_a < c_k
            else "no_successes"
            if c_k == 0
            else "equal_successes",
            "transitions": dict(
                Counter(f"{int(p['success_K'])}->{int(p['success_A'])}" for p in pairs)
            ),
            "scope": "three known development cases; no general superiority or physical identification",
        },
    )
    result["comparison"]["development_signal"] = (
        "supported_structure_gain"
        if c_a > c_k and summaries["no_nested_trig"]["supported_reconstructions"] > 0
        else "approximation_gain_only"
        if c_a > c_k
        else "hypothesis_not_supported"
    )
    return result
