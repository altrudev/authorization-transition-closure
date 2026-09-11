# Technical Review Package

This document is the current review boundary for Authorization Transition
Closure / STBP v0.1.

## Normative / candidate normative

- `spec/state-transition-binding-profile-v0.1.md`
- `spec/conformance-v0.1.md`
- `schema/stbp-v0.1.schema.json`
- `docs/adr/0001-state-transition-binding-profile.md`

## Research note

- `docs/research-note-v0.1.md`

## Evidence and interoperability

- `analysis/ddc-gap-matrix.md`
- `analysis/evidence-ledger.md`
- `analysis/trace-adapter.md`
- `analysis/agent-manifest-adapter.md`
- `analysis/ca2a-adapter.md`
- `analysis/full-composition.md`
- `analysis/interoperability-report-v0.1.md`
- `conformance/source-mapping-v0.1.json`

## Executable implementation

- `reference/verifier.py`
- `reference/stbp.py`
- `reference/trace_adapter.py`
- `reference/agent_manifest_adapter.py`
- `reference/ca2a_adapter.py`
- `reference/composition.py`

## Conformance evidence

The test corpus covers exact closure, explicit replay, replay uncertainty, stale
predecessor, observer trust uncertainty, action mismatch, policy mismatch,
missing execution outcome, missing successor evidence, successor mismatch,
upstream signature tampering, valid TRACE receipt without consequence proof,
valid Agent Manifest HITL with stale target state, valid cA2A holder-proof replay
inside its challenge window, and full cross-system composition.

## Current assurance statement

The project can demonstrate, with pinned upstream artifacts/algorithms and a
governed DSR run, that:

> Valid identity, authority, human approval, action binding, provenance and
> execution-related evidence do not necessarily establish that the authorized
> state transition occurred.

The candidate STBP profile is the smallest currently implemented portable join
for the remaining S0/S1, replay and predicate evidence.

## Review discipline

Reviewers should challenge the profile in this order:

1. Is the purported gap already covered by an existing normative primitive?
2. Does any STBP field duplicate an existing binding unnecessarily?
3. Does the profile accidentally strengthen an upstream assurance claim?
4. Can any required field be removed while preserving the demonstrated
   distinction between `CLOSED`, `FAILED`, and `INDETERMINATE`?
5. Are observer trust, freshness, replay, and predicate semantics sufficiently
   separated?
6. Is exact-successor-digest too narrow for v0.1, or correctly minimal?

If an existing normative mechanism already closes the demonstrated cases, the
profile should be narrowed or retired rather than defended.
