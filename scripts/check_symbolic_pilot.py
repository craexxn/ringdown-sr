"""Run/audit paired schema-3 controls with independent direct-matrix diagnostics."""

import argparse
import hashlib
import json
import tempfile
from contextlib import nullcontext
from fractions import Fraction
from pathlib import Path

import numpy as np

from ringdown_sr.pilot import run_pilot
from ringdown_sr.symbolic import evaluate_tree

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    def reject(value):
        raise ValueError(f"Nonstandard JSON number: {value}")

    return json.loads(path.read_text(), parse_constant=reject)


def verify(directory: Path):
    """Audit artifacts without rerunning searches or using signal truth to select."""
    directory = directory.resolve()
    result, metadata = (
        read(directory / "result.json"),
        read(directory / "metadata.json"),
    )
    assert result["schema_version"] == metadata["schema_version"] == 3
    assert result["status"] == metadata["status"] == "success"
    config = read(directory / "resolved_config.json")
    for name, expected in metadata["artifact_sha256"].items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    reference = read(directory / result["reference"]["result_file"])
    assert reference["status"] == "success" and reference["schema_version"] == 2
    with np.load(
        directory / result["shared_inputs_file"], allow_pickle=False
    ) as inputs:
        arrays = {name: inputs[name] for name in inputs.files}
    time, observed = arrays["time_s"], arrays["observed"]
    n = len(time)
    assert n == config["sampling"]["n_samples"]
    np.testing.assert_array_equal(
        time, np.arange(n) / config["sampling"]["sample_rate_hz"]
    )
    np.testing.assert_array_equal(observed, arrays["signal"] + arrays["noise"])
    signal = config["signal"]
    analytic = (
        signal["amplitude"]
        * np.exp(-time / signal["decay_time_s"])
        * np.cos(2 * np.pi * signal["frequency_hz"] * time + signal["phase_rad"])
    )
    np.testing.assert_allclose(arrays["signal"], analytic, rtol=1e-13, atol=1e-15)
    train = np.loadtxt(
        directory / "reference/background_train.csv", delimiter=",", ndmin=2
    )
    raw = train.T @ train / len(train)
    alpha = result["covariance_estimation"]["alpha_selected"]
    estimated = (1 - alpha) * raw + alpha * np.trace(raw) / n * np.eye(n)
    # For a PSD covariance, its largest absolute entry is the largest variance.
    # Use only the independent reference, with no floor in amplitude-squared units.
    covariance_scale = float(np.max(np.abs(estimated)))
    assert np.isfinite(covariance_scale) and covariance_scale > 0, (
        "The reconstructed covariance needs a finite positive comparison scale."
    )
    np.testing.assert_allclose(
        arrays["covariance_estimated"] / covariance_scale,
        estimated / covariance_scale,
        rtol=1e-12,
        atol=1e-15,
        err_msg="Estimated covariance differs from independent shrinkage reconstruction.",
    )
    check = np.loadtxt(
        directory / "reference/background_check.csv", delimiter=",", ndmin=2
    )
    for kind in ("true", "estimated"):
        matrix = arrays["covariance_" + kind]
        sign, logdet = np.linalg.slogdet(matrix)
        assert sign == 1
        score = logdet + np.sum(check * np.linalg.solve(matrix, check.T).T) / len(check)
        np.testing.assert_allclose(
            score,
            reference["diagnostics"]["background_check"][kind]["score"],
            rtol=1e-11,
            atol=1e-11,
        )
    for name, record in result["symbolic_arms"].items():
        assert record["status"] == "success"
        arm_dir = (directory / record["result_file"]).parent
        arm = read(arm_dir / "result.json")
        with np.load(arm_dir / "inputs.npz", allow_pickle=False) as inputs:
            expected = {"time_s", "observed"} | (
                set() if name == "ordinary" else {"covariance"}
            )
            assert set(inputs.files) == expected
            np.testing.assert_array_equal(inputs["time_s"], time)
            np.testing.assert_array_equal(inputs["observed"], observed)
            used = (
                np.eye(n)
                if name == "ordinary"
                else arrays[
                    "covariance_true"
                    if name == "known_covariance"
                    else "covariance_estimated"
                ]
            )
            if name != "ordinary":
                np.testing.assert_array_equal(inputs["covariance"], used)
        assert read(arm_dir / "request.json")["budget"] == config["symbolic_search"]
        selected = min(
            range(len(arm["candidates"])),
            key=lambda i: (
                arm["candidates"][i]["loss"],
                arm["candidates"][i]["complexity"],
            ),
        )
        assert arm["selected_index"] == record["selected"]["index"] == selected
        for candidate in arm["candidates"]:
            prediction = np.asarray(candidate["prediction"])
            python_prediction = evaluate_tree(candidate["tree"], time)
            scale = max(
                float(np.max(np.abs(prediction))),
                float(np.max(np.abs(python_prediction))),
            )
            if scale:
                np.testing.assert_allclose(
                    python_prediction / scale,
                    prediction / scale,
                    rtol=1e-12,
                    atol=1e-14,
                )
            residual = observed - prediction
            np.testing.assert_array_equal(candidate["residual"], residual)
            loss = residual @ np.linalg.solve(used, residual) / n
            np.testing.assert_allclose(candidate["loss"], loss, rtol=1e-10, atol=0)
        candidate = arm["candidates"][selected]
        prediction = np.asarray(candidate["prediction"])
        residual = observed - prediction
        metrics = record["metrics"]
        sigma = config["noise"]["standard_deviation"]
        if config["noise"]["kind"] == "gaussian_ar1":
            rho = config["noise"]["correlation"]
            # Independent stationary AR(1) innovation formula, no covariance solve.
            q_true = (
                (residual[0] / sigma) ** 2
                + np.sum(
                    (
                        (residual[1:] - rho * residual[:-1])
                        / (sigma * np.sqrt(1 - rho * rho))
                    )
                    ** 2
                )
            ) / n
        else:
            q_true = np.mean((residual / sigma) ** 2)
        np.testing.assert_allclose(
            metrics["q_true_per_sample"], q_true, rtol=1e-10, atol=0
        )
        np.testing.assert_allclose(
            metrics["ordinary_mse"], np.mean(residual**2), rtol=1e-12, atol=0
        )
        np.testing.assert_allclose(
            metrics["mse_to_clean_signal"],
            np.mean((prediction - arrays["signal"]) ** 2),
            rtol=1e-12,
            atol=0,
        )
        expected_used = residual @ np.linalg.solve(used, residual) / n
        if name == "ordinary":
            assert metrics["q_used_per_sample"] is None
        else:
            np.testing.assert_allclose(
                metrics["q_used_per_sample"], expected_used, rtol=1e-10, atol=0
            )
        assert record["selected"]["parameter_interpretation"] == "not_attempted"
        initial = read(arm_dir / "metadata_initial.json")
        assert read(arm_dir / "metadata.json")["provenance"] == initial["provenance"]
        print(
            f"{directory.name}/{name}: {len(arm['candidates'])} candidates, Q_true/N={q_true:.12g}"
        )
    print(f"Schema-3 audit passed: {directory}; alpha={alpha:g}.")


