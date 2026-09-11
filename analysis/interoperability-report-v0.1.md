# STBP v0.1 Interoperability Report

Status: **Experimental evidence report**

This report records how the current empirical adapters map TRACE, Agent
Manifest, and cA2A evidence into STBP v0.1, and which closure facts still require
an independent source.

## 1. Evidence sources tested

| System | Pinned revision / artifact | Empirical result |
|---|---|---|
| TRACE | action-receipt conformance fixture at `10fcba46c8a08010c205952bf4d197a25b4dc80e` | real Ed25519 receipt verifies; accepted action does not establish physical completion |
| Agent Manifest | `AM-VEC-009` at `3525644331fc5d7a7d9055a875bd5c81f31fc492` | manifest and HITL approval verify; approval does not generically create per-call resource-state binding |
| cA2A | holder/delegation implementation at `d3b7eb618084c4dc2f1270c2050d443f5bab5a3d` | delegation and holder proof verify; same proof remains usable inside challenge window |
| ATC/STBP | local composition/reference verifier | `CLOSED` only after independent S0/S1 + execution + replay + predicate evidence is present |

## 2. Field coverage matrix

Legend:

- **DIRECT** — inspected upstream evidence can directly establish the STBP field or its underlying fact.
- **COMPOSABLE** — upstream evidence contributes, but another layer must supply the final STBP binding.
- **EXTERNAL** — current inspected upstream systems do not generically establish the field.
- **POLICY** — relying-party/domain policy decision rather than a fact inferred from the upstream artifact.

| STBP field | TRACE | Agent Manifest | cA2A | Independent source still needed? |
|---|---|---|---|---|
| `resource.resource_id` | COMPOSABLE | COMPOSABLE | COMPOSABLE | Yes, unless application profile binds resource identity |
| `resource.representation` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes** |
| `authorization.authorization_id` | COMPOSABLE | DIRECT for manifest/HITL identity | COMPOSABLE | Often composition-specific |
| `authorization.action_digest` | DIRECT for bound action receipt | Not generic per-call binding | DIRECT/COMPOSABLE for exact request fields | Cross-system action-equivalence rule |
| `authorization.predecessor_digest` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes** |
| `authorization.policy_digest` | DIRECT/COMPOSABLE | DIRECT policy-bundle identity | COMPOSABLE through effective policy decision | May require profile normalization |
| `execution.action_digest` | DIRECT/COMPOSABLE | COMPOSABLE | COMPOSABLE | Execution adapter |
| `execution.policy_digest` | DIRECT/COMPOSABLE | DIRECT configuration identity | COMPOSABLE | Execution adapter |
| `execution.succeeded` | Receipt acceptance is not completion | Not generic execution consequence | Authorization decision is not execution success | **Yes, execution evidence** |
| `predecessor.state_digest` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes** |
| `predecessor.observer_id` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes** |
| `predecessor.trusted` | POLICY | POLICY | POLICY | **Yes, relying-party policy** |
| `predecessor.fresh` | EXTERNAL/POLICY | EXTERNAL/POLICY | EXTERNAL/POLICY | **Yes** |
| `successor.state_digest` | Explicitly not established by tested receipt | EXTERNAL | EXTERNAL | **Yes** |
| `successor.observer_id` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes** |
| `successor.trusted` | POLICY | POLICY | POLICY | **Yes, relying-party policy** |
| `successor.fresh` | EXTERNAL/POLICY | EXTERNAL/POLICY | EXTERNAL/POLICY | **Yes** |
| `replay.status` | Partial freshness/chain evidence | Verification freshness != exactly-once action | bounded replay window, not exactly-once | **Yes for not-replayed** |
| `predicate.expected_successor_digest` | EXTERNAL | EXTERNAL | EXTERNAL | **Yes, domain authorization/policy** |

## 3. What the composition experiment proves

The current executable composition establishes:

```text
TRACE valid
+ Agent Manifest valid / HITL approved
+ cA2A valid
!= CLOSED
```

The result remains `INDETERMINATE` until the evidence package additionally
establishes:

1. exact target resource and representation;
2. authorized predecessor S0;
3. trusted/fresh observed S0;
4. actual execution outcome;
5. transition uniqueness / non-replay;
6. trusted/fresh observed S1;
7. an explicit predicate for acceptable S1.

When those facts are supplied and agree, the same verifier returns `CLOSED`.

## 4. Negative interoperability findings

### TRACE

The tested action receipt is correctly treated as evidence that a trusted
controller accepted a bound action. It is not translated into
`execution.succeeded=true` or into successor-state evidence.

### Agent Manifest

The tested HITL approval remains `VALID / APPROVED` even when ATC rejects a
stale predecessor. This demonstrates that approval validity and transition
validity are separate questions.

### cA2A

The tested holder proof verifies twice inside its challenge window. Therefore
the adapter must not map that condition to `replay.status=not-replayed`.

## 5. Minimal unresolved interoperability layer

The remaining portable gap is narrow:

```text
resource identity + representation
S0 observation
S1 observation
execution outcome
replay/uniqueness evidence
transition predicate
```

STBP v0.1 carries these facts without requiring TRACE, Agent Manifest, or cA2A
to become general-purpose application-state stores.

## 6. Evidence ceiling

This report does not claim:

- that STBP proves observer truth;
- that every TRACE profile lacks successor semantics;
- that every Agent Manifest integration lacks per-call state binding;
- that cA2A cannot be deployed with an external exactly-once store;
- that STBP is ready for standardization.

It claims only what the pinned, executable experiments establish.

## 7. Review question

The technical review question is now:

> Is there already a normative, portable mechanism in the inspected ecosystem
> that binds authorization to S0 and execution to trusted S1 with explicit
> replay semantics and a transition predicate?

If yes, STBP should narrow or disappear.

If no, STBP v0.1 is a candidate minimal composition profile for that missing
join.
