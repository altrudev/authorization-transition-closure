# State-Transition Binding Profile v0.1

Status: **Experimental Draft**

This profile defines the minimum portable evidence bindings needed for an
independent verifier to evaluate whether an authorized consequential action
produced an acceptable state transition.

It is intentionally compositional. It does not replace identity, authorization,
delegation, approval, execution-receipt, provenance, or attestation systems.

## 1. Design objective

The profile joins five facts that may originate in different assurance systems:

```text
authorization context
        +
predecessor state S0
        +
exact executed action
        +
successor state S1
        +
transition/replay evidence
        =
transition-closure decision
```

A conforming verifier returns one of:

- `CLOSED`
- `FAILED`
- `INDETERMINATE`

## 2. Non-goals

This profile MUST NOT be interpreted as:

- proof that an upstream authorization system is itself valid;
- proof that an observer is trustworthy merely because its output is hashed;
- a generic state database;
- an exactly-once transport protocol;
- a replacement for domain-specific transition semantics;
- evidence of authorship, ownership, or authority beyond the supplied evidence.

## 3. Top-level object

A profile document is a JSON object with:

```json
{
  "profile": "atc.stbp.v0.1",
  "transition_id": "...",
  "resource": {},
  "authorization": {},
  "execution": {},
  "predecessor": {},
  "successor": {},
  "replay": {},
  "predicate": {}
}
```

Unknown top-level fields MUST be rejected in v0.1.

## 4. Resource binding

`resource` identifies the exact state-bearing object.

Required fields:

- `resource_id` — non-empty application-defined identifier.
- `representation` — non-empty identifier for the state representation.

Example representations:

- `git-tree-sha256`
- `api-resource-etag`
- `database-row-canonical-json`
- `device-state-v1`
- `blockchain-state-root`

The profile does not interpret the representation. A domain adapter does.

All authorization, execution, and observation evidence MUST refer to this same
resource identity.

## 5. Authorization binding

`authorization` contains:

- `authorization_id`
- `action_digest`
- `predecessor_digest`
- `policy_digest`
- `evidence_ref`

The authorization MUST bind the exact action to the predecessor state against
which it was approved.

`evidence_ref` identifies the upstream authorization/approval evidence. The
reference itself does not make that evidence valid; validity is an input from
the relevant verifier.

## 6. Execution binding

`execution` contains:

- `action_digest`
- `policy_digest`
- `succeeded`
- `evidence_ref`

The execution action and policy digests MUST match the authorization bindings
for closure.

`succeeded=true` means only that the referenced execution evidence reports a
successful execution outcome under its own semantics. It does not establish S1.

## 7. State observations

Both `predecessor` and `successor` contain:

- `state_digest`
- `observer_id`
- `observed_at`
- `trusted`
- `fresh`
- `evidence_ref`

The observer identity is explicit because a digest binds bytes, not truth.

For `CLOSED`:

- both observations MUST be trusted by the relying party;
- both MUST be fresh under the applicable domain freshness rule;
- predecessor `state_digest` MUST equal the authorization
  `predecessor_digest`.

A stale observation is a positive contradiction and yields `FAILED`.

Unknown trust or freshness cannot establish closure and yields
`INDETERMINATE`.

## 8. Replay / uniqueness binding

`replay` contains:

- `status`: one of `not-replayed`, `replayed`, `unknown`
- `evidence_ref`

Semantics:

- `replayed` -> `FAILED`
- `unknown` -> `INDETERMINATE`
- `not-replayed` permits evaluation to continue

A bounded challenge window is not equivalent to `not-replayed` unless an
external mechanism establishes single-use or equivalent transition uniqueness.

## 9. Transition predicate

v0.1 defines one mandatory predicate type:

```json
{
  "type": "exact-successor-digest",
  "expected_successor_digest": "sha256:..."
}
```

The observed successor digest MUST equal the expected digest.

Future profiles may add domain predicates, but a verifier MUST NOT interpret an
unknown predicate type as success.

Unknown predicate type -> `INDETERMINATE`.

Known predicate with a false result -> `FAILED`.

## 10. Digest format

All v0.1 digest fields use:

```text
sha256:<64 lowercase hexadecimal characters>
```

A malformed digest is a profile-conformance failure.

## 11. Evidence references

An `evidence_ref` is an opaque non-empty string identifying independently
verifiable evidence.

Examples:

- a TRACE receipt id/hash;
- an Agent Manifest id;
- a cA2A provenance record;
- a signed observer receipt;
- a DSR result digest.

The profile MUST NOT dereference or trust the value merely because it is present.

## 12. Decision procedure

A v0.1 verifier evaluates in this order:

1. validate profile structure and digest syntax;
2. reject explicit replay;
3. require one resource identity;
4. require trusted/fresh predecessor evidence;
5. compare authorized and observed predecessor;
6. compare authorized and executed action;
7. compare authorization and execution policy;
8. require execution success;
9. require trusted/fresh successor evidence;
10. evaluate the transition predicate;
11. require known non-replay status;
12. return `CLOSED`.

Any positive contradiction returns `FAILED`.

Any missing or unresolved fact required for closure returns
`INDETERMINATE`.

## 13. Upstream composition

The profile is designed so existing systems remain within their own assurance
boundaries.

A composition may use:

- TRACE for action/execution evidence;
- Agent Manifest for approved configuration/HITL evidence;
- cA2A for delegated authority/holder binding;
- a domain observer for S0/S1;
- an exactly-once mechanism for replay status.

No one source is required to provide every field.

## 14. Security invariant

The core invariant is:

> Valid upstream evidence MUST NOT be promoted into a stronger transition claim
> unless the bindings needed for that stronger claim are independently present.

In particular:

```text
authorization != execution
execution != consequence
lineage != state continuity
freshness != exactly-once
digest equality != observer trust
```

## 15. Conformance

A v0.1 implementation is conformant when it:

- rejects structurally malformed profile documents;
- distinguishes contradiction from missing evidence;
- never returns `CLOSED` with unknown replay status;
- never returns `CLOSED` without trusted fresh S0 and S1;
- never returns `CLOSED` when action/policy/resource bindings disagree;
- never treats upstream evidence validity as proof of successor state.
