"""Freeze fresh package seeds and unchanged physical inputs without running fits."""

import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

import numpy as np

BASE_COMMIT = "fbdb45003c777c878f833e08a2287b70daa00485"
SIGNALS = (("anchor", 2), ("variant_low", 2), ("variant_high", 4))
SEED_GENERATOR = 2026111202
SOURCE_INPUT = "data/restart_confirmation_inputs.npz"
SOURCE_PROTOCOL = "data/restart_confirmation_protocol.json"
SOURCE_INPUT_SHA256 = "02d03ebf37be51613b4e6303a2806dcb308fc344c544e82ff0dfd0d82000c8f2"
SOURCE_PROTOCOL_SHA256 = (
    "44d2a73a2189c5b4f06570c6abebcc8edceb2d1669925871c665f51520b1d6f9"
)
TIME_KEYS = ("time_s", "diagnostic_time_s", "irregular_time_s")


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


def prepare(repo, commit):
    canonical = git(repo, "rev-parse", commit + "^{commit}").decode().strip()
    if commit != canonical or commit != BASE_COMMIT:
        raise ValueError("Use the frozen complete PR84 base commit.")
    source_raw = source_at(repo, commit, SOURCE_INPUT)
    source_config_raw = source_at(repo, commit, SOURCE_PROTOCOL)
    source_config = json.loads(source_config_raw)
    if (
        sha256(source_raw) != SOURCE_INPUT_SHA256
        or sha256(source_config_raw) != SOURCE_PROTOCOL_SHA256
        or source_config["inputs_sha256"] != SOURCE_INPUT_SHA256
    ):
        raise ValueError("Source confirmation inputs or protocol hash changed.")
    with np.load(io.BytesIO(source_raw), allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    expected_keys = set(TIME_KEYS) | {
        name + "_" + role
        for name, _ in SIGNALS
        for role in ("observed", "diagnostic_truth", "irregular_truth")
    }
    if set(arrays) != expected_keys or any(
        value.dtype != np.dtype("float64")
        or value.ndim != 1
        or not np.all(np.isfinite(value))
        for value in arrays.values()
    ):
        raise ValueError("Changed original input roles or numeric representation.")
    cases = {case["name"]: case for case in source_config["signals"]}
    if set(cases) != {name for name, _ in SIGNALS}:
        raise ValueError("Changed original signal set.")
    for name, _ in SIGNALS:
        case = cases[name]
        original = {
            key: arrays[key if key.endswith("time_s") else name + "_" + key]
            for key in ("time_s", "observed", "diagnostic_time_s", "diagnostic_truth")
        }
        grid = {
            "time_s": arrays["irregular_time_s"],
            "truth": arrays[name + "_irregular_truth"],
        }
        if {key: fingerprint(value) for key, value in original.items()} != case[
            "arrays"
        ] or {key: fingerprint(value) for key, value in grid.items()} != case["grid"]:
            raise ValueError("Source signal or grid fingerprint changed.")

    # Include all numeric lines: a JSON seed commonly occupies its own line.
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
    while len(seeds) < 4 * sum(blocks for _, blocks in SIGNALS):
        value = int(rng.integers(1, 2**31))
        if value not in used and value not in seeds:
            seeds.append(value)

    config = {
        "format": "ringdown-sr-restart-budget-protocol-1",
        "status": "frozen_before_implementation",
        "base_commit": commit,
        "purpose": "bounded_development_budget_allocation",
        "restart_iterations": 1000,
        "long_iterations": 2000,
        "outer_iterations_per_package": 4000,
        "search_calls": 48,
        "algorithm_outputs": 16,
        "paired_blocks": 8,
        "worker_seconds": 1800,
        "signal_seconds": 50400,
        "verify_seconds": 7200,
        "series_verify_seconds": 21600,
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
            "protocol_path": SOURCE_PROTOCOL,
            "protocol_sha256": SOURCE_PROTOCOL_SHA256,
            "reuse": "byte-identical original NPZ with all physical time/truth values and irregular points; no signal or grid regeneration",
        },
        "grid": {
            "reuse_source_points": True,
            "seed": source_config["grid_seed"],
            "points": source_config["grid_points"],
            "attempts": source_config["grid_attempts"],
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
            "restart_candidate": "R A-count and joint-count are no lower on every signal, and R joint-count is strictly higher on at least one signal",
            "long_candidate": "reverse directional condition with R and L exchanged",
            "unchanged_counts": "same A-count and joint-count on all signals; costs remain descriptive",
            "mixed": "all other complete verified outcomes; retain uncertainty, no automatic profile adoption",
            "no_automatic_profile_change": True,
            "no_confirmation_gate": True,
        },
        "signals": [],
    }
    offset = 0
    for name, blocks in SIGNALS:
        case = cases[name]
        config["signals"].append(
            {
                "name": name,
                "truth": case["truth"],
                "blocks": blocks,
                "seeds": [
                    seeds[offset + 4 * block : offset + 4 * (block + 1)]
                    for block in range(blocks)
                ],
                "odd_block_order": ["R", "L"],
                "even_block_order": ["L", "R"],
                "arrays": case["arrays"],
                "grid": case["grid"],
            }
        )
        offset += 4 * blocks
    # Preserve the entire source archive, including ZIP metadata; do not repack.
    config["inputs_sha256"] = SOURCE_INPUT_SHA256
    config["generation"] = {
        "numpy": np.__version__,
        "recipe": "byte-identical source NPZ copy; independent PCG64 seed-slot generation",
        "original_array_roles": len(arrays),
        "original_array_values": sum(value.size for value in arrays.values()),
        "input_bytes": len(source_raw),
        "truth_regenerated": False,
        "grid_regenerated": False,
        "coordinate_transformed": False,
    }
    return {
        "data/restart_budget_protocol.json": json_bytes(config),
        "data/restart_budget_inputs.npz": source_raw,
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
            raise ValueError("Generated protocol or input differs from recorded bytes.")
    else:
        if any(path.exists() for path in paths.values()):
            raise FileExistsError("Do not overwrite a protocol or input file.")
        for name, value in files.items():
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            paths[name].write_bytes(value)
    print("Input SHA-256:", config["inputs_sha256"])
    print("Unchanged input array roles:", config["generation"]["original_array_roles"])
    print("Fresh calls:", config["search_calls"])
    for case in config["signals"]:
        print(case["name"], case["seeds"])


if __name__ == "__main__":
    main()
