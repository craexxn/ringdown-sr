"""Check exported three-fit controls against independent matrix and RNG references."""

import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr import background, covariance_pilot, pilot
from ringdown_sr.cli import main
from ringdown_sr.config import load_config

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("ordinary", "known_covariance", "estimated_covariance")


def small_example(kind="ar1"):
    return (
        (ROOT / f"configs/pilot_estimated_{kind}.toml")
        .read_text()
        .replace("n_samples = 128", "n_samples = 32")
        .replace("n_train = 64", "n_train = 16")
        .replace("n_validation = 128", "n_validation = 20")
        .replace("n_check = 256", "n_check = 24")
        .replace("[0.0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]", "[0.0, 0.5, 1.0]")
    )


def read_json(path):
    return json.loads(path.read_text())


def matrix(path):
    return np.loadtxt(path, delimiter=",", ndmin=2)


def samples(output):
    return np.genfromtxt(output / "samples.csv", delimiter=",", names=True)


@pytest.fixture(scope="module", params=["white", "ar1"])
def stored(request, tmp_path_factory):
    root = tmp_path_factory.mktemp("comparison-" + request.param)
    config = root / "input.toml"
    config.write_text(small_example(request.param))
    output = root / "run"
    assert pilot.run_pilot(config, output).status == "success"
    return config, output


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "input.toml"
    path.write_text(small_example())
    return path


