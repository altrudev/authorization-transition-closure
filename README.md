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
- **FAILED** — trustworthy evidence establishes a contradiction, mismatch, replay, stale observation, wrong resource, or unacceptable consequence.
- **INDETERMINATE** — there is not enough trustworthy evidence to establish either closure or failure.

Missing evidence is not equivalent to success and is not always evidence of failure.

## Current DDC finding

A cross-system pass over TRACE, cA2A, and Agent Manifest found substantial existing coverage for identity, delegated authority, policy, action/request binding, approvals, freshness, and lineage.

The narrower unresolved hypothesis is:

> Existing inspected evidence does not generically bind the exact authorization to a particular predecessor application state and then bind execution to an independently observed acceptable successor application state.

See:

- `analysis/ddc-gap-matrix.md`
- `analysis/evidence-ledger.md`
- `analysis/proposal-hypothesis.md`

This is a research hypothesis, not a claim that the upstream projects are defective.

## Executable experiment

The repository now contains serialized cross-system vectors. Each vector explicitly separates:

1. **source assumptions** — facts assumed to have been verified by TRACE, cA2A, Agent Manifest, or another upstream profile; and
2. **ATC evidence** — the facts the reference transition verifier actually evaluates.

The initial interoperability cases are:

| Vector | Upstream premise | ATC result |
|---|---|---|
| valid action, no successor | valid authorization/action evidence | `INDETERMINATE` |
| valid approval, stale predecessor | valid HITL/action approval | `FAILED` |
| cA2A authority, replay unknown | valid delegation + holder proof | `INDETERMINATE` |
| TRACE receipt, wrong successor | valid action receipt | `FAILED` |
| complete state-bound transition | valid upstream evidence + trusted fresh S0/S1 | `CLOSED` |

The reference verifier will not return `CLOSED` unless authorization, execution, and observations identify the same resource; action and policy bindings agree; predecessor and successor observations are trusted and fresh; execution succeeded; the successor satisfies the transition predicate; and replay status is known.

## Repository layout

```text
analysis/
  ddc-gap-matrix.md
  evidence-ledger.md
  proposal-hypothesis.md

spec/
  model.md
  threat-model.md
  verifier-semantics.md
  vector-format.md

reference/
  __init__.py
  verifier.py

tests/
  test_verifier.py
  test_vectors.py

vectors/
  01-valid-action-no-successor.json
  02-valid-approval-stale-predecessor.json
  03-ca2a-valid-authority-replay-unknown.json
  04-trace-valid-receipt-wrong-successor.json
  05-complete-state-bound-transition.json
  README.md
```

## Run

Use Python 3.11+:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

No GitHub Actions workflow is required. The corpus is intended to be runnable by any independent verifier or governed executor.

## Scope

ATC is deliberately representation-neutral. A state commitment might represent a database object, blockchain state root, filesystem tree, Git tree, API resource version, device state, or another independently verifiable representation.

ATC does **not** authenticate upstream evidence merely by accepting its digest. Observer trust and evidence-source validity remain explicit relying-party inputs.

## Relationship to existing assurance systems

ATC is designed to compose with evidence produced by other systems rather than replace identity, authorization, provenance, execution receipts, attestation, or transparency mechanisms.

A future integration profile should be proposed only after executable vectors demonstrate an ambiguity that existing normative mechanisms cannot already resolve.

## Status

Experimental research artifact with pinned upstream adapters, a full cross-system composition experiment, STBP v0.1 draft profile/schema, conformance requirements, interoperability mapping, and governed DSR verification.

For external technical review, start with:

- `docs/research-note-v0.1.md`
- `docs/adr/0001-state-transition-binding-profile.md`
- `REVIEW.md`

STBP v0.1 is not presented as a finished standard. The profile should be narrowed, superseded, or retired if an existing normative mechanism already closes the demonstrated transition-evidence gap.
