"""Check prospective seed/data bindings and fail-closed input preparation."""

import copy
import hashlib
import io
import json
import re
import subprocess
import zipfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from ringdown_sr import assessment_publication as publication
from ringdown_sr import noise_pilot_inputs as inputs
from ringdown_sr.covariance_estimation import CovarianceEstimationError


@pytest.fixture(autouse=True)
def one_blas_thread():
    with threadpool_limits(limits=1):
        yield


@pytest.fixture(scope="module")
def common():
    return inputs.derive_common_inputs()[0]


@pytest.fixture
def bound_sources(monkeypatch):
    software = {"software_commit": "a" * 40, "source_sha256": {}}
    monkeypatch.setattr(
        inputs.confirmed_search,
        "freeze_software",
        lambda consumed: copy.deepcopy(software),
    )
    return software


@pytest.fixture
def prepared(tmp_path, bound_sources):
    output = tmp_path / "inputs"
    inputs.prepare_inputs(output, technical=True)
    return output


def all_files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def rewrite_manifest(root, change):
    path = root / "preparation.json"
    value = json.loads(path.read_text())
    change(value)
    path.write_bytes(inputs.sources.json_bytes(value))


def test_seed_table_is_exactly_the_separately_committed_plan():
    raw = subprocess.check_output(
        ["git", "show", inputs.PLAN_COMMIT + ":" + inputs.PLAN_PATH], cwd=inputs.ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == inputs.PLAN_SHA256
    rows = []
    for line in raw.decode().splitlines():
        match = re.fullmatch(
            r"\| ([1-6]) \| (white|ar1) \| (\d+) \| (\d+) \| "
            r"(\d+), (\d+), (\d+), (\d+) \|",
            line,
        )
        if match:
            rows.append(tuple(int(match[k]) for k in range(3, 9)))
    assert tuple(rows) == inputs.SEED_ROWS
    numbers = [value for row in rows for value in row]
    assert len(numbers) == len(set(numbers)) == 72
    assert all(0 < value < 2**31 for value in numbers)
    rng = np.random.Generator(np.random.PCG64(2026111409))
    assert [int(rng.integers(1, 2**31)) for _ in range(72)] == numbers
    reserved = {2026111409, 2026111410, 2026111411, 2026111412, 2026111413}
    assert reserved.isdisjoint(numbers)
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", inputs.SEED_BASE_COMMIT],
        cwd=inputs.ROOT,
        text=True,
    ).splitlines()
    excluded = set()
    for name in names:
        if name.split("/", 1)[0] not in {"data", "docs", "src", "scripts", "tests"}:
            continue
        old = subprocess.check_output(
            ["git", "show", inputs.SEED_BASE_COMMIT + ":" + name], cwd=inputs.ROOT
        )
        try:
            text = old.decode("utf-8")
        except UnicodeDecodeError:
            continue
        excluded.update(
            int(value)
            for value in re.findall(r"(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])", text)
            if 0 < int(value) < 2**31
        )
    assert len(excluded) == 1766
    digest = hashlib.sha256(
        ("\n".join(str(v) for v in sorted(excluded)) + "\n").encode()
    ).hexdigest()
    assert digest == "a6a653c98dd9fedf63626e30f57c148685952eefaa7062795d6cffa74c05021a"
    assert excluded.isdisjoint(set(numbers) | reserved)


def test_case_order_counts_and_technical_scope_are_distinct():
    specs = inputs.case_specs()
    assert [spec["id"] for spec in specs] == [
        "white-01",
        "ar1-01",
        "ar1-02",
        "white-02",
        "white-03",
        "ar1-03",
        "ar1-04",
        "white-04",
        "white-05",
        "ar1-05",
        "ar1-06",
        "white-06",
    ]
    assert sum(len(spec["search_seeds"]) * 3 for spec in specs) == 144
    assert all(spec["niterations"] == 1000 and not spec["technical"] for spec in specs)
    (technical,) = inputs.case_specs(technical=True)
    assert technical["id"] == "technical-ar1"
    assert technical["noise_seed"] == 2026111411
    assert technical["background_seed"] == 2026111412
    assert technical["search_seeds"] == [2026111413]
    assert technical["niterations"] == 10 and technical["technical"] is True
    with pytest.raises(TypeError):
        inputs.case_specs(technical=1)


