# STBP v0.1 Technical Review Snapshot

**Status:** Frozen for external technical review  
**Snapshot line:** `stbp-v0.1-review-snapshot`  
**Freeze date:** 2026-09-11  
**Pre-freeze evidence revision:** `5a77440d754b1232da2f8a6b45d2eb72ffae52db`

This snapshot freezes the current ATC/STBP v0.1 research state for review. It is
not a standards release and does not imply specification stability beyond this
review branch.

## Review invariant

The snapshot exists so reviewers can evaluate one fixed artifact while
`main` remains available for later corrections or follow-up work.

The profile should be narrowed, superseded, or retired if an existing normative
mechanism already closes the demonstrated gap.

## Pinned upstream evidence

### TRACE

- repository: `agentrust-io/trace-spec`
- revision: `10fcba46c8a08010c205952bf4d197a25b4dc80e`
- artifact: `examples/action-receipts/conformance/01-valid-controller-accepted.json`
- tested boundary: valid bound action receipt does not establish external
  completion or successor state.

### Agent Manifest

- repository: `agentrust-io/agent-manifest`
- revision: `3525644331fc5d7a7d9055a875bd5c81f31fc492`
- artifact: `python/tests/vectors/AM-VEC-009.json`
- tested boundary: valid manifest/HITL approval does not generically establish
  one per-call target-resource state transition.

### cA2A

- repository: `agentrust-io/ca2a`
- revision: `d3b7eb618084c4dc2f1270c2050d443f5bab5a3d`
- tested boundary: valid holder proof is replay-bounded by the challenge window,
  not exactly-once.

## Key governed DSR evidence

| Purpose | DSR job | Result |
|---|---|---|
| TRACE adapter | `a7c3e91d54b648c2a10f7e3d5b9c2468` | PASS |
| Agent Manifest adapter | `c2f5d8a174b64e3f90a1c7d5e2b84369` | PASS |
| cA2A adapter | `d3a6f9c281b54e70a4c8d1e5f7b29360` | PASS |
| full composition | `e4b7a2c95d1f4630b8e6a9d37c524f18` | PASS |
| STBP parser/schema/conformance | `f5c8b1d47e2a4930a6d9c3e7b12584f0` | PASS |
| interoperability package | `b7e0c4d219f34a68a1d5e7c9832f604b` | PASS |
| real Git transition regression | `d9a1c6e47b2f4058a3e7c9d5216b804f` | PASS, 64 tests |
| standalone real Git transition | `e1b4d7c923f64a50b8e2d5f6a913704c` | PASS |

The final regression job used worker `vps-377a113a-slot2`, DDC radial outcome
`ALLOW`, and Parallax shadow `ALLOW`.

The standalone real-transition job used worker `vps-377a113a`, DDC radial
outcome `ALLOW`, and captured the actual transition evidence in stdout. Its
Parallax shadow result is affected by the separately tracked DDCRE causal-graph
issue #44.

## Real Git transition evidence

Transition id:

`git-transition:8c50fcdcab6dfff485714cdaaf72ac6737b16126e6308b91b40e2d41611456f5`

### Git tree identities

- authorized S0: `00ce80ea220e4fc18efe83a53a5d191b1928a857`
- observed S0: `00ce80ea220e4fc18efe83a53a5d191b1928a857`
- expected S1: `fc5eb13e1c4278453be4574b6edebb87abc51836`
- observed S1: `fc5eb13e1c4278453be4574b6edebb87abc51836`

### STBP commitments

- S0: `sha256:ed35fda7d504e226c202271a82fee13d337617e01a9f0875a22376fe19339d8a`
- action: `sha256:276d44428c69b25b5edce35f689bb7bce2861398fc97c29efdae93b918ad2000`
- policy: `sha256:e7cf6a9b0ecc45047cf779f2af34de0a935b7212310824a5a00a3537cd4d62e5`
- expected S1: `sha256:fdd9f2a8b306561d9d694dbbef3cad6739a5c765494b1783b75ef1a5ca3bf1a2`
- observed S1: `sha256:fdd9f2a8b306561d9d694dbbef3cad6739a5c765494b1783b75ef1a5ca3bf1a2`

### Disposition transition

Before explicit replay evidence:

```text
INDETERMINATE
reason: replay status is unknown
```

After atomic single-use evidence:

```text
CLOSED
reason: resource, authorization, predecessor, execution, policy, successor,
observer trust, freshness, and replay bindings agree
```

The second consumption of the same transition id was rejected.

## Known limitations

1. STBP v0.1 supports only `exact-successor-digest`.
2. Observer trust is supplied by the relying-party model; hashing does not make
   an observer trustworthy.
3. The real Git experiment uses two local workspaces, not separate
   administrative trust domains.
4. The single-use file store is experimental local evidence, not a distributed
   exactly-once service.
5. The cA2A experiment reproduces pinned upstream algorithms with deterministic
   inputs because no committed portable holder-proof vector was found at the
   inspected revision.
6. The worker result signatures were observed in DSR output; this snapshot does
   not claim a separate independent signature-verification pass unless such a
   pass is explicitly added later.
7. DDC Remote Executor issue #44 tracks a Parallax shadow causal-graph ingestion
   defect that can report existing DSR parent artifacts as missing.

## Review entry points

Start with:

1. `docs/research-note-v0.1.md`
2. `docs/adr/0001-state-transition-binding-profile.md`
3. `analysis/interoperability-report-v0.1.md`
4. `spec/state-transition-binding-profile-v0.1.md`
5. `spec/conformance-v0.1.md`
6. `analysis/real-git-transition.md`
7. `REVIEW.md`

## What is frozen

On the review branch, the following are frozen for the duration of the review:

- STBP v0.1 profile semantics;
- JSON schema;
- reference verifier behavior;
- pinned upstream revisions;
- current interoperability claims;
- real Git transition evidence;
- conformance corpus.

Corrections discovered during review should be made on `main` and documented
before creating a replacement review snapshot.
