# Agent Manifest HITL Adapter

This is the second empirical ATC integration.

Pinned source:

- repository: `agentrust-io/agent-manifest`
- revision: `3525644331fc5d7a7d9055a875bd5c81f31fc492`
- vector: `python/tests/vectors/AM-VEC-009.json`
- source blob: `23ff1e409efd60105d3bd0c387978a55daed918d`

The vector is language-neutral test material with deterministic Ed25519
manifest and approver signatures.

## What is independently verified

The ATC adapter verifies:

- the manifest's Ed25519 signature against the vector's trusted issuer key;
- system-prompt, policy-bundle, and model-version observations;
- manifest expiry;
- the independently signed HITL approval;
- approval-to-manifest binding;
- approval scope and approval expiry.

For the pinned fixture the expected upstream result is:

```text
Agent Manifest: VALID
HITL:           APPROVED
```

## Important boundary discovered

Agent Manifest does **not** generically bind a per-call consequential action.

Its own specification says:

> Per-call authorization - the manifest binds which tools were approved, not
> what a call through one of them may do.

Accordingly, ATC does not manufacture an `authorized_action_digest` from a
valid HITL approval.

A valid HITL approval therefore remains insufficient on its own for transition
closure.

## Stale-predecessor experiment

The second experiment composes the valid Agent Manifest/HITL result with a
separate exact per-call authorization and target-resource binding.

The resource observation is then marked stale.

Expected result:

```text
Agent Manifest     VALID
HITL approval      APPROVED
exact call binding VALID (external premise)
predecessor state  STALE

ATC                FAILED
```

This demonstrates the distinction:

```text
valid human approval != valid current-state transition
```

The approval has not become cryptographically invalid. The transition is
rejected because the state assumptions under which the consequential action is
being evaluated are no longer current.
