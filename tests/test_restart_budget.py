"""Independent package, cost and decision boundaries for the frozen comparison."""

import copy

import pytest

from ringdown_sr import restart_budget as budget
from ringdown_sr import restart_budget_profile as profile


def cells(name="anchor", technical=False):
    return [
        {
            "plan": plan,
            "status": "completed",
            "A": True,
            "A_and_original_family": True,
            "curve_grade": "A",
            "original_family_status": "proven_member",
            "any_front_A": True,
            "selected": {"loss": 0.01 + plan["member"], "complexity": 9},
            "costs": {
                key: (10 + plan["number"]) * (i + 1)
                for i, key in enumerate(budget.previous.COST_FIELDS)
            },
        }
        for plan in profile.plans(name, technical)
    ]


def members(data, arm, block=1):
    return [c for c in data if c["plan"]["arm"] == arm and c["plan"]["block"] == block]


def sections():
    return [
        {
            "signal": name,
            "scope": "scientific",
            "comparison": budget.comparison(cells(name), name),
        }
        for name in profile.names()
    ]


def test_forty_eight_fresh_calls_have_nested_seed_pairs_and_equal_iteration_sums():
    seen, calls, outputs, iterations = set(), 0, 0, 0
    expected_blocks = {"anchor": 2, "variant_low": 2, "variant_high": 4}
    assert profile.names() == list(expected_blocks)
    for name, blocks in expected_blocks.items():
        plans = profile.plans(name)
        assert len(plans) == blocks * 6
        assert [p["number"] for p in plans] == list(range(1, 6 * blocks + 1))
        for block in range(1, blocks + 1):
            group = [p for p in plans if p["block"] == block]
            restart = [p for p in group if p["arm"] == "R"]
            long = [p for p in group if p["arm"] == "L"]
            assert len(restart) == 4 and len(long) == 2
            assert [p["member"] for p in restart] == [0, 1, 2, 3]
            assert [p["member"] for p in long] == [0, 1]
            assert [p["arm"] for p in group] == (
                ["R"] * 4 + ["L"] * 2 if block % 2 else ["L"] * 2 + ["R"] * 4
            )
            seeds = [p["seed"] for p in restart]
            assert seeds == profile.case(name)["seeds"][block - 1]
            assert [p["seed"] for p in long] == seeds[:2]
            assert len(set(seeds)) == 4 and not set(seeds) & seen
            assert all(type(seed) is int and 0 < seed < 2**31 for seed in seeds)
            seen.update(seeds)
            for paired in range(2):
                assert restart[paired]["number"] != long[paired]["number"]
            assert all(p["niterations"] == 1000 for p in restart)
            assert all(p["niterations"] == 2000 for p in long)
            assert sum(p["niterations"] for p in restart) == 4000
            assert sum(p["niterations"] for p in long) == 4000
            assert all(
                p["condition"] == "iterations" and p["signal"] == name for p in group
            )
            iterations += sum(p["niterations"] for p in group)
            outputs += 2
        calls += len(plans)
    assert (calls, outputs, len(seen), iterations) == (48, 16, 32, 64000)


def test_two_tiny_fixtures_exercise_both_complete_packages():
    plans = [p for name in profile.names(True) for p in profile.plans(name, True)]
    assert len(profile.names(True)) == 2 and len(plans) == 12
    assert all(p["block"] == 1 for p in plans)
    assert sum(p["arm"] == "R" and p["niterations"] == 1 for p in plans) == 8
    assert sum(p["arm"] == "L" and p["niterations"] == 2 for p in plans) == 4
    assert not {p["signal"] for p in plans} & set(profile.names())


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "seed",
        "signal",
        "order",
        "unfinished",
        "member",
        "iterations",
        "arm",
    ],
)
def test_changed_or_incomplete_plan_cannot_release(fault):
    data = cells()
    if fault == "missing":
        data.pop()
    elif fault == "duplicate":
        data[-1] = copy.deepcopy(data[0])
    elif fault == "order":
        data[0], data[1] = data[1], data[0]
    elif fault == "unfinished":
        data[0]["status"] = "running"
    else:
        key, value = {
            "seed": ("seed", data[0]["plan"]["seed"] + 1),
            "signal": ("signal", "variant_low"),
            "member": ("member", 1),
            "iterations": ("niterations", 2000),
            "arm": ("arm", "L"),
        }[fault]
        data[0]["plan"][key] = value
    with pytest.raises(ValueError, match="every planned"):
        budget.comparison(data, "anchor")