def test_complete_exports_have_consistent_shapes_hashes_and_fit_metrics(stored):
    config_path, output = stored
    config = load_config(config_path)
    expected = {
        "config.toml",
        "resolved_config.json",
        "metadata.json",
        "result.json",
        "samples.csv",
        "plot.png",
        "covariance_plot.png",
    }
    expected |= {f"background_{role}.csv" for role in ("train", "validation", "check")}
    expected |= {f"covariance_{name}.csv" for name in ("true", "raw", "estimated")}
    assert {path.name for path in output.iterdir()} == expected
    for image in ("plot.png", "covariance_plot.png"):
        assert (output / image).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    meta = read_json(output / "metadata.json")
    result = read_json(output / "result.json")
    assert meta["schema_version"] == result["schema_version"] == 2
    assert meta["status"] == result["status"] == "success"
    assert result["stage"] == "complete"
    assert meta["environment"]["julia_used"] is False
    assert meta["elapsed_seconds"] >= 0
    assert meta["finished_at_utc"] >= meta["started_at_utc"]
    assert set(meta["artifact_sha256"]) == expected - {"metadata.json"}
    for name, digest in meta["artifact_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    assert (output / "config.toml").read_bytes() == config_path.read_bytes()
    assert read_json(output / "resolved_config.json") == json.loads(
        json.dumps(config.to_dict())
    )
    assert (
        meta["configuration"]["original_sha256"]
        == meta["artifact_sha256"]["config.toml"]
    )
    assert (
        meta["configuration"]["resolved_sha256"]
        == meta["artifact_sha256"]["resolved_config.json"]
    )
    data = samples(output)
    assert data.dtype.names == (
        "time_s",
        "signal",
        "noise",
        "observed",
        *(
            field + "_" + name
            for name in VARIANTS
            for field in ("prediction", "residual")
        ),
    )
    assert_array_equal(data["observed"], data["signal"] + data["noise"])
    true = matrix(output / "covariance_true.csv")
    for role, amount in (("train", 16), ("validation", 20), ("check", 24)):
        assert matrix(output / f"background_{role}.csv").shape == (amount, 32)
    for name in VARIANTS:
        record = result["fits"][name]
        assert record["status"] == "success" and record["error"] is None
        assert record["fit"]["weighting"] == name
        assert len(record["fit"]["attempts"]) == 3
        residual = data["residual_" + name]
        assert_array_equal(residual, data["observed"] - data["prediction_" + name])
        metrics = record["metrics"]
        assert metrics["evaluation_scope"] == "fitted_samples_only"
        assert_allclose(metrics["ordinary_mse"], np.mean(residual**2), rtol=1e-14)
        assert_allclose(
            metrics["mse_to_clean_signal"],
            np.mean((data["prediction_" + name] - data["signal"]) ** 2),
            rtol=1e-14,
        )
        assert_allclose(
            metrics["q_true_per_sample"],
            residual @ np.linalg.solve(true, residual) / 32,
            rtol=1e-13,
        )
        if name == "ordinary":
            assert metrics["q_used_per_sample"] is None
            assert record["fit"]["covariance_file"] is None
        else:
            used = matrix(output / record["fit"]["covariance_file"])
            assert_allclose(
                metrics["q_used_per_sample"],
                residual @ np.linalg.solve(used, residual) / 32,
                rtol=1e-13,
            )


def independent_score(covariance, windows):
    sign, logdet = np.linalg.slogdet(covariance)
    assert sign == 1
    quadratic = np.sum(windows * np.linalg.solve(covariance, windows.T).T) / len(
        windows
    )
    return logdet, quadratic, logdet + quadratic


def test_saved_inputs_reconstruct_shrinkage_selection_and_separate_check_score(stored):
    _, output = stored
    result = read_json(output / "result.json")
    estimate = result["covariance_estimation"]
    train, validation, check = [
        matrix(output / f"background_{role}.csv")
        for role in ("train", "validation", "check")
    ]
    raw = matrix(output / "covariance_raw.csv")
    # Gram products use different accumulation/scaling; bound absolute error by
    # training row count, machine epsilon and the largest empirical variance.
    tolerance = 8 * len(train) * np.finfo(float).eps * np.max(np.diag(raw))
    assert_allclose(raw, train.T @ train / len(train), rtol=0, atol=tolerance)
    assert_array_equal(raw, raw.T)
    mu = np.trace(raw) / 32
    assert_allclose(estimate["mu"], mu, rtol=4 * np.finfo(float).eps)
    assert estimate["refit"] is False
    assert estimate["candidates"][0]["reason"] == "structurally_singular"
    for candidate in estimate["candidates"][1:]:
        alpha = candidate["alpha"]
        covariance = (1 - alpha) * raw + alpha * mu * np.eye(32)
        expected = independent_score(covariance, validation)
        relative_tolerance = 128 * np.finfo(float).eps * np.linalg.cond(covariance)
        assert_allclose(
            [
                candidate[key]
                for key in ("log_determinant", "validation_quadratic_mean", "score")
            ],
            expected,
            rtol=relative_tolerance,
            atol=0,
        )
    winner = min(estimate["candidates"][1:], key=lambda c: (c["score"], c["alpha"]))
    assert estimate["alpha_selected"] == winner["alpha"]
    selected = matrix(output / "covariance_estimated.csv")
    assert_allclose(
        selected,
        (1 - winner["alpha"]) * raw + winner["alpha"] * mu * np.eye(32),
        rtol=0,
        atol=tolerance,
    )
    truth = matrix(output / "covariance_true.csv")
    diagnostics = result["diagnostics"]
    assert diagnostics["evaluation_scope"] == "post_selection_only"
    assert_allclose(
        diagnostics["relative_frobenius_error"],
        np.linalg.norm(selected - truth, "fro") / np.linalg.norm(truth, "fro"),
        rtol=1e-14,
    )
    for name, covariance in (("true", truth), ("estimated", selected)):
        record = diagnostics["background_check"][name]
        assert record["n_windows"] == 24
        assert_allclose(
            [record[key] for key in ("log_determinant", "quadratic_mean", "score")],
            independent_score(covariance, check),
            rtol=1e-13,
        )


def independent_windows(rng, noise, amount, n_samples):
    rows = []
    for _ in range(amount):
        if noise.kind == "gaussian_white":
            row = rng.normal(0, noise.standard_deviation, n_samples)
        else:
            z = rng.standard_normal(n_samples, dtype=np.float64)
            rho = noise.correlation
            # Closed innovation sum, independent of the production recurrence.
            row = noise.standard_deviation * np.array(
                [
                    rho**k * z[0]
                    + math.sqrt(1 - rho * rho)
                    * sum(rho ** (k - j) * z[j] for j in range(1, k + 1))
                    for k in range(n_samples)
                ]
            )
        rows.append(row)
    return np.stack(rows)


def test_role_seeds_rng_states_and_independent_stationary_windows_replay(stored):
    config_path, output = stored
    config = load_config(config_path)
    meta = read_json(output / "metadata.json")["random"]
    assert meta["background"]["root_seed"] == 20261019
    assert meta["background"]["scheme"] == "seedsequence_role_v1"
    assert meta["background"]["sampling"] == asdict(config.sampling)
    assert (
        meta["background"]["distribution"]["standard_deviation"]
        == config.noise.standard_deviation
    )
    before = np.random.get_state()
    for role, role_id, amount in (
        ("train", 0, 16),
        ("validation", 1, 20),
        ("check", 2, 24),
    ):
        record = meta["background"]["roles"][role]
        assert record["role_id"] == role_id
        assert record["seed_sequence"] == {
            "entropy": 20261019,
            "spawn_key": [role_id],
            "pool_size": 4,
        }
        rng = np.random.Generator(
            np.random.PCG64(
                np.random.SeedSequence(20261019, spawn_key=(role_id,), pool_size=4)
            )
        )
        assert rng.bit_generator.state == record["state_before"]
        expected = independent_windows(rng, config.noise, amount, 32)
        assert_allclose(
            matrix(output / f"background_{role}.csv"),
            expected,
            rtol=128 * np.finfo(float).eps,
            atol=128 * np.finfo(float).eps * 0.1,
        )
        assert rng.bit_generator.state == record["state_after"]
        assert (
            record["calls"]["completed_calls"]
            == record["calls"]["expected_calls"]
            == amount
        )
        assert record["calls"]["size"] == 32
        if config.noise.kind == "gaussian_ar1":
            assert (
                record["transform"]["initialization"]
                == "independent_stationary_start_per_window"
            )
    rng = np.random.Generator(np.random.PCG64(42))
    assert meta["signal"]["state_before"] == rng.bit_generator.state
    expected = independent_windows(rng, config.noise, 1, 32)[0]
    assert_allclose(
        samples(output)["noise"],
        expected,
        rtol=128 * np.finfo(float).eps,
        atol=128 * np.finfo(float).eps * 0.1,
    )
    assert meta["signal"]["state_after"] == rng.bit_generator.state
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])


