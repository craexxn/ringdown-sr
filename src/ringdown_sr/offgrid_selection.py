"""Compare frozen candidate selection using separately simulated noisy observations."""

import copy
import html
import io
import math
import time
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import noise_background_plots as plots
from . import noise_followup_inputs as original
from .pilot import _environment, _provenance
from .signals import ringdown_signal
from .structure import _validated_tree
from .symbolic import evaluate_tree, select_candidate

FORMAT = "ringdown-sr-offgrid-selection-1"
PLAN = "docs/offgrid_selection_plan.md"
# Execution remains unavailable until the separate post-scaling plan is frozen.
PLAN_SHA256 = None
MANIFESTS = {
    "shared": "e938851c3f5ffeec0bcd8505ed5f38835df8a14865e0aa5f5b34759dece1299a",
    "duration": "2af1c2e46aae4526e0c272729033ad90939c21fa41e395044108cc56aff77c22",
    "sampling": "94bf6f7ac6ce7dfd45a6dcc240abf9fa2f44855aae7d63e407adea2f9a27c0e1",
}
CASES = tuple(f"ar1-{i:02d}" for i in range(1, 21)) + tuple(
    f"white-{i:02d}" for i in range(1, 7)
)
ARMS = tuple(original.ARMS)
SELECTORS = ("original", "same_grid", "off_grid")
GRID_SEED = 2026112401
CASE_SEEDS = dict(zip(CASES, range(2026112501, 2026112527), strict=True))
SECONDS = 14400
LABELS = {
    "original": "Original: Trainingsverlust",
    "same_grid": "Neue Messung: ursprüngliches Raster",
    "off_grid": "Neue Messung: Off-grid",
}


def _array(values, name):
    result = np.asarray(values, dtype=np.float64)
    if result.ndim != 1 or not len(result) or not np.isfinite(result).all():
        raise ValueError(f"{name} must be a finite nonempty vector.")
    return result


def _mse(residual):
    """Sum squares with scaling; unrepresentable scores remain unavailable."""
    residual = np.asarray(residual, dtype=np.float64)
    if not np.isfinite(residual).all():
        return None
    scale = float(np.max(np.abs(residual)))
    if scale == 0:
        return 0.0
    normalized = math.fsum(float(x / scale) ** 2 for x in residual) / len(residual)
    rms = scale * math.sqrt(normalized)
    value = rms * rms
    # Only an exactly zero residual may report zero: retain representable
    # positive subnormals, but do not turn a positive underflowed MSE into a tie.
    return value if math.isfinite(value) and value > 0 else None


def _validate_pool(pool):
    if not pool:
        raise ValueError("A candidate pool cannot be empty.")
    identities = []
    for item in pool:
        if (
            set(item) != {"id", "tree", "complexity"}
            or not isinstance(item["id"], str)
            or not item["id"]
            or type(item["complexity"]) is not int
            or item["complexity"] < 1
        ):
            raise ValueError(
                "The selector accepts only identities, trees and complexity."
            )
        _validated_tree(item["tree"])

        def size(node):
            return 1 + sum(size(child) for child in node.get("children", []))

        if size(item["tree"]) != item["complexity"]:
            raise ValueError("Candidate complexity differs from its original tree.")
        identities.append(item["id"])
    if len(set(identities)) != len(identities):
        raise ValueError("Candidate identities must be unique.")


def select(pool, time_s, observed):
    """Select from trees and noisy observations only; never accept clean truth."""
    _validate_pool(pool)
    times, target = _array(time_s, "time_s"), _array(observed, "observed")
    if times.shape != target.shape or np.any(np.diff(times) <= 0):
        raise ValueError("Selection needs matching ordered observation vectors.")
    scores = []
    for item in pool:
        try:
            prediction = evaluate_tree(item["tree"], times)
        except ValueError as error:
            if str(error) != "Tree prediction is not finite.":
                raise
            prediction = None
        with np.errstate(all="ignore"):
            score = None if prediction is None else _mse(target - prediction)
        scores.append(
            {
                "id": item["id"],
                "mse": score,
                "complexity": item["complexity"],
                "status": "finite" if score is not None else "unavailable",
                "reason": None
                if score is not None
                else "nonfinite_prediction"
                if prediction is None
                else "nonfinite_or_unrepresentable_mse",
            }
        )
    eligible = [item for item in scores if item["mse"] is not None]
    chosen = (
        min(eligible, key=lambda item: (item["mse"], item["complexity"], item["id"]))
        if eligible
        else None
    )
    return {
        "selected_id": None if chosen is None else chosen["id"],
        "status": "abstained" if chosen is None else "selected",
        "rule": "minimum_finite_validation_mse_then_complexity_then_stable_id",
        "scores": scores,
    }


