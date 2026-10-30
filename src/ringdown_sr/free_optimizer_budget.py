"""Frozen free-search budget intervention, strict profiles and descriptive endpoints."""

import copy
import math
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import median

from .constant_diagnostic import backend_seed
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .representation_profiles import source_hashes as base_sources
from .representation_profiles import validate_plugin_records
from .symbolic import ROOT, SearchBudget, search_parameters

FORMAT = "ringdown-sr-free-optimizer-budget-1"
PROFILE_FORMAT = "ringdown-sr-free-optimizer-profile-1"
PLAN = "docs/free_optimizer_budget_plan.md"
PLAN_COMMIT = "bb4862034b49b89dcc37d8341814e42aa02989c5"
PLAN_SHA256 = "b63e66461e3a380f9e8ca5c127e8c5f99cd2a0d574be7be1603f18f56292907b"
SEEDS = (20261020, 20261021, 20261022)
ITERATIONS = (20, 100)
LIMIT_SECONDS = 3600
OBJECTIVE = "Main.FreeOptimizerBudget.objective"
RUNTIME = {
    "driver.py": "scripts/repeat_symbolic_arm.py",
    "probe_symbolic_numerics.py": "scripts/probe_symbolic_numerics.py",
    "worker.py": "scripts/run_free_optimizer_worker.py",
    "backend.py": "scripts/check_free_optimizer_backend.py",
    **{
        name: "julia/src/" + name
        for name in (
            "RingdownSRLoss.jl",
            "RingdownSRSearch.jl",
            "RepresentationProfiles.jl",
            "FreeOptimizerBudget.jl",
        )
    },
}


def source_hashes():
    hashes = base_sources()
    for name in (
        PLAN,
        *RUNTIME.values(),
        "scripts/run_free_optimizer_budget.py",
        "scripts/check_free_optimizer_integration.py",
        "scripts/run_representation_control.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen free optimizer-budget plan changed.")
    return dict(sorted(hashes.items()))


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "iterations"}
        or document["format"] != PROFILE_FORMAT
        or type(document["iterations"]) is not int
        or document["iterations"] not in ITERATIONS
    ):
        raise ValueError("Invalid restricted free optimizer-budget profile.")
    return document["iterations"]


def profile_parameters(budget, iterations):
    checked_profile({"format": PROFILE_FORMAT, "iterations": iterations})
    parameters = search_parameters(budget)
    parameters.update(
        loss_function=OBJECTIVE,
        optimizer_iterations=iterations,
        use_frequency=True,
        use_frequency_in_tournament=True,
    )
    return parameters