def test_common_grids_truth_and_private_rng_are_frozen(common):
    state = np.random.get_state()
    actual, record = inputs.derive_common_inputs()
    after = np.random.get_state()
    assert all(np.array_equal(a, b) for a, b in zip(state, after, strict=True))
    assert len(common["time_s"]) == 128
    assert len(common["diagnostic_time_s"]) == 889
    assert len(common["irregular_time_s"]) == 1024
    assert np.array_equal(common["time_s"], np.arange(128) / 4096)
    assert common["time_s"][-1] == 127 / 4096
    assert np.all(np.diff(common["irregular_time_s"]) > 0)
    assert not any(float(t * 32768).is_integer() for t in common["irregular_time_s"])
    assert all(v < 1e-13 for v in record["reference_maximum_errors"].values())
    assert inputs.SIGMA.hex() == (inputs.SIGNAL["amplitude"] * 0.05).hex()
    for name, value in common.items():
        assert value.tobytes() == actual[name].tobytes()
        with pytest.raises(ValueError):
            value.setflags(write=True)


@pytest.mark.parametrize("index", [0, 1])
def test_real_case_draws_and_estimator_match_independent_numpy_definition(
    index, common
):
    spec = inputs.case_specs()[index]
    case = inputs.derive_case(spec, common)
    arrays = case.arrays
    assert case.record["status"] == "ready"
    assert all(v == "ready" for v in case.record["arm_status"].values())
    assert arrays["background_train"].shape == (64, 128)
    assert arrays["background_validation"].shape == (128, 128)
    assert arrays["background_check"].shape == (256, 128)
    rng = np.random.Generator(np.random.PCG64(spec["noise_seed"]))
    if spec["noise_model"] == "white":
        expected = rng.normal(0.0, inputs.SIGMA, 128)
        covariance = inputs.SIGMA**2 * np.eye(128)
    else:
        expected = rng.standard_normal(128)
        gain = np.sqrt((1 - 0.65) * (1 + 0.65))
        for k in range(1, 128):
            expected[k] = 0.65 * expected[k - 1] + gain * expected[k]
        expected *= inputs.SIGMA
        covariance = inputs.SIGMA**2 * 0.65 ** np.abs(
            np.subtract.outer(np.arange(128), np.arange(128))
        )
    assert np.array_equal(arrays["noise"], expected)
    assert np.array_equal(arrays["observed"], common["signal"] + expected)
    assert np.array_equal(arrays["covariance_true"], covariance)
    independent_raw = arrays["background_train"].T @ arrays["background_train"] / 64
    np.testing.assert_allclose(
        arrays["covariance_raw"], independent_raw, atol=2e-18, rtol=3e-14
    )
    estimated = case.record["covariance_estimation"]
    assert estimated["candidates"][0]["alpha"] == 0
    assert estimated["candidates"][0]["reason"] is not None
    eligible = [r for r in estimated["candidates"] if r["reason"] is None]
    chosen = min(eligible, key=lambda row: (row["score"], row["alpha"]))
    assert chosen["alpha"] == estimated["alpha_selected"]
    alpha, mu = estimated["alpha_selected"], estimated["mu"]
    np.testing.assert_allclose(
        arrays["covariance_estimated"],
        (1 - alpha) * independent_raw + alpha * mu * np.eye(128),
        atol=2e-18,
        rtol=3e-14,
    )
    assert estimated["refit"] is False
    archive = inputs.npz_bytes(arrays)
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        assert sum(info.file_size for info in zipped.infolist()) < 2 * 1024**2
    assert archive == inputs.npz_bytes(dict(reversed(list(arrays.items()))))


