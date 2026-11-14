"""Run one bound four-search package with the confirmed general-search profile."""

import io
import math
import signal
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_profile as profile
from . import future_assessment as future
from . import global_restarts as restarts
from . import iteration_time as costs
from .pilot import _provenance, _write_json
from .symbolic import ROOT, _inputs, select_candidate

FORMAT = "ringdown-sr-confirmed-search-package-1"
PROFILE = "r4x1000-local300x5-v1"
# Operational limits, not scientific search-budget or success criteria.
PACKAGE_SECONDS = 4 * 1800 + 600
TECHNICAL_SECONDS = 1200
VERIFY_SECONDS = 600


@dataclass(frozen=True)
class ConfirmedPackageRun:
    output_directory: Path
    status: str
    selected_member: int | None
    selected_directory: Path | None
    selected_candidate: dict | None
    costs: dict


def freeze_software(consumed):
    """Bind every imported package source and every native adapter to Git bytes."""
    software = future.freeze_software(consumed)
    for name, digest in profile.source_hashes().items():
        sources.safe_name(name)
        raw = (ROOT / name).read_bytes()
        if sources.sha256(raw) != digest or raw != consumed.git_file(
            software["software_commit"], name
        ):
            raise ValueError("Uncommitted confirmed-search source: " + name)
        consumed.add(ROOT / name, raw)
        software["source_sha256"][name] = digest
    return software


def _seeds(values):
    if (
        not isinstance(values, (tuple, list))
        or len(values) != 4
        or any(type(seed) is not int or not 0 < seed < 2**31 for seed in values)
        or len(set(values)) != 4
    ):
        raise ValueError(
            "A confirmed package needs four distinct positive 31-bit seeds."
        )
    return tuple(values)


def _arrays(time_s, observed, covariance):
    times, target, matrix = _inputs(time_s, observed, covariance)
    arrays = {
        "time_s": times,
        "observed": target,
        **({"covariance": matrix} if matrix is not None else {}),
    }
    for array in arrays.values():
        array.setflags(write=False)
    return arrays


def _input_arrays(raw):
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        if set(archive.files) not in (
            {"time_s", "observed"},
            {"time_s", "observed", "covariance"},
        ) or len(archive.files) != len(set(archive.files)):
            raise ValueError("Wrong confirmed-package input roles.")
        arrays = {key: archive[key].copy() for key in archive.files}
    if any(value.dtype != np.dtype("float64") for value in arrays.values()):
        raise ValueError("Confirmed-package inputs must retain Float64 bytes.")
    _arrays(arrays["time_s"], arrays["observed"], arrays.get("covariance"))
    return arrays


def _fingerprints(arrays):
    return {key: sources.fingerprint(value) for key, value in arrays.items()}


def _check_provenance(provenance, software):
    expected_python = {
        name.removeprefix("src/"): digest
        for name, digest in software["source_sha256"].items()
        if name.startswith("src/ringdown_sr/") and name.endswith(".py")
    }
    project_names = {
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        "src/ringdown_sr/juliapkg.json",
        "julia/Project.toml",
        "julia/Manifest.toml",
    }
    sources._same(
        provenance,
        {
            "git": {
                "available": True,
                "commit": software["software_commit"],
                "dirty": False,
                "changes": [],
            },
            "python_source_sha256": expected_python,
            "python_source_set_sha256": sources.sha256(
                sources.json_bytes(expected_python)
            ),
            "project_file_sha256": {
                name: digest
                for name, digest in software["source_sha256"].items()
                if name in project_names
            },
        },
        "Confirmed-package provenance differs from its bound software.",
    )


def _directory(output, member):
    return output / f"member-{member + 1:02d}"


def _prepared_files(output):
    files = {
        name: (output / name).read_bytes()
        for name in ("inputs.npz", "preparation.json")
    }
    for member in range(4):
        directory = _directory(output, member)
        for name, raw in profile.prepared_files(directory).items():
            sources.safe_name(name)
            files[directory.name + "/" + name] = raw
    return files


