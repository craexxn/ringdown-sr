"""Check confirmation decisions independently of native search success."""

import copy
from math import comb

import pytest

from ringdown_sr import restart_budget_confirmation as confirmation
from ringdown_sr import restart_budget_confirmation_profile as profile


def cells(name="confirm_low", technical=False):
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
                key: (10 + plan["number"]) * (index + 1)
                for index, key in enumerate(confirmation.previous.COST_FIELDS)
            },
        }
        for plan in profile.plans(name, technical)
    ]


def members(data, arm, block=1):
    return [c for c in data if c["plan"]["arm"] == arm and c["plan"]["block"] == block]


def sections(restart=(10, 10, 10), long=(10, 10, 10)):
    result = []
    for name, r, l in zip(profile.names(), restart, long, strict=True):
        data = cells(name)
        for cell in data:
            count = r if cell["plan"]["arm"] == "R" else l
            if cell["plan"]["block"] > count:
                cell.update(
                    A_and_original_family=False, original_family_status="unresolved"
                )
        result.append(
            {
                "signal": name,
                "scope": "scientific",
                "comparison": confirmation.comparison(data, name),
            }
        )
    return result


@pytest.mark.parametrize("arm", ["R", "L"])
@pytest.mark.parametrize("joint", [0, 7, 8, 9, 10])
def test_practical_gate_requires_original_family_in_addition_to_A(arm, joint):
    data = cells()
    for cell in data:
        if cell["plan"]["arm"] == arm and cell["plan"]["block"] > joint:
            cell.update(
                A_and_original_family=False,
                original_family_status="proven_nonmember",
                continuous_extension={"family_status": "proven_member"},
            )
    report = confirmation.comparison(data, "confirm_low")
    assert report["totals"][arm]["denominator"] == 10
    assert report["totals"][arm]["A"] == 10
    assert report["totals"][arm]["A_and_original_family"] == joint
    assert report[arm + "_meets_signal_threshold"] is (joint >= 8)
    assert report["algorithm_outputs"] == 20
    assert report["automatic_execution"] is False


@pytest.mark.parametrize(
    "restart,long,expected_r,expected_l",
    [
        ((8, 8, 8), (7, 10, 10), True, False),
        ((10, 10, 7), (10, 10, 10), False, True),
        ((8, 9, 10), (8, 8, 8), True, True),
        ((7, 10, 10), (10, 10, 7), False, False),
    ],
)
def test_all_signals_must_pass_and_control_never_replaces_primary_candidate(
    restart, long, expected_r, expected_l
):
    evidence = sections(restart, long)
    # Cost superiority cannot rescue an insufficient primary success count.
    for section in evidence:
        for arm in ("R", "L"):
            section["comparison"]["totals"][arm]["costs"] = {
                key: None for key in confirmation.previous.COST_FIELDS
            }
    assert confirmation.confirmation_decision(evidence) == {
        "transition_criterion_met": expected_r,
        "L_control_criterion_met": expected_l,
    }


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate_signal",
        "comparison_signal",
        "extra_arm",
        "technical",
        "denominator",
        "bool_count",
        "float_count",
        "negative_count",
        "joint_above_A",
        "A_above_denominator",
    ],
)
def test_confirmation_requires_complete_scientific_integer_counts(fault):
    data = sections()
    if fault == "missing":
        data.pop()
    elif fault == "duplicate_signal":
        data[2] = copy.deepcopy(data[0])
    elif fault == "comparison_signal":
        data[0]["comparison"]["signal"] = profile.names()[1]
    elif fault == "extra_arm":
        data[0]["comparison"]["totals"]["other"] = copy.deepcopy(
            data[0]["comparison"]["totals"]["L"]
        )
    elif fault == "technical":
        data[0]["scope"] = "technical"
    else:
        count = data[0]["comparison"]["totals"]["L"]
        field, value = {
            "denominator": ("denominator", 9),
            "bool_count": ("A", True),
            "float_count": ("A_and_original_family", 8.0),
            "negative_count": ("A_and_original_family", -1),
            "joint_above_A": ("A", 9),
            "A_above_denominator": ("A", 11),
        }[fault]
        count[field] = value
    with pytest.raises(ValueError):
        confirmation.confirmation_decision(data)


def test_exact_intervals_satisfy_independent_binomial_tail_equations():
    def tail(probability, first, last):
        return sum(
            comb(10, k) * probability**k * (1 - probability) ** (10 - k)
            for k in range(first, last + 1)
        )

    for successes in range(11):
        interval = confirmation.binomial_interval(successes, 10)
        assert interval["method"] == "Clopper-Pearson"
        assert interval["confidence"] == 0.95
        lower, upper = interval["lower"], interval["upper"]
        if successes:
            assert tail(lower, successes, 10) == pytest.approx(0.025, abs=2e-14)
        else:
            assert lower == 0
        if successes < 10:
            assert tail(upper, 0, successes) == pytest.approx(0.025, abs=2e-14)
        else:
            assert upper == 1
    interval = confirmation.binomial_interval(8, 10)
    assert interval["lower"] < 0.45 and interval["upper"] > 0.97
    report = confirmation.comparison(cells(), "confirm_low")
    for arm in ("R", "L"):
        assert set(report["totals"][arm]["uncertainty"]) == {
            "A",
            "A_and_original_family",
        }


