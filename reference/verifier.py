"""Reference verifier for Authorization Transition Closure.

The reference implementation is intentionally conservative. It implements exact
binding semantics only; domain profiles may later replace exact successor
equality with a richer transition predicate.

CLOSED means the evidence supplied to this function is sufficient under this
model. It does not make an untrusted observer trustworthy merely because the
observer's bytes were hashed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class Disposition(str, Enum):
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class VerificationResult:
    disposition: Disposition
    reason: str


@dataclass(frozen=True)
class TransitionEvidence:
    authorization_id: str | None
    authorized_resource_id: str | None
    execution_resource_id: str | None
    observation_resource_id: str | None

    authorized_action_digest: str | None
    executed_action_digest: str | None

    authorized_predecessor_digest: str | None
    observed_predecessor_digest: str | None
    expected_successor_digest: str | None
    observed_successor_digest: str | None

    policy_digest: str | None
    execution_policy_digest: str | None

    predecessor_observer_trusted: bool | None
    successor_observer_trusted: bool | None
    predecessor_fresh: bool | None
    successor_fresh: bool | None

    execution_succeeded: bool | None
    replay_detected: bool | None
    successor_observed: bool | None


def _bad_digest(name: str, value: str | None) -> VerificationResult | None:
    if value is not None and _DIGEST_RE.fullmatch(value) is None:
        return VerificationResult(
            Disposition.FAILED,
            f"{name} is not a canonical sha256 digest",
        )
    return None


def verify_transition(e: TransitionEvidence) -> VerificationResult:
    """Evaluate exact transition closure over supplied evidence."""

    required_for_reasoning = {
        "authorization_id": e.authorization_id,
        "authorized_resource_id": e.authorized_resource_id,
        "execution_resource_id": e.execution_resource_id,
        "observation_resource_id": e.observation_resource_id,
        "authorized_action_digest": e.authorized_action_digest,
        "executed_action_digest": e.executed_action_digest,
        "authorized_predecessor_digest": e.authorized_predecessor_digest,
        "observed_predecessor_digest": e.observed_predecessor_digest,
        "policy_digest": e.policy_digest,
        "execution_policy_digest": e.execution_policy_digest,
    }
    missing = [name for name, value in required_for_reasoning.items() if value is None]
    if missing:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "missing required evidence: " + ", ".join(sorted(missing)),
        )

    for name in (
        "authorized_action_digest",
        "executed_action_digest",
        "authorized_predecessor_digest",
        "observed_predecessor_digest",
        "expected_successor_digest",
        "observed_successor_digest",
        "policy_digest",
        "execution_policy_digest",
    ):
        bad = _bad_digest(name, getattr(e, name))
        if bad is not None:
            return bad

    if e.replay_detected is True:
        return VerificationResult(Disposition.FAILED, "replay detected")

    if not (
        e.authorized_resource_id
        == e.execution_resource_id
        == e.observation_resource_id
    ):
        return VerificationResult(
            Disposition.FAILED,
            "authorization, execution, and observation name different resources",
        )

    if e.predecessor_observer_trusted is False:
        return VerificationResult(
            Disposition.FAILED,
            "predecessor observer is explicitly untrusted",
        )
    if e.predecessor_observer_trusted is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "predecessor observer trust is unknown",
        )

    if e.predecessor_fresh is False:
        return VerificationResult(
            Disposition.FAILED,
            "predecessor observation is stale",
        )
    if e.predecessor_fresh is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "predecessor freshness is unknown",
        )

    if e.authorized_predecessor_digest != e.observed_predecessor_digest:
        return VerificationResult(
            Disposition.FAILED,
            "execution predecessor does not match authorized predecessor",
        )

    if e.authorized_action_digest != e.executed_action_digest:
        return VerificationResult(
            Disposition.FAILED,
            "executed action does not match authorized action",
        )

    if e.policy_digest != e.execution_policy_digest:
        return VerificationResult(
            Disposition.FAILED,
            "execution policy does not match authorized policy",
        )

    if e.execution_succeeded is False:
        return VerificationResult(Disposition.FAILED, "execution reported failure")
    if e.execution_succeeded is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "execution outcome is unavailable",
        )

    if e.successor_observed is not True or e.observed_successor_digest is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "successor state is not independently observed",
        )

    if e.successor_observer_trusted is False:
        return VerificationResult(
            Disposition.FAILED,
            "successor observer is explicitly untrusted",
        )
    if e.successor_observer_trusted is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "successor observer trust is unknown",
        )

    if e.successor_fresh is False:
        return VerificationResult(
            Disposition.FAILED,
            "successor observation is stale",
        )
    if e.successor_fresh is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "successor freshness is unknown",
        )

    if e.expected_successor_digest is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "no exact successor predicate is available",
        )

    if e.expected_successor_digest != e.observed_successor_digest:
        return VerificationResult(
            Disposition.FAILED,
            "observed successor does not satisfy the authorized transition",
        )

    if e.replay_detected is None:
        return VerificationResult(
            Disposition.INDETERMINATE,
            "replay status is unknown",
        )

    return VerificationResult(
        Disposition.CLOSED,
        "resource, authorization, predecessor, execution, policy, successor, "
        "observer trust, freshness, and replay bindings agree",
    )