@pytest.mark.parametrize("arm", ["R", "L"])
def test_package_choice_uses_only_original_native_loss_complexity_and_member(arm):
    data = members(cells(), arm)
    for cell in data:
        cell["selected"] = {"loss": 0.1, "complexity": 10}
    data[-1]["selected"]["loss"] = 0.0
    data[-1].update(
        A=False,
        A_and_original_family=False,
        curve_grade="D",
        original_family_status="unresolved",
        any_front_A=False,
    )
    data[-1]["irregular_errors"] = {"relative_rms": 1000.0}
    expected = data[-1]["plan"]["number"]
    output = budget.selected_output(list(reversed(data)))
    assert output["selected_cell"] == expected and not output["A"]
    assert output["any_front_A"]  # Presence elsewhere is a separate diagnostic.
    data[-1]["selected"]["loss"] = 0.1
    data[-1]["selected"]["complexity"] = 9
    assert budget.selected_output(data)["selected_cell"] == expected
    for cell in data:
        cell["selected"]["complexity"] = 9
    assert (
        budget.selected_output(list(reversed(data)))["selected_cell"]
        == data[0]["plan"]["number"]
    )


@pytest.mark.parametrize("arm", ["R", "L"])
@pytest.mark.parametrize(
    "loss", [float("nan"), float("inf"), float("-inf"), -1.0, True, "0.0", None]
)
def test_invalid_original_loss_cannot_win_either_package(arm, loss):
    data = members(cells(), arm)
    data[0]["selected"]["loss"] = loss
    assert budget.selected_output(data)["selected_cell"] == data[1]["plan"]["number"]


@pytest.mark.parametrize("complexity", [True, 0, -1, 2.5, "3"])
def test_invalid_original_complexity_cannot_be_used_for_package_choice(complexity):
    data = members(cells(), "L")
    data[0]["selected"]["complexity"] = complexity
    with pytest.raises(ValueError, match="complexity"):
        budget.selected_output(data)


@pytest.mark.parametrize("arm,size", [("R", 4), ("L", 2)])
def test_one_failed_member_retains_costs_and_one_package_denominator(arm, size):
    data = cells()
    group = members(data, arm)
    group[0].update(status="worker_failed", A=False, A_and_original_family=False)
    group[0].pop("selected")
    group[0]["costs"]["worker_wall_seconds"] = None
    result = budget.comparison(data, "anchor")
    output = result["pairs"][0]["outputs"][arm]
    assert len(output["members"]) == size and output["failed_members"] == 1
    assert output["selected_cell"] == group[1]["plan"]["number"]
    assert output["costs"]["callback_calls_during_fit"] == sum(
        c["costs"]["callback_calls_during_fit"] for c in group
    )
    assert output["costs"]["worker_wall_seconds"] is None
    assert result["totals"][arm]["denominator"] == 2
    assert result["totals"][arm]["failures"] == 0
    assert result["totals"][arm]["A_and_original_family"] == 2
    assert result["totals"][arm]["costs"]["worker_wall_seconds"] is None
    assert result["all_costs_observed"] is False


@pytest.mark.parametrize("arm,size", [("R", 4), ("L", 2)])
@pytest.mark.parametrize("fault", ["worker_failed", "no_finite_loss"])
def test_no_eligible_member_is_one_failed_package_with_all_member_costs(
    arm, size, fault
):
    data = cells()
    group = members(data, arm)
    for cell in group:
        if fault == "worker_failed":
            cell.update(status="worker_failed", A=False, A_and_original_family=False)
            cell.pop("selected")
        else:
            cell["selected"]["loss"] = float("nan")
    result = budget.comparison(data, "anchor")
    output = result["pairs"][0]["outputs"][arm]
    assert output["status"] == "worker_failed" and output["selected_cell"] is None
    assert not output["A"] and not output["A_and_original_family"]
    assert output["curve_grade"] == "no_output"
    assert result["totals"][arm]["denominator"] == 2
    assert result["totals"][arm]["failures"] == 1
    assert result["totals"][arm]["A"] == 1
    assert output["failed_members"] == (size if fault == "worker_failed" else 0)
    for key in budget.previous.COST_FIELDS:
        assert output["costs"][key] == sum(c["costs"][key] for c in group)


@pytest.mark.parametrize("field", budget.previous.COST_FIELDS)
@pytest.mark.parametrize("value", [-1.0, True, float("nan"), float("inf")])
def test_invalid_cost_in_unselected_member_blocks_the_comparison(field, value):
    data = cells()
    members(data, "R")[-1]["costs"][field] = value
    with pytest.raises(ValueError, match="cost"):
        budget.comparison(data, "anchor")


