from dataclasses import replace
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from reference.ca2a_adapter import (
    build_challenge,
    build_holder_proof,
    ca2a_to_atc_partial,
    sign_credential,
    verify_ca2a_request,
    verify_holder_proof,
)
from reference.verifier import Disposition, verify_transition


ROOT_SEED = bytes(range(32))
LEAF_SEED = bytes(reversed(range(32)))
SECRET = b"atc-ca2a-test-secret-material-32b"[:32]
AUDIENCE = "test-callee-channel-key"
NOW = 2_000_000_000
EXPIRY = NOW + 60
RAND = "22" * 16


def deterministic_request():
    root_key = Ed25519PrivateKey.from_private_bytes(ROOT_SEED)
    leaf_key = Ed25519PrivateKey.from_private_bytes(LEAF_SEED)
    leaf_pub = leaf_key.public_key().public_bytes_raw().hex()

    cred = sign_credential(
        root_key,
        credential_id="cred-0",
        subject=leaf_pub,
        scope=frozenset({"read", "write"}),
        depth=0,
        parent_id=None,
    )
    challenge = build_challenge(SECRET, expiry=EXPIRY, rand=RAND)
    proof = build_holder_proof(
        leaf_key,
        cred,
        audience=AUDIENCE,
        challenge=challenge,
        requested_capability="write",
        record_id="r0",
    )
    return [cred], proof


def test_ca2a_chain_and_holder_proof_verify() -> None:
    chain, proof = deterministic_request()
    result = verify_ca2a_request(
        chain,
        proof,
        trusted_root_issuers={chain[0].issuer},
        audience=AUDIENCE,
        challenge_secret=SECRET,
        now=NOW,
        requested_capability="write",
        record_id="r0",
    )
    assert result.chain_valid is True
    assert result.holder_valid is True
    assert result.replay_window_exactly_once is False


def test_same_holder_proof_verifies_twice_inside_window() -> None:
    chain, proof = deterministic_request()

    verify_holder_proof(
        proof,
        chain[-1],
        audience=AUDIENCE,
        challenge_secret=SECRET,
        now=NOW,
        requested_capability="write",
        record_id="r0",
    )
    verify_holder_proof(
        proof,
        chain[-1],
        audience=AUDIENCE,
        challenge_secret=SECRET,
        now=NOW + 1,
        requested_capability="write",
        record_id="r0",
    )


def test_holder_proof_expires_at_boundary() -> None:
    chain, proof = deterministic_request()
    try:
        verify_holder_proof(
            proof,
            chain[-1],
            audience=AUDIENCE,
            challenge_secret=SECRET,
            now=EXPIRY,
            requested_capability="write",
            record_id="r0",
        )
    except ValueError as exc:
        assert "expired" in str(exc)
    else:
        raise AssertionError("expired holder proof unexpectedly verified")


def test_holder_proof_is_bound_to_capability() -> None:
    chain, proof = deterministic_request()
    try:
        verify_holder_proof(
            proof,
            chain[-1],
            audience=AUDIENCE,
            challenge_secret=SECRET,
            now=NOW,
            requested_capability="read",
            record_id="r0",
        )
    except ValueError as exc:
        assert "holder proof invalid" in str(exc)
    else:
        raise AssertionError("proof transferred across capability")


def test_valid_ca2a_authority_does_not_establish_exactly_once_transition() -> None:
    chain, proof = deterministic_request()
    ca2a = verify_ca2a_request(
        chain,
        proof,
        trusted_root_issuers={chain[0].issuer},
        audience=AUDIENCE,
        challenge_secret=SECRET,
        now=NOW,
        requested_capability="write",
        record_id="r0",
    )

    evidence = ca2a_to_atc_partial(
        ca2a,
        authorization_id="ca2a:cred-0:r0",
        resource_id="resource:example",
        action_digest="sha256:" + "5" * 64,
        predecessor_digest="sha256:" + "6" * 64,
        policy_digest="sha256:" + "7" * 64,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert evidence.replay_detected is None


def test_replay_uncertainty_survives_success_and_successor_evidence() -> None:
    chain, proof = deterministic_request()
    ca2a = verify_ca2a_request(
        chain,
        proof,
        trusted_root_issuers={chain[0].issuer},
        audience=AUDIENCE,
        challenge_secret=SECRET,
        now=NOW,
        requested_capability="write",
        record_id="r0",
    )

    evidence = ca2a_to_atc_partial(
        ca2a,
        authorization_id="ca2a:cred-0:r0",
        resource_id="resource:example",
        action_digest="sha256:" + "5" * 64,
        predecessor_digest="sha256:" + "6" * 64,
        policy_digest="sha256:" + "7" * 64,
    )

    result = verify_transition(
        replace(
            evidence,
            execution_succeeded=True,
            successor_observed=True,
            observed_successor_digest="sha256:" + "8" * 64,
            expected_successor_digest="sha256:" + "8" * 64,
            successor_observer_trusted=True,
            successor_fresh=True,
        )
    )
    assert result.disposition is Disposition.INDETERMINATE
    assert "replay status" in result.reason