def verify_assessment(source, output):
    """Independently check the new grades on the existing tiny native controls."""
    assert not (output / "ASSESSMENT_LOCKED").exists()
    report = read(output / "assessment_report.json")
    assert report["status"] == "completed"
    assert report["stage"] == 3
    assert report["structure_policy_timing"] == "before_first_fit"
    assert report["remainder_policy_timing"] == "before_first_fit"
    for name, digest in read(output / "assessment_checksums.json").items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    records = read(output / "assessment_records.json")
    assert len(records) == 3
    with np.load(source / "assessment_inputs.npz", allow_pickle=False) as arrays:
        for record in records:
            name = record["source_identity"]["arm"]
            front = read(source / "symbolic" / name / "result.json")
            index = front["selected_index"]
            assert index == record["source_identity"]["original_selected_index"]
            assert front["candidates"][index] == record["original_candidate"]
            proof = record["supplemental"]
            assert proof["structure_proof_format"] == "ringdown-sr-structure-proof-1"
            exact_endpoints = tuple(
                Fraction(int(e["numerator_hex"], 16), int(e["denominator_hex"], 16))
                for e in proof["domain"]["interval"]["endpoints"]
            )
            expected_endpoints = tuple(
                Fraction.from_float(float(t))
                for t in arrays["training_time_s"][[0, -1]]
            )
            assert exact_endpoints == expected_endpoints
            assert (
                proof["domain"]["interval"]
                == read(source / "assessment_contract.json")["structure_interval"]
            )
            for name in (
                "algebraic_identity",
                "domain",
                "original_family",
                "continuous_extension",
            ):
                assert proof[name]["status"] != "not_assessed"
            if proof["original_family"]["status"] == "proven_member":
                assert proof["domain"]["status"] == "defined_everywhere"
                assert (
                    proof["algebraic_identity"]["status"] == "proven_on_original_domain"
                )
            assert proof["new_parameter_match"]["status"] == "not_assessed"
            remainder = proof["remainder"]
            assert remainder["format"] == "ringdown-sr-remainder-proof-1"
            assert remainder["status"] in ("bound_proven", "unresolved")
            assert remainder["evaluation_model"] == "exact_real_original_tree"
            for grid in ("training", "diagnostic"):
                for field, source_key in (
                    ("time_s", grid + "_time_s"),
                    ("truth", grid + "_truth"),
                ):
                    vector = np.ascontiguousarray(arrays[source_key], dtype="<f8")
                    assert remainder["reference_binding"][grid][field] == {
                        "dtype": "<f8",
                        "shape": list(vector.shape),
                        "sha256": hashlib.sha256(vector.tobytes()).hexdigest(),
                    }
            values = []
            for grid in ("training", "diagnostic"):
                truth = arrays[grid + "_truth"]
                try:
                    prediction = evaluate_tree(
                        front["candidates"][index]["tree"], arrays[grid + "_time_s"]
                    )
                except ValueError:
                    assert record["curve_errors"][grid]["status"] != "available"
                    break
                difference = prediction - truth
                rms = float(np.linalg.norm(difference) / np.linalg.norm(truth))
                maximum = float(np.max(np.abs(difference)) / np.max(np.abs(truth)))
                saved = record["curve_errors"][grid]
                np.testing.assert_allclose(
                    [saved["relative_rms"], saved["relative_max"]],
                    [rms, maximum],
                    rtol=1e-12,
                    atol=0,
                )
                values.append((saved["relative_rms"], saved["relative_max"]))
            expected = None
            if len(values) == 2:
                expected = "D"
                for grade, rms, maximum in (
                    ("A", 0.001, 0.01),
                    ("B", 0.01, 0.02),
                    ("C", 0.05, 0.1),
                ):
                    if all(r <= rms and m <= maximum for r, m in values):
                        expected = grade
                        break
            assert record["supplemental"]["curve"]["grade"] == expected
    print(f"Prospective assessment audit passed: {output}; three original selections.")
    print("Stage-2 interval, proof statuses and original-selection bindings passed.")
    print(
        "Stage-3 remainder contract, separate components and reference bindings passed."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        type=Path,
        help="Audit an existing schema-3 result without running searches",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New root for both control cases; default is temporary",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use the unmodified example configurations and standard budgets",
    )
    args = parser.parse_args()
    if args.verify:
        if args.output or args.full:
            parser.error("--verify cannot be combined with --output or --full")
        verify(args.verify)
        return
    context = (
        nullcontext(args.output.resolve())
        if args.output
        else tempfile.TemporaryDirectory(prefix="ringdown-sr-schema3-")
    )
    with context as root:
        root = Path(root)
        if args.output:
            root.mkdir(parents=True, exist_ok=False)
        for kind in ("white", "ar1"):
            content = (ROOT / f"configs/pilot_sr_{kind}.toml").read_text()
            if not args.full:
                for old, new in (
                    ("n_samples = 128", "n_samples = 32"),
                    ("n_train = 64", "n_train = 16"),
                    ("n_validation = 128", "n_validation = 20"),
                    ("n_check = 256", "n_check = 24"),
                    ("niterations = 10", "niterations = 1"),
                    ("populations = 2", "populations = 1"),
                    ("population_size = 32", "population_size = 16"),
                    ("ncycles_per_iteration = 50", "ncycles_per_iteration = 2"),
                ):
                    content = content.replace(old, new)
            path = root / f"{kind}.toml"
            path.write_text(content)
            assessment = root / (kind + "-assessment")
            outcome = run_pilot(path, root / kind, assessment_output=assessment)
            if outcome.status != "success":
                print((outcome.output_directory / "result.json").read_text())
                for log in outcome.output_directory.rglob("worker.log"):
                    print(f"Worker log: {log}\n{log.read_text()}")
                raise SystemExit(f"Schema-3 control failed: {outcome.output_directory}")
            verify(outcome.output_directory)
            verify_assessment(outcome.output_directory, assessment)


if __name__ == "__main__":
    main()
