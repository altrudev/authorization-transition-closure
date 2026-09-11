# Executable Conformance Vectors

The vector corpus tests the current ATC hypothesis against evidence boundaries already present in TRACE, cA2A, and Agent Manifest.

Each JSON file contains:

- a stable vector id;
- a human-readable description;
- explicit `source_assumptions`;
- the `TransitionEvidence` supplied to ATC;
- the expected ATC disposition and reason fragment.

See `spec/vector-format.md` for the normative experiment format.

## Initial cross-system vectors

| File | Upstream premise | Expected ATC disposition | Why |
|---|---|---|---|
| `01-valid-action-no-successor.json` | valid action/authorization evidence | `INDETERMINATE` | no independently observed consequence |
| `02-valid-approval-stale-predecessor.json` | valid HITL/action approval | `FAILED` | the state assumption used by authorization is stale |
| `03-ca2a-valid-authority-replay-unknown.json` | valid cA2A delegation and holder proof | `INDETERMINATE` | exact transition uniqueness is not established |
| `04-trace-valid-receipt-wrong-successor.json` | valid TRACE-composing receipt | `FAILED` | external successor contradicts the authorized transition |
| `05-complete-state-bound-transition.json` | valid upstream evidence plus trusted fresh S0/S1 | `CLOSED` | every current exact-binding invariant is established |

## Important interpretation rule

A vector that says an upstream artifact is valid does not mean the ATC reference implementation verified that upstream artifact.

For example:

```text
"cA2A holder proof verifies"
```

is a premise supplied to the ATC experiment.

The experiment then asks:

```text
Given that valid authority evidence, can the resulting state transition be closed?
```

This separation prevents ATC from laundering an assumption into a verification claim.

## Next vector families

After the initial corpus is independently executed, extend it with:

- partial effects;
- collateral mutation;
- concurrent state change between authorization and execution;
- stale successor observation;
- multi-resource atomicity;
- observer substitution;
- observer compromise;
- action succeeds but postcondition fails;
- exactly-once profile versus bounded replay window;
- profile-defined non-exact transition predicates.