def _check_preparation(preparation, software, arrays, consumed):
    if (
        set(preparation)
        != {
            "format",
            "profile",
            "technical",
            "seeds",
            "software",
            "provenance",
            "input_fingerprints",
        }
        or preparation["format"] != FORMAT
        or preparation["profile"] != PROFILE
        or type(preparation["technical"]) is not bool
    ):
        raise ValueError("Unknown confirmed-package preparation.")
    _seeds(preparation["seeds"])
    sources._same(
        preparation["input_fingerprints"],
        _fingerprints(arrays),
        "Confirmed-package input bits differ from preparation.",
    )
    original = preparation["software"]
    _check_provenance(preparation["provenance"], original)
    sources._same(
        original["source_sha256"],
        software["source_sha256"],
        "The confirmed-package implementation differs from its execution sources.",
    )
    commit = original["software_commit"]
    if (
        type(commit) is not str
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
    ):
        raise ValueError("Invalid confirmed-package execution commit.")
    for name, digest in original["source_sha256"].items():
        if sources.sha256(consumed.git_file(commit, name)) != digest:
            raise ValueError("Confirmed-package source binding differs: " + name)


def _member_records(output, preparation, arrays, consumed, verified=None):
    records = []
    environment = None
    for member, seed in enumerate(preparation["seeds"]):
        consumed.check()
        record = (
            profile.verify_member(_directory(output, member))
            if verified is None
            else verified[member]
        )
        if (
            record["status"] not in {"completed", "fit_error", "timeout"}
            or record["profile"] != PROFILE
            or type(record["seed"]) is not int
            or record["seed"] != seed
            or type(record["technical"]) is not bool
            or record["technical"] != preparation["technical"]
            or set(record["costs"]) != set(costs.COST_FIELDS)
        ):
            raise ValueError("Confirmed-package member differs from its planned slot.")
        sources._same(
            record["input_fingerprints"],
            _fingerprints(arrays),
            "Confirmed-package worker inputs or covariance differ.",
        )
        sources._same(
            record["provenance"],
            preparation["provenance"],
            "Member provenance differs from package preparation.",
        )
        if record["status"] == "completed":
            if any(
                type(candidate["loss"]) not in (int, float)
                or not math.isfinite(candidate["loss"])
                or candidate["loss"] < 0
                or type(candidate["complexity"]) is not int
                or candidate["complexity"] < 1
                for candidate in record["candidates"]
            ):
                raise ValueError("Invalid original candidate loss or complexity.")
            selected = record["selected_index"]
            if type(selected) is not int or selected != select_candidate(
                record["candidates"]
            ):
                raise ValueError("Original worker selection changed.")
            sources._same(
                record["selected"],
                record["candidates"][selected],
                "Original selected worker candidate changed.",
            )
        elif (
            record["selected"] is not None
            or record["selected_index"] is not None
            or record["candidates"]
        ):
            raise ValueError("A failed member cannot supply a selectable candidate.")
        current = record["numerical_environment"]
        if current is not None:
            if environment is not None:
                sources._same(
                    current, environment, "Package numerical environments differ."
                )
            environment = current
        elif record["status"] == "completed":
            raise ValueError("Completed worker lacks numerical-environment evidence.")
        records.append({"member": member, **record})
        consumed.check()
    costs.cost_totals(records)
    return records, environment


def _report(output, preparation, arrays, records, environment):
    chosen = restarts.package_selection(records)
    return {
        "format": FORMAT,
        "status": "completed",
        "package_status": "success" if chosen is not None else "failed",
        "profile": PROFILE,
        "technical": preparation["technical"],
        "seeds": preparation["seeds"],
        "software": preparation["software"],
        "inputs_sha256": sources.sha256((output / "inputs.npz").read_bytes()),
        "input_files": {
            "inputs.npz": sources.sha256((output / "inputs.npz").read_bytes())
        },
        "input_fingerprints": _fingerprints(arrays),
        "preparation_sha256": sources.sha256(
            (output / "preparation.json").read_bytes()
        ),
        "selection": "minimum_native_training_loss_then_complexity_then_member",
        "loss": "covariance_quadratic_form_per_sample"
        if "covariance" in arrays
        else "mean_squared_error",
        "members": records,
        "search_calls": 4,
        "algorithm_outputs": 1,
        "selected_member": chosen,
        "selected_candidate": None if chosen is None else records[chosen]["selected"],
        "selected_candidate_path": None
        if chosen is None
        else f"member-{chosen + 1:02d}/result.json",
        "costs": costs.cost_totals(records),
        "all_costs_observed": all(
            value is not None for value in costs.cost_totals(records).values()
        ),
        "numerical_environment": environment,
        "scientific_success_assessed": False,
    }


