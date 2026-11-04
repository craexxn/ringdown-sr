"""Read-only parameter diagnostics for one complete recorded schema-3 pilot."""

import io
import json
import math
from pathlib import Path, PurePosixPath

import numpy as np

from .parameters import analyze_tree
from .pilot import _environment, _json_bytes, _provenance, _sha256, _utc_now
from .symbolic import FORMAT as ARM_FORMAT
from .symbolic import _check_prediction_replay, evaluate_tree

FORMAT = "ringdown-sr-parameter-diagnostics-1"
ARMS = ("ordinary", "known_covariance", "estimated_covariance")


def _read_json(content):
    def reject(value):
        raise ValueError(f"Nonfinite JSON number: {value}")

    def number(value):
        result = float(value)
        return result if math.isfinite(result) else reject(value)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        content, parse_constant=reject, parse_float=number, object_pairs_hook=pairs
    )


def _inside(root, name):
    if (
        type(name) is not str
        or not name
        or "\\" in name
        or ":" in name
        or PurePosixPath(name).is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
    ):
        raise ValueError(f"Invalid source artifact path: {name!r}")
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Source artifact escapes its directory: {name}")
    return path


def _manifest(root, value):
    if type(value) is not dict or not value:
        raise ValueError("A nonempty source checksum manifest is required.")
    for name, expected in value.items():
        _inside(root, name)
        if (
            type(expected) is not str
            or len(expected) != 64
            or any(char not in "0123456789abcdef" for char in expected)
        ):
            raise ValueError(f"Invalid source checksum: {name}")
    return value


class _Source:
    """Keep consumed bytes and their source checksums, including the trust anchor."""

    def __init__(self, root):
        self.root = root
        content = _inside(root, "metadata.json").read_bytes()
        self.metadata = _read_json(content)
        self.hashes = {"metadata.json": _sha256(content)}
        self.manifest = _manifest(root, self.metadata["artifact_sha256"])

    def read(self, name, *, worker_manifest=None, worker_name=None):
        content = _inside(self.root, name).read_bytes()
        digest = _sha256(content)
        if self.manifest.get(name) != digest:
            raise ValueError(f"Missing or mismatched source checksum: {name}")
        if worker_manifest is not None and worker_manifest.get(worker_name) != digest:
            raise ValueError(f"Missing or mismatched worker checksum: {name}")
        if name in self.hashes and self.hashes[name] != digest:
            raise ValueError(f"Source changed during diagnosis: {name}")
        self.hashes[name] = digest
        return content

    def document(self, name, **kwargs):
        return _read_json(self.read(name, **kwargs))

    def recheck(self):
        for name, expected in self.hashes.items():
            if _sha256(_inside(self.root, name).read_bytes()) != expected:
                raise ValueError(f"Source changed during diagnosis: {name}")


def _successful(record, schema):
    if (
        type(record["schema_version"]) is not int
        or record["schema_version"] != schema
        or record["status"] != "success"
    ):
        raise ValueError(f"A successful schema-{schema} source is required.")


def _times(content, n_samples, expected_names=None):
    with np.load(io.BytesIO(content), allow_pickle=False) as stored:
        if (
            "time_s" not in stored.files
            or len(stored.files) != len(set(stored.files))
            or (expected_names is not None and set(stored.files) != expected_names)
        ):
            raise ValueError("Unexpected saved input array names.")
        # Only time samples enter parameter diagnosis; truth/targets are not read.
        values = stored["time_s"].copy()
    if (
        values.dtype.kind != "f"
        or values.dtype.itemsize != 8
        or values.shape != (n_samples,)
        or not np.all(np.isfinite(values))
    ):
        raise ValueError("Saved time samples must be a finite Float64 vector.")
    return values


def _fingerprint(values):
    return {
        "shape": list(values.shape),
        "dtype": "<f8",
        "sha256": _sha256(np.ascontiguousarray(values, dtype="<f8").tobytes()),
    }


def _node_count(tree):
    return 1 + sum(_node_count(child) for child in tree.get("children", []))


def _candidate(
    candidate, index, selected_index, time_s, fs, *, prediction_verifier=None
):
    # analyze_tree validates the bounded complete tree before any other traversal.
    analysis = analyze_tree(candidate["tree"], time_s, sample_rate_hz=fs)
    if (
        type(candidate["complexity"]) is not int
        or candidate["complexity"] != _node_count(candidate["tree"])
        or type(candidate["loss"]) not in (int, float)
        or not math.isfinite(candidate["loss"])
        or candidate["loss"] < 0
        or type(candidate["display_equation"]) is not str
    ):
        raise ValueError("Invalid recorded candidate fields.")
    saved = np.asarray(candidate["prediction"])
    if saved.dtype.kind not in "fiu" or saved.shape != time_s.shape:
        raise ValueError("Saved prediction must cover the recorded sample window.")
    python = evaluate_tree(candidate["tree"], time_s)
    replay = (
        _check_prediction_replay(python, saved)
        if prediction_verifier is None
        else prediction_verifier(candidate, time_s, python, saved)
    )
    return {
        "source_index": index,
        "is_selected": index == selected_index,
        "source_candidate": candidate,
        "saved_prediction_replay": {"status": "passed", **replay},
        "analysis": analysis,
    }


