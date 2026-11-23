"""Bounded native and fresh-process controls for the separate scaling pilot."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from ringdown_sr import white_scaling as study
from ringdown_sr import white_scaling_fixed as fixed
from ringdown_sr import white_scaling_worker as scaling
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json

SEED = 73
SIGMA = 0.25
CELLS = (
    ("ordinary", "ordinary"),
    ("scaled", "scaled"),
    ("covariance", "covariance"),
    ("ordinary-repeat", "ordinary"),
)


def verify(output):
    """Read every arm again; only the predetermined same-arm repeat must match."""
    output = Path(output)
    times = np.arange(8, dtype=np.float64) / 16
    observed = 1.0 + times
    reports = {}
    for name, arm in CELLS:
        report = scaling.verify_member(output / name)
        request = report["request"]
        if (
            request["arm"] != arm
            or request["technical"] is not True
            or request["sigma_hex"] != SIGMA.hex()
            or scaling.checked_request(request).seed != SEED
            or scaling.checked_request(request).niterations != 2
        ):
            raise ValueError("Changed technical scaling cell.")
        _, arrays, _ = scaling.verify_prepared(output / name)
        if not np.array_equal(arrays["time_s"], times) or not np.array_equal(
            arrays["observed"], observed
        ):
            raise ValueError("Changed technical scaling data.")
        expected_zero_loss = float(np.mean(observed**2))
        if arm != "ordinary":
            expected_zero_loss /= SIGMA**2
        np.testing.assert_allclose(
            report["zero_expression_loss"], expected_zero_loss, rtol=1e-14, atol=0
        )
        reports[name] = report
    for field in (
        "candidates",
        "selected_index",
        "baseline_loss",
        "cost_normalization",
    ):
        if _json_bytes(reports["ordinary"][field]) != _json_bytes(
            reports["ordinary-repeat"][field]
        ):
            raise ValueError("Repeated ordinary worker changed its original front.")
    if (
        reports["ordinary"]["costs"]["callback_calls_during_fit"]
        != reports["ordinary-repeat"]["costs"]["callback_calls_during_fit"]
    ):
        raise ValueError("Repeated ordinary worker changed its fit callback count.")
    fixed.verify_fixed(output / "fixed-ordinary")
    fixed_request, _, _ = scaling.verify_prepared(output / "fixed-ordinary")
    if (
        fixed_request["technical"] is not True
        or fixed_request["arm"] != "ordinary"
        or fixed_request["sigma_hex"] != SIGMA.hex()
        or scaling.checked_request(fixed_request).seed != SEED
    ):
        raise ValueError("Changed fixed-structure technical control.")
    print(
        "White-scaling controls passed: O/S/K/O, native objective arithmetic, "
        "unaltered options, independent replay, fixed-worker replay and repeated original front."
    )
    return reports


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(scaling.native.JULIA_THREADS)
    environment.update(
        {
            name: "1"
            for name in (
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    environment["OPENBLAS_CORETYPE"] = "Haswell"
    started = time.monotonic()
    with (output / "native.log").open("xb") as log:
        subprocess.run(
            [
                sys.executable,
                str(scaling.ROOT / "scripts/run_python.py"),
                str(scaling.ROOT / "scripts/check_white_scaling_native.py"),
            ],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=1800,
        )
    times = np.arange(8, dtype=np.float64) / 16
    for name, arm in CELLS:
        scaling.prepare_member(
            output / name,
            times,
            1.0 + times,
            arm=arm,
            sigma=SIGMA,
            seed=SEED,
            technical=True,
            niterations=2,
        )
        scaling.run_member(output / name, deadline=started + 7200)
    fixed_directory = output / "fixed-ordinary"
    scaling.prepare_member(
        fixed_directory,
        times,
        1.0 + times,
        arm="ordinary",
        sigma=SIGMA,
        seed=SEED,
        technical=True,
        niterations=2,
    )
    _write_json(
        fixed_directory / "fixed_request.json",
        {
            "format": fixed.FORMAT,
            "starts": [
                {"name": f"start-{index + 1}", "parameters": values}
                for index, values in enumerate(study.starts(1.0 + times))
            ],
        },
    )
    _write_json(
        fixed_directory / "fixed_prepared.json",
        {
            "request_sha256": _sha256(
                (fixed_directory / "fixed_request.json").read_bytes()
            ),
            "source_sha256": scaling.source_hashes(),
            "prepared_sha256": _sha256(
                (fixed_directory / "prepared.json").read_bytes()
            ),
        },
    )
    study._fixed(fixed_directory, started + 7200)
    verify(output)
    _write_json(
        output / "technical-summary.json",
        {
            "format": "ringdown-sr-white-scaling-technical-1",
            "status": "passed",
            "source_sha256": scaling.source_hashes(),
            "wall_seconds": time.monotonic() - started,
            "cells": [name for name, _ in CELLS] + ["fixed-ordinary"],
            "scope": "technical_linear_fixture_only_no_scientific_windows",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if (args.output is None) == (args.verify is None):
        parser.error("Choose exactly one of --output and --verify.")
    if args.verify is not None:
        verify(args.verify)
    else:
        run(args.output)
