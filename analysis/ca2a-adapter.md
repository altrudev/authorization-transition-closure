# cA2A Holder-Binding Adapter

This is the third empirical ATC integration.

Pinned upstream source:

- repository: `agentrust-io/ca2a`
- revision: `d3b7eb618084c4dc2f1270c2050d443f5bab5a3d`
- holder proof: `src/ca2a_runtime/delegation/holder.py`
- credential verification: `src/ca2a_runtime/delegation/credential.py`
- challenge verification: `src/ca2a_runtime/challenge.py`
- canonicalization: `src/ca2a_runtime/canonical.py`
- replay regression: `tests/unit/test_holder_binding.py`

cA2A does not publish a committed portable holder-proof JSON fixture at this revision.
ATC therefore does not claim one exists. The integration uses a deterministic
cross-implementation vector derived from the pinned upstream byte rules.

The property under test is upstream's explicit guarantee:

```text
delegation chain     VALID
holder proof         VALID
requested capability BOUND
same proof in window VALID AGAIN
exactly-once         NOT ESTABLISHED
```

The same replay-window behavior is pinned upstream by
`test_a_proof_replays_inside_its_challenge_window`.

ATC must therefore preserve:

```text
valid delegated authority != exactly-once consequential transition
```

A valid cA2A proof can contribute authority and exact request binding while replay
status remains unresolved. In that state ATC must return `INDETERMINATE`, even
if another evidence source later asserts execution success and a matching successor.
