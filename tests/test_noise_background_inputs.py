"""Check the fixed nested-background design and guarded prospective release."""

import copy
import hashlib
import io
import json
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from ringdown_sr import assessment_publication as publication
from ringdown_sr import noise_background_inputs as inputs
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


def test_seed_table_counts_and_exclusion_match_the_frozen_plan():
    raw = subprocess.check_output(
        ["git", "show", inputs.PLAN_COMMIT + ":" + inputs.PLAN_PATH], cwd=inputs.ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == inputs.PLAN_SHA256
    rows = [
        tuple(int(value) for value in match.groups()[2:])
        for match in re.finditer(
            r"^\| (ar1|white)-(\d+) \| (\d+) \| (\d+) \| (\d+), (\d+), (\d+), (\d+) \|$",
            raw.decode(),
            re.MULTILINE,
        )
    ]
    assert tuple(rows) == inputs.SEED_ROWS
    numbers = [value for row in rows for value in row]
    assert len(numbers) == len(set(numbers)) == 156
    rng = np.random.Generator(np.random.PCG64(2026111609))
    assert [int(rng.integers(1, 2**31)) for _ in range(156)] == numbers
    reserved = {2026111609, 2026111610, 2026111611, 2026111612, 2026111613}
    assert reserved.isdisjoint(numbers)
    names = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            inputs.SEED_BASE_COMMIT,
            "--",
            "data",
            "docs",
            "src",
            "scripts",
            "tests",
        ],
        cwd=inputs.ROOT,
        text=True,
    ).splitlines()
    excluded = set()
    for name in names:
        try:
            text = subprocess.check_output(
                ["git", "show", inputs.SEED_BASE_COMMIT + ":" + name], cwd=inputs.ROOT
            ).decode("utf-8")
        except UnicodeDecodeError:
            continue
        excluded.update(
            int(value)
            for value in re.findall(r"(?<![A-Za-z0-9_])\d+(?![A-Za-z0-9_])", text)
            if 0 < int(value) < 2**31
        )
    assert len(excluded) == 2119
    digest = hashlib.sha256(
        ("\n".join(str(v) for v in sorted(excluded)) + "\n").encode()
    ).hexdigest()
    assert digest == "76c6bbc7bf1b7f651e7c9cc38a4707c372af0baacdaa15d2570a61a768c66823"
    assert excluded.isdisjoint(set(numbers) | reserved)


def test_case_order_and_five_arm_technical_inventory():
    cases = inputs.case_specs()
    expected = [
        item
        for block in range(1, 7)
        for item in (f"ar1-{block:02d}", f"white-{block:02d}")
    ]
    expected += [f"ar1-{block:02d}" for block in range(7, 21)]
    assert [case["id"] for case in cases] == expected
    assert sum(len(case["search_seeds"]) * len(inputs.ARMS) for case in cases) == 520
    assert len(cases) * len(inputs.ARMS) == 130
    assert all(case["niterations"] == 1000 for case in cases)
    (technical,) = inputs.case_specs(technical=True)
    assert technical["id"] == "technical-ar1"
    assert technical["search_seeds"] == [2026111613]
    assert technical["noise_seed"] == 2026111611
    assert technical["background_seed"] == 2026111612
    assert technical["niterations"] == 10
    assert inputs._initial_states()["checked_states"] == 109
    with pytest.raises(TypeError):
        inputs.case_specs(technical=1)


def test_actual_role_collision_is_rejected(monkeypatch):
    original = inputs.pilot_generators

    def collision(noise_seed, background_seed):
        return original(2026111611, 2026111612)

    monkeypatch.setattr(inputs, "pilot_generators", collision)
    with pytest.raises(ValueError, match="initial states collide"):
        inputs._initial_states()


def test_fixed_grids_remain_independent_of_global_randomness(common):
    before = np.random.get_state()
    actual, record = inputs.derive_common_inputs()
    after = np.random.get_state()
    assert all(np.array_equal(a, b) for a, b in zip(before, after, strict=True))
    assert np.array_equal(common["time_s"], np.arange(128) / 4096)
    assert len(common["diagnostic_time_s"]) == 889
    assert len(common["irregular_time_s"]) == 1024
    assert np.all(np.diff(common["irregular_time_s"]) > 0)
    assert not any(float(t * 32768).is_integer() for t in common["irregular_time_s"])
    assert record["grid_seed"] == 2026111610
    assert record["random_state_check"]["collisions"] == 0
    assert all(value < 1e-13 for value in record["reference_maximum_errors"].values())
    assert not np.array_equal(
        common["irregular_time_s"],
        inputs.pilot.derive_common_inputs()[0]["irregular_time_s"],
    )
    for key, array in actual.items():
        assert array.tobytes() == common[key].tobytes()
        with pytest.raises(ValueError):
            array.setflags(write=True)


