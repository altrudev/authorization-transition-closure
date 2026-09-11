# Verifier Semantics

The reference verifier implements a deliberately narrow evidence model.

## Input fields

A verification case contains:

- `authorization_id`
- `authorized_action_digest`
- `executed_action_digest`
- `authorized_predecessor_digest`
- `observed_predecessor_digest`
- `expected_successor_digest` when the authorized consequence is exact
- `observed_successor_digest`
- `policy_digest`
- `execution_policy_digest`
- `execution_succeeded`
- `replay_detected`
- `successor_observed`

## Evaluation order

The verifier first checks whether enough evidence exists to reason about the transition. It then checks contradictions in bindings before considering closure.

A missing successor is `INDETERMINATE`.

A successor that is present but contradicts the expected successor is `FAILED`.

This distinction is important:

```text
unknown consequence != known bad consequence
```

## Extensibility

The first verifier supports exact digest equality only. Domain profiles may later replace the exact-successor comparison with a structured transition predicate while preserving the three-state disposition.
