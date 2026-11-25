"""Freeze N103 main-study inputs with independent roles and explicit evaluation axes."""

import copy
import hashlib
import io
import math
import os
import signal
import stat
import time
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.signal import lfilter

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search
from . import noise_followup_covariance as covariance
from . import noise_pilot_inputs as pilot
from .background import draw_noise_window, pilot_generators
from .config import AR1NoiseConfig, NoiseConfig
from .covariance_estimation import CovarianceEstimationError
from .noise import ar1_covariance
from .pilot import _utc_now
from .signals import ringdown_signal, sample_times

ROOT = sources.ROOT
FORMAT = "ringdown-sr-main-study-inputs-2"
CALL_FORMAT = "ringdown-sr-main-study-input-call-1"
PLAN_PATH = "docs/main_study_plan.md"
WIDTH_PLAN_PATH = "docs/main_study_reference_width_v2.md"
WIDTH_PLAN_SHA256 = "c1173c98be3f0d92892d07b198482b28d08c7293b8ed5dded3365079aa772dde"
SEEDS_PATH = "data/main_study_seeds.json"
PLAN_COMMIT = "126b39e311eceeb12102cf09e6da57deb735025b"
PLAN_SHA256 = "772b26883e5bb871ad64af9d60b2e07b69c786af34790e9c68cfeb6930b5d706"
SEEDS_SHA256 = "b03b2ec41a868e6875169c5375639c2fbee5c52838063ae479a3dd990a870381"
LOCK = "INPUTS_LOCKED"
PREPARE_SECONDS = 14400
ARMS = ("ordinary", "known_covariance", "estimated_64s", "estimated_4096s")
ESTIMATED_ARMS = ARMS[2:]
DURATIONS = (64, 4096)
SAMPLE_RATE = 4096
N_SAMPLES = 103
RHO = 0.65
SIGNALS = {
    "signal_200_4ms": {
        "amplitude": 1.0,
        "frequency_hz": 200.0,
        "decay_time_s": 0.004,
        "phase_rad": 0.0,
    },
    "signal_250_6ms": {
        "amplitude": 1.0,
        "frequency_hz": 250.0,
        "decay_time_s": 0.006,
        "phase_rad": 0.0,
    },
}
SIGMA = 0.05
ALPHAS = pilot.ALPHAS
COVARIANCE_CHUNK_SAMPLES = 65508
MAIN_END_SECONDS = 0.025
EVALUATION_POINTS = 1024
AXIS_TRUTH_ROLES = {
    "time_s": "signal",
    "main_time_s": "main_truth",
    "support_time_s": "support_truth",
    "endpoint_time_s": "endpoint_truth",
}
COMMON_KEYS = set(AXIS_TRUTH_ROLES) | {
    signal_id + "__" + role
    for signal_id in SIGNALS
    for role in AXIS_TRUTH_ROLES.values()
}
CASE_KEYS = {
    "noise",
    "observed",
    "covariance_true",
    "background_validation",
    "background_check",
    "covariance_raw_64s",
    "covariance_estimated_64s",
    "covariance_raw_4096s",
    "covariance_estimated_4096s",
}
_freeze = pilot._freeze


@dataclass(frozen=True)
class PreparedInputs:
    """Keep only small common arrays, manifests and case specifications in memory."""

    root: Path
    manifest: dict
    common: dict
    cases: dict
    call: dict | None = None


@dataclass(frozen=True)
class PreparedCase:
    """Expose one case's small arrays and a closed, separately guarded raw file."""

    spec: dict
    arrays: dict
    record: dict
    train_path: Path


def _purpose(purpose, technical):
    if technical is not None:
        if type(technical) is not bool or purpose != "scientific":
            raise ValueError("Use exactly one explicit purpose or technical alias.")
        purpose = "technical" if technical else "scientific"
    if purpose not in {"scientific", "technical"}:
        raise ValueError("Unknown input purpose.")
    return purpose


def _seed_table():
    path = ROOT / SEEDS_PATH
    if path.is_symlink():
        raise ValueError("Seed tables cannot be symbolic links.")
    raw = path.read_bytes()
    if sources.sha256(raw) != SEEDS_SHA256:
        raise ValueError("Seed table differs from the frozen protocol.")
    return sources.read_json(raw)


