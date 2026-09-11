# TRACE Action-Receipt Adapter

This adapter is the first empirical ATC integration.

It pins the upstream TRACE fixture:

- repository: `agentrust-io/trace-spec`
- revision: `10fcba46c8a08010c205952bf4d197a25b4dc80e`
- path: `examples/action-receipts/conformance/01-valid-controller-accepted.json`
- source blob: `853b029d2d4a97e06f82bcaf315c46d51e03c53c`

The fixture contains a real Ed25519 test signature and trusted public JWK.

## What the adapter verifies

The adapter independently verifies the same core properties used by TRACE's
informative conformance fixture:

- action reference recomputation;
- receipt-to-action binding;
- call and session binding;
- detached evidence hash;
- receipt-chain predecessor;
- freshness and future-time rejection;
- decision vocabulary;
- physical-completion claim boundary;
- pinned Ed25519 issuer key and signature.

## What it maps into ATC

A valid accepted receipt contributes:

- exact action digest;
- controller acceptance of that bound action;
- call/session-bound evidence validity.

It does **not** map controller acceptance to:

- successful execution;
- physical completion;
- observed successor state;
- exactly-once execution.

Therefore the first real TRACE→ATC experiment is expected to remain
`INDETERMINATE`.

That is the point of this adapter: preserve the upstream assurance ceiling
instead of silently upgrading "accepted" into "completed".
