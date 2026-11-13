"""Freeze untouched confirmation signals, fresh seed pairs and a diagnostic grid."""

import argparse
import hashlib
import io
import json
import re
import subprocess
import zipfile
from fractions import Fraction
from pathlib import Path

import mpmath as mp
import numpy as np

from ringdown_sr.signals import ringdown_signal

BASE_COMMIT = "16f2e4533583ca7cced88799ffc3abb8d0052904"
SEED_GENERATOR = 2026111301
GRID_SEED = 2026111302
GRID_POINTS = 1024
GRID_ATTEMPTS = 100
BLOCKS = 10
PARAMETERS = ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
PARAMETER_BOUNDS = (("1/2", "1"), ("210", "320"), ("3/500", "1/100"), ("-1/2", "2/5"))
SIGNALS = (
    ("confirm_low", ("7/12", "685/3", "7/750", "-1/20"), (0, 0, 2, 1)),
    ("confirm_mid", ("11/12", "265", "1/150", "1/4"), (2, 1, 0, 2)),
    ("confirm_high", ("3/4", "905/3", "1/125", "-7/20"), (1, 2, 1, 0)),
)
SOURCE_INPUT = "data/restart_confirmation_inputs.npz"
SOURCE_INPUT_SHA256 = "02d03ebf37be51613b4e6303a2806dcb308fc344c544e82ff0dfd0d82000c8f2"
SIGNAL_SOURCE = "src/ringdown_sr/signals.py"


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def fingerprint(array):
    array = np.ascontiguousarray(array, dtype="<f8")
    return {
        "shape": list(array.shape),
        "dtype": "<f8",
        "sha256": sha256(array.tobytes()),
    }


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def source_at(repo, commit, path):
    return git(repo, "show", commit + ":" + path)


def historical_truths(repo, commit):
    """Collect complete documented signal definitions, never run old generators."""
    paths = (
        git(repo, "ls-tree", "-r", "--name-only", commit, "data").decode().splitlines()
    )
    found = set()

    def visit(value):
        if isinstance(value, dict):
            if all(key in value for key in PARAMETERS):
                found.add(tuple(float(value[key]).hex() for key in PARAMETERS))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for path in paths:
        if path.endswith(".json"):
            visit(json.loads(source_at(repo, commit, path)))
    return sorted(found)


def fresh_grid():
    """Use a private RNG and the previously specified nonlattice strata rule."""
    rng = np.random.Generator(np.random.PCG64(GRID_SEED))
    values = []
    for index in range(GRID_POINTS):
        for _ in range(GRID_ATTEMPTS):
            fraction = rng.random()
            value = (index + fraction) / GRID_POINTS * (127 / 4096)
            if 0 < fraction < 1 and not (value * 32768).is_integer():
                values.append(value)
                break
        else:
            raise ValueError("Could not generate the fixed nonlattice diagnostic grid.")
    return np.array(values, dtype="<f8")


def npz_bytes(arrays):
    """Write explicit ZIP metadata so regeneration never depends on the clock."""
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, array in arrays.items():
            stream = io.BytesIO()
            np.lib.format.write_array(
                stream,
                np.asarray(array, dtype="<f8"),
                version=(1, 0),
                allow_pickle=False,
            )
            info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, stream.getvalue())
    return target.getvalue()


