# Real Git-State Transition Experiment

Status: executable experiment.

This experiment moves ATC/STBP beyond synthetic S0/S1 digest fixtures.

## Resource

The state-bearing resource is a real temporary Git repository containing:

```text
state.txt
```

Initial content:

```text
balance=100
status=ready
```

The exact authorized patch changes only:

```text
balance=100 -> balance=75
```

and leaves `status=ready`.

## Two-workspace design

The experiment uses two separate Git workspaces.

### Authorization workspace

Git creates the predecessor tree object S0 with `git write-tree`.

The exact patch is hashed as the authorized action.

The policy text is hashed separately.

The patch is applied in the authorization workspace only to derive the exact
expected successor Git tree.

### Execution workspace

A fresh independent Git repository is created from the same initial bytes.

Before execution, Git independently produces its S0 tree object. The experiment
requires it to match the authorized S0.

The exact patch is then applied with:

```text
git apply --index
```

and Git independently produces the observed S1 tree object.

STBP receives SHA-256 commitments over the typed Git tree identities. The raw
Git tree object IDs are retained in the experiment report.

## Replay discipline

The experiment does **not** translate DSR execution into
`replay.status=not-replayed`.

First, the complete state/action/execution package is evaluated with replay
status unknown. The required result is:

```text
INDETERMINATE
```

The experiment then uses an atomic filesystem single-use token store based on
`O_CREAT | O_EXCL`.

The first transition-id consumption succeeds and emits an evidence reference.
A second consumption of the same transition id must fail.

Only after that explicit uniqueness evidence is present does the profile use:

```text
replay.status = not-replayed
```

and the expected result becomes:

```text
CLOSED
```

## Evidence ceiling

This experiment proves a real Git tree transition under the experiment's local
trust model.

It does not claim:

- that Git tree hashing makes the observer independently trustworthy;
- that the observer is in a separate administrative trust domain;
- that DSR itself provides exactly-once semantics;
- that a local file token store is suitable for distributed production use;
- that exact-successor equality is sufficient for every real application.

Its purpose is to establish that the STBP closure model can operate over a real
state-bearing resource rather than only synthetic digest strings.