def test_repeated_run_preserves_all_numeric_inputs_and_results(stored, tmp_path):
    config, first = stored
    second = tmp_path / "repeated"
    assert pilot.run_pilot(config, second).status == "success"
    for path in first.iterdir():
        if path.suffix == ".csv" or path.name in (
            "result.json",
            "resolved_config.json",
        ):
            assert path.read_bytes() == (second / path.name).read_bytes()


def test_one_estimate_and_three_fits_share_data_distribution_starts_and_fixed_matrices(
    config_path, tmp_path, monkeypatch
):
    original_estimate = covariance_pilot.estimate_covariance
    original_fit = covariance_pilot.fit_ringdown
    original_draw = background.draw_noise_window
    estimates, fits, draws = [], [], []

    def estimate(train, validation, **kwargs):
        assert set(kwargs) == {"alpha_candidates", "kappa_max", "mean_mode"}
        result = original_estimate(train, validation, **kwargs)
        estimates.append(result)
        return result

    def fit(times, observed, **kwargs):
        fits.append((times, observed, kwargs))
        return original_fit(times, observed, **kwargs)

    def draw(noise, n_samples, rng):
        draws.append((asdict(noise), n_samples))
        return original_draw(noise, n_samples, rng)

    monkeypatch.setattr(covariance_pilot, "estimate_covariance", estimate)
    monkeypatch.setattr(covariance_pilot, "fit_ringdown", fit)
    monkeypatch.setattr(covariance_pilot, "draw_noise_window", draw)
    monkeypatch.setattr(background, "draw_noise_window", draw)
    before = np.random.get_state()
    output = tmp_path / "spied"
    assert pilot.run_pilot(config_path, output).status == "success"
    assert len(estimates) == 1 and len(fits) == 3
    assert all(
        times is fits[0][0] and observed is fits[0][1] for times, observed, _ in fits
    )
    assert fits[0][2]["covariance"] is None
    assert fits[2][2]["covariance"] is estimates[0].covariance
    assert not estimates[0].covariance.flags.writeable
    assert_array_equal(
        estimates[0].covariance, matrix(output / "covariance_estimated.csv")
    )
    for _, _, kwargs in fits[1:]:
        assert {k: v for k, v in kwargs.items() if k != "covariance"} == {
            k: v for k, v in fits[0][2].items() if k != "covariance"
        }
    assert draws == [(asdict(load_config(config_path).noise), 32)] * (1 + 16 + 20 + 24)
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])


