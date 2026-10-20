"""Generate independent noise windows using fixed, versioned RNG roles."""

import numpy as np

from ringdown_sr.config import BackgroundConfig, NoiseConfig, SamplingConfig
from ringdown_sr.noise import gaussian_ar1_noise, gaussian_white_noise

ROLE_IDS = {"train": 0, "validation": 1, "check": 2}


def pilot_generators(
    signal_seed: int, background_seed: int
) -> dict[str, np.random.Generator]:
    """Create the four actual pilot streams and reject equal initial states.

    Direct integer seeding can encode the same SeedSequence input as a
    background spawn key. Compare full PCG64 states before drawing anything;
    distinct initial states alone are not a proof of statistical independence.
    """
    generators = {"signal": np.random.Generator(np.random.PCG64(signal_seed))}
    generators.update(
        {
            role: np.random.Generator(
                np.random.PCG64(
                    np.random.SeedSequence(
                        background_seed, spawn_key=(role_id,), pool_size=4
                    )
                )
            )
            for role, role_id in ROLE_IDS.items()
        }
    )
    states = {}
    for role, rng in generators.items():
        state = rng.bit_generator.state
        for previous_role, previous_state in states.items():
            if state == previous_state:
                raise ValueError(
                    f"Initial PCG64 states collide for {previous_role} and {role}; "
                    "choose different noise.seed/background.seed."
                )
        states[role] = state
    return generators


def noise_draw_record(noise: NoiseConfig, n_samples: int, n_calls: int) -> dict:
    """Describe actual per-window calls, with no implied completed draws."""
    ar1 = noise.kind == "gaussian_ar1"
    call = {
        "method": "standard_normal" if ar1 else "normal",
        "size": n_samples,
        "expected_calls": n_calls,
        "completed_calls": 0,
        "output_dtype": "float64",
    }
    if ar1:
        call["dtype"] = "float64"
    else:
        call.update(loc=0.0, scale=noise.standard_deviation)
    return {
        "bit_generator": "PCG64",
        "state_before": None,
        "state_after": None,
        "calls": call,
        "transform": (
            {
                "kind": "stationary_gaussian_ar1_v1",
                "marginal_standard_deviation": noise.standard_deviation,
                "correlation": noise.correlation,
                "initialization": "independent_stationary_start_per_window",
            }
            if ar1
            else {"kind": "identity"}
        ),
    }


def draw_noise_window(noise: NoiseConfig, n_samples: int, rng: np.random.Generator):
    """Use the same configured distribution for background and signal noise."""
    if noise.kind == "gaussian_ar1":
        return gaussian_ar1_noise(
            n_samples,
            standard_deviation=noise.standard_deviation,
            correlation=noise.correlation,
            rng=rng,
        )
    return gaussian_white_noise(
        n_samples, standard_deviation=noise.standard_deviation, rng=rng
    )


def background_random_record(
    noise: NoiseConfig, sampling: SamplingConfig, background: BackgroundConfig
) -> dict:
    """Reserve fixed SeedSequence role descriptions without drawing samples."""
    return {
        "scheme": background.stream_scheme,
        "root_seed": background.seed,
        "sampling": {
            "n_samples": sampling.n_samples,
            "sample_rate_hz": sampling.sample_rate_hz,
        },
        "distribution": {
            "kind": noise.kind,
            "known_mean": 0.0,
            "standard_deviation": noise.standard_deviation,
            **(
                {"correlation": noise.correlation}
                if noise.kind == "gaussian_ar1"
                else {}
            ),
        },
        "roles": {
            role: {
                "role_id": role_id,
                "seed_sequence": {
                    "entropy": background.seed,
                    "spawn_key": [role_id],
                    "pool_size": 4,
                },
                **noise_draw_record(
                    noise, sampling.n_samples, getattr(background, "n_" + role)
                ),
            }
            for role, role_id in ROLE_IDS.items()
        },
    }


def generate_background(
    noise: NoiseConfig,
    sampling: SamplingConfig,
    background: BackgroundConfig,
    *,
    windows: dict,
    random: dict,
    generators: dict[str, np.random.Generator],
) -> None:
    """Fill independent role matrices, preserving completed rows on failure.

    Each AR(1) call starts a new stationary window. No windows are cut from
    one continuous trajectory. The signal RNG is never accessed. Fixed
    spawn keys prevent role sizes or execution order from shifting peers.
    The caller supplies the already checked, unadvanced pilot generators.
    """
    for role in ROLE_IDS:
        record = random["roles"][role]
        rng = generators[role]
        record["state_before"] = rng.bit_generator.state
        completed = []
        try:
            for _ in range(getattr(background, "n_" + role)):
                completed.append(draw_noise_window(noise, sampling.n_samples, rng))
                record["calls"]["completed_calls"] += 1
        finally:
            record["state_after"] = rng.bit_generator.state
            if completed:
                windows[role] = np.stack(completed)