def validation_grid(common):
    """Generate one fixed stratified axis without observing any candidate."""
    rng = np.random.Generator(np.random.PCG64(GRID_SEED))
    fractions = rng.random(128)
    grid = (np.arange(128) + fractions) / 128 * common["time_s"][-1]
    forbidden = np.concatenate(
        [
            common[key]
            for key in (
                "time_s",
                "jitter_time_s",
                "diagnostic_time_s",
                "irregular_time_s",
            )
        ]
    )
    if (
        np.any(fractions <= 0)
        or np.any(fractions >= 1)
        or np.any(np.diff(grid) <= 0)
        or np.any(np.isin(grid, forbidden))
    ):
        raise ValueError(
            "The predeclared validation grid collides; no replacement draw."
        )
    return grid


def validation_observations(case, common, grid):
    """Simulate an independent observation; truth stays outside the selector API."""
    if case not in CASE_SEEDS:
        raise ValueError("Unknown frozen development case.")
    union = np.unique(np.concatenate((common["time_s"], common["jitter_time_s"], grid)))
    rng = np.random.Generator(np.random.PCG64(CASE_SEEDS[case]))
    before = copy.deepcopy(rng.bit_generator.state)
    noise = original.union_noise(
        rng,
        union,
        sigma=original.SIGMA,
        rho=original.RHO if case.startswith("ar1-") else 0.0,
    )
    signal = ringdown_signal(union, **original.SIGNAL)
    truth_error = original.pilot._truth_reference(union, signal)
    observed = signal + noise
    values = {}
    for role, axis in (
        ("uniform", common["time_s"]),
        ("jitter", common["jitter_time_s"]),
        ("off_grid", grid),
    ):
        values[role] = observed[np.searchsorted(union, axis)]
    return values, {
        "case": case,
        "seed": CASE_SEEDS[case],
        "rng_before": before,
        "rng_after": copy.deepcopy(rng.bit_generator.state),
        "independent_realization_of_same_known_signal": True,
        "noise_model": "stationary_ou"
        if case.startswith("ar1-")
        else "independent_white",
        "sigma_hex": original.SIGMA.hex(),
        "rho_at_4096_hz": original.RHO if case.startswith("ar1-") else 0.0,
        "union_time_s": union.tolist(),
        "union_noise": noise.tolist(),
        "union_observed": observed.tolist(),
        "truth_reference_max_absolute_error_over_amplitude": truth_error,
    }


class OriginalFiles:
    """Read only individually consumed files anchored in original archive manifests."""

    def __init__(self, root, consumed):
        self.root = Path(root).absolute()
        if not self.root.is_dir() or self.root != self.root.resolve():
            raise ValueError(
                "Original source needs a real directory without symlink parents."
            )
        self.expected, self.used = {}, {}
        self.consumed = consumed
        for part, digest in MANIFESTS.items():
            name = f"ARCHIVE-{part}.json"
            self.expected[name] = digest
            document = self.json(name)
            if document["part"] != part:
                raise ValueError("Original archive part identity differs.")
            for relative, value in document["files_sha256"].items():
                sources.safe_name(relative)
                if relative in self.expected and self.expected[relative] != value:
                    raise ValueError("Original archive inventories conflict.")
                self.expected[relative] = value
        consumed.callbacks.append(self.check)

    def raw(self, name):
        sources.safe_name(name)
        path = self.root / name
        self.consumed.clock.check()
        if path != path.resolve() or not path.is_file():
            raise ValueError("Consumed original is missing or is a link: " + name)
        raw = path.read_bytes()
        digest = sources.sha256(raw)
        if self.expected.get(name) != digest:
            raise ValueError("Original archive binding differs: " + name)
        self.used[name] = digest
        return raw

    def json(self, name):
        return sources.read_json(self.raw(name))

    def arrays(self, name):
        with np.load(io.BytesIO(self.raw(name)), allow_pickle=False) as data:
            return {key: data[key].copy() for key in data.files}

    def check(self):
        for name in tuple(self.used):
            self.raw(name)


def _compact(candidate, identity):
    return {
        "id": identity,
        "tree": copy.deepcopy(candidate["tree"]),
        "complexity": candidate["complexity"],
        "original_formula": candidate["display_equation"],
        "native_training_loss": candidate["loss"],
    }


