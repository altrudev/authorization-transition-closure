"""Reference verifier for Authorization Transition Closure.

This module intentionally implements only exact-binding semantics. It is a
research baseline, not a complete domain policy engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    authorized_action_digest: str | None
    executed_action_digest: str | None
    authorized_predecessor_digest: str | None
    observed_predecessor_digest: str | None
    expected_successor_digest: str | None
    observed_successor_digest: str | None
    policy_digest: str | None
    execution_policy_digest: str | None
    execution_succeeded: bool | None
    replay_detected: bool | None
    successor_observed: bool | None


def verify_transition(e: TransitionEvidence) -> VerificationResult:
    """Evaluate exact transition closure over supplied evidence."""

    required_for_reasoning = {
        "authorization_id": e.authorization_id,
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

    if e.replay_detected is True:
        return VerificationResult(Disposition.FAILED, "replay detected")

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
        "authorization, predecessor, execution, policy, successor, and replay bindings agree",
    )
