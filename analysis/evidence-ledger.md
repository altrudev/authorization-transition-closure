# Evidence Ledger

This ledger records the concrete upstream observations behind the ATC gap matrix. It intentionally separates facts from interpretation.

## TRACE

Repository: `agentrust-io/trace-spec`

Observed:

- Trust Records bind execution environment, policy, tool transcript, identity and lineage-related claims.
- `references` registers `authorized-intent`, `approval-outcome`, and `behavior-trace`.
- The specification says a reference is a pointer, not attested evidence.
- The specification says a reference cannot carry a pre-execution commitment.
- Action-receipt examples verify issuer trust, signature, action binding, freshness and chain properties.
- The action-receipt example explicitly describes an accepted bound action without claiming physical completion.
- The audit-chain tutorial states that transcript matching does not establish action completion or output correctness.

Interpretation:

TRACE deliberately stops before generic consequence proof. ATC should compose with TRACE rather than claim TRACE is defective.

## cA2A

Repository: `agentrust-io/ca2a`

Observed:

- Delegation credentials form a signed attenuated authority chain.
- Holder proof commits the live presenter to audience/challenge, leaf credential/subject, requested capability, record id, parent-record hash, sealed payload when present, and offered channel key when present.
- Effective scope is delegated leaf scope intersected with local policy.
- `DelegationRecord` carries `record_id`, `credential_id`, `subject`, `scope`, `parent_record_hash`, caller-attestation status, and denial-specific fields.
- Provenance DAG verification detects tampering, reparenting and continuation after denial.
- The profile states holder proof is at-most-once per challenge window, not exactly-once.

Interpretation:

cA2A strongly answers "who held what authority for this request and how did the authority chain continue?" It does not generically answer "what target state existed before the request and what state resulted afterward?"

## Agent Manifest

Repository: `agentrust-io/agent-manifest`

Observed:

- Manifest artifacts bind approved system prompt, policy bundle, tool manifest, model identity and other configuration/evidence artifacts.
- HITL approval is independently signed by the approver.
- The HITL design defines action/evidence binding and time-bounded approval.
- Verification results support relying-party challenge binding through `challenge_nonce` and `verification_context_hash`.
- Runtime correlation distinguishes stable agent identity and instance identity.
- Verification explicitly distinguishes VALID, MISMATCH, INCOMPLETE and UNVERIFIABLE states.

Interpretation:

Agent Manifest supplies strong approved-configuration, human-authority, and freshness primitives. Those can feed ATC but do not replace target-resource predecessor/successor evidence.

## DDC contradiction checks

### Detection != consequence

A valid execution log can prove that an event was recorded without proving the external state changed as intended.

### Authorization != transition validity

A valid authorization can remain cryptographically valid while its predecessor assumptions become stale.

### Execution success != acceptable successor

A tool or controller can report success while producing a partial, collateral, stale, or substituted state.

### Lineage != state continuity

A hash-linked evidence chain proves evidence lineage. It does not automatically prove continuity of the external resource being acted upon.

### Freshness != exactly-once

A challenge window can limit replay without proving a consequential operation occurred exactly once.

These distinctions are the working invariants for the next vector set.
