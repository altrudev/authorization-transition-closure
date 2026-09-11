# Authorization Transition Closure

Authorization Transition Closure (ATC) is an experimental assurance model for answering a question that identity, authorization, execution logs, and signatures do not answer by themselves:

> Did an authorized action produce an acceptable state transition from the state that authorization actually evaluated?

ATC treats authorization and execution as necessary evidence, but not as proof of consequence.

## Problem

An agent may be correctly identified, hold valid authority, call an allowed tool with approved arguments, and produce a valid execution receipt while the resulting state is still wrong, stale, replayed, incomplete, substituted, or impossible to verify.

ATC models the full chain:

```text
predecessor state
      |
proposed action
      |
authorization
      |
execution evidence
      |
observed successor state
      |
transition verification
```

The verifier returns one of three dispositions:

- **CLOSED** — the supplied evidence is sufficient to establish the authorized transition.
- **FAILED** — the evidence establishes a contradiction, mismatch, replay, stale predecessor, or unacceptable consequence.
- **INDETERMINATE** — there is not enough trustworthy evidence to establish either closure or failure.

The third state is intentional. Missing evidence is not equivalent to success and is not always evidence of failure.

## Initial research questions

1. What binds an authorization to the exact predecessor state it evaluated?
2. What binds execution evidence to the exact authorized action?
3. What binds the observed successor state to that execution?
4. How should replay and stale-state transitions be detected?
5. How should a verifier distinguish a contradictory transition from an unobservable one?
6. Which parts of this chain can existing evidence systems already establish, and where are new bindings actually required?

## Repository layout

```text
spec/
  model.md
  threat-model.md
  verifier-semantics.md

reference/
  verifier.py

tests/
  test_verifier.py

vectors/
  README.md
```

## Scope

ATC is deliberately representation-neutral. A state commitment might represent a database object, blockchain state root, filesystem tree, Git tree, API resource version, device state, or another independently verifiable representation.

This repository does **not** claim that every system can observe complete state, nor that transition closure can always be established. Where evidence is insufficient, the correct result is `INDETERMINATE`.

## Relationship to existing assurance systems

ATC is designed to evaluate evidence produced by other systems rather than replace identity, authorization, provenance, execution receipts, attestation, or transparency mechanisms.

Integration work should follow evidence. The first goal is to determine which transition-closure vectors existing systems can already resolve and which remain ambiguous.

## Status

Early research prototype. The current model and verifier are intentionally small so that assumptions are visible and falsifiable.