def case_specs(*, purpose="scientific", technical=None):
    """Read the single frozen seed table, with a separate technical inventory."""
    purpose = _purpose(purpose, technical)
    table = _seed_table()
    rows = table[purpose + "_cases"]
    return tuple(
        {
            **copy.deepcopy(row),
            "purpose": purpose,
            "technical": purpose == "technical",
            "niterations": 10 if purpose == "technical" else 1000,
            "sampling": {"n_samples": N_SAMPLES, "sample_rate_hz": float(SAMPLE_RATE)},
            "signal": dict(SIGNALS[row["signal_id"]]),
            "standard_deviation": SIGMA,
            "correlation": RHO if row["noise_model"] == "ar1" else 0.0,
            "background_durations_seconds": list(DURATIONS),
            "background_validation_windows": 128,
            "background_check_windows": 256,
            "chunk_samples": covariance.CHUNK_SAMPLES,
            "covariance_chunk_samples": COVARIANCE_CHUNK_SAMPLES,
            "covariance_estimation": {
                "mean_mode": "known_zero",
                "alpha_candidates": list(ALPHAS),
                "kappa_max": 1e8,
            },
        }
        for row in rows
    )


def initial_rng_states():
    """Check actual PCG64 states without generating observations or background."""
    table = _seed_table()
    seen = set()
    for role in (
        "table_generator",
        "evaluation_grid",
        "support_grid",
        "technical_noise",
        "technical_background",
        "technical_search",
    ):
        state = sources.json_bytes(np.random.PCG64(table["reserved"][role]).state)
        if state in seen:
            raise ValueError("Reserved random-stream initial states collide.")
        seen.add(state)
    for purpose in ("scientific", "technical"):
        for spec in case_specs(purpose=purpose):
            for generator in pilot_generators(
                spec["noise_seed"], spec["background_seed"]
            ).values():
                state = sources.json_bytes(generator.bit_generator.state)
                if state in seen:
                    raise ValueError("Main-study random-stream initial states collide.")
                seen.add(state)
    return {"checked_states": len(seen), "collisions": 0}


def _evaluation_grid(seed, end, training):
    """Draw one open point per equal stratum without training-point overlap."""
    rng = np.random.Generator(np.random.PCG64(seed))
    before = copy.deepcopy(rng.bit_generator.state)
    values = []
    for index in range(EVALUATION_POINTS):
        for _ in range(100):
            fraction = rng.random()
            value = (index + fraction) / EVALUATION_POINTS * end
            lower = index / EVALUATION_POINTS * end
            upper = (index + 1) / EVALUATION_POINTS * end
            if (
                0 < fraction < 1
                and lower < value < upper
                and not np.any(training == value)
            ):
                values.append(value)
                break
        else:
            raise ValueError("Could not generate the fixed open evaluation axis.")
    return _freeze(values), {
        "seed": seed,
        "state_before": before,
        "state_after": copy.deepcopy(rng.bit_generator.state),
        "points": EVALUATION_POINTS,
        "end_seconds_hex": float(end).hex(),
        "weights": "equal",
        "maximum_draws_per_stratum": 100,
    }


def _truth_reference(time_s, actual, parameters):
    """Check exact Binary64 parameters with mathematical pi at 100 decimals."""
    with mp.workdps(100):
        amplitude, frequency, decay, phase = (
            mp.mpf(parameters[name])
            for name in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
        )
        maximum = mp.mpf(0)
        for time_value, signal_value in zip(time_s, actual, strict=True):
            t = mp.mpf(float(time_value))
            expected = (
                amplitude
                * mp.exp(-t / decay)
                * mp.cos(2 * mp.pi * frequency * t + phase)
            )
            maximum = max(
                maximum, abs(mp.mpf(float(signal_value)) - expected) / abs(amplitude)
            )
        if maximum >= mp.mpf("1e-13"):
            raise ValueError(
                "Main-study truth exceeds its independent reference bound."
            )
        return float(maximum)


def derive_common_inputs():
    """Bind shared evaluation axes and separate truth arrays for both signals."""
    reserved = _seed_table()["reserved"]
    training = sample_times(N_SAMPLES, float(SAMPLE_RATE))
    main, main_record = _evaluation_grid(
        reserved["evaluation_grid"], MAIN_END_SECONDS, training
    )
    support, support_record = _evaluation_grid(
        reserved["support_grid"], training[-1], training
    )
    arrays = {
        "time_s": training,
        "main_time_s": main,
        "support_time_s": support,
        "endpoint_time_s": np.array([0.0, MAIN_END_SECONDS], dtype=np.float64),
    }
    truth_errors = {}
    for signal_id, parameters in SIGNALS.items():
        for time_key, truth_key in AXIS_TRUTH_ROLES.items():
            name = signal_id + "__" + truth_key
            arrays[name] = ringdown_signal(arrays[time_key], **parameters)
            truth_errors[name] = _truth_reference(
                arrays[time_key], arrays[name], parameters
            )
    arrays = {key: _freeze(value) for key, value in arrays.items()}
    record = {
        "signal_hex": {
            signal_id: {key: value.hex() for key, value in parameters.items()}
            for signal_id, parameters in SIGNALS.items()
        },
        "sigma_hex": SIGMA.hex(),
        "main_evaluation": main_record,
        "support_evaluation": support_record,
        "domain_interval_rational": [[0, 1], [1, 40]],
        "training_interval_rational": [[0, 1], [102, 4096]],
        "input_fingerprints": pilot._fingerprints(arrays),
        "reference_decimal_precision": 100,
        "reference_amplitude_normalized_bound": 1e-13,
        "reference_maximum_errors": truth_errors,
    }
    return arrays, record


