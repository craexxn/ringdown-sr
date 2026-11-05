"""Independent signal references, phase-sensitive parameter checks, and fixed design."""

import copy
import itertools
import math
import subprocess
from collections import Counter

import mpmath as mp
import numpy as np
import pytest
import test_search_duration as duration_tests
from test_local_optimizer import option_fixture
from test_noiseless_control import BACKEND_SEEDS, candidate, reference_tree
from test_noiseless_control import DRIVER as OLD

from ringdown_sr import outer_search_ladder as prior
from ringdown_sr import transfer_check as control
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.noiseless_control import parameter_match
from ringdown_sr.pilot import _sha256
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.symbolic import SearchBudget

NATIVE_SEEDS = {20261210: 1040546249, 20261211: 315614060, 20261212: 2067734657}


@pytest.fixture(scope="module")
def diagnoses():
    return duration_tests.diagnoses.__wrapped__()


@pytest.fixture(autouse=True)
def seed_mapping(monkeypatch):
    for seed, native in NATIVE_SEEDS.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)


def test_bound_plan_input_bytes_order_and_unchanged_profile():
    assert control.SEEDS == (20261210, 20261211, 20261212)
    assert set(control.SEEDS).isdisjoint(prior.SEEDS)
    assert {s: backend_seed(s) for s in control.SEEDS} == NATIVE_SEEDS
    assert (control.LIMIT_SECONDS, control.WORKER_LIMIT_SECONDS) == (7200, 900)
    cells = control.planned_cells()
    assert [c["signal"] for c in cells] == [
        "anchor",
        "frequency",
        "decay",
        "phase",
        "amplitude",
        "combined",
        "decay",
        "phase",
        "amplitude",
        "combined",
        "anchor",
        "frequency",
        "amplitude",
        "combined",
        "anchor",
        "frequency",
        "decay",
        "phase",
    ]
    assert Counter((c["signal"], c["budget"]["seed"]) for c in cells) == dict.fromkeys(
        itertools.product(control.SIGNALS, control.SEEDS), 1
    )
    common = None
    for c in cells:
        assert c["budget"]["niterations"] == 500
        assert c["condition"] == "local_300_5" and c["grammar"] == "unrestricted"
        actual = control.profile_parameters(SearchBudget(**c["budget"]), c["condition"])
        assert actual == prior.profile_parameters(
            SearchBudget(**c["budget"]), "local_300_5"
        )
        assert (
            actual["optimizer_iterations"] == 300 and actual["optimizer_nrestarts"] == 5
        )
        current = control.common_parameters(actual)
        assert common is None or common == current
        common = current
    assert common["niterations"] == 500 and common["should_simplify"] is False
    assert len(control.search_profiles()) == 18
    for name, digest in (
        (control.PLAN, control.PLAN_SHA256),
        (control.INPUT, control.INPUT_SHA256),
        (control.INPUT_MANIFEST, control.MANIFEST_SHA256),
    ):
        contents = (control.ROOT / name).read_bytes()
        assert _sha256(contents) == digest
        assert (
            subprocess.check_output(
                ["git", "show", f"{control.PLAN_COMMIT}:{name}"], cwd=control.ROOT
            )
            == contents
        )
    assert control.source_hashes()[control.INPUT] == control.INPUT_SHA256


def test_all_frozen_values_against_independent_high_precision_formula():
    _, arrays = control.read_inputs(control.ROOT / control.INPUT)
    assert arrays["observed"].shape == (6, 128)
    assert arrays["diagnostic_truth"].shape == (6, 889)
    np.testing.assert_array_equal(arrays["time_s"], np.arange(128) / 4096)
    expected_inner = np.array(
        [(8 * j + k) / 32768 for j in range(127) for k in range(1, 8)]
    )
    np.testing.assert_array_equal(arrays["diagnostic_time_s"], expected_inner)
    assert all(not v.flags.writeable for v in arrays.values())
    with mp.workdps(80):
        for index, signal in enumerate(control.SIGNALS):
            p = control.reference_truth(signal)
            a, f, tau, phase = [
                mp.mpf(p[k])
                for k in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
            ]
            for ts, ys in (
                (arrays["time_s"], arrays["observed"][index]),
                (arrays["diagnostic_time_s"], arrays["diagnostic_truth"][index]),
            ):
                for t, y in zip(ts, ys, strict=True):
                    expected = (
                        a
                        * mp.exp(-mp.mpf(float(t)) / tau)
                        * mp.cos(2 * mp.pi * f * mp.mpf(float(t)) + phase)
                    )
                    assert abs(mp.mpf(float(y)) - expected) / a < mp.mpf("1e-13")


