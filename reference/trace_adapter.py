"""TRACE action-receipt adapter for Authorization Transition Closure.

This module verifies the subset of TRACE's informative action-receipt
conformance profile needed by the pinned interoperability fixture in
fixtures/trace/.

The adapter deliberately preserves TRACE's assurance boundary:
receipt acceptance is not mapped to physical execution success.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .verifier import TransitionEvidence


ACTION_REF_FIELDS = ("agent_id", "action_type", "action_scope", "action_timestamp")


@dataclass(frozen=True)
class TraceReceiptResult:
    valid: bool
    status: str
    controller_outcome: str
    failures: tuple[str, ...]


def _canonical_json(value: Any) -> bytes:
    """Canonicalize the restricted fixture subset used by this adapter.

    The pinned TRACE fixture contains only JSON objects, arrays, strings,
    integers, booleans and null values whose RFC 8785 representation is
    identical to sorted UTF-8 JSON with compact separators.

    This function intentionally rejects floats so it cannot silently pretend
    to be a complete RFC 8785 implementation.
    """

    def reject_float(v: Any) -> None:
        if isinstance(v, float):
            raise ValueError("float values require a full RFC 8785 implementation")
        if isinstance(v, dict):
            for k, child in v.items():
                if not isinstance(k, str):
                    raise ValueError("JSON object keys must be strings")
                reject_float(child)
        elif isinstance(v, list):
            for child in v:
                reject_float(child)

    reject_float(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_jcs(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value)).hexdigest()


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_trace_action_receipt_fixture(fixture: dict[str, Any]) -> TraceReceiptResult:
    """Verify the pinned TRACE informative action-receipt fixture."""

    failures: list[str] = []
    action = fixture["action"]
    context = fixture["context"]
    evidence = fixture["evidence"]
    receipt = fixture["receipt"]

    preimage = {field: action[field] for field in ACTION_REF_FIELDS}
    if action["action_ref"] != _sha256_jcs(preimage):
        failures.append("action_ref_invalid")

    if receipt["action_ref"] != action["action_ref"]:
        failures.append("action_ref_mismatch")

    if receipt["linked_call_id"] != context["call_id"]:
        failures.append("call_id_mismatch")

    if receipt["session_id"] != context["session_id"]:
        failures.append("session_id_mismatch")

    if receipt["evidence_hash"] != _sha256_jcs(evidence):
        failures.append("evidence_hash_mismatch")

    if receipt["previous_receipt_hash"] != context["expected_previous_receipt_hash"]:
        failures.append("receipt_chain_gap")

    age = (
        _parse_timestamp(context["verification_time"])
        - _parse_timestamp(receipt["issued_at"])
    ).total_seconds()
    if age < 0:
        failures.append("receipt_from_future")
    elif age > context["max_receipt_age_seconds"]:
        failures.append("receipt_stale")

    if receipt["decision"] not in {"accepted", "rejected"}:
        failures.append("decision_invalid")

    if evidence["physical_completion_claim"] != "none":
        failures.append("unsupported_physical_completion_claim")

    jwk = fixture["trusted_issuer_keys"].get(receipt["issuer_key_id"])
    if jwk is None:
        failures.append("issuer_key_unknown")
    elif jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519":
        failures.append("signature_or_key_mismatch")
    else:
        try:
            pub = Ed25519PublicKey.from_public_bytes(_b64url_decode(jwk["x"]))
            signing_input = {
                key: value for key, value in receipt.items() if key != "signature"
            }
            pub.verify(
                _b64url_decode(receipt["signature"]),
                _canonical_json(signing_input),
            )
        except (ValueError, InvalidSignature):
            failures.append("signature_or_key_mismatch")

    if failures:
        return TraceReceiptResult(
            valid=False,
            status="receipt_invalid",
            controller_outcome="unknown",
            failures=tuple(failures),
        )

    status = (
        "receipt_valid_accepted"
        if receipt["decision"] == "accepted"
        else "receipt_valid_rejected"
    )
    return TraceReceiptResult(
        valid=True,
        status=status,
        controller_outcome=evidence["terminal_state"],
        failures=(),
    )


def trace_receipt_to_atc_partial(
    fixture: dict[str, Any],
    result: TraceReceiptResult,
    *,
    authorization_id: str,
    resource_id: str,
    predecessor_digest: str,
    policy_digest: str,
) -> TransitionEvidence:
    """Compose verified TRACE receipt facts into partial ATC evidence.

    TRACE contributes the exact action binding and controller decision.
    It does not contribute proof that the action executed or that a successor
    application/physical state was observed, so those ATC fields remain unknown.
    """

    if not result.valid:
        raise ValueError("cannot map an invalid TRACE receipt into ATC evidence")

    action_ref = fixture["action"]["action_ref"]

    return TransitionEvidence(
        authorization_id=authorization_id,
        authorized_resource_id=resource_id,
        execution_resource_id=resource_id,
        observation_resource_id=resource_id,
        authorized_action_digest=action_ref,
        executed_action_digest=action_ref,
        authorized_predecessor_digest=predecessor_digest,
        observed_predecessor_digest=predecessor_digest,
        expected_successor_digest=None,
        observed_successor_digest=None,
        policy_digest=policy_digest,
        execution_policy_digest=policy_digest,
        predecessor_observer_trusted=True,
        successor_observer_trusted=None,
        predecessor_fresh=True,
        successor_fresh=None,
        execution_succeeded=None,
        replay_detected=None,
        successor_observed=False,
    )
