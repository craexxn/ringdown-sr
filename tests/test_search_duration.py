"""Independent design, invocation and paired endpoint counterexamples."""

import copy
import itertools
import subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_noiseless_control import candidate, reference_tree
from test_structure import constant

from ringdown_sr import search_duration as control
from ringdown_sr import trigonometric_grammar as grammar
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.symbolic import SearchBudget


def test_fresh_module_uses_source_despite_valid_timestamp_cached_bytecode(tmp_path):
    import os
    import py_compile

    path = tmp_path / "module.py"
    path.write_text("value = 1\n")
    original = path.stat()
    cached = py_compile.compile(str(path), doraise=True)
    path.write_text("value = 2\n")
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
    before = Path(cached).read_bytes()
    loaded = control.load_module(path, "duration_source_test")
    assert loaded.value == 2
    assert Path(cached).read_bytes() == before


def test_bound_plan_factorial_design_and_unchanged_shared_policy():
    cells = control.planned_cells()
    assert control.SEEDS == tuple(range(20261103, 20261108))
    assert (control.LIMIT_SECONDS, control.WORKER_LIMIT_SECONDS) == (7200, 600)
    assert len(cells) == 20
    labels = [(c["condition"], c["budget"]["niterations"]) for c in cells]
    k, a = "unrestricted", "no_nested_trig"
    conditions = [(k, 200), (a, 200), (k, 2000), (a, 2000)]
    assert labels == [
        conditions[i]
        for i in (0, 1, 3, 2, 1, 2, 0, 3, 2, 3, 1, 0, 3, 0, 2, 1, 0, 1, 3, 2)
    ]
    assert Counter(labels) == dict.fromkeys(conditions, 5)
    for p in range(4):
        assert set(labels[p:16:4]) == set(conditions)
    transitions = [(labels[i], labels[i + 1]) for i in range(16) if i % 4 != 3]
    assert len(set(transitions)) == 12
    assert all(a != b for a, b in transitions)
    common = None
    for cell in cells:
        budget = SearchBudget(**cell["budget"])
        profile = control.profile_parameters(budget, cell["condition"])
        assert profile == grammar.profile_parameters(budget, cell["condition"])
        assert profile["niterations"] == budget.niterations
        assert profile["optimizer_iterations"] == 100
        current = control.common_parameters(profile)
        assert common is None or current == common
        common = current
    assert len(control.search_profiles()) == 20
    contents = (control.ROOT / control.PLAN).read_bytes()
    assert _sha256(contents) == control.PLAN_SHA256
    assert (
        subprocess.check_output(
            ["git", "show", f"{control.PLAN_COMMIT}:{control.PLAN}"], cwd=control.ROOT
        )
        == contents
    )
    assert len(grammar.planned_cells()) == 6


def invocation_kwargs(iterations=2000):
    return {
        "niterations": iterations,
        "parallelism": "serial",
        "return_state": True,
        "saved_state": None,
        "guesses": None,
        "weights": None,
    }


def test_invocation_guard_preserves_arguments_result_and_other_attributes():
    calls, result, options, x, y = [], object(), object(), object(), object()

    def invoke(*args, **kwargs):
        calls.append((args, kwargs))
        return result

    backend = SimpleNamespace(
        equation_search=SimpleNamespace(_jl_call_nogil=invoke), Options=options
    )
    guard = control.SearchInvocationGuard(backend, 2000)
    assert guard.Options is options
    assert (
        guard.equation_search._jl_call_nogil(
            x, y, **invocation_kwargs(), options=options
        )
        is result
    )
    assert calls == [((x, y), {**invocation_kwargs(), "options": options})]
    assert guard.record() == control.invocation_record(2000)
    with pytest.raises(ValueError):
        guard.equation_search._jl_call_nogil(x, y, **invocation_kwargs())
    assert len(calls) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("niterations", 200),
        ("niterations", True),
        ("niterations", 2000.0),
        ("parallelism", "multithreading"),
        ("return_state", False),
        ("saved_state", object()),
        ("guesses", []),
        ("weights", []),
    ],
)
def test_actual_wrong_budget_warmstart_or_altered_search_fails_before_delegation(
    field, value
):
    guard = control.SearchInvocationGuard(object(), 2000)
    kwargs = invocation_kwargs()
    kwargs[field] = value
    with pytest.raises(ValueError):
        guard.equation_search._jl_call_nogil(object(), object(), **kwargs)
    assert guard.calls == 0
    with pytest.raises(ValueError):
        guard.record()


