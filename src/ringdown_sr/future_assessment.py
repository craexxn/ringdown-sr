"""Predeclare clean diagnostic data and assess recorded schema-3 selections."""

import io
import platform
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import assessment_sources as sources
from .assessment_publication import (
    Consumption,
    Deadline,
    export_transaction,
    validate_output,
)
from .config import SymbolicPilotConfig, parse_config
from .losses import CovarianceLoss, mean_squared_error
from .noiseless_control import curve_errors
from .parameter_export import ARMS, _Source, _successful
from .signals import ringdown_signal, sample_times
from .structure import _validated_tree
from .supplemental_assessment import THRESHOLDS, git, grade_curve
from .symbolic import FORMAT, _check_prediction_replay, evaluate_tree

ROOT = sources.ROOT
POLICY = ROOT / "data/future_assessment_v1.json"
POLICY_SHA256 = "97ee7e796689c0d65ce69de3f9c567bed9dc0fce8319ab541b355e49d0bf7872"
VERSION = "ringdown-sr-future-assessment-1"
SCHEMA = "ringdown-sr-future-record-1"
INPUTS = "assessment_inputs.npz"
CONTRACT = "assessment_contract.json"
KEYS = {"training_time_s", "training_truth", "diagnostic_time_s", "diagnostic_truth"}


def freeze_software(consumed):
    """Bind the committed implementation and prospective policy before use."""
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Use a clean, committed assessment checkout.")
    commit = git("rev-parse", "HEAD")
    paths = [
        *sorted((ROOT / "src/ringdown_sr").glob("*.py")),
        POLICY,
        ROOT / "docs/supplemental_assessment.md",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        ROOT / ".python-version",
    ]
    hashes = {}
    for path in paths:
        consumed.clock.check()
        raw = path.read_bytes()
        name = path.relative_to(ROOT).as_posix()
        if raw != sources._git_file(commit, name):
            raise ValueError("Assessment source differs from its commit: " + name)
        consumed.add(path, raw)
        hashes[name] = sources.sha256(raw)

    def same_head():
        if git("rev-parse", "HEAD") != commit:
            raise ValueError("Assessment checkout changed during export.")

    consumed.callbacks.append(same_head)
    if sources.sha256(consumed.files[POLICY]) != POLICY_SHA256:
        raise ValueError("Future policy bytes differ from the versioned contract.")
    policy = sources.read_json(consumed.files[POLICY])
    expected_thresholds = [
        {
            "grade": grade,
            "relative_rms": rms,
            "relative_max": maximum,
            "rms_hex": rms.hex(),
            "max_hex": maximum.hex(),
        }
        for grade, rms, maximum in THRESHOLDS
    ]
    sources._same(policy["thresholds"], expected_thresholds, "Unsupported thresholds.")
    if (
        policy["policy_id"] != VERSION
        or policy["schema"] != SCHEMA
        or policy["reference"] != "known_clean_signal_on_both_grids"
        or policy["planned_arms"] != list(ARMS)
        or policy["stage"] != 1
        or policy["domain_interval"] is not None
    ):
        raise ValueError("Unsupported future assessment policy.")
    return {
        "software_commit": commit,
        "source_sha256": hashes,
        "policy": policy,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
    }


def planned_arrays(config):
    """Create deterministic assessment-only samples without drawing any randomness."""
    time = sample_times(**asdict(config.sampling))
    dense = (
        (np.arange(len(time) - 1)[:, None] + np.arange(1, 8)[None, :] / 8)
        / config.sampling.sample_rate_hz
    ).ravel()
    if (
        not dense.size
        or not np.all(np.diff(time) > 0)
        or not np.all(np.diff(dense) > 0)
    ):
        raise ValueError(
            "Assessment requires distinct training and diagnostic samples."
        )
    return {
        "training_time_s": time,
        "training_truth": ringdown_signal(time, **asdict(config.signal)),
        "diagnostic_time_s": dense,
        "diagnostic_truth": ringdown_signal(dense, **asdict(config.signal)),
    }