def test_changed_check_values_cannot_change_selection_or_any_fit(
    stored, tmp_path, monkeypatch
):
    config, first = stored
    original = covariance_pilot.generate_background

    def altered(*args, windows, **kwargs):
        original(*args, windows=windows, **kwargs)
        windows["check"] *= 7

    monkeypatch.setattr(covariance_pilot, "generate_background", altered)
    second = tmp_path / "changed-check"
    assert pilot.run_pilot(config, second).status == "success"
    old, new = [read_json(path / "result.json") for path in (first, second)]
    assert old["covariance_estimation"] == new["covariance_estimation"]
    assert old["fits"] == new["fits"]
    assert old["diagnostics"] != new["diagnostics"]
    for name in (
        "samples.csv",
        "covariance_estimated.csv",
        "background_train.csv",
        "background_validation.csv",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


@pytest.mark.parametrize(
    "role,old,new", [("train", 16, 17), ("validation", 20, 21), ("check", 24, 25)]
)
def test_role_amount_does_not_shift_signal_noise_or_other_roles(
    config_path, tmp_path, role, old, new
):
    first, second = tmp_path / "first", tmp_path / "second"
    assert pilot.run_pilot(config_path, first).status == "success"
    config_path.write_text(
        config_path.read_text().replace(f"n_{role} = {old}", f"n_{role} = {new}")
    )
    assert pilot.run_pilot(config_path, second).status == "success"
    for field in ("time_s", "signal", "noise", "observed"):
        assert_array_equal(samples(first)[field], samples(second)[field])
    for other in ("train", "validation", "check"):
        if other != role:
            assert (first / f"background_{other}.csv").read_bytes() == (
                second / f"background_{other}.csv"
            ).read_bytes()
    assert_array_equal(
        matrix(first / f"background_{role}.csv"),
        matrix(second / f"background_{role}.csv")[:old],
    )


@pytest.mark.parametrize(
    "old,new", [("amplitude = 1.0", "amplitude = 1.5"), ("seed = 42", "seed = 43")]
)
def test_signal_truth_or_signal_seed_cannot_change_background_estimate(
    config_path, tmp_path, old, new
):
    first, second = tmp_path / "first", tmp_path / "second"
    assert pilot.run_pilot(config_path, first).status == "success"
    config_path.write_text(config_path.read_text().replace(old, new))
    assert pilot.run_pilot(config_path, second).status == "success"
    assert (
        read_json(first / "result.json")["covariance_estimation"]
        == read_json(second / "result.json")["covariance_estimation"]
    )
    for name in (
        "background_train",
        "background_validation",
        "background_check",
        "covariance_estimated",
        "covariance_raw",
    ):
        assert (first / f"{name}.csv").read_bytes() == (
            second / f"{name}.csv"
        ).read_bytes()


def test_failed_estimation_retains_inputs_candidates_and_never_runs_a_fit(
    config_path, tmp_path, monkeypatch
):
    config_path.write_text(config_path.read_text().replace("[0.0, 0.5, 1.0]", "[0.0]"))

    def forbidden(*args, **kwargs):
        pytest.fail("A failed covariance estimate must not start a substitute fit")

    monkeypatch.setattr(covariance_pilot, "fit_ringdown", forbidden)
    output = tmp_path / "failed"
    assert pilot.run_pilot(config_path, output).status == "estimation_failed"
    result = read_json(output / "result.json")
    assert result["stage"] == "covariance_estimation"
    assert result["error"]["type"] == "CovarianceEstimationError"
    assert (
        result["covariance_estimation"]["candidates"][0]["reason"]
        == "structurally_singular"
    )
    assert all(record["status"] == "not_run" for record in result["fits"].values())
    assert (output / "covariance_raw.csv").is_file()
    assert not (output / "covariance_estimated.csv").exists()
    assert not (output / "plot.png").exists()
    assert read_json(output / "metadata.json")["status"] == "estimation_failed"


def test_exhausted_fits_keep_all_three_attempt_sets_and_estimated_covariance(
    config_path, tmp_path
):
    config_path.write_text(
        config_path.read_text().replace("max_nfev = 1000", "max_nfev = 1")
    )
    output = tmp_path / "exhausted"
    assert pilot.run_pilot(config_path, output).status == "fit_failed"
    result = read_json(output / "result.json")
    for record in result["fits"].values():
        assert record["status"] == "fit_failed" and record["fit"] is None
        assert record["error"]["type"] == "ReferenceFitError"
        assert len(record["error"]["attempts"]) == 3
    assert result["covariance_estimation"]["alpha_selected"] is not None
    assert (output / "covariance_estimated.csv").is_file()
    assert samples(output).dtype.names == ("time_s", "signal", "noise", "observed")


def test_overflowing_check_retains_fits_finite_logdet_and_reports_evaluation_failure(
    config_path, tmp_path, monkeypatch
):
    original = covariance_pilot.generate_background

    def huge_check(*args, windows, **kwargs):
        original(*args, windows=windows, **kwargs)
        windows["check"][:] = 1e200

    monkeypatch.setattr(covariance_pilot, "generate_background", huge_check)

    output = tmp_path / "bad-check"
    assert pilot.run_pilot(config_path, output).status == "evaluation_failed"
    result = read_json(output / "result.json")
    assert result["stage"] == "diagnostics"
    assert all(record["status"] == "success" for record in result["fits"].values())
    check = result["diagnostics"]["background_check"]["true"]
    assert math.isfinite(check["log_determinant"])
    assert check["quadratic_mean"] is None and check["score"] is None
    assert read_json(output / "metadata.json")["status"] == "evaluation_failed"


def test_generation_failure_saves_only_completed_background_rows_and_real_rng_state(
    config_path, tmp_path, monkeypatch
):
    original = background.draw_noise_window
    calls = 0

    def fail_fourth(*args, **kwargs):
        nonlocal calls
        calls += 1
        row = original(*args, **kwargs)
        if calls == 4:
            raise FloatingPointError("induced background generation failure")
        return row

    monkeypatch.setattr(background, "draw_noise_window", fail_fourth)
    output = tmp_path / "partial"
    assert pilot.run_pilot(config_path, output).status == "generation_failed"
    assert matrix(output / "background_train.csv").shape == (3, 32)
    roles = read_json(output / "metadata.json")["random"]["background"]["roles"]
    assert roles["train"]["calls"]["completed_calls"] == 3
    assert roles["train"]["state_after"] is not None
    replay = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(20261019, spawn_key=(0,), pool_size=4))
    )
    for _ in range(4):
        replay.standard_normal(32, dtype=np.float64)
    assert roles["train"]["state_after"] == replay.bit_generator.state
    assert roles["validation"]["state_before"] is None
    assert roles["check"]["calls"]["completed_calls"] == 0


