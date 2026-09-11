"""Reference parser/verifier adapter for ATC STBP v0.1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .verifier import TransitionEvidence, VerificationResult, verify_transition


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ProfileError(ValueError):
    """Raised when an STBP v0.1 document is structurally non-conformant."""


_TOP = {
    "profile",
    "transition_id",
    "resource",
    "authorization",
    "execution",
    "predecessor",
    "successor",
    "replay",
    "predicate",
}


@dataclass(frozen=True)
class STBPResult:
    transition_id: str
    verification: VerificationResult


def _object(value: Any, name: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileError(f"{name} must be an object")
    unknown = set(value) - allowed
    if unknown:
        raise ProfileError(f"{name} has unknown fields: {sorted(unknown)}")
    return value


def _required(obj: dict[str, Any], fields: set[str], name: str) -> None:
    missing = fields - set(obj)
    if missing:
        raise ProfileError(f"{name} missing required fields: {sorted(missing)}")


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProfileError(f"{name} must be a non-empty string")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ProfileError(f"{name} must be a canonical sha256 digest")
    return value


def _tri_bool(value: Any, name: str) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise ProfileError(f"{name} must be boolean or null")
    return value


def parse_stbp_v01(doc: dict[str, Any]) -> TransitionEvidence:
    """Parse one conforming STBP v0.1 document into ATC evidence."""

    root = _object(doc, "document", _TOP)
    _required(root, _TOP, "document")

    if root["profile"] != "atc.stbp.v0.1":
        raise ProfileError("unsupported profile")
    _nonempty(root["transition_id"], "transition_id")

    resource = _object(
        root["resource"], "resource", {"resource_id", "representation"}
    )
    _required(resource, {"resource_id", "representation"}, "resource")
    resource_id = _nonempty(resource["resource_id"], "resource.resource_id")
    _nonempty(resource["representation"], "resource.representation")

    authorization = _object(
        root["authorization"],
        "authorization",
        {
            "authorization_id",
            "action_digest",
            "predecessor_digest",
            "policy_digest",
            "evidence_ref",
        },
    )
    _required(
        authorization,
        {
            "authorization_id",
            "action_digest",
            "predecessor_digest",
            "policy_digest",
            "evidence_ref",
        },
        "authorization",
    )

    execution = _object(
        root["execution"],
        "execution",
        {"action_digest", "policy_digest", "succeeded", "evidence_ref"},
    )
    _required(
        execution,
        {"action_digest", "policy_digest", "succeeded", "evidence_ref"},
        "execution",
    )

    def observation(name: str) -> dict[str, Any]:
        obj = _object(
            root[name],
            name,
            {
                "state_digest",
                "observer_id",
                "observed_at",
                "trusted",
                "fresh",
                "evidence_ref",
            },
        )
        _required(
            obj,
            {
                "state_digest",
                "observer_id",
                "observed_at",
                "trusted",
                "fresh",
                "evidence_ref",
            },
            name,
        )
        _digest(obj["state_digest"], f"{name}.state_digest")
        _nonempty(obj["observer_id"], f"{name}.observer_id")
        _nonempty(obj["observed_at"], f"{name}.observed_at")
        _tri_bool(obj["trusted"], f"{name}.trusted")
        _tri_bool(obj["fresh"], f"{name}.fresh")
        _nonempty(obj["evidence_ref"], f"{name}.evidence_ref")
        return obj

    predecessor = observation("predecessor")
    successor = observation("successor")

    replay = _object(root["replay"], "replay", {"status", "evidence_ref"})
    _required(replay, {"status", "evidence_ref"}, "replay")
    if replay["status"] not in {"not-replayed", "replayed", "unknown"}:
        raise ProfileError("replay.status is invalid")
    _nonempty(replay["evidence_ref"], "replay.evidence_ref")

    predicate = _object(
        root["predicate"],
        "predicate",
        {"type", "expected_successor_digest"},
    )
    _required(
        predicate,
        {"type", "expected_successor_digest"},
        "predicate",
    )
    if predicate["type"] != "exact-successor-digest":
        raise ProfileError("unsupported predicate.type")

    return TransitionEvidence(
        authorization_id=_nonempty(
            authorization["authorization_id"], "authorization.authorization_id"
        ),
        authorized_resource_id=resource_id,
        execution_resource_id=resource_id,
        observation_resource_id=resource_id,
        authorized_action_digest=_digest(
            authorization["action_digest"], "authorization.action_digest"
        ),
        executed_action_digest=_digest(
            execution["action_digest"], "execution.action_digest"
        ),
        authorized_predecessor_digest=_digest(
            authorization["predecessor_digest"],
            "authorization.predecessor_digest",
        ),
        observed_predecessor_digest=predecessor["state_digest"],
        expected_successor_digest=_digest(
            predicate["expected_successor_digest"],
            "predicate.expected_successor_digest",
        ),
        observed_successor_digest=successor["state_digest"],
        policy_digest=_digest(
            authorization["policy_digest"], "authorization.policy_digest"
        ),
        execution_policy_digest=_digest(
            execution["policy_digest"], "execution.policy_digest"
        ),
        predecessor_observer_trusted=predecessor["trusted"],
        successor_observer_trusted=successor["trusted"],
        predecessor_fresh=predecessor["fresh"],
        successor_fresh=successor["fresh"],
        execution_succeeded=_tri_bool(
            execution["succeeded"], "execution.succeeded"
        ),
        replay_detected=(
            True
            if replay["status"] == "replayed"
            else False
            if replay["status"] == "not-replayed"
            else None
        ),
        successor_observed=True,
    )


def verify_stbp_v01(doc: dict[str, Any]) -> STBPResult:
    evidence = parse_stbp_v01(doc)
    return STBPResult(
        transition_id=doc["transition_id"],
        verification=verify_transition(evidence),
    )
