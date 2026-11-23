"""Independent N103 geometry, role, prefix and artifact-integrity references."""

import copy
import hashlib
import json
import os
from pathlib import Path

import mpmath as mp
import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import main_study_inputs as inputs


def fixture_table():
    return {
        "reserved": {
            "table_generator": 100,
            "evaluation_grid": 101,
            "support_grid": 102,
            "technical_noise": 103,
            "technical_background": 104,
            "technical_search": 105,
        },
        "scientific_cases": [],
        "technical_cases": [
            {
                "id": signal_id + "-technical-ar1",
                "signal_id": signal_id,
                "noise_model": "ar1",
                "block": 0,
                "noise_seed": 110 + 3 * index,
                "background_seed": 111 + 3 * index,
                "search_seeds": [112 + 3 * index],
            }
            for index, signal_id in enumerate(inputs.SIGNALS)
        ],
    }


@pytest.fixture
def technical_table(monkeypatch):
    table = fixture_table()
    monkeypatch.setattr(inputs, "_seed_table", lambda: copy.deepcopy(table))
    return table


@pytest.fixture
def tiny_protocol(monkeypatch, technical_table):
    # Keep the N103 matrix and historical arm names, using a fixture-only
    # 64-Hz rate and unrelated seeds. This is not a main-study input series.
    monkeypatch.setattr(inputs, "SAMPLE_RATE", 64)
    monkeypatch.setattr(inputs, "EVALUATION_POINTS", 8)
    monkeypatch.setattr(inputs, "_protocol", lambda consumed: {"fixture": True})
    monkeypatch.setattr(inputs, "_freeze_sources", lambda consumed: {"fixture": True})