def common_for_case(prepared, case_or_spec):
    """Select signal-specific references without exposing another signal's truth."""
    common = prepared.common if isinstance(prepared, PreparedInputs) else prepared
    spec = case_or_spec.spec if isinstance(case_or_spec, PreparedCase) else case_or_spec
    signal_id = spec["signal_id"]
    if signal_id not in SIGNALS or set(common) != COMMON_KEYS:
        raise ValueError("Unknown signal or incomplete common array roles.")
    return {
        **{name: common[name] for name in AXIS_TRUTH_ROLES},
        **{role: common[signal_id + "__" + role] for role in AXIS_TRUTH_ROLES.values()},
    }


def continuous_chunks(
    rng, count, *, sigma, rho, chunk_samples=covariance.CHUNK_SAMPLES
):
    """Draw one stationary path, carrying the AR(1) state over every chunk edge."""
    if (
        type(count) is not int
        or count <= 0
        or type(chunk_samples) is not int
        or chunk_samples <= 0
        or not math.isfinite(sigma)
        or sigma <= 0
        or not math.isfinite(rho)
        or not 0 <= rho < 1
    ):
        raise ValueError("Invalid continuous-noise geometry.")
    previous = None
    innovation = sigma * math.sqrt(1 - rho * rho)
    for start in range(0, count, chunk_samples):
        z = rng.standard_normal(min(chunk_samples, count - start), dtype=np.float64)
        if rho == 0:
            values = sigma * z
        elif previous is None:
            values = np.empty(z.size, dtype=np.float64)
            values[0] = sigma * z[0]
            if z.size > 1:
                values[1:], _ = lfilter(
                    [innovation], [1.0, -rho], z[1:], zi=[rho * values[0]]
                )
        else:
            values, _ = lfilter([innovation], [1.0, -rho], z, zi=[rho * previous])
        if not np.isfinite(values).all():
            raise FloatingPointError("Continuous noise contains nonfinite samples.")
        previous = float(values[-1])
        yield values


def _npy_header(count):
    output = io.BytesIO()
    np.lib.format.write_array_header_1_0(
        output, {"descr": "<f8", "fortran_order": False, "shape": (count,)}
    )
    return output.getvalue()


def _training(spec, rng, path, *, write, clock=None):
    count = max(spec["background_durations_seconds"]) * SAMPLE_RATE
    before = copy.deepcopy(rng.bit_generator.state)
    digest = hashlib.sha256()
    header = _npy_header(count)
    digest.update(header)
    stream = path.open("xb") if write else None
    completed = 0
    try:
        if stream is not None:
            stream.write(header)
        for chunk in continuous_chunks(
            rng,
            count,
            sigma=SIGMA,
            rho=spec["correlation"],
            chunk_samples=spec["chunk_samples"],
        ):
            if clock is not None:
                clock.check()
            raw = np.asarray(chunk, dtype="<f8").tobytes()
            digest.update(raw)
            if stream is not None:
                stream.write(raw)
            completed += chunk.size
    finally:
        if stream is not None:
            stream.close()
    return {
        "bit_generator": "PCG64",
        "state_before": before,
        "state_after": copy.deepcopy(rng.bit_generator.state),
        "sample_count": count,
        "completed_samples": completed,
        "chunk_samples": spec["chunk_samples"],
        "distribution": "stationary_continuous_discrete_ar1"
        if spec["correlation"]
        else "independent_gaussian_white",
        "window_boundary_reset": False,
        "file_sha256": digest.hexdigest(),
        "file_bytes": len(header) + count * 8,
    }


@contextmanager
def open_training(case):
    """Open only one read-only memory map and always release its mapping."""
    path = case.train_path if isinstance(case, PreparedCase) else Path(case)
    if path.is_symlink() or path.absolute() != path.resolve():
        raise ValueError("Training paths must not contain symlinks.")
    values = np.load(path, mmap_mode="r", allow_pickle=False)
    try:
        if values.ndim != 1 or values.dtype != np.dtype("float64"):
            raise ValueError("Invalid training array layout.")
        yield values
    finally:
        values._mmap.close()