def prepare(repo, commit):
    canonical = git(repo, "rev-parse", commit + "^{commit}").decode().strip()
    if commit != canonical or commit != BASE_COMMIT:
        raise ValueError("Use the frozen complete PR86 result-source commit.")
    original = source_at(repo, commit, SOURCE_INPUT)
    if sha256(original) != SOURCE_INPUT_SHA256:
        raise ValueError("Historical regular input axes changed.")
    source = source_at(repo, commit, SIGNAL_SOURCE)
    if source != Path(ringdown_signal.__code__.co_filename).read_bytes():
        raise ValueError("The loaded signal generator differs from its frozen source.")
    with np.load(io.BytesIO(original), allow_pickle=False) as old:
        times = old["time_s"].copy()
        inner = old["diagnostic_time_s"].copy()
        old_grid = old["irregular_time_s"].copy()
    if not np.array_equal(times, np.arange(128, dtype=np.float64) / 4096):
        raise ValueError("Unexpected original training axis.")
    expected_inner = (
        np.arange(127, dtype=np.float64)[:, None]
        + np.arange(1, 8, dtype=np.float64)[None, :] / 8
    ).reshape(-1) / 4096
    if not np.array_equal(inner, expected_inner):
        raise ValueError("Unexpected original intermediate axis.")
    grid = fresh_grid()
    if set(grid.tolist()) & set(old_grid.tolist()):
        raise ValueError("A fresh diagnostic point duplicates an old irregular point.")
    documented = historical_truths(repo, commit)

    # JSON seeds often occupy numeric-only lines, so inspect all tracked numbers.
    tracked = git(
        repo,
        "grep",
        "-h",
        "-I",
        "-E",
        "[0-9]+",
        commit,
        "--",
        "data",
        "docs",
        "src",
        "scripts",
        "tests",
    ).decode()
    used = {int(value) for value in re.findall(r"\b\d+\b", tracked)}
    used = {value for value in used if 0 < value < 2**31}
    rng = np.random.Generator(np.random.PCG64(SEED_GENERATOR))
    seeds = []
    while len(seeds) < 4 * BLOCKS * len(SIGNALS):
        value = int(rng.integers(1, 2**31))
        if value not in used and value not in seeds:
            seeds.append(value)

    config = {
        "format": "ringdown-sr-restart-budget-confirmation-protocol-1",
        "status": "frozen_before_implementation",
        "base_commit": commit,
        "purpose": "prospective_confirmation_on_untouched_fixed_signals",
        "restart_iterations": 1000,
        "long_iterations": 2000,
        "outer_iterations_per_package": 4000,
        "blocks_per_signal": BLOCKS,
        "search_calls": 180,
        "algorithm_outputs": 60,
        "paired_blocks": 30,
        "worker_seconds": 1800,
        "signal_seconds": 115200,
        "verify_seconds": 7200,
        "series_verify_seconds": 21600,
        "minimum_joint_successes": 8,
        "arms": [
            {"name": "R", "members": 4, "iterations": 1000, "seed_slots": [0, 1, 2, 3]},
            {"name": "L", "members": 2, "iterations": 2000, "seed_slots": [0, 1]},
        ],
        "coordinate": {"name": "t", "scale_hex": float(1).hex(), "unit": "s"},
        "execution": {
            "all_members_fresh": True,
            "historical_reuse": False,
            "checkpoint_continuation": False,
            "within_arm_order": "all_members_in_seed_slot_order",
            "shared_seed_slots": [0, 1],
            "shared_seed_calls_are_distinct": True,
        },
        "seed_generator": {
            "bit_generator": "PCG64",
            "seed": SEED_GENERATOR,
            "draw": "integers(1, 2**31); reject duplicates and every positive 31-bit integer token in tracked text under data/docs/src/scripts/tests",
            "exclusion_commit": commit,
            "excluded_values": len(used),
            "excluded_values_sha256": sha256(json_bytes(sorted(used))),
            "scope": "documented repository values; no claim about unknown external searches",
        },
        "source": {
            "commit": commit,
            "inputs_path": SOURCE_INPUT,
            "inputs_sha256": SOURCE_INPUT_SHA256,
            "reuse": "regular physical time axes only; all signal values and irregular points are new",
            "signal_source_path": SIGNAL_SOURCE,
            "signal_source_sha256": sha256(source),
        },
        "signal_design": {
            "rule": "fixed midpoints of three equal-width strata in each parameter; fixed rank permutations, no search-based choice",
            "parameter_order": list(PARAMETERS),
            "bounds_rational": dict(zip(PARAMETERS, PARAMETER_BOUNDS, strict=True)),
            "truth_definition": "the exact values of the stored binary64 parameters; rational midpoints are rounded once before signal evaluation",
            "documented_parameter_tuples": len(documented),
            "documented_parameter_tuples_sha256": sha256(json_bytes(documented)),
            "novelty_scope": "all complete signal parameter dictionaries in tracked data JSON at base_commit; no claim about unknown external searches",
            "generalization": "three fixed interior cases, not a random sample or a guarantee over the full parameter box",
        },
        "grid": {
            "reuse_source_points": False,
            "bit_generator": "PCG64",
            "seed": GRID_SEED,
            "points": GRID_POINTS,
            "attempts": GRID_ATTEMPTS,
            "rule": "one private-RNG point per equal-width stratum in (0,127/4096); reject exact 1/32768-grid hits",
            "new_threshold": None,
        },
        "profile": {
            "native_worker": "unchanged time_budget_worker; condition iterations",
            "local_iterations": 300,
            "additional_local_restarts": 5,
            "use_frequency": True,
            "use_frequency_in_tournament": True,
            "should_simplify": False,
            "warmup_maxsize_by": 0.0,
            "grammar": ["+", "-", "*", "/", "exp", "sin", "cos"],
            "population_count": 2,
            "population_size": 32,
            "cycles_per_iteration": 50,
            "maxsize": 20,
            "maxdepth": 20,
            "parsimony": 0.0,
            "optimizer_function_limit": 10000,
            "loss": "unweighted native MSE",
        },
        "selection": [
            "finite_native_training_loss_of_original_selected_candidate",
            "original_complexity",
            "member_seed_slot",
        ],
        "original_selection": [
            "finite_native_training_loss",
            "original_complexity",
            "original_front_index",
        ],
        "endpoint": "physical_curve_A_and_proven_original_family",
        "parameter_match": "not_assessed",
        "decision": {
            "primary_candidate": "R",
            "primary_confirmation": "R has at least 8 of 10 A-and-proven-original-family outputs on each of all three verified signals",
            "control_arm": "L",
            "control_gate": "report the same per-signal 8-of-10 condition separately for L; it never replaces the R decision",
            "comparison": "descriptive paired A/joint gains, losses, ties and observed costs; no superiority or significance gate",
            "uncertainty": "marginal exact two-sided 95-percent Clopper-Pearson intervals by signal/arm/endpoint under the Bernoulli assumption; no simultaneous guarantee",
            "no_pooled_success_rate": True,
            "no_automatic_control_adoption": True,
            "no_hybrid_selection": True,
            "no_automatic_profile_change": True,
            "no_additional_tuning_after_failure": True,
        },
        "technical": {
            "scope": "separate artificial fixtures; no scientific confirmation decision",
            "signals": ["fixture_a", "fixture_b"],
            "blocks_per_signal": 1,
            "restart_iterations": 1,
            "long_iterations": 2,
            "search_calls": 12,
            "algorithm_outputs": 4,
        },
        "signals": [],
    }
    arrays = {"time_s": times, "diagnostic_time_s": inner, "irregular_time_s": grid}
    checks = 0
    largest = mp.mpf(0)
    with mp.workdps(100):
        for index, (name, rational, strata) in enumerate(SIGNALS):
            for value, stratum, bounds in zip(
                rational, strata, PARAMETER_BOUNDS, strict=True
            ):
                low, high = map(Fraction, bounds)
                if Fraction(value) != low + Fraction(2 * stratum + 1, 6) * (high - low):
                    raise ValueError(
                        "Signal parameters differ from the fixed strata design."
                    )
            truth = {
                key: float(Fraction(value))
                for key, value in zip(PARAMETERS, rational, strict=True)
            }
            if tuple(truth[key].hex() for key in PARAMETERS) in documented:
                raise ValueError(
                    "A confirmation signal already occurs in documented data."
                )
            values = {
                key: ringdown_signal(axis, **truth)
                for key, axis in (
                    ("observed", times),
                    ("diagnostic_truth", inner),
                    ("irregular_truth", grid),
                )
            }
            for key, value in values.items():
                arrays[name + "_" + key] = value
            a, f, tau, phase = (mp.mpf(truth[key]) for key in PARAMETERS)
            for key, axis in (
                ("observed", times),
                ("diagnostic_truth", inner),
                ("irregular_truth", grid),
            ):
                for x, y in zip(axis, values[key], strict=True):
                    time = mp.mpf(float(x))
                    reference = (
                        a * mp.exp(-time / tau) * mp.cos(2 * mp.pi * f * time + phase)
                    )
                    largest = max(largest, abs(mp.mpf(float(y)) - reference) / a)
                    checks += 1
            offset = index * 4 * BLOCKS
            config["signals"].append(
                {
                    "name": name,
                    "truth": truth,
                    "truth_hex": {key: value.hex() for key, value in truth.items()},
                    "design_rational": dict(zip(PARAMETERS, rational, strict=True)),
                    "design_strata": dict(zip(PARAMETERS, strata, strict=True)),
                    "blocks": BLOCKS,
                    "seeds": [
                        seeds[offset + 4 * block : offset + 4 * (block + 1)]
                        for block in range(BLOCKS)
                    ],
                    "odd_block_order": ["R", "L"],
                    "even_block_order": ["L", "R"],
                    "arrays": {
                        key: fingerprint(value)
                        for key, value in {
                            "time_s": times,
                            "observed": values["observed"],
                            "diagnostic_time_s": inner,
                            "diagnostic_truth": values["diagnostic_truth"],
                        }.items()
                    },
                    "grid": {
                        "time_s": fingerprint(grid),
                        "truth": fingerprint(values["irregular_truth"]),
                    },
                }
            )
        if largest >= mp.mpf("1e-13"):
            raise ValueError(
                "Generated signal values disagree with the independent reference."
            )
        maximum = float(largest)
    raw = npz_bytes(arrays)
    config["inputs_sha256"] = sha256(raw)
    config["generation"] = {
        "numpy": np.__version__,
        "mpmath": mp.__version__,
        "recipe": "reuse regular time axes; new fixed binary64 signal parameters and private-PCG64 irregular grid; deterministic stored ZIP/NPY",
        "array_roles": len(arrays),
        "array_values": sum(value.size for value in arrays.values()),
        "input_bytes": len(raw),
        "truth_regenerated": True,
        "grid_regenerated": True,
        "coordinate_transformed": False,
        "independent_check": {
            "method": "mpmath 100 decimal places, exact stored Binary64 times/parameters, mathematical pi",
            "values_checked": checks,
            "max_absolute_error_over_amplitude": maximum,
            "bound": 1e-13,
        },
    }
    return {
        "data/restart_budget_confirmation_protocol.json": json_bytes(config),
        "data/restart_budget_confirmation_inputs.npz": raw,
    }, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, config = prepare(args.repo.resolve(), args.base_commit)
    paths = {name: args.output.resolve() / name for name in files}
    if args.check:
        if any(paths[name].read_bytes() != value for name, value in files.items()):
            raise ValueError("Generated protocol or inputs differ from recorded bytes.")
    else:
        if any(path.exists() for path in paths.values()):
            raise FileExistsError("Do not overwrite a confirmation protocol or inputs.")
        for name, value in files.items():
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            paths[name].write_bytes(value)
    print("Input SHA-256:", config["inputs_sha256"])
    print("Fresh calls:", config["search_calls"])
    print(
        "Independent values checked:",
        config["generation"]["independent_check"]["values_checked"],
    )
    for case in config["signals"]:
        print(case["name"], case["truth"], case["seeds"])


if __name__ == "__main__":
    main()
