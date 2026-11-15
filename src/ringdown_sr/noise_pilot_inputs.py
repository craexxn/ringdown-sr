"""Freeze all prospective noise-pilot inputs before any search or reference fit."""

import copy
import io
import math
import resource
import signal
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.linalg import LinAlgError, cholesky, norm, solve_triangular

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search
from .background import (
    background_random_record,
    draw_noise_window,
    generate_background,
    noise_draw_record,
    pilot_generators,
)
from .config import AR1NoiseConfig, BackgroundConfig, NoiseConfig, SamplingConfig
from .covariance_estimation import CovarianceEstimationError, estimate_covariance
from .noise import ar1_covariance
from .pilot import _utc_now
from .signals import ringdown_signal, sample_times

ROOT = sources.ROOT
FORMAT = "ringdown-sr-noise-pilot-inputs-1"
CALL_FORMAT = "ringdown-sr-noise-pilot-input-call-1"
PLAN_PATH = "docs/noise_pilot_plan.md"
PLAN_COMMIT = "27367a707b0f78c2d8e4ec397e0af6d958f5c527"
PLAN_SHA256 = "2a8e521b7729a668832ca02b0c8dd587d46ddec4010d7657d71e7b4d4d295fb8"
SEED_BASE_COMMIT = "4e1fa18461b2b32fc2f8c39e77fd7c51b06c868a"
GRID_SEED = 2026111410
LOCK = "INPUTS_LOCKED"
PREPARE_SECONDS = 2400
COMMON_KEYS = {
    "time_s",
    "signal",
    "diagnostic_time_s",
    "diagnostic_truth",
    "irregular_time_s",
    "irregular_truth",
}
CASE_KEYS = {
    "noise",
    "observed",
    "covariance_true",
    "background_train",
    "background_validation",
    "background_check",
    "covariance_raw",
    "covariance_estimated",
}
SIGNAL = {
    "amplitude": float.fromhex("0x1.d555555555555p-1"),
    "frequency_hz": float.fromhex("0x1.0900000000000p+8"),
    "decay_time_s": float.fromhex("0x1.b4e81b4e81b4fp-8"),
    "phase_rad": float.fromhex("0x1.0000000000000p-2"),
}
SIGMA = float.fromhex("0x1.7777777777778p-5")
ALPHAS = (0.0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0)
# Rows retain the separately committed protocol's block/white/AR(1) order.
SEED_ROWS = (
    (566695175, 415413690, 1734708527, 1539770707, 1622328068, 1225308221),
    (495067099, 1676223713, 1494771928, 1678574396, 2096825714, 1211174835),
    (1566182586, 809849776, 596152422, 614436374, 1180778442, 1006610954),
    (1777518894, 1064722274, 486821846, 99725564, 814485586, 575382670),
    (796396672, 2142819059, 1618513868, 674176212, 552276091, 1316430785),
    (522170952, 878189361, 1459026218, 1799747039, 521508560, 716632464),
    (541435809, 2074815860, 1886273123, 2057732517, 1527388407, 569076422),
    (1101297837, 576312512, 62189220, 883512557, 1060488681, 848276631),
    (1972424494, 232958399, 512201544, 377696954, 1835826724, 670096281),
    (630298913, 490261955, 750060073, 1366925241, 1786922412, 652748693),
    (714889379, 2129723798, 314569512, 604072557, 732549740, 515882677),
    (197369405, 1481384320, 1719232956, 1051201175, 1449253553, 459990396),
)


@dataclass(frozen=True)
class PreparedCase:
    """Retain one prospective comparison and every realized preparation role."""

    spec: dict
    arrays: dict
    record: dict


@dataclass(frozen=True)
class PreparedInputs:
    """Expose verified common references and cases in their frozen execution order."""

    manifest: dict
    common: dict
    cases: dict[str, PreparedCase]
    call: dict | None = None


def _freeze(array):
    values = np.ascontiguousarray(array, dtype="<f8")
    if not np.all(np.isfinite(values)):
        raise FloatingPointError("Prospective inputs contain nonfinite values.")
    # Immutable bytes prohibit callers from re-enabling WRITEABLE.
    return np.frombuffer(values.tobytes(), dtype="<f8").reshape(values.shape)