@pytest.mark.parametrize("name", ["fixture_a", "fixture_b"])
def test_technical_fixtures_do_not_release_practical_gates_or_intervals(name):
    report = confirmation.comparison(cells(name, True), name, True)
    for arm in ("R", "L"):
        assert report[arm + "_meets_signal_threshold"] is None
        assert report["totals"][arm]["denominator"] == 1
        assert report["totals"][arm]["uncertainty"] is None


@pytest.mark.parametrize("arm", ["R", "L"])
def test_original_loss_complexity_and_member_order_alone_choose_one_output(arm):
    group = members(cells(), arm)
    for cell in group:
        cell["selected"] = {"loss": 0.1, "complexity": 9}
    group[-1]["selected"]["loss"] = 0.0
    group[-1].update(A=False, A_and_original_family=False, curve_grade="D")
    group[-1]["irregular_errors"] = {"relative_rms": 1000}
    chosen = confirmation.selected_output(list(reversed(group)))
    assert chosen["selected_cell"] == group[-1]["plan"]["number"]
    assert not chosen["A"] and chosen["any_front_A"]
    group[-1]["selected"].update(loss=0.1, complexity=8)
    assert (
        confirmation.selected_output(group)["selected_cell"] == chosen["selected_cell"]
    )
    for cell in group:
        cell["selected"]["complexity"] = 8
    assert (
        confirmation.selected_output(list(reversed(group)))["selected_cell"]
        == group[0]["plan"]["number"]
    )


@pytest.mark.parametrize("arm", ["R", "L"])
@pytest.mark.parametrize("loss", [float("nan"), float("inf"), -1.0, True, None])
def test_nonfinite_or_invalid_losses_do_not_win_or_remove_member_costs(arm, loss):
    group = members(cells(), arm)
    group[0]["selected"]["loss"] = loss
    chosen = confirmation.selected_output(group)
    assert chosen["selected_cell"] == group[1]["plan"]["number"]
    for field in confirmation.previous.COST_FIELDS:
        assert chosen["costs"][field] == sum(c["costs"][field] for c in group)


@pytest.mark.parametrize("arm,size", [("R", 4), ("L", 2)])
@pytest.mark.parametrize("all_failed", [False, True])
def test_failed_members_keep_package_denominator_and_unknown_costs(
    arm, size, all_failed
):
    data = cells()
    group = members(data, arm)
    for cell in group if all_failed else group[:1]:
        cell.update(status="worker_failed", A=False, A_and_original_family=False)
        cell.pop("selected")
    group[0]["costs"]["worker_wall_seconds"] = None
    report = confirmation.comparison(data, "confirm_low")
    output = report["pairs"][0]["outputs"][arm]
    total = report["totals"][arm]
    assert len(output["members"]) == size
    assert output["failed_members"] == (size if all_failed else 1)
    assert total["denominator"] == 10 and total["failures"] == int(all_failed)
    assert total["A_and_original_family"] == 10 - int(all_failed)
    assert output["costs"]["worker_wall_seconds"] is None
    assert total["costs"]["worker_wall_seconds"] is None
    assert output["costs"]["callback_calls_during_fit"] == sum(
        c["costs"]["callback_calls_during_fit"] for c in group
    )
    assert report["all_costs_observed"] is False


@pytest.mark.parametrize("fault", ["missing", "duplicate", "order", "seed", "running"])
def test_comparison_rejects_missing_reordered_or_unfinished_planned_calls(fault):
    data = cells()
    if fault == "missing":
        data.pop()
    elif fault == "duplicate":
        data[-1] = copy.deepcopy(data[0])
    elif fault == "order":
        data[0], data[1] = data[1], data[0]
    elif fault == "seed":
        data[0]["plan"]["seed"] += 1
    else:
        data[0]["status"] = "running"
    with pytest.raises(ValueError, match="every planned"):
        confirmation.comparison(data, "confirm_low")


def test_paired_contrasts_count_packages_without_pooling_members_or_signals():
    data = cells()
    members(data, "L", 1)[0].update(A=False, A_and_original_family=False)
    members(data, "R", 2)[0].update(A_and_original_family=False)
    for arm in ("R", "L"):
        members(data, arm, 3)[0].update(A=False, A_and_original_family=False)
    report = confirmation.comparison(data, "confirm_low")
    assert report["R_minus_L"]["A"] == {"gains": 1, "losses": 0, "ties": 9}
    assert report["R_minus_L"]["A_and_original_family"] == {
        "gains": 1,
        "losses": 1,
        "ties": 8,
    }
    assert "development_decision" not in report
    assert "descriptive_preference" not in report