def _pool(originals, case, arm, spec):
    block = "sampling" if arm.startswith("jitter_") else "duration"
    base = f"{block}/cases/{case}/symbolic/{arm}"
    package = originals.json(base + "/completion/assessment_report.json")
    if (
        package["package_status"] != "success"
        or package["technical"] is not False
        or package["search_calls"] != 4
    ):
        raise ValueError("The bound original package is incomplete.")
    pool, originals_by_id = [], {}
    selected_workers = []
    for member in range(1, 5):
        prefix = f"{base}/member-{member:02d}"
        checksums = originals.json(prefix + "/checksums.json")
        documents = {}
        for name in ("result.json", "request.json", "metadata.json", "prepared.json"):
            raw = originals.raw(prefix + "/" + name)
            if checksums.get(name) != sources.sha256(raw):
                raise ValueError("Original worker checksum mismatch.")
            documents[name] = sources.read_json(raw)
        request, result = documents["request.json"], documents["result.json"]
        provenance = documents["prepared.json"]["provenance"]["git"]
        if (
            request["technical"] is not False
            or request["profile"] != "r4x1000-local300x5-v1"
            or request["seed"] != spec["search_seeds"][member - 1]
            or request["budget"]
            != {
                "niterations": 1000,
                "seed": spec["search_seeds"][member - 1],
                "populations": 2,
                "population_size": 32,
                "ncycles_per_iteration": 50,
            }
            or documents["metadata.json"]["phase"] != "success"
            or provenance["commit"] != "8a1a4a1437f4b01daf1f070b56add248074c5907"
            or provenance["dirty"] is not False
        ):
            raise ValueError("Original worker scientific identity differs.")
        if result["selected_index"] != select_candidate(result["candidates"]):
            raise ValueError("Original worker selection cannot be reproduced.")
        for index, candidate in enumerate(result["candidates"]):
            identity = f"member-{member:02d}/candidate-{index:03d}"
            compact = _compact(candidate, identity)
            pool.append(compact)
            originals_by_id[identity] = candidate
        selected_workers.append(
            f"member-{member:02d}/candidate-{result['selected_index']:03d}"
        )
    chosen = min(
        pool,
        key=lambda item: (item["native_training_loss"], item["complexity"], item["id"]),
    )
    original_id = selected_workers[package["selected_member"]]
    if (
        chosen["id"] != original_id
        or originals_by_id[original_id] != package["selected_candidate"]
    ):
        raise ValueError("Original package selection cannot be reproduced.")
    return pool, original_id


def _prediction(tree, axis):
    if tree is None:
        return np.full(len(axis), np.nan)
    try:
        return evaluate_tree(tree, axis)
    except ValueError as error:
        if str(error) != "Tree prediction is not finite.":
            raise
        result = np.full(len(axis), np.nan)
        for index, point in enumerate(axis):
            try:
                result[index] = evaluate_tree(tree, [point])[0]
            except ValueError as inner:
                if str(inner) != "Tree prediction is not finite.":
                    raise
        return result


def _metrics(prediction, truth):
    if not np.isfinite(prediction).all() or not np.isfinite(truth).all():
        return {
            "status": "nonfinite",
            "rms_over_amplitude": None,
            "max_over_amplitude": None,
        }
    with np.errstate(over="ignore", invalid="ignore"):
        residual = prediction - truth
    if np.isfinite(residual).all():
        scale = float(np.max(np.abs(residual)))
        normalized = residual if scale == 0 else residual / scale
    else:
        # Subtraction itself can overflow for opposite huge finite operands.
        # This branch cannot lose all residuals to cancellation: an overflowing
        # difference has a scaled magnitude of order one.
        scale = max(float(np.max(np.abs(prediction))), float(np.max(np.abs(truth))))
        normalized = prediction / scale - truth / scale
    amplitude = abs(original.SIGNAL["amplitude"])
    maximum = scale * (float(np.max(np.abs(normalized))) / amplitude)
    rms = scale * (
        math.sqrt(math.fsum(float(x) ** 2 for x in normalized) / len(normalized))
        / amplitude
    )
    return {
        "status": "finite"
        if math.isfinite(rms) and math.isfinite(maximum)
        else "partly_or_wholly_unrepresentable",
        "rms_over_amplitude": rms if math.isfinite(rms) else None,
        "max_over_amplitude": maximum if math.isfinite(maximum) else None,
    }


def _assess(pool, selections, common, training, validation, grid, jitter):
    by_id = {item["id"]: item for item in pool}
    axes = {
        "training": (
            common["jitter_time_s" if jitter else "time_s"],
            common["jitter_signal" if jitter else "signal"],
            training,
        ),
        "same_grid": (
            common["jitter_time_s" if jitter else "time_s"],
            common["jitter_signal" if jitter else "signal"],
            validation["jitter" if jitter else "uniform"],
        ),
        "off_grid": (
            grid,
            ringdown_signal(grid, **original.SIGNAL),
            validation["off_grid"],
        ),
        "diagnostic": (common["diagnostic_time_s"], common["diagnostic_truth"], None),
        "irregular": (common["irregular_time_s"], common["irregular_truth"], None),
    }
    records, rows = {}, []
    for selector in SELECTORS:
        identity = selections[selector]
        candidate = None if identity is None else by_id[identity]
        metrics = {}
        for role, (axis, truth, observed) in axes.items():
            prediction = _prediction(
                None if candidate is None else candidate["tree"], axis
            )
            metrics[role] = _metrics(prediction, truth)
            for i, point in enumerate(axis):
                finite = math.isfinite(float(prediction[i]))
                rows.append(
                    {
                        "selector": selector,
                        "grid": role,
                        "time_s": float(point),
                        "truth": float(truth[i]),
                        "observed": None if observed is None else float(observed[i]),
                        "prediction": float(prediction[i]) if finite else None,
                        "status": "finite" if finite else "unavailable",
                    }
                )
        records[selector] = {
            "selected": candidate,
            "status": "abstained" if candidate is None else "selected",
            "metrics": metrics,
        }
    return records, rows