def derive_case(spec, common, train_path, *, write=False, clock=None):
    """Generate or replay one case without retaining its complete raw trajectory."""
    expected = {item["id"]: item for item in case_specs(purpose=spec["purpose"])}
    sources._same(
        spec, expected.get(spec["id"]), "Case differs from the fixed protocol."
    )
    if set(common) != COMMON_KEYS:
        raise ValueError("Incomplete common array roles.")
    train_path = Path(train_path)
    generators = pilot_generators(spec["noise_seed"], spec["background_seed"])
    selected_common = common_for_case(common, spec)
    noise_config = (
        AR1NoiseConfig(
            kind="gaussian_ar1",
            standard_deviation=SIGMA,
            bit_generator="PCG64",
            correlation=RHO,
            seed=spec["background_seed"],
        )
        if spec["noise_model"] == "ar1"
        else NoiseConfig(
            kind="gaussian_white",
            standard_deviation=SIGMA,
            bit_generator="PCG64",
            seed=spec["background_seed"],
        )
    )
    rng = generators["signal"]
    noise_before = copy.deepcopy(rng.bit_generator.state)
    noise = draw_noise_window(noise_config, N_SAMPLES, rng)
    true_covariance = (
        ar1_covariance(N_SAMPLES, standard_deviation=SIGMA, correlation=RHO)
        if spec["noise_model"] == "ar1"
        else SIGMA**2 * np.eye(N_SAMPLES)
    )
    arrays = {
        "noise": noise,
        "observed": selected_common["signal"] + noise,
        "covariance_true": true_covariance,
    }
    random = {
        "signal": {
            "seed": spec["noise_seed"],
            "state_before": noise_before,
            "state_after": copy.deepcopy(rng.bit_generator.state),
            "sample_count": N_SAMPLES,
            "transform": "stationary_gaussian_ar1_v1"
            if spec["correlation"]
            else "gaussian_white_v1",
        }
    }
    random["train"] = _training(
        spec, generators["train"], train_path, write=write, clock=clock
    )
    if stream_sha256(train_path, clock=clock) != random["train"]["file_sha256"]:
        raise ValueError("Raw training bytes differ from deterministic generation.")
    for role in ("validation", "check"):
        rng = generators[role]
        before = copy.deepcopy(rng.bit_generator.state)
        count = spec[f"background_{role}_windows"]
        arrays["background_" + role] = np.stack(
            [draw_noise_window(noise_config, N_SAMPLES, rng) for _ in range(count)]
        )
        random[role] = {
            "state_before": before,
            "state_after": copy.deepcopy(rng.bit_generator.state),
            "independent_stationary_windows": count,
            "sample_count_per_window": N_SAMPLES,
        }
    record = {
        "format": FORMAT,
        "spec": copy.deepcopy(spec),
        "status": "ready",
        "arm_status": dict.fromkeys(ARMS, "ready"),
        "random": random,
        "covariance_estimation": {},
        "covariance_diagnostics": {},
        "error": None,
        "background_prefixes": {},
    }
    with open_training(train_path) as train:
        if train.size != max(DURATIONS) * SAMPLE_RATE:
            raise ValueError("Incorrect raw training duration.")
        for seconds, arm in zip(DURATIONS, ESTIMATED_ARMS, strict=True):
            prefix = train[: seconds * SAMPLE_RATE]
            n_train = prefix.size // N_SAMPLES
            raw = None
            record["background_prefixes"][arm] = {
                "file": "background_train.npy",
                "sample_start": 0,
                "sample_stop": seconds * SAMPLE_RATE,
                "n_nonoverlapping_blocks": n_train,
                "estimation_sample_stop": n_train * N_SAMPLES,
                "archived_unused_tail_samples": prefix.size - n_train * N_SAMPLES,
                "covariance_chunk_samples": spec["covariance_chunk_samples"],
                "blocks_independent": not spec["correlation"],
            }
            try:
                raw = covariance.empirical_from_series(
                    prefix[: n_train * N_SAMPLES],
                    n_samples=N_SAMPLES,
                    chunk_samples=spec["covariance_chunk_samples"],
                )
                arrays[f"covariance_raw_{seconds}s"] = raw
                estimate = covariance.estimate_from_raw(
                    raw,
                    arrays["background_validation"],
                    n_train=n_train,
                    structural_rank_bound=n_train,
                    **spec["covariance_estimation"],
                )
            except CovarianceEstimationError as error:
                record["status"] = "covariance_failed"
                record["arm_status"][arm] = "not_run"
                estimate_record = pilot._estimate_record(error=error)
                estimate_record["method"] = covariance.METHOD
                estimate_record["n_train"] = n_train
                estimate_record["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }
            else:
                arrays[f"covariance_estimated_{seconds}s"] = estimate.covariance
                estimate_record = pilot._estimate_record(estimate=estimate)
            record["covariance_estimation"][arm] = estimate_record
            diagnostic_arrays = {
                **arrays,
                "covariance_raw": raw,
                "covariance_estimated": arrays.get(f"covariance_estimated_{seconds}s"),
            }
            record["covariance_diagnostics"][arm] = pilot.covariance_diagnostics(
                diagnostic_arrays,
                "ready"
                if record["arm_status"][arm] == "ready"
                else "covariance_failed",
            )
    arrays = {key: _freeze(value) for key, value in arrays.items()}
    record["input_fingerprints"] = pilot._fingerprints(arrays)
    sources.json_bytes(record)
    return PreparedCase(copy.deepcopy(spec), arrays, record, train_path)


def arm_arrays(prepared, case, arm):
    """Return signal-specific references and one arm's unchanged weighting."""
    if arm not in ARMS:
        raise ValueError("Unknown main-study arm.")
    arrays = {**common_for_case(prepared, case), **case.arrays}
    if arm in ESTIMATED_ARMS:
        suffix = arm.removeprefix("estimated_")
        arrays["covariance_raw"] = arrays.get("covariance_raw_" + suffix)
        arrays["covariance_estimated"] = arrays.get("covariance_estimated_" + suffix)
        arrays["covariance"] = arrays["covariance_estimated"]
    elif arm == "known_covariance":
        arrays["covariance"] = arrays["covariance_true"]
    else:
        arrays["covariance"] = None
    return arrays


def npz_bytes(arrays):
    """Serialize only the small immutable arrays with fixed zip metadata."""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, array in sorted(arrays.items()):
            if name not in COMMON_KEYS | CASE_KEYS:
                raise ValueError("Unknown main-study array role.")
            payload = io.BytesIO()
            np.lib.format.write_array(
                payload, _freeze(array), version=(1, 0), allow_pickle=False
            )
            info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload.getvalue())
    return output.getvalue()


