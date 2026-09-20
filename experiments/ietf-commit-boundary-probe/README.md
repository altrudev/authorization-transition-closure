# IETF Commit-Boundary Probe v0.4

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
- T8: the guard is decomposed into its actual prerequisite reads and final write. An external prerequisite changes after the reads but before the write, and the stale read-time verdict still commits.
- T9: T7b is replayed with an authoritative monotonic ordering witness for the final read, revocation, and commit. With `read_seq < revoke_seq < commit_seq`, the relying party can cleanly reject instead of treating the case as undecidable.

T7b demonstrates the modeled distinction: `fresh observation != commit-time guarantee`.

T8 shows that the same distinction can reappear *inside* an application guard when the prerequisite authorities and effecting boundary are not atomic.

T9 demonstrates a narrower positive result: an authoritative ordering relation can make a specific read/revocation/commit sequence decidable without synchronized wall-clock time. It does **not** by itself solve how that ordering relation is established across independent authorities.

## Independent relying-party review

T8 and the T9 ordering-witness trace were proposed and independently exercised by **Thorsten** during a relying-party review in September 2026, then incorporated here with his permission. His review also reproduced the pinned base traces before adding these cases.

The base probe remains unchanged so its original hash and T1-T7b reproduction remain independently checkable. The new cases live in `probe_extension.py`.

The review exposed two separate properties:

- moving a check closer to execution only helps while the state behind that check remains stable; and
- a relying party needs evidence of relative event order, not merely evidence that each event existed.

## Scope

This probe does **not** by itself establish a standards gap or claim that OAuth RAR, RFC 9110 conditional requests, WebDAV, Transaction Tokens, EMILIA/AEB, SCITT, or another specification is defective.

The remaining interoperability question is whether an existing or composable mechanism both:

1. conveys a conjunction of independently versioned execution preconditions to the effecting boundary; and
2. provides an authoritative ordering relation strong enough for a relying party to determine whether any relevant prerequisite changed between the final accepted read and the consequential commit.

T9 deliberately leaves the distributed case open: producing one trustworthy total order across independent authorities may itself require coordination or another trust assumption.

## Run

Base matrix:

```bash
python3 ietf_commit_boundary_probe.py > results.json
sha256sum ietf_commit_boundary_probe.py
```

Relying-party extension:

```bash
python3 probe_extension.py > extension-results.json
```

Both scripts contain assertions for their scenarios and exit non-zero if an expected outcome changes.
