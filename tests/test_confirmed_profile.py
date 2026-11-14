"""The opt-in member must retain its profile and reject integrity failures."""

import copy
import csv
import io
import json
from dataclasses import asdict

import numpy as np
import pytest

from ringdown_sr import confirmed_profile as profile
from ringdown_sr import symbolic
from ringdown_sr.pilot import _write_json


def request(*, technical=False):
    return {
        "format": profile.FORMAT,
        "profile": profile.PROFILE,
        "seed": 20261401,
        "technical": technical,
        "budget": asdict(
            symbolic.SearchBudget(seed=20261401, niterations=1 if technical else 1000)
        ),
    }


@pytest.mark.parametrize("technical,iterations", [(False, 1000), (True, 1)])
def test_explicit_profile_retains_local_budget_and_native_loss(technical, iterations):
    budget = profile.checked_request(request(technical=technical))
    actual = profile.parameters(budget)
    assert actual["niterations"] == iterations
    assert actual["optimizer_iterations"] == 300
    assert actual["optimizer_nrestarts"] == 5
    assert actual["use_frequency"] is actual["use_frequency_in_tournament"] is True
    assert actual["should_simplify"] is False
    assert actual["warmup_maxsize_by"] == 0
    assert actual["loss_function"] == "Main.SearchTimeBudget.objective"
    assert actual["batching"] is False
    assert actual["timeout_in_seconds"] is None
    assert actual["guesses"] is None


def test_legacy_default_search_parameters_are_unchanged():
    legacy = symbolic.search_parameters(symbolic.SearchBudget())
    assert legacy["optimizer_iterations"] == 20
    assert legacy["optimizer_nrestarts"] == 2
    assert legacy["use_frequency"] is legacy["use_frequency_in_tournament"] is False
    assert "should_simplify" not in legacy
    assert legacy["loss_function"] == "Main.RingdownSRSearch.objective"


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", True),
        ("seed", 0),
        ("seed", 2**31),
        ("technical", 1),
        ("profile", "legacy"),
        ("format", symbolic.FORMAT),
    ],
)
def test_request_cannot_silently_change_scope(field, value):
    document = request()
    document[field] = value
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("niterations", True),
        ("niterations", 2),
        ("niterations", 1.0),
        ("populations", 1),
        ("population_size", 64),
        ("ncycles_per_iteration", 1),
        ("seed", 4),
    ],
)
def test_effective_budget_aliases_and_changes_are_rejected(field, value):
    document = request(technical=True)
    document["budget"][field] = value
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize(
    "message",
    [
        "ValueError: Unexpected actual equation_search invocation.",
        "KeyboardInterrupt: ",
        "InterruptedError: interrupted",
        "RuntimeError: unknown",
        "AssertionError: replay failed",
        'JuliaError: ErrorException("Wrong native option")',
    ],
)
@pytest.mark.parametrize("timed_out", [False, True])
def test_integrity_and_interrupts_are_not_fit_errors_even_after_timeout(
    message, timed_out
):
    with pytest.raises(ValueError, match="integrity"):
        profile.failure_status(
            {"phase": "failed", "failed_during": "fit", "error": message},
            timed_out=timed_out,
        )


@pytest.mark.parametrize("message", profile.NUMERICAL_ERRORS)
def test_only_explicit_fit_numerical_errors_are_allowed(message):
    metadata = {
        "phase": "failed",
        "failed_during": "fit",
        "error": message + " numerical case",
    }
    assert profile.failure_status(metadata) == "fit_error"
    assert profile.failure_status(metadata, timed_out=True) == "timeout"
    with pytest.raises(ValueError):
        profile.failure_status({**metadata, "failed_during": "replay"})


def test_early_timeout_allows_only_missing_not_contradictory_worker_origin():
    initial = {"provenance": {"git": {"commit": "bound"}}}
    manifest = {"sources": {"worker": "hash"}}
    early = {
        **initial,
        "adapter_source_sha256": manifest["sources"],
        "phase": "worker_start",
    }
    assert profile.failure_status(early, timed_out=True) == "timeout"
    profile._verify_origin(early, initial, manifest, completed=False)
    for key in ("worker_provenance", "worker_adapter_source_sha256"):
        with pytest.raises(ValueError, match="actual worker"):
            profile._verify_origin(
                {**early, key: {}}, initial, manifest, completed=False
            )
    with pytest.raises(ValueError, match="actual worker"):
        profile._verify_origin(
            {**early, "phase": "fit"}, initial, manifest, completed=False
        )