def stream_sha256(path, *, clock=None):
    """Hash a stable regular file in bounded chunks, rejecting symlink traversal."""
    path = Path(path).absolute()
    if path != path.resolve() or path.is_symlink():
        raise ValueError("Expected a regular file without symbolic-link parents.")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Expected a regular input file.")
    digest = hashlib.sha256()

    def signature(value):
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        if signature(os.fstat(stream.fileno())) != signature(before):
            raise ValueError("Input file changed before opening.")
        while chunk := stream.read(1024 * 1024):
            if clock is not None:
                clock.check()
            digest.update(chunk)
        if signature(os.fstat(stream.fileno())) != signature(before) or signature(
            path.stat()
        ) != signature(before):
            raise ValueError("Input file changed while hashing.")
    return digest.hexdigest()


def _hold_file(path, expected, consumed):
    path = Path(path).absolute()
    held = getattr(consumed, "_main_study_stream_files", None)
    if held is None:
        held = {}
        consumed._main_study_stream_files = held
    if path in held:
        if held[path] != expected:
            raise ValueError("Conflicting streaming input snapshot.")
        return
    if stream_sha256(path, clock=consumed.clock) != expected:
        raise ValueError("Input checksum differs: " + str(path))
    held[path] = expected

    def unchanged():
        if stream_sha256(path, clock=consumed.clock) != expected:
            raise ValueError("Streamed input changed after consumption: " + str(path))

    consumed.callbacks.append(unchanged)


def _small_read(path, consumed):
    path = Path(path).absolute()
    if (
        path != path.resolve()
        or path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 8 * 1024**2
    ):
        raise ValueError("Expected a bounded regular metadata file.")
    raw = path.read_bytes()
    consumed.add(path, raw)
    return raw


def _protocol(consumed):
    result = {}
    for path_name, expected in ((PLAN_PATH, PLAN_SHA256), (SEEDS_PATH, SEEDS_SHA256)):
        original = consumed.git_file(PLAN_COMMIT, path_name)
        raw = _small_read(ROOT / path_name, consumed)
        if raw != original or sources.sha256(raw) != expected:
            raise ValueError(
                "Frozen main-study plan or seed table differs from its commit."
            )
        result[path_name] = expected
    addendum = _small_read(ROOT / WIDTH_PLAN_PATH, consumed)
    if sources.sha256(addendum) != WIDTH_PLAN_SHA256:
        raise ValueError("Frozen main-study reference-width addendum differs.")
    return {
        "commit": PLAN_COMMIT,
        "file_sha256": result,
        "prediction_failure_policy": confirmed_search.WIDTH_POLICY,
        "addendum_sha256": {WIDTH_PLAN_PATH: WIDTH_PLAN_SHA256},
    }


def _freeze_sources(consumed):
    software = confirmed_search.freeze_software(consumed)
    if (
        sources.sha256(consumed.git_file(software["software_commit"], WIDTH_PLAN_PATH))
        != WIDTH_PLAN_SHA256
    ):
        raise ValueError("The study software does not contain the frozen width policy.")
    return software


