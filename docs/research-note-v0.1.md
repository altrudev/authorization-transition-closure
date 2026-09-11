# Research Note: From Authorization Evidence to Transition Closure

**Status:** Experimental research note  
**Version:** 0.1  
**Date:** 2026-09-11

## Abstract

Modern agent assurance systems can establish strong facts about identity,
delegated authority, human approval, policy, request binding, provenance, and
execution-related evidence. Those facts are necessary, but they do not
necessarily establish that the authorized state transition occurred.

This repository tests that distinction against three concrete assurance
surfaces: TRACE action receipts, Agent Manifest HITL approval, and cA2A
delegation/holder binding.

The result is a narrow claim:

> A verifier can accept valid upstream evidence about who was authorized to do
> what, under which policy, without yet having enough evidence to establish the
> resulting state transition.

The missing join is between authorization context, predecessor state,
execution, replay semantics, successor observation, and the predicate that
defines an acceptable consequence.

STBP v0.1 is an experimental proposal for carrying that join. It is not a
replacement for the upstream systems and is not presented as a finished
standard.

## 1. Research question

The central question is:

> What must an offline or independent verifier know before it can distinguish
> "the authorized action was validly requested or accepted" from "the authorized
> state transition was established"?

The repository uses three dispositions:

- `CLOSED` — sufficient trusted evidence establishes the transition;
- `FAILED` — trusted evidence establishes a contradiction;
- `INDETERMINATE` — the evidence is insufficient to establish either result.

This distinction is essential. Unknown consequence is not the same as known bad
consequence, and neither is success.

## 2. Experimental method

The work proceeded in four stages.

### 2.1 Inspect existing assurance boundaries

TRACE, Agent Manifest, and cA2A were inspected for bindings related to:

- action identity;
- policy;
- authority;
- human approval;
- lineage;
- freshness;
- replay;
- predecessor state;
- successor state;
- consequence.

The analysis deliberately treats "represented," "signed," "trusted," and
"consequence-proving" as different properties.

### 2.2 Verify real or pinned upstream evidence

The repository then built adapters around pinned upstream material.

**TRACE:** a real signed action-receipt conformance fixture is independently
verified. The receipt proves a bound controller decision but explicitly does not
claim physical completion.

**Agent Manifest:** the pinned `AM-VEC-009` manifest and HITL approval are
verified. The result remains valid even when a separately bound target-resource
predecessor is stale.

**cA2A:** the pinned holder/delegation/challenge algorithms are reproduced with
deterministic inputs. A valid holder proof verifies more than once inside the
stateless challenge window, matching cA2A's documented replay semantics.

### 2.3 Compose the upstream evidence

The three valid upstream layers are composed without strengthening any of their
claims.

The composition remains `INDETERMINATE` when execution consequence, replay
status, or successor evidence is unresolved.

A wrong successor produces `FAILED` even while every upstream layer remains
valid.

### 2.4 Add the missing state-transition evidence

The composition reaches `CLOSED` only when the verifier also receives:

- one exact resource identity and representation;
- an authorized predecessor commitment;
- a trusted and fresh predecessor observation;
- exact action/policy agreement;
- execution success evidence;
- known non-replay;
- a trusted and fresh successor observation;
- a transition predicate that the successor satisfies.

## 3. Main finding

The experiments support this narrower statement:

> Identity, authority, approval, action binding, provenance, and
> execution-related evidence are not equivalent to consequence evidence.

This is not a claim that TRACE, Agent Manifest, or cA2A are deficient. In the
tested material, each system draws a defensible boundary around what it proves.

The unresolved layer is compositional.

## 4. Why predecessor state matters

An authorization is often meaningful only relative to the state that was
evaluated.

For example:

```text
approve transfer while balance = 100
```

does not necessarily authorize the same transfer after another action changes
the balance to 20.

Therefore an action can remain:

- authentic;
- correctly delegated;
- correctly approved;
- correctly signed;

while no longer being valid against the current resource state.

This is why stale predecessor evidence produces `FAILED` rather than merely
"approval invalid."

## 5. Why successor state matters

A receipt can establish that a controller accepted or invoked an action without
establishing the external consequence.

The verifier therefore needs an independently meaningful S1 observation.

Even then, S1 alone is insufficient. The verifier also needs to know what
transition was expected.

For v0.1, STBP deliberately uses the narrowest predicate:

```text
observed_successor_digest == expected_successor_digest
```

Richer domain predicates are deferred.

## 6. Why replay is separate

Freshness and replay are related but not equivalent.

The cA2A experiment is instructive: the holder proof is fresh, authentic, bound
to the requested capability, and still reusable within the challenge TTL.

Therefore:

```text
fresh proof != exactly-once transition
```

ATC cannot return `CLOSED` while replay status is unresolved.

## 7. Candidate profile

STBP v0.1 carries only the portable bindings needed to evaluate closure:

```text
resource
authorization
execution
predecessor observation
successor observation
replay status
transition predicate
evidence references
```

It intentionally does not define:

- identity systems;
- signature formats for upstream evidence;
- application state storage;
- observer trust roots;
- domain freshness rules;
- exactly-once infrastructure;
- rich semantic transition languages.

Those remain responsibilities of the systems that actually own them.

## 8. Limitations

The current work has important limits.

First, the experiments cover specific pinned upstream artifacts and
implementations. They do not prove that every profile or deployment of those
projects has the same boundary.

Second, observer trust is an input. STBP does not transform a signed observation
into a trustworthy observation.

Third, v0.1 uses exact SHA-256 state commitments and exact-successor equality.
Many real transitions require structured predicates.

Fourth, the current cA2A interop test reproduces the pinned upstream algorithms
with deterministic inputs rather than consuming a committed portable
holder-proof fixture, because such a fixture was not found at the inspected
revision.

Fifth, the work demonstrates an interoperability gap, not the inevitability of
STBP as the solution.

## 9. Falsifiable open question

The most important review question is:

> Does an existing normative portable mechanism already bind authorization to
> an exact predecessor resource state and bind execution to a trusted successor
> state, with explicit replay semantics and an evaluable transition predicate?

If yes, STBP should be narrowed, replaced, or abandoned.

If no, STBP is a candidate minimal composition profile for that missing join.

## 10. Current evidence package

The repository contains:

- pinned upstream fixtures/source provenance;
- independent adapters;
- adversarial tests;
- composition tests;
- a JSON schema;
- conformance requirements;
- machine-readable source mappings;
- a reference verifier;
- governed DSR execution receipts.

The work should therefore be reviewed as an **experimental technical artifact**,
not as a claim of standardization.
