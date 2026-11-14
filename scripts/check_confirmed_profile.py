"""Bounded technical checks of the opt-in profile and its weighted native route."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from ringdown_sr import confirmed_profile as profile
from ringdown_sr.confirmed_search import run_confirmed_package, verify_confirmed_package
from ringdown_sr.pilot import _write_json

SEEDS = (20261401, 20261402, 20261403, 20261404)
CHECK_FORMAT = "ringdown-sr-confirmed-profile-technical-1"


def fixture(covariance="full"):
    arrays = {"time_s": np.array([0.0, 1.0]), "observed": np.array([1.0, 0.0])}
    matrix = np.array([[2.5, 1.5], [1.5, 4.5]])
    if covariance != "ordinary":
        arrays["covariance"] = (
            np.diag(np.diag(matrix)) if covariance == "diagonal" else matrix
        )
    return arrays


def verify_fixture(record, covariance):
    expected = {
        key: profile.sources.fingerprint(value)
        for key, value in fixture(covariance).items()
    }
    profile.sources._same(
        record["input_fingerprints"], expected, "Changed technical weighting fixture."
    )


def analytic_worker(output):
    sources = profile.source_hashes()
    import pysr  # noqa: F401
    from juliacall import Main as jl

    jl.include(str(profile.ROOT / "julia/test/confirmed_profile.jl"))
    native = jl.ConfirmedProfileChecks.run(str(profile.ROOT))
    records = [
        {
            "kind": str(row.kind),
            "weighting": str(row.weighting),
            "losses": list(row.losses),
            "parameters": list(row.parameters),
            "calls": int(row.calls),
        }
        for row in native
    ]
    if profile.source_hashes() != sources:
        raise ValueError("Analytical profile sources changed during consumption.")
    _write_json(
        output,
        {
            "format": CHECK_FORMAT,
            "profile": profile.PROFILE,
            "sources": sources,
            "status": "passed",
            "cases": records,
        },
    )


def verify_analytic(path):
    report = profile.read(path.parent, path.name)
    records = report.get("cases", [])
    expected = {
        ("ranking", "full"): ([1 / 3, 9 / 16], []),
        ("ranking", "diagonal"): ([1 / 2, 9 / 32], []),
        ("ranking", "ordinary"): ([1, 9 / 16], []),
        ("constant", "full"): ([1 / 5], [7 / 5]),
        ("constant", "diagonal"): ([1 / 7], [11 / 7]),
        ("constant", "ordinary"): ([1], [2]),
        ("linear", "full"): ([4 / 21], [0, 1 / 7]),
        ("linear", "diagonal"): ([4 / 33], [4 / 11, -1 / 11]),
        ("linear", "ordinary"): ([2 / 9], [1 / 3, 0]),
    }
    if (
        set(report) != {"format", "profile", "sources", "status", "cases"}
        or report.get("format") != CHECK_FORMAT
        or report.get("profile") != profile.PROFILE
        or report.get("sources") != profile.source_hashes()
        or report.get("status") != "passed"
        or len(records) != 9
    ):
        raise ValueError("Incomplete analytical native profile controls.")
    seen = set()
    for record in records:
        key = record["kind"], record["weighting"]
        if (
            set(record) != {"kind", "weighting", "losses", "parameters", "calls"}
            or key not in expected
            or key in seen
            or type(record["calls"]) is not int
            or record["calls"] <= 0
            or any(
                type(value) not in (int, float)
                for field in ("losses", "parameters")
                for value in record[field]
            )
        ):
            raise ValueError("Invalid analytical control inventory.")
        seen.add(key)
        losses, parameters = expected[key]
        np.testing.assert_allclose(
            record["losses"],
            losses,
            atol=1e-14 if key[0] == "ranking" else 1e-11,
            rtol=0,
        )
        np.testing.assert_allclose(record["parameters"], parameters, atol=1e-6, rtol=0)
    return report


def verify(output):
    output = Path(output)
    verify_analytic(output / "analytic.json")
    package = verify_confirmed_package(output / "full")
    if package["technical"] is not True or package["seeds"] != list(SEEDS):
        raise ValueError("Native profile checker requires explicitly technical scope.")
    verify_fixture(package, "full")
    for name, expected in (("diagonal", 0.2), ("ordinary", 0.5)):
        record = profile.verify_member(output / name)
        if record["status"] != "completed" or record["technical"] is not True:
            raise ValueError("Incomplete technical weighting worker.")
        if record["seed"] != (20261405 if name == "diagonal" else 20261406):
            raise ValueError("Changed technical weighting seed.")
        verify_fixture(record, name)
        result = profile.read(output / name, "result.json")
        np.testing.assert_allclose(
            result["zero_expression_loss"], expected, rtol=1e-14, atol=0
        )
    for number in range(1, 5):
        directory = output / "full" / f"member-{number:02d}"
        result = profile.read(directory, "result.json")
        np.testing.assert_allclose(
            result["zero_expression_loss"], 0.25, rtol=1e-14, atol=0
        )
    print(
        "Confirmed profile passed: six tiny searches, full/diagonal/MSE ranking and constant controls, read-only replay."
    )


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(profile.native.JULIA_THREADS)
    environment.update(
        {
            key: "1"
            for key in (
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    environment["OPENBLAS_CORETYPE"] = "Haswell"
    subprocess.run(
        [
            sys.executable,
            str(profile.ROOT / "scripts/run_python.py"),
            str(Path(__file__).resolve()),
            "--analytic-worker",
            str(output / "analytic.json"),
        ],
        check=True,
        env=environment,
        timeout=600,
    )
    arrays = fixture()
    times, observed, covariance = (
        arrays["time_s"],
        arrays["observed"],
        arrays["covariance"],
    )
    run_confirmed_package(
        times,
        observed,
        covariance=covariance,
        output=output / "full",
        seeds=SEEDS,
        technical=True,
    )
    for name, matrix in (
        ("diagonal", np.diag(np.diag(covariance))),
        ("ordinary", None),
    ):
        profile.prepare_member(
            output / name,
            times,
            observed,
            covariance=matrix,
            seed=20261405 if name == "diagonal" else 20261406,
            technical=True,
        )
        profile.run_member(output / name, deadline=time.monotonic() + 600)
    verify(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--verify", type=Path)
    mode.add_argument("--analytic-worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.analytic_worker:
        analytic_worker(args.analytic_worker)
    elif args.verify:
        verify(args.verify)
    else:
        run(args.output)