def _fingerprints(arrays):
    return {name: sources.fingerprint(value) for name, value in sorted(arrays.items())}


def _spec(block, model, seeds, *, technical):
    return {
        "id": "technical-ar1" if technical else f"{model}-{block:02d}",
        "block": block,
        "noise_model": model,
        "noise_seed": seeds[0],
        "background_seed": seeds[1],
        "search_seeds": list(seeds[2:]),
        "technical": technical,
        "niterations": 10 if technical else 1000,
        "sampling": {"n_samples": 128, "sample_rate_hz": 4096.0},
        "signal": dict(SIGNAL),
        "noise": {
            "kind": "gaussian_white" if model == "white" else "gaussian_ar1",
            "standard_deviation": SIGMA,
            "bit_generator": "PCG64",
            "seed": seeds[0],
            **({"correlation": 0.65} if model == "ar1" else {}),
        },
        "background": {
            "n_train": 64,
            "n_validation": 128,
            "n_check": 256,
            "bit_generator": "PCG64",
            "seed": seeds[1],
            "stream_scheme": "seedsequence_role_v1",
        },
        "covariance_estimation": {
            "mean_mode": "known_zero",
            "alpha_candidates": list(ALPHAS),
            "kappa_max": 1e8,
        },
    }


def case_specs(*, technical=False):
    """Return only the committed cases, with no configurable sampling or seed budget."""
    if type(technical) is not bool:
        raise TypeError("technical must be a boolean.")
    if technical:
        return (_spec(0, "ar1", (2026111411, 2026111412, 2026111413), technical=True),)
    result = []
    for block in range(1, 7):
        models = ("white", "ar1") if block % 2 else ("ar1", "white")
        for model in models:
            index = 2 * (block - 1) + (model == "ar1")
            result.append(_spec(block, model, SEED_ROWS[index], technical=False))
    return tuple(result)


def _truth_reference(time_s, actual):
    """Check exact Binary64 parameters against mathematical pi at 100 decimals."""
    maximum = mp.mpf(0)
    with mp.workdps(100):
        amplitude, frequency, decay, phase = (
            mp.mpf(SIGNAL[name])
            for name in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
        )
        for time_value, signal_value in zip(time_s, actual, strict=True):
            t = mp.mpf(float(time_value))
            expected = (
                amplitude
                * mp.exp(-t / decay)
                * mp.cos(2 * mp.pi * frequency * t + phase)
            )
            error = abs(mp.mpf(float(signal_value)) - expected) / amplitude
            maximum = max(maximum, error)
        if maximum >= mp.mpf("1e-13"):
            raise ValueError("Noise-pilot truth exceeds the frozen reference bound.")
        return float(maximum)


def derive_common_inputs():
    """Generate the three fixed grids without advancing any search/noise generator."""
    time_s = sample_times(128, 4096.0)
    inner = (
        np.arange(127, dtype=np.float64)[:, None]
        + np.arange(1, 8, dtype=np.float64)[None, :] / 8
    ).reshape(-1) / 4096
    rng = np.random.Generator(np.random.PCG64(GRID_SEED))
    before = copy.deepcopy(rng.bit_generator.state)
    irregular = []
    for index in range(1024):
        for _ in range(100):
            fraction = rng.random()
            value = (index + fraction) / 1024 * (127 / 4096)
            if 0 < fraction < 1 and not (value * 32768).is_integer():
                irregular.append(value)
                break
        else:
            raise ValueError("Could not generate the committed irregular grid.")
    arrays = {
        "time_s": time_s,
        "diagnostic_time_s": inner,
        "irregular_time_s": np.array(irregular, dtype=np.float64),
    }
    reference_errors = {}
    for time_name, truth_name in (
        ("time_s", "signal"),
        ("diagnostic_time_s", "diagnostic_truth"),
        ("irregular_time_s", "irregular_truth"),
    ):
        values = ringdown_signal(arrays[time_name], **SIGNAL)
        arrays[truth_name] = values
        reference_errors[truth_name] = _truth_reference(arrays[time_name], values)
    arrays = {name: _freeze(values) for name, values in arrays.items()}
    record = {
        "signal_hex": {name: value.hex() for name, value in SIGNAL.items()},
        "sigma_hex": SIGMA.hex(),
        "grid_seed": GRID_SEED,
        "grid_state_before": before,
        "grid_state_after": copy.deepcopy(rng.bit_generator.state),
        "reference_decimal_precision": 100,
        "reference_amplitude_normalized_bound": 1e-13,
        "reference_maximum_errors": reference_errors,
        "input_fingerprints": _fingerprints(arrays),
    }
    return arrays, record