def test_covariance_failure_preserves_ordinary_known_and_all_random_evidence(
    monkeypatch, common
):
    def fail(*args, **kwargs):
        raise CovarianceEstimationError(
            "No usable matrix.", raw_covariance=np.zeros((128, 128)), mu=0.0
        )

    monkeypatch.setattr(inputs, "estimate_covariance", fail)
    case = inputs.derive_case(inputs.case_specs()[0], common)
    assert case.record["status"] == "covariance_failed"
    assert case.record["arm_status"] == {
        "ordinary": "ready",
        "known_covariance": "ready",
        "estimated_covariance": "not_run",
    }
    assert "covariance_estimated" not in case.arrays
    assert "observed" in case.arrays and "covariance_true" in case.arrays
    diagnostic = case.record["covariance_diagnostics"]
    assert diagnostic["background_check"]["true"]["status"] == "available"
    assert (
        diagnostic["background_check"]["estimated"]["reason"]
        == "covariance_estimation_failed"
    )
    assert diagnostic["relative_frobenius_error"]["value"] is None
    assert (
        case.record["random"]["background"]["roles"]["check"]["calls"][
            "completed_calls"
        ]
        == 256
    )


def test_numerical_data_failure_keeps_case_and_no_arm_ready(monkeypatch, common):
    def fail(*args, **kwargs):
        raise FloatingPointError("Unrepresentable generated values.")

    monkeypatch.setattr(inputs, "draw_noise_window", fail)
    case = inputs.derive_case(inputs.case_specs()[0], common)
    assert case.record["status"] == "data_failed"
    assert all(v == "not_run" for v in case.record["arm_status"].values())
    assert case.record["random"]["signal"]["state_after"] is not None
    assert case.record["random"]["signal"]["calls"]["completed_calls"] == 0
    diagnostic = case.record["covariance_diagnostics"]
    assert diagnostic["background_check"]["true"]["reason"] == "data_preparation_failed"
    assert diagnostic["relative_frobenius_error"]["value"] is None


def test_covariance_diagnostics_have_independent_diagonal_references():
    arrays = {
        "covariance_true": np.diag([1.0, 4.0]),
        "covariance_estimated": np.diag([2.0, 8.0]),
        "background_check": np.array([[1.0, 2.0], [3.0, 4.0]]),
    }
    original = {name: value.copy() for name, value in arrays.items()}
    result = inputs.covariance_diagnostics(arrays, "ready")
    known = result["background_check"]["true"]["value"]
    estimated = result["background_check"]["estimated"]["value"]
    assert known["n_windows"] == 2
    assert known["log_determinant"] == pytest.approx(np.log(4))
    assert known["quadratic_mean"] == pytest.approx((1 + 1 + 9 + 4) / 2)
    assert known["score"] == pytest.approx(np.log(4) + 7.5)
    assert estimated["score"] == pytest.approx(np.log(16) + 3.75)
    assert result["condition_number"]["true"]["value"] == 4
    assert result["condition_number"]["estimated"]["value"] == 4
    assert result["relative_frobenius_error"]["value"] == 1
    assert result["changes_covariance_or_alpha"] is False
    assert all(np.array_equal(arrays[name], value) for name, value in original.items())


def test_diagnostic_numeric_failure_is_explicit_but_unknown_error_propagates(
    monkeypatch,
):
    arrays = {
        "covariance_true": np.eye(2),
        "covariance_estimated": np.eye(2),
        "background_check": np.ones((2, 2)),
    }

    def numerical(*args, **kwargs):
        raise FloatingPointError("Unrepresentable diagnostic.")

    monkeypatch.setattr(inputs, "_background_check_score", numerical)
    result = inputs.covariance_diagnostics(arrays, "ready")
    assert (
        result["background_check"]["true"]["reason"] == "numerical_diagnostic_failure"
    )
    assert result["background_check"]["true"]["value"] is None

    def unknown(*args, **kwargs):
        raise ValueError("Invalid array contract.")

    monkeypatch.setattr(inputs, "_background_check_score", unknown)
    with pytest.raises(ValueError, match="Invalid array contract"):
        inputs.covariance_diagnostics(arrays, "ready")