def planned_cells():
    return [
        {
            "number": 2 * block + offset + 1,
            "directory": f"cell-{2 * block + offset + 1:02d}",
            "iterations": iterations,
            "arm": f"optimizer_{iterations}",
            "budget": asdict(SearchBudget(seed=seed, niterations=200)),
            "status": "planned",
        }
        for block, seed in enumerate(SEEDS)
        for offset, iterations in enumerate((20, 100) if block % 2 == 0 else (100, 20))
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
        raise ValueError("Changed free optimizer-budget manifest.")
    for root, hashes in (
        (Path(runtime), manifest["runtime"]),
        (Path(directory), manifest["inputs"]),
    ):
        for name, digest in hashes.items():
            path = root / name
            if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                raise ValueError("Changed consumed free optimizer-budget file: " + name)
    return manifest


def verify_options(record, seed, iterations, base, support):
    """Check absolute policy before allowing the declared differences to normalize."""
    validate_plugin_records(record["plugins"], "complexity_frequency")
    fields = support.backend_without_output(record["backend_options"])
    expected_seed = backend_seed(seed)
    if (
        record["backend_seed"] != expected_seed
        or type(record["backend_seed"]) is not int
    ):
        raise ValueError("Wrong absolute free-search backend seed.")
    for name in ("use_frequency", "use_frequency_in_tournament"):
        if fields.get(name) != {"type": "Bool", "value": "true"}:
            raise ValueError("Both frequency flags must be enabled.")
    names = (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    if fields.get("loss_function") not in [
        {"type": f"typeof({n})", "value": n} for n in names
    ]:
        raise ValueError("Wrong shared free-budget loss guard.")
    if fields.get("plugins") != record["plugins_field"]:
        raise ValueError("The concrete plugin field disagrees with its snapshot.")
    settings = record["optimizer_settings"]
    if (
        settings.get("iterations") != str(iterations)
        or settings.get("callback") != "nothing"
    ):
        raise ValueError(
            "Wrong optimizer iteration limit or unexpected instrumentation."
        )
    optimizer = fields.get("optimizer_options", {})
    pattern = r"(?<=[(,])\s*iterations\s*=\s*(\d+)\s*(?=,)"
    if re.findall(pattern, optimizer.get("value", "")) != [str(iterations)]:
        raise ValueError("Wrong concrete optimizer options iteration field.")
    normalized = copy.deepcopy(record["backend_options"])
    for field in normalized:
        if field["name"] in ("use_frequency", "use_frequency_in_tournament"):
            field["value"] = "false"
        elif field["name"] == "loss_function":
            field.update(
                type="typeof(Main.RingdownSRSearch.objective)",
                value="Main.RingdownSRSearch.objective",
            )
        elif field["name"] == "optimizer_options":
            field["value"] = re.sub(pattern, " iterations = 20", field["value"])
    return base.verify_backend_policy(
        normalized,
        asdict(SearchBudget(seed=seed, niterations=200)),
        {"python_seed": seed, "backend_seed": record["backend_seed"]},
        support,
    )


def common_options(record, support):
    """Retain plugins and every effective field after absolute validation."""
    fields = support.backend_without_output(record["backend_options"])
    return {
        "fields": {
            k: v for k, v in fields.items() if k not in {"seed", "optimizer_options"}
        },
        "optimizer_settings": {
            k: v for k, v in record["optimizer_settings"].items() if k != "iterations"
        },
        "plugins": record["plugins"],
    }


def supported_reconstruction(candidate):
    physical = candidate["physical_analysis"]
    return (
        candidate["curve_marker"] == "within_tolerance"
        and candidate["search_analysis"]["structure"]["structure_status"]
        == "recognized"
        and candidate["parameter_match"]["status"] == "matched"
        and all(
            physical[name]["status"] == "passed"
            for name in ("raw_replay", "alias_replay")
        )
    )


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
            for key in ("number", "directory", "iterations", "arm", "budget")
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
    for iterations in ITERATIONS:
        group = [c for c in cells if c["iterations"] == iterations]
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
        summaries[str(iterations)] = {
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
                c for c in cells if c["budget"]["seed"] == seed and c["iterations"] == i
            )
            for i in ITERATIONS
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
                "optimizer_20": value,
                "optimizer_100": other,
                "availability_20": left,
                "availability_100": right,
                "difference": delta if available else None,
                "status": "available" if available else "not_assessed",
                "reason": None if available else "unavailable_or_out_of_range_metric",
            }
        pairs.append(
            {
                "seed": seed,
                "markers_20": _markers(first),
                "markers_100": _markers(second),
                "metrics": metrics,
                "success_20": first["curve_marker"] == "within_tolerance",
                "success_100": second["curve_marker"] == "within_tolerance",
            }
        )
    c20, c100 = [summaries[str(i)]["curve_successes"] for i in ITERATIONS]
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "C20": c20,
            "C100": c100,
            "outcome": "more_successes"
            if c100 > c20
            else "fewer_successes"
            if c100 < c20
            else "no_successes"
            if c20 == 0
            else "equal_successes",
            "transitions": dict(
                Counter(
                    f"{int(p['success_20'])}->{int(p['success_100'])}" for p in pairs
                )
            ),
            "scope": "three known development cases; no general superiority or physical identification",
        },
    )
    return result
