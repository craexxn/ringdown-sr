"""Small analytical and storage fixtures for paired acquisition preparation."""

import hashlib
import os
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_followup_inputs as inputs


def test_continuous_ar1_chunks_match_explicit_scalar_recurrence():
    sigma, rho, count = 0.7, 0.65, 43
    expected_rng = np.random.Generator(np.random.PCG64(77))
    normals = expected_rng.standard_normal(count)
    expected = np.empty(count)
    expected[0] = sigma * normals[0]
    for index in range(1, count):
        expected[index] = (
            rho * expected[index - 1] + sigma * np.sqrt(1 - rho**2) * normals[index]
        )
    for chunk in (1, 7, 16, 100):
        rng = np.random.Generator(np.random.PCG64(77))
        actual = np.concatenate(
            list(
                inputs.continuous_chunks(
                    rng, count, sigma=sigma, rho=rho, chunk_samples=chunk
                )
            )
        )
        np.testing.assert_allclose(actual, expected, atol=2e-16, rtol=3e-15)
        assert rng.bit_generator.state == expected_rng.bit_generator.state
        # The prefix is unaffected by how much additional background is requested.
        prefix = np.concatenate(
            list(
                inputs.continuous_chunks(
                    np.random.Generator(np.random.PCG64(77)),
                    21,
                    sigma=sigma,
                    rho=rho,
                    chunk_samples=chunk,
                )
            )
        )
        np.testing.assert_array_equal(actual[:21], prefix)


def test_continuous_white_is_unscaled_standard_normal_sequence():
    expected_rng = np.random.Generator(np.random.PCG64(78))
    expected = 0.3 * expected_rng.standard_normal(23)
    actual_rng = np.random.Generator(np.random.PCG64(78))
    actual = np.concatenate(
        list(
            inputs.continuous_chunks(actual_rng, 23, sigma=0.3, rho=0, chunk_samples=7)
        )
    )
    np.testing.assert_array_equal(actual, expected)
    assert actual_rng.bit_generator.state == expected_rng.bit_generator.state


def test_union_noise_covariance_follows_transition_product():
    class BasisGenerator:
        def __init__(self, basis):
            self.basis = basis

        def standard_normal(self, count, dtype):
            assert count == len(self.basis) and dtype == np.float64
            return self.basis.copy()

    times = np.array([0.0, 0.2, 0.4, 1.0]) / inputs.SAMPLE_RATE
    columns = [
        inputs.union_noise(BasisGenerator(basis), times, sigma=0.8, rho=0.65)
        for basis in np.eye(4)
    ]
    factor = np.column_stack(columns)
    expected = 0.8**2 * 0.65 ** (
        inputs.SAMPLE_RATE * np.abs(times[:, None] - times[None, :])
    )
    np.testing.assert_allclose(factor @ factor.T, expected, rtol=5e-15, atol=2e-16)


def test_single_seed_table_and_complete_case_inventories():
    science = inputs.case_specs()
    diagnostics = inputs.case_specs(purpose="diagnostic")
    technical = inputs.case_specs(purpose="technical")
    assert len(science) == 26 and len(diagnostics) == 12 and len(technical) == 1
    assert [case["id"] for case in science[:4]] == [
        "ar1-01",
        "white-01",
        "ar1-02",
        "white-02",
    ]
    assert sum(len(case["search_seeds"]) * len(inputs.ARMS) for case in science) == 624
    assert all(case["search_seeds"] == [] for case in diagnostics)
    assert len(technical[0]["search_seeds"]) == 1
    assert technical[0]["niterations"] == 10
    table = inputs._seed_table()
    assert table["new_initial_rng_state_collisions"] == 0
    assert inputs.initial_rng_states() == {"checked_states": 159, "collisions": 0}


@pytest.fixture
def tiny_protocol(monkeypatch):
    # Exercise the full storage contract using 4 Hz, unrelated fixture seeds,
    # and only 16384 raw samples, never the prospective scientific inputs.
    monkeypatch.setattr(inputs, "SAMPLE_RATE", 4)
    monkeypatch.setattr(
        inputs,
        "_seed_table",
        lambda: {
            "reserved": {
                "acquisition_jitter": 101,
                "evaluation_grid": 102,
                "technical_noise": 103,
                "technical_background": 104,
                "technical_search": 105,
            }
        },
    )
    monkeypatch.setattr(inputs, "_protocol", lambda consumed: {"fixture": True})
    monkeypatch.setattr(inputs, "_freeze_sources", lambda consumed: {"fixture": True})
    monkeypatch.setattr(inputs, "initial_rng_states", lambda: {"fixture": True})


