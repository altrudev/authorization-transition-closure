# IETF Commit-Boundary Probe v0.3

This deterministic in-memory probe models whether a fresh final read of independently changing prerequisite state establishes a commit-time guarantee.

It does **not** test OAuth, HTTP servers, WebDAV servers, EMILIA/AEB implementations, or real participating providers. It models checks and orderings so candidate mechanisms can be compared against the same traces.

## Key traces

- T1: target-only no-race control commits.
- T2: target changes before commit; target guard refuses with zero effect.
- T3: external budget prerequisite changes while target remains unchanged; target-only guard still commits.
- T4a: full application guard, no race; guarded path commits.
- T4b: same guarded path after external prerequisite changes; it refuses with zero effect. This tests enforcement rather than merely calculating a predicate.
- T5: verifier passes, target changes; mutation-boundary target guard refuses.
- T6: verifier passes, compliance changes from approved to suspended while target stays unchanged; target-only guard still commits.
- T7a: final read passes and nothing changes; commit succeeds.
- T7b: final read passes at compliance v4/approved, compliance changes to v5/suspended, then target mutation commits; target-only commit still succeeds.

T7b demonstrates the modeled distinction: `fresh observation != commit-time guarantee`.

## Scope

This probe does **not** by itself establish a standards gap or claim that OAuth RAR, RFC 9110 conditional requests, WebDAV, Transaction Tokens, EMILIA/AEB, or another specification is defective.

The remaining interoperability question is whether an existing generic mechanism both conveys a conjunction of independently versioned execution preconditions to the effecting boundary and gives them commitment/ordering semantics strong enough to survive post-read revocation across participating authorities.

## Run

```bash
python3 ietf_commit_boundary_probe.py > results.json
sha256sum ietf_commit_boundary_probe.py
```

The script contains assertions for every scenario and exits non-zero if an expected outcome changes.