def _summary(report):
    selected = report["selected_member"]
    return (
        "# Bestätigtes allgemeines Suchpaket\n\n"
        f"Profil: `{PROFILE}`. Vier vollständig neue Suchaufrufe.\n\n"
        f"Paketstatus: `{report['package_status']}`. "
        f"Ausgewähltes Mitglied (nullbasiert): `{selected}`.\n\n"
        "Auswahl allein nach nativem Trainingsverlust, Komplexität und "
        "fester Mitgliedsposition. Keine wissenschaftliche Erfolgsbewertung.\n"
    )


def run_confirmed_package(
    time_s, observed, *, covariance=None, output, seeds, technical=False
):
    """Prepare all members, run four fresh workers, and publish one selected output."""
    seeds = _seeds(seeds)
    if type(technical) is not bool:
        raise ValueError("Technical scope must be explicitly boolean.")
    arrays = _arrays(time_s, observed, covariance)
    output = publication.validate_output(output)
    output.mkdir(parents=True)
    state = {"status": "preparing", "members": ["planned"] * 4}
    _write_json(output / "run_state.json", state)
    seconds = TECHNICAL_SECONDS if technical else PACKAGE_SECONDS
    started = time.monotonic()
    closing, published, completed = [], [], False

    def build(consumed):
        closing.append(consumed)
        software = freeze_software(consumed)
        np.savez(output / "inputs.npz", **arrays)
        preparation = {
            "format": FORMAT,
            "profile": PROFILE,
            "technical": technical,
            "seeds": list(seeds),
            "software": software,
            "provenance": _provenance(),
            "input_fingerprints": _fingerprints(arrays),
        }
        _check_provenance(preparation["provenance"], software)
        _write_json(output / "preparation.json", preparation)
        restarts.freeze_files(
            consumed,
            output,
            {
                name: (output / name).read_bytes()
                for name in ("inputs.npz", "preparation.json")
            },
        )
        for member, seed in enumerate(seeds):
            consumed.check()
            profile.prepare_member(
                _directory(output, member),
                arrays["time_s"],
                arrays["observed"],
                covariance=arrays.get("covariance"),
                seed=seed,
                technical=technical,
            )
            restarts.freeze_files(
                consumed,
                _directory(output, member),
                profile.prepared_files(_directory(output, member)),
            )
        prepared = _prepared_files(output)
        sources._same(
            _fingerprints(arrays),
            preparation["input_fingerprints"],
            "Package input arrays changed during preparation.",
        )
        _write_json(
            output / "prepared_bindings.json",
            {name: sources.sha256(raw) for name, raw in prepared.items()},
        )
        consumed.add(
            output / "prepared_bindings.json",
            (output / "prepared_bindings.json").read_bytes(),
        )
        consumed.git_file.clear()
        verified = []
        for member in range(4):
            consumed.check()
            state["status"] = "running"
            state["members"][member] = "running"
            _write_json(output / "run_state.json", state)
            verified.append(
                profile.run_member(
                    _directory(output, member), deadline=started + seconds
                )
            )
            restarts.freeze_files(
                consumed,
                _directory(output, member),
                restarts.raw_files(_directory(output, member)),
            )
            consumed.check()
            state["members"][member] = "finished"
            _write_json(output / "run_state.json", state)
        records, environment = _member_records(
            output, preparation, arrays, consumed, verified
        )
        sources._same(
            _fingerprints(arrays),
            preparation["input_fingerprints"],
            "Package input arrays changed during execution.",
        )
        state.update(
            status="completed", members=[record["status"] for record in records]
        )
        _write_json(output / "run_state.json", state)
        raw = costs.hold_inventory(consumed, output, restarts.raw_files(output))
        report = _report(output, preparation, arrays, records, environment)
        summary = _summary(report)
        payloads = {"raw_checksums.json": sources.json_bytes(raw)}
        documents = {
            **payloads,
            publication.REPORT: sources.json_bytes(report),
            publication.SUMMARY: summary.encode(),
        }
        # Retain expected bytes before export; a post-export read could already
        # observe changed closing documents and accidentally bless that change.
        published.append(
            {
                **documents,
                publication.MANIFEST: sources.json_bytes(
                    {name: sources.sha256(raw) for name, raw in documents.items()}
                ),
            }
        )
        return report, summary, payloads

    with ExitStack() as stack:

        def interrupt(signum, frame):
            raise InterruptedError(
                "Confirmed package interrupted by signal " + str(signum)
            )

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous = signal.signal(sig, interrupt)
            stack.callback(signal.signal, sig, previous)
        try:
            report = publication.export_transaction(
                output / "completion", build, seconds=seconds
            )
            completed = True
            restarts.freeze_files(closing[0], output / "completion", published[0])
            closing[0].callbacks.append(
                lambda: publication.verify_bytes(
                    output / "completion", published[0], locked=False
                )
            )
            closing[0].check()
            if time.monotonic() - started >= seconds:
                raise TimeoutError("Whole confirmed package exceeded its deadline.")
            selected = report["selected_member"]
            result = ConfirmedPackageRun(
                output,
                report["package_status"],
                selected,
                None if selected is None else _directory(output, selected),
                report["selected_candidate"],
                report["costs"],
            )
            stack.close()
            closing[0].check()
            return result
        except BaseException as error:
            if completed:
                publication.revoke(output / "completion", error, closing[0].clock)
            state.update(status="aborted", error=f"{type(error).__name__}: {error}")
            _write_json(output / "run_state.json", state)
            raise


