"""Prepare fixed coordinate-comparison inputs and seeds without searches or fits."""

import argparse
import hashlib
import io
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

SIGNALS = (("anchor", 2), ("variant_low", 2), ("variant_high", 4))
SEED_GENERATOR = 2026111201
SOURCE_INPUT = "data/restart_confirmation_inputs.npz"
SOURCE_PROTOCOL = "data/restart_confirmation_protocol.json"
TIME_KEYS = ("time_s", "diagnostic_time_s", "irregular_time_s")
COORDINATE_KEYS = ("time_u", "diagnostic_time_u", "irregular_time_u")


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
    if commit != canonical:
        raise ValueError("Use the complete immutable base commit.")
    source_raw = source_at(repo, commit, SOURCE_INPUT)
    source_config_raw = source_at(repo, commit, SOURCE_PROTOCOL)
    source_config = json.loads(source_config_raw)
    if sha256(source_raw) != source_config["inputs_sha256"]:
        raise ValueError("Source confirmation archive does not match its protocol.")
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
        raise ValueError("Changed confirmation input roles or numeric representation.")
    cases = {case["name"]: case for case in source_config["signals"]}
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
    checked_values = 0
    for source_key, target_key in zip(TIME_KEYS, COORDINATE_KEYS, strict=True):
        physical = arrays[source_key]
        scaled = np.ldexp(physical, 5)
        if not np.all(np.isfinite(scaled)):
            raise ValueError("Nonfinite normalized coordinate.")
        for physical_value, normalized_value in zip(physical, scaled, strict=True):
            if Fraction(float(normalized_value)) != 32 * Fraction(
                float(physical_value)
            ):
                raise ValueError("Coordinate transform is not exact over binary64.")
            checked_values += 1
        if fingerprint(np.ldexp(scaled, -5)) != fingerprint(physical):
            raise ValueError("Coordinate roundtrip changed physical Float64 bits.")
        arrays[target_key] = scaled

    # Read all tracked text lines, not only lines containing the word "seed".
    # JSON seed arrays commonly put each seed on its own numeric line.
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
    while len(seeds) < sum(blocks for _, blocks in SIGNALS):
        value = int(rng.integers(1, 2**31))
        if value not in used and value not in seeds:
            seeds.append(value)

    config = {
        "format": "ringdown-sr-time-coordinate-protocol-1",
        "status": "frozen_before_implementation",
        "base_commit": commit,
        "purpose": "bounded_development_coordinate_comparison",
        "outer_iterations": 2000,
        "search_calls": 16,
        "paired_blocks": 8,
        "worker_seconds": 1800,
        "signal_seconds": 21600,
        "verify_seconds": 7200,
        "series_verify_seconds": 21600,
        "arms": [
            {"name": "T", "coordinate": "t", "scale_hex": float(1).hex(), "unit": "s"},
            {
                "name": "U",
                "coordinate": "32*t",
                "scale_hex": float(32).hex(),
                "unit": "s",
            },
        ],
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
            "inputs_sha256": sha256(source_raw),
            "protocol_path": SOURCE_PROTOCOL,
            "protocol_sha256": sha256(source_config_raw),
            "reuse": "all original physical time/truth bytes and irregular points; no regeneration of signal values",
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
            "finite_native_training_loss",
            "original_complexity",
            "original_front_index",
        ],
        "endpoint": "physical_curve_A_and_proven_original_family",
        "parameter_match": "not_assessed",
        "decision": {
            "normalization_candidate": "U A-count and joint-count are no lower on every signal, and U joint-count is strictly higher on at least one signal",
            "raw_coordinate_supported": "reverse directional condition with T and U exchanged",
            "unchanged_counts": "same A-count and joint-count on all signals; costs remain descriptive",
            "mixed": "all other complete verified outcomes; retain uncertainty, no automatic coordinate adoption",
            "no_automatic_profile_change": True,
            "no_confirmation_gate": True,
            "next_budget_plan": "separate frozen 4x1000 versus 2x2000; choose coordinate explicitly after this diagnosis",
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
                "seeds": seeds[offset : offset + blocks],
                "odd_block_order": ["T", "U"],
                "even_block_order": ["U", "T"],
                "arrays": case["arrays"],
                "grid": case["grid"],
                "normalized_times": {
                    key: fingerprint(arrays[key]) for key in COORDINATE_KEYS
                },
            }
        )
        offset += blocks
    stream = io.BytesIO()
    np.savez(stream, **arrays)
    raw = stream.getvalue()
    config["inputs_sha256"] = sha256(raw)
    config["generation"] = {
        "numpy": np.__version__,
        "recipe": "copy source arrays; add exactly scaled time axes using ldexp(x,5)",
        "coordinate_values_checked_with_exact_rationals": checked_values,
        "coordinate_roundtrip_bits": "identical",
        "truth_regenerated": False,
    }
    return {
        "data/time_coordinate_protocol.json": json_bytes(config),
        "data/time_coordinate_inputs.npz": raw,
    }, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, config = prepare(args.source_repo.resolve(), args.base_commit)
    paths = {name: args.output.resolve() / name for name in files}
    if args.check:
        if any(paths[name].read_bytes() != raw for name, raw in files.items()):
            raise ValueError("Generated draft differs from the recorded files.")
    else:
        if any(path.exists() for path in paths.values()):
            raise FileExistsError("Do not overwrite a protocol or input file.")
        for name, raw in files.items():
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            paths[name].write_bytes(raw)
    print("Input SHA-256:", config["inputs_sha256"])
    print(
        "Exact coordinate values checked:",
        config["generation"]["coordinate_values_checked_with_exact_rationals"],
    )
    for case in config["signals"]:
        print(case["name"], case["seeds"])


if __name__ == "__main__":
    main()