def _panel(case, arm, rows):
    figure = plots._figure((11, 8))
    top, bottom = figure.subplots(2, 1, sharex=True)
    magnitude = max(
        abs(float(row[key]))
        for row in rows
        for key in ("prediction", "truth")
        if row[key] is not None
    )
    scale = magnitude if magnitude > 1e100 or 0 < magnitude < 1e-100 else 1.0
    for selector, color in zip(
        SELECTORS, ("#b2182b", "#2166ac", "#008837"), strict=True
    ):
        points = [
            row
            for row in rows
            if row["selector"] == selector
            and row["grid"] in ("diagnostic", "irregular")
        ]
        times = [row["time_s"] for row in points]
        predictions = [
            np.nan if row["prediction"] is None else row["prediction"] / scale
            for row in points
        ]
        residual = [
            (value - row["truth"] / scale) / abs(original.SIGNAL["amplitude"])
            for value, row in zip(predictions, points, strict=True)
        ]
        top.scatter(
            times, predictions, s=3, alpha=0.65, color=color, label=LABELS[selector]
        )
        bottom.scatter(
            times, residual, s=3, alpha=0.65, color=color, label=LABELS[selector]
        )
        missing = [point for point in points if point["prediction"] is None]
        if missing:
            bottom.scatter(
                [point["time_s"] for point in missing],
                np.full(len(missing), 0.025),
                transform=bottom.get_xaxis_transform(),
                marker="x",
                color=color,
                label=f"{LABELS[selector]}: {len(missing)} nicht verfügbar",
            )
    points = sorted(
        (
            row
            for row in rows
            if row["selector"] == "original" and row["grid"] == "irregular"
        ),
        key=lambda row: row["time_s"],
    )
    top.plot(
        [row["time_s"] for row in points],
        [row["truth"] / scale for row in points],
        color="black",
        lw=0.6,
        label="Sauberes bekanntes Entwicklungssignal",
    )
    scale_label = "" if scale == 1 else f" / {scale:.17g}"
    top.set_ylabel("Signal / Original-Amplitudeneinheit" + scale_label)
    bottom.set_ylabel("(Vorhersage − Wahrheit) / |A|" + scale_label)
    bottom.set_xlabel("t / s")
    figure.suptitle(f"{case} / {arm}: Originale und zwei neue Auswahlregeln")
    for axis in (top, bottom):
        axis.grid(alpha=0.2)
        axis.legend(fontsize=7)
    figure.text(
        0.03,
        0.015,
        "Keine Glättung oder Achsenkappung. Vollständige Originalformeln, Bäume und Punkte separat.\n"
        + (
            f"Beide Anzeigeachsen geteilt durch {scale:.17g}; CSV enthält unveränderte Werte."
            if scale != 1
            else "Endliche Raster beweisen keine kontinuierliche Fehlergrenze; neue Messinformation ist zusätzlich."
        ),
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 0.96))
    return plots._images(figure)


def _statistics(values):
    """Keep finite extreme observations without overflowing sums or medians."""
    if not values:
        return {
            "mean": None,
            "median": None,
            "sd": None,
            "mcse": None,
            "sd_status": "fewer_than_two_observations",
            "mcse_status": "fewer_than_two_observations",
        }
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Nonfinite values need an explicit unavailable count.")
    scale = max(abs(value) for value in values)
    normalized = (
        sorted(value / scale for value in values) if scale else [0.0] * len(values)
    )
    mean = math.fsum(normalized) / len(values)
    middle = len(values) // 2
    median = (
        normalized[middle]
        if len(values) % 2
        else normalized[middle - 1] / 2 + normalized[middle] / 2
    )
    sd = mcse = None
    if len(values) > 1:
        normalized_sd = math.sqrt(
            math.fsum((value - mean) ** 2 for value in normalized) / (len(values) - 1)
        )
        sd = scale * normalized_sd
        mcse = scale * (normalized_sd / math.sqrt(len(values)))
    return {
        "mean": scale * mean,
        "median": scale * median,
        "sd": sd if sd is None or math.isfinite(sd) else None,
        "mcse": mcse if mcse is None or math.isfinite(mcse) else None,
        "sd_status": "fewer_than_two_observations"
        if sd is None
        else "finite"
        if math.isfinite(sd)
        else "not_representable",
        "mcse_status": "fewer_than_two_observations"
        if mcse is None
        else "finite"
        if math.isfinite(mcse)
        else "not_representable",
    }


