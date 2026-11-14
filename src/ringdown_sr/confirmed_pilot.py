"""Route the fixed confirmed package through all three general weighting arms."""

import io
import signal
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from .background import (
    background_random_record,
    draw_noise_window,
    generate_background,
    pilot_generators,
)
from .config import CONFIRMED_PROFILE, ConfirmedPilotConfig, parse_config
from .confirmed_search import run_confirmed_package, verify_confirmed_package
from .covariance_estimation import estimate_covariance
from .covariance_pilot import run_covariance_pilot
from .losses import CovarianceLoss
from .noise import ar1_covariance
from .pilot import PilotRun, _environment, _provenance, _utc_now, _write_json
from .signals import ringdown_signal, sample_times
from .symbolic_pilot import ARM_LABELS, _diagnose, _reference_toml

FORMAT = "ringdown-sr-confirmed-pilot-1"
RUN_SECONDS = 25200
TECHNICAL_SECONDS = 4800
VERIFY_SECONDS = 2400
INPUT_ROLES = {
    "time_s",
    "signal",
    "noise",
    "observed",
    "covariance_true",
    "covariance_estimated",
}
SUMMARY = "# Bestätigtes Profil im allgemeinen Laufweg\n\nDrei getrennte Gewichtungsarme; keine Auswahl zwischen ihren Zielfunktionen.\n"


def _publication_bytes(report):
    documents = {
        publication.REPORT: sources.json_bytes(report),
        publication.SUMMARY: SUMMARY.encode(),
    }
    return {
        **documents,
        publication.MANIFEST: sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in documents.items()}
        ),
    }


def _read(path, consumed):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a regular pilot artifact.")
    raw = path.read_bytes()
    consumed.add(path, raw)
    return raw


def _json(path, consumed):
    return sources.read_json(_read(path, consumed))


def _snapshot_tree(root, consumed):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Expected an existing regular artifact directory.")

    def inventory():
        paths = sorted(root.rglob("*"))
        if any(
            path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths
        ):
            raise ValueError("Only regular artifact files and directories are allowed.")
        return tuple(
            path.relative_to(root).as_posix() for path in paths if path.is_file()
        )

    names = inventory()
    for name in names:
        _read(root / name, consumed)

    def unchanged():
        if inventory() != names:
            raise ValueError("Artifact inventory changed during verification.")

    consumed.callbacks.append(unchanged)


def _source_binding():
    binding = _provenance()
    if not binding["git"]["available"] or binding["git"]["dirty"]:
        raise ValueError(
            "Confirmed pilot requires an identified clean source checkout."
        )
    return binding


def _root_inventory(root):
    required = {
        "config.toml",
        "reference_config.toml",
        "resolved_config.json",
        "preparation.json",
        "run_state.json",
        "reference",
        "symbolic",
        "completion",
    }
    if {path.name for path in root.iterdir()} != required:
        raise ValueError("Unexpected pilot root inventory.")
    if any((root / name).is_symlink() for name in required):
        raise ValueError("Pilot root artifact symlinks are forbidden.")
    if {path.name for path in (root / "symbolic").iterdir()} != set(ARM_LABELS):
        raise ValueError("Pilot weighting-arm inventory changed.")


def _completed_state(root, status, consumed):
    expected = {"format": FORMAT, "status": "completed", "pilot_status": status}
    sources._same(
        _json(root / "run_state.json", consumed),
        expected,
        "Pilot run state is incomplete or inconsistent.",
    )


def _same_array(actual, expected, name):
    if (
        actual.dtype != np.dtype("float64")
        or actual.shape != expected.shape
        or actual.tobytes(order="C") != expected.tobytes(order="C")
    ):
        raise ValueError("Pilot input differs from its configured source: " + name)


