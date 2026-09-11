# Full Composition Experiment

The full ATC composition experiment joins the three verified upstream evidence
families already implemented in this repository:

- TRACE action receipt;
- Agent Manifest + HITL approval;
- cA2A delegation + holder proof.

The composition layer does not merge their assurance claims into one larger
claim. Each source contributes only the fact it actually establishes.

## Inputs

### TRACE contributes

- a verified action reference;
- call/session-bound controller evidence;
- a valid receipt signature.

It does not contribute physical completion.

### Agent Manifest contributes

- a verified manifest signature;
- approved policy/configuration identity;
- a verified HITL approval.

It does not contribute generic per-call authorization or target-resource state.

### cA2A contributes

- trusted delegated authority;
- holder possession;
- exact requested-capability / record binding.

It does not contribute exactly-once semantics.

### External state evidence contributes

- target resource identity;
- trusted/fresh predecessor observation S0;
- trusted/fresh successor observation S1;
- replay/exactly-once evidence;
- expected transition predicate.

## State machine demonstrated

The test suite walks the same verified upstream bundle through progressively
stronger evidence states:

```text
TRACE valid
+ Agent Manifest valid / HITL approved
+ cA2A valid
------------------------------------------------
execution unknown
=> INDETERMINATE
```

Then:

```text
+ execution success
+ trusted matching successor
but replay status unknown
=> INDETERMINATE
```

Then:

```text
+ replay status known non-replayed
but no successor
=> INDETERMINATE
```

Then:

```text
+ trusted successor
but no transition predicate
=> INDETERMINATE
```

Then:

```text
+ trusted fresh S0
+ exact action agreement across cA2A and TRACE
+ execution success
+ known non-replay
+ trusted fresh S1
+ S1 satisfies the expected transition
=> CLOSED
```

A wrong successor yields `FAILED`, even though TRACE, Agent Manifest, and cA2A
remain individually valid.

## Core result

This is the narrow research claim ATC can now demonstrate executablely:

> Valid identity, authority, approval, action binding, execution evidence and
> lineage can all coexist without sufficient evidence to establish a valid
> state transition.

Transition closure requires the missing join between the authorization context,
the exact resource predecessor, execution, replay semantics, and a trusted
successor observation evaluated against an explicit transition predicate.

That join is what ATC verifies. It does not require the upstream formats to
become generic state databases.