def _call_path(root):
    return root.with_name(root.name + "-call.json")


def _record_call(root, started, wall, usage, manifest_hash, error=None):
    current = pilot._cpu_usage()
    return {
        "format": CALL_FORMAT,
        "kind": "inputs",
        "status": "completed" if error is None else "aborted",
        "input_manifest_sha256": manifest_hash,
        "started_at_utc": started,
        "finished_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - wall,
        "cpu_user_seconds": current[0] - usage[0],
        "cpu_system_seconds": current[1] - usage[1],
        "cpu_scope": "self_plus_reaped_children",
        "cpu_measurement_complete": error is None,
        "measurement_scope": "entry_through_release_and_handler_teardown_excluding_call_write_and_final_rechecks",
        "error": None if error is None else f"{type(error).__name__}: {error}",
    }


def _inventory(root, case_ids, *, locked=False):
    expected = {"common.npz", "preparation.json", "cases"} | (
        {LOCK} if locked else set()
    )
    if root.is_symlink() or {path.name for path in root.iterdir()} != expected:
        raise ValueError("Incomplete or unexpected input root inventory.")
    if {path.name for path in (root / "cases").iterdir()} != set(case_ids):
        raise ValueError("Input case inventory differs from the frozen plan.")
    for case_id in case_ids:
        case_root = root / "cases" / case_id
        if case_root.is_symlink() or {path.name for path in case_root.iterdir()} != {
            "arrays.npz",
            "background_train.npy",
            "record.json",
        }:
            raise ValueError("Incomplete or unexpected case input inventory.")


def _load_arrays(raw, allowed):
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        if (
            len(archive.files) != len(set(archive.files))
            or not set(archive.files) <= allowed
        ):
            raise ValueError("Unexpected or duplicated array roles.")
        arrays = {}
        for name in archive.files:
            array = archive[name]
            if array.dtype != np.dtype("float64"):
                raise ValueError(
                    "Inputs must retain their original Float64 representation."
                )
            arrays[name] = _freeze(array)
    return arrays


def _validate_case_record(spec, arrays, record):
    if (
        set(record)
        != {
            "format",
            "spec",
            "status",
            "arm_status",
            "random",
            "covariance_estimation",
            "covariance_diagnostics",
            "error",
            "background_prefixes",
            "input_fingerprints",
        }
        or record["format"] != FORMAT
        or record["status"] not in {"ready", "covariance_failed"}
        or set(record["arm_status"]) != set(ARMS)
        or set(record["covariance_estimation"]) != set(ESTIMATED_ARMS)
        or set(record["covariance_diagnostics"]) != set(ESTIMATED_ARMS)
        or set(record["background_prefixes"]) != set(ESTIMATED_ARMS)
        or set(record["random"]) != {"signal", "train", "validation", "check"}
    ):
        raise ValueError("Invalid prospective case schema.")
    required = CASE_KEYS - {
        "covariance_raw_64s",
        "covariance_estimated_64s",
        "covariance_raw_4096s",
        "covariance_estimated_4096s",
    }
    failed = False
    for arm in ARMS:
        state = record["arm_status"][arm]
        if arm not in ESTIMATED_ARMS:
            if state != "ready":
                raise ValueError("Only estimated-weighting arms may be unavailable.")
            continue
        suffix = arm.removeprefix("estimated_")
        if state == "ready":
            required.update(
                {"covariance_raw_" + suffix, "covariance_estimated_" + suffix}
            )
        elif state == "not_run":
            failed = True
            if "covariance_estimated_" + suffix in arrays:
                raise ValueError(
                    "An unavailable covariance arm contains a replacement matrix."
                )
        else:
            raise ValueError("Unknown estimated-arm status.")
    if (record["status"] == "covariance_failed") != failed or not required <= set(
        arrays
    ):
        raise ValueError("Input availability and prospective arrays disagree.")
    for name, array in arrays.items():
        expected_shape = (
            (spec[f"background_{name.removeprefix('background_')}_windows"], N_SAMPLES)
            if name.startswith("background_")
            else (N_SAMPLES, N_SAMPLES)
            if "covariance" in name
            else (N_SAMPLES,)
        )
        if array.shape != expected_shape:
            raise ValueError("Wrong prospective array shape: " + name)
        if "covariance" in name and not np.array_equal(array, array.T):
            raise ValueError("Prospective covariance is not exactly symmetric.")


