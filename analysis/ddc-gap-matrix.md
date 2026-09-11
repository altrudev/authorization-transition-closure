# DDC Gap Matrix: Authorization to Transition Closure

Status: evidence-led research pass, not a proposed upstream specification change.

This analysis compares the ATC closure requirements against three current AgenTrust surfaces:

- `agentrust-io/trace-spec`
- `agentrust-io/ca2a`
- `agentrust-io/agent-manifest`

The purpose is to distinguish four different states:

1. a concept is absent;
2. a concept is represented but only asserted;
3. a concept is cryptographically or independently bound;
4. the binding is sufficient to close a state transition.

Presence is not counted as proof.

## DDC dimensions used

The pass examines the evidence radially rather than treating a successful signature as a universal success condition.

| Dimension | ATC question |
|---|---|
| Semantic | What exact action and consequence are being claimed? |
| Authority | Who authorized it, and within what scope? |
| State | Against which predecessor state was the decision valid, and what successor was observed? |
| Resource | Which concrete object, account, file, device, task, or other resource changed? |
| Physical / external | Does evidence establish an external consequence rather than a software decision? |
| Frequency / replay | Can the authorization or execution package be reused? |
| Lineage | Can the verifier reconstruct the exact chain leading to this action? |
| Policy | Which rule set governed authorization and execution? |
| Freshness | Was each observation valid for the decision being made? |
| Consequence | Did the resulting state satisfy the authorized transition predicate? |

## Cross-system matrix

Legend:

- **BOUND** — the inspected material defines a cryptographic or independently verifiable binding.
- **PARTIAL** — useful evidence exists, but it does not establish the ATC requirement by itself.
- **POINTER** — the system can name external evidence but explicitly does not make that target trusted evidence.
- **ABSENT** — no relevant binding was found in the inspected current material.
- **OUT OF SCOPE** — the source explicitly says it does not establish this property.

| ATC requirement | TRACE | cA2A | Agent Manifest | DDC conclusion |
|---|---|---|---|---|
| Agent/workload identity | BOUND through signed Trust Record / `cnf` and runtime claims | BOUND through delegation subject, holder proof, peer appraisal | BOUND through signed manifest identity and runtime correlation | Strong coverage |
| Delegated authority | PARTIAL in core TRACE; delegation link identifies parent record and credential | BOUND: signed attenuated delegation chain plus local-policy intersection | BOUND: signed delegation chain and verification policy | Strong coverage |
| Human approval | POINTER via TRACE `references.rel=approval-outcome`; external action receipts can supply separate evidence | Not the main primitive | BOUND where HITL applies: separate approver signature over manifest/action approval data | Strongest in Agent Manifest |
| Exact authorized action | PARTIAL: action-receipt profiles bind an action reference/call and detached evidence; `authorized-intent` reference is only a pointer | PARTIAL: holder proof commits requested capability and sealed-payload digest when present | PARTIAL/BOUND depending profile: HITL `evidence_hash` is defined over the action being approved; approved scope is independently signed | Useful action binding exists |
| Policy identity at decision | BOUND in Trust Record policy hash/enforcement mode | BOUND in effective-scope decision from delegated scope ∩ local policy, but provenance record carries only resulting scope/decision data | BOUND through policy-bundle artifact and verification context | Strong coverage |
| Execution occurrence | PARTIAL: tool transcript and action receipts can show invocation/decision evidence | PARTIAL: provenance record proves allow/deny decision and delegation lineage; task transport can bind payload | PARTIAL: decision-trace/runtime evidence can bind configured execution artifacts | Evidence of execution context, not consequence |
| Predecessor application state | ABSENT in inspected core/action-receipt material | ABSENT in inspected delegation/provenance model | ABSENT as a generic action-state primitive; manifest artifacts are configuration/runtime state, not arbitrary target-resource state | **Candidate gap** |
| Authorization-to-predecessor binding | ABSENT | ABSENT | ABSENT in inspected generic action/HITL flow | **Candidate gap** |
| Successor application state | OUT OF SCOPE for existing TRACE action-receipt example that explicitly does not claim physical completion; no generic successor commitment found | ABSENT in `DelegationRecord` | ABSENT as a generic post-action resource-state primitive | **Candidate gap** |
| Execution-to-successor binding | ABSENT | ABSENT | ABSENT | **Candidate gap** |
| Transition predicate | OUT OF SCOPE / profile-specific | ABSENT in delegation core | ABSENT as generic action consequence; policy checks configuration and authority | **Candidate gap** |
| Replay protection | PARTIAL: receipt freshness/chain checks exist; exact semantics depend on receipt profile | PARTIAL: holder challenge bounds replay window but profile explicitly says it is not exactly-once | PARTIAL: challenge nonce can be single-use for verification results; does not by itself make an external action exactly-once | Important unresolved dimension |
| Lineage / parent continuity | BOUND via delegation parent-record hash and receipt-chain checks | BOUND strongly through delegation chain and provenance DAG | BOUND through previous manifest/delegation/audit continuity mechanisms | Strong coverage |
| Independent observation of consequence | OUT OF SCOPE in action-decision evidence unless a separate trusted controller/evidence source supplies it | ABSENT | ABSENT as generic action consequence | **Candidate gap** |