def test_one_failed_fit_does_not_hide_other_variants_or_become_success(
    config_path, tmp_path, monkeypatch
):
    original = covariance_pilot.fit_ringdown
    calls = 0

    def fail_known(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("induced known-covariance fit failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(covariance_pilot, "fit_ringdown", fail_known)
    output = tmp_path / "partial-fits"
    assert pilot.run_pilot(config_path, output).status == "fit_failed"
    records = read_json(output / "result.json")["fits"]
    assert (
        records["ordinary"]["status"]
        == records["estimated_covariance"]["status"]
        == "success"
    )
    assert records["known_covariance"]["status"] == "fit_failed"
    assert records["known_covariance"]["fit"] is None
    assert (
        records["estimated_covariance"]["fit"]["covariance_file"]
        == "covariance_estimated.csv"
    )


def test_export_failure_keeps_manifest_running_and_existing_target_is_rejected(
    config_path, tmp_path, monkeypatch
):
    def fail(*args, **kwargs):
        raise OSError("induced export failure")

    monkeypatch.setattr(covariance_pilot, "_save_comparison_plot", fail)
    output = tmp_path / "partial-export"
    with pytest.raises(OSError, match="export failure"):
        pilot.run_pilot(config_path, output)
    assert read_json(output / "metadata.json")["status"] == "running"
    before = (output / "metadata.json").read_bytes()
    with pytest.raises(FileExistsError):
        pilot.run_pilot(config_path, output)
    assert (output / "metadata.json").read_bytes() == before


def test_schema_two_cli_reports_three_variants_and_failure_exit_codes(
    config_path, tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    assert main(["run", str(config_path), "--output", "success"]) == 0
    output = capsys.readouterr().out
    assert "Gewähltes Alpha:" in output
    assert output.count("Q_true/N") == 3
    assert "Fit mit geschätzter Kovarianz" in output
    assert main(["run", str(config_path), "--output", "success"]) == 2
    config_path.write_text(config_path.read_text().replace("[0.0, 0.5, 1.0]", "[0.0]"))
    assert main(["run", str(config_path), "--output", "failed"]) == 1


@pytest.mark.parametrize("scale", [1.0, 1e-300, 1e300])
def test_relative_matrix_error_uses_scale_stable_frobenius_reference(scale):
    assert_allclose(
        covariance_pilot._relative_matrix_error(
            np.diag([2.0, 2.0]) * scale, np.diag([1.0, 2.0]) * scale
        ),
        1 / math.sqrt(5),
        rtol=2e-15,
    )
