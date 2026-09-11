import json
from dataclasses import replace
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from reference.agent_manifest_adapter import verify_agent_manifest_hitl_vector
from reference.ca2a_adapter import (
    build_challenge,
    build_holder_proof,
    sign_credential,
    verify_ca2a_request,
)
from reference.composition import StateObservation, compose_upstream_evidence
from reference.trace_adapter import verify_trace_action_receipt_fixture
from reference.verifier import Disposition, verify_transition


ROOT = Path(__file__).resolve().parents[1]
TRACE_FIXTURE = ROOT / "fixtures" / "trace" / "01-valid-controller-accepted.json"
AM_FIXTURE = ROOT / "fixtures" / "agent-manifest" / "AM-VEC-009.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def valid_ca2a():
    root_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    leaf_key = Ed25519PrivateKey.from_private_bytes(bytes(reversed(range(32))))
    leaf_pub = leaf_key.public_key().public_bytes_raw().hex()

    cred = sign_credential(
        root_key,
        credential_id="cred-0",
        subject=leaf_pub,
        scope=frozenset({"write"}),
        depth=0,
        parent_id=None,
    )
    secret = b"composition-secret-material-32-by"[:32]
    now = 2_000_000_000
    challenge = build_challenge(
        secret,
        expiry=now + 60,
        rand="33" * 16,
    )
    proof = build_holder_proof(
        leaf_key,
        cred,
        audience="composition-callee",
        challenge=challenge,
        requested_capability="write",
        record_id="r-compose",
    )
    result = verify_ca2a_request(
        [cred],
        proof,
        trusted_root_issuers={cred.issuer},
        audience="composition-callee",
        challenge_secret=secret,
        now=now,
        requested_capability="write",
        record_id="r-compose",
    )
    return result


def upstream_bundle():
    trace_fixture = load_json(TRACE_FIXTURE)
    trace_result = verify_trace_action_receipt_fixture(trace_fixture)
    manifest_vector = load_json(AM_FIXTURE)
    manifest_result = verify_agent_manifest_hitl_vector(manifest_vector)
    ca2a_result = valid_ca2a()

    assert trace_result.valid is True
    assert manifest_result.valid is True
    assert manifest_result.hitl_result == "APPROVED"
    assert ca2a_result.chain_valid is True
    assert ca2a_result.holder_valid is True

    return trace_fixture, trace_result, manifest_vector, manifest_result, ca2a_result


def base_state():
    return StateObservation(
        resource_id="robot:cell-a:arm-2",
        predecessor_digest="sha256:" + "9" * 64,
        predecessor_trusted=True,
        predecessor_fresh=True,
    )


def compose(**overrides):
    trace_fixture, trace_result, manifest_vector, manifest_result, ca2a_result = upstream_bundle()
    kwargs = dict(
        trace_fixture=trace_fixture,
        trace_result=trace_result,
        manifest_vector=manifest_vector,
        manifest_result=manifest_result,
        ca2a_result=ca2a_result,
        state=base_state(),
        ca2a_action_digest=trace_fixture["action"]["action_ref"],
        execution_succeeded=None,
        replay_detected=None,
        expected_successor_digest=None,
    )
    kwargs.update(overrides)
    return compose_upstream_evidence(**kwargs)


def test_all_three_upstream_layers_valid_but_no_execution_is_indeterminate():
    result = verify_transition(compose())

    assert result.disposition is Disposition.INDETERMINATE
    assert "execution outcome is unavailable" in result.reason


def test_success_plus_matching_successor_still_indeterminate_when_replay_unknown():
    successor = "sha256:" + "a" * 64
    evidence = compose(
        state=replace(
            base_state(),
            successor_digest=successor,
            successor_trusted=True,
            successor_fresh=True,
        ),
        execution_succeeded=True,
        expected_successor_digest=successor,
        replay_detected=None,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert "replay status" in result.reason


def test_exactly_once_known_but_no_successor_is_indeterminate():
    evidence = compose(
        execution_succeeded=True,
        replay_detected=False,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert "successor state" in result.reason


def test_successor_present_but_no_transition_predicate_is_indeterminate():
    successor = "sha256:" + "b" * 64
    evidence = compose(
        state=replace(
            base_state(),
            successor_digest=successor,
            successor_trusted=True,
            successor_fresh=True,
        ),
        execution_succeeded=True,
        replay_detected=False,
        expected_successor_digest=None,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.INDETERMINATE
    assert "no exact successor predicate" in result.reason


def test_wrong_successor_fails_even_when_all_upstream_layers_are_valid():
    evidence = compose(
        state=replace(
            base_state(),
            successor_digest="sha256:" + "c" * 64,
            successor_trusted=True,
            successor_fresh=True,
        ),
        execution_succeeded=True,
        replay_detected=False,
        expected_successor_digest="sha256:" + "d" * 64,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.FAILED
    assert "successor" in result.reason


def test_full_composition_closes_only_with_complete_state_and_replay_evidence():
    successor = "sha256:" + "e" * 64
    evidence = compose(
        state=replace(
            base_state(),
            successor_digest=successor,
            successor_trusted=True,
            successor_fresh=True,
        ),
        execution_succeeded=True,
        replay_detected=False,
        expected_successor_digest=successor,
    )
    result = verify_transition(evidence)

    assert result.disposition is Disposition.CLOSED


def test_cross_system_action_mismatch_is_rejected_before_atc():
    trace_fixture, trace_result, manifest_vector, manifest_result, ca2a_result = upstream_bundle()

    try:
        compose_upstream_evidence(
            trace_fixture=trace_fixture,
            trace_result=trace_result,
            manifest_vector=manifest_vector,
            manifest_result=manifest_result,
            ca2a_result=ca2a_result,
            state=base_state(),
            ca2a_action_digest="sha256:" + "f" * 64,
            execution_succeeded=None,
            replay_detected=None,
            expected_successor_digest=None,
        )
    except ValueError as exc:
        assert "disagree" in str(exc)
    else:
        raise AssertionError("cross-system action mismatch was accepted")
