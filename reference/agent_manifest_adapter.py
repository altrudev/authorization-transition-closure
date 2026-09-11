"""Agent Manifest HITL adapter for Authorization Transition Closure.

This module verifies the pinned language-neutral Agent Manifest vector
AM-VEC-009 and preserves Agent Manifest's assurance boundary: manifest/HITL
approval does not become per-call authorization or target-resource state proof.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .verifier import TransitionEvidence


SIGNED_FIELDS = (
    "@context",
    "@type",
    "manifest_id",
    "previous_manifest_id",
    "agent_id",
    "agent_instance_id",
    "version",
    "min_verifier_version",
    "issued_at",
    "expires_at",
    "issuer",
    "crypto_profile",
    "profile",
    "unbound_artifacts",
    "source_bundle",
    "artifacts",
    "delegation_chain",
    "hitl_record",
    "prior_transparency_log_entry",
    "log_retention",
    "data_scope",
    "operational_lifecycle",
    "intent",
)


@dataclass(frozen=True)
class AgentManifestResult:
    valid: bool
    result: str
    hitl_result: str
    failures: tuple[str, ...]


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def _canonical(value: Any) -> bytes:
    return rfc8785.dumps(_drop_none(value))


def _manifest_preimage(manifest: dict[str, Any]) -> bytes:
    subset = {k: manifest[k] for k in SIGNED_FIELDS if k in manifest}
    hitl = subset.get("hitl_record")
    if isinstance(hitl, dict):
        normalized = dict(hitl)
        normalized["approvals"] = []
        subset["hitl_record"] = normalized
    return _canonical(subset)


def _approval_preimage(
    manifest_id: str,
    approval: dict[str, Any],
) -> bytes:
    obj = {
        "manifest_id": manifest_id,
        "approved_at": approval["approved_at"],
        "approved_scope": approval["approved_scope"],
        "approver_id": approval["approver_id"],
    }
    if approval.get("approval_method") is not None:
        obj["approval_method"] = approval["approval_method"]
    return _canonical(obj)


def _parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt


def verify_agent_manifest_hitl_vector(vector: dict[str, Any]) -> AgentManifestResult:
    """Verify the relevant AM-VEC-009 properties independently."""

    failures: list[str] = []
    manifest = vector["manifest"]
    context = vector["context"]

    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        failures.append("manifest_signature_missing")
    else:
        key_id = signature.get("key_id")
        key_b64 = context.get("trusted_keys", {}).get(key_id)
        if key_b64 is None:
            failures.append("manifest_key_untrusted")
        else:
            try:
                Ed25519PublicKey.from_public_bytes(_b64url_decode(key_b64)).verify(
                    _b64url_decode(signature["signature_value"]),
                    _manifest_preimage(manifest),
                )
            except (InvalidSignature, ValueError, KeyError):
                failures.append("manifest_signature_invalid")

    artifacts = manifest.get("artifacts", {})
    if artifacts.get("system_prompt", {}).get("hash") != context.get("system_prompt_hash"):
        failures.append("system_prompt_mismatch")
    if artifacts.get("policy_bundle", {}).get("hash") != context.get("policy_bundle_hash"):
        failures.append("policy_bundle_mismatch")
    if artifacts.get("model_identity", {}).get("version") != context.get("model_version"):
        failures.append("model_version_mismatch")

    try:
        expires_at = _parse_time(manifest["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            failures.append("manifest_expired")
    except (KeyError, ValueError):
        failures.append("manifest_expiry_invalid")

    hitl = manifest.get("hitl_record")
    if context.get("enforce_hitl"):
        if not isinstance(hitl, dict) or hitl.get("required") is not True:
            failures.append("hitl_required_missing")
        else:
            approvals = hitl.get("approvals")
            if not isinstance(approvals, list) or not approvals:
                failures.append("hitl_approval_missing")
            else:
                valid_approval = False
                for approval in approvals:
                    try:
                        approver_id = approval["approver_id"]
                        pub_b64 = context.get("approver_public_keys", {}).get(approver_id)
                        if pub_b64 is None:
                            continue

                        duration = approval["approved_scope"].get(
                            "approval_duration_seconds", 0
                        )
                        if (
                            not isinstance(duration, (int, float))
                            or isinstance(duration, bool)
                        ):
                            continue
                        approved_at = _parse_time(approval["approved_at"])
                        if duration and datetime.now(timezone.utc) > (
                            approved_at + timedelta(seconds=duration)
                        ):
                            continue

                        Ed25519PublicKey.from_public_bytes(
                            _b64url_decode(pub_b64)
                        ).verify(
                            _b64url_decode(approval["approval_signature"]),
                            _approval_preimage(manifest["manifest_id"], approval),
                        )
                        valid_approval = True
                        break
                    except (
                        InvalidSignature,
                        ValueError,
                        KeyError,
                        TypeError,
                    ):
                        continue
                if not valid_approval:
                    failures.append("hitl_approval_invalid")

    if failures:
        return AgentManifestResult(
            valid=False,
            result="MISMATCH",
            hitl_result="INVALID",
            failures=tuple(failures),
        )

    return AgentManifestResult(
        valid=True,
        result="VALID",
        hitl_result="APPROVED" if context.get("enforce_hitl") else "NOT_REQUIRED",
        failures=(),
    )


def agent_manifest_to_atc_partial(
    vector: dict[str, Any],
    result: AgentManifestResult,
) -> TransitionEvidence:
    """Map only facts Agent Manifest actually proves.

    The manifest contributes policy/configuration identity and authenticated
    HITL approval. It does not generically identify one per-call action,
    one target resource, or S0/S1 target-resource state.
    """

    if not result.valid:
        raise ValueError("cannot map invalid Agent Manifest evidence")

    policy_digest = vector["manifest"]["artifacts"]["policy_bundle"]["hash"]

    return TransitionEvidence(
        authorization_id=vector["manifest"]["manifest_id"],
        authorized_resource_id=None,
        execution_resource_id=None,
        observation_resource_id=None,
        authorized_action_digest=None,
        executed_action_digest=None,
        authorized_predecessor_digest=None,
        observed_predecessor_digest=None,
        expected_successor_digest=None,
        observed_successor_digest=None,
        policy_digest=policy_digest,
        execution_policy_digest=policy_digest,
        predecessor_observer_trusted=None,
        successor_observer_trusted=None,
        predecessor_fresh=None,
        successor_fresh=None,
        execution_succeeded=None,
        replay_detected=None,
        successor_observed=None,
    )


def compose_valid_hitl_with_external_action(
    vector: dict[str, Any],
    result: AgentManifestResult,
    *,
    resource_id: str,
    action_digest: str,
    authorized_predecessor_digest: str,
    observed_predecessor_digest: str,
    predecessor_fresh: bool,
) -> TransitionEvidence:
    """Compose valid HITL/config evidence with separate per-call authorization.

    This is the correct boundary: Agent Manifest supplies approved
    configuration/HITL authority; an external layer supplies the exact action
    and target-resource state binding.
    """

    if not result.valid:
        raise ValueError("Agent Manifest evidence must verify first")

    policy_digest = vector["manifest"]["artifacts"]["policy_bundle"]["hash"]

    return TransitionEvidence(
        authorization_id=vector["manifest"]["manifest_id"] + ":external-call",
        authorized_resource_id=resource_id,
        execution_resource_id=resource_id,
        observation_resource_id=resource_id,
        authorized_action_digest=action_digest,
        executed_action_digest=action_digest,
        authorized_predecessor_digest=authorized_predecessor_digest,
        observed_predecessor_digest=observed_predecessor_digest,
        expected_successor_digest=None,
        observed_successor_digest=None,
        policy_digest=policy_digest,
        execution_policy_digest=policy_digest,
        predecessor_observer_trusted=True,
        successor_observer_trusted=None,
        predecessor_fresh=predecessor_fresh,
        successor_fresh=None,
        execution_succeeded=None,
        replay_detected=False,
        successor_observed=False,
    )
