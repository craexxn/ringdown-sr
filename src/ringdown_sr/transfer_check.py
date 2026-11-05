"""Bound signal transfer inputs, fixed search profile, and paired diagnostics."""

import copy
import io
import json
from collections import Counter
from dataclasses import asdict
from statistics import median

import numpy as np

from . import outer_search_ladder as prior
from . import search_duration as duration
from .local_optimizer import _costs
from .noiseless_control import fingerprint
from .pilot import _sha256
from .representation_control import _markers, _metric_availability, _metrics
from .symbolic import ROOT, SearchBudget

FORMAT = "ringdown-sr-transfer-check-1"
PROFILE_FORMAT = "ringdown-sr-transfer-check-profile-1"
PLAN = "docs/transfer_check_plan.md"
PLAN_COMMIT = "446afbfea8958f409693c2253f8d9d4950f24e45"
PLAN_SHA256 = "f29561b8151a2a4e17cd881a8c4576f406f0efd340309ac54fcbbde2faabb6f3"
INPUT = "data/transfer_check_inputs.npz"
INPUT_SHA256 = "e4de71bb6aa5cb5e3afc72914466b997adb2ef6438bbe38d7baa421a85bd2628"
INPUT_MANIFEST = "data/transfer_check_inputs.json"
MANIFEST_SHA256 = "54f7ddb7b524640e20911ae3fe69334d3fd31d25d9c9fab69d132e1ade9d1773"
SEEDS = (20261210, 20261211, 20261212)
SIGNALS = ("anchor", "frequency", "decay", "phase", "amplitude", "combined")
CONDITIONS = ("local_300_5",)
NATIVE_MODULE, OBJECTIVE = prior.NATIVE_MODULE, prior.OBJECTIVE
LIMIT_SECONDS, WORKER_LIMIT_SECONDS = 7200, 900
RUNTIME = {
    **prior.RUNTIME,
    "worker.py": "scripts/run_transfer_check_worker.py",
    "backend.py": "scripts/check_transfer_check_backend.py",
}
load_module = prior.load_module
selected = prior.selected
supported_reconstruction = prior.supported_reconstruction


def source_hashes():
    hashes = prior.source_hashes()
    for name in (
        PLAN,
        INPUT,
        INPUT_MANIFEST,
        *RUNTIME.values(),
        "src/ringdown_sr/transfer_check.py",
        "scripts/run_transfer_check.py",
        "scripts/check_transfer_check_integration.py",
    ):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    if any(
        hashes[name] != digest
        for name, digest in (
            (PLAN, PLAN_SHA256),
            (INPUT, INPUT_SHA256),
            (INPUT_MANIFEST, MANIFEST_SHA256),
        )
    ):
        raise ValueError("The frozen transfer plan or input bytes changed.")
    return dict(sorted(hashes.items()))


def input_manifest():
    contents = (ROOT / INPUT_MANIFEST).read_bytes()
    if _sha256(contents) != MANIFEST_SHA256:
        raise ValueError("The frozen transfer input manifest changed.")
    return json.loads(contents)


def reference_truth(signal):
    return copy.deepcopy(input_manifest()["cases"][SIGNALS.index(signal)]["truth"])


