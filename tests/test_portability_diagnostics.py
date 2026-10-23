"""Check evidence identity, tiny numerical differences and safe diagnostic I/O."""

import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "portability_diagnostics", ROOT / "scripts/diagnose_symbolic_pilot.py"
)
DIAG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAG)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(DIAG.json_bytes(data))


def hashes(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def source(tmp_path):
    """Build small independent stored artifacts, with no project computation mocks."""
    root = tmp_path / "stored"
    provenance = {
        "git": {
            "available": True,
            "commit": "recorded-commit",
            "dirty": False,
            "changes": [],
        }
    }
    environment = {
        "platform": "recorded-platform",
        "packages": {"numpy": "recorded-version"},
    }
    for case in DIAG.CASES:
        base = root / case
        base.mkdir(parents=True)
        reference = base / "reference"
        reference.mkdir()
        time = np.array([0.0, 0.25, 0.5])
        signal = np.array([1.0, 0.5, -0.25])
        noise = np.array([0.1, -0.1, 0.2])
        observed = signal + noise
        matrix = np.array([[2.0, 0.5, 0.0], [0.5, 2.0, 0.5], [0.0, 0.5, 2.0]])
        np.savez(
            reference / "comparison_inputs.npz",
            time_s=time,
            signal=signal,
            noise=noise,
            observed=observed,
            covariance_true=matrix,
            covariance_estimated=matrix * 2,
        )
        for role in ("train", "validation", "check"):
            np.savetxt(reference / f"background_{role}.csv", np.eye(3), delimiter=",")
        write(
            reference / "metadata.json",
            {
                "status": "success",
                "provenance": provenance,
                "environment": environment,
                "random": {"seed": 42, "states": [1, 2, 3]},
            },
        )
        write(
            reference / "result.json",
            {"status": "success", "covariance_estimation": {"alpha_selected": 0.5}},
        )
        result = {
            "schema_version": 3,
            "status": "success",
            "shared_inputs_file": "reference/comparison_inputs.npz",
            "symbolic_arms": {},
        }
        for arm in DIAG.ARMS:
            directory = base / "symbolic" / arm
            directory.mkdir(parents=True)
            inputs = {"time_s": time, "observed": observed}
            if arm != "ordinary":
                inputs["covariance"] = (
                    matrix if arm == "known_covariance" else matrix * 2
                )
            np.savez(directory / "inputs.npz", **inputs)
            write(directory / "metadata_initial.json", {"provenance": provenance})
            write(
                directory / "metadata.json",
                {
                    "provenance": provenance,
                    "worker_provenance": provenance,
                    "environment": environment,
                    "environment_after_search": environment,
                    "adapter_source_sha256": {"adapter": "old-source"},
                    "worker_adapter_source_sha256": {"adapter": "old-source"},
                    "julia_version": "recorded-julia",
                    "symbolic_regression_version": "recorded-backend",
                },
            )
            write(
                directory / "request.json", {"budget": {"seed": 123, "niterations": 1}}
            )
            write(
                directory / "pysr_parameters.json",
                {"random_state": 123, "output_directory": "/original/path"},
            )
            write(
                directory / "backend_options.json",
                [
                    {"name": "seed", "type": "Int64", "value": "456"},
                    {
                        "name": "output_directory",
                        "type": "String",
                        "value": "/original/path",
                    },
                ],
            )
            write(
                directory / "result.json",
                {
                    "selected_index": 0,
                    "rng": {"backend_seed": 456, "state_status": "not_exported"},
                    "baseline_loss": 1.0,
                    "use_baseline": True,
                    "cost_normalization": 1.0,
                    "zero_expression_loss": 1.0,
                    "zero_expression_loss_status": "finite",
                    "candidates": [
                        {
                            "tree": {"value_hex": "0x0.0p+0"},
                            "loss": 1.0,
                            "complexity": 1,
                            "prediction": [0.0, 0.0, 0.0],
                            "residual": observed.tolist(),
                        }
                    ],
                },
            )
            result["symbolic_arms"][arm] = {
                "status": "success",
                "metrics": {"q_true_per_sample": 1.0},
            }
        write(base / "result.json", result)
        write(base / "resolved_config.json", {"schema_version": 3, "seed": 42})
        write(
            base / "metadata.json",
            {
                "schema_version": 3,
                "status": "success",
                "provenance": provenance,
                "environment": environment,
                "artifact_sha256": hashes(base),
            },
        )
    return root


def test_export_is_read_only_and_keeps_recorded_environment(
    source, tmp_path, monkeypatch
):
    before = hashes(source)
    monkeypatch.setattr(
        DIAG.platform,
        "platform",
        lambda: pytest.fail("Must not recapture the search host"),
    )
    report = DIAG.export(source, tmp_path / "bundle", "host-a")
    assert hashes(source) == before
    assert report["exporter"]["role"].startswith("export_only")
    assert (
        report["runs"]["white"]["recorded_environment"]["pilot"]["platform"]
        == "recorded-platform"
    )
    loaded, arrays = DIAG.load_bundle(tmp_path / "bundle")
    assert loaded == report and len(arrays) == 46
    with np.load(source / "white/reference/comparison_inputs.npz") as original:
        assert (
            arrays["white.shared.observed"].tobytes() == original["observed"].tobytes()
        )
    with pytest.raises(FileExistsError):
        DIAG.export(source, tmp_path / "bundle", "host-a")


def test_identical_exports_and_operational_paths(source, tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    DIAG.export(source, left, "a")
    DIAG.export(source, right, "b")
    report, _ = DIAG.load_bundle(right)
    arm = report["runs"]["white"]["arms"]["ordinary"]
    arm["pysr_parameters"]["output_directory"] = "/different/host/path"
    arm["backend_options_repr"]["output_directory"]["value"] = "/different/host/path"
    write(right / "report.json", report)
    write(
        right / "checksums.json",
        {
            name: DIAG.digest((right / name).read_bytes())
            for name in ("report.json", "arrays.npz")
        },
    )
    compared = DIAG.compare(left, right, tmp_path / "comparison.json")
    for run in compared["runs"].values():
        assert all(item["bitwise_equal"] for item in run["arrays"].values())
    options = compared["runs"]["white"]["arms"]["ordinary"]
    assert options["pysr_parameters"] == options["backend_options_repr"] == []
    assert options["pysr_parameters_operational"] == ["/output_directory"]
    with pytest.raises(FileExistsError):
        DIAG.compare(left, right, tmp_path / "comparison.json")


def test_rng_options_sources_and_environment_are_separate(source, tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    DIAG.export(source, left, "a")
    DIAG.export(source, right, "b")
    report, _ = DIAG.load_bundle(right)
    case = report["runs"]["white"]
    case["configuration"]["seed"] = 43
    case["reference_rng"]["seed"] = 43
    arm = case["arms"]["known_covariance"]
    arm["rng"]["backend_seed"] = 457
    arm["request"]["budget"]["seed"] = 124
    arm["pysr_parameters"]["random_state"] = 124
    arm["backend_options_repr"]["seed"]["value"] = "457"
    arm["adapter_sources"]["adapter_source_sha256"]["adapter"] = "changed"
    arm["recorded_environment"]["before_fit"]["platform"] = "different"
    arm["front"][0]["loss"] = 0.5
    write(right / "report.json", report)
    write(
        right / "checksums.json",
        {
            name: DIAG.digest((right / name).read_bytes())
            for name in ("report.json", "arrays.npz")
        },
    )
    compared = DIAG.compare(left, right, tmp_path / "comparison.json")["runs"]["white"]
    assert compared["configuration"] == compared["reference_rng"] == ["/seed"]
    for name in (
        "rng",
        "request",
        "pysr_parameters",
        "backend_options_repr",
        "adapter_sources",
        "recorded_environment",
        "front",
    ):
        assert compared["arms"]["known_covariance"][name]
    assert compared["arms"]["ordinary"]["rng"] == []


@pytest.mark.parametrize("scale", [1.0, 1e-21, 1e-150])
def test_one_ulp_difference_is_visible_without_absolute_floor(scale):
    a = np.array([scale, 0.0])
    b = np.array([np.nextafter(scale, np.inf), 0.0])
    result = DIAG.array_difference(a, b)
    assert not result["bitwise_equal"] and result["elements_with_different_values"] == 1
    assert result["max_absolute_difference"] == b[0] - a[0] > 0
    assert result["max_normalized_difference"] > 0


def test_bundle_comparison_locates_one_tiny_input_difference(source, tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    DIAG.export(source, left, "a")
    DIAG.export(source, right, "b")
    report, arrays = DIAG.load_bundle(right)
    key = "white.shared.noise"
    arrays[key][0] = np.nextafter(arrays[key][0], np.inf)
    report["runs"]["white"]["arrays"][key] = DIAG.fingerprint(arrays[key])
    np.savez_compressed(right / "arrays.npz", **arrays)
    write(right / "report.json", report)
    write(
        right / "checksums.json",
        {
            name: DIAG.digest((right / name).read_bytes())
            for name in ("report.json", "arrays.npz")
        },
    )
    comparison = DIAG.compare(left, right, tmp_path / "comparison.json")
    changed = {
        name
        for run in comparison["runs"].values()
        for name, info in run["arrays"].items()
        if not info["bitwise_equal"]
    }
    assert changed == {key}
    assert (
        comparison["runs"]["white"]["arrays"][key]["elements_with_different_bits"] == 1
    )


def test_byte_order_signed_zero_shape_and_overflow():
    a = np.array([1.0, -0.0], dtype="<f8")
    assert DIAG.fingerprint(a) == DIAG.fingerprint(a.astype(">f8"))
    result = DIAG.array_difference(a, np.array([1.0, 0.0]))
    assert result["numeric_equal"] and not result["bitwise_equal"]
    assert (
        result["elements_with_different_bits"] == 1
        and result["max_absolute_difference"] == 0
    )
    assert DIAG.array_difference(a, a.reshape(1, 2))["status"] == "shape_mismatch"
    large = DIAG.array_difference(np.array([1e308]), np.array([-1e308]))
    assert (
        large["max_normalized_difference"] == 2
        and large["max_absolute_difference"] is None
    )


@pytest.mark.parametrize(
    "values",
    [
        np.array([np.nan]),
        np.array([1.0], dtype=np.float32),
        np.array([True]),
        np.array(1.0),
    ],
)
def test_unsupported_or_nonfinite_arrays_are_rejected(values):
    with pytest.raises(ValueError):
        DIAG.canonical(values)


def test_corrupt_source_is_rejected_before_output_reservation(source, tmp_path):
    (source / "white/reference/background_train.csv").write_text("changed")
    with pytest.raises(ValueError, match="checksum"):
        DIAG.export(source, tmp_path / "absent", "host")
    assert not (tmp_path / "absent").exists()


def test_bundle_corruption_and_descriptor_mismatch(source, tmp_path):
    directory = tmp_path / "bundle"
    DIAG.export(source, directory, "host")
    original = (directory / "arrays.npz").read_bytes()
    (directory / "arrays.npz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        DIAG.load_bundle(directory)
    (directory / "arrays.npz").write_bytes(original)
    report = DIAG.read_json((directory / "report.json").read_bytes())
    report["runs"]["white"]["arrays"]["white.shared.signal"]["sha256"] = "wrong"
    write(directory / "report.json", report)
    write(
        directory / "checksums.json",
        {
            name: DIAG.digest((directory / name).read_bytes())
            for name in ("report.json", "arrays.npz")
        },
    )
    with pytest.raises(ValueError, match="descriptors"):
        DIAG.load_bundle(directory)


def test_no_writes_inside_evidence_and_invalid_cli(source, tmp_path):
    with pytest.raises(ValueError, match="outside"):
        DIAG.export(source, source / "new", "host")
    DIAG.export(source, tmp_path / "bundle", "host")
    with pytest.raises(ValueError, match="outside"):
        DIAG.compare(
            tmp_path / "bundle", tmp_path / "bundle", tmp_path / "bundle/compare.json"
        )
    with pytest.raises(SystemExit) as error:
        DIAG.main(
            ["export", str(source), "--label", "host", "--output", str(source / "bad")]
        )
    assert error.value.code == 2


def test_escape_path_and_empty_label(source, tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        DIAG.inside(source, "../outside")
    with pytest.raises(ValueError, match="label"):
        DIAG.export(source, tmp_path / "absent", " ")
    assert not (tmp_path / "absent").exists()
    DIAG.export(source, tmp_path / "bundle", "host")
    manifest = tmp_path / "bundle/checksums.json"
    external = tmp_path / "external-manifest.json"
    external.write_bytes(manifest.read_bytes())
    manifest.unlink()
    manifest.symlink_to(external)
    with pytest.raises(ValueError, match="escapes"):
        DIAG.load_bundle(tmp_path / "bundle")
    metadata = source / "white/metadata.json"
    external = tmp_path / "external-metadata.json"
    external.write_bytes(metadata.read_bytes())
    metadata.unlink()
    metadata.symlink_to(external)
    with pytest.raises(ValueError, match="escapes"):
        DIAG.export(source, tmp_path / "absent", "host")
    assert not (tmp_path / "absent").exists()
