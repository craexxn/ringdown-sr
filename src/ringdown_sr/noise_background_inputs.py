"""Bind nested background-study inputs before any fit or symbolic search."""

import copy
import io
import signal
import time
import zipfile
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search
from . import noise_pilot_inputs as pilot
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
FORMAT = "ringdown-sr-noise-background-inputs-1"
CALL_FORMAT = "ringdown-sr-noise-background-input-call-1"
PLAN_PATH = "docs/noise_background_plan.md"
PLAN_COMMIT = "0c4b52868d8cc9809f38db02fe066ab540bcfeb3"
PLAN_SHA256 = "d3bb289cf4a2ac75a31f88c34721ca72da348c5af6d9d6a3917d4a6cc90f52f7"
SEED_BASE_COMMIT = "d1140178b2996c2bbf0bfa7e7ee98ced39dc856a"
GRID_SEED = 2026111610
LOCK = "INPUTS_LOCKED"
PREPARE_SECONDS = 2400
TRAINING_SIZES = (64, 256, 1024)
ESTIMATED_ARMS = tuple(f"estimated_{size}" for size in TRAINING_SIZES)
ARMS = ("ordinary", "known_covariance", *ESTIMATED_ARMS)
COMMON_KEYS = pilot.COMMON_KEYS
CASE_KEYS = {
    "noise",
    "observed",
    "covariance_true",
    "background_train",
    "background_validation",
    "background_check",
    *(
        f"covariance_{kind}_{size}"
        for kind in ("raw", "estimated")
        for size in TRAINING_SIZES
    ),
}
SIGNAL = dict(pilot.SIGNAL)
SIGMA = pilot.SIGMA
ALPHAS = pilot.ALPHAS
PreparedCase = pilot.PreparedCase
PreparedInputs = pilot.PreparedInputs
# These pure numerical/file helpers do not choose cases or use pilot formats.
_freeze = pilot._freeze
_fingerprints = pilot._fingerprints
_truth_reference = pilot._truth_reference
_read = pilot._read
_inventory = pilot._inventory
_cpu_usage = pilot._cpu_usage
_timing = pilot._timing
_verify_timing = pilot._verify_timing
_call_path = pilot._call_path

# Table order: AR(1) 01--20, then white 01--06; execution order is separate.
SEED_ROWS = (
    (646793876, 950461961, 396503743, 667450480, 414882043, 1186887900),
    (966005564, 2131299745, 224595958, 143460462, 583542165, 1062557763),
    (1972632683, 596718766, 1464369716, 1317917552, 1865880593, 624569914),
    (1650338219, 1552640662, 1008562290, 1905374137, 1149751997, 730539992),
    (413899298, 514055703, 1199221718, 389793444, 1483889227, 932926354),
    (1096683654, 1873929890, 464176975, 1586673715, 514597075, 2099248160),
    (653624123, 19673332, 1940945950, 1854345846, 569272474, 2027841777),
    (691266039, 756971811, 484384071, 1208482622, 2112118114, 659058988),
    (741373155, 2074180037, 71327655, 1172723461, 873508989, 1967894403),
    (1152667351, 362856872, 2008397264, 1974146732, 702735018, 1536548225),
    (85725611, 634179035, 200012446, 1038893210, 1549005214, 1096150590),
    (1451052659, 694866974, 1761466409, 166853572, 1556594400, 351696746),
    (251011455, 1867190795, 432510272, 1094408579, 2144670917, 790763179),
    (1109200832, 294890751, 8825503, 1706784002, 460915138, 40986374),
    (790432377, 1762994460, 1576026321, 229935957, 1405010561, 1648770210),
    (379242070, 207107888, 1594960252, 1523618046, 168417674, 20606404),
    (1055920531, 1901945751, 1301489750, 1261565030, 579531758, 1822901715),
    (2133118313, 1800753884, 1461571083, 1488595906, 688856225, 1927678864),
    (2102872469, 149230512, 1217296411, 90968200, 1602463611, 1741087819),
    (1600506978, 1943687657, 2102622658, 1357013345, 100106180, 1931697111),
    (188052562, 1431168838, 1891587003, 1697294631, 1803237116, 1060684896),
    (1501851379, 1863999801, 2011719561, 1211536402, 1724950367, 898939138),
    (1740183739, 1241269774, 2131104941, 1544013876, 1327216417, 1790832426),
    (607614599, 546057503, 1912681404, 805678233, 91075310, 950885165),
    (1507809470, 776290915, 1646235952, 81491730, 410527150, 495425711),
    (1849396610, 142870846, 1164831031, 1406544, 727495337, 695090960),
)


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
        "training_sizes": list(TRAINING_SIZES),
        "background": {
            "n_train": 1024,
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
    """Return the fixed scientific inventory or the separate five-worker check."""
    if type(technical) is not bool:
        raise TypeError("technical must be a boolean.")
    if technical:
        return (_spec(0, "ar1", (2026111611, 2026111612, 2026111613), technical=True),)
    result = []
    for block in range(1, 21):
        result.append(_spec(block, "ar1", SEED_ROWS[block - 1], technical=False))
        if block <= 6:
            result.append(
                _spec(block, "white", SEED_ROWS[20 + block - 1], technical=False)
            )
    return tuple(result)


def _initial_states():
    """Check actual PCG64 states across every scientific and technical data role."""
    seen = {sources.json_bytes(np.random.PCG64(GRID_SEED).state)}
    for spec in (*case_specs(), *case_specs(technical=True)):
        for generator in pilot_generators(
            spec["noise_seed"], spec["background_seed"]
        ).values():
            state = sources.json_bytes(generator.bit_generator.state)
            if state in seen:
                raise ValueError("Background-study random initial states collide.")
            seen.add(state)
    return {
        "checked_states": len(seen),
        "scope": "all_scientific_and_technical_data_roles_plus_irregular_grid",
        "collisions": 0,
    }


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
        "random_state_check": _initial_states(),
    }
    return arrays, record