def _availability(output, grid, metric):
    """Distinguish selection abstention from unusable selected-formula assessment."""
    if output["status"] == "abstained":
        if output["metrics"][grid][metric] is not None:
            raise ValueError("An abstained output cannot have an available assessment.")
        return "abstained"
    if output["status"] != "selected":
        raise ValueError("Unknown selection output status.")
    assessment = output["metrics"][grid]
    value = assessment[metric]
    if value is not None:
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(
                "An available assessment metric must be finite and nonnegative."
            )
        return "available"
    if assessment["status"] == "nonfinite":
        return "nonfinite_assessment"
    if assessment["status"] == "partly_or_wholly_unrepresentable":
        return "unrepresentable_assessment"
    raise ValueError("An unavailable assessment metric lacks a reason.")


def _summaries(records):
    summaries = []
    for model, planned in (("ar1", 20), ("white", 6)):
        for arm in ARMS:
            group = [
                row
                for row in records
                if row["case"].startswith(model + "-") and row["arm"] == arm
            ]
            for selector in SELECTORS:
                for grid in ("irregular", "diagnostic"):
                    for metric in ("rms_over_amplitude", "max_over_amplitude"):
                        values, paired, availability = [], [], []
                        for row in group:
                            availability.append(
                                _availability(row["outputs"][selector], grid, metric)
                            )
                            value = row["outputs"][selector]["metrics"][grid][metric]
                            baseline = row["outputs"]["original"]["metrics"][grid][
                                metric
                            ]
                            if value is not None:
                                values.append(value)
                            if value is not None and baseline is not None:
                                paired.append(value - baseline)
                        summaries.append(
                            {
                                "model": model,
                                "arm": arm,
                                "selector": selector,
                                "grid": grid,
                                "metric": metric,
                                "planned_cases": planned,
                                "not_run_cases": planned - len(group),
                                "selected_cases": sum(
                                    reason != "abstained" for reason in availability
                                ),
                                "abstained_cases": availability.count("abstained"),
                                "unusable_assessment_cases": availability.count(
                                    "nonfinite_assessment"
                                )
                                + availability.count("unrepresentable_assessment"),
                                "nonfinite_assessment_cases": availability.count(
                                    "nonfinite_assessment"
                                ),
                                "unrepresentable_assessment_cases": availability.count(
                                    "unrepresentable_assessment"
                                ),
                                "finite_cases": len(values),
                                "paired_cases": len(paired),
                                **_statistics(values),
                                "mean_change_from_original": _statistics(paired)[
                                    "mean"
                                ],
                                "improved": sum(value < 0 for value in paired),
                                "worsened": sum(value > 0 for value in paired),
                                "unchanged": sum(value == 0 for value in paired),
                                "interpretation": "descriptive_known_development_cases; no_independent_confirmation",
                            }
                        )
    return summaries


def _contrasts(records):
    """Make the paired geometry contrast primary and original comparisons secondary."""
    rows, summary = [], []
    comparisons = (
        ("off_grid", "same_grid", "primary"),
        ("off_grid", "original", "secondary"),
        ("same_grid", "original", "secondary"),
    )
    for record in records:
        for left, right, priority in comparisons:
            for grid in ("irregular", "diagnostic"):
                for metric in ("rms_over_amplitude", "max_over_amplitude"):
                    a = record["outputs"][left]["metrics"][grid][metric]
                    b = record["outputs"][right]["metrics"][grid][metric]
                    reasons = (
                        _availability(record["outputs"][left], grid, metric),
                        _availability(record["outputs"][right], grid, metric),
                    )
                    exclusion = next(
                        (
                            reason
                            for reason in (
                                "abstained",
                                "nonfinite_assessment",
                                "unrepresentable_assessment",
                            )
                            if reason in reasons
                        ),
                        None,
                    )
                    rows.append(
                        {
                            "case": record["case"],
                            "model": record["case"].split("-")[0],
                            "arm": record["arm"],
                            "contrast": left + "-minus-" + right,
                            "priority": priority,
                            "endpoint_priority": "primary"
                            if grid == "irregular" and metric == "rms_over_amplitude"
                            else "secondary",
                            "grid": grid,
                            "metric": metric,
                            "difference": None if exclusion is not None else a - b,
                            "left_available": reasons[0] == "available",
                            "right_available": reasons[1] == "available",
                            "left_status": reasons[0],
                            "right_status": reasons[1],
                            "pair_status": "available"
                            if exclusion is None
                            else exclusion,
                        }
                    )
    for model, planned in (("ar1", 20), ("white", 6)):
        for arm in ARMS:
            for left, right, priority in comparisons:
                for grid in ("irregular", "diagnostic"):
                    for metric in ("rms_over_amplitude", "max_over_amplitude"):
                        grouped = [
                            row
                            for row in rows
                            if row["model"] == model
                            and row["arm"] == arm
                            and row["contrast"] == left + "-minus-" + right
                            and row["grid"] == grid
                            and row["metric"] == metric
                        ]
                        values = [
                            row["difference"]
                            for row in grouped
                            if row["pair_status"] == "available"
                        ]
                        excluded = [row["pair_status"] for row in grouped]
                        summary.append(
                            {
                                "model": model,
                                "arm": arm,
                                "contrast": left + "-minus-" + right,
                                "priority": priority,
                                "endpoint_priority": "primary"
                                if grid == "irregular"
                                and metric == "rms_over_amplitude"
                                else "secondary",
                                "grid": grid,
                                "metric": metric,
                                "planned_pairs": planned,
                                "available_pairs": len(values),
                                "unavailable_pairs": planned - len(values),
                                "not_run_pairs": planned - len(grouped),
                                "excluded_abstention_pairs": excluded.count(
                                    "abstained"
                                ),
                                "excluded_nonfinite_assessment_pairs": excluded.count(
                                    "nonfinite_assessment"
                                ),
                                "excluded_unrepresentable_assessment_pairs": excluded.count(
                                    "unrepresentable_assessment"
                                ),
                                **_statistics(values),
                                "improved": sum(value < 0 for value in values),
                                "worsened": sum(value > 0 for value in values),
                                "unchanged": sum(value == 0 for value in values),
                                "interpretation": "descriptive_known_development_cases; conditional_on_available_pairs; no_independent_confirmation",
                            }
                        )
    return rows, summary


