"""Export and compare recorded schema-3 evidence without importing Julia or PySR."""

import argparse
import hashlib
import io
import json
import math
import platform
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

FORMAT = "ringdown-sr-portability-diagnostics-1"
CASES = ("white", "ar1")
ARMS = ("ordinary", "known_covariance", "estimated_covariance")
OPERATIONAL_PARAMETERS = {"output_directory"}


def json_bytes(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def read_json(content):
    def reject(value):
        raise ValueError(f"Nonstandard JSON number: {value}")

    return json.loads(content, parse_constant=reject)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Artifact escapes its source directory: {name}")
    return path


def outside(output, *sources):
    output = Path(output).resolve()
    if any(output.is_relative_to(Path(source).resolve()) for source in sources):
        raise ValueError("Output must be outside the source evidence directories.")
    return output


def canonical(array):
    values = np.asarray(array)
    if values.ndim == 0:
        raise ValueError("Diagnostic arrays must have at least one dimension.")
    if values.dtype.kind != "f" or values.dtype.itemsize != 8:
        raise ValueError("Diagnostic arrays must be float64; no precision conversion.")
    if not np.all(np.isfinite(values)):
        raise ValueError("Diagnostic arrays must be finite.")
    return np.ascontiguousarray(values, dtype="<f8")


def fingerprint(array):
    values = canonical(array)
    return {
        "shape": list(values.shape),
        "dtype": "<f8",
        "sha256": digest(values.tobytes()),
    }


def npz_arrays(content):
    with np.load(io.BytesIO(content), allow_pickle=False) as stored:
        return {name: canonical(stored[name]) for name in stored.files}


def collect_case(root, case, arrays):
    """Verify checksums of every consumed artifact, keeping run provenance intact."""
    metadata_bytes = inside(root, "metadata.json").read_bytes()
    metadata = read_json(metadata_bytes)
    if metadata["schema_version"] != 3 or metadata["status"] != "success":
        raise ValueError("Diagnostics require a completed successful schema-3 run.")
    hashes = {"metadata.json": digest(metadata_bytes)}

    def read(name):
        content = inside(root, name).read_bytes()
        actual = digest(content)
        if metadata["artifact_sha256"].get(name) != actual:
            raise ValueError(f"Missing or mismatched source checksum: {name}")
        hashes[name] = actual
        return content

    def document(name):
        return read_json(read(name))

    def add(name, value):
        key = f"{case}.{name}"
        if key in arrays:
            raise ValueError(f"Duplicate diagnostic array: {key}")
        arrays[key] = canonical(value)
        return key

    result = document("result.json")
    if result["schema_version"] != 3 or result["status"] != "success":
        raise ValueError("The schema-3 result is not successful.")
    shared = npz_arrays(read(result["shared_inputs_file"]))
    if set(shared) != {
        "time_s",
        "signal",
        "noise",
        "observed",
        "covariance_true",
        "covariance_estimated",
    }:
        raise ValueError("Unexpected shared input array set.")
    for name, values in shared.items():
        add("shared." + name, values)
    for role in ("train", "validation", "check"):
        values = np.loadtxt(
            io.BytesIO(read(f"reference/background_{role}.csv")),
            delimiter=",",
            ndmin=2,
        )
        add("background." + role, values)
    reference = document("reference/metadata.json")
    reference_result = document("reference/result.json")
    if reference["status"] != "success" or reference_result["status"] != "success":
        raise ValueError("The classical reference stage is not successful.")
    record = {
        "configuration": document("resolved_config.json"),
        "provenance": {
            "pilot": metadata["provenance"],
            "reference": reference["provenance"],
        },
        "recorded_environment": {
            "pilot": metadata["environment"],
            "reference": reference["environment"],
        },
        "reference_rng": reference["random"],
        "covariance_selection": reference_result["covariance_estimation"],
        "arms": {},
        "source_file_sha256": hashes,
    }
    for arm in ARMS:
        prefix = f"symbolic/{arm}/"
        summary = result["symbolic_arms"][arm]
        if summary["status"] != "success":
            raise ValueError(f"Unsuccessful symbolic arm: {arm}")
        worker = document(prefix + "metadata.json")
        worker_initial = document(prefix + "metadata_initial.json")
        if worker["provenance"] != worker_initial["provenance"]:
            raise ValueError("Worker initial provenance was replaced.")
        inputs = npz_arrays(read(prefix + "inputs.npz"))
        expected = {"time_s", "observed"} | (
            set() if arm == "ordinary" else {"covariance"}
        )
        if set(inputs) != expected:
            raise ValueError("Unexpected arm input array set.")
        for name, values in inputs.items():
            source = (
                shared[
                    "covariance_true"
                    if arm == "known_covariance"
                    else "covariance_estimated"
                ]
                if name == "covariance"
                else shared[name]
            )
            if fingerprint(values) != fingerprint(source):
                raise ValueError(f"Arm input differs from shared input: {arm}/{name}")
            add(f"{arm}.input.{name}", values)
        front = document(prefix + "result.json")
        selected = front["candidates"][front["selected_index"]]
        for name in ("prediction", "residual"):
            add(f"{arm}.selected.{name}", np.asarray(selected[name], dtype="<f8"))
        fields = document(prefix + "backend_options.json")
        backend = {
            field["name"]: {k: field[k] for k in ("type", "value")} for field in fields
        }
        if len(backend) != len(fields):
            raise ValueError("Duplicate backend option name.")
        record["arms"][arm] = {
            "request": document(prefix + "request.json"),
            "rng": front["rng"],
            "pysr_parameters": document(prefix + "pysr_parameters.json"),
            "backend_options_repr": backend,
            "recorded_environment": {
                "before_fit": worker["environment"],
                "after_search": worker["environment_after_search"],
            },
            "provenance": {k: worker[k] for k in ("provenance", "worker_provenance")},
            "adapter_sources": {
                k: worker[k]
                for k in (
                    "adapter_source_sha256",
                    "worker_adapter_source_sha256",
                )
            },
            "julia_version": worker["julia_version"],
            "symbolic_regression_version": worker["symbolic_regression_version"],
            "loss_context": {
                k: front[k]
                for k in (
                    "baseline_loss",
                    "use_baseline",
                    "cost_normalization",
                    "zero_expression_loss",
                    "zero_expression_loss_status",
                )
            },
            "candidate_count": len(front["candidates"]),
            "front": [
                {k: candidate[k] for k in ("tree", "loss", "complexity")}
                for candidate in front["candidates"]
            ],
            "selected_index": front["selected_index"],
            "metrics": summary["metrics"],
        }
    record["arrays"] = {
        k: fingerprint(v) for k, v in arrays.items() if k.startswith(case + ".")
    }
    return record


def export(root, output, label):
    root = Path(root).resolve()
    output = outside(output, root)
    if not label.strip():
        raise ValueError("A nonempty machine label is required.")
    arrays = {}
    runs = {case: collect_case(root / case, case, arrays) for case in CASES}
    report = {
        "format": FORMAT,
        "label": label,
        "runs": runs,
        "exporter": {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "source_sha256": digest(Path(__file__).read_bytes()),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "role": "export_only; not the recorded search environment",
        },
        "scope": "consumed source checksums and input identity; not a new loss audit or search",
        "limitations": [
            "Differences do not establish causation or statistical performance.",
            "Backend options are recorded representations, not semantic equivalence proofs.",
            "Complete Julia RNG checkpoints and explicit Julia CPU-target/BLAS configuration were not recorded.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    with (output / "arrays.npz").open("xb") as file:
        np.savez_compressed(file, **arrays)
    (output / "report.json").write_bytes(json_bytes(report))
    (output / "checksums.json").write_bytes(
        json_bytes(
            {
                name: digest((output / name).read_bytes())
                for name in ("report.json", "arrays.npz")
            }
        )
    )
    print(f"Diagnoseexport gespeichert: {output}")
    for case, run in runs.items():
        print(f"{case}: Commit {run['provenance']['pilot']['git']['commit']}")
        for name in (
            "time_s",
            "signal",
            "noise",
            "observed",
            "covariance_true",
            "covariance_estimated",
        ):
            print(f"  {name}: {run['arrays'][case + '.shared.' + name]['sha256']}")
        for arm, record in run["arms"].items():
            print(
                f"  {arm}: backend_seed={record['rng']['backend_seed']}, Kandidaten={record['candidate_count']}"
            )
    return report


def load_bundle(root):
    root = Path(root).resolve()
    checksums = read_json(inside(root, "checksums.json").read_bytes())
    if set(checksums) != {"report.json", "arrays.npz"}:
        raise ValueError("Unexpected diagnostic bundle manifest.")
    content = {name: inside(root, name).read_bytes() for name in checksums}
    if any(digest(content[name]) != expected for name, expected in checksums.items()):
        raise ValueError("Diagnostic bundle checksum mismatch.")
    report = read_json(content["report.json"])
    if report["format"] != FORMAT or set(report["runs"]) != set(CASES):
        raise ValueError("Unsupported diagnostic bundle format or case set.")
    arrays = npz_arrays(content["arrays.npz"])
    descriptions = {}
    for case, run in report["runs"].items():
        for name, info in run["arrays"].items():
            if not name.startswith(case + ".") or name in descriptions:
                raise ValueError("Invalid or duplicate diagnostic array key.")
            descriptions[name] = info
    if set(arrays) != set(descriptions) or any(
        fingerprint(a) != descriptions[k] for k, a in arrays.items()
    ):
        raise ValueError("Array snapshot differs from its recorded descriptors.")
    return report, arrays


def differing_paths(left, right, path=""):
    if type(left) is not type(right):
        return [path or "/"]
    if isinstance(left, dict):
        return [
            item
            for key in sorted(left.keys() | right.keys())
            for item in (
                [path + "/" + key]
                if key not in left or key not in right
                else differing_paths(left[key], right[key], path + "/" + key)
            )
        ]
    if isinstance(left, list):
        if len(left) != len(right):
            return [path or "/"]
        return [
            item
            for i, (a, b) in enumerate(zip(left, right, strict=True))
            for item in differing_paths(a, b, path + f"/{i}")
        ]
    return [] if left == right else [path or "/"]


def array_difference(left, right):
    if left.shape != right.shape:
        return {
            "status": "shape_mismatch",
            "left_shape": list(left.shape),
            "right_shape": list(right.shape),
        }
    scale = max(
        float(np.max(np.abs(left), initial=0)), float(np.max(np.abs(right), initial=0))
    )
    normalized = (
        0.0
        if scale == 0
        else float(np.max(np.abs(left / scale - right / scale), initial=0))
    )
    # Subtract first when representable: normalization can erase a one-ULP gap.
    with np.errstate(over="ignore", under="ignore"):
        absolute = float(np.max(np.abs(left - right), initial=0))
    if math.isfinite(absolute):
        normalized = 0.0 if scale == 0 else absolute / scale
    bits = int(np.count_nonzero(left.view("<u8") != right.view("<u8")))
    values = int(np.count_nonzero(left != right))
    return {
        "status": "compared",
        "bitwise_equal": bits == 0,
        "numeric_equal": values == 0,
        "elements_with_different_bits": bits,
        "elements_with_different_values": values,
        "common_max_abs_scale": scale,
        "max_normalized_difference": normalized,
        "max_absolute_difference": absolute if math.isfinite(absolute) else None,
        "absolute_difference_status": "finite"
        if math.isfinite(absolute)
        else "exceeds_float64_range",
    }


def compare(left_root, right_root, output):
    output = outside(output, left_root, right_root)
    left, left_arrays = load_bundle(left_root)
    right, right_arrays = load_bundle(right_root)
    comparison = {
        "format": FORMAT + "/comparison",
        "left_label": left["label"],
        "right_label": right["label"],
        "scope": "descriptive evidence comparison; no causal attribution",
        "same_exporter_source": left["exporter"]["source_sha256"]
        == right["exporter"]["source_sha256"],
        "runs": {},
    }
    for case in CASES:
        a, b = left["runs"][case], right["runs"][case]
        details = {
            name: differing_paths(a[name], b[name])
            for name in (
                "configuration",
                "reference_rng",
                "covariance_selection",
                "provenance",
                "recorded_environment",
            )
        }
        details["arrays"] = {}
        for key in sorted(a["arrays"].keys() | b["arrays"].keys()):
            details["arrays"][key] = (
                {
                    "status": "missing_left"
                    if key not in left_arrays
                    else "missing_right"
                }
                if key not in left_arrays or key not in right_arrays
                else array_difference(left_arrays[key], right_arrays[key])
            )
        details["arms"] = {}
        for arm in ARMS:
            first, second = a["arms"][arm], b["arms"][arm]
            record = {
                name: differing_paths(first[name], second[name])
                for name in (
                    "request",
                    "rng",
                    "recorded_environment",
                    "provenance",
                    "adapter_sources",
                    "julia_version",
                    "symbolic_regression_version",
                    "loss_context",
                    "front",
                    "selected_index",
                    "metrics",
                )
            }
            for name in ("pysr_parameters", "backend_options_repr"):
                record[name] = differing_paths(
                    {
                        k: v
                        for k, v in first[name].items()
                        if k not in OPERATIONAL_PARAMETERS
                    },
                    {
                        k: v
                        for k, v in second[name].items()
                        if k not in OPERATIONAL_PARAMETERS
                    },
                )
                record[name + "_operational"] = differing_paths(
                    {
                        k: v
                        for k, v in first[name].items()
                        if k in OPERATIONAL_PARAMETERS
                    },
                    {
                        k: v
                        for k, v in second[name].items()
                        if k in OPERATIONAL_PARAMETERS
                    },
                )
            details["arms"][arm] = record
        comparison["runs"][case] = details
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as file:
        file.write(json_bytes(comparison))
    for case, run in comparison["runs"].items():
        changed = [
            name
            for name, value in run["arrays"].items()
            if not value.get("bitwise_equal", False)
        ]
        print(f"{case}: {len(changed)} Arrays mit unterschiedlichen Bits oder Formen")
        for name in changed:
            print("  " + name)
        for arm, record in run["arms"].items():
            print(
                f"  {arm}: Front verschieden={bool(record['front'])}; RNG verschieden={bool(record['rng'])}"
            )
    print(f"Vergleich gespeichert: {output}")
    return comparison


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export_parser = commands.add_parser("export")
    export_parser.add_argument(
        "root", type=Path, help="Paired results directory containing white/ and ar1/"
    )
    export_parser.add_argument("--output", type=Path, required=True)
    export_parser.add_argument(
        "--label", required=True, help="For example manjaro or wsl2"
    )
    compare_parser = commands.add_parser("compare")
    compare_parser.add_argument("left", type=Path)
    compare_parser.add_argument("right", type=Path)
    compare_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            export(args.root, args.output, args.label)
        else:
            compare(args.left, args.right, args.output)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        parser.exit(2, f"Diagnose fehlgeschlagen: {error}\n")


if __name__ == "__main__":
    main()
