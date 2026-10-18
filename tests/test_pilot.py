"""Exercise the stored pilot contract, independent data references, and failures."""

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr import pilot
from ringdown_sr.cli import main
from ringdown_sr.config import load_config, parse_config

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = (ROOT / "configs/pilot_white.toml").read_bytes()


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "input.toml"
    path.write_bytes(EXAMPLE)
    return path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def samples(output):
    return np.genfromtxt(output / "samples.csv", delimiter=",", names=True)


def test_success_stores_complete_artifacts_and_consistent_metrics(
    config_path, tmp_path
):
    output = tmp_path / "run"
    outcome = pilot.run_pilot(config_path, output)
    assert outcome.status == "success"
    assert {p.name for p in output.iterdir()} == {
        "config.toml",
        "resolved_config.json",
        "metadata.json",
        "result.json",
        "samples.csv",
        "plot.png",
    }
    assert (output / "config.toml").read_bytes() == EXAMPLE
    assert (output / "plot.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    resolved = read_json(output / "resolved_config.json")
    assert resolved["noise"]["standard_deviation"] == 0.1
    data = samples(output)
    result = read_json(output / "result.json")
    assert data.dtype.names == (
        "time_s",
        "signal",
        "noise",
        "observed",
        "prediction",
        "residual",
    )
    assert len(data) == 128
    assert_array_equal(data["observed"], data["signal"] + data["noise"])
    assert_array_equal(data["residual"], data["observed"] - data["prediction"])
    mse = np.sum(data["residual"] ** 2) / 128
    assert_allclose(result["metrics"]["ordinary_mse"], mse, rtol=1e-14)
    assert_allclose(
        result["metrics"]["covariance_mean_squared"], mse / 0.01, rtol=1e-14
    )
    assert_allclose(
        result["metrics"]["mse_to_clean_signal"],
        np.sum((data["prediction"] - data["signal"]) ** 2) / 128,
        rtol=1e-14,
    )
    assert result["metrics"]["evaluation_scope"] == "fitted_samples_only"
    assert result["sampling"]["window_duration_s"] == 128 / 4096
    assert result["sampling"]["last_sample_time_s"] == 127 / 4096
    assert len(result["fit"]["attempts"]) == 3
    manifest = read_json(output / "metadata.json")
    assert manifest["status"] == result["status"] == "success"
    assert manifest["finished_at_utc"] >= manifest["started_at_utc"]
    assert manifest["elapsed_seconds"] >= 0
    assert manifest["environment"]["julia_used"] is False
    assert manifest["environment"]["packages"]["numpy"] == np.__version__
    assert set(manifest["artifact_sha256"]) == {p.name for p in output.iterdir()} - {
        "metadata.json"
    }
    for name, digest in manifest["artifact_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    assert (
        manifest["configuration"]["original_sha256"]
        == manifest["artifact_sha256"]["config.toml"]
    )
    assert (
        manifest["configuration"]["resolved_sha256"]
        == manifest["artifact_sha256"]["resolved_config.json"]
    )


def test_same_configuration_repeats_data_and_results_with_rng_state_replay(
    config_path, tmp_path
):
    first, second = tmp_path / "first", tmp_path / "second"
    pilot.run_pilot(config_path, first)
    pilot.run_pilot(first / "config.toml", second)
    for name in ("samples.csv", "result.json", "resolved_config.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    manifest = read_json(first / "metadata.json")
    replay = np.random.Generator(np.random.PCG64())
    replay.bit_generator.state = manifest["random"]["state_before"]
    expected = replay.normal(0.0, 0.1, 128)
    assert_array_equal(expected, samples(first)["noise"])
    assert replay.bit_generator.state == manifest["random"]["state_after"]
    assert manifest["random"]["calls"] == [
        {"method": "normal", "loc": 0.0, "scale": 0.1, "size": 128, "completed": True}
    ]


def test_new_seed_changes_noise_without_changing_signal_or_global_rng(
    config_path, tmp_path
):
    before = np.random.get_state()
    first, second = tmp_path / "first", tmp_path / "second"
    pilot.run_pilot(config_path, first)
    config_path.write_bytes(EXAMPLE.replace(b"seed = 42", b"seed = 43"))
    pilot.run_pilot(config_path, second)
    assert_array_equal(samples(first)["signal"], samples(second)["signal"])
    assert not np.array_equal(samples(first)["noise"], samples(second)["noise"])
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])


