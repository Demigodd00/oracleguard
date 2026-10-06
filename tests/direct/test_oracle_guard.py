from datetime import datetime, timezone
from pathlib import Path
import json
import re


CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "OracleGuard.py"
SDK = "v0.2.16"
TIME = "2026-10-06T12:00:00Z"
NOW = int(datetime(2026, 10, 6, 12, tzinfo=timezone.utc).timestamp())
FEED = "https://feed.example.org/eth-usd.json"
REF_A = "https://reference-a.example.net/eth-usd.json"
REF_B = "https://reference-b.example.com/eth-usd.json"


def deploy(vm, direct_deploy, owner):
    vm.warp(TIME)
    vm.sender = owner
    return direct_deploy(str(CONTRACT), "ETH-USD", FEED, REF_A, REF_B, 600, 200, 1000, 1800, sdk_version=SDK)


def mock(vm, *, feed=3000, a=3000, b=3000, feed_age=10, reference_age=10, feed_status=200):
    values = (
        (FEED, feed, NOW - feed_age, feed_status),
        (REF_A, a, NOW - reference_age, 200),
        (REF_B, b, NOW - reference_age, 200),
    )
    for url, price, observed, status in values:
        body = json.dumps({"pair": "ETH-USD", "price_e8": price * 10**8, "observed_at": observed})
        vm.mock_web(re.escape(url), {"status": status, "body": body})


def open_and_evaluate(vm, contract, requester, duration=900):
    vm.sender = requester
    assessment_id = contract.open_assessment(duration, "Investigate feed quality")
    record = contract.get_assessment(assessment_id)
    assert record["status"] == "OPEN"
    assert record["feed_url"] == FEED
    assert record["reference_a_url"] == REF_A
    assert record["reference_b_url"] == REF_B
    result = contract.evaluate_assessment(assessment_id)
    return assessment_id, result


def test_healthy_feed_keeps_borrow_gate_open(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    mock(direct_vm)
    assessment_id, result = open_and_evaluate(direct_vm, contract, direct_bob)
    assert result == "NO_TRIGGER"
    assert contract.get_assessment(assessment_id)["reason"] == "WITHIN_POLICY"
    assert contract.get_gate()["closed"] is False
    assert direct_vm.run_validator(leader_result=direct_vm._captured_validators[-1][0]) is True
    direct_vm.sender = direct_bob
    assert contract.request_borrow(12) == 12
    assert contract.get_borrowed_units("0x" + direct_bob.hex()) == "12"


def test_price_deviation_closes_only_for_bounded_period(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    mock(direct_vm, feed=2600)
    assessment_id, result = open_and_evaluate(direct_vm, contract, direct_bob)
    assert result == "TRIGGER_CONFIRMED"
    record = contract.get_assessment(assessment_id)
    assert record["reason"] == "PRICE_DEVIATION"
    assert record["pause_until"] == NOW + 900
    assert contract.get_gate()["closed"] is True
    assert direct_vm.run_validator(leader_result=direct_vm._captured_validators[-1][0]) is True
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("borrow_gate_closed"):
        contract.request_borrow(1)
    direct_vm.warp("2026-10-06T12:15:01Z")
    assert contract.get_gate()["closed"] is False
    assert contract.request_borrow(1) == 1


def test_stale_feed_triggers_when_references_are_fresh(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    mock(direct_vm, feed_age=601)
    assessment_id, result = open_and_evaluate(direct_vm, contract, direct_bob)
    assert result == "TRIGGER_CONFIRMED"
    assert contract.get_assessment(assessment_id)["reason"] == "FEED_STALE"


def test_conflicting_references_and_missing_source_create_no_authority(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    mock(direct_vm, feed=2500, a=3000, b=3200)
    first, result = open_and_evaluate(direct_vm, contract, direct_bob)
    assert result == "INSUFFICIENT_EVIDENCE"
    assert contract.get_assessment(first)["reason"] == "REFERENCES_CONFLICT"
    assert contract.get_gate()["closed"] is False
    direct_vm.clear_mocks()
    mock(direct_vm, feed=2500, feed_status=503)
    second, result = open_and_evaluate(direct_vm, contract, direct_bob)
    assert result == "INSUFFICIENT_EVIDENCE"
    assert contract.get_assessment(second)["reason"] == "SOURCE_INVALID"
    assert contract.get_gate()["closed"] is False


def test_validator_independently_rechecks_material_decision(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    mock(direct_vm, feed=2500)
    open_and_evaluate(direct_vm, contract, direct_bob)
    proposed = direct_vm._captured_validators[-1][0]
    direct_vm.clear_mocks()
    mock(direct_vm, feed=3000)
    assert direct_vm.run_validator(leader_result=proposed) is False


def test_policy_and_one_shot_assessment_rules(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    assert contract.get_policy()["max_pause_seconds"] == "1800"
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("duration_out_of_bounds"):
        contract.open_assessment(1801, "Too long")
    with direct_vm.expect_revert("invalid_note"):
        contract.open_assessment(900, " ")
    mock(direct_vm)
    assessment_id, _ = open_and_evaluate(direct_vm, contract, direct_bob)
    with direct_vm.expect_revert("assessment_already_evaluated"):
        contract.evaluate_assessment(assessment_id)
    with direct_vm.expect_revert("units_out_of_bounds"):
        contract.request_borrow(1001)
    assert contract.list_assessments(0, 25)["total"] == "1"