def _reference_inputs(root, config, consumed):
    """Replay generation and covariance estimation, never reference fits or searches."""
    reference = root / "reference"
    _snapshot_tree(reference, consumed)
    metadata = _json(reference / "metadata.json", consumed)
    result = _json(reference / "result.json", consumed)
    if metadata["status"] != "success" or result["status"] != "success":
        raise ValueError("The shared reference preparation did not complete.")
    expected_config = _reference_toml(config.reference_config())
    if _read(reference / "config.toml", consumed) != expected_config:
        raise ValueError("Reference configuration differs from schema 4.")
    checksums = metadata["artifact_sha256"]
    actual_names = {
        path.relative_to(reference).as_posix()
        for path in reference.rglob("*")
        if path.is_file() and path != reference / "metadata.json"
    }
    if set(checksums) != actual_names:
        raise ValueError("Incomplete reference artifact manifest.")
    for name, digest in checksums.items():
        path = reference / str(sources.safe_name(name))
        if sources.sha256(_read(path, consumed)) != digest:
            raise ValueError("Reference artifact checksum mismatch.")
    with np.load(
        io.BytesIO(_read(reference / "comparison_inputs.npz", consumed)),
        allow_pickle=False,
    ) as stored:
        if set(stored.files) != INPUT_ROLES or len(stored.files) != len(INPUT_ROLES):
            raise ValueError("Unexpected shared reference input roles.")
        data = {name: stored[name].copy() for name in stored.files}
    generators = pilot_generators(config.noise.seed, config.background.seed)
    time_s = sample_times(**asdict(config.sampling))
    signal = ringdown_signal(time_s, **asdict(config.signal))
    noise = draw_noise_window(config.noise, len(time_s), generators["signal"])
    with np.errstate(over="raise", invalid="raise"):
        observed = signal + noise
    truth = (
        ar1_covariance(
            len(time_s),
            standard_deviation=config.noise.standard_deviation,
            correlation=config.noise.correlation,
        )
        if config.noise.kind == "gaussian_ar1"
        else config.noise.standard_deviation**2 * np.eye(len(time_s))
    )
    background = {}
    generate_background(
        config.noise,
        config.sampling,
        config.background,
        windows=background,
        random=background_random_record(
            config.noise, config.sampling, config.background
        ),
        generators=generators,
    )
    estimate = estimate_covariance(
        background["train"],
        background["validation"],
        **asdict(config.covariance_estimation),
    )
    expected = {
        "time_s": time_s,
        "signal": signal,
        "noise": noise,
        "observed": observed,
        "covariance_true": truth,
        "covariance_estimated": estimate.covariance,
    }
    sources._same(
        result["covariance_estimation"]["alpha_selected"],
        estimate.alpha_selected,
        "Reference covariance selection changed.",
    )
    for name, array in data.items():
        _same_array(array, expected[name], name)
        array.setflags(write=False)
    CovarianceLoss(data["covariance_true"])
    CovarianceLoss(data["covariance_estimated"])
    return data, result, metadata


def _package_record(directory, config, data, covariance, technical, consumed):
    consumed.check()
    _snapshot_tree(directory, consumed)
    report = verify_confirmed_package(directory)
    if (
        report["status"] != "completed"
        or report["profile"] != CONFIRMED_PROFILE
        or report["seeds"] != list(config.confirmed_search.seeds)
        or type(report["technical"]) is not bool
        or report["technical"] is not technical
        or len(report["members"]) != 4
        or report["package_status"] not in ("success", "failed")
    ):
        raise ValueError("Confirmed package does not match the pilot contract.")
    raw = _read(directory / "inputs.npz", consumed)
    if sources.sha256(raw) != report["inputs_sha256"]:
        raise ValueError("Package input hash differs from its verified report.")
    with np.load(io.BytesIO(raw), allow_pickle=False) as inputs:
        expected = {"time_s": data["time_s"], "observed": data["observed"]}
        if covariance is not None:
            expected["covariance"] = covariance
        if set(inputs.files) != set(expected) or len(inputs.files) != len(expected):
            raise ValueError("Unexpected weighting-arm input roles.")
        for name, value in expected.items():
            _same_array(inputs[name], value, name)
    selected = report["selected_candidate"]
    record = {
        "status": report["package_status"],
        "package_report": directory.name + "/completion/assessment_report.json",
        "selected": None,
        "metrics": None,
        "costs": report["costs"],
        "planned_members": 4,
        "numerical_environment": report["numerical_environment"],
        "error": None,
    }
    if report["package_status"] == "success":
        if selected is None or type(report["selected_member"]) is not int:
            raise ValueError("Successful package lacks its original selection.")
        record["selected"] = {
            "member": report["selected_member"],
            "complexity": selected["complexity"],
            "display_equation": selected["display_equation"],
            "training_loss": selected["loss"],
            "selection": "minimum_native_training_loss_then_complexity_then_member",
            "parameter_interpretation": "not_assessed",
        }
        record["metrics"] = _diagnose(
            selected,
            data["observed"],
            data["signal"],
            data["covariance_true"],
            covariance,
        )
    elif selected is not None or report["selected_member"] is not None:
        raise ValueError("Failed package unexpectedly declares a selection.")
    else:
        record["error"] = {
            "type": "NoFiniteMember",
            "message": "No admissible package member.",
        }
    consumed.check()
    return record