def test_callback_counts_must_be_integer_and_unknown_is_not_zero():
    data = cells()
    members(data, "L")[-1]["costs"]["callback_calls_during_fit"] = 1.5
    with pytest.raises(ValueError, match="cost"):
        budget.comparison(data, "anchor")
    members(data, "L")[-1]["costs"]["callback_calls_during_fit"] = None
    report = budget.comparison(data, "anchor")
    assert report["totals"]["L"]["costs"]["callback_calls_during_fit"] is None
    assert report["totals"]["R"]["costs"]["callback_calls_during_fit"] > 0
    assert report["all_costs_observed"] is False


@pytest.mark.parametrize(
    "name,denominator", [("anchor", 2), ("variant_low", 2), ("variant_high", 4)]
)
def test_packages_not_members_define_endpoints_and_all_arm_costs(name, denominator):
    data = cells(name)
    report = budget.comparison(data, name)
    assert report["algorithm_outputs"] == 2 * denominator
    assert len(report["pairs"]) == denominator
    assert report["automatic_execution"] is False
    assert (
        "R_meets_signal_threshold" not in report
        and "descriptive_preference" not in report
    )
    for arm in ["R", "L"]:
        totals = report["totals"][arm]
        assert (
            totals["denominator"]
            == totals["A"]
            == totals["A_and_original_family"]
            == denominator
        )
        assert totals["failures"] == totals["failed_members"] == 0
        for key in budget.previous.COST_FIELDS:
            expected = sum(c["costs"][key] for c in data if c["plan"]["arm"] == arm)
            assert totals["costs"][key] == expected
    for pair, seeds in zip(report["pairs"], profile.case(name)["seeds"], strict=True):
        assert pair["seeds"] == seeds
        assert len(pair["outputs"]["R"]["members"]) == 4
        assert len(pair["outputs"]["L"]["members"]) == 2


def test_paired_gains_losses_and_ties_are_not_pooled_across_members():
    data = cells("variant_high")
    members(data, "L", 1)[0].update(A=False, A_and_original_family=False)
    members(data, "R", 2)[0].update(A_and_original_family=False)
    members(data, "R", 3)[0].update(A=False, A_and_original_family=False)
    members(data, "L", 3)[0].update(A=False, A_and_original_family=False)
    report = budget.comparison(data, "variant_high")
    assert report["R_minus_L"]["A"] == {"gains": 1, "losses": 0, "ties": 3}
    assert report["R_minus_L"]["A_and_original_family"] == {
        "gains": 1,
        "losses": 1,
        "ties": 2,
    }


@pytest.mark.parametrize(
    "weaker,expected", [("L", "restart_candidate"), ("R", "long_candidate")]
)
def test_direction_requires_joint_gain_and_no_loss_on_any_signal_endpoint(
    weaker, expected
):
    data = sections()
    data[2]["comparison"]["totals"][weaker]["A_and_original_family"] -= 1
    assert budget.development_decision(data) == expected
    stronger = "R" if weaker == "L" else "L"
    data[0]["comparison"]["totals"][stronger].update(A=1, A_and_original_family=1)
    assert budget.development_decision(data) == "mixed"


def test_equal_counts_and_curve_only_gain_never_use_costs_to_choose_a_winner():
    data = sections()
    for section in data:
        section["comparison"]["totals"]["R"]["costs"] = {
            key: None for key in budget.previous.COST_FIELDS
        }
    assert budget.development_decision(data) == "unchanged_counts"
    for arm in ["R", "L"]:
        data[2]["comparison"]["totals"][arm]["A_and_original_family"] = 3
    data[2]["comparison"]["totals"]["L"]["A"] = 3
    assert budget.development_decision(data) == "mixed"


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate_signal",
        "technical",
        "denominator",
        "bool_count",
        "negative_count",
        "joint_above_A",
        "A_above_denominator",
    ],
)
def test_decision_requires_every_scientific_signal_and_valid_integer_counts(fault):
    data = sections()
    if fault == "missing":
        data.pop()
    elif fault == "duplicate_signal":
        data[2] = copy.deepcopy(data[0])
    elif fault == "technical":
        data[0]["scope"] = "technical"
    else:
        count = data[0]["comparison"]["totals"]["R"]
        if fault == "denominator":
            count["denominator"] = 4
        elif fault == "bool_count":
            count["A"] = True
        elif fault == "negative_count":
            count["A_and_original_family"] = -1
        elif fault == "joint_above_A":
            count["A"] = 1
        else:
            count["A"] = 3
    with pytest.raises(ValueError):
        budget.development_decision(data)
