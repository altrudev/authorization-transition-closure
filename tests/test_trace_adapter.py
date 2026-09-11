import json
from pathlib import Path

from reference.trace_adapter import (
    trace_receipt_to_atc_partial,
    verify_trace_action_receipt_fixture,
)
from reference.verifier import Disposition, verify_transition


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "trace"
    / "01-valid-controller-accepted.json"
)


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_pinned_trace_fixture_verifies_with_real_signature() -> None:
    fixture = load_fixture()
    result = verify_trace_action_receipt_fixture(fixture)

    assert result.valid is True
    assert result.status == fixture["expected"]["status"]
    assert result.controller_outcome == fixture["expected"]["controller_outcome"]
    assert result.failures == ()


def test_trace_signature_tamper_is_rejected() -> None:
    fixture = load_fixture()
    fixture["receipt"]["signature"] = fixture["receipt"]["signature"][:-1] + "A"

    result = verify_trace_action_receipt_fixture(fixture)

    assert result.valid is False
    assert "signature_or_key_mismatch" in result.failures


def test_trace_action_tamper_is_rejected_before_atc() -> None:
    fixture = load_fixture()
    fixture["action"]["action_scope"] = "/different_action"

    result = verify_trace_action_receipt_fixture(fixture)

    assert result.valid is False
    assert "action_ref_invalid" in result.failures


def test_valid_trace_receipt_does_not_close_transition() -> None:
    fixture = load_fixture()
    trace_result = verify_trace_action_receipt_fixture(fixture)
    assert trace_result.valid

    evidence = trace_receipt_to_atc_partial(
        fixture,
        trace_result,
        authorization_id="external-auth-1",
        resource_id="robot:cell-a:arm-2",
        predecessor_digest="sha256:" + "1" * 64,
        policy_digest="sha256:" + "2" * 64,
    )

    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert "execution outcome is unavailable" in result.reason


def test_trace_acceptance_is_not_mapped_to_execution_success() -> None:
    fixture = load_fixture()
    trace_result = verify_trace_action_receipt_fixture(fixture)
    evidence = trace_receipt_to_atc_partial(
        fixture,
        trace_result,
        authorization_id="external-auth-1",
        resource_id="robot:cell-a:arm-2",
        predecessor_digest="sha256:" + "1" * 64,
        policy_digest="sha256:" + "2" * 64,
    )

    assert trace_result.controller_outcome == "accepted"
    assert evidence.execution_succeeded is None
    assert evidence.successor_observed is False
