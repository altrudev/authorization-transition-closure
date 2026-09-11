# Transition Closure Model

## 1. Objective

A transition-closure verifier evaluates whether supplied evidence establishes that an authorized action transformed an accepted predecessor state into an acceptable successor state.

The model uses five primary inputs:

- **S0** — predecessor-state commitment
- **A** — exact authorized action
- **P** — policy and transition constraints
- **E** — execution evidence
- **S1** — successor-state commitment

The verifier evaluates:

```text
VERIFY(S0, A, P, E, S1)
```

and returns `CLOSED`, `FAILED`, or `INDETERMINATE`.

## 2. Required bindings

A closed transition requires evidence for all of the following bindings.

### 2.1 Authorization-to-predecessor binding

The authorization must identify the predecessor state, state version, or equivalent freshness/continuity token against which the action was approved.

Authorization against `S0` does not automatically authorize the same action against a later `S2`.

### 2.2 Authorization-to-action binding

The action actually executed must be the same action authorized, including all parameters that can affect consequence.

Semantic aliases are outside the core model unless a profile defines canonical equivalence.

### 2.3 Execution-to-action binding

Execution evidence must identify the action it reports having executed. A generic "success" event is insufficient.

### 2.4 Execution-to-successor binding

The successor observation must be attributable to the execution under evaluation rather than merely occurring afterward.

### 2.5 Policy-to-transition binding

The policy or constraint set used to judge the transition must be the one bound to the authorization or otherwise explicitly permitted by a version-transition rule.

## 3. Transition predicate

A profile defines a predicate:

```text
acceptable(S0, A, P, S1) -> true | false | unknown
```

Examples:

- balance decreased by exactly the authorized amount;
- object version advanced from v17 to v18;
- Git tree changed only within an allowed path set;
- device state moved within a permitted operating envelope.

The core verifier does not invent domain semantics.

## 4. Dispositions

### CLOSED

Return `CLOSED` only when:

1. every required binding is established;
2. no replay or stale-predecessor condition is present;
3. policy identity/version is acceptable;
4. the successor observation is sufficiently fresh and attributable;
5. the profile transition predicate evaluates true.

### FAILED

Return `FAILED` when trustworthy evidence establishes a contradiction, including:

- wrong predecessor;
- action substitution;
- replay;
- policy mismatch;
- execution failure;
- successor mismatch;
- forbidden collateral change;
- transition predicate false.

### INDETERMINATE

Return `INDETERMINATE` when closure cannot be established because required evidence is absent, unverifiable, stale beyond interpretation, or unable to establish consequence.

## 5. Non-goals

ATC does not:

- authenticate an agent by itself;
- authorize an action by itself;
- execute actions;
- infer missing state;
- treat log presence as proof of consequence;
- treat cryptographic validity as semantic correctness.