def read_inputs(path):
    contents = path.read_bytes()
    if _sha256(contents) != INPUT_SHA256:
        raise ValueError("The frozen transfer input bundle changed.")
    manifest = input_manifest()
    with np.load(io.BytesIO(contents), allow_pickle=False) as bundle:
        arrays = {name: bundle[name] for name in bundle.files}
    if set(arrays) != set(manifest["arrays"]) or any(
        value.dtype != np.dtype("float64")
        or not np.all(np.isfinite(value))
        or fingerprint(value) != manifest["arrays"][name]
        for name, value in arrays.items()
    ):
        raise ValueError("Transfer arrays do not match the frozen data bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return contents, arrays


def arrays_for_cell(arrays, cell):
    index = SIGNALS.index(cell["signal"])
    return {
        "time_s": arrays["time_s"],
        "observed": arrays["observed"][index],
        "diagnostic_time_s": arrays["diagnostic_time_s"],
        "diagnostic_truth": arrays["diagnostic_truth"][index],
    }


def planned_cells():
    cells = []
    for seed, shift in zip(SEEDS, (0, 2, 4), strict=True):
        for signal in SIGNALS[shift:] + SIGNALS[:shift]:
            number = len(cells) + 1
            cells.append(
                {
                    "number": number,
                    "directory": f"cell-{number:02d}",
                    "condition": "local_300_5",
                    "arm": signal,
                    "signal": signal,
                    "grammar": "unrestricted",
                    "budget": asdict(SearchBudget(seed=seed, niterations=500)),
                    "status": "planned",
                }
            )
    return cells


def checked_profile(document):
    if document != {"format": PROFILE_FORMAT, "condition": "local_300_5"}:
        raise ValueError("Expected the fixed transfer 300/5 profile.")
    return "local_300_5"


def profile_parameters(budget, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return prior.profile_parameters(budget, condition)


def search_profiles():
    return [
        {
            "number": c["number"],
            "condition": c["condition"],
            "signal": c["signal"],
            "budget": c["budget"],
            "parameters": profile_parameters(
                SearchBudget(**c["budget"]), c["condition"]
            ),
        }
        for c in planned_cells()
    ]


verify_options = prior.verify_options
common_options = prior.common_options
verify_tree_grammar = prior.verify_tree_grammar
expected_grammar_cases = prior.expected_grammar_cases


def common_parameters(parameters):
    return {k: v for k, v in parameters.items() if k != "random_state"}


def verify_manifest(directory, runtime):
    module = load_module(
        ROOT / "src/ringdown_sr/trigonometric_grammar.py",
        "ringdown_sr._transfer_manifest",
    )
    module.FORMAT, module.source_hashes, module.RUNTIME = FORMAT, source_hashes, RUNTIME
    return module.verify_manifest(directory, runtime)


def invocation_record(iterations):
    return {**prior.invocation_record(iterations), "format": FORMAT}


class SearchInvocationGuard(prior.SearchInvocationGuard):
    def record(self):
        return {**super().record(), "format": FORMAT}


def comparison(cells, *, final_verified):
    result = {"summaries": None, "pair_differences": None, "comparison": None}
    if (
        not final_verified
        or len(cells) != 18
        or any(c["status"] != "completed" for c in cells)
    ):
        return result
    for cell, expected in zip(cells, planned_cells(), strict=True):
        if any(
            cell[k] != expected[k]
            for k in (
                "number",
                "directory",
                "condition",
                "arm",
                "signal",
                "grammar",
                "budget",
            )
        ):
            raise ValueError("Wrong completed transfer cell identity or order.")
    summaries = {}
    for signal in SIGNALS:
        group = [c for c in cells if c["signal"] == signal]
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
                "planned_count": 3,
                "minimum": min(values) if values else None,
                "median": median(values) if values else None,
                "maximum": max(values) if values else None,
            }
        summaries[signal] = {
            "truth": reference_truth(signal),
            "count": 3,
            "curve_successes": sum(
                c["curve_marker"] == "within_tolerance" for c in chosen
            ),
            "supported_reconstructions": sum(map(supported_reconstruction, chosen)),
            "markers": {
                k: dict(Counter(_markers(c)[k] for c in chosen))
                for k in ("curve", "structure", "parameters")
            },
            "statistics": statistics,
            "cost_by_seed": [{"seed": c["budget"]["seed"], **_costs(c)} for c in group],
            "unselected_curve_successes": sum(
                d["curve_marker"] == "within_tolerance" and not d["is_selected"]
                for c in group
                for d in c["diagnostics"]["candidates"]
            ),
        }
    indexed = {(c["signal"], c["budget"]["seed"]): c for c in cells}
    pairs, contrasts = [], {}
    for signal in SIGNALS[1:]:
        name = f"{signal}_minus_anchor"
        paired = []
        for seed in SEEDS:
            left, right = indexed["anchor", seed], indexed[signal, seed]
            first_cost, second_cost = _costs(left), _costs(right)
            paired.append(
                {
                    "contrast": name,
                    "signal_first": "anchor",
                    "signal_second": signal,
                    **duration.pair_record(
                        left, right, factor="signal", fixed="500/300/5", seed=seed
                    ),
                    "supported_first": supported_reconstruction(selected(left)),
                    "costs": {"first": first_cost, "second": second_cost},
                    "cost_changes": {
                        k: prior._cost_change(first_cost[k], second_cost[k])
                        for k in ("worker_wall_seconds", "callback_calls_during_fit")
                    },
                }
            )
        a, b = summaries["anchor"], summaries[signal]
        contrasts[name] = {
            "curve_difference": b["curve_successes"] - a["curve_successes"],
            "supported_difference": b["supported_reconstructions"]
            - a["supported_reconstructions"],
            "curve_transitions": prior._transitions(
                paired, "success_first", "success_second"
            ),
            "supported_transitions": prior._transitions(
                paired, "supported_first", "supported_second"
            ),
        }
        pairs.extend(paired)
    result.update(
        summaries=summaries,
        pair_differences=pairs,
        comparison={
            "contrasts": contrasts,
            "scope": "six fixed signals, three fresh paired seeds, fixed 500/300/5; separate curve and supported-selection counts; limited recognizer; no pooled success rate or physical identification",
        },
    )
    return copy.deepcopy(result)
