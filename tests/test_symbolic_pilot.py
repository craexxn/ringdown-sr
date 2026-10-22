"""Verify schema-3 data identity, selection, diagnostics and failure persistence."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import symbolic_pilot
from ringdown_sr.cli import main
from ringdown_sr.config import SymbolicPilotConfig, load_config, parse_config
from ringdown_sr.losses import CovarianceLoss, mean_squared_error
from ringdown_sr.pilot import _write_json, run_pilot
from ringdown_sr.symbolic import FORMAT, SearchRun, evaluate_tree, select_candidate

ROOT = Path(__file__).resolve().parents[1]


def small_config(kind="ar1"):
    return (
        (ROOT / f"configs/pilot_sr_{kind}.toml")
        .read_text()
        .replace("n_samples = 128", "n_samples = 32")
        .replace("n_train = 64", "n_train = 16")
        .replace("n_validation = 128", "n_validation = 20")
        .replace("n_check = 256", "n_check = 24")
        .replace("niterations = 10", "niterations = 1")
        .replace("populations = 2", "populations = 1")
        .replace("population_size = 32", "population_size = 16")
        .replace("ncycles_per_iteration = 50", "ncycles_per_iteration = 2")
    )


def read(path):
    return json.loads(path.read_text())


def constant(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


def candidate_tree():
    return {
        "kind": "operator",
        "arity": 2,
        "operator_index": 3,
        "operator": "*",
        "children": [
            constant(0.3),
            {
                "kind": "operator",
                "arity": 1,
                "operator_index": 1,
                "operator": "exp",
                "children": [
                    {
                        "kind": "operator",
                        "arity": 2,
                        "operator_index": 3,
                        "operator": "*",
                        "children": [constant(-3), {"kind": "variable", "index": 1}],
                    }
                ],
            },
        ],
    }


def write_worker(time, observed, *, covariance, output, budget):
    """Stub only the costly search; exercise artifact validation and metrics normally."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    arrays = {"time_s": time, "observed": observed}
    if covariance is not None:
        arrays["covariance"] = covariance
    np.savez(output / "inputs.npz", **arrays)
    _write_json(output / "request.json", {"format": FORMAT, "budget": asdict(budget)})
    candidates = []
    for tree, size in ((constant(2), 1), (candidate_tree(), 6)):
        prediction = evaluate_tree(tree, time)
        residual = observed - prediction
        loss = (
            mean_squared_error(residual)
            if covariance is None
            else CovarianceLoss(covariance).mean_squared(residual)
        )
        candidates.append(
            {
                "tree": tree,
                "prediction": prediction.tolist(),
                "residual": residual.tolist(),
                "loss": loss,
                "complexity": size,
                "display_equation": "test candidate",
            }
        )
    _write_json(
        output / "result.json",
        {
            "format": FORMAT,
            "evaluation_scope": "fitted_samples_only",
            "candidates": candidates,
            "selected_index": select_candidate(candidates),
        },
    )
    for name in ("metadata.json", "metadata_initial.json"):
        _write_json(output / name, {"test_stub": True})
    _write_json(
        output / "checksums.json",
        {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in output.iterdir()
            if path.is_file()
        },
    )
    return SearchRun(output, "success")


@pytest.fixture
def stub_search(monkeypatch):
    calls = []

    def search(time, observed, *, covariance, output, budget):
        assert not time.flags.writeable and not observed.flags.writeable
        assert covariance is None or not covariance.flags.writeable
        calls.append(
            (
                time.copy(),
                observed.copy(),
                None if covariance is None else covariance.copy(),
                budget,
            )
        )
        return write_worker(
            time, observed, covariance=covariance, output=output, budget=budget
        )

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", search)
    return calls


