# STBP v0.1 Conformance Requirements

Status: **Experimental Draft**

This document defines the minimum requirements for implementations claiming
conformance with the State-Transition Binding Profile (STBP) v0.1.

## 1. Conformance classes

STBP v0.1 defines three conformance classes.

### 1.1 Producer

A conforming producer emits a structurally valid `atc.stbp.v0.1` document.

A producer MUST:

- emit every required field;
- use canonical lowercase SHA-256 digest syntax;
- identify one resource representation;
- distinguish unknown facts from false facts;
- not emit `not-replayed` unless an evidence source actually establishes that property;
- not mark observations trusted merely because they are signed or hashed;
- provide non-empty evidence references for every externally established fact.

A producer MUST NOT claim `CLOSED`. Disposition belongs to the verifier.

### 1.2 Verifier

A conforming verifier MUST:

- reject malformed profile documents before semantic evaluation;
- return exactly one of `CLOSED`, `FAILED`, or `INDETERMINATE`;
- return `FAILED` for an explicit contradiction established by trusted evidence;
- return `INDETERMINATE` when a fact required for closure is unresolved;
- never promote upstream validity into successor-state proof;
- never return `CLOSED` with unknown replay status;
- never return `CLOSED` with stale or untrusted S0/S1;
- never return `CLOSED` with action, policy, predecessor, or successor mismatch.

### 1.3 Adapter

An adapter maps an upstream assurance artifact into one or more STBP fields.

A conforming adapter MUST document:

- the exact upstream source/profile/version;
- which STBP field each upstream claim can populate;
- whether the upstream claim is cryptographically bound, locally trusted, asserted, or unresolved;
- the assurance ceiling that MUST be preserved.

An adapter MUST NOT populate an STBP field solely because a semantically nearby
field exists upstream.

## 2. Mandatory semantic tests

Every verifier implementation MUST pass equivalents of these cases:

| Case | Expected |
|---|---|
| all required bindings valid | `CLOSED` |
| explicit replay | `FAILED` |
| replay unknown | `INDETERMINATE` |
| stale predecessor | `FAILED` |
| predecessor trust unknown | `INDETERMINATE` |
| action mismatch | `FAILED` |
| policy mismatch | `FAILED` |
| execution outcome unknown | `INDETERMINATE` |
| execution failure | `FAILED` |
| successor absent | `INDETERMINATE` |
| successor trust unknown | `INDETERMINATE` |
| stale successor | `FAILED` |
| successor contradicts predicate | `FAILED` |

## 3. Upstream validity boundary

Conformance requires preserving this distinction:

```text
upstream artifact valid
        !=
STBP field established
        !=
transition CLOSED
```

For example:

- TRACE receipt validity can establish that a bound action receipt verifies;
- Agent Manifest validity can establish approved manifest/HITL context;
- cA2A validity can establish delegated authority and holder possession;
- none of these facts alone establishes target-resource S1.

## 4. Evidence-reference requirements

`evidence_ref` is an identifier, not proof.

A verifier or relying party MAY dereference or separately verify it through an
adapter, but MUST NOT treat presence of a reference as evidence validity.

## 5. Trust decisions

Observer trust is a relying-party decision.

A profile producer may carry the decision, but a conforming verifier deployment
SHOULD document the trust policy used to produce `trusted=true`.

Signed evidence and trusted evidence are not synonymous.

## 6. Freshness decisions

Freshness is domain-specific.

A conforming deployment MUST define how it decides:

- predecessor freshness;
- successor freshness;
- allowed observation/execution ordering;
- acceptable clock, version, sequence, or state-token skew.

The core profile does not invent these semantics.

## 7. Replay semantics

The value `not-replayed` requires evidence that rules out duplicate transition
use to the level required by the domain.

A challenge that is reusable within a TTL MUST NOT by itself be translated to
`not-replayed`.

## 8. Predicate semantics

STBP v0.1 requires `exact-successor-digest`.

An implementation encountering another predicate type MUST refuse v0.1
conformance for that document rather than silently applying approximate
semantics.

## 9. Failure discipline

A verifier MUST preserve:

```text
unknown != false
false != malformed
malformed != untrusted
untrusted != stale
```

These distinctions are part of the interoperability contract.

## 10. Versioning

A future profile revision that changes required fields, digest semantics,
predicate semantics, or decision semantics MUST use a new profile identifier.

A v0.1 verifier MUST NOT guess how to interpret a future version.
