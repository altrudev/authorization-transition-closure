# Executable Vector Format

ATC vectors are serialized JSON experiments. They deliberately separate facts
that ATC evaluates from facts assumed to have already been established by an
upstream evidence system.

## Shape

```json
{
  "id": "stable-vector-name",
  "description": "what ambiguity this vector tests",
  "source_assumptions": [
    "facts established by TRACE, cA2A, Agent Manifest, or another source profile"
  ],
  "evidence": {
    "...": "TransitionEvidence fields"
  },
  "expected": {
    "disposition": "CLOSED | FAILED | INDETERMINATE",
    "reason_contains": "stable reason fragment"
  }
}
```

## Why source assumptions are separate

ATC must not claim to verify another project's signature, attestation, delegation
or approval semantics unless it actually invokes that verifier.

A vector may therefore say:

> "cA2A holder proof verifies"

as an experimental premise.

That does **not** mean the ATC reference verifier independently verified cA2A.
It means the experiment asks a narrower question: given valid authority evidence,
is transition closure established?

This boundary prevents two opposite errors:

1. treating upstream validity as irrelevant; and
2. pretending ATC re-verifies evidence formats it does not implement.

## Closure requirements represented by the baseline format

The current exact-binding model requires:

- authorization identity;
- one concrete resource identity shared by authorization, execution and observations;
- exact authorized and executed action digests;
- authorized and observed predecessor-state digests;
- exact expected and observed successor-state digests;
- policy identity at authorization and execution;
- explicit trust decisions for predecessor and successor observers;
- freshness decisions for both observations;
- execution outcome;
- replay status;
- an independently observed successor.

A domain profile may replace exact successor equality with a richer predicate,
but it must preserve the three-state result model.