def test_small_input_roundtrip_is_lazy_and_role_bound(tmp_path, tiny_protocol):
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    assert prepared.manifest["purpose"] == "technical"
    assert prepared.cases["technical-ar1"]["search_seeds"] == [105]
    assert "arrays" not in prepared.cases["technical-ar1"]
    assert prepared.call["status"] == "completed"
    assert (tmp_path / "inputs-call.json").is_file()
    consumed = publication.Consumption(publication.Deadline(30))
    replay = inputs.verify_inputs(prepared.root, consumed, regenerate=True)
    case = inputs.read_case(replay, "technical-ar1", consumed)
    assert isinstance(case.train_path, Path)
    assert not any(isinstance(value, np.memmap) for value in case.arrays.values())
    assert all(
        not name.endswith("background_train.npy") for name in map(str, consumed.files)
    )
    uniform = inputs.arm_arrays(replay, case, "ordinary")
    jitter = inputs.arm_arrays(replay, case, "jitter_known_covariance")
    np.testing.assert_array_equal(uniform["noise"][[0, -1]], jitter["noise"][[0, -1]])
    np.testing.assert_array_equal(
        uniform["irregular_time_s"], jitter["irregular_time_s"]
    )
    assert uniform["covariance"] is None
    assert jitter["covariance"] is jitter["covariance_true"]
    assert not (prepared.root / inputs.LOCK).exists()
    with inputs.open_training(case) as train:
        assert train.shape == (4 * 4096,)
        assert not train.flags.writeable


def test_frozen_grids_preserve_geometry_and_reject_truth_overlap(
    tmp_path, tiny_protocol
):
    common, record = inputs.derive_common_inputs()
    uniform, jitter = common["time_s"], common["jitter_time_s"]
    assert len(record["union_time_s"]) == 254
    assert np.all(np.diff(jitter) >= 0.5 / inputs.SAMPLE_RATE)
    np.testing.assert_array_equal(uniform[[0, -1]], jitter[[0, -1]])
    assert not np.isin(jitter[1:-1], uniform).any()
    assert not np.isin(common["irregular_time_s"], jitter).any()
    assert not np.any((common["irregular_time_s"] * 32768) % 1 == 0)
    assert max(record["reference_maximum_errors"].values()) < 1e-13


def test_input_preparation_is_exclusive_and_failed_generation_stays_locked(
    tmp_path, tiny_protocol, monkeypatch
):
    output = tmp_path / "inputs"
    original = inputs.continuous_chunks

    def interrupted(*args, **kwargs):
        yield next(original(*args, **kwargs))
        raise InterruptedError("fixture interruption")

    monkeypatch.setattr(inputs, "continuous_chunks", interrupted)
    with pytest.raises(InterruptedError, match="fixture interruption"):
        inputs.prepare_inputs(output, purpose="technical")
    assert (output / inputs.LOCK).exists()
    assert not (output / "preparation.json").exists()
    call = sources.read_json((tmp_path / "inputs-call.json").read_bytes())
    assert call["status"] == "aborted" and call["wall_seconds"] >= 0
    with pytest.raises(ValueError):
        inputs.prepare_inputs(output, purpose="technical")


def test_stream_snapshot_detects_changed_bytes_even_with_restored_mtime(tmp_path):
    path = tmp_path / "raw.npy"
    path.write_bytes(b"original")
    original_stat = path.stat()
    consumed = publication.Consumption(publication.Deadline(30))
    inputs._hold_file(path, hashlib.sha256(b"original").hexdigest(), consumed)
    path.write_bytes(b"modified")
    os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    with pytest.raises(ValueError, match="changed after consumption"):
        consumed.check()


def test_symlink_and_extra_payload_are_rejected(tmp_path, tiny_protocol):
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    extra = prepared.root / "unexpected"
    extra.write_text("not a bound input")
    with pytest.raises(ValueError, match="inventory"):
        inputs.verify_inputs(prepared.root)
    extra.unlink()
    case_root = prepared.root / "cases" / "technical-ar1"
    train = case_root / "background_train.npy"
    moved = tmp_path / "moved.npy"
    train.rename(moved)
    train.symlink_to(moved)
    with pytest.raises(ValueError, match="symbolic-link"):
        inputs.verify_inputs(prepared.root)


@pytest.mark.parametrize("raw_failure", [False, True])
def test_covariance_failure_marks_only_its_arm(
    tmp_path, tiny_protocol, monkeypatch, raw_failure
):
    original = inputs.covariance.estimate_from_raw

    def fail_short(raw, validation, **kwargs):
        if kwargs["n_train"] < 10:
            raise inputs.CovarianceEstimationError(
                "fixture rejected short estimate", raw_covariance=raw
            )
        return original(raw, validation, **kwargs)

    if raw_failure:
        original_raw = inputs.covariance.empirical_from_series

        def fail_raw_short(series, **kwargs):
            if series.size < 1280:
                raise inputs.CovarianceEstimationError("fixture raw moment overflow")
            return original_raw(series, **kwargs)

        monkeypatch.setattr(inputs.covariance, "empirical_from_series", fail_raw_short)
    else:
        monkeypatch.setattr(inputs.covariance, "estimate_from_raw", fail_short)
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    case = inputs.read_case(prepared, "technical-ar1")
    assert case.record["status"] == "covariance_failed"
    assert case.record["arm_status"]["estimated_64s"] == "not_run"
    assert all(
        case.record["arm_status"][arm] == "ready"
        for arm in inputs.ARMS
        if arm != "estimated_64s"
    )
    assert (
        case.record["covariance_estimation"]["estimated_64s"]["method"]
        == inputs.covariance.METHOD
    )
    assert inputs.arm_arrays(prepared, case, "estimated_64s")["covariance"] is None
    assert ("covariance_raw_64s" in case.arrays) is not raw_failure