def _estimate_record(estimate=None, error=None):
    if estimate is not None:
        return {
            "status": "ready",
            "method": estimate.method,
            "mean_mode": estimate.mean_mode,
            "n_train": estimate.n_train,
            "n_validation": estimate.n_validation,
            "kappa_max": estimate.kappa_max,
            "mu": estimate.mu,
            "alpha_selected": estimate.alpha_selected,
            "candidates": [asdict(candidate) for candidate in estimate.candidates],
            "refit": False,
        }
    mu = error.mu
    return {
        "status": "failed",
        "method": "empirical_identity_shrinkage_holdout_v1",
        "mean_mode": "known_zero",
        "n_train": 64,
        "n_validation": 128,
        "kappa_max": 1e8,
        "mu": mu if mu is None or math.isfinite(mu) else None,
        "mu_nonfinite": mu is not None and not math.isfinite(mu),
        "alpha_selected": None,
        "candidates": [asdict(candidate) for candidate in error.candidates],
        "refit": False,
    }


def _finite_diagnostic(value):
    value = float(value)
    if not math.isfinite(value):
        raise FloatingPointError("Covariance diagnostic is not representable.")
    return value


def _background_check_score(matrix, windows):
    """Score already frozen matrices on held-out windows, without refitting."""
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        factor = cholesky(matrix, lower=True, check_finite=False)
        logdet = _finite_diagnostic(2 * np.log(factor.diagonal()).sum())
        transformed = solve_triangular(
            factor, windows.T, lower=True, check_finite=False
        )
        if not np.all(np.isfinite(transformed)):
            raise FloatingPointError("Background-check whitening is not representable.")
        scaled = float(
            norm((transformed / math.sqrt(len(windows))).ravel(), check_finite=False)
        )
        quadratic = _finite_diagnostic(scaled * scaled)
        return {
            "n_windows": len(windows),
            "log_determinant": logdet,
            "quadratic_mean": quadratic,
            "score": _finite_diagnostic(logdet + quadratic),
        }


def _condition_number(matrix):
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        scale = float(np.max(np.abs(matrix)))
        if not scale > 0:
            raise FloatingPointError("Covariance scale is not positive.")
        eigenvalues = np.linalg.eigvalsh(matrix / scale)
        if not np.all(np.isfinite(eigenvalues)) or eigenvalues[0] <= 0:
            raise FloatingPointError("Covariance eigenvalue diagnosis is not positive.")
        return _finite_diagnostic(eigenvalues[-1] / eigenvalues[0])


def _relative_frobenius(estimated, truth):
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        scale = max(float(np.max(np.abs(estimated))), float(np.max(np.abs(truth))))
        if not scale > 0:
            raise FloatingPointError("Reference covariance scale is not positive.")
        reference = truth / scale
        denominator = float(norm(reference.ravel(), check_finite=False))
        if not denominator > 0:
            raise FloatingPointError("Reference covariance norm is not positive.")
        return _finite_diagnostic(
            float(norm((estimated / scale - reference).ravel(), check_finite=False))
            / denominator
        )


def _diagnostic(action=None, *, reason=None):
    if reason is not None:
        return {"status": "unavailable", "value": None, "reason": reason, "error": None}
    try:
        value = action()
    except (FloatingPointError, OverflowError, LinAlgError) as error:
        return {
            "status": "unavailable",
            "value": None,
            "reason": "numerical_diagnostic_failure",
            "error": {"type": type(error).__name__, "message": str(error)},
        }
    return {"status": "available", "value": value, "reason": None, "error": None}