def _verify(root, consumed, *, locked=False, include_call=True):
    raw = _small_read(root / "preparation.json", consumed)
    manifest = sources.read_json(raw)
    if (
        set(manifest)
        != {
            "format",
            "status",
            "purpose",
            "technical",
            "protocol",
            "software",
            "case_order",
            "cases",
            "common",
            "file_sha256",
            "initial_rng_states",
            "planned_search_calls",
            "planned_algorithm_outputs",
        }
        or manifest.get("format") != FORMAT
        or manifest.get("status") != "prepared"
        or manifest.get("purpose") not in {"scientific", "technical"}
        or manifest.get("technical") is not (manifest["purpose"] == "technical")
    ):
        raise ValueError("Invalid main-study input manifest.")
    specs = case_specs(purpose=manifest["purpose"])
    ids = [spec["id"] for spec in specs]
    sources._same(manifest["case_order"], ids, "Changed input execution order.")
    sources._same(
        manifest["cases"], list(specs), "Changed prospective input specifications."
    )
    sources._same(
        manifest["initial_rng_states"],
        initial_rng_states(),
        "Changed actual random initial states.",
    )
    _inventory(root, ids, locked=locked)
    consumed.callbacks.append(lambda: _inventory(root, ids, locked=locked))
    sources._same(
        manifest["protocol"], _protocol(consumed), "Changed protocol binding."
    )
    sources._same(
        manifest["software"], _freeze_sources(consumed), "Changed input software."
    )
    expected_names = {"common.npz"} | {
        f"cases/{case_id}/{name}"
        for case_id in ids
        for name in ("arrays.npz", "background_train.npy", "record.json")
    }
    if set(manifest["file_sha256"]) != expected_names:
        raise ValueError("Unexpected prospective input file roles.")
    for name, digest in manifest["file_sha256"].items():
        _hold_file(root / name, digest, consumed)
    common, common_record = derive_common_inputs()
    sources._same(
        manifest["common"],
        common_record,
        "Changed common acquisition/evaluation grids.",
    )
    if _small_read(root / "common.npz", consumed) != npz_bytes(common):
        raise ValueError("Stored common arrays differ from deterministic generation.")
    expected_calls = 1280 if manifest["purpose"] == "scientific" else 8
    if (
        type(manifest.get("planned_search_calls")) is not int
        or manifest["planned_search_calls"] != expected_calls
    ):
        raise ValueError("Wrong prospective search count.")
    expected_outputs = 320 if manifest["purpose"] == "scientific" else expected_calls
    if (
        type(manifest.get("planned_algorithm_outputs")) is not int
        or manifest["planned_algorithm_outputs"] != expected_outputs
    ):
        raise ValueError("Wrong prospective output count.")
    call = None
    if include_call:
        call = sources.read_json(_small_read(_call_path(root), consumed))
        if (
            set(call)
            != {
                "format",
                "kind",
                "status",
                "input_manifest_sha256",
                "started_at_utc",
                "finished_at_utc",
                "wall_seconds",
                "cpu_user_seconds",
                "cpu_system_seconds",
                "cpu_scope",
                "cpu_measurement_complete",
                "measurement_scope",
                "error",
            }
            or call.get("kind") != "inputs"
            or call.get("format") != CALL_FORMAT
            or call.get("status") != "completed"
            or call.get("input_manifest_sha256") != sources.sha256(raw)
            or call.get("error") is not None
            or call.get("measurement_scope")
            != "entry_through_release_and_handler_teardown_excluding_call_write_and_final_rechecks"
            or call.get("cpu_scope") != "self_plus_reaped_children"
            or call.get("cpu_measurement_complete") is not True
        ):
            raise ValueError("Incomplete input call-cost evidence.")
        for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
            value = call.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Invalid measured input preparation cost.")
        for key in ("started_at_utc", "finished_at_utc"):
            try:
                value = datetime.fromisoformat(call[key])
                if value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
                    raise ValueError
            except (TypeError, ValueError) as error:
                raise ValueError("Invalid UTC input-call timestamp.") from error
        if call["wall_seconds"] >= PREPARE_SECONDS:
            raise ValueError("Input preparation exceeded its fixed deadline.")
    consumed.check()
    return PreparedInputs(
        root, manifest, common, {spec["id"]: spec for spec in specs}, call
    )


def verify_inputs(path, consumed=None, *, regenerate=False):
    """Verify streamed hashes and small references; optionally regenerate each case."""
    root = Path(path).absolute()
    if root != root.resolve() or not root.is_dir() or (root / LOCK).exists():
        raise ValueError("Expected existing released inputs without symlinks.")
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(PREPARE_SECONDS))
    prepared = _verify(root, consumed)
    if regenerate:
        for case_id in prepared.cases:
            read_case(prepared, case_id, consumed=consumed, regenerate=True)
    consumed.check()
    return prepared