class PreparedAssessment:
    """Keep the pre-search bytes in memory until separate publication has completed."""

    def __init__(self, config):
        self.consumed = Consumption(Deadline(300))
        software = freeze_software(self.consumed)
        arrays = planned_arrays(config)
        buffer = io.BytesIO()
        np.savez(buffer, **arrays)
        raw = buffer.getvalue()
        contract = {
            "format": VERSION,
            "software": software,
            "resolved_config_sha256": sources.sha256(
                sources.json_bytes(config.to_dict())
            ),
            "inputs_sha256": sources.sha256(raw),
            "arrays": {
                key: sources.fingerprint(value) for key, value in arrays.items()
            },
        }
        self.payloads = {INPUTS: raw, CONTRACT: sources.json_bytes(contract)}

    def install(self, output):
        for name, raw in self.payloads.items():
            path = output / name
            path.write_bytes(raw)
            self.consumed.add(path, raw)
        return {name: sources.sha256(raw) for name, raw in self.payloads.items()}

    def bind_initial(self, output):
        path = output / "metadata_initial.json"
        self.consumed.add(path, path.read_bytes())

    def attach(self, consumed):
        # The export deadline starts after the search, not at preparation time.
        for path, raw in self.consumed.files.items():
            consumed.add(path, raw)
        consumed.callbacks.extend(self.consumed.callbacks)
        consumed.check()


def separate_paths(source, output):
    source, output = Path(source).absolute(), Path(output).absolute()
    if (
        source != source.resolve()
        or output != output.resolve()
        or source.is_relative_to(output)
        or output.is_relative_to(source)
    ):
        raise ValueError("Source and assessment need separate paths without symlinks.")
    if output.exists():
        raise FileExistsError(output)
    return source, output


def run_assessed_pilot(config, original, filename, source, output):
    """Opt in to pre-search capture and automatic post-run assessment publication."""
    from .symbolic_pilot import run_symbolic_pilot

    source, output = separate_paths(source, output)
    validate_output(output)
    if source.exists():
        raise FileExistsError(source)
    prepared = PreparedAssessment(config)
    try:
        outcome = run_symbolic_pilot(
            config, original, filename, source, _assessment=prepared
        )
    except BaseException as error:

        def failed(consumed, failure=error):
            raise failure

        export_transaction(output, failed)
        raise
    export_assessment(source, output, prepared=prepared)
    return outcome


class Source:
    """Freeze the complete original run, checking both levels of checksum manifests."""

    def __init__(self, root, consumed):
        self.root = root
        self.source = _Source(root)
        if "metadata.json" in self.source.manifest:
            raise ValueError(
                "The root metadata must not list an unverifiable self checksum."
            )
        self.files = {}
        names = set(self.source.manifest) | {"metadata.json"}

        def inventory():
            actual = {
                p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
            }
            if actual != names or any(p.is_symlink() for p in root.rglob("*")):
                raise ValueError("Source inventory changed or contains symlinks.")

        inventory()
        consumed.callbacks.append(inventory)
        for name in sorted(names):
            consumed.clock.check()
            raw = (
                (root / name).read_bytes()
                if name == "metadata.json"
                else self.source.read(name)
            )
            consumed.add(root / name, raw)
            self.files[name] = raw
        # Bind the metadata bytes used to load the manifest, too.
        if (
            sources.sha256(self.files["metadata.json"])
            != self.source.hashes["metadata.json"]
        ):
            raise ValueError("Source metadata changed during import.")
        self.hashes = {key: sources.sha256(raw) for key, raw in self.files.items()}

    def document(self, name):
        return sources.read_json(self.files[name])

    def manifest(self, prefix, values):
        if not isinstance(values, dict) or not values:
            raise ValueError("Missing nested manifest.")
        for name, digest in values.items():
            sources.safe_name(name)
            if self.hashes.get(prefix + name) != digest:
                raise ValueError("Nested manifest mismatch: " + prefix + name)