def test_bundle_mutation_rejected_without_regeneration(tmp_path):
    path = tmp_path / "wrong.npz"
    data = bytearray((control.ROOT / control.INPUT).read_bytes())
    data[len(data) // 2] ^= 1
    path.write_bytes(data)
    with pytest.raises(ValueError, match="bundle changed"):
        control.read_inputs(path)


@pytest.mark.parametrize("signal", control.SIGNALS)
@pytest.mark.parametrize("sign,turns", [(1, 0), (1, 2), (-1, 0)])
def test_signed_amplitude_phase_truth_and_original_tree(signal, sign, turns):
    _, root = control.read_inputs(control.ROOT / control.INPUT)
    arrays = control.arrays_for_cell(root, {"signal": signal})
    truth = control.reference_truth(signal)
    tree = reference_tree(
        amplitude=sign * truth["amplitude"],
        frequency=truth["frequency_hz"],
        rate=-1 / truth["decay_time_s"],
        phase=truth["phase_rad"] + (math.pi if sign == -1 else 0) + turns * math.tau,
    )
    original = copy.deepcopy(tree)
    result = diagnose_candidate(
        candidate(tree, arrays),
        0,
        0,
        arrays,
        "complexity_frequency",
        extended_structure=True,
        truth=truth,
    )
    assert tree == original
    assert result["curve_marker"] == "within_tolerance"
    assert result["parameter_match"]["status"] == "matched"
    assert max(result["parameter_match"]["errors"].values()) < 1e-12
    if signal != "anchor":
        assert parameter_match(result["physical_analysis"])["status"] == "mismatched"
    else:
        assert parameter_match(result["physical_analysis"]) == result["parameter_match"]


@pytest.mark.parametrize(
    "delta,matched", [(0, True), (0.009, True), (0.011, False), (math.pi, False)]
)
def test_phase_distance_matches_independent_chord_length(delta, matched):
    truth = control.reference_truth("combined")
    _, root = control.read_inputs(control.ROOT / control.INPUT)
    arrays = control.arrays_for_cell(root, {"signal": "combined"})
    tree = reference_tree(
        amplitude=0.6, frequency=180, rate=-1 / 0.012, phase=-0.9 + delta
    )
    analysis = diagnose_candidate(
        candidate(tree, arrays), 0, 0, arrays, "complexity_frequency", truth=truth
    )["physical_analysis"]
    result = parameter_match(analysis, truth=truth)
    assert result["errors"]["complex_amplitude"] == pytest.approx(
        2 * abs(math.sin(delta / 2)), abs=1e-14
    )
    assert (result["status"] == "matched") is matched


@pytest.mark.parametrize(
    "factor,matched", [(1.009, True), (1.011, False), (0.989, False)]
)
def test_amplitude_error_is_relative_to_each_reference(factor, matched):
    truth = control.reference_truth("amplitude")
    _, root = control.read_inputs(control.ROOT / control.INPUT)
    arrays = control.arrays_for_cell(root, {"signal": "amplitude"})
    tree = reference_tree(amplitude=0.4 * factor)
    result = diagnose_candidate(
        candidate(tree, arrays), 0, 0, arrays, "complexity_frequency", truth=truth
    )["parameter_match"]
    assert result["errors"]["amplitude"] == pytest.approx(abs(factor - 1))
    assert (result["status"] == "matched") is matched


@pytest.mark.parametrize("fault", ["raw_replay", "alias_replay", "structure", "field"])
def test_general_truth_keeps_unresolved_parameter_gates(diagnoses, fault):
    analysis = copy.deepcopy(diagnoses[1]["physical_analysis"])
    if fault in ("raw_replay", "alias_replay"):
        analysis[fault]["status"] = "failed"
    elif fault == "structure":
        analysis["structure"]["structure_status"] = "not_supported"
    else:
        analysis["raw_parameters"]["amplitude"]["status"] = "numerical_unresolved"
    result = parameter_match(analysis, truth=control.reference_truth("phase"))
    assert result["status"] == "not_assessed"
    assert all(v is None for v in result["errors"].values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("amplitude", 0),
        ("frequency_hz", -1),
        ("decay_time_s", 0),
        ("phase_rad", math.inf),
        ("amplitude", True),
    ],
)
def test_invalid_reference_parameters_fail(diagnoses, field, value):
    truth = control.reference_truth("anchor")
    truth[field] = value
    with pytest.raises(ValueError):
        parameter_match(diagnoses[1]["physical_analysis"], truth=truth)


@pytest.mark.parametrize("seed", tuple(NATIVE_SEEDS))
def test_exact_native_profile_and_all_seed_bits(seed):
    record = option_fixture(seed, "local_300_5")
    control.verify_options(record, seed, "local_300_5", OLD, OLD.load_support())
    for field in record["backend_options"]:
        if field["name"] == "optimizer_nrestarts":
            field["value"] = "2"
    with pytest.raises(ValueError):
        control.verify_options(record, seed, "local_300_5", OLD, OLD.load_support())


