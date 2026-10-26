"""Probe input integrity, fixed starts, scaling and retained failure evidence."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/probe_symbolic_numerics.py"
SPEC = importlib.util.spec_from_file_location("probe_symbolic_numerics", PATH)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def write(path, value):
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def seal(source):
    write(
        source / "checksums.json",
        {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in PROBE.SOURCE_FILES
        },
    )


@pytest.fixture
def source(tmp_path):
    directory = tmp_path / "source"
    directory.mkdir()
    for name in PROBE.SOURCE_FILES:
        if name != "inputs.npz":
            write(directory / name, {})
    np.savez(
        directory / "inputs.npz",
        time_s=np.array([0.0, 0.25, 0.5]),
        observed=np.array([0.0, 1.0, 0.0]),
    )
    write(directory / "request.json", {"format": PROBE.FORMAT})
    write(directory / "status.json", {"status": "success"})
    write(
        directory / "pysr_parameters.json",
        {
            "optimizer_algorithm": "BFGS",
            "optimizer_iterations": 20,
            "optimizer_nrestarts": 2,
            "optimizer_f_calls_limit": None,
            "autodiff_backend": None,
            "batching": False,
            "turbo": False,
            "bumper": False,
            "dimensionless_constants_only": False,
        },
    )
    seal(directory)
    return directory


def install_worker(
    monkeypatch, *, fail=False, different=False, mutate=None, worker_environment=None
):
    def run(command, *, stdout):
        directory = Path(command[-1])
        assert command[-2] == "--worker"
        assert Path(command[2]).name == "driver.py"
        assert Path(command[2]).read_bytes() == PATH.read_bytes()
        stdout.write("controlled worker output\n")
        info = {"phase": "failed" if fail else "completed"}
        if worker_environment is not None:
            assert command[3:5] == ["--require-openblas-core", "Haswell"]
            info.update(
                {
                    phase: {"environment": worker_environment}
                    for phase in ("before", "after")
                }
            )
        write(directory / "metadata.json", info)
        if fail:
            write(directory / "result.json", {"cases": ["partial"]})
            return SimpleNamespace(returncode=1)
        write(
            directory / "result.json",
            {
                "format": PROBE.PROBE_FORMAT,
                "cases": [
                    {
                        "name": case[0],
                        "value_hex": "-0x0.0p+0"
                        if different and directory.name == "run-2"
                        else "0x0.0p+0",
                    }
                    for case in PROBE.CASES
                ],
            },
        )
        if mutate:
            mutate()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(PROBE, "_run_worker", run)


def test_source_snapshot_uses_hashed_bytes_and_original_precision(source):
    contents, arrays = PROBE.source_snapshot(source)
    assert len(contents) == 9
    assert all(value.dtype == np.float64 for value in arrays.values())
    np.testing.assert_array_equal(arrays["time_s"], [0.0, 0.25, 0.5])


@pytest.mark.parametrize("name", PROBE.SOURCE_FILES)
def test_changed_source_files_rejected_before_output(source, tmp_path, name):
    (source / name).write_bytes(b"modified")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="checksum mismatch"):
        PROBE.probe(source, output, label="test")
    assert not output.exists()


@pytest.mark.parametrize("kind", ["covariance", "float32", "nan", "shape"])
def test_invalid_arrays_rejected(source, kind):
    arrays = {"time_s": np.array([0.0, 0.25, 0.5]), "observed": np.zeros(3)}
    if kind == "covariance":
        arrays["covariance"] = np.eye(3)
    elif kind == "float32":
        arrays["observed"] = arrays["observed"].astype(np.float32)
    elif kind == "nan":
        arrays["observed"][0] = np.nan
    else:
        arrays["observed"] = np.zeros(2)
    np.savez(source / "inputs.npz", **arrays)
    seal(source)
    with pytest.raises(ValueError):
        PROBE.source_snapshot(source)


def test_unknown_optimizer_policy_rejected(source):
    path = source / "pysr_parameters.json"
    data = json.loads(path.read_text())
    data["optimizer_iterations"] = 100
    write(path, data)
    seal(source)
    with pytest.raises(ValueError, match="policy"):
        PROBE.source_snapshot(source)


def test_source_cannot_escape_through_symlink(source, tmp_path):
    path = source / "metadata.json"
    outside = tmp_path / "outside.json"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        PROBE.source_snapshot(source)


def test_probe_two_workers_exclusive_outputs_and_manifest(
    source, tmp_path, monkeypatch
):
    install_worker(monkeypatch)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    output = tmp_path / "output"
    report = PROBE.probe(source, output, label="test")
    assert report["status"] == "completed"
    assert report["local_results_bitwise_equal"] is True
    assert len(report["runs"]) == 2
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before
    checksums = json.loads((output / "checksums.json").read_text())
    assert "run-2/result.json" in checksums and "source/inputs.npz" in checksums
    for name, expected in checksums.items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    with pytest.raises(FileExistsError):
        PROBE.probe(source, output, label="test")


def test_signed_zero_difference_is_reported_not_hidden(source, tmp_path, monkeypatch):
    install_worker(monkeypatch, different=True)
    report = PROBE.probe(source, tmp_path / "output", label="test")
    assert report["status"] == "completed"
    assert report["local_results_bitwise_equal"] is False


def test_worker_failure_keeps_initial_metadata_partial_results_and_log(
    source, tmp_path, monkeypatch
):
    install_worker(monkeypatch, fail=True)
    output = tmp_path / "output"
    with pytest.raises(RuntimeError, match="worker failed"):
        PROBE.probe(source, output, label="test")
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "failed"
    assert report["initial"]["provenance"]
    assert (output / "run-1/metadata.json").exists()
    assert json.loads((output / "run-1/result.json").read_text())["cases"] == [
        "partial"
    ]
    assert "controlled worker output" in (output / "run-1/worker.log").read_text()
    assert (output / "checksums.json").exists()


def test_source_change_during_run_is_detected(source, tmp_path, monkeypatch):
    install_worker(
        monkeypatch, mutate=lambda: (source / "result.json").write_text("modified")
    )
    with pytest.raises(ValueError):
        PROBE.probe(source, tmp_path / "output", label="test")


@pytest.mark.parametrize("label,nested", [(" ", False), ("ok", True)])
def test_invalid_destination_or_label(source, label, nested, tmp_path):
    output = source / "nested" if nested else tmp_path / "output"
    with pytest.raises(ValueError):
        PROBE.probe(source, output, label=label)
    assert not output.exists()


@pytest.mark.parametrize(
    "model,values,expected",
    [
        ("sine", (-0.5,), lambda t: np.sin(t * -0.5)),
        ("linear", (1.0, -1.0), lambda t: 1.0 + -1.0 * t),
        ("amplitude_sine", (0.5, -1.0), lambda t: 0.5 * np.sin(t * -1.0)),
    ],
)
def test_start_trees_preserve_binary_order(model, values, expected):
    time = np.array([0.0, 0.25, 0.5])
    actual = PROBE.evaluate_tree(PROBE.start_tree(model, values), time)
    np.testing.assert_array_equal(actual, expected(time))


@pytest.mark.parametrize("scale", [1.0, 1e-21])
def test_replay_accepts_correct_prediction_and_rejects_opposite_sign(scale):
    time, observed = np.array([0.0, 1.0]), np.zeros(2)
    tree = {"kind": "constant", "value_hex": float(scale).hex()}
    prediction = np.full(2, scale)
    record = SimpleNamespace(
        prediction=prediction,
        residual=-prediction,
        loss=scale**2,
        sum_loss=scale**2,
        dot_loss=scale**2,
    )
    actual = PROBE.checked_evaluation(record, tree, time, observed)
    assert actual["prediction"][0]["hex"] == scale.hex()
    record.prediction = -prediction
    record.residual = prediction
    with pytest.raises(AssertionError):
        PROBE.checked_evaluation(record, tree, time, observed)


def test_nonfinite_trace_values_are_explicit_json_safe():
    result = [PROBE.number(value) for value in (np.inf, -np.inf, np.nan, -0.0)]
    json.dumps(result, allow_nan=False)
    assert all(value["value"] is None for value in result[:3])
    assert result[-1]["hex"] == "-0x0.0p+0"


def control_environment(*, julia=True):
    paths = [
        "/venv/site-packages/numpy.libs/libnumpy.so",
        "/venv/site-packages/scipy.libs/libscipy.so",
    ]
    if julia:
        paths.append("/venv/julia/install/lib/julia/libopenblas64_.so")
    pools = [
        {
            "filepath": path,
            "architecture": "Haswell",
            "num_threads": 1,
            "user_api": "blas",
            "internal_api": "openblas",
        }
        for path in paths
    ]
    pools.append({"user_api": "openmp", "num_threads": 1})
    return {
        "numerical_libraries": {
            "threadpools": {"status": "available", "details": pools}
        }
    }


def set_control_environment(monkeypatch):
    monkeypatch.setenv("OPENBLAS_CORETYPE", "Haswell")
    for key in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        monkeypatch.setenv(key, "1")


def test_numerical_julia_payload_matches_original_diagnosis():
    # Golden hash from both independently audited 25 October packages.
    assert (
        hashlib.sha256(PROBE.JULIA_SOURCE.encode()).hexdigest()
        == "8481613c28f91e01772f7c30686ba17f0746d4c77e580bfb1af2e597ce4d33df"
    )


def test_native_mode_does_not_require_a_specific_core():
    assert (
        PROBE.verify_blas_control({}, None, require_julia=True)["status"]
        == "not_requested"
    )


def test_control_requires_numpy_scipy_and_julia_pools():
    result = PROBE.verify_blas_control(
        control_environment(), "Haswell", require_julia=True
    )
    assert result["status"] == "verified"
    assert result["roles"] == ["julia", "numpy", "scipy"]
    assert len(result["pools"]) == 3


def test_parent_can_verify_python_pools_before_julia_loads():
    env = control_environment(julia=False)
    assert (
        PROBE.verify_blas_control(env, "Haswell", require_julia=False)["status"]
        == "verified"
    )
    with pytest.raises(ValueError, match="julia"):
        PROBE.verify_blas_control(env, "Haswell", require_julia=True)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_each_wrong_blas_core_is_rejected(index):
    env = control_environment()
    env["numerical_libraries"]["threadpools"]["details"][index]["architecture"] = (
        "SkylakeX"
    )
    with pytest.raises(ValueError, match="does not report Haswell"):
        PROBE.verify_blas_control(env, "Haswell", require_julia=True)


@pytest.mark.parametrize(
    "failure",
    [
        "unavailable",
        "missing_details",
        "unknown_architecture",
        "other_blas",
        "unknown_role",
        "blas_threads",
        "openmp_threads",
    ],
)
def test_unverifiable_or_incomplete_control_is_rejected(failure):
    env = control_environment()
    snap = env["numerical_libraries"]["threadpools"]
    pools = snap["details"]
    if failure == "unavailable":
        snap["status"] = "unavailable"
    elif failure == "missing_details":
        snap["details"] = None
    elif failure == "unknown_architecture":
        pools[2]["architecture"] = None
    elif failure == "other_blas":
        pools[2]["internal_api"] = "mkl"
    elif failure == "unknown_role":
        pools[2]["filepath"] = "/unknown/lib.so"
    else:
        pools[0 if failure == "blas_threads" else 3]["num_threads"] = 2
    with pytest.raises(ValueError):
        PROBE.verify_blas_control(env, "Haswell", require_julia=True)


@pytest.mark.parametrize(
    "missing",
    [
        "OPENBLAS_CORETYPE",
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ],
)
def test_control_request_must_be_set_before_parent_starts(
    source, tmp_path, monkeypatch, missing
):
    set_control_environment(monkeypatch)
    monkeypatch.delenv(missing)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="before starting"):
        PROBE.probe(source, output, label="test", required_openblas_core="Haswell")
    assert not output.exists()


def test_control_flag_reaches_workers_and_actual_pools_are_rechecked(
    source, tmp_path, monkeypatch
):
    set_control_environment(monkeypatch)
    original = PROBE.metadata

    def controlled_metadata(**kwargs):
        info = original(**kwargs)
        info["environment"].update(control_environment(julia=False))
        return info

    monkeypatch.setattr(PROBE, "metadata", controlled_metadata)
    install_worker(monkeypatch, worker_environment=control_environment())
    result = PROBE.probe(
        source, tmp_path / "output", label="test", required_openblas_core="Haswell"
    )
    assert result["required_openblas_core"] == "Haswell"
    assert result["initial"]["openblas_coretype_environment"] == "Haswell"
    assert result["initial"]["blas_control"]["status"] == "verified"


def test_worker_success_without_actual_julia_core_is_rejected(
    source, tmp_path, monkeypatch
):
    set_control_environment(monkeypatch)
    original = PROBE.metadata

    def controlled_metadata(**kwargs):
        info = original(**kwargs)
        info["environment"].update(control_environment(julia=False))
        return info

    monkeypatch.setattr(PROBE, "metadata", controlled_metadata)
    env = copy.deepcopy(control_environment())
    env["numerical_libraries"]["threadpools"]["details"][2]["architecture"] = "Zen"
    install_worker(monkeypatch, worker_environment=env)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="does not report Haswell"):
        PROBE.probe(source, output, label="test", required_openblas_core="Haswell")
    result = json.loads((output / "report.json").read_text())
    assert result["status"] == "failed"
    assert result["initial"]["blas_control"]["status"] == "verified"
    assert (output / "run-1/metadata.json").exists()