def verify_snapshot(source, software):
    config = parse_config(source.files["config.toml"])
    if not isinstance(config, SymbolicPilotConfig):
        raise TypeError("A schema-3 configuration is required.")
    sources._same(
        source.document("resolved_config.json"),
        config.to_dict(),
        "Configuration differs.",
    )
    contract = source.document(CONTRACT)
    if contract["format"] != VERSION:
        raise ValueError("Missing supported pre-search assessment contract.")
    sources._same(
        contract["software"]["policy"], software["policy"], "Assessment policy differs."
    )
    verify_origin(source, contract["software"])
    if contract["inputs_sha256"] != source.hashes[INPUTS]:
        raise ValueError("Assessment input hash differs.")
    if contract["resolved_config_sha256"] != sources.sha256(
        sources.json_bytes(config.to_dict())
    ):
        raise ValueError("Assessment configuration differs.")
    arrays = sources._npz(source.files[INPUTS], KEYS)
    expected = planned_arrays(config)
    for key, value in arrays.items():
        if value.dtype != np.dtype("float64") or not np.all(np.isfinite(value)):
            raise ValueError("Assessment inputs must be finite Float64 arrays.")
        if (
            sources.fingerprint(value) != sources.fingerprint(expected[key])
            or sources.fingerprint(value) != contract["arrays"][key]
        ):
            raise ValueError("Assessment grid or truth differs: " + key)
    # Recompute only to verify the recorded snapshot; never replace missing data.
    return config, arrays, contract


def verify_origin(source, frozen):
    """Bind recorded preparation sources to Git and the original run provenance."""
    commit = frozen["software_commit"]
    if (
        type(commit) is not str
        or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)
    ):
        raise ValueError("Invalid preparation commit.")
    hashes = frozen["source_sha256"]
    required = {
        "data/future_assessment_v1.json",
        "docs/supplemental_assessment.md",
        "uv.lock",
        "pyproject.toml",
        ".python-version",
    }
    if (
        not required <= hashes.keys()
        or hashes["data/future_assessment_v1.json"] != POLICY_SHA256
    ):
        raise ValueError("Incomplete preparation source binding.")
    python = {}
    for name, digest in hashes.items():
        sources.safe_name(name)
        if name.startswith("src/ringdown_sr/") and name.endswith(".py"):
            python[name.removeprefix("src/")] = digest
        elif name not in required:
            raise ValueError("Unexpected preparation source.")
        if sources.sha256(sources._git_file(commit, name)) != digest:
            raise ValueError("Preparation source differs from its Git commit.")
    if not python:
        raise ValueError("Missing preparation Python sources.")
    for prefix in ("", "reference/", *(f"symbolic/{arm}/" for arm in ARMS)):
        provenance = source.document(prefix + "metadata.json")["provenance"]
        if (
            provenance["git"]["commit"] != commit
            or provenance["git"]["dirty"] is not False
            or provenance["python_source_sha256"] != python
            or provenance["python_source_set_sha256"]
            != sources.sha256(sources.json_bytes(python))
        ):
            raise ValueError("Recorded execution and preparation sources disagree.")
        # Schema 2 records provenance in its final metadata only.
        if prefix != "reference/":
            sources._same(
                provenance,
                source.document(prefix + "metadata_initial.json")["provenance"],
                "Initial and final provenance disagree.",
            )


def endpoint(tree, times, truth):
    try:
        return curve_errors(evaluate_tree(tree, times), truth)
    except (ValueError, OverflowError, FloatingPointError) as error:
        return {
            "status": "not_available",
            "reason": str(error),
            "relative_rms": None,
            "relative_max": None,
        }