def covariance_diagnostics(arrays, status):
    """Keep held-out diagnostics separate from generation and alpha selection."""
    result = {
        "diagnostic_role": "post_selection_only",
        "changes_covariance_or_alpha": False,
        "background_check": {},
        "condition_number": {},
        "relative_frobenius_error": None,
    }
    for role in ("true", "estimated"):
        reason = (
            "data_preparation_failed"
            if status == "data_failed"
            else "covariance_estimation_failed"
            if role == "estimated" and status == "covariance_failed"
            else None
        )
        matrix = arrays.get("covariance_" + role)
        result["background_check"][role] = _diagnostic(
            lambda m=matrix: _background_check_score(m, arrays["background_check"]),
            reason=reason,
        )
        result["condition_number"][role] = _diagnostic(
            lambda m=matrix: _condition_number(m), reason=reason
        )
    unavailable = (
        "data_preparation_failed"
        if status == "data_failed"
        else "covariance_estimation_failed"
        if status == "covariance_failed"
        else None
    )
    result["relative_frobenius_error"] = _diagnostic(
        lambda: _relative_frobenius(
            arrays["covariance_estimated"], arrays["covariance_true"]
        ),
        reason=unavailable,
    )
    return result


def derive_case(spec, common):
    """Reproduce data and covariance selection; never run a reference fit or search."""
    candidates = case_specs() + case_specs(technical=True)
    if not any(
        sources.json_bytes(spec) == sources.json_bytes(item) for item in candidates
    ):
        raise ValueError("Case differs from the committed noise-pilot protocol.")
    if set(common) != COMMON_KEYS:
        raise ValueError("Incomplete common noise-pilot reference roles.")
    sampling = SamplingConfig(**spec["sampling"])
    background_config = BackgroundConfig(**spec["background"])
    noise_type = AR1NoiseConfig if spec["noise_model"] == "ar1" else NoiseConfig
    noise = noise_type(**spec["noise"])
    generators = pilot_generators(noise.seed, background_config.seed)
    noise_random = noise_draw_record(noise, 128, 1)
    noise_random.update(seed=noise.seed, derivation="direct_seed_v1")
    random = {
        "signal": noise_random,
        "background": background_random_record(noise, sampling, background_config),
    }
    arrays, background = {}, {}
    record = {
        "format": FORMAT,
        "spec": copy.deepcopy(spec),
        "status": "ready",
        "stage": "generation",
        "random": random,
        "covariance_estimation": None,
        "arm_status": {
            "ordinary": "ready",
            "known_covariance": "ready",
            "estimated_covariance": "ready",
        },
        "error": None,
    }
    try:
        rng = generators["signal"]
        noise_random["state_before"] = copy.deepcopy(rng.bit_generator.state)
        try:
            values = draw_noise_window(noise, 128, rng)
            noise_random["calls"]["completed_calls"] = 1
            arrays["noise"] = _freeze(values)
        finally:
            noise_random["state_after"] = copy.deepcopy(rng.bit_generator.state)
        with np.errstate(over="raise", invalid="raise"):
            arrays["observed"] = _freeze(common["signal"] + arrays["noise"])
        arrays["covariance_true"] = _freeze(
            ar1_covariance(128, standard_deviation=SIGMA, correlation=0.65)
            if spec["noise_model"] == "ar1"
            else SIGMA**2 * np.eye(128)
        )
        record["stage"] = "background_generation"
        generate_background(
            noise,
            sampling,
            background_config,
            windows=background,
            random=random["background"],
            generators=generators,
        )
    except (FloatingPointError, OverflowError) as error:
        record.update(
            status="data_failed",
            error={"type": type(error).__name__, "message": str(error)},
        )
        record["arm_status"] = dict.fromkeys(record["arm_status"], "not_run")
    finally:
        arrays.update(
            {"background_" + name: _freeze(value) for name, value in background.items()}
        )
    if record["status"] == "ready":
        record["stage"] = "covariance_estimation"
        try:
            estimate = estimate_covariance(
                background["train"],
                background["validation"],
                **spec["covariance_estimation"],
            )
        except CovarianceEstimationError as error:
            record.update(
                status="covariance_failed",
                covariance_estimation=_estimate_record(error=error),
                error={"type": type(error).__name__, "message": str(error)},
            )
            record["arm_status"]["estimated_covariance"] = "not_run"
            if error.raw_covariance is not None:
                arrays["covariance_raw"] = _freeze(error.raw_covariance)
        else:
            arrays["covariance_raw"] = _freeze(estimate.raw_covariance)
            arrays["covariance_estimated"] = _freeze(estimate.covariance)
            record["covariance_estimation"] = _estimate_record(estimate=estimate)
            record["stage"] = "complete"
    arrays = {name: _freeze(value) for name, value in arrays.items()}
    record["input_fingerprints"] = _fingerprints(arrays)
    record["covariance_diagnostics"] = covariance_diagnostics(arrays, record["status"])
    # Strict JSON rejects malformed nonfinite evidence, rather than hiding it.
    sources.json_bytes(record)
    return PreparedCase(copy.deepcopy(spec), arrays, record)