def _assemble(root, consumed, *, complete_state=True):
    _root_inventory(root)
    consumed.callbacks.append(lambda: _root_inventory(root))
    preparation = _json(root / "preparation.json", consumed)
    original = _read(root / "config.toml", consumed)
    config = parse_config(original)
    if not isinstance(config, ConfirmedPilotConfig):
        raise TypeError("Confirmed pilot verification requires schema 4.")
    sources._same(
        _json(root / "resolved_config.json", consumed),
        config.to_dict(),
        "Resolved pilot configuration changed.",
    )
    if _read(root / "reference_config.toml", consumed) != _reference_toml(
        config.reference_config()
    ):
        raise ValueError("Shared reference configuration changed.")
    binding = _source_binding()
    if (
        preparation["format"] != FORMAT
        or preparation["configuration_sha256"] != sources.sha256(original)
        or type(preparation["technical"]) is not bool
    ):
        raise ValueError("Pilot preparation or source binding changed.")
    sources._same(preparation["provenance"], binding, "Pilot source binding changed.")

    def unchanged_sources():
        if _source_binding() != binding:
            raise ValueError("Pilot sources changed during publication.")

    consumed.callbacks.append(unchanged_sources)
    data, reference_result, reference_metadata = _reference_inputs(
        root, config, consumed
    )
    sources._same(
        reference_metadata["provenance"],
        binding,
        "Reference preparation used different actual sources.",
    )
    arms = {}
    environment = None
    for name in ARM_LABELS:
        covariance = (
            None
            if name == "ordinary"
            else data[
                "covariance_true"
                if name == "known_covariance"
                else "covariance_estimated"
            ]
        )
        arms[name] = _package_record(
            root / "symbolic" / name,
            config,
            data,
            covariance,
            preparation["technical"],
            consumed,
        )
        arms[name]["package_report"] = "symbolic/" + arms[name]["package_report"]
        current = arms[name]["numerical_environment"]
        if current is not None:
            if environment is not None:
                sources._same(
                    current, environment, "Weighting-arm numerical environments differ."
                )
            environment = current
    failed = [name for name, arm in arms.items() if arm["status"] != "success"]
    report = {
        "format": FORMAT,
        "schema_version": 4,
        "pilot_status": "comparison_failed" if failed else "success",
        "profile": CONFIRMED_PROFILE,
        "technical": preparation["technical"],
        "seeds": list(config.confirmed_search.seeds),
        "planned_search_calls": 12,
        "algorithm_outputs": 3,
        "search_calls_during_verification": 0,
        "shared_inputs_file": "reference/comparison_inputs.npz",
        "shared_inputs_sha256": sources.sha256(
            _read(root / "reference/comparison_inputs.npz", consumed)
        ),
        "configuration_sha256": sources.sha256(original),
        "preparation_sha256": sources.sha256(
            _read(root / "preparation.json", consumed)
        ),
        "covariance_estimation": reference_result["covariance_estimation"],
        "symbolic_arms": arms,
        "evaluation_scope": "fitted_samples_only",
        "selection_across_weighting_arms": "forbidden",
        "physical_parameter_match": "not_assessed",
        "error": None
        if not failed
        else {
            "type": "ComparisonIncomplete",
            "message": "Failed SR packages: " + ", ".join(failed),
        },
    }
    if complete_state:
        _completed_state(root, report["pilot_status"], consumed)
    return report