def completed(diagnoses, state):
    cells = control.planned_cells()
    for c in cells:
        value = state(c)
        chosen = copy.deepcopy(diagnoses[int(value > 0)])
        if value == 1:
            chosen["parameter_match"]["status"] = "not_assessed"
        unselected = copy.deepcopy(diagnoses[1])
        unselected.update(source_index=1, is_selected=False)
        c.update(
            status="completed",
            diagnostics={"selected_index": 0, "candidates": [chosen, unselected]},
        )
    return cells


def test_all_paired_curve_support_directions_and_denominators(diagnoses):
    # Nine distinct state pairs, rotated over all variants and three seeds.
    states = tuple(itertools.product(range(3), repeat=2))
    for offset in range(9):

        def state(c, offset=offset):
            seed = control.SEEDS.index(c["budget"]["seed"])
            variant = control.SIGNALS.index(c["signal"])
            return (
                states[(offset + seed) % 9][0]
                if variant == 0
                else states[(offset + seed + variant - 1) % 9][1]
            )

        cells = completed(diagnoses, state)
        result = control.comparison(cells, final_verified=True)
        assert len(result["pair_differences"]) == 15
        for signal, summary in result["summaries"].items():
            group = [c for c in cells if c["signal"] == signal]
            assert summary["count"] == 3
            assert summary["curve_successes"] == sum(state(c) > 0 for c in group)
            assert summary["supported_reconstructions"] == sum(
                state(c) == 2 for c in group
            )
            assert summary["unselected_curve_successes"] == 3
        for signal in control.SIGNALS[1:]:
            contrast = result["comparison"]["contrasts"][signal + "_minus_anchor"]
            for name, predicate in (
                ("curve", lambda n: n > 0),
                ("supported", lambda n: n == 2),
            ):
                pairs = [
                    (
                        state(
                            next(
                                c
                                for c in cells
                                if c["signal"] == s and c["budget"]["seed"] == seed
                            )
                        )
                    )
                    for seed in control.SEEDS
                    for s in ("anchor", signal)
                ]
                assert contrast[name + "_difference"] == sum(
                    predicate(pairs[i + 1]) - predicate(pairs[i])
                    for i in range(0, 6, 2)
                )
                assert contrast[name + "_transitions"] == {
                    f"{a}->{b}": sum(
                        predicate(pairs[i]) == bool(a)
                        and predicate(pairs[i + 1]) == bool(b)
                        for i in range(0, 6, 2)
                    )
                    for a in (0, 1)
                    for b in (0, 1)
                }


@pytest.mark.parametrize(
    "fault", ["pending", "missing", "failed", "order", "signal", "budget"]
)
def test_incomplete_or_changed_design_cannot_release_comparisons(diagnoses, fault):
    cells = completed(diagnoses, lambda c: 2)
    if fault == "missing":
        cells.pop()
    if fault == "failed":
        cells[-1]["status"] = "failed"
    if fault == "order":
        cells.reverse()
    if fault == "signal":
        cells[0]["signal"] = "phase"
    if fault == "budget":
        cells[0]["budget"]["niterations"] = 1000
    if fault in ("order", "signal", "budget"):
        with pytest.raises(ValueError):
            control.comparison(cells, final_verified=True)
    else:
        assert all(
            v is None
            for v in control.comparison(
                cells, final_verified=fault != "pending"
            ).values()
        )


def test_missing_metrics_unselected_successes_and_costs_do_not_imply_success(diagnoses):
    cells = completed(diagnoses, lambda c: 0)
    control.selected(cells[0])["curve_errors"]["diagnostic"].update(
        status="not_available", relative_rms=None, relative_max=None
    )
    for c in cells:
        c["diagnostics"].update(
            worker_wall_seconds=c["number"] * 2.0,
            callback_calls_during_fit=c["number"] * 10,
        )
    result = control.comparison(cells, final_verified=True)
    assert all(
        s["curve_successes"] == s["supported_reconstructions"] == 0
        for s in result["summaries"].values()
    )
    assert (
        result["summaries"]["anchor"]["statistics"]["diagnostic/relative_rms"][
            "finite_count"
        ]
        == 2
    )
    for pair in result["pair_differences"]:
        assert pair["cost_changes"]["worker_wall_seconds"]["difference"] == 2.0 * (
            pair["second_cell"] - pair["first_cell"]
        )
    assert (
        result["pair_differences"][0]["metrics"]["diagnostic/relative_rms"][
            "difference"
        ]
        is None
    )