def test_noiseless_run_matches_independent_hand_calculated_samples(
    config_path, tmp_path
):
    text = (
        EXAMPLE.decode()
        .replace("n_samples = 128", "n_samples = 20")
        .replace("sample_rate_hz = 4096.0", "sample_rate_hz = 1024.0")
        .replace("amplitude = 1.0", f"amplitude = {math.sqrt(2)!r}")
        .replace("frequency_hz = 250.0", "frequency_hz = 256.0")
        .replace("decay_time_s = 0.008", f"decay_time_s = {1 / (1024 * math.log(2))!r}")
        .replace("phase_rad = 0.0", f"phase_rad = {-math.pi / 4!r}")
        .replace("standard_deviation = 0.1", "standard_deviation = 0.0")
        .replace('weighting = "known_white"', 'weighting = "ordinary"')
        .replace("[100.0, 500.0]", "[180.0, 350.0]")
        .replace("[0.002, 0.03]", "[0.0005, 0.006]")
        .replace(
            "[[150.0, 0.004], [300.0, 0.015], [450.0, 0.004]]",
            "[[210.0, 0.0009], [320.0, 0.003]]",
        )
    )
    config_path.write_text(text, encoding="utf-8")
    output = tmp_path / "analytic"
    assert pilot.run_pilot(config_path, output).status == "success"
    expected = np.ldexp(np.resize([1.0, 1.0, -1.0, -1.0], 20), -np.arange(20))
    data = samples(output)
    assert_allclose(data["signal"], expected, rtol=2e-14, atol=0)
    assert_allclose(data["prediction"], expected, rtol=1e-6, atol=0)
    assert_array_equal(data["noise"], np.zeros(20))
    assert (
        read_json(output / "result.json")["metrics"]["covariance_mean_squared"] is None
    )


def test_exhausted_fit_is_saved_as_failure_with_input_data(config_path, tmp_path):
    config_path.write_bytes(EXAMPLE.replace(b"max_nfev = 1000", b"max_nfev = 1"))
    output = tmp_path / "failed"
    assert pilot.run_pilot(config_path, output).status == "fit_failed"
    result = read_json(output / "result.json")
    assert result["fit"] is None and result["metrics"] is None
    assert result["error"]["type"] == "ReferenceFitError"
    assert len(result["error"]["attempts"]) == 3
    assert all(
        not a["usable"] and a["status"] == 0 for a in result["error"]["attempts"]
    )
    assert samples(output).dtype.names == ("time_s", "signal", "noise", "observed")
    assert not (output / "plot.png").exists()
    assert read_json(output / "metadata.json")["status"] == "fit_failed"


def test_generation_failure_does_not_claim_random_draws_or_a_fit(
    config_path, tmp_path, monkeypatch
):
    def fail(*args, **kwargs):
        raise FloatingPointError("induced generation overflow")

    monkeypatch.setattr(pilot, "ringdown_signal", fail)
    output = tmp_path / "failed"
    assert pilot.run_pilot(config_path, output).status == "generation_failed"
    manifest = read_json(output / "metadata.json")
    assert manifest["random"]["calls"] == []
    assert manifest["random"]["state_before"] is None
    assert not (output / "samples.csv").exists()
    assert read_json(output / "result.json")["stage"] == "generation"


def test_export_failure_leaves_manifest_incomplete(config_path, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("induced plot write failure")

    monkeypatch.setattr(pilot, "_save_plot", fail)
    output = tmp_path / "interrupted"
    with pytest.raises(OSError, match="plot write"):
        pilot.run_pilot(config_path, output)
    manifest = read_json(output / "metadata.json")
    assert manifest["status"] == "running"
    assert manifest["finished_at_utc"] is None


@pytest.mark.parametrize("existing", ["directory", "file", "symlink"])
def test_existing_output_is_never_overwritten(config_path, tmp_path, existing):
    output = tmp_path / "existing"
    if existing == "directory":
        output.mkdir()
        sentinel = output / "result.json"
        sentinel.write_text("preserve", encoding="utf-8")
    elif existing == "file":
        output.write_text("preserve", encoding="utf-8")
        sentinel = output
    else:
        sentinel = tmp_path / "target"
        sentinel.write_text("preserve", encoding="utf-8")
        output.symlink_to(sentinel)
    with pytest.raises(FileExistsError):
        pilot.run_pilot(config_path, output)
    assert sentinel.read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"schema_version = 1", b"schema_version = 2"),
        (b"schema_version = 1", b"schema_version = true"),
        (b"n_samples = 128", b"n_samples = 4"),
        (b"n_samples = 128", b"n_samples = 128.0"),
        (b"sample_rate_hz = 4096.0", b"sample_rate_hz = 0"),
        (b"amplitude = 1.0", b"amplitude = true"),
        (b"amplitude = 1.0", b"amplitude = nan"),
        (b"frequency_hz = 250.0", b"frequency_hz = 2048.0"),
        (b"decay_time_s = 0.008", b"decay_time_s = -1"),
        (b"standard_deviation = 0.1", b"standard_deviation = -1"),
        (b"standard_deviation = 0.1", b"standard_deviation = 0"),
        (b"standard_deviation = 0.1", b"standard_deviation = 1e-200"),
        (b"standard_deviation = 0.1", b"standard_deviation = 1e200"),
        (b"seed = 42", b"seed = -1"),
        (b"seed = 42", b"seed = true"),
        (b'kind = "gaussian_white"', b'kind = "colored"'),
        (b'bit_generator = "PCG64"', b'bit_generator = "default"'),
        (b'weighting = "known_white"', b'weighting = "estimated"'),
        (b"[100.0, 500.0]", b"[0, 500]"),
        (b"[100.0, 500.0]", b"[100, 2048]"),
        (b"[0.002, 0.03]", b"[0.03, 0.002]"),
        (b"[[150.0, 0.004], [300.0, 0.015], [450.0, 0.004]]", b"[]"),
        (b"[[150.0, 0.004], [300.0, 0.015], [450.0, 0.004]]", b"[[100, 0.004]]"),
        (b"max_nfev = 1000", b"max_nfev = 0"),
        (b"max_nfev = 1000", b"max_nfev = true"),
        (b"seed = 42", b"unknown_seed = 42"),
        (b"schema_version = 1", b"schema_version = 1\nunknown = 3"),
        (b"[signal]", b"[signal]\nunknown = 3"),
        (b"[sampling]", b"[sampling]\nunknown = 3"),
        (b"[fit]", b"[fit]\nunknown = 3"),
        (b"phase_rad = 0.0\n", b""),
    ],
)
def test_invalid_configuration_creates_no_output(config_path, tmp_path, old, new):
    config_path.write_bytes(EXAMPLE.replace(old, new))
    output = tmp_path / "invalid"
    with pytest.raises((ValueError, TypeError)):
        pilot.run_pilot(config_path, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "content", [b"[broken", b"\xff", b"schema_version = 1\nschema_version = 1"]
)
def test_malformed_toml_is_rejected(content):
    with pytest.raises(ValueError, match="Invalid UTF-8 TOML"):
        parse_config(content)