def _run_confirmed_pilot(
    config,
    original,
    source_filename,
    output_directory,
    owned,
    closing_checks,
    *,
    technical=False,
):
    """Run three fresh packages; never convert integrity errors into fit failures."""
    if not isinstance(config, ConfirmedPilotConfig) or parse_config(original) != config:
        raise ValueError("Schema-4 configuration and original bytes disagree.")
    if type(technical) is not bool:
        raise TypeError("technical must be a boolean.")
    pilot_generators(config.noise.seed, config.background.seed)
    binding = _source_binding()
    clock = publication.Deadline(TECHNICAL_SECONDS if technical else RUN_SECONDS)
    initial = publication.Consumption(clock)
    closing = []
    output = publication.validate_output(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    owned.append(output)
    _write_json(output / "run_state.json", {"format": FORMAT, "status": "preparing"})
    reference_bytes = _reference_toml(config.reference_config())
    (output / "config.toml").write_bytes(original)
    (output / "reference_config.toml").write_bytes(reference_bytes)
    _write_json(output / "resolved_config.json", config.to_dict())
    _write_json(
        output / "preparation.json",
        {
            "format": FORMAT,
            "configuration_sha256": sources.sha256(original),
            "source_filename": source_filename,
            "provenance": binding,
            "environment": _environment(),
            "technical": technical,
            "started_at_utc": _utc_now(),
        },
    )
    for name in (
        "config.toml",
        "reference_config.toml",
        "resolved_config.json",
        "preparation.json",
    ):
        _read(output / name, initial)

    def sources_unchanged():
        if _source_binding() != binding:
            raise ValueError("Sources changed after pilot preparation.")

    initial.callbacks.append(sources_unchanged)
    try:
        reference = run_covariance_pilot(
            config.reference_config(),
            reference_bytes,
            "reference_config.toml",
            output / "reference",
            _capture_inputs=True,
        )
        if reference.status != "success":
            raise RuntimeError("Shared reference preparation failed.")
        data, _, _ = _reference_inputs(output, config, initial)
        for name in ARM_LABELS:
            initial.check()
            _write_json(
                output / "run_state.json",
                {"format": FORMAT, "status": "running", "arm": name},
            )
            covariance = (
                None
                if name == "ordinary"
                else data[
                    "covariance_true"
                    if name == "known_covariance"
                    else "covariance_estimated"
                ]
            )
            run_confirmed_package(
                data["time_s"],
                data["observed"],
                covariance=covariance,
                output=output / "symbolic" / name,
                seeds=config.confirmed_search.seeds,
                technical=technical,
            )
            _snapshot_tree(output / "symbolic" / name, initial)
            initial.check()

        def build(consumed):
            closing.append(consumed)
            consumed.callbacks.append(initial.check)
            report = _assemble(output, consumed, complete_state=False)
            _write_json(
                output / "run_state.json",
                {
                    "format": FORMAT,
                    "status": "completed",
                    "pilot_status": report["pilot_status"],
                },
            )
            _completed_state(output, report["pilot_status"], consumed)
            return report, SUMMARY, {}

        report = publication.export_transaction(
            output / "completion", build, seconds=VERIFY_SECONDS
        )
        expected = _publication_bytes(report)

        def final_check():
            initial.check()
            closing[-1].check()
            publication.verify_bytes(output / "completion", expected, locked=False)
            _root_inventory(output)
            initial.check()
            closing[-1].check()

        closing_checks.append(final_check)
        final_check()
        return PilotRun(output, report["pilot_status"])
    except BaseException as error:
        if (output / "completion").is_dir() and not (
            output / "completion" / publication.LOCK
        ).exists():
            publication.revoke(output / "completion", error, clock)
        _write_json(
            output / "run_state.json",
            {
                "format": FORMAT,
                "status": "aborted",
                "error": f"{type(error).__name__}: {error}",
            },
        )
        raise


def run_confirmed_pilot(
    config, original, source_filename, output_directory, *, technical=False
):
    """Keep interruption revocation active through publication and context teardown."""
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    owned = []
    closing_checks = []

    def interrupted(signum, frame):
        raise InterruptedError("Confirmed pilot interrupted by signal " + str(signum))

    try:
        with ExitStack() as stack:
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous = signal.signal(sig, interrupted)
                stack.callback(signal.signal, sig, previous)
            outcome = _run_confirmed_pilot(
                config,
                original,
                source_filename,
                output_directory,
                owned,
                closing_checks,
                technical=technical,
            )
        # Restoring caller signal handlers is part of the owned transaction.
        closing_checks[0]()
        return outcome
    except BaseException as error:
        if owned:
            output = owned[0]
            completion = output / "completion"
            if completion.is_dir() and not (completion / publication.LOCK).exists():
                publication.revoke(
                    completion, error, publication.Deadline(VERIFY_SECONDS)
                )
            _write_json(
                output / "run_state.json",
                {
                    "format": FORMAT,
                    "status": "aborted",
                    "error": f"{type(error).__name__}: {error}",
                },
            )
        raise


def verify_confirmed_pilot(output_directory):
    """Read-verify all package selections and the original shared input preparation."""
    output = Path(output_directory).absolute()
    if output != output.resolve():
        raise ValueError("Pilot verification rejects symlink paths.")
    clock = publication.Deadline(VERIFY_SECONDS)
    consumed = publication.Consumption(clock)
    completion = output / "completion"
    if (completion / publication.LOCK).exists():
        raise ValueError("Pilot completion is locked.")
    expected = {
        name: _read(completion / name, consumed)
        for name in (publication.REPORT, publication.SUMMARY, publication.MANIFEST)
    }
    manifest = sources.read_json(expected[publication.MANIFEST])
    if manifest != {
        name: sources.sha256(raw)
        for name, raw in expected.items()
        if name != publication.MANIFEST
    }:
        raise ValueError("Pilot completion checksum mismatch.")
    publication.verify_bytes(completion, expected, locked=False)
    report = _assemble(output, consumed)
    if (
        sources.json_bytes({**report, "status": "completed"})
        != expected[publication.REPORT]
    ):
        raise ValueError(
            "Recomputed pilot report differs from its original publication."
        )
    consumed.check()
    publication.verify_bytes(completion, expected, locked=False)
    consumed.check()
    return {**report, "status": "completed"}