def test_guard_checks_actual_native_call_before_delegating():
    class Backend:
        @property
        def equation_search(self):
            pytest.fail("Guard must reject before actual native invocation.")

    guard = profile.native.SearchInvocationGuard(Backend(), 1000)
    with pytest.raises(ValueError, match="actual equation_search"):
        guard._jl_call_nogil(
            np.ones((1, 2)),
            np.ones(2),
            niterations=500,
            parallelism="serial",
            return_state=True,
            saved_state=None,
            guesses=None,
            weights=None,
        )
    with pytest.raises(ValueError, match="completed"):
        guard.record()


def test_prepare_binds_all_fixed_inputs_and_preserves_original_arrays(tmp_path):
    times, observed = np.array([0.0, 1.0]), np.array([1.0, 0.0])
    covariance = np.array([[2.5, 1.5], [1.5, 4.5]])
    output = tmp_path / "member"
    profile.prepare_member(
        output, times, observed, covariance=covariance, seed=20261401, technical=True
    )
    immutable = profile.prepared_files(output)
    times[0] = 99
    observed[0] = 99
    covariance[0, 0] = 99
    checked, arrays, _ = profile.verify_prepared(output)
    assert checked["technical"] is True
    assert arrays["time_s"].tolist() == [0.0, 1.0]
    assert arrays["observed"].tolist() == [1.0, 0.0]
    assert arrays["covariance"].tolist() == [[2.5, 1.5], [1.5, 4.5]]
    _write_json(output / "metadata.json", {"phase": "running"})
    assert immutable == profile.prepared_files(output)
    (output / "inputs.npz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="preparation"):
        profile.verify_prepared(output)


def test_artifact_parser_rejects_duplicate_keys_and_nonfinite(tmp_path):
    for content in (b'{"seed":1,"seed":2}', b'{"loss":NaN}'):
        (tmp_path / "record.json").write_bytes(content)
        with pytest.raises(ValueError):
            profile.read(tmp_path, "record.json")


def failed_member(tmp_path, *, phase="worker_start", error=None, timed_out=True):
    output = tmp_path / "failed"
    manifest = profile.prepare_member(
        output, [0.0, 1.0], [1.0, 0.0], seed=20261401, technical=True
    )
    initial = profile.read(output, "metadata_initial.json")
    metadata = {**initial, "phase": phase}
    if phase == "fit":
        _write_json(output / "native_runtime.json", native_runtime())
        _write_json(
            output / "backend_sources.json",
            profile.native.configuration()["reviewed_backend_sources"],
        )
        metadata.update(
            worker_provenance=initial["provenance"],
            worker_adapter_source_sha256=manifest["sources"],
        )
    if error is not None:
        metadata.update(phase="failed", failed_during=phase, error=error)
    _write_json(output / "metadata.json", metadata)
    _write_json(
        output / "outcome.json",
        {
            "format": profile.FORMAT,
            "status": "timeout" if timed_out else "fit_error",
            "returncode": -15 if timed_out else 1,
            "timed_out": timed_out,
            "worker_wall_seconds": 12.0,
            "adapter_call_wall_seconds": 12.0,
            "cpu_user_seconds": None if timed_out else 3.0,
            "cpu_system_seconds": None if timed_out else 1.0,
        },
    )
    rebind_checksums(output)
    return output


def rebind_checksums(output):
    _write_json(
        output / "member_checksums.json",
        {
            path.relative_to(output).as_posix(): profile._sha256(path.read_bytes())
            for path in output.rglob("*")
            if path.is_file() and path.name != "member_checksums.json"
        },
    )


def test_read_only_failed_member_preserves_unknown_cpu_and_fixed_denominator(tmp_path):
    output = failed_member(tmp_path)
    before = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
    record = profile.verify_member(output)
    assert record["status"] == "timeout"
    assert record["selected"] is None
    assert record["candidates"] == []
    assert record["costs"]["cpu_user_seconds"] is None
    assert record["costs"]["callback_calls_during_fit"] is None
    assert record["costs"]["worker_wall_seconds"] == 12
    assert before == {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}


@pytest.mark.parametrize("field", ["worker_provenance", "worker_adapter_source_sha256"])
def test_failed_member_reverification_rejects_actual_worker_contradictions(
    tmp_path, field, monkeypatch
):
    monkeypatch.setattr(profile, "numerical_environment", lambda *args, **kwargs: None)
    output = failed_member(
        tmp_path, phase="fit", error="OverflowError: ordinary range", timed_out=False
    )
    assert profile.verify_member(output)["status"] == "fit_error"
    metadata = profile.read(output, "metadata.json")
    metadata[field] = {}
    _write_json(output / "metadata.json", metadata)
    rebind_checksums(output)
    with pytest.raises(ValueError, match="actual worker"):
        profile.verify_member(output)


@pytest.mark.parametrize(
    "message",
    [
        "KeyboardInterrupt: stopped",
        "ValueError: Unexpected actual equation_search invocation.",
    ],
)
def test_failed_member_reverification_cannot_hide_interrupt_or_guard_behind_timeout(
    tmp_path, message
):
    output = failed_member(tmp_path, phase="fit", error=message)
    with pytest.raises(ValueError, match="integrity"):
        profile.verify_member(output)


def test_failed_member_late_change_is_not_released(tmp_path, monkeypatch):
    output = failed_member(tmp_path)
    original = profile.failure_status

    def mutate(metadata, **kwargs):
        result = original(metadata, **kwargs)
        outcome = profile.read(output, "outcome.json")
        outcome["worker_wall_seconds"] = 99.0
        _write_json(output / "outcome.json", outcome)
        rebind_checksums(output)
        return result

    monkeypatch.setattr(profile, "failure_status", mutate)
    with pytest.raises(ValueError, match="changed during"):
        profile.verify_member(output)


def test_checker_rejects_changed_covariance_even_with_same_zero_expression_loss():
    checker = profile.native.load_module(
        profile.ROOT / "scripts/check_confirmed_profile.py", "confirmed_checker_fixture"
    )
    original = checker.fixture("full")
    altered = {**original, "covariance": np.array([[3.0, 2.0], [2.0, 4.0]])}
    y = original["observed"]
    original_zero = y @ np.linalg.solve(original["covariance"], y) / y.size
    altered_zero = y @ np.linalg.solve(altered["covariance"], y) / y.size
    assert original_zero == altered_zero == 0.25
    record = {
        "input_fingerprints": {
            key: profile.sources.fingerprint(value) for key, value in altered.items()
        }
    }
    with pytest.raises(ValueError, match="fixture"):
        checker.verify_fixture(record, "full")


def native_runtime():
    return {
        "cpu_name": "test",
        "cpu_models": ["test"],
        "cpu_threads": 1,
        "word_size": 64,
        "julia_threads": 1,
        "interactive_threads": 0,
        "gc_threads": 1,
        "blas_threads": 1,
        "affinity": [0],
        "thread_environment": dict(profile.native.JULIA_THREADS),
    }


def python_environment():
    pins = {
        item["name"]: item.get("version")
        for item in profile.tomllib.loads((profile.ROOT / "uv.lock").read_text())[
            "package"
        ]
    }
    return {
        "python_version": (profile.ROOT / ".python-version").read_text().strip(),
        "python_implementation": "CPython",
        "array_dtype": "float64",
        "julia_used": True,
        "thread_environment": {
            key: "1"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "packages": {
            key: pins[key]
            for key in (
                "numpy",
                "scipy",
                "pysr",
                "juliacall",
                "gmpy2",
                "sympy",
                "threadpoolctl",
            )
        },
        "numerical_libraries": {
            "snapshot": "before_fit",
            "threadpools": {
                "status": "available",
                "details": [
                    {
                        "user_api": "blas",
                        "internal_api": "openblas",
                        "num_threads": 1,
                        "architecture": "Haswell",
                        "filepath": path,
                    }
                    for path in (
                        "/prefix/numpy.libs/libopenblas.so",
                        "/prefix/scipy.libs/libopenblas.so",
                        "/prefix/lib/julia/libopenblas.so",
                    )
                ],
                "error": None,
            },
        },
    }


@pytest.mark.parametrize(
    "tamper", ["version", "threads", "core", "missing_julia", "python"]
)
def test_actual_numeric_environment_rejects_package_and_blas_drift(tamper):
    environment = python_environment()
    profile.checked_environment(environment)
    pools = environment["numerical_libraries"]["threadpools"]["details"]
    if tamper == "version":
        environment["packages"]["numpy"] = "0.0"
    elif tamper == "threads":
        pools[0]["num_threads"] = 2
    elif tamper == "core":
        pools[1]["architecture"] = "SkylakeX"
    elif tamper == "missing_julia":
        pools.pop()
    else:
        environment["python_version"] = "3.13.0"
    with pytest.raises(ValueError):
        profile.checked_environment(environment)


@pytest.mark.parametrize("name", ["native_runtime.json", "backend_sources.json"])
def test_fit_failure_requires_actual_native_runtime_and_sources(
    tmp_path, monkeypatch, name
):
    monkeypatch.setattr(profile, "numerical_environment", lambda *args, **kwargs: None)
    output = failed_member(
        tmp_path, phase="fit", error="OverflowError: ordinary range", timed_out=False
    )
    assert profile.verify_member(output)["status"] == "fit_error"
    (output / name).unlink()
    rebind_checksums(output)
    with pytest.raises(ValueError, match="actual native"):
        profile.verify_member(output)


@pytest.mark.parametrize("phase", ["worker_start", "fit"])
def test_any_present_backend_source_contradiction_blocks_failure(
    tmp_path, monkeypatch, phase
):
    monkeypatch.setattr(profile, "numerical_environment", lambda *args, **kwargs: None)
    output = failed_member(
        tmp_path,
        phase=phase,
        error=None if phase == "worker_start" else "OverflowError: ordinary range",
    )
    _write_json(output / "backend_sources.json", {"pysr/sr.py": "wrong actual backend"})
    rebind_checksums(output)
    with pytest.raises(ValueError, match="actual native"):
        profile.verify_member(output)


def native_front(tmp_path):
    directory = tmp_path / "pysr/search"
    directory.mkdir(parents=True)
    (directory / "hall_of_fame.csv").write_text(
        'Complexity,Loss,Equation\n1,0.5,"1.0"\n2,0.25,"cos(t)"\n'
    )
    return [
        {
            "loss": 0.5,
            "complexity": 1,
            "display_equation": "1.0",
            "tree": {"kind": "constant", "value_hex": float(1).hex()},
        },
        {
            "loss": 0.25,
            "complexity": 2,
            "display_equation": "cos(t)",
            "tree": {
                "kind": "operator",
                "arity": 1,
                "operator_index": 3,
                "operator": "cos",
                "children": [{"kind": "variable", "index": 1}],
            },
        },
    ]


@pytest.mark.parametrize(
    "mutation", ["truncated", "complexities", "loss", "reordered", "equation", "tree"]
)
def test_native_end_front_binds_all_original_candidates_and_complexity(
    tmp_path, mutation
):
    candidates = native_front(tmp_path)
    profile.verify_front(tmp_path, candidates)
    if mutation == "truncated":
        candidates.pop()
    elif mutation == "complexities":
        for candidate in candidates:
            candidate["complexity"] += 100
    elif mutation == "loss":
        candidates[0]["loss"] = 0.0
    elif mutation == "reordered":
        candidates.reverse()
    elif mutation == "equation":
        candidates[1]["display_equation"] = "1.0"
    else:
        candidates[1]["tree"] = {"kind": "constant", "value_hex": float(1).hex()}
    with pytest.raises(ValueError, match="native end front"):
        profile.verify_front(tmp_path, candidates)


# Original first technical weighted worker, seed 20261401: final native rows.
NATIVE_FRONT_REFERENCES = json.loads(r"""
[{"loss":0.14154173548802765,"complexity":1,"display_equation":"1.0228329336721003","tree":{"kind":"constant","value_hex":"0x1.05d8610f64b66p+0"}},{"loss":0.12967785521564792,"complexity":3,"display_equation":"1.0228329336721003 + -0.417920315860959","tree":{"arity":2,"children":[{"kind":"constant","value_hex":"0x1.05d8610f64b66p+0"},{"kind":"constant","value_hex":"-0x1.abf34da3d3c5cp-2"}],"kind":"operator","operator":"+","operator_index":1}},{"loss":0.07684836838706577,"complexity":4,"display_equation":"cos(-0.731988397702203 * t)","tree":{"arity":1,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.76c72eea5d640p-1"},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"cos","operator_index":3}},{"loss":0.009950917062857433,"complexity":6,"display_equation":"cos(-0.0415222619010015) + (-0.731988397702203 * t)","tree":{"arity":2,"children":[{"arity":1,"children":[{"kind":"constant","value_hex":"-0x1.54267e9d76c50p-5"}],"kind":"operator","operator":"cos","operator_index":3},{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.76c72eea5d640p-1"},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"+","operator_index":1}},{"loss":0.007103116176267246,"complexity":8,"display_equation":"cos(-0.0415222619010015) + ((-0.0415222619010015 + -0.731988397702203) * t)","tree":{"arity":2,"children":[{"arity":1,"children":[{"kind":"constant","value_hex":"-0x1.54267e9d76c50p-5"}],"kind":"operator","operator":"cos","operator_index":3},{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.54267e9d76c50p-5"},{"kind":"constant","value_hex":"-0x1.76c72eea5d640p-1"}],"kind":"operator","operator":"+","operator_index":1},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"+","operator_index":1}},{"loss":4.10520882311232e-22,"complexity":9,"display_equation":"(0.8487147958204526 + 0.1512852041490713) + ((-1.0000000000280376 * t) * t)","tree":{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"0x1.b28abee75c3e2p-1"},{"kind":"constant","value_hex":"0x1.35d5046182f57p-3"}],"kind":"operator","operator":"+","operator_index":1},{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.000000001ed3ep+0"},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"+","operator_index":1}},{"loss":1.355517978648141e-24,"complexity":10,"display_equation":"cos((-0.035671372619899146 + -0.726137508421066) * t) + (-0.7235886486331108 * t)","tree":{"arity":2,"children":[{"arity":1,"children":[{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.24384a59c9e7dp-5"},{"kind":"constant","value_hex":"-0x1.73c84ba62282ap-1"}],"kind":"operator","operator":"+","operator_index":1},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"cos","operator_index":3},{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.727a361b45a7dp-1"},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"+","operator_index":1}},{"loss":1.3037497367075503e-25,"complexity":15,"display_equation":"(0.6639662723760636 + 0.3360337276234908) + (((((-0.3521410111588249 + -0.6478589888401889) * t) * t) * t) * t)","tree":{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"0x1.53f3632301233p-1"},{"kind":"constant","value_hex":"0x1.581939b9fbc40p-2"}],"kind":"operator","operator":"+","operator_index":1},{"arity":2,"children":[{"arity":2,"children":[{"arity":2,"children":[{"arity":2,"children":[{"arity":2,"children":[{"kind":"constant","value_hex":"-0x1.6897a73a07b46p-2"},{"kind":"constant","value_hex":"-0x1.4bb42c62f9faap-1"}],"kind":"operator","operator":"+","operator_index":1},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3},{"index":1,"kind":"variable"}],"kind":"operator","operator":"*","operator_index":3}],"kind":"operator","operator":"+","operator_index":1}}]
""")


def write_native_reference_front(output, candidates):
    directory = output / "pysr/search"
    directory.mkdir(parents=True)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Complexity", "Loss", "Equation"])
    for candidate in candidates:
        writer.writerow(
            [
                candidate["complexity"],
                repr(candidate["loss"]),
                candidate["display_equation"],
            ]
        )
    (directory / "hall_of_fame.csv").write_text(stream.getvalue())


@pytest.mark.parametrize("candidate", NATIVE_FRONT_REFERENCES)
def test_actual_native_equation_roundtrips_exact_binary64_tree(tmp_path, candidate):
    write_native_reference_front(tmp_path, [candidate])
    profile.verify_front(tmp_path, [candidate])
    assert profile.equation_tree(candidate["display_equation"]) == candidate["tree"]


def test_grid_equivalent_ast_rewrite_cannot_replace_original_native_formula(tmp_path):
    candidates = copy.deepcopy(NATIVE_FRONT_REFERENCES)
    write_native_reference_front(tmp_path, candidates)
    original = copy.deepcopy(candidates[-1]["tree"])
    changed = candidates[-1]["tree"]
    changed["children"][1]["children"][1] = {
        "kind": "constant",
        "value_hex": float(1).hex(),
    }
    assert profile._node_count(original) == profile._node_count(changed) == 15
    times = np.array([0.0, 1.0])
    np.testing.assert_array_equal(
        symbolic.evaluate_tree(original, times), symbolic.evaluate_tree(changed, times)
    )
    assert (
        symbolic.evaluate_tree(original, [0.5])[0]
        != symbolic.evaluate_tree(changed, [0.5])[0]
    )
    with pytest.raises(ValueError, match="native end front"):
        profile.verify_front(tmp_path, candidates)


@pytest.mark.parametrize(
    "equation",
    [
        "__import__('os').system('echo bad')",
        "t.__class__",
        "[t]",
        "t ** 2",
        "abs(t)",
        "cos(t, 1)",
        "cos(value=t)",
        "True",
        "1e999",
        "-t",
        " + ".join(["t"] * 11),
    ],
)
def test_native_equation_parser_is_bounded_and_never_evaluates_code(equation):
    with pytest.raises(ValueError):
        profile.equation_tree(equation)
