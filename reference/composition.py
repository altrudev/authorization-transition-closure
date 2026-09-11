"""Composition layer for TRACE + Agent Manifest + cA2A + state evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .agent_manifest_adapter import AgentManifestResult
from .ca2a_adapter import CA2AVerification
from .trace_adapter import TraceReceiptResult
from .verifier import TransitionEvidence


@dataclass(frozen=True)
class StateObservation:
    resource_id: str
    predecessor_digest: str
    predecessor_trusted: bool
    predecessor_fresh: bool
    successor_digest: str | None = None
    successor_trusted: bool | None = None
    successor_fresh: bool | None = None


def compose_upstream_evidence(
    *,
    trace_fixture: dict,
    trace_result: TraceReceiptResult,
    manifest_vector: dict,
    manifest_result: AgentManifestResult,
    ca2a_result: CA2AVerification,
    state: StateObservation,
    ca2a_action_digest: str,
    execution_succeeded: bool | None,
    replay_detected: bool | None,
    expected_successor_digest: str | None,
) -> TransitionEvidence:
    """Compose verified upstream facts without upgrading their assurance claims."""

    if not trace_result.valid:
        raise ValueError("TRACE evidence is not valid")
    if not manifest_result.valid:
        raise ValueError("Agent Manifest evidence is not valid")
    if not (ca2a_result.chain_valid and ca2a_result.holder_valid):
        raise ValueError("cA2A evidence is not valid")

    trace_action = trace_fixture["action"]["action_ref"]
    if ca2a_action_digest != trace_action:
        raise ValueError("cA2A request binding and TRACE action binding disagree")

    policy_digest = manifest_vector["manifest"]["artifacts"]["policy_bundle"]["hash"]

    successor_observed = state.successor_digest is not None

    return TransitionEvidence(
        authorization_id=(
            manifest_vector["manifest"]["manifest_id"]
            + ":"
            + ca2a_result.record_id
        ),
        authorized_resource_id=state.resource_id,
        execution_resource_id=state.resource_id,
        observation_resource_id=state.resource_id,
        authorized_action_digest=trace_action,
        executed_action_digest=trace_action,
        authorized_predecessor_digest=state.predecessor_digest,
        observed_predecessor_digest=state.predecessor_digest,
        expected_successor_digest=expected_successor_digest,
        observed_successor_digest=state.successor_digest,
        policy_digest=policy_digest,
        execution_policy_digest=policy_digest,
        predecessor_observer_trusted=state.predecessor_trusted,
        successor_observer_trusted=state.successor_trusted,
        predecessor_fresh=state.predecessor_fresh,
        successor_fresh=state.successor_fresh,
        execution_succeeded=execution_succeeded,
        replay_detected=replay_detected,
        successor_observed=successor_observed,
    )