def selected_record(source, name, summary, config, shared, arrays):
    prefix = f"symbolic/{name}/"
    if (
        summary["status"] != "success"
        or summary["result_file"] != prefix + "result.json"
    ):
        raise ValueError("Incomplete or misassigned arm: " + name)
    checksums = source.document(prefix + "checksums.json")
    source.manifest(prefix, checksums)
    if (
        not {
            "metadata.json",
            "metadata_initial.json",
            "inputs.npz",
            "request.json",
            "result.json",
        }
        <= checksums.keys()
    ):
        raise ValueError("Missing required worker bindings.")
    worker = source.document(prefix + "metadata.json")
    initial = source.document(prefix + "metadata_initial.json")
    if worker["phase"] != "success" or worker["provenance"] != initial["provenance"]:
        raise ValueError("Worker status or provenance differs.")
    sources._same(
        source.document(prefix + "request.json"),
        {"format": FORMAT, "budget": asdict(config.symbolic_search)},
        "Worker request differs.",
    )
    keys = {"time_s", "observed"} | (set() if name == "ordinary" else {"covariance"})
    inputs = sources._npz(source.files[prefix + "inputs.npz"], keys)
    expected = {"time_s": shared["time_s"], "observed": shared["observed"]}
    if name != "ordinary":
        expected["covariance"] = shared[
            "covariance_true" if name == "known_covariance" else "covariance_estimated"
        ]
    for key, value in inputs.items():
        if value.dtype != np.dtype("float64") or sources.fingerprint(
            value
        ) != sources.fingerprint(expected[key]):
            raise ValueError("Worker input differs: " + key)
    front = source.document(prefix + "result.json")
    if front["format"] != FORMAT or front["evaluation_scope"] != "fitted_samples_only":
        raise ValueError("Wrong worker format.")
    index = front["selected_index"]
    if type(index) is not int or not 0 <= index < len(front["candidates"]):
        raise ValueError("Invalid original selection index.")
    chosen = front["candidates"][index]
    sources._same(
        summary["selected"],
        {
            "index": index,
            "complexity": chosen["complexity"],
            "display_equation": chosen["display_equation"],
            "training_loss": chosen["loss"],
            "selection": "minimum_training_loss_then_complexity",
            "parameter_interpretation": "not_attempted",
        },
        "Original selection and worker disagree.",
    )
    _validated_tree(chosen["tree"])
    replay = _check_prediction_replay(
        evaluate_tree(chosen["tree"], arrays["training_time_s"]), chosen["prediction"]
    )
    if not np.array_equal(
        shared["observed"] - np.asarray(chosen["prediction"]), chosen["residual"]
    ):
        raise ValueError("Selected residual differs.")
    residual = np.asarray(chosen["residual"], dtype=np.float64)
    loss = (
        mean_squared_error(residual)
        if name == "ordinary"
        else CovarianceLoss(inputs["covariance"]).mean_squared(residual)
    )
    if type(chosen["loss"]) not in (int, float):
        raise ValueError("Invalid selected loss.")
    np.testing.assert_allclose(chosen["loss"], loss, rtol=1e-10, atol=0)
    errors = {
        grid: endpoint(
            chosen["tree"], arrays[grid + "_time_s"], arrays[grid + "_truth"]
        )
        for grid in ("training", "diagnostic")
    }
    return {
        "schema": SCHEMA,
        "assessment_version": VERSION,
        "source_identity": {
            "arm": name,
            "original_selected_index": index,
            "source_result_sha256": source.hashes[prefix + "result.json"],
            "source_candidate_sha256": sources.sha256(sources.json_bytes(chosen)),
            "original_seed": config.symbolic_search.seed,
        },
        "original_candidate": chosen,
        "unchanged_original": summary,
        "training_prediction_replay": replay,
        "curve_errors": errors,
        "supplemental": {
            "curve": grade_curve(errors, source_verified=True),
            **{
                key: {"status": "not_assessed"}
                for key in (
                    "algebraic_identity",
                    "original_family",
                    "continuous_extension",
                    "remainder",
                    "new_parameter_match",
                )
            },
            "domain": {"status": "not_assessed", "interval": None, "exclusions": None},
            "coefficients_exact": None,
            "coefficient_sign_proofs": None,
            "proof_trace": [],
        },
    }