## Evidence that prevents overclaiming

### TRACE

TRACE already draws the distinction ATC needs.

The current Trust Record can bind runtime, model, policy, data class and tool transcript. Its `references` block may point at `authorized-intent`, `approval-outcome`, or `behavior-trace`, but the specification explicitly says a reference is a pointer rather than attested evidence and cannot carry a pre-execution commitment.

Its action-receipt material is even more important. The conformance example describes a trusted controller accepting a bound action **without claiming physical completion**, and the audit-chain tutorial warns that a transcript digest does not establish that an action completed or that outputs are correct.

That is not a defect in TRACE. It is an explicit assurance boundary.

### cA2A

cA2A has strong authority and lineage semantics:

- signed attenuated delegation;
- holder proof over the leaf credential;
- challenge/audience binding;
- requested capability binding;
- sealed payload binding when present;
- local-policy intersection;
- provenance DAG parent continuity.

Its current `DelegationRecord` contains identity, credential, scope, parent link, caller-attestation outcome, and denial information. It does not contain generic predecessor-state or successor-state commitments.

The profile also explicitly states that holder binding is bounded by a challenge window rather than exactly-once. A captured exact request can be replayed inside that window unless a deployment adds state.

Again, this is an explicit design trade, not a defect.

### Agent Manifest

Agent Manifest strongly covers approved composition and HITL authority.

The HITL design can bind an approval to an action hash and approver signature. Verification results can be challenge-bound to a relying party's live request through `challenge_nonce` and `verification_context_hash`.

Those are powerful freshness and authority primitives.

But a manifest primarily proves which configuration/artifacts were approved and which runtime evidence matched them. The inspected HITL/action material does not generically bind:

```text
predecessor resource state
        ->
approved action
        ->
execution
        ->
observed successor resource state
```

## First DDC conclusion

The strongest current hypothesis is **not** "AgenTrust lacks action binding."

It does not.

The stronger and narrower statement is:

> Existing inspected AgenTrust evidence can establish substantial identity, authority, policy, action, freshness, and lineage facts, but no inspected generic primitive establishes that the exact authorized action was evaluated against a particular predecessor application state and produced an independently observed acceptable successor application state.

That is the ATC research boundary.

## What would falsify this hypothesis

This finding must be withdrawn or narrowed if an existing normative profile is found that binds all of the following for a generic consequential action:

1. the exact authorization;
2. the exact predecessor resource-state commitment;
3. the exact executed action;
4. execution identity/evidence;
5. the exact observed successor-state commitment;
6. freshness/ordering sufficient to relate S0 and S1 to that execution;
7. replay semantics;
8. a transition predicate or independently verifiable expected consequence.

Finding only one or several of these does not falsify the hypothesis.

## Next experiment

Do not propose a new field yet.

Build interoperable vectors using existing evidence first:

1. a valid authorized action with no successor observation -> `INDETERMINATE`;
2. valid HITL/action receipt + stale predecessor -> should remain unresolved by existing evidence;
3. valid cA2A lineage + replayed exact request inside challenge window -> authority remains valid while transition uniqueness is unresolved;
4. valid TRACE action receipt + wrong independently supplied successor -> ATC should fail even though the action receipt itself remains valid;
5. complete existing evidence + independently bound S0/S1 -> ATC closes.

Only after these vectors are executable should a minimal integration profile be proposed.
