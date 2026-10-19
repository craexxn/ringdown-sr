"""Check configured correlated draws, persisted covariance, and fit weighting."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.config import load_config
from ringdown_sr.pilot import run_pilot

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = (ROOT / "configs/pilot_ar1.toml").read_bytes()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def samples(path):
    return np.genfromtxt(path / "samples.csv", delimiter=",", names=True)


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "ar1.toml"
    path.write_bytes(EXAMPLE)
    return path


def innovation_quadratic(residual, sigma, rho):
    # Independent analytic inverse of the stationary AR(1) recursion.
    return (residual[0] / sigma) ** 2 + np.sum(
        (residual[1:] - rho * residual[:-1]) ** 2
    ) / (sigma**2 * (1 - rho**2))


def test_known_covariance_export_matches_model_and_innovation_quadratic(
    config_path, tmp_path
):
    output = tmp_path / "weighted"
    assert run_pilot(config_path, output).status == "success"
    data = samples(output)
    covariance = np.loadtxt(output / "covariance.csv", delimiter=",")
    sigma, rho = 0.1, 0.65
    assert covariance.shape == (128, 128)
    assert_array_equal(covariance, covariance.T)
    assert_allclose(
        covariance[0, :5],
        sigma**2 * np.array([1, 0.65, 0.4225, 0.274625, 0.17850625]),
        rtol=2e-15,
        atol=0,
    )
    result = read_json(output / "result.json")
    expected = innovation_quadratic(data["residual"], sigma, rho) / 128
    assert_allclose(
        result["metrics"]["covariance_mean_squared"], expected, rtol=1e-12, atol=0
    )
    assert_allclose(
        result["metrics"]["known_covariance_mean_squared"], expected, rtol=1e-12, atol=0
    )
    assert result["noise_model"] == {
        "kind": "gaussian_ar1",
        "covariance_source": "analytic_stationary_ar1",
        "covariance_file": "covariance.csv",
        "covariance_used_for_fit": True,
    }
    manifest = read_json(output / "metadata.json")
    assert manifest["random"]["calls"] == [
        {
            "method": "standard_normal",
            "dtype": "float64",
            "size": 128,
            "completed": True,
        }
    ]
    assert manifest["random"]["transform"]["initialization"] == "stationary"
    # Recover the exact draws from the saved state and apply an independent
    # lower-triangular analytic mapping (not the production recursion).
    generator = np.random.Generator(np.random.PCG64())
    generator.bit_generator.state = manifest["random"]["state_before"]
    independent = generator.standard_normal(128, dtype=np.float64)
    matrix = np.zeros((128, 128))
    for i in range(128):
        matrix[i, 0] = sigma * rho**i
        for j in range(1, i + 1):
            matrix[i, j] = sigma * np.sqrt(1 - rho**2) * rho ** (i - j)
    assert_allclose(data["noise"], matrix @ independent, rtol=0, atol=2e-15)
    assert generator.bit_generator.state == manifest["random"]["state_after"]
    for name, digest in manifest["artifact_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    assert "covariance.csv" in manifest["artifact_sha256"]


def test_ordinary_and_weighted_examples_share_data_starts_and_known_diagnostic(
    tmp_path,
):
    weighted_config = load_config(ROOT / "configs/pilot_ar1.toml").to_dict()
    ordinary_config = load_config(ROOT / "configs/pilot_ar1_ordinary.toml").to_dict()
    ordinary_config["fit"]["weighting"] = "known_covariance"
    assert ordinary_config == weighted_config
    weighted, ordinary = tmp_path / "weighted", tmp_path / "ordinary"
    assert run_pilot(ROOT / "configs/pilot_ar1.toml", weighted).status == "success"
    assert (
        run_pilot(ROOT / "configs/pilot_ar1_ordinary.toml", ordinary).status
        == "success"
    )
    w, o = samples(weighted), samples(ordinary)
    for field in ("time_s", "signal", "noise", "observed"):
        assert_array_equal(w[field], o[field])
    assert (weighted / "covariance.csv").read_bytes() == (
        ordinary / "covariance.csv"
    ).read_bytes()
    wr, orr = read_json(weighted / "result.json"), read_json(ordinary / "result.json")
    assert orr["metrics"]["covariance_mean_squared"] is None
    assert orr["noise_model"]["covariance_used_for_fit"] is False
    assert_allclose(
        orr["metrics"]["known_covariance_mean_squared"],
        innovation_quadratic(o["residual"], 0.1, 0.65) / 128,
        rtol=1e-12,
        atol=0,
    )
    # A numerical objective check for this control case; no performance claim.
    assert (
        wr["metrics"]["known_covariance_mean_squared"]
        <= orr["metrics"]["known_covariance_mean_squared"] + 1e-8
    )
    assert orr["metrics"]["ordinary_mse"] <= wr["metrics"]["ordinary_mse"] + 1e-10


def test_repeated_ar1_run_preserves_samples_results_and_covariance(
    config_path, tmp_path
):
    first, second = tmp_path / "first", tmp_path / "second"
    run_pilot(config_path, first)
    run_pilot(first / "config.toml", second)
    for name in (
        "samples.csv",
        "result.json",
        "covariance.csv",
        "resolved_config.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_zero_correlation_reduces_to_white_control(config_path, tmp_path):
    config_path.write_bytes(
        EXAMPLE.replace(b"correlation = 0.65", b"correlation = 0.0")
    )
    ar1, white = tmp_path / "ar1", tmp_path / "white"
    run_pilot(config_path, ar1)
    run_pilot(ROOT / "configs/pilot_white.toml", white)
    assert_array_equal(samples(ar1)["noise"], samples(white)["noise"])
    assert_allclose(
        samples(ar1)["prediction"], samples(white)["prediction"], rtol=0, atol=1e-12
    )


def test_noiseless_ar1_ordinary_keeps_zero_covariance_and_undefined_weighted_diagnostic(
    config_path, tmp_path
):
    config_path.write_bytes(
        EXAMPLE.replace(
            b"standard_deviation = 0.1", b"standard_deviation = 0.0"
        ).replace(b'weighting = "known_covariance"', b'weighting = "ordinary"')
    )
    output = tmp_path / "zero"
    assert run_pilot(config_path, output).status == "success"
    assert_array_equal(
        np.loadtxt(output / "covariance.csv", delimiter=","), np.zeros((128, 128))
    )
    assert (
        read_json(output / "result.json")["metrics"]["known_covariance_mean_squared"]
        is None
    )


def test_failed_ar1_fit_preserves_known_covariance_and_draws(config_path, tmp_path):
    config_path.write_bytes(EXAMPLE.replace(b"max_nfev = 1000", b"max_nfev = 1"))
    output = tmp_path / "failed"
    assert run_pilot(config_path, output).status == "fit_failed"
    assert (output / "covariance.csv").is_file()
    assert samples(output).dtype.names == ("time_s", "signal", "noise", "observed")
    assert len(read_json(output / "result.json")["error"]["attempts"]) == 3
    assert "covariance.csv" in read_json(output / "metadata.json")["artifact_sha256"]


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"correlation = 0.65", b"correlation = 1"),
        (b"correlation = 0.65", b"correlation = -1"),
        (b"correlation = 0.65", b"correlation = nan"),
        (b"correlation = 0.65", b"correlation = true"),
        (b"correlation = 0.65", b'correlation = "0.5"'),
        (b"correlation = 0.65\n", b""),
        (b"correlation = 0.65", b"correlation = 0.65\nunknown = 1"),
        (b'weighting = "known_covariance"', b'weighting = "known_white"'),
        (b"standard_deviation = 0.1", b"standard_deviation = 0"),
        (b"standard_deviation = 0.1", b"standard_deviation = 1e-200"),
        (b"standard_deviation = 0.1", b"standard_deviation = 1e200"),
        (b'kind = "gaussian_ar1"', b'kind = "gaussian_white"'),
    ],
)
def test_invalid_ar1_configuration_is_rejected_before_output(
    config_path, tmp_path, old, new
):
    config_path.write_bytes(EXAMPLE.replace(old, new))
    with pytest.raises((ValueError, TypeError)):
        run_pilot(config_path, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_generic_known_covariance_weighting_accepts_white_noise(tmp_path):
    path = tmp_path / "white.toml"
    path.write_bytes(
        (ROOT / "configs/pilot_white.toml")
        .read_bytes()
        .replace(b'weighting = "known_white"', b'weighting = "known_covariance"')
    )
    assert run_pilot(path, tmp_path / "white").status == "success"