def test_frozen_inventory_and_seed_roles_are_complete():
    specs = inputs.case_specs()
    technical = inputs.case_specs(purpose="technical")
    assert len(specs) == 80 and len(technical) == 2
    assert [spec["signal_id"] for spec in specs[:40]] == ["signal_200_4ms"] * 40
    assert [spec["id"] for spec in specs[:4]] == [
        "signal_200_4ms-ar1-01",
        "signal_200_4ms-white-01",
        "signal_200_4ms-ar1-02",
        "signal_200_4ms-white-02",
    ]
    assert sum(len(spec["search_seeds"]) * len(inputs.ARMS) for spec in specs) == 1280
    assert all(spec["sampling"]["n_samples"] == 103 for spec in (*specs, *technical))
    assert all(spec["niterations"] == 1000 for spec in specs)
    assert all(spec["niterations"] == 10 for spec in technical)
    values = [
        value
        for spec in (*specs, *technical)
        for value in (
            spec["noise_seed"],
            spec["background_seed"],
            *spec["search_seeds"],
        )
    ]
    assert len(values) == len(set(values)) == 486
    assert inputs.initial_rng_states() == {"checked_states": 334, "collisions": 0}
    for seconds, rows, tail in ((64, 2545, 9), (4096, 162885, 61)):
        assert divmod(seconds * 4096, 103) == (rows, tail)
    assert inputs.COVARIANCE_CHUNK_SAMPLES == (65536 // 103) * 103 == 65508


def test_rng_collision_stops_before_any_input_generation(
    tmp_path, tiny_protocol, technical_table, monkeypatch
):
    technical_table["technical_cases"][0]["noise_seed"] = technical_table["reserved"][
        "evaluation_grid"
    ]
    generated = []

    def forbidden_generation(*args, **kwargs):
        generated.append(True)
        raise AssertionError("Data generation preceded the random-state check.")

    monkeypatch.setattr(inputs, "derive_common_inputs", forbidden_generation)
    monkeypatch.setattr(inputs, "derive_case", forbidden_generation)
    output = tmp_path / "inputs"
    with pytest.raises(ValueError, match="random-stream initial states collide"):
        inputs.prepare_inputs(output, purpose="technical")
    assert not generated
    assert not output.exists()


def test_n103_main_and_support_axes_have_distinct_contracts(technical_table):
    common, record = inputs.derive_common_inputs()
    training = common["time_s"]
    np.testing.assert_array_equal(training, np.arange(103) / 4096)
    assert training[-1] == 0.02490234375
    assert training[-1] < 0.025
    assert record["domain_interval_rational"] == [[0, 1], [1, 40]]
    assert record["training_interval_rational"] == [[0, 1], [102, 4096]]
    for name, end in (("main_time_s", 0.025), ("support_time_s", training[-1])):
        values = common[name]
        assert len(values) == 1024 and not np.isin(values, training).any()
        boundaries = np.arange(1025) / 1024 * end
        assert np.all(values > boundaries[:-1]) and np.all(values < boundaries[1:])
        assert not values.flags.writeable
    assert not np.array_equal(common["main_time_s"], common["support_time_s"])
    np.testing.assert_array_equal(common["endpoint_time_s"], [0.0, 0.025])
    assert max(record["reference_maximum_errors"].values()) < 1e-13


@pytest.mark.parametrize(
    "signal_id,frequency,decay",
    [("signal_200_4ms", 200, 0.004), ("signal_250_6ms", 250, 0.006)],
)
def test_signal_specific_truth_matches_independent_high_precision_formula(
    technical_table, signal_id, frequency, decay
):
    common, _ = inputs.derive_common_inputs()
    selected = inputs.common_for_case(common, {"signal_id": signal_id})
    with mp.workdps(100):
        expected = [
            float(
                mp.exp(-mp.mpf(float(t)) / mp.mpf(decay))
                * mp.cos(2 * mp.pi * frequency * mp.mpf(float(t)))
            )
            for t in selected["time_s"]
        ]
    np.testing.assert_allclose(selected["signal"], expected, rtol=0, atol=1e-15)
    assert selected["signal"][0] == 1.0
    assert not any("__" in key for key in selected)


def test_grid_generation_rejects_closed_strata_before_any_input_write(
    technical_table, monkeypatch
):
    class ClosedGenerator:
        bit_generator = type("State", (), {"state": {"fixture": True}})()

        def random(self):
            return 0.0

    monkeypatch.setattr(inputs.np.random, "Generator", lambda unused: ClosedGenerator())
    with pytest.raises(ValueError, match="open evaluation axis"):
        inputs.derive_common_inputs()


def test_n103_chunk_boundaries_preserve_stationary_scalar_ar1():
    seed, sigma, rho, count = 717, 0.05, 0.65, 2 * 103 + 9
    rng = np.random.Generator(np.random.PCG64(seed))
    z = rng.standard_normal(count)
    expected = np.empty(count)
    expected[0] = sigma * z[0]
    for index in range(1, count):
        expected[index] = (
            rho * expected[index - 1] + sigma * np.sqrt(1 - rho * rho) * z[index]
        )
    actual_rng = np.random.Generator(np.random.PCG64(seed))
    actual = np.concatenate(
        list(
            inputs.continuous_chunks(
                actual_rng, count, sigma=sigma, rho=rho, chunk_samples=103
            )
        )
    )
    np.testing.assert_allclose(actual, expected, rtol=2e-15, atol=2e-17)
    assert actual_rng.bit_generator.state == rng.bit_generator.state


def test_small_n103_roundtrip_keeps_prefix_tails_and_all_four_arms(
    tmp_path, tiny_protocol
):
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    assert prepared.manifest["planned_search_calls"] == 8
    assert prepared.call["status"] == "completed"
    assert prepared.call["cpu_scope"] == "self_plus_reaped_children"
    assert prepared.call["cpu_measurement_complete"] is True
    consumed = publication.Consumption(publication.Deadline(120))
    replay = inputs.verify_inputs(prepared.root, consumed, regenerate=True)
    for case_id in replay.cases:
        case = inputs.read_case(replay, case_id, consumed)
        assert isinstance(case.train_path, Path)
        assert not any(isinstance(value, np.memmap) for value in case.arrays.values())
        with inputs.open_training(case) as train:
            assert train.shape == (262144,) and not train.flags.writeable
            for seconds, arm in zip((64, 4096), inputs.ESTIMATED_ARMS, strict=True):
                count = seconds * 64
                rows, tail = divmod(count, 103)
                prefix = case.record["background_prefixes"][arm]
                assert prefix["sample_stop"] == count
                assert prefix["estimation_sample_stop"] == rows * 103
                assert prefix["archived_unused_tail_samples"] == tail
                # Direct dense matrix multiplication is independent of the streamed
                # BLAS triangular accumulation used by production preparation.
                windows = np.array(train[: rows * 103]).reshape(rows, 103)
                expected = (windows.T @ windows) / rows
                np.testing.assert_allclose(
                    case.arrays[f"covariance_raw_{seconds}s"],
                    expected,
                    rtol=1e-13,
                    atol=3e-18,
                )
        ordinary = inputs.arm_arrays(replay, case, "ordinary")
        known = inputs.arm_arrays(replay, case, "known_covariance")
        assert ordinary["covariance"] is None
        assert known["covariance"] is known["covariance_true"]
        np.testing.assert_array_equal(ordinary["main_time_s"], known["main_time_s"])
        np.testing.assert_array_equal(
            ordinary["observed"], ordinary["signal"] + ordinary["noise"]
        )
        indices = np.arange(103)
        np.testing.assert_allclose(
            known["covariance"],
            0.05**2 * 0.65 ** np.abs(indices[:, None] - indices[None, :]),
            rtol=2e-15,
            atol=0,
        )
    assert not any(
        name.endswith("background_train.npy") for name in map(str, consumed.files)
    )
    assert not (prepared.root / inputs.LOCK).exists()


def test_preparation_failure_remains_locked_with_partial_costs(
    tmp_path, tiny_protocol, monkeypatch
):
    original = inputs.continuous_chunks

    def interrupted(*args, **kwargs):
        yield next(original(*args, **kwargs))
        raise InterruptedError("fixture interruption")

    monkeypatch.setattr(inputs, "continuous_chunks", interrupted)
    output = tmp_path / "inputs"
    with pytest.raises(InterruptedError, match="fixture interruption"):
        inputs.prepare_inputs(output, purpose="technical")
    assert (output / inputs.LOCK).is_file()
    call = sources.read_json((tmp_path / "inputs-call.json").read_bytes())
    assert call["status"] == "aborted" and call["wall_seconds"] >= 0
    assert call["cpu_scope"] == "self_plus_reaped_children"
    assert call["cpu_measurement_complete"] is False
    with pytest.raises(ValueError):
        inputs.prepare_inputs(output, purpose="technical")


@pytest.mark.parametrize("raw_failure", [False, True])
def test_failed_short_estimator_never_replaces_its_weighting(
    tmp_path, tiny_protocol, monkeypatch, raw_failure
):
    original = inputs.covariance.estimate_from_raw

    def fail_short(raw, validation, **kwargs):
        if kwargs["n_train"] < 50:
            raise inputs.CovarianceEstimationError(
                "fixture short estimate failure", raw_covariance=raw
            )
        return original(raw, validation, **kwargs)

    if raw_failure:
        original_raw = inputs.covariance.empirical_from_series

        def fail_raw_short(series, **kwargs):
            if series.size < 50 * 103:
                raise inputs.CovarianceEstimationError("fixture raw moment failure")
            return original_raw(series, **kwargs)

        monkeypatch.setattr(inputs.covariance, "empirical_from_series", fail_raw_short)
    else:
        monkeypatch.setattr(inputs.covariance, "estimate_from_raw", fail_short)
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    case = inputs.read_case(prepared, next(iter(prepared.cases)))
    assert case.record["arm_status"]["estimated_64s"] == "not_run"
    assert all(
        case.record["arm_status"][arm] == "ready"
        for arm in inputs.ARMS
        if arm != "estimated_64s"
    )
    assert inputs.arm_arrays(prepared, case, "estimated_64s")["covariance"] is None
    assert ("covariance_raw_64s" in case.arrays) is not raw_failure


def test_stream_snapshot_detects_same_size_change_with_restored_mtime(tmp_path):
    path = tmp_path / "raw.npy"
    path.write_bytes(b"original")
    before = path.stat()
    consumed = publication.Consumption(publication.Deadline(30))
    inputs._hold_file(path, hashlib.sha256(b"original").hexdigest(), consumed)
    path.write_bytes(b"modified")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(ValueError, match="changed after consumption"):
        consumed.check()


def test_extra_payload_and_symlink_are_not_accepted(tmp_path, tiny_protocol):
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    extra = prepared.root / "unbound"
    extra.write_text("extra")
    with pytest.raises(ValueError, match="inventory"):
        inputs.verify_inputs(prepared.root)
    extra.unlink()
    raw = prepared.root / "cases" / next(iter(prepared.cases)) / "background_train.npy"
    moved = tmp_path / "moved.npy"
    raw.rename(moved)
    raw.symlink_to(moved)
    with pytest.raises(ValueError, match="symbolic-link"):
        inputs.verify_inputs(prepared.root)


def test_plan_and_seed_bindings_reject_same_name_mutation(tmp_path, monkeypatch):
    root = tmp_path / "source"
    (root / "data").mkdir(parents=True)
    payload = json.dumps(fixture_table()).encode()
    seed = root / inputs.SEEDS_PATH
    seed.write_bytes(payload)
    monkeypatch.setattr(inputs, "ROOT", root)
    monkeypatch.setattr(inputs, "SEEDS_SHA256", hashlib.sha256(payload).hexdigest())
    assert inputs._seed_table()["reserved"]["evaluation_grid"] == 101
    seed.write_bytes(payload + b"\n")
    with pytest.raises(ValueError, match="frozen protocol"):
        inputs._seed_table()


@pytest.mark.parametrize(
    "change",
    [
        {"cpu_measurement_complete": False},
        {"cpu_measurement_complete": 1},
        {"cpu_scope": "self_plus_children"},
    ],
)
def test_completed_input_requires_complete_precise_cpu_evidence(
    tmp_path, tiny_protocol, change
):
    prepared = inputs.prepare_inputs(tmp_path / "inputs", purpose="technical")
    path = inputs._call_path(prepared.root)
    record = sources.read_json(path.read_bytes())
    record.update(change)
    path.write_bytes(sources.json_bytes(record))
    with pytest.raises(ValueError, match="call-cost evidence"):
        inputs.verify_inputs(prepared.root)