def _arm_view(common, arrays, arm):
    if arm not in ARMS:
        raise ValueError("Unknown background-study weighting arm.")
    result = {**common, **arrays}
    if arm in ESTIMATED_ARMS:
        size = int(arm.removeprefix("estimated_"))
        if "background_train" in arrays:
            result["background_train"] = arrays["background_train"][:size]
        for kind in ("raw", "estimated"):
            key = f"covariance_{kind}_{size}"
            if key in arrays:
                result[f"covariance_{kind}"] = arrays[key]
    return result


def arm_arrays(prepared, case, arm):
    """Expose the same observations with the assigned immutable covariance view."""
    return _arm_view(prepared.common, case.arrays, arm)


def covariance_diagnostics(arrays, arm_status, status):
    """Apply the unchanged held-out matrix diagnostics to each frozen estimate."""
    result = {}
    for arm in ESTIMATED_ARMS:
        state = (
            "data_failed"
            if status in {"data_failed", "background_failed"}
            else "covariance_failed"
            if arm_status[arm] == "not_run"
            else "ready"
        )
        result[arm] = pilot.covariance_diagnostics(_arm_view({}, arrays, arm), state)
        if status == "background_failed":
            for diagnostics in (
                result[arm]["background_check"],
                result[arm]["condition_number"],
            ):
                for diagnostic in diagnostics.values():
                    diagnostic["reason"] = "background_preparation_failed"
            result[arm]["relative_frobenius_error"]["reason"] = (
                "background_preparation_failed"
            )
    return result


def derive_case(spec, common):
    """Regenerate one measured window and a nested pool without any fit or search."""
    if not any(
        sources.json_bytes(spec) == sources.json_bytes(item)
        for item in (*case_specs(), *case_specs(technical=True))
    ):
        raise ValueError("Case differs from the frozen background-study protocol.")
    if set(common) != COMMON_KEYS:
        raise ValueError("Incomplete common background-study reference roles.")
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
        "covariance_estimation": dict.fromkeys(ESTIMATED_ARMS),
        "arm_status": dict.fromkeys(ARMS, "ready"),
        "error": None,
        "background_prefixes": {},
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
    except (FloatingPointError, OverflowError) as error:
        record.update(
            status="data_failed",
            error={"type": type(error).__name__, "message": str(error)},
        )
        record["arm_status"] = dict.fromkeys(ARMS, "not_run")
    if record["status"] == "ready":
        record["stage"] = "background_generation"
        try:
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
                status="background_failed",
                error={"type": type(error).__name__, "message": str(error)},
            )
            record["arm_status"].update(dict.fromkeys(ESTIMATED_ARMS, "not_run"))
        finally:
            arrays.update(
                {
                    "background_" + name: _freeze(value)
                    for name, value in background.items()
                }
            )
    if record["status"] == "ready":
        record["stage"] = "covariance_estimation"
        for size, arm in zip(TRAINING_SIZES, ESTIMATED_ARMS, strict=True):
            train = arrays["background_train"][:size]
            record["background_prefixes"][arm] = {
                "pool": "background_train",
                "start": 0,
                "stop": size,
                "fingerprint": sources.fingerprint(train),
                "validation_fingerprint": sources.fingerprint(
                    arrays["background_validation"]
                ),
                "check_fingerprint": sources.fingerprint(arrays["background_check"]),
            }
            try:
                estimate = estimate_covariance(
                    train,
                    arrays["background_validation"],
                    **spec["covariance_estimation"],
                )
            except CovarianceEstimationError as error:
                entry = pilot._estimate_record(error=error)
                entry["n_train"] = size
                entry["error"] = {"type": type(error).__name__, "message": str(error)}
                record["covariance_estimation"][arm] = entry
                record["status"] = "covariance_failed"
                record["arm_status"][arm] = "not_run"
                if error.raw_covariance is not None:
                    arrays[f"covariance_raw_{size}"] = _freeze(error.raw_covariance)
            else:
                arrays[f"covariance_raw_{size}"] = _freeze(estimate.raw_covariance)
                arrays[f"covariance_estimated_{size}"] = _freeze(estimate.covariance)
                record["covariance_estimation"][arm] = pilot._estimate_record(
                    estimate=estimate
                )
        record["stage"] = "complete"
    arrays = {name: _freeze(value) for name, value in arrays.items()}
    record["input_fingerprints"] = _fingerprints(arrays)
    record["covariance_diagnostics"] = covariance_diagnostics(
        arrays, record["arm_status"], record["status"]
    )
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
        raise ValueError(
            "Frozen noise-background plan differs from its separate commit."
        )
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
    if record["wall_seconds"] >= PREPARE_SECONDS:
        raise ValueError("Input preparation exceeded its frozen deadline.")
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
        manifest["protocol"],
        _protocol(consumed),
        "Changed noise-background plan binding.",
    )
    sources._same(
        manifest["software"],
        _freeze_sources(consumed),
        "Changed input-preparation software.",
    )
    if (
        manifest["case_order"] != ids
        or type(manifest["planned_search_calls"]) is not int
        or manifest["planned_search_calls"] != (5 if manifest["technical"] else 520)
        or type(manifest["planned_algorithm_outputs"]) is not int
        or manifest["planned_algorithm_outputs"]
        != (5 if manifest["technical"] else 130)
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
    _initial_states()
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
                "planned_search_calls": 5 if technical else 520,
                "planned_algorithm_outputs": 5 if technical else 130,
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
