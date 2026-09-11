import copy
import json
from pathlib import Path

from reference.agent_manifest_adapter import (
    agent_manifest_to_atc_partial,
    compose_valid_hitl_with_external_action,
    verify_agent_manifest_hitl_vector,
)
from reference.verifier import Disposition, verify_transition


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "agent-manifest"
    / "AM-VEC-009.json"
)


def load_vector() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_pinned_agent_manifest_hitl_vector_verifies() -> None:
    vector = load_vector()
    result = verify_agent_manifest_hitl_vector(vector)

    assert result.valid is True
    assert result.result == vector["expected"]["result"]
    assert result.hitl_result == vector["expected"]["fields_verified"]["hitl_record"]
    assert result.failures == ()


def test_hitl_approval_signature_tamper_is_rejected() -> None:
    vector = load_vector()
    approval = vector["manifest"]["hitl_record"]["approvals"][0]
    approval["approval_signature"] = approval["approval_signature"][:-1] + "A"

    result = verify_agent_manifest_hitl_vector(vector)

    assert result.valid is False
    assert "hitl_approval_invalid" in result.failures


def test_hitl_scope_tamper_is_rejected() -> None:
    vector = load_vector()
    vector["manifest"]["hitl_record"]["approvals"][0]["approved_scope"][
        "approval_duration_seconds"
    ] = 1

    result = verify_agent_manifest_hitl_vector(vector)

    assert result.valid is False
    assert "hitl_approval_invalid" in result.failures


def test_manifest_signature_tamper_is_rejected() -> None:
    vector = load_vector()
    vector["manifest"]["agent_id"] = "spiffe://trust.example/agent/other"

    result = verify_agent_manifest_hitl_vector(vector)

    assert result.valid is False
    assert "manifest_signature_invalid" in result.failures


def test_valid_hitl_alone_does_not_create_per_call_authorization() -> None:
    vector = load_vector()
    am_result = verify_agent_manifest_hitl_vector(vector)
    evidence = agent_manifest_to_atc_partial(vector, am_result)

    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert evidence.authorized_action_digest is None
    assert evidence.authorized_resource_id is None


def test_valid_hitl_plus_stale_predecessor_fails_transition() -> None:
    vector = load_vector()
    am_result = verify_agent_manifest_hitl_vector(vector)
    assert am_result.valid is True
    assert am_result.hitl_result == "APPROVED"

    evidence = compose_valid_hitl_with_external_action(
        vector,
        am_result,
        resource_id="account:customer-17",
        action_digest="sha256:" + "3" * 64,
        authorized_predecessor_digest="sha256:" + "4" * 64,
        observed_predecessor_digest="sha256:" + "4" * 64,
        predecessor_fresh=False,
    )

    result = verify_transition(evidence)

    assert result.disposition is Disposition.FAILED
    assert "stale" in result.reason
    # The upstream human approval remains valid; ATC rejects the state transition.
    assert am_result.result == "VALID"
    assert am_result.hitl_result == "APPROVED"
