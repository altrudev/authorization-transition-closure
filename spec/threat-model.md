# Threat Model

ATC assumes evidence may be incomplete, reordered, replayed, substituted, or individually valid while collectively describing different events.

## Adversarial cases

### Stale predecessor

Authorization is valid for predecessor `S0`, but execution occurs after the resource has advanced to `S2`.

Risk: the action was authorized under conditions that no longer existed.

### Action substitution

Authorization binds action `A`, but execution evidence describes action `B`, or omits consequence-bearing arguments.

Risk: an execution receipt is valid but not for the authorized operation.

### Successor substitution

A valid successor state is supplied, but it is not the successor caused by the execution under evaluation.

Risk: post-state evidence is true but irrelevant.

### Replay

A valid authorization and execution package is used more than once where only one transition was authorized.

Risk: individually valid evidence supports an unauthorized additional consequence.

### Partial effect

Execution performs only part of a compound transition.

Risk: a tool reports success while the intended invariant is not achieved.

### Collateral mutation

The intended state change occurs, but additional forbidden state changes also occur.

Risk: checking only the expected field produces a false positive.

### Policy skew

Authorization binds policy version `P1`; evaluation or execution uses `P2`.

Risk: transition validity is judged under rules that were not authorized.

### Observation gap

Execution evidence is present but the successor cannot be independently observed or sufficiently attributed.

Risk: absence of contradictory evidence is mistaken for proof of success.

## Trust assumptions

ATC does not make unverified inputs trustworthy by hashing them. A digest binds bytes; it does not establish that the underlying observation is true.

Profiles must state which evidence sources are trusted and why.