@pytest.mark.parametrize("technical,index", [(True, 0), (False, 1)])
def test_nested_pool_matches_independent_random_and_covariance_formulas(
    technical, index, common
):
    spec = inputs.case_specs(technical=technical)[index]
    case = inputs.derive_case(spec, common)
    assert case.record["status"] == "ready"
    arrays = case.arrays
    assert arrays["background_train"].shape == (1024, 128)
    assert arrays["background_validation"].shape == (128, 128)
    assert arrays["background_check"].shape == (256, 128)
    # Draw the first background window directly from the documented stream.
    rng = np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence(spec["background_seed"], spawn_key=(0,), pool_size=4)
        )
    )
    if spec["noise_model"] == "white":
        expected = rng.normal(0.0, inputs.SIGMA, 128)
    else:
        expected = rng.standard_normal(128)
        gain = np.sqrt((1 - 0.65) * (1 + 0.65))
        for k in range(1, 128):
            expected[k] = 0.65 * expected[k - 1] + gain * expected[k]
        expected *= inputs.SIGMA
    assert np.array_equal(expected, arrays["background_train"][0])
    prepared = inputs.PreparedInputs({}, common, {spec["id"]: case})
    for size, arm in zip(inputs.TRAINING_SIZES, inputs.ESTIMATED_ARMS, strict=True):
        view = inputs.arm_arrays(prepared, case, arm)
        assert np.shares_memory(view["background_train"], arrays["background_train"])
        assert view["background_train"].shape == (size, 128)
        assert (
            view["background_train"].tobytes()
            == arrays["background_train"][:size].tobytes()
        )
        assert case.record["background_prefixes"][arm][
            "fingerprint"
        ] == inputs.sources.fingerprint(view["background_train"])
        assert np.shares_memory(
            view["covariance_estimated"], arrays[f"covariance_estimated_{size}"]
        )
        assert (
            view["background_validation"].tobytes()
            == arrays["background_validation"].tobytes()
        )
        raw = (
            arrays["background_train"][:size].T
            @ arrays["background_train"][:size]
            / size
        )
        np.testing.assert_allclose(
            arrays[f"covariance_raw_{size}"], raw, rtol=3e-14, atol=2e-18
        )
        record = case.record["covariance_estimation"][arm]
        assert record["n_train"] == size
        assert record["n_validation"] == 128
        scores = []
        for alpha in inputs.ALPHAS:
            if alpha == 0 and size < 128:
                continue
            matrix = (1 - alpha) * raw + alpha * np.trace(raw) / 128 * np.eye(128)
            values = np.linalg.eigvalsh(matrix)
            if values[0] <= 0 or values[-1] / values[0] > 1e8:
                continue
            score = np.linalg.slogdet(matrix)[1] + np.mean(
                np.sum(
                    arrays["background_validation"]
                    * np.linalg.solve(matrix, arrays["background_validation"].T).T,
                    axis=1,
                )
            )
            scores.append((score, alpha))
        assert record["alpha_selected"] == min(scores)[1]
        alpha = record["alpha_selected"]
        np.testing.assert_allclose(
            view["covariance_estimated"],
            (1 - alpha) * raw + alpha * np.trace(raw) / 128 * np.eye(128),
            rtol=3e-14,
            atol=2e-18,
        )
        assert record["refit"] is False
    for arm in inputs.ARMS[:2]:
        assert "covariance_estimated" not in inputs.arm_arrays(prepared, case, arm)
    with pytest.raises(ValueError, match="Unknown"):
        inputs.arm_arrays(prepared, case, "estimated_covariance")
    encoded = inputs.npz_bytes(arrays)
    assert encoded == inputs.npz_bytes(dict(reversed(list(arrays.items()))))
    with np.load(io.BytesIO(encoded), allow_pickle=False) as archive:
        assert set(archive.files) == set(arrays)
        for key in arrays:
            assert archive[key].tobytes() == arrays[key].tobytes()


