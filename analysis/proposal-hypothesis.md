# Proposal Hypothesis: State-Transition Binding Profile

This document is intentionally a hypothesis, not an upstream proposal.

## Candidate contribution

Define a minimal, representation-neutral profile that lets an independent verifier compose existing authorization/execution evidence with external state observations.

The profile would not replace TRACE, cA2A, Agent Manifest, Acta, hardware attestation, or application-specific policy.

It would define the missing join:

```text
authorization evidence
        +
predecessor-state observation
        +
execution evidence
        +
successor-state observation
        +
transition predicate
        =
transition-closure result
```

## Minimal information under investigation

A future profile may need to bind concepts equivalent to:

- `authorization_digest`
- `action_digest`
- `predecessor_state_digest`
- `predecessor_observed_at` or version/sequence token
- `execution_evidence_digest`
- `successor_state_digest`
- `successor_observed_at` or version/sequence token
- `resource_id`
- `transition_policy_digest`
- replay/sequence evidence
- observer identity / trust basis

These are concepts, not proposed field names.

## Why a separate profile may be preferable

Putting generic application-state semantics directly into a Trust Record or manifest risks making those formats responsible for every database, blockchain, filesystem, API and physical-device state model.

A compositional profile keeps each system's assurance boundary intact:

- TRACE can continue proving runtime/execution evidence.
- cA2A can continue proving delegated authority and lineage.
- Agent Manifest can continue proving approved configuration and human authority.
- Domain observers can prove state in the representation native to the resource.
- ATC can verify whether the evidence composes into a closed transition.

## DDC gate before proposing upstream

No upstream proposal should be filed until all of these are true:

1. at least one real existing system can produce S0 and S1 observations;
2. the ATC verifier can combine them with existing AgenTrust evidence;
3. adversarial vectors demonstrate a case existing verification accepts while transition closure must remain `INDETERMINATE` or `FAILED`;
4. no existing normative field/profile already closes that case;
5. the proposed addition is the smallest change that resolves the measured ambiguity.

If these conditions are not met, the correct outcome is research documentation rather than a specification change.