def _binding(consumed):
    if PLAN_SHA256 is None:
        raise RuntimeError("The separate selection plan has not been frozen.")
    names = sorted(
        {
            PLAN,
            original.SEEDS_PATH,
            original.PLAN_PATH,
            "scripts/run_offgrid_selection.py",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            *(
                p.relative_to(sources.ROOT).as_posix()
                for p in (sources.ROOT / "src/ringdown_sr").glob("*.py")
            ),
        }
    )
    hashes = {}
    for name in names:
        path = sources.ROOT / name
        raw = path.read_bytes()
        consumed.add(path, raw)
        hashes[name] = sources.sha256(raw)
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen selection plan changed.")
    provenance = _provenance()
    if not provenance["git"]["available"] or provenance["git"]["dirty"]:
        raise ValueError(
            "Selection requires a clean, identified implementation checkout."
        )
    return {
        "plan": PLAN,
        "plan_sha256": PLAN_SHA256,
        "source_sha256": hashes,
        "provenance": provenance,
    }


def _compute(source, consumed, *, images):
    binding = _binding(consumed)
    originals = OriginalFiles(source, consumed)
    common = originals.arrays("inputs/common.npz")
    grid = validation_grid(common)
    specs = {item["id"]: item for item in original.case_specs()}
    if set(specs) != set(CASES):
        raise ValueError("Original case inventory differs from the frozen pool.")
    historical_seeds = {
        seed
        for spec in specs.values()
        for seed in (
            spec.get("noise_seed"),
            spec.get("background_seed"),
            *spec["search_seeds"],
        )
    }
    if historical_seeds.intersection({GRID_SEED, *CASE_SEEDS.values()}):
        raise ValueError("A new random stream reuses an original seed.")
    payloads, records, all_scores, generated = {}, [], [], []
    gallery = [
        "<!doctype html><html lang='de'><meta charset='utf-8'><title>Off-grid-Auswahl</title><body><h1>Zusätzliche Messinformation zur Formelauswahl</h1><p>Bekannte Entwicklungsfälle; keine neue Suche, kein Refit, keine unabhängige Bestätigung. Alle 156 Pakete und drei Auswahlen je Paket. Originalformeln unverändert.</p>"
    ]
    for case in CASES:
        arrays = originals.arrays(f"inputs/cases/{case}/arrays.npz")
        originals.json(f"inputs/cases/{case}/record.json")
        validation, generated_record = validation_observations(case, common, grid)
        generated.append(generated_record)
        for arm in ARMS:
            consumed.clock.check()
            pool, selected = _pool(originals, case, arm, specs[case])
            selector_pool = [
                {key: item[key] for key in ("id", "tree", "complexity")}
                for item in pool
            ]
            jitter = arm.startswith("jitter_")
            same = select(
                selector_pool,
                common["jitter_time_s" if jitter else "time_s"],
                validation["jitter" if jitter else "uniform"],
            )
            off = select(selector_pool, grid, validation["off_grid"])
            chosen = {
                "original": selected,
                "same_grid": same["selected_id"],
                "off_grid": off["selected_id"],
            }
            outputs, rows = _assess(
                pool,
                chosen,
                common,
                arrays["jitter_observed" if jitter else "observed"],
                validation,
                grid,
                jitter,
            )
            record = {
                "case": case,
                "arm": arm,
                "pool_size": len(pool),
                "original_selection_reproduced": True,
                "outputs": outputs,
            }
            records.append(record)
            stem = f"{case}-{arm}"
            payloads[stem + ".csv"] = plots._csv(rows)
            payloads[stem + ".json"] = sources.json_bytes(
                {**record, "candidate_pool": pool}
            )
            formulas = "\n\n".join(
                f"{LABELS[name]}\n"
                + (
                    "Keine zulässige Auswahl"
                    if outputs[name]["selected"] is None
                    else outputs[name]["selected"]["original_formula"]
                )
                for name in SELECTORS
            )
            payloads[stem + ".formula.txt"] = (
                f"{case} / {arm}; t in Sekunden; ursprüngliche Amplitudeneinheit.\n\n"
                + formulas
                + "\n"
            ).encode()
            if images:
                for suffix, raw in _panel(case, arm, rows).items():
                    payloads[f"{stem}.{suffix}"] = raw
            gallery.append(
                f"<h2>{html.escape(stem)}</h2><p><a href='{stem}.csv'>Punktdaten</a> · <a href='{stem}.json'>Bäume und Zuordnung</a> · <a href='{stem}.formula.txt'>Originalformeln</a></p><pre>{html.escape(formulas)}</pre><img width='1000' src='{stem}.png' alt='{html.escape(stem)}'>"
            )
            for selector, selection in (("same_grid", same), ("off_grid", off)):
                all_scores.extend(
                    {"case": case, "arm": arm, "selector": selector, **score}
                    for score in selection["scores"]
                )
            print(
                f"Off-grid-Auswahl: {len(records)}/156 Pakete abgeschlossen ({case}, {arm}).",
                flush=True,
            )
    if len(records) != len(CASES) * len(ARMS):
        raise ValueError("Incomplete selection census.")
    payloads["candidate-scores.csv"] = plots._csv(all_scores)
    payloads["validation-observations.json"] = sources.json_bytes(
        {"grid_seed": GRID_SEED, "off_grid_time_s": grid.tolist(), "cases": generated}
    )
    summaries = _summaries(records)
    paired, contrasts = _contrasts(records)
    payloads["summary.csv"] = plots._csv(summaries)
    payloads["paired-contrasts.csv"] = plots._csv(paired)
    payloads["contrast-summary.csv"] = plots._csv(contrasts)
    payloads["index.html"] = ("\n".join(gallery) + "</body></html>\n").encode()
    report = {
        "format": FORMAT,
        "binding": binding,
        "execution_environment": _environment(),
        "archive_manifest_sha256": MANIFESTS,
        "consumed_original_sha256": dict(sorted(originals.used.items())),
        "original_source_scope": "hash_bound_files_beneath_supplied_root",
        "planned_packages": 156,
        "completed_packages": len(records),
        "planned_outputs": 468,
        "abstentions": sum(
            item["status"] == "abstained"
            for row in records
            for item in row["outputs"].values()
        ),
        "search_calls": 0,
        "fits": 0,
        "additional_observation_assumption": "independent_synthetic_repeat_of_known_signal; not_recoverable_from_existing_single_event",
        "selection_arithmetic": "original_binary_tree_order_numpy_float64; scaled_fsum_mse",
        "continuous_domain_status": "not_assessed",
        "confirmation_status": "known_development_data_only",
        "records": records,
        "summaries": summaries,
        "contrasts": contrasts,
    }
    return report, payloads