def read_case(prepared, case_id, consumed=None, *, regenerate=True):
    """Read one small case, with optional bounded-memory deterministic replay."""
    if case_id not in prepared.cases:
        raise ValueError("Unknown fixed input case.")
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(PREPARE_SECONDS))
    root = prepared.root / "cases" / case_id
    for name in ("arrays.npz", "record.json", "background_train.npy"):
        _hold_file(
            root / name,
            prepared.manifest["file_sha256"][f"cases/{case_id}/{name}"],
            consumed,
        )
    raw_arrays = _small_read(root / "arrays.npz", consumed)
    raw_record = _small_read(root / "record.json", consumed)
    record = sources.read_json(raw_record)
    sources._same(record.get("spec"), prepared.cases[case_id], "Case identity changed.")
    arrays = _load_arrays(raw_arrays, CASE_KEYS)
    _validate_case_record(prepared.cases[case_id], arrays, record)
    sources._same(
        record.get("input_fingerprints"),
        pilot._fingerprints(arrays),
        "Case array fingerprints differ.",
    )
    if regenerate:
        replay = derive_case(
            prepared.cases[case_id],
            prepared.common,
            root / "background_train.npy",
            clock=consumed.clock,
        )
        if (
            sources.json_bytes(replay.record) != raw_record
            or npz_bytes(replay.arrays) != raw_arrays
        ):
            raise ValueError("Case differs from deterministic input regeneration.")
    consumed.check()
    return PreparedCase(
        copy.deepcopy(prepared.cases[case_id]),
        arrays,
        record,
        root / "background_train.npy",
    )


def prepare_inputs(path, *, purpose="scientific", technical=None):
    """Create exclusive complete prospective inputs, retaining a lock on failure."""
    purpose = _purpose(purpose, technical)
    root = publication.validate_output(path)
    if _call_path(root).exists() or _call_path(root).is_symlink():
        raise ValueError("Input-call evidence already exists.")
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, wall, usage = _utc_now(), time.monotonic(), pilot._cpu_usage()
    clock = publication.Deadline(PREPARE_SECONDS)
    consumed = publication.Consumption(clock)
    owned, manifest_hash = False, None
    try:
        with clock.active():
            software, protocol = _freeze_sources(consumed), _protocol(consumed)
            rng_initial_record = initial_rng_states()
            specs = case_specs(purpose=purpose)
            root.mkdir(parents=True, exist_ok=False)
            owned = True
            (root / LOCK).write_text("Input preparation has not completed.\n")
            (root / "cases").mkdir()
            common, common_record = derive_common_inputs()
            common_raw = npz_bytes(common)
            (root / "common.npz").write_bytes(common_raw)
            hashes = {"common.npz": sources.sha256(common_raw)}
            for spec in specs:
                clock.check()
                case_root = root / "cases" / spec["id"]
                case_root.mkdir()
                case = derive_case(
                    spec,
                    common,
                    case_root / "background_train.npy",
                    write=True,
                    clock=clock,
                )
                small = {
                    "arrays.npz": npz_bytes(case.arrays),
                    "record.json": sources.json_bytes(case.record),
                }
                for name, raw in small.items():
                    (case_root / name).write_bytes(raw)
                for name in (*small, "background_train.npy"):
                    hashes[f"cases/{spec['id']}/{name}"] = stream_sha256(
                        case_root / name, clock=clock
                    )
            manifest = {
                "format": FORMAT,
                "status": "prepared",
                "purpose": purpose,
                "technical": purpose == "technical",
                "protocol": protocol,
                "software": software,
                "case_order": [spec["id"] for spec in specs],
                "cases": list(specs),
                "initial_rng_states": rng_initial_record,
                "common": common_record,
                "file_sha256": hashes,
                "planned_search_calls": 1280 if purpose == "scientific" else 8,
                "planned_algorithm_outputs": 320 if purpose == "scientific" else 8,
            }
            raw = sources.json_bytes(manifest)
            (root / "preparation.json").write_bytes(raw)
            manifest_hash = sources.sha256(raw)
            locked = publication.Consumption(clock)
            _verify(root, locked, locked=True, include_call=False)
            consumed.check()
            (root / LOCK).unlink()
            closing = publication.Consumption(clock)
            _verify(root, closing, include_call=False)
            consumed.check()
        consumed.check()
        closing.check()
        call = _record_call(root, started, wall, usage, manifest_hash)
        _call_path(root).write_bytes(sources.json_bytes(call))
        verified = _verify(root, publication.Consumption(clock))
        return verified
    except BaseException as error:
        if owned:
            try:
                (root / LOCK).write_text("Input release revoked.\n")
            finally:
                _call_path(root).write_bytes(
                    sources.json_bytes(
                        _record_call(root, started, wall, usage, manifest_hash, error)
                    )
                )
        raise
