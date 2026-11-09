"""Generate fixed confirmation inputs; no search or fitting."""

import hashlib, json, re, subprocess
from pathlib import Path
import mpmath as mp
import numpy as np
from ringdown_sr.signals import ringdown_signal
from ringdown_sr.global_restarts import grid
from ringdown_sr.noiseless_control import fingerprint

root = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
signals = [
    ("anchor", 1.0, 250.0, 0.008, 0.0),
    ("variant_low", 0.5, 210.0, 0.010, -0.5),
    ("variant_high", 0.8, 320.0, 0.006, 0.4),
]
old = json.loads((root / "data/transfer_check_inputs.json").read_bytes())["cases"]
truths = [
    dict(amplitude=a, frequency_hz=f, decay_time_s=tau, phase_rad=phase)
    for _, a, f, tau, phase in signals
]
assert all(truth not in [c["truth"] for c in old] for truth in truths[1:])
tracked = subprocess.check_output(
    [
        "git",
        "grep",
        "-h",
        "-I",
        "-E",
        "seed|Seed",
        "294f4ab79ee2e9588f9e5021b996bad726187d41",
        "--",
        "data",
        "docs",
        "src",
        "scripts",
        "tests",
    ],
    text=True,
)
used = {int(n) for n in re.findall(r"\b\d+\b", tracked)}
rng = np.random.Generator(np.random.PCG64(2026110901))
seeds = []
while len(seeds) < 120:
    n = int(rng.integers(1, 2**31))
    if n not in used and n not in seeds:
        seeds.append(n)
with np.load(root / "data/transfer_check_inputs.npz", allow_pickle=False) as prior:
    times = prior["time_s"]
    inner = prior["diagnostic_time_s"]
    anchor = prior["observed"][0]
    anchor_diag = prior["diagnostic_truth"][0]
grid_times = grid()["time_s"]
arrays = {"time_s": times, "diagnostic_time_s": inner, "irregular_time_s": grid_times}
config = {
    "format": "ringdown-sr-restart-confirmation-protocol-1",
    "blocks_per_signal": 10,
    "members": 4,
    "long_iterations": 2000,
    "restart_iterations": 500,
    "worker_seconds": 1800,
    "signal_seconds": 108000,
    "verify_seconds": 7200,
    "series_verify_seconds": 21600,
    "minimum_joint_successes": 8,
    "seed_generator": {
        "bit_generator": "PCG64",
        "seed": 2026110901,
        "draw": "integers(1, 2**31); reject duplicates and numeric values on seed-related tracked lines",
        "exclusion_commit": "294f4ab79ee2e9588f9e5021b996bad726187d41",
    },
    "grid_seed": 2026110601,
    "grid_points": 1024,
    "grid_attempts": 100,
    "signals": [],
}
mp.mp.dps = 100
largest = mp.mpf(0)
checks = 0
for i, ((name, *_), truth) in enumerate(zip(signals, truths, strict=True)):
    values = {
        k: ringdown_signal(t, **truth)
        for k, t in [
            ("observed", times),
            ("diagnostic_truth", inner),
            ("irregular_truth", grid_times),
        ]
    }
    if i == 0:
        assert np.array_equal(values["observed"], anchor) and np.array_equal(
            values["diagnostic_truth"], anchor_diag
        )
        values["observed"] = anchor
        values["diagnostic_truth"] = anchor_diag
    for key, value in values.items():
        arrays[name + "_" + key] = value
    for key, t in [
        ("observed", times),
        ("diagnostic_truth", inner),
        ("irregular_truth", grid_times),
    ]:
        for x, y in zip(t, values[key], strict=True):
            a, f, tau, phase = [
                mp.mpf(truth[k])
                for k in ["amplitude", "frequency_hz", "decay_time_s", "phase_rad"]
            ]
            ref = (
                a
                * mp.exp(-mp.mpf(float(x)) / tau)
                * mp.cos(2 * mp.pi * f * mp.mpf(float(x)) + phase)
            )
            largest = max(largest, abs(mp.mpf(float(y)) - ref) / a)
            checks += 1
    case = {
        "name": name,
        "truth": truth,
        "seeds": [seeds[i * 40 + j * 4 : i * 40 + j * 4 + 4] for j in range(10)],
        "arrays": {
            key: fingerprint(value)
            for key, value in {
                "time_s": times,
                "observed": values["observed"],
                "diagnostic_time_s": inner,
                "diagnostic_truth": values["diagnostic_truth"],
            }.items()
        },
        "grid": {
            key: fingerprint(value)
            for key, value in {
                "time_s": grid_times,
                "truth": values["irregular_truth"],
            }.items()
        },
    }
    config["signals"].append(case)
assert largest < mp.mpf("1e-13")
p = root / "data/restart_confirmation_inputs.npz"
np.savez(p, **arrays)
config["inputs_sha256"] = sha(p.read_bytes())
config["generation"] = {
    "numpy": np.__version__,
    "source": "src/ringdown_sr/signals.py",
    "source_sha256": sha((root / "src/ringdown_sr/signals.py").read_bytes()),
    "recipe": "reuse transfer training/diagnostic times; ringdown_signal for each fixed truth; reuse existing stratified irregular times; preserve anchor bits",
    "independent_check": {
        "method": "mpmath 100 decimal places, exact Binary64 times/parameters, mathematical pi",
        "values_checked": checks,
        "max_absolute_error_over_amplitude": float(largest),
        "bound": 1e-13,
    },
}
(root / "data/restart_confirmation_protocol.json").write_text(
    json.dumps(config, indent=2) + "\n"
)
print(
    "Frozen input sha256:",
    config["inputs_sha256"],
    "values:",
    checks,
    "maximum normalized error:",
    float(largest),
)
for case in config["signals"]:
    print(case["name"], case["truth"])
    print(case["seeds"])