def run(source, output):
    """Publish a separate complete comparison while retaining every original byte."""
    source, output = Path(source).absolute(), Path(output).absolute()
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("Selection output must be separate from original data.")
    started, cpu_started = time.perf_counter(), time.process_time()
    publication.validate_output(output)
    call_path = publication.validate_output(
        output.with_name(output.name + "-call.json")
    )
    call_path.parent.mkdir(parents=True, exist_ok=True)
    running = sources.json_bytes({"format": FORMAT + "-call", "status": "running"})
    with call_path.open("xb") as stream:
        stream.write(running)

    def build(consumed):
        report, payloads = _compute(source, consumed, images=True)
        report["computation_wall_seconds"] = time.perf_counter() - started
        report["timing_scope"] = (
            "entry_through_computation_including_plots_excluding_publication"
        )
        summary = "# Off-grid-Auswahl aus gespeicherten Formeln\n\n156 ursprüngliche Pakete, drei Auswahlregeln, zusätzliche unabhängige synthetische Messinformation. Keine neue Suche oder Anpassung von Konstanten. Vollständige Formeln und Punktdaten in index.html. Alle Ergebnisse sind Entwicklungsbefunde; kontinuierliche Domain und unabhängige Bestätigung bleiben ungeprüft.\n"
        return report, summary, payloads

    failure, result = None, None
    try:
        result = publication.export_transaction(output, build, seconds=SECONDS)
        return result
    except BaseException as error:
        failure = error
        raise
    finally:
        call = {
            "format": FORMAT + "-call",
            "status": "completed" if failure is None else "aborted",
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu_started,
            "cpu_scope": "current_process_only",
            "scope": "owned_entry_through_publication_or_abort_excluding_final_cost_write",
            "error": None
            if failure is None
            else f"{type(failure).__name__}: {failure}",
            "source_report_sha256": None
            if result is None
            else sources.sha256(sources.json_bytes(result)),
        }
        try:
            _write_call(call_path, running, call)
        except BaseException as cost_error:
            if failure is not None:
                failure.add_note(
                    f"Could not record measured call costs: {type(cost_error).__name__}: {cost_error}"
                )
            else:
                try:
                    publication.revoke(
                        output, cost_error, publication.Deadline(SECONDS)
                    )
                except BaseException as revoke_error:  # noqa: BLE001 -- Preserve the original publication failure.
                    cost_error.add_note(
                        f"Could not revoke publication: {type(revoke_error).__name__}: {revoke_error}"
                    )
                raise


