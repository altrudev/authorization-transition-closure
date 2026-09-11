# Conformance Vector Plan

The conformance corpus will grow from the reference verifier into serialized, implementation-independent cases.

Initial required vectors:

| Vector | Expected disposition | Purpose |
|---|---|---|
| valid-transition | CLOSED | complete exact binding |
| stale-predecessor | FAILED | authorization evaluated a different state |
| action-substitution | FAILED | execution differs from authorization |
| successor-substitution | FAILED | supplied post-state is not the expected result |
| replay | FAILED | valid package reused |
| policy-version-skew | FAILED | authorization and execution policy differ |
| execution-failure | FAILED | action did not execute successfully |
| successor-unobserved | INDETERMINATE | consequence cannot be established |
| replay-status-unknown | INDETERMINATE | non-replay cannot be established |
| transition-predicate-missing | INDETERMINATE | no domain consequence rule is available |

Future vectors should add partial effects, collateral mutation, concurrent state change, stale observation, multi-resource atomicity, and domain-specific predicates.
