# ADR-0001: Use a Minimal State-Transition Binding Profile for Consequence Closure

- **Status:** Proposed / Experimental
- **Date:** 2026-09-11
- **Decision owners:** Repository maintainers
- **Scope:** Authorization Transition Closure (ATC) research prototype
- **Profile:** STBP v0.1

## Context

The repository investigates a narrow assurance question:

> Given valid upstream evidence about identity, authority, approval, policy,
> action binding, and execution-related events, what additional evidence is
> required before an independent verifier can establish that the authorized
> state transition actually occurred?

The current experiments use pinned evidence or algorithms from three upstream
systems:

- TRACE action-receipt evidence;
- Agent Manifest with HITL approval;
- cA2A delegation and holder binding.

Each system provides useful assurance at its own layer. The experiments also
show that those layers do not generically establish all of the following at once:

1. the exact target resource;
2. the predecessor state against which authorization was valid;
3. the exact executed action;
4. the actual execution outcome;
5. replay / transition uniqueness;
6. a trusted and fresh successor observation;
7. a predicate defining an acceptable successor.

The full composition experiment remains `INDETERMINATE` until those missing
facts are supplied. When they are supplied and agree, the same verifier returns
`CLOSED`. Contradictory evidence returns `FAILED`.

## Decision

Adopt an **experimental, minimal State-Transition Binding Profile (STBP v0.1)**
inside this repository as the portable composition format for those missing
bindings.

STBP v0.1 will carry only the facts needed to evaluate transition closure:

- resource identity and representation;
- authorization identity;
- authorized action digest;
- authorized predecessor digest;
- policy digest;
- execution action/policy binding and outcome;
- predecessor observation;
- successor observation;
- observer identity, trust and freshness;
- replay status;
- transition predicate;
- opaque references to the evidence establishing each fact.

The profile will not replace upstream identity, authorization, approval,
delegation, provenance, or attestation formats.

## Why this decision

### 1. The gap is compositional

The evidence tested so far is not simply "missing signatures" or "missing
identity." Strong cryptographic evidence can be present while transition closure
remains unresolved.

Adding another general-purpose identity or provenance format would therefore
solve the wrong problem.

### 2. The missing facts belong to different trust domains

Authorization, execution, resource-state observation, replay control, and
transition semantics may be established by different systems.

A composition profile allows those facts to remain independently verifiable.

### 3. A three-state verifier is necessary

The experiments repeatedly require a distinction between:

- `FAILED`: trusted evidence establishes a contradiction;
- `INDETERMINATE`: necessary evidence is missing or unresolved;
- `CLOSED`: every required binding is established and consistent.

Collapsing missing evidence into either success or failure loses information and
creates unsafe conclusions.

### 4. The profile can remain narrow

STBP need not store application state. It carries commitments, evidence
references, trust/freshness decisions, and a transition predicate.

That keeps state ownership with the domain system that actually observes it.

## Alternatives considered

### A. Extend TRACE directly

Rejected for now.

TRACE already distinguishes action/decision evidence from physical or external
completion in the tested material. Forcing generic application S0/S1 into TRACE
would broaden its responsibility before the need for such a change is proven.

STBP may later become a TRACE-adjacent profile if review shows that is the
smallest appropriate integration point.

### B. Extend Agent Manifest directly

Rejected for now.

Agent Manifest is strongest around approved configuration, manifest identity,
runtime verification, and HITL approval. The tested flow is not a generic
per-call target-resource state protocol.

### C. Extend cA2A directly

Rejected for now.

cA2A addresses delegated authority, holder binding, policy intersection, and
provenance. Its replay semantics deliberately permit reuse inside the stateless
challenge window unless deployment state is added.

That design trade should not be silently changed merely to satisfy ATC.

### D. Put all state in ATC

Rejected.

ATC/STBP should bind state evidence, not become the source of truth for
application state.

### E. Treat successful execution evidence as consequence proof

Rejected.

This is the exact inference the experiments show is unsafe. Execution success
does not establish an acceptable successor state.

### F. Do nothing and leave composition application-specific

Viable, but rejected as the current research direction.

The same unresolved bindings recur across the tested systems. A small portable
profile makes those assumptions explicit and testable rather than leaving each
integration to invent them implicitly.

## Consequences

### Positive

- The assurance boundary becomes explicit.
- Existing upstream systems keep their current responsibilities.
- Cross-system compositions can be tested consistently.
- Unknown evidence remains distinguishable from contradictory evidence.
- Reviewers can challenge or replace individual bindings without accepting the
  whole profile.
- The profile is representation-neutral.

### Negative / costs

- STBP introduces another data structure.
- Trust and freshness decisions remain deployment-specific.
- v0.1 only supports an exact-successor-digest predicate.
- A real deployment still needs domain-specific observers and replay controls.
- Interoperability requires adapters and explicit equivalence rules for actions,
  policies, and resources across systems.

## Security invariants

A conforming implementation must preserve:

```text
authorization != execution
execution != consequence
lineage != state continuity
freshness != exactly-once
signature validity != observer trust
digest equality != truth
unknown != false
```

No upstream artifact may be promoted to a stronger claim merely because it is
cryptographically valid.

## Falsification / reversal criteria

This ADR should be superseded or withdrawn if any of the following is shown:

1. an existing normative portable mechanism already binds the exact
   authorization, S0, execution, S1, replay semantics, and transition predicate;
2. one or more STBP fields are redundant because an existing mandatory binding
   already supplies the same assurance without ambiguity;
3. the profile cannot distinguish `FAILED` from `INDETERMINATE` consistently
   across realistic domains;
4. the observer/replay/predicate model is shown to require stateful semantics
   that cannot be represented safely as portable evidence bindings;
5. a simpler profile closes all currently demonstrated cases.

The goal is not to preserve STBP. The goal is to preserve the assurance
distinction the experiments exposed.

## Evidence supporting this ADR

- `analysis/interoperability-report-v0.1.md`
- `analysis/full-composition.md`
- `analysis/trace-adapter.md`
- `analysis/agent-manifest-adapter.md`
- `analysis/ca2a-adapter.md`
- `conformance/source-mapping-v0.1.json`
- `spec/state-transition-binding-profile-v0.1.md`
- `spec/conformance-v0.1.md`

The repository's executable test suite is the primary implementation evidence.