def npz_bytes(arrays):
    """Keep archive bytes independent of generation time and dictionary order."""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, array in sorted(arrays.items()):
            if name not in COMMON_KEYS | CASE_KEYS:
                raise ValueError("Unknown prospective array role.")
            payload = io.BytesIO()
            np.lib.format.write_array(
                payload, _freeze(array), version=(1, 0), allow_pickle=False
            )
            info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload.getvalue())
    return output.getvalue()


def _protocol(consumed):
    original = consumed.git_file(PLAN_COMMIT, PLAN_PATH)
    path = ROOT / PLAN_PATH
    current = path.read_bytes()
    if (
        path.is_symlink()
        or sources.sha256(original) != PLAN_SHA256
        or current != original
    ):
        raise ValueError("Frozen noise-pilot plan differs from its separate commit.")
    consumed.add(path, current)
    return {
        "commit": PLAN_COMMIT,
        "path": PLAN_PATH,
        "sha256": PLAN_SHA256,
        "seed_exclusion_base_commit": SEED_BASE_COMMIT,
    }


def _freeze_sources(consumed):
    software = confirmed_search.freeze_software(consumed)
    _protocol(consumed)
    return software


def _read(root, name, consumed):
    path = root / str(sources.safe_name(name))
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a regular prospective input artifact.")
    raw = sources.bounded_read(path)
    consumed.add(path, raw)
    return raw


def _inventory(root, ids, *, locked=False):
    expected = {"common.npz", "cases", "preparation.json"} | (
        {LOCK} if locked else set()
    )
    if root.is_symlink() or {p.name for p in root.iterdir()} != expected:
        raise ValueError("Prospective input root inventory changed.")
    if any((root / name).is_symlink() for name in expected):
        raise ValueError("Prospective inputs cannot contain symlinks.")
    directory = root / "cases"
    expected_cases = {
        case + extension for case in ids for extension in (".npz", ".json")
    }
    if (
        not directory.is_dir()
        or {p.name for p in directory.iterdir()} != expected_cases
    ):
        raise ValueError("Prospective case inventory changed.")
    if any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError("Prospective case artifacts must be regular files.")


def _timing(started, wall, usage):
    user, system = _cpu_usage()
    return {
        "started_at_utc": started,
        "finished_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - wall,
        "cpu_user_seconds": user - usage[0],
        "cpu_system_seconds": system - usage[1],
        "measurement_scope": "preparation_until_manifest_write_excludes_closing_verification",
    }


def _cpu_usage():
    usages = (
        resource.getrusage(resource.RUSAGE_SELF),
        resource.getrusage(resource.RUSAGE_CHILDREN),
    )
    return tuple(
        sum(getattr(usage, field) for usage in usages)
        for field in ("ru_utime", "ru_stime")
    )