def _write_call(path, expected_running, record):
    """Replace only this call's exclusively reserved sidecar, retaining failures."""
    if path.is_symlink() or path.read_bytes() != expected_running:
        raise ValueError("Owned call-cost evidence changed during execution.")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(sources.json_bytes(record))
    if path.is_symlink() or path.read_bytes() != expected_running:
        raise ValueError("Owned call-cost evidence changed before publication.")
    temporary.replace(path)


def _verified_output(output):
    if output != output.resolve() or (output / publication.LOCK).exists():
        raise ValueError("Selection publication is missing or locked.")
    raw_manifest = (output / publication.MANIFEST).read_bytes()
    manifest = sources.read_json(raw_manifest)
    if {p.name for p in output.iterdir()} != set(manifest) | {publication.MANIFEST}:
        raise ValueError("Selection output inventory changed.")
    for name, digest in manifest.items():
        if len(sources.safe_name(name).parts) != 1:
            raise ValueError("Unsafe output manifest path.")
        path = output / name
        if path.is_symlink() or sources.sha256(path.read_bytes()) != digest:
            raise ValueError("Selection output bytes changed.")
    report = sources.read_json((output / publication.REPORT).read_bytes())
    if report.get("status") != "completed":
        raise ValueError("Selection report is not completed.")
    return raw_manifest, report


def _verified_call(output):
    path = output.with_name(output.name + "-call.json")
    if path != path.resolve() or not path.is_file():
        raise ValueError("Missing or linked selection call-cost evidence.")
    raw = path.read_bytes()
    record = sources.read_json(raw)
    report_raw = (output / publication.REPORT).read_bytes()
    report = sources.read_json(report_raw)
    computation = report.get("computation_wall_seconds")
    if (
        record.get("format") != FORMAT + "-call"
        or record.get("status") != "completed"
        or record.get("error") is not None
        or record.get("scope")
        != "owned_entry_through_publication_or_abort_excluding_final_cost_write"
        or record.get("cpu_scope") != "current_process_only"
        or record.get("source_report_sha256") != sources.sha256(report_raw)
        or any(
            type(record.get(key)) not in (int, float)
            or not math.isfinite(record[key])
            or record[key] < 0
            for key in ("wall_seconds", "cpu_seconds")
        )
    ):
        raise ValueError("Selection call-cost evidence is incomplete or inconsistent.")
    if (
        type(computation) not in (int, float)
        or not math.isfinite(computation)
        or not 0 <= computation <= record["wall_seconds"]
        or report.get("timing_scope")
        != "entry_through_computation_including_plots_excluding_publication"
    ):
        raise ValueError("Selection computation costs exceed the containing call.")
    return raw


def verify(source, output):
    """Recompute selections and numerical exports without new fits or searches."""
    output = Path(output).absolute()
    raw_manifest, saved = _verified_output(output)
    raw_call = _verified_call(output)
    clock = publication.Deadline(SECONDS)
    consumed = publication.Consumption(clock)
    with clock.active():
        current, payloads = _compute(source, consumed, images=False)
        for key in (
            "status",
            "computation_wall_seconds",
            "timing_scope",
            "execution_environment",
        ):
            saved.pop(key, None)
        current.pop("execution_environment")
        # Source hashes, not a later documentation-only HEAD, bind the replay.
        saved["binding"].pop("provenance", None)
        current["binding"].pop("provenance", None)
        if saved != current:
            raise ValueError("Selection scientific replay differs.")
        for name, raw in payloads.items():
            if (output / name).read_bytes() != raw:
                raise ValueError("Selection numerical replay differs: " + name)
        consumed.check()
    if _verified_output(output)[0] != raw_manifest:
        raise ValueError("Selection publication changed during verification.")
    if _verified_call(output) != raw_call:
        raise ValueError("Selection call-cost evidence changed during verification.")
    return {
        "format": FORMAT,
        "status": "verified",
        "packages": 156,
        "outputs": 468,
        "fits": 0,
        "search_calls": 0,
    }