def test_failed_backend_call_cannot_be_reported_as_completed():
    def fail(*args, **kwargs):
        raise RuntimeError("backend failed")

    guard = control.SearchInvocationGuard(
        SimpleNamespace(equation_search=SimpleNamespace(_jl_call_nogil=fail)), 2000
    )
    with pytest.raises(RuntimeError):
        guard.equation_search._jl_call_nogil(1, 2, **invocation_kwargs())
    with pytest.raises(ValueError):
        guard.record()


@pytest.fixture(scope="module")
def diagnoses():
    arrays = frozen_data()
    return [
        diagnose_candidate(
            candidate(tree, arrays), 0, 0, arrays, "complexity_frequency"
        )
        for tree in (constant(0), reference_tree())
    ]


def completed(diagnoses, successes=None):
    cells = control.planned_cells()
    for cell in cells:
        success = bool(successes and successes(cell))
        chosen = copy.deepcopy(diagnoses[int(success)])
        unselected = copy.deepcopy(diagnoses[1])
        unselected.update(source_index=1, is_selected=False)
        cell.update(
            status="completed",
            diagnostics={"selected_index": 0, "candidates": [chosen, unselected]},
        )
    return cells


def test_all_1024_paired_success_patterns_keep_counts_and_transitions(diagnoses):
    for pattern in itertools.product((False, True), repeat=10):

        def succeeds(cell, pattern=pattern):
            index = control.SEEDS.index(cell["budget"]["seed"])
            return pattern[index + (5 if cell["budget"]["niterations"] == 2000 else 0)]

        result = control.comparison(completed(diagnoses, succeeds), final_verified=True)
        for summary in result["comparison"]["by_grammar"].values():
            assert summary["C_200"] == sum(pattern[:5])
            assert summary["C_2000"] == sum(pattern[5:])
            assert sum(summary["transitions"].values()) == 5
            assert summary["development_signal"] == (
                "supported_structure_gain"
                if sum(pattern[5:]) > sum(pattern[:5])
                else "hypothesis_not_supported"
            )
        assert result["comparison"]["count_interaction"] == 0


@pytest.mark.parametrize(
    "fault", ["parameter", "structure", "replay", "old_success_only"]
)
def test_new_supported_gain_must_belong_to_new_success_same_selection(diagnoses, fault):
    cells = completed(
        diagnoses,
        lambda c: (
            c["budget"]["seed"] == control.SEEDS[0]
            or (
                c["budget"]["niterations"] == 2000
                and c["budget"]["seed"] == control.SEEDS[1]
            )
        ),
    )
    for cell in cells:
        if cell["budget"]["seed"] != control.SEEDS[1]:
            continue
        chosen = control.selected(cell)
        if fault in ("parameter", "old_success_only"):
            chosen["parameter_match"]["status"] = "not_assessed"
        elif fault == "structure":
            chosen["search_analysis"]["structure"]["structure_status"] = "not_supported"
        else:
            chosen["physical_analysis"]["raw_replay"]["status"] = "failed"
    result = control.comparison(cells, final_verified=True)
    assert all(
        v["development_signal"] == "approximation_gain_only"
        for v in result["comparison"]["by_grammar"].values()
    )


@pytest.mark.parametrize("fault", ["final", "missing", "failed", "identity", "order"])
def test_partial_or_misidentified_series_never_unlocks_groups(diagnoses, fault):
    cells = completed(diagnoses)
    if fault == "missing":
        cells.pop()
    if fault == "failed":
        cells[-1]["status"] = "failed"
    if fault == "identity":
        cells[0]["budget"]["niterations"] = 2000
    if fault == "order":
        cells.reverse()
    if fault in ("identity", "order"):
        with pytest.raises(ValueError):
            control.comparison(cells, final_verified=True)
    else:
        assert all(
            v is None
            for v in control.comparison(cells, final_verified=fault != "final").values()
        )


def test_unselected_success_does_not_count_and_unavailable_metrics_keep_denominators(
    diagnoses,
):
    cells = completed(diagnoses)
    chosen = control.selected(cells[0])
    chosen["curve_errors"]["diagnostic"].update(
        status="not_available", reason="fixture", relative_rms=None, relative_max=None
    )
    result = control.comparison(cells, final_verified=True)
    assert len(result["pair_differences"]) == 20
    assert (
        result["summaries"]["unrestricted/200"]["statistics"][
            "diagnostic/relative_rms"
        ]["finite_count"]
        == 4
    )
    for group in result["summaries"].values():
        assert group["curve_successes"] == 0
        assert group["unselected_curve_successes"] == 5
    pair = result["pair_differences"][0]["metrics"]["diagnostic/relative_rms"]
    assert pair["difference"] is None and pair["status"] == "not_assessed"