def _collect(root):
    source = _Source(root)
    metadata = source.metadata
    _successful(metadata, 3)
    initial = source.document("metadata_initial.json")
    if initial["provenance"] != metadata["provenance"]:
        raise ValueError("The original pilot provenance was replaced.")
    result = source.document("result.json")
    _successful(result, 3)
    if (
        result["stage"] != "complete"
        or result["evaluation_scope"] != "fitted_samples_only"
        or set(result["symbolic_arms"]) != set(ARMS)
        or result["reference"]["status"] != "success"
        or result["reference"]["result_file"] != "reference/result.json"
    ):
        raise ValueError("A complete three-arm schema-3 source is required.")
    reference = source.document("reference/metadata.json")
    reference_result = source.document("reference/result.json")
    _successful(reference, 2)
    _successful(reference_result, 2)
    config = source.document("resolved_config.json")
    if type(config["schema_version"]) is not int or config["schema_version"] != 3:
        raise ValueError("Expected a resolved schema-3 configuration.")
    sampling = config["sampling"]
    n_samples, fs = sampling["n_samples"], sampling["sample_rate_hz"]
    if type(n_samples) is not int or n_samples <= 0:
        raise ValueError("The recorded sample count must be a positive integer.")
    # The scalar rate is validated by analyze_tree, including unsupported trees.
    time_s = _times(source.read(result["shared_inputs_file"]), n_samples)
    arms = {}
    for name in ARMS:
        prefix = f"symbolic/{name}/"
        summary = result["symbolic_arms"][name]
        if (
            summary["status"] != "success"
            or summary["result_file"] != prefix + "result.json"
        ):
            raise ValueError(f"Incomplete or misassigned symbolic arm: {name}")
        checksums = _manifest(
            _inside(root, prefix.rstrip("/")),
            source.document(prefix + "checksums.json"),
        )

        def read(filename, prefix=prefix, checksums=checksums):
            return source.read(
                prefix + filename, worker_manifest=checksums, worker_name=filename
            )

        def document(filename):
            return _read_json(read(filename))

        worker = document("metadata.json")
        worker_initial = document("metadata_initial.json")
        if (
            worker["phase"] != "success"
            or worker["provenance"] != worker_initial["provenance"]
        ):
            raise ValueError(f"Incomplete worker or replaced provenance: {name}")
        request = document("request.json")
        if request != {"format": ARM_FORMAT, "budget": config["symbolic_search"]}:
            raise ValueError("Recorded worker request and configuration disagree.")
        expected_names = {"time_s", "observed"} | (
            set() if name == "ordinary" else {"covariance"}
        )
        arm_times = _times(read("inputs.npz"), n_samples, expected_names)
        if _fingerprint(time_s) != _fingerprint(arm_times):
            raise ValueError(f"Arm and shared time samples differ: {name}")
        front = document("result.json")
        if (
            front["format"] != ARM_FORMAT
            or front["evaluation_scope"] != "fitted_samples_only"
            or type(front["candidates"]) is not list
            or not front["candidates"]
        ):
            raise ValueError("Expected a nonempty recorded full candidate front.")
        selected = front["selected_index"]
        if type(selected) is not int or not 0 <= selected < len(front["candidates"]):
            raise ValueError("Invalid recorded selected_index.")
        chosen = front["candidates"][selected]
        selection = summary["selected"]
        if (
            type(selection["index"]) is not int
            or selection["index"] != selected
            or selection["complexity"] != chosen["complexity"]
            or selection["training_loss"] != chosen["loss"]
            or selection["display_equation"] != chosen["display_equation"]
            or selection["parameter_interpretation"] != "not_attempted"
        ):
            raise ValueError("Pilot and worker candidate selection disagree.")
        arms[name] = {
            "source_result_file": prefix + "result.json",
            "source_result_sha256": source.hashes[prefix + "result.json"],
            "selected_index": selected,
            "source_selection": selection,
            "selection_role": "recorded_only; no reranking",
            "request": request,
            "recorded_metadata": worker,
            "recorded_initial_metadata": worker_initial,
            "candidate_count": len(front["candidates"]),
            "candidates": [
                _candidate(candidate, i, selected, arm_times, fs)
                for i, candidate in enumerate(front["candidates"])
            ],
        }
    return source, {
        "format": FORMAT,
        "scope": "post_selection_diagnostics_on_recorded_samples_only",
        "physical_identification": "not_assessed",
        "source": {
            "directory": str(root),
            "file_sha256": source.hashes,
            "integrity_scope": "consumed_files; metadata.json is a recorded trust anchor",
            "recorded_metadata": metadata,
            "recorded_initial_metadata": initial,
            "recorded_reference_metadata": reference,
            "sampling": sampling,
            "time_samples": time_s.tolist(),
            "time_fingerprint": _fingerprint(time_s),
        },
        "arms": arms,
    }


def export_parameter_diagnostics(source_directory, output_directory):
    """Export one successful stored pilot to an exclusive directory outside it.

    No search, fit, data generation, reranking or source write is performed.
    Invalid input fails before the output directory is reserved. Consumed bytes
    are checked again immediately before writing. Checksums prove consistency,
    not authenticity of the source metadata or scientific validity.
    """
    root = Path(source_directory).resolve()
    output = Path(output_directory).resolve()
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("Output and source directories must not overlap.")
    if output.exists():
        raise FileExistsError(output)
    source, report = _collect(root)
    environment = _environment()
    environment["numerical_libraries"]["snapshot"] = "parameter_diagnostics_export"
    report["exporter"] = {
        "captured_at_utc": _utc_now(),
        "role": "diagnosis_only; separate from the recorded search environment",
        "provenance": _provenance(),
        "environment": environment,
    }
    content = _json_bytes(report)
    source.recheck()
    output.mkdir(parents=True, exist_ok=False)
    # Metadata is the last completion marker; a partial write has none.
    with (output / "diagnostics.json").open("xb") as file:
        file.write(content)
    manifest = {
        "format": FORMAT,
        "status": "success",
        "artifact_sha256": {"diagnostics.json": _sha256(content)},
    }
    with (output / "metadata.json").open("xb") as file:
        file.write(_json_bytes(manifest))
    return output