def test_one_covariance_failure_preserves_four_other_arms(monkeypatch, common):
    original = inputs.estimate_covariance
    seen = []

    def partial(train, validation, **kwargs):
        seen.append(len(train))
        if len(train) == 256:
            raise CovarianceEstimationError(
                "No usable matrix.", raw_covariance=np.eye(128), mu=1.0
            )
        return original(train, validation, **kwargs)

    monkeypatch.setattr(inputs, "estimate_covariance", partial)
    case = inputs.derive_case(inputs.case_specs(technical=True)[0], common)
    assert seen == [64, 256, 1024]
    assert case.record["status"] == "covariance_failed"
    assert case.record["arm_status"] == dict.fromkeys(inputs.ARMS, "ready") | {
        "estimated_256": "not_run"
    }
    assert "covariance_estimated_256" not in case.arrays
    assert (
        "covariance_estimated_64" in case.arrays
        and "covariance_estimated_1024" in case.arrays
    )
    failed = case.record["covariance_estimation"]["estimated_256"]
    assert (
        failed["n_train"] == 256
        and failed["error"]["type"] == "CovarianceEstimationError"
    )
    assert (
        case.record["covariance_diagnostics"]["estimated_256"][
            "relative_frobenius_error"
        ]["value"]
        is None
    )
    assert (
        case.record["covariance_diagnostics"]["estimated_1024"][
            "relative_frobenius_error"
        ]["value"]
        is not None
    )


def test_background_failure_retains_shared_observations_and_controls(
    monkeypatch, common
):
    def fail(*args, **kwargs):
        kwargs["windows"]["train"] = np.ones((2, 128))
        kwargs["random"]["roles"]["train"]["calls"]["completed_calls"] = 2
        raise FloatingPointError("Unrepresentable background.")

    monkeypatch.setattr(inputs, "generate_background", fail)
    case = inputs.derive_case(inputs.case_specs(technical=True)[0], common)
    assert case.record["status"] == "background_failed"
    assert case.record["arm_status"] == dict.fromkeys(
        inputs.ESTIMATED_ARMS, "not_run"
    ) | dict.fromkeys(inputs.ARMS[:2], "ready")
    assert case.arrays["background_train"].shape == (2, 128)
    assert "observed" in case.arrays and "covariance_true" in case.arrays
    for entry in case.record["covariance_diagnostics"].values():
        assert (
            entry["relative_frobenius_error"]["reason"]
            == "background_preparation_failed"
        )


def test_measurement_failure_marks_all_five_not_run(monkeypatch, common):
    def fail(*args, **kwargs):
        raise FloatingPointError("Unrepresentable observation.")

    monkeypatch.setattr(inputs, "draw_noise_window", fail)
    case = inputs.derive_case(inputs.case_specs(technical=True)[0], common)
    assert case.record["status"] == "data_failed"
    assert set(case.record["arm_status"].values()) == {"not_run"}
    assert case.record["random"]["signal"]["state_after"] is not None


def test_check_windows_never_select_an_alpha(monkeypatch, common):
    spec = inputs.case_specs(technical=True)[0]
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
    for size, arm in zip(inputs.TRAINING_SIZES, inputs.ESTIMATED_ARMS, strict=True):
        assert np.array_equal(
            original.arrays[f"covariance_estimated_{size}"],
            modified.arrays[f"covariance_estimated_{size}"],
        )
        before = original.record["covariance_diagnostics"][arm]["background_check"][
            "estimated"
        ]["value"]
        after = modified.record["covariance_diagnostics"][arm]["background_check"][
            "estimated"
        ]["value"]
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
    assert verified.manifest["planned_search_calls"] == 5
    assert verified.manifest["planned_algorithm_outputs"] == 5
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


@pytest.mark.parametrize(
    "field,value",
    [
        ("technical", False),
        ("planned_search_calls", 520),
        ("planned_algorithm_outputs", 130),
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
    with pytest.raises(ValueError, match="Frozen noise-background plan"):
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


def test_replayed_call_at_deadline_is_rejected(prepared):
    path = inputs._call_path(prepared)
    record = json.loads(path.read_text())
    record["wall_seconds"] = inputs.PREPARE_SECONDS
    path.write_bytes(inputs.sources.json_bytes(record))
    with pytest.raises(ValueError, match="exceeded its frozen deadline"):
        inputs.verify_inputs(prepared)