def verify_confirmed_package(output):
    """Recompute all four original worker records and the package without writing."""
    output = Path(output).absolute()
    if output != output.resolve() or not output.is_dir():
        raise ValueError("Use an existing package without symlink parents.")
    clock = publication.Deadline(VERIFY_SECONDS)
    consumed = publication.Consumption(clock)
    # Callers may already own a publication alarm. This verifier is read-only and
    # cooperatively checks its own deadline without replacing that active alarm.
    software = freeze_software(consumed)
    completion = output / "completion"
    expected_names = {
        publication.REPORT,
        publication.SUMMARY,
        publication.MANIFEST,
        "raw_checksums.json",
    }
    if (
        completion.is_symlink()
        or {path.name for path in completion.iterdir()} != expected_names
    ):
        raise ValueError("Confirmed package is incomplete or its release is locked.")
    exported = {name: (completion / name).read_bytes() for name in expected_names}
    manifest = sources.read_json(exported[publication.MANIFEST])
    if manifest != {
        name: sources.sha256(raw)
        for name, raw in exported.items()
        if name != publication.MANIFEST
    }:
        raise ValueError("Confirmed-package publication checksum differs.")
    restarts.freeze_files(consumed, completion, exported)

    def still_released():
        if {path.name for path in completion.iterdir()} != expected_names:
            raise ValueError("Confirmed-package release was revoked or changed.")

    consumed.callbacks.append(still_released)
    raw = restarts.raw_files(output)
    inventory = costs.hold_inventory(consumed, output, raw)
    if inventory != sources.read_json(exported["raw_checksums.json"]):
        raise ValueError("Confirmed-package raw inventory differs.")
    arrays = _input_arrays(raw["inputs.npz"])
    preparation = sources.read_json(raw["preparation.json"])
    _check_preparation(preparation, software, arrays, consumed)
    if sources.read_json(raw["prepared_bindings.json"]) != {
        name: sources.sha256(contents)
        for name, contents in _prepared_files(output).items()
    }:
        raise ValueError("Confirmed-package prepared bindings differ.")
    records, environment = _member_records(output, preparation, arrays, consumed)
    expected_state = {
        "status": "completed",
        "members": [record["status"] for record in records],
    }
    sources._same(
        sources.read_json(raw["run_state.json"]),
        expected_state,
        "Incomplete package run state.",
    )
    report = _report(output, preparation, arrays, records, environment)
    if (
        exported[publication.REPORT] != sources.json_bytes(report)
        or exported[publication.SUMMARY] != _summary(report).encode()
    ):
        raise ValueError("Confirmed-package selection, costs or report changed.")
    consumed.check()
    return report