def test_load_and_missing_config_without_output(config_path, tmp_path):
    config = load_config(config_path)
    assert config.fit.initial_points == ((150.0, 0.004), (300.0, 0.015), (450.0, 0.004))
    assert config.schema_version == 1
    with pytest.raises(FileNotFoundError):
        pilot.run_pilot(tmp_path / "missing.toml", tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_cli_exposes_success_failure_and_input_error_exit_codes(
    config_path, tmp_path, capsys
):
    assert main(["run", str(config_path), "--output", str(tmp_path / "success")]) == 0
    assert "Frequenz:" in capsys.readouterr().out
    config_path.write_bytes(EXAMPLE.replace(b"max_nfev = 1000", b"max_nfev = 1"))
    assert main(["run", str(config_path), "--output", str(tmp_path / "failed")]) == 1
    assert "Fehler:" in capsys.readouterr().err
    assert main(["run", str(config_path), "--output", str(tmp_path / "failed")]) == 2
    assert "nicht vollständig" in capsys.readouterr().err


def test_entry_point_works_from_another_directory_without_importing_julia(
    config_path, tmp_path
):
    script = "import sys; from ringdown_sr.cli import main; status=main(sys.argv[1:]); assert 'pysr' not in sys.modules and 'juliacall' not in sys.modules; raise SystemExit(status)"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            "run",
            str(config_path),
            "--output",
            str(tmp_path / "outside"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = read_json(tmp_path / "outside" / "metadata.json")
    assert "ringdown_sr/pilot.py" in manifest["provenance"]["python_source_sha256"]
    assert (
        manifest["provenance"]["project_file_sha256"]["uv.lock"]
        == hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    )


def test_provenance_marks_unavailable_git_without_losing_source_hashes(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(pilot.subprocess, "check_output", missing)
    provenance = pilot._provenance()
    assert provenance["git"] == {
        "available": False,
        "commit": None,
        "dirty": None,
        "changes": [],
    }
    assert provenance["python_source_sha256"]
    assert provenance["project_file_sha256"]["uv.lock"]


def test_provenance_distinguishes_clean_commit_dirty_sources_and_other_repositories(
    tmp_path, monkeypatch
):
    if shutil.which("git") is None:
        pytest.skip("Git is unavailable")
    root = tmp_path / "checkout"
    package = root / "src" / "ringdown_sr"
    package.mkdir(parents=True)
    source = package / "pilot.py"
    source.write_text("# first source\n", encoding="utf-8")

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, text=True
        ).strip()

    git("init")
    git(
        "-c",
        "user.name=Test Author",
        "-c",
        "user.email=test@example.invalid",
        "add",
        "src",
    )
    git(
        "-c",
        "user.name=Test Author",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "test fixture",
    )
    monkeypatch.setattr(pilot, "__file__", str(source))
    clean = pilot._provenance()
    assert clean["git"]["commit"] == git("rev-parse", "HEAD")
    assert clean["git"]["dirty"] is False
    source.write_text("# changed source\n", encoding="utf-8")
    dirty = pilot._provenance()
    assert dirty["git"]["dirty"] is True
    assert dirty["git"]["changes"][0].startswith(" M ")
    assert dirty["python_source_set_sha256"] != clean["python_source_set_sha256"]
    installed = root / "unrelated" / "site-packages" / "ringdown_sr"
    installed.mkdir(parents=True)
    (installed / "pilot.py").write_text("# installed source\n", encoding="utf-8")
    monkeypatch.setattr(pilot, "__file__", str(installed / "pilot.py"))
    assert pilot._provenance()["git"]["available"] is False
