"""Reproduce the frozen seed inventory without generating study observations."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "a0ddad1ad7751ed858a40534a8a2fd41b73be523"
TOKEN_PATTERN = r"(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])"
SIGNALS = ("signal_200_4ms", "signal_250_6ms")
RESERVED = {
    "table_generator": 2026112701,
    "evaluation_grid": 2026112702,
    "support_grid": 2026112703,
    "technical_noise": 2026112704,
    "technical_background": 2026112705,
    "technical_search": 2026112706,
}


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True
    ).stdout


def historical_exclusions(root):
    """Scan every tracked UTF-8 blob at the fixed historical base."""
    listing = _git(root, "ls-tree", "-r", "-z", BASE_COMMIT)
    values, text_files, skipped = set(), [], []
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("Historical inventory contains a non-regular blob.")
        raw = _git(root, "cat-file", "blob", oid)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(path)
            continue
        text_files.append(path)
        for token in re.findall(TOKEN_PATTERN, text):
            value = int(token)
            if 0 < value < 2**31:
                values.add(value)
    serialized = "".join(f"{value}\n" for value in sorted(values)).encode()
    return values, {
        "base_commit": BASE_COMMIT,
        "historical_scope": "all tracked regular UTF-8 blobs at base_commit",
        "historical_tree_listing_sha256": hashlib.sha256(listing).hexdigest(),
        "historical_utf8_files": len(text_files),
        "historical_non_utf8_paths": skipped,
        "exclusion_regex": TOKEN_PATTERN,
        "excluded_count": len(values),
        "excluded_sha256": hashlib.sha256(serialized).hexdigest(),
        "excluded_values": sorted(values),
    }


def _draw(generator, count, excluded):
    accepted, rejected = [], []
    before = generator.bit_generator.state
    while len(accepted) < count:
        value = int(generator.integers(1, 2**31))
        if value in excluded:
            rejected.append(value)
            continue
        excluded.add(value)
        accepted.append(value)
    return accepted, {
        "bit_generator": "PCG64",
        "draws": count + len(rejected),
        "rejections": rejected,
        "state_before": before,
        "state_after": generator.bit_generator.state,
    }


def generate(root=ROOT):
    """Return the complete deterministic table, including its exclusion proof."""
    historical, metadata = historical_exclusions(root)
    excluded = historical | set(RESERVED.values())
    scientific_values, scientific_draw = _draw(
        np.random.Generator(np.random.PCG64(RESERVED["table_generator"])),
        480,
        excluded,
    )
    scientific = []
    values = iter(scientific_values)
    for signal_id in SIGNALS:
        for block in range(1, 31):
            for model in ("ar1", "white") if block <= 10 else ("ar1",):
                scientific.append(
                    {
                        "id": f"{signal_id}-{model}-{block:02d}",
                        "signal_id": signal_id,
                        "noise_model": model,
                        "block": block,
                        "noise_seed": next(values),
                        "background_seed": next(values),
                        "search_seeds": [next(values) for _ in range(4)],
                    }
                )
    technical_values, technical_draw = {}, {}
    for role in ("noise", "background", "search"):
        technical_values[role], technical_draw[role] = _draw(
            np.random.Generator(np.random.PCG64(RESERVED[f"technical_{role}"])),
            2,
            excluded,
        )
    technical = [
        {
            "id": f"{signal_id}-technical-ar1",
            "signal_id": signal_id,
            "noise_model": "ar1",
            "block": 0,
            "noise_seed": technical_values["noise"][index],
            "background_seed": technical_values["background"][index],
            "search_seeds": [technical_values["search"][index]],
        }
        for index, signal_id in enumerate(SIGNALS)
    ]
    return {
        "format": "ringdown-sr-main-study-seeds-1",
        **metadata,
        "numpy": np.__version__,
        "reserved": dict(RESERVED),
        "reserved_present_in_historical_tokens": sorted(
            historical & set(RESERVED.values())
        ),
        "scientific_generation": scientific_draw,
        "technical_generation": technical_draw,
        "scientific_cases": scientific,
        "technical_cases": technical,
    }


def encoded_table(table):
    return (json.dumps(table, indent=2, ensure_ascii=False) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path, help="Create a new seed table.")
    group.add_argument("--verify", type=Path, help="Verify an existing seed table.")
    args = parser.parse_args()
    expected = encoded_table(generate())
    if args.output is not None:
        with args.output.open("xb") as stream:
            stream.write(expected)
        print(f"Seed table created: {args.output}")
    else:
        if args.verify.is_symlink() or args.verify.read_bytes() != expected:
            raise ValueError("Seed table differs from its frozen generation recipe.")
        print("All 480 scientific and six technical seeds reproduced; no data drawn.")


if __name__ == "__main__":
    main()