def test_held_out_check_changes_diagnostics_not_alpha_or_covariance(
    monkeypatch, common
):
    spec = inputs.case_specs()[1]
    original = inputs.derive_case(spec, common)
    generate = inputs.generate_background

    def changed(*args, **kwargs):
        generate(*args, **kwargs)
        kwargs["windows"]["check"] *= 2

    monkeypatch.setattr(inputs, "generate_background", changed)
    modified = inputs.derive_case(spec, common)
    assert (
        original.record["covariance_estimation"]
        == modified.record["covariance_estimation"]
    )
    assert np.array_equal(
        original.arrays["covariance_estimated"], modified.arrays["covariance_estimated"]
    )
    before = original.record["covariance_diagnostics"]["background_check"]["estimated"][
        "value"
    ]
    after = modified.record["covariance_diagnostics"]["background_check"]["estimated"][
        "value"
    ]
    assert after["quadratic_mean"] == pytest.approx(4 * before["quadratic_mean"])


@pytest.mark.parametrize(
    "error",
    [
        ValueError("Unknown generator error."),
        KeyboardInterrupt(),
        RuntimeError("Invocation guard failed."),
    ],
)
def test_unknown_generation_errors_and_interruptions_are_fatal(
    monkeypatch, common, error
):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(inputs, "draw_noise_window", fail)
    with pytest.raises(type(error)):
        inputs.derive_case(inputs.case_specs()[0], common)


def test_prepare_and_verify_are_read_only_and_bind_all_roles(prepared):
    before = all_files(prepared)
    before_call = inputs._call_path(prepared).read_bytes()
    consumed = publication.Consumption(publication.Deadline(60))
    verified = inputs.verify_inputs(prepared, consumed)
    assert before == all_files(prepared)
    assert before_call == inputs._call_path(prepared).read_bytes()
    assert verified.manifest["planned_search_calls"] == 3
    assert verified.manifest["planned_algorithm_outputs"] == 3
    assert verified.manifest["protocol"]["commit"] == inputs.PLAN_COMMIT
    assert list(verified.cases) == ["technical-ar1"]
    assert not (prepared / inputs.LOCK).exists()
    assert verified.manifest["timing"]["wall_seconds"] > 0
    assert verified.call["wall_seconds"] >= verified.manifest["timing"]["wall_seconds"]
    assert verified.call["status"] == "completed"
    assert verified.call["cpu_scope"] == "self_plus_children"
    (prepared / "cases/technical-ar1.npz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Consumed file changed"):
        consumed.check()


def test_complete_scientific_preparation_is_global_before_any_execution(
    tmp_path, bound_sources
):
    root = tmp_path / "scientific"
    manifest = inputs.prepare_inputs(root)
    assert manifest["planned_search_calls"] == 144
    assert manifest["planned_algorithm_outputs"] == 36
    assert len(manifest["case_order"]) == 12
    assert len(manifest["file_sha256"]) == 25
    assert len(list((root / "cases").iterdir())) == 24
    assert not (root / inputs.LOCK).exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("technical", False),
        ("planned_search_calls", 144),
        ("planned_algorithm_outputs", 36),
        ("case_order", ["ar1-01"]),
        ("software", {"software_commit": "b" * 40}),
        ("protocol", {}),
    ],
)
def test_resealed_global_manifest_contradictions_fail(prepared, field, value):
    rewrite_manifest(prepared, lambda manifest: manifest.__setitem__(field, value))
    with pytest.raises((ValueError, KeyError)):
        inputs.verify_inputs(prepared)


@pytest.mark.parametrize(
    "name", ["common.npz", "cases/technical-ar1.npz", "cases/technical-ar1.json"]
)
def test_resealed_input_or_record_changes_fail(prepared, name):
    path = prepared / name
    path.write_bytes(path.read_bytes() + b" ")
    rewrite_manifest(
        prepared,
        lambda manifest: manifest["file_sha256"].__setitem__(
            name, inputs.sources.sha256(path.read_bytes())
        ),
    )
    with pytest.raises(ValueError):
        inputs.verify_inputs(prepared)


def test_extra_files_and_locked_preparations_are_rejected(prepared):
    extra = prepared / "cases/unplanned.json"
    extra.write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        inputs.verify_inputs(prepared)
    extra.unlink()
    (prepared / inputs.LOCK).write_text("incomplete")
    with pytest.raises(ValueError, match="locked"):
        inputs.verify_inputs(prepared)