def _verify_timing(record):
    expected = {
        "started_at_utc",
        "finished_at_utc",
        "wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "measurement_scope",
    }
    if (
        set(record) != expected
        or record["measurement_scope"]
        != "preparation_until_manifest_write_excludes_closing_verification"
    ):
        raise ValueError("Unexpected input-preparation timing scope.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        value = record[name]
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid input-preparation cost evidence.")
    start, finish = (
        datetime.fromisoformat(record[key])
        for key in ("started_at_utc", "finished_at_utc")
    )
    if start.utcoffset() is None or finish.utcoffset() is None or finish < start:
        raise ValueError("Invalid input-preparation timestamps.")


def _call_path(root):
    return root.with_name(root.name + "-call.json")


def _call_record(root, manifest_sha256, started, wall, usage, error=None):
    user, system = _cpu_usage()
    return {
        "format": CALL_FORMAT,
        "status": "completed" if error is None else "aborted",
        "input_directory": root.name,
        "input_manifest_sha256": manifest_sha256,
        "started_at_utc": started,
        "finished_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - wall,
        "cpu_user_seconds": user - usage[0],
        "cpu_system_seconds": system - usage[1],
        "cpu_scope": "self_plus_children",
        "measurement_scope": (
            "prepare_inputs_through_handler_teardown_excludes_call_write_and_final_checks"
        ),
        "error": None
        if error is None
        else {"type": type(error).__name__, "message": str(error)},
    }


def _verify_call(root, consumed):
    record = sources.read_json(_read(root.parent, _call_path(root).name, consumed))
    if (
        set(record)
        != {
            "format",
            "status",
            "input_directory",
            "input_manifest_sha256",
            "started_at_utc",
            "finished_at_utc",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "cpu_scope",
            "measurement_scope",
            "error",
        }
        or record["format"] != CALL_FORMAT
        or record["status"] != "completed"
        or record["input_directory"] != root.name
        or record["input_manifest_sha256"]
        != sources.sha256(consumed.files[root / "preparation.json"])
        or record["cpu_scope"] != "self_plus_children"
        or record["measurement_scope"]
        != "prepare_inputs_through_handler_teardown_excludes_call_write_and_final_checks"
        or record["error"] is not None
    ):
        raise ValueError("Incomplete or contradictory preparation-call evidence.")
    partial = {
        key: record[key]
        for key in (
            "started_at_utc",
            "finished_at_utc",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
        )
    }
    partial["measurement_scope"] = (
        "preparation_until_manifest_write_excludes_closing_verification"
    )
    _verify_timing(partial)
    manifest = sources.read_json(consumed.files[root / "preparation.json"])
    for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if record[key] < manifest["timing"][key]:
            raise ValueError(
                "Complete preparation-call cost is below its included part."
            )
    consumed.check()
    return record


def _verify(root, consumed, *, locked=False):
    manifest = sources.read_json(_read(root, "preparation.json", consumed))
    if (
        set(manifest)
        != {
            "format",
            "status",
            "technical",
            "protocol",
            "software",
            "case_order",
            "planned_search_calls",
            "planned_algorithm_outputs",
            "common",
            "file_sha256",
            "timing",
        }
        or manifest["format"] != FORMAT
        or manifest["status"] != "prepared"
        or type(manifest["technical"]) is not bool
    ):
        raise ValueError("Invalid global prospective input manifest.")
    specs = case_specs(technical=manifest["technical"])
    ids = [spec["id"] for spec in specs]
    _inventory(root, ids, locked=locked)
    consumed.callbacks.append(lambda: _inventory(root, ids, locked=locked))
    sources._same(
        manifest["protocol"], _protocol(consumed), "Changed noise-pilot plan binding."
    )
    sources._same(
        manifest["software"],
        _freeze_sources(consumed),
        "Changed input-preparation software.",
    )
    if (
        manifest["case_order"] != ids
        or type(manifest["planned_search_calls"]) is not int
        or manifest["planned_search_calls"] != (3 if manifest["technical"] else 144)
        or type(manifest["planned_algorithm_outputs"]) is not int
        or manifest["planned_algorithm_outputs"] != (3 if manifest["technical"] else 36)
    ):
        raise ValueError("Changed prospective case or search-call inventory.")
    _verify_timing(manifest["timing"])
    common, common_record = derive_common_inputs()
    sources._same(
        manifest["common"], common_record, "Changed common diagnostic references."
    )
    payloads = {"common.npz": npz_bytes(common)}
    cases = {}
    for spec in specs:
        consumed.clock.check()
        case = derive_case(spec, common)
        cases[spec["id"]] = case
        payloads[f"cases/{spec['id']}.npz"] = npz_bytes(case.arrays)
        payloads[f"cases/{spec['id']}.json"] = sources.json_bytes(case.record)
    if manifest["file_sha256"] != {
        name: sources.sha256(raw) for name, raw in sorted(payloads.items())
    }:
        raise ValueError(
            "Prospective payload hashes differ from deterministic regeneration."
        )
    for name, expected in payloads.items():
        if _read(root, name, consumed) != expected:
            raise ValueError("Prospective input changed: " + name)
    consumed.check()
    return PreparedInputs(manifest, common, cases)


def verify_inputs(path, consumed=None):
    """Read-rederive every original input without modifying it or running any fit."""
    root = Path(path).absolute()
    if root != root.resolve() or not root.is_dir():
        raise ValueError("Expected a regular prospective input directory.")
    if (root / LOCK).exists():
        raise ValueError("Prospective input preparation is locked.")
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(PREPARE_SECONDS))
    result = _verify(root, consumed)
    call = _verify_call(root, consumed)
    return PreparedInputs(result.manifest, result.common, result.cases, call)