def build_assessment(root, consumed, prepared=None):
    software = freeze_software(consumed)
    if prepared is not None:
        prepared.attach(consumed)
    source = Source(root, consumed)
    meta, initial, result = (
        source.document(n)
        for n in ("metadata.json", "metadata_initial.json", "result.json")
    )
    _successful(meta, 3)
    _successful(result, 3)
    if (
        result["stage"] != "complete"
        or result["evaluation_scope"] != "fitted_samples_only"
        or set(result["symbolic_arms"]) != set(ARMS)
        or result["shared_inputs_file"] != "reference/comparison_inputs.npz"
        or result["reference"]
        != {
            "status": "success",
            "schema_version": 2,
            "result_file": "reference/result.json",
        }
        or meta["provenance"] != initial["provenance"]
    ):
        raise ValueError("Incomplete source or changed provenance.")
    binding = {name: source.hashes[name] for name in (INPUTS, CONTRACT)}
    sources._same(
        initial["supplemental_assessment"], binding, "Initial snapshot binding differs."
    )
    sources._same(
        meta["supplemental_assessment"], binding, "Final snapshot binding differs."
    )
    config, arrays, contract = verify_snapshot(source, software)
    if (
        meta["configuration"] != initial["configuration"]
        or meta["configuration"]["original_sha256"] != source.hashes["config.toml"]
        or meta["configuration"]["resolved_sha256"]
        != source.hashes["resolved_config.json"]
    ):
        raise ValueError("Configuration provenance differs.")
    ref = source.document("reference/metadata.json")
    _successful(ref, 2)
    _successful(source.document("reference/result.json"), 2)
    source.manifest("reference/", ref["artifact_sha256"])
    if (
        ref["artifact_sha256"].get("comparison_inputs.npz")
        != source.hashes["reference/comparison_inputs.npz"]
    ):
        raise ValueError("Missing reference input binding.")
    shared = sources._npz(
        source.files["reference/comparison_inputs.npz"],
        {
            "time_s",
            "signal",
            "noise",
            "observed",
            "covariance_true",
            "covariance_estimated",
        },
    )
    n = len(arrays["training_time_s"])
    for key, value in shared.items():
        shape = (n, n) if key.startswith("covariance_") else (n,)
        if (
            value.dtype != np.dtype("float64")
            or value.shape != shape
            or not np.all(np.isfinite(value))
        ):
            raise ValueError("Invalid shared numerical data: " + key)
    if not np.array_equal(shared["observed"], shared["signal"] + shared["noise"]):
        raise ValueError("Observed samples differ from signal plus noise.")
    for key, expected in (
        ("time_s", arrays["training_time_s"]),
        ("signal", arrays["training_truth"]),
    ):
        if shared[key].dtype != np.dtype("float64") or sources.fingerprint(
            shared[key]
        ) != sources.fingerprint(expected):
            raise ValueError("Shared training data and frozen reference disagree.")
    records = [
        selected_record(
            source, name, result["symbolic_arms"][name], config, shared, arrays
        )
        for name in ARMS
    ]
    report = {
        "format": VERSION,
        "software": software,
        "pre_search_contract": contract,
        "condition": config.to_dict(),
        "source": {
            "directory": str(root),
            "file_sha256": source.hashes,
            "integrity_scope": "complete recorded run; metadata.json is a recorded trust anchor, not an external signature",
        },
        "release": "verified_original_selections",
        "records_file": "assessment_records.json",
        "groups": [
            {
                "arm": record["source_identity"]["arm"],
                "planned_denominator": 1,
                "curve_grade_counts": {
                    key: int(
                        (record["supplemental"]["curve"]["grade"] or "not_assessable")
                        == key
                    )
                    for key in ("A", "B", "C", "D", "not_assessable")
                },
            }
            for record in records
        ],
    }
    summary = "# Zusatzbewertung eines Schema-3-Laufs\n\nOriginalauswahlen; sauberes Signal auf beiden Rastern.\nKeine gemeinsame Erfolgsquote; spätere Bewertungsstufen: not_assessed.\n\n"
    summary += (
        "\n".join(
            f"- {r['source_identity']['arm']}: {r['supplemental']['curve']['grade'] or 'not_assessable'} (Nenner 1)"
            for r in records
        )
        + "\n"
    )
    return (
        report,
        summary,
        {
            "assessment_records.json": sources.json_bytes(records),
            "original-result.json": source.files["result.json"],
        },
    )


def export_assessment(source, output, *, seconds=300, prepared=None):
    """Assess a saved run with its pre-search snapshot; never start any worker."""
    source, output = separate_paths(source, output)
    return export_transaction(
        output,
        lambda consumed: build_assessment(source, consumed, prepared),
        seconds=seconds,
    )