@pytest.mark.parametrize("kind", ["white", "ar1"])
def test_schema3_reference_conversion_roundtrips_all_existing_values(kind):
    config = parse_config(small_config(kind).encode())
    assert isinstance(config, SymbolicPilotConfig) and config.schema_version == 3
    reference = config.reference_config()
    old = parse_config((ROOT / f"configs/pilot_estimated_{kind}.toml").read_bytes())
    assert reference.signal == old.signal and reference.noise == old.noise
    assert (
        reference.fit == old.fit
        and reference.covariance_estimation == old.covariance_estimation
    )
    assert parse_config(symbolic_pilot._reference_toml(reference)) == reference
    assert reference.schema_version == 2 and config.schema_version == 3


@pytest.mark.parametrize(
    "old,new",
    [
        ("[symbolic_search]", "[unknown_search]"),
        ("seed = 20261020", "seed = true"),
        ("seed = 20261020", "seed = 4294967296"),
        ("niterations = 1", "niterations = 0"),
        ("populations = 1", "populations = 0"),
        ("population_size = 16", "population_size = 15"),
        ("ncycles_per_iteration = 2", "ncycles_per_iteration = -1"),
        ("ncycles_per_iteration = 2", 'ncycles_per_iteration = 2\nguesses = ["truth"]'),
        ("ncycles_per_iteration = 2", "ncycles_per_iteration = 2\nparsimony = 0.1"),
        ("ncycles_per_iteration = 2", ""),
    ],
)
def test_invalid_schema3_never_reserves_output(tmp_path, old, new):
    path = tmp_path / "bad.toml"
    path.write_text(small_config().replace(old, new))
    with pytest.raises((TypeError, ValueError)):
        run_pilot(path, tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("kind", ["white", "ar1"])
def test_shared_binary_data_diagnostics_and_all_artifact_hashes(
    tmp_path, stub_search, kind
):
    config_path = tmp_path / "input.toml"
    config_path.write_text(small_config(kind))
    outcome = run_pilot(config_path, tmp_path / "run")
    output = outcome.output_directory
    assert outcome.status == "success"
    result, meta = read(output / "result.json"), read(output / "metadata.json")
    assert result["schema_version"] == meta["schema_version"] == 3
    assert meta["status"] == "success" and len(stub_search) == 3
    assert read(output / "metadata_initial.json")["status"] == "running"
    assert (output / "config.toml").read_bytes() == config_path.read_bytes()
    assert read(output / "reference/result.json")["schema_version"] == 2
    for field in ("covariance_file", "raw_covariance_file"):
        assert (output / result["covariance_estimation"][field]).is_file()
    with np.load(output / result["shared_inputs_file"], allow_pickle=False) as data:
        for i, (time, observed, covariance, budget) in enumerate(stub_search):
            np.testing.assert_array_equal(time, data["time_s"])
            np.testing.assert_array_equal(observed, data["observed"])
            assert budget == load_config(config_path).symbolic_search
            if i == 0:
                assert covariance is None
            else:
                np.testing.assert_array_equal(
                    covariance,
                    data["covariance_true" if i == 1 else "covariance_estimated"],
                )
        # Independent direct solves, not the production Cholesky loss.
        for name, record in result["symbolic_arms"].items():
            arm = read(output / record["result_file"])
            assert record["status"] == "success" and record["selected"]["index"] == 1
            selected = arm["candidates"][arm["selected_index"]]
            prediction = np.array(selected["prediction"])
            residual = data["observed"] - prediction
            expected = (
                residual
                @ np.linalg.solve(data["covariance_true"], residual)
                / residual.size
            )
            metrics = record["metrics"]
            np.testing.assert_allclose(
                metrics["q_true_per_sample"], expected, rtol=1e-13
            )
            np.testing.assert_allclose(
                metrics["ordinary_mse"], np.mean(residual**2), rtol=1e-13
            )
            np.testing.assert_allclose(
                metrics["mse_to_clean_signal"],
                np.mean((prediction - data["signal"]) ** 2),
                rtol=1e-13,
            )
            if name == "ordinary":
                assert metrics["q_used_per_sample"] is None
            else:
                matrix = data[
                    "covariance_true"
                    if name == "known_covariance"
                    else "covariance_estimated"
                ]
                expected_used = (
                    residual @ np.linalg.solve(matrix, residual) / residual.size
                )
                np.testing.assert_allclose(
                    metrics["q_used_per_sample"], expected_used, rtol=1e-13
                )
    for name, digest in meta["artifact_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    assert (output / "plot.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    # A standalone schema-2 run has exactly the same data and estimated covariance.
    reference_path = tmp_path / "reference.toml"
    reference_path.write_bytes((output / "reference_config.toml").read_bytes())
    assert run_pilot(reference_path, tmp_path / "standalone").status == "success"
    for name in (
        "samples.csv",
        "background_train.csv",
        "background_validation.csv",
        "background_check.csv",
        "covariance_true.csv",
        "covariance_estimated.csv",
    ):
        assert (output / "reference" / name).read_bytes() == (
            tmp_path / "standalone" / name
        ).read_bytes()
    with pytest.raises(FileExistsError):
        run_pilot(config_path, output)


@pytest.mark.parametrize("bad_arm", list(symbolic_pilot.ARM_LABELS))
def test_failed_worker_keeps_other_arms_and_complete_failure_status(
    tmp_path, monkeypatch, bad_arm
):
    calls = []

    def search(time, observed, **kwargs):
        calls.append(Path(kwargs["output"]).name)
        if calls[-1] == bad_arm:
            Path(kwargs["output"]).mkdir(parents=True)
            (Path(kwargs["output"]) / "worker.log").write_text("injected failure")
            return SearchRun(Path(kwargs["output"]), "failed")
        return write_worker(time, observed, **kwargs)

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", search)
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    outcome = run_pilot(path, tmp_path / "run")
    result = read(outcome.output_directory / "result.json")
    assert outcome.status == "comparison_failed" and len(calls) == 3
    assert result["symbolic_arms"][bad_arm]["status"] == "failed"
    assert sum(x["status"] == "success" for x in result["symbolic_arms"].values()) == 2
    assert (
        read(outcome.output_directory / "metadata.json")["status"]
        == "comparison_failed"
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "input",
        "covariance",
        "selection",
        "prediction",
        "residual",
        "loss",
        "hash",
        "missing_field",
    ],
)
def test_worker_contract_corruption_is_rejected(tmp_path, monkeypatch, corruption):
    def search(time, observed, **kwargs):
        run = write_worker(time, observed, **kwargs)
        directory = run.output_directory
        if directory.name != "known_covariance":
            return run
        result = read(directory / "result.json")
        if corruption in ("input", "covariance"):
            with np.load(directory / "inputs.npz") as inputs:
                arrays = {name: inputs[name].copy() for name in inputs.files}
            arrays["observed" if corruption == "input" else "covariance"] *= 2
            np.savez(directory / "inputs.npz", **arrays)
        elif corruption == "selection":
            result["selected_index"] = 0
        elif corruption in ("prediction", "residual"):
            result["candidates"][0][corruption][0] *= -1
        elif corruption == "loss":
            result["candidates"][0]["loss"] *= 2
        elif corruption == "missing_field":
            del result["candidates"][0]["tree"]
        else:
            (directory / "metadata.json").write_text("changed after hashing")
        if corruption != "hash":
            _write_json(directory / "result.json", result)
            checksums = read(directory / "checksums.json")
            for name in checksums:
                checksums[name] = hashlib.sha256(
                    (directory / name).read_bytes()
                ).hexdigest()
            _write_json(directory / "checksums.json", checksums)
        return run

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", search)
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    outcome = run_pilot(path, tmp_path / "run")
    assert outcome.status == "comparison_failed"
    assert (
        read(outcome.output_directory / "result.json")["symbolic_arms"][
            "known_covariance"
        ]["status"]
        == "failed"
    )


def test_reference_failure_never_starts_search(tmp_path, monkeypatch, stub_search):
    def fail(*args, **kwargs):
        raise ValueError("injected preparation failure")

    monkeypatch.setattr(symbolic_pilot, "run_covariance_pilot", fail)
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    outcome = run_pilot(path, tmp_path / "run")
    assert outcome.status == "failed" and stub_search == []
    result = read(outcome.output_directory / "result.json")
    assert all(
        record["status"] == "not_run" for record in result["symbolic_arms"].values()
    )
    assert read(outcome.output_directory / "metadata_initial.json")["provenance"]


def test_seed_collision_is_rejected_before_output(tmp_path):
    path = tmp_path / "collision.toml"
    path.write_text(
        small_config().replace(
            "seed = 42", "seed = 340282366920938463463374607431788472475"
        )
    )
    with pytest.raises(ValueError):
        run_pilot(path, tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


def test_cli_schema3_success_and_failure(tmp_path, stub_search, capsys):
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    assert main(["run", str(path), "--output", str(tmp_path / "run")]) == 0
    text = capsys.readouterr().out
    assert "SR mit wahrer Kovarianz" in text and "Q_true/N" in text
    assert "Frequenz:" not in text


def test_truth_diagnostics_cannot_change_frozen_selection(
    tmp_path, stub_search, monkeypatch
):
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    before = run_pilot(path, tmp_path / "before")
    diagnose = symbolic_pilot._diagnose

    def changed_truth(selected, observed, signal, truth, covariance):
        return diagnose(selected, observed, signal * 1e6, truth, covariance)

    monkeypatch.setattr(symbolic_pilot, "_diagnose", changed_truth)
    after = run_pilot(path, tmp_path / "after")
    first, second = (
        read(before.output_directory / "result.json"),
        read(after.output_directory / "result.json"),
    )
    for name in symbolic_pilot.ARM_LABELS:
        assert (
            first["symbolic_arms"][name]["selected"]
            == second["symbolic_arms"][name]["selected"]
        )
        assert (
            first["symbolic_arms"][name]["metrics"]["mse_to_clean_signal"]
            != second["symbolic_arms"][name]["metrics"]["mse_to_clean_signal"]
        )
    for original, repeated in zip(stub_search[:3], stub_search[3:], strict=True):
        np.testing.assert_array_equal(original[0], repeated[0])
        np.testing.assert_array_equal(original[1], repeated[1])
        if original[2] is not None:
            np.testing.assert_array_equal(original[2], repeated[2])


def test_interrupt_and_export_failure_do_not_report_success(tmp_path, monkeypatch):
    path = tmp_path / "input.toml"
    path.write_text(small_config())

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(symbolic_pilot, "run_search_arm", interrupt)
    with pytest.raises(KeyboardInterrupt):
        run_pilot(path, tmp_path / "interrupted")
    assert read(tmp_path / "interrupted/result.json")["status"] == "aborted"
    assert read(tmp_path / "interrupted/metadata.json")["status"] == "aborted"
    monkeypatch.setattr(symbolic_pilot, "run_search_arm", write_worker)

    def fail_plot(*args):
        raise OSError("injected export failure")

    monkeypatch.setattr(symbolic_pilot, "_save_symbolic_plot", fail_plot)
    with pytest.raises(OSError, match="export failure"):
        run_pilot(path, tmp_path / "export-failed")
    assert read(tmp_path / "export-failed/result.json")["status"] == "export_failed"
    assert read(tmp_path / "export-failed/metadata.json")["status"] == "export_failed"


def test_corrupt_reference_handoff_never_reaches_search(
    tmp_path, monkeypatch, stub_search
):
    original = symbolic_pilot.run_covariance_pilot

    def tamper(*args, **kwargs):
        outcome = original(*args, **kwargs)
        (outcome.output_directory / "comparison_inputs.npz").write_bytes(b"corrupted")
        return outcome

    monkeypatch.setattr(symbolic_pilot, "run_covariance_pilot", tamper)
    path = tmp_path / "input.toml"
    path.write_text(small_config())
    outcome = run_pilot(path, tmp_path / "run")
    assert outcome.status == "failed" and stub_search == []
    assert (
        "checksum" in read(outcome.output_directory / "result.json")["error"]["message"]
    )