def prepare_inputs(path, *, technical=False):
    """Prepare all fixed cases under an interruption-safe release lock before search."""
    call_started, call_wall, call_usage = _utc_now(), time.monotonic(), _cpu_usage()
    specs = case_specs(technical=technical)
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    root = publication.validate_output(path)
    if _call_path(root).exists() or _call_path(root).is_symlink():
        raise ValueError(
            "Preparation-call evidence must not overwrite an existing file."
        )
    clock = publication.Deadline(PREPARE_SECONDS)
    consumed = publication.Consumption(clock)
    owned = False
    manifest_sha256 = None
    try:
        with clock.active():
            started, wall, usage = _utc_now(), time.monotonic(), _cpu_usage()
            software = _freeze_sources(consumed)
            protocol = _protocol(consumed)
            root.mkdir(parents=True, exist_ok=False)
            owned = True
            (root / LOCK).write_text("Prospective input preparation is incomplete.\n")
            (root / "cases").mkdir()
            common, common_record = derive_common_inputs()
            payloads = {"common.npz": npz_bytes(common)}
            for spec in specs:
                consumed.clock.check()
                case = derive_case(spec, common)
                payloads[f"cases/{spec['id']}.npz"] = npz_bytes(case.arrays)
                payloads[f"cases/{spec['id']}.json"] = sources.json_bytes(case.record)
            for name, raw in payloads.items():
                destination = root / name
                destination.write_bytes(raw)
                consumed.add(destination, raw)
            manifest = {
                "format": FORMAT,
                "status": "prepared",
                "technical": technical,
                "protocol": protocol,
                "software": software,
                "case_order": [spec["id"] for spec in specs],
                "planned_search_calls": 3 if technical else 144,
                "planned_algorithm_outputs": 3 if technical else 36,
                "common": common_record,
                "file_sha256": {
                    name: sources.sha256(raw) for name, raw in sorted(payloads.items())
                },
                "timing": _timing(started, wall, usage),
            }
            raw_manifest = sources.json_bytes(manifest)
            manifest_sha256 = sources.sha256(raw_manifest)
            (root / "preparation.json").write_bytes(raw_manifest)
            consumed.add(root / "preparation.json", raw_manifest)
            consumed.check()
            locked = publication.Consumption(clock)
            _verify(root, locked, locked=True)
            consumed.check()
            (root / LOCK).unlink()
            # The locked inventory callback cannot be reused after intentional unlock.
            closing = publication.Consumption(clock)
            verified = _verify(root, closing)
            consumed.check()
        # Handler restoration is part of the owned preparation transaction.
        consumed.check()
        closing.check()
        call = _call_record(root, manifest_sha256, call_started, call_wall, call_usage)
        raw_call = sources.json_bytes(call)
        _call_path(root).write_bytes(raw_call)
        consumed.add(_call_path(root), raw_call)
        _verify_call(root, consumed)
        closing.check()
        return verified.manifest
    except BaseException as error:
        if owned:
            try:
                (root / LOCK).write_text("Prospective input release revoked.\n")
            finally:
                _call_path(root).write_bytes(
                    sources.json_bytes(
                        _call_record(
                            root,
                            manifest_sha256,
                            call_started,
                            call_wall,
                            call_usage,
                            error,
                        )
                    )
                )
        raise
