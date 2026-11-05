"""Import anchored historical selections as data, without executing archive code."""

import hashlib
import io
import json
import math
import stat
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType

import numpy as np

from .structure import _validated_tree

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/supplemental_series.json"
MAX_ARCHIVE = 64 * 1024**2
MAX_MEMBER = 64 * 1024**2
MAX_TOTAL = 256 * 1024**2
MAX_MEMBERS = 10000


def json_bytes(value):
    """Match the historical candidate-hash serialization, without display rounding."""
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def sha256(contents):
    return hashlib.sha256(contents).hexdigest()


def read_json(contents):
    """Reject duplicate fields, nonfinite tokens and overflowing numeric literals."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field: " + key)
            result[key] = value
        return result

    def real(token):
        value = float(token)
        if not math.isfinite(value):
            raise ValueError("Nonfinite JSON number.")
        return value

    def reject(token):
        raise ValueError("Nonfinite JSON token: " + token)

    return json.loads(
        contents, object_pairs_hook=pairs, parse_float=real, parse_constant=reject
    )


def contracts():
    document = read_json(CATALOG.read_bytes())
    if document["format"] != "ringdown-sr-assessment-sources-1":
        raise ValueError("Unknown archival import contract.")
    return document["series"]


def safe_name(name):
    path = PurePosixPath(name)
    if (
        not name
        or name == "."
        or path.is_absolute()
        or ".." in path.parts
        or str(path) != name
        or "\\" in name
        or "\0" in name
    ):
        raise ValueError("Unsafe archive path.")
    name.encode("utf-8")
    return path


def bounded_read(path):
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Archive must be a bounded regular file, not a link.")
    with path.open("rb") as stream:
        contents = stream.read(MAX_ARCHIVE + 1)
    if len(contents) > MAX_ARCHIVE:
        raise ValueError("Archive exceeds compressed size limit.")
    return contents


def archive_files(contents, prefix, check=lambda: None):
    """Read a bounded TAR into immutable byte strings; never extract to disk."""
    files, seen, total = {}, set(), 0
    with tarfile.open(fileobj=io.BytesIO(contents), mode="r:gz") as archive:
        for member in archive:
            check()
            name = member.name.rstrip("/") if member.isdir() else member.name
            path = safe_name(name)
            if path.parts[0] != prefix or name in seen or len(seen) >= MAX_MEMBERS:
                raise ValueError(
                    "Wrong archive root, duplicate member or member limit."
                )
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile() or not 0 <= member.size <= MAX_MEMBER:
                raise ValueError("Unsupported or oversized archive member.")
            total += member.size
            if total > MAX_TOTAL:
                raise ValueError("Archive exceeds total uncompressed size limit.")
            relative = str(path.relative_to(prefix))
            safe_name(relative)
            raw = archive.extractfile(member).read(MAX_MEMBER + 1)
            if len(raw) != member.size:
                raise ValueError("Truncated archive member.")
            files[relative] = raw
    manifest = read_json(files["checksums.json"])
    expected = {
        name: sha256(raw) for name, raw in files.items() if name != "checksums.json"
    }
    if manifest != expected:
        raise ValueError("Incomplete or inconsistent original archive manifest.")
    for name, raw in files.items():
        if name.endswith(".json"):
            check()
            read_json(raw)
    return files


def _git_file(commit, name):
    safe_name(name)
    return subprocess.check_output(
        ["git", "show", f"{commit}:{name}"], cwd=ROOT, timeout=30
    )


def _same(first, second, reason):
    if json_bytes(first) != json_bytes(second):
        raise ValueError(reason)


def _npz(raw, keys):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if (
            sorted(i.filename for i in infos) != sorted(key + ".npy" for key in keys)
            or sum(i.file_size for i in infos) > 2 * 1024**2
        ):
            raise ValueError("Wrong or oversized numerical archive.")
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in keys}


def fingerprint(array):
    array = np.ascontiguousarray(array, dtype="<f8")
    return {
        "dtype": "<f8",
        "shape": list(array.shape),
        "sha256": sha256(array.tobytes()),
    }


def _arrays(files, report, spec):
    arrays = {
        **_npz(files["training.npz"], ("time_s", "observed")),
        **_npz(files["diagnostic.npz"], ("diagnostic_time_s", "diagnostic_truth")),
    }
    signals = len(spec["signal_order"])
    for grid, time_key, truth_key in (
        ("training", "time_s", "observed"),
        ("diagnostic", "diagnostic_time_s", "diagnostic_truth"),
    ):
        n = spec["data_shape"][grid]
        shape = (n,) if signals == 1 else (signals, n)
        for key, expected in ((time_key, (n,)), (truth_key, shape)):
            a = arrays[key]
            if (
                a.dtype != np.dtype("<f8")
                or a.shape != expected
                or not np.isfinite(a).all()
            ):
                raise ValueError("Wrong data role, shape, dtype or nonfinite input.")
        if not np.all(np.diff(arrays[time_key]) > 0):
            raise ValueError("Original time grid is not strictly ordered.")
        if not np.all(np.any(arrays[truth_key] != 0, axis=-1)):
            raise ValueError("Original reference norm is zero.")
    _same(
        {key: fingerprint(a) for key, a in arrays.items()},
        report["input_fingerprints"],
        "Changed original data fingerprints.",
    )
    if spec.get("input_manifest_path"):
        manifest = read_json(
            _git_file(spec["execution_commit"], spec["input_manifest_path"])
        )
        _same(report["input_manifest"], manifest, "Wrong frozen input manifest.")
        _same(
            report["input_fingerprints"], manifest["arrays"], "Wrong frozen data bits."
        )
        _same(
            [case["name"] for case in manifest["cases"]],
            spec["signal_order"],
            "Wrong frozen signal order.",
        )
        _same(
            report["configuration"]["truth"],
            {case["name"]: case["truth"] for case in manifest["cases"]},
            "Wrong signal reference binding.",
        )
    return arrays


def _sources(files, report, spec, check):
    sources = report["source_sha256"]
    if (
        len(sources) != spec["source_count"]
        or sha256(json_bytes(sources)) != spec["source_set_sha256"]
    ):
        raise ValueError("Wrong complete historical source set.")
    for name, digest in sources.items():
        check()
        if sha256(_git_file(spec["execution_commit"], name)) != digest:
            raise ValueError("Historical source disagrees with trusted Git: " + name)
    if (
        sha256(_git_file(spec["plan"]["commit"], spec["plan_path"]))
        != spec["plan"]["sha256"]
    ):
        raise ValueError("Historical plan binding failed.")
    for alias, name in spec["runtime_sources"].items():
        if sha256(files["runtime/" + alias]) != sources[name]:
            raise ValueError("Archived runtime source changed.")
    provenance = report["control_initial"]["provenance"]
    _same(
        provenance["git"],
        {
            "available": True,
            "changes": [],
            "commit": spec["execution_commit"],
            "dirty": False,
        },
        "Wrong original execution provenance.",
    )
    _same(
        report["control_final"]["provenance"],
        provenance,
        "Changed final original provenance.",
    )
    expected_python = {
        name.removeprefix("src/"): digest
        for name, digest in sources.items()
        if name.startswith("src/ringdown_sr/") and name.endswith(".py")
    }
    _same(
        provenance["python_source_sha256"],
        expected_python,
        "Wrong Python source provenance.",
    )
    if provenance["python_source_set_sha256"] != sha256(json_bytes(expected_python)):
        raise ValueError("Wrong Python source-set digest.")
    if set(provenance["project_file_sha256"]) != {
        ".python-version",
        "pyproject.toml",
        "uv.lock",
        "src/ringdown_sr/juliapkg.json",
        "julia/Project.toml",
        "julia/Manifest.toml",
    }:
        raise ValueError("Incomplete project-file provenance.")
    for name, digest in provenance["project_file_sha256"].items():
        if sha256(_git_file(spec["execution_commit"], name)) != digest:
            raise ValueError("Wrong project-file provenance.")
    return provenance


def _selection(files, cell, expected, arrays, spec, provenance, sources):
    for key, value in expected.items():
        _same(
            cell.get(key), value, "Original cell identity differs from its plan: " + key
        )
    if cell["status"] != "completed":
        raise ValueError("Incomplete original cell.")
    prefix = expected["directory"] + "/"
    read = lambda name: read_json(files[prefix + name])
    diagnosis = cell["diagnostics"]
    anchors = diagnosis["source_file_sha256"]
    required = {
        "result.json",
        "inputs.npz",
        "request.json",
        "profile.json",
        "manifest.json",
        "metadata.json",
        "metadata_initial.json",
        "status.json",
        "verification.json",
        "pysr_parameters.json",
        "backend_options.json",
        "checksums.json",
    }
    if not required <= anchors.keys():
        raise ValueError("Missing original cell consumption anchors.")
    for name, digest in anchors.items():
        safe_name(name)
        if sha256(files[prefix + name]) != digest:
            raise ValueError("Changed original cell artifact.")
    _same(
        read("request.json"),
        {"format": "ringdown-sr-search-arm-1", "budget": expected["budget"]},
        "Wrong original request.",
    )
    _same(
        read("profile.json"),
        {"format": spec["profile_format"], "condition": expected["condition"]},
        "Wrong original profile.",
    )
    if (
        read("status.json")["status"] != "success"
        or read("metadata.json")["phase"] != "success"
    ):
        raise ValueError("Original worker did not succeed.")
    for name, key in (
        ("metadata_initial.json", "provenance"),
        ("metadata.json", "provenance"),
        ("metadata.json", "worker_provenance"),
    ):
        _same(read(name)[key], provenance, "Wrong original worker provenance.")
    manifest = read("manifest.json")
    _same(
        manifest["sources"],
        sources,
        "Wrong worker source binding.",
    )
    if manifest["format"] != spec["format"]:
        raise ValueError("Wrong worker manifest format.")
    _same(
        manifest["inputs"],
        {
            name: sha256(files[prefix + name])
            for name in ("inputs.npz", "profile.json", "request.json")
        },
        "Incomplete worker input manifest.",
    )
    _same(
        manifest["runtime"],
        {alias: sources[name] for alias, name in spec["runtime_sources"].items()},
        "Wrong worker runtime manifest.",
    )
    for name, digest in read("checksums.json").items():
        safe_name(name)
        if sha256(files[prefix + name]) != digest:
            raise ValueError("Changed worker checksum binding.")
    parameters = read("pysr_parameters.json")
    _same(
        parameters,
        diagnosis["effective_parameters"],
        "Wrong effective parameter binding.",
    )
    expected_parameters = {
        **spec["local_profiles"][expected["condition"]],
        "niterations": expected["budget"]["niterations"],
    }
    for key, value in expected_parameters.items():
        _same(parameters.get(key), value, "Wrong original effective parameter: " + key)
    for name, digest in manifest["inputs"].items():
        safe_name(name)
        if sha256(files[prefix + name]) != digest:
            raise ValueError("Wrong worker input binding.")
    saved = _npz(files[prefix + "inputs.npz"], ("time_s", "observed"))
    signal = expected.get("signal", "anchor")
    observed = arrays["observed"]
    if len(spec["signal_order"]) > 1:
        observed = observed[spec["signal_order"].index(signal)]
    for key, value in (("time_s", arrays["time_s"]), ("observed", observed)):
        if (
            saved[key].dtype != value.dtype
            or saved[key].shape != value.shape
            or saved[key].tobytes() != value.tobytes()
        ):
            raise ValueError("Wrong selected signal input bits.")
    front = read("result.json")
    index = front["selected_index"]
    if type(index) is not int or not 0 <= index < len(front["candidates"]):
        raise ValueError("Invalid original selection index.")
    if (
        front["format"] != "ringdown-sr-search-arm-1"
        or front["selection"] != "minimum_training_loss_then_complexity"
        or front["evaluation_scope"] != "fitted_samples_only"
        or type(diagnosis["selected_index"]) is not int
        or diagnosis["selected_index"] != index
        or type(diagnosis["candidate_count"]) is not int
        or diagnosis["candidate_count"] != len(front["candidates"])
        or len(diagnosis["candidates"]) != len(front["candidates"])
    ):
        raise ValueError(
            "Inconsistent original selection policy, index or candidate count."
        )
    for i, (candidate, record) in enumerate(
        zip(front["candidates"], diagnosis["candidates"], strict=True)
    ):
        if (
            type(record["source_index"]) is not int
            or record["source_index"] != i
            or record["is_selected"] is not (i == index)
            or record["source_candidate_sha256"] != sha256(json_bytes(candidate))
        ):
            raise ValueError("Candidate identity or original selection flag changed.")
    selected, old = front["candidates"][index], diagnosis["candidates"][index]
    _validated_tree(selected["tree"])
    for key, source in (
        ("complexity", "complexity"),
        ("display_equation", "display_equation"),
        ("training_loss", "loss"),
    ):
        _same(
            old[key],
            selected[source],
            "Selected diagnosis disagrees with original candidate.",
        )
    native = read("verification.json")
    _same(
        diagnosis["native_verification"],
        native,
        "Wrong archived native verification binding.",
    )
    if native["format"] != spec["format"] or native["status"] != "verified":
        raise ValueError("Original native verification unavailable.")
    _same(
        native["backend_options"],
        read("backend_options.json"),
        "Wrong native backend binding.",
    )
    _same(
        diagnosis["effective_backend_options"],
        read("backend_options.json"),
        "Wrong effective backend binding.",
    )
    if old["training_verification"]["status"] != "passed":
        raise ValueError("Selected training verification unavailable.")
    for key in ("prediction_replay", "loss_replay"):
        if selected[key]["status"] != "passed":
            raise ValueError("Selected numerical verification unavailable.")
    _same(
        selected["prediction_replay"]["times"],
        fingerprint(arrays["time_s"]),
        "Prediction grid changed.",
    )
    if selected["prediction_replay"]["tree_sha256"] != sha256(
        json_bytes(selected["tree"])
    ):
        raise ValueError("Selected tree verification binding changed.")
    _same(front["rng"], diagnosis["rng"], "Wrong original seed binding.")
    if (
        type(front["rng"]["python_seed"]) is not int
        or front["rng"]["python_seed"] != expected["budget"]["seed"]
    ):
        raise ValueError("Wrong original Python seed.")
    return {
        "cell": expected,
        "original_selected_index": index,
        "source_candidate_sha256": old["source_candidate_sha256"],
        "source_file_sha256": anchors,
        "candidate": selected,
        "unchanged_historical": old,
        "grid_binding": {
            "time_coordinate": "physical_seconds",
            "signal": signal,
            "input_fingerprints": {
                key: fingerprint(value) for key, value in arrays.items()
            },
        },
    }


@dataclass(frozen=True)
class VerifiedSeries:
    """Keep source bytes and selection records immutable until export publication."""

    series_id: str
    archive_path: Path
    archive_bytes: bytes
    files: MappingProxyType
    records: tuple[bytes, ...]

    def unchanged(self):
        if bounded_read(self.archive_path) != self.archive_bytes:
            raise ValueError("Original archive changed after consumption.")


def read_verified_series(path, series_id, *, check=lambda: None):
    spec = contracts()[series_id]
    path = Path(path).absolute()
    raw = bounded_read(path)
    if sha256(raw) != spec["archive_sha256"]:
        raise ValueError("Wrong externally anchored original archive: " + series_id)
    files = archive_files(raw, series_id, check)
    report = read_json(files["report.json"])
    if (
        report["format"] != spec["format"]
        or report["status"] != "completed"
        or report["final_verification"] != "passed"
    ):
        raise ValueError("Original series is not complete and verified.")
    _same(report["plan"], spec["plan"], "Wrong original plan.")
    if len(report["cells"]) != len(spec["cells"]):
        raise ValueError("Incomplete original series.")
    frozen = {
        name: sha256(value)
        for name, value in files.items()
        if name not in {"report.json", "summary.md", "checksums.json"}
    }
    _same(
        report["frozen_file_sha256"],
        frozen,
        "Incomplete or changed original consumption anchors.",
    )
    provenance = _sources(files, report, spec, check)
    arrays = _arrays(files, report, spec)
    records = []
    for cell, expected in zip(report["cells"], spec["cells"], strict=True):
        check()
        records.append(
            json_bytes(
                _selection(
                    files,
                    cell,
                    expected,
                    arrays,
                    spec,
                    provenance,
                    report["source_sha256"],
                )
            )
        )
    result = VerifiedSeries(
        series_id, path, raw, MappingProxyType(files), tuple(records)
    )
    check()
    result.unchanged()
    return result