def test_interruption_preserves_locked_partial_preparation(
    tmp_path, bound_sources, monkeypatch
):
    root = tmp_path / "interrupted"

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(inputs, "derive_case", interrupt)
    with pytest.raises(KeyboardInterrupt):
        inputs.prepare_inputs(root, technical=True)
    assert (root / inputs.LOCK).exists()
    call = json.loads(inputs._call_path(root).read_text())
    assert call["status"] == "aborted"
    assert call["wall_seconds"] > 0
    assert call["error"]["type"] == "KeyboardInterrupt"
    with pytest.raises(ValueError, match="locked"):
        inputs.verify_inputs(root)


def test_mutation_during_unlock_revokes_preparation(
    tmp_path, bound_sources, monkeypatch
):
    original = Path.unlink

    def mutate(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path.name == inputs.LOCK:
            (path.parent / "common.npz").write_bytes(b"late mutation")
        return result

    monkeypatch.setattr(Path, "unlink", mutate)
    output = tmp_path / "late"
    with pytest.raises(ValueError, match="Prospective input changed"):
        inputs.prepare_inputs(output, technical=True)
    assert (output / inputs.LOCK).exists()


def test_mutation_during_handler_restoration_revokes_preparation(
    tmp_path, bound_sources, monkeypatch
):
    original = publication.Deadline.active
    output = tmp_path / "teardown"

    @contextmanager
    def mutate(clock):
        with original(clock):
            yield clock
        (output / "cases/technical-ar1.json").write_text("{}")

    monkeypatch.setattr(publication.Deadline, "active", mutate)
    with pytest.raises(ValueError, match="Consumed file changed"):
        inputs.prepare_inputs(output, technical=True)
    assert (output / inputs.LOCK).exists()


def test_protocol_content_cannot_move_to_a_changed_working_file(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / inputs.PLAN_PATH).write_text("changed protocol")
    monkeypatch.setattr(inputs, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Frozen noise-pilot plan"):
        inputs._protocol(publication.Consumption(publication.Deadline(60)))


def test_symlink_payload_is_rejected_even_with_same_bytes(prepared, tmp_path):
    original = prepared / "common.npz"
    outside = tmp_path / "outside.npz"
    outside.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        inputs.verify_inputs(prepared)


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_manifest_sha256", "0" * 64),
        ("status", "aborted"),
        ("input_directory", "different"),
        ("cpu_scope", "self_only"),
        ("wall_seconds", 0.0),
        ("cpu_user_seconds", -1.0),
    ],
)
def test_missing_or_contradictory_call_evidence_is_rejected(prepared, field, value):
    path = inputs._call_path(prepared)
    record = json.loads(path.read_text())
    record[field] = value
    path.write_bytes(inputs.sources.json_bytes(record))
    with pytest.raises(ValueError):
        inputs.verify_inputs(prepared)


def test_call_missing_or_changed_after_verification_invalidates_inputs(prepared):
    consumed = publication.Consumption(publication.Deadline(60))
    inputs.verify_inputs(prepared, consumed)
    inputs._call_path(prepared).unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        consumed.check()
    with pytest.raises(ValueError, match="regular prospective"):
        inputs.verify_inputs(prepared)


def test_mutation_while_writing_call_revokes_input_release(
    tmp_path, bound_sources, monkeypatch
):
    original = Path.write_bytes
    output = tmp_path / "call-mutation"
    changed = False

    def mutate(path, data):
        nonlocal changed
        result = original(path, data)
        if path == inputs._call_path(output) and not changed:
            changed = True
            (output / "common.npz").write_bytes(b"late source change")
        return result

    monkeypatch.setattr(Path, "write_bytes", mutate)
    with pytest.raises(ValueError, match="Consumed file changed"):
        inputs.prepare_inputs(output, technical=True)
    assert (output / inputs.LOCK).exists()
    assert json.loads(inputs._call_path(output).read_text())["status"] == "aborted"
