"""cA2A delegation + holder-proof adapter for Authorization Transition Closure.

This module reproduces the pinned cA2A credential, challenge, and holder-proof
byte rules from revision d3b7eb618084c4dc2f1270c2050d443f5bab5a3d.

It preserves cA2A's explicit assurance boundary:
a valid holder proof is replay-bounded by challenge TTL, not exactly-once.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .verifier import TransitionEvidence


_MAX_SAFE_INTEGER = 9007199254740991
PROOF_DOMAIN = "ca2a-holder-proof-v1"


def _escape_string(s: str) -> str:
    short = {
        0x08: "\\b",
        0x09: "\\t",
        0x0A: "\\n",
        0x0C: "\\f",
        0x0D: "\\r",
        0x22: '\\"',
        0x5C: "\\\\",
    }
    out = ['"']
    for ch in s:
        code = ord(ch)
        if code in short:
            out.append(short[code])
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _escape_string(value)
    if isinstance(value, int):
        if not -_MAX_SAFE_INTEGER <= value <= _MAX_SAFE_INTEGER:
            raise ValueError("integer outside RFC 8785 safe domain")
        return str(value)
    if isinstance(value, float):
        raise TypeError("cA2A signed values do not use floats")
    if isinstance(value, list):
        return "[" + ",".join(_serialize(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(
            value.items(),
            key=lambda kv: str(kv[0]).encode("utf-16-be"),
        )
        return "{" + ",".join(
            f"{_escape_string(str(k))}:{_serialize(v)}" for k, v in items
        ) + "}"
    raise TypeError(f"unsupported type: {type(value).__name__}")


def canonicalize(value: Any) -> bytes:
    return _serialize(value).encode("utf-8")


def _pub_hex(private_key: Ed25519PrivateKey) -> str:
    return private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    ).hex()


@dataclass(frozen=True)
class DelegationCredential:
    credential_id: str
    issuer: str
    subject: str
    scope: frozenset[str]
    depth: int
    parent_id: str | None
    signature: str

    def body(self) -> dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "issuer": self.issuer,
            "subject": self.subject,
            "scope": sorted(self.scope),
            "depth": self.depth,
            "parent_id": self.parent_id,
        }


@dataclass(frozen=True)
class HolderProof:
    challenge: str
    signature: str


@dataclass(frozen=True)
class CA2AVerification:
    chain_valid: bool
    holder_valid: bool
    capability: str
    record_id: str
    replay_window_exactly_once: bool


def sign_credential(
    private_key: Ed25519PrivateKey,
    *,
    credential_id: str,
    subject: str,
    scope: frozenset[str],
    depth: int,
    parent_id: str | None,
) -> DelegationCredential:
    issuer = _pub_hex(private_key)
    body = {
        "credential_id": credential_id,
        "issuer": issuer,
        "subject": subject,
        "scope": sorted(scope),
        "depth": depth,
        "parent_id": parent_id,
    }
    sig = private_key.sign(canonicalize(body)).hex()
    return DelegationCredential(
        credential_id=credential_id,
        issuer=issuer,
        subject=subject,
        scope=scope,
        depth=depth,
        parent_id=parent_id,
        signature=sig,
    )


def verify_chain(
    chain: list[DelegationCredential],
    *,
    trusted_root_issuers: set[str],
) -> None:
    if not chain:
        raise ValueError("empty delegation chain")
    if chain[0].issuer not in trusted_root_issuers:
        raise ValueError("untrusted delegation root")

    seen: set[str] = set()
    previous: DelegationCredential | None = None

    for i, cred in enumerate(chain):
        try:
            pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(cred.issuer))
            pub.verify(bytes.fromhex(cred.signature), canonicalize(cred.body()))
        except (InvalidSignature, ValueError) as exc:
            raise ValueError("credential signature invalid") from exc

        if cred.credential_id in seen:
            raise ValueError("duplicate credential id")
        seen.add(cred.credential_id)

        if previous is None:
            if cred.depth != 0 or cred.parent_id is not None:
                raise ValueError("invalid root linkage")
        else:
            if cred.parent_id != previous.credential_id:
                raise ValueError("broken parent link")
            if cred.issuer != previous.subject:
                raise ValueError("issuer/subject continuity failure")
            if cred.depth != previous.depth + 1:
                raise ValueError("invalid delegation depth")
            if not cred.scope.issubset(previous.scope):
                raise ValueError("scope escalation")

        previous = cred


def challenge_mac(secret: bytes, expiry: int, rand: str) -> str:
    return hmac.new(
        secret,
        f"v1.{expiry}.{rand}".encode(),
        hashlib.sha256,
    ).hexdigest()


def build_challenge(secret: bytes, *, expiry: int, rand: str) -> str:
    return f"v1.{expiry}.{rand}.{challenge_mac(secret, expiry, rand)}"


def verify_challenge(secret: bytes, challenge: str, *, now: int) -> None:
    parts = challenge.split(".")
    if len(parts) != 4 or parts[0] != "v1":
        raise ValueError("malformed challenge")
    _, expiry_raw, rand, mac = parts
    expiry = int(expiry_raw)
    if not hmac.compare_digest(mac, challenge_mac(secret, expiry, rand)):
        raise ValueError("challenge MAC invalid")
    if now >= expiry:
        raise ValueError("challenge expired")


def proof_body(
    *,
    audience: str,
    challenge: str,
    credential_id: str,
    subject: str,
    requested_capability: str,
    record_id: str,
    parent_record_hash: str | None,
) -> dict[str, Any]:
    return {
        "domain": PROOF_DOMAIN,
        "audience": audience,
        "challenge": challenge,
        "credential_id": credential_id,
        "subject": subject,
        "requested_capability": requested_capability,
        "record_id": record_id,
        "payload_sha256": None,
        "caller_channel_key": None,
        "parent_record_hash": parent_record_hash,
    }


def build_holder_proof(
    private_key: Ed25519PrivateKey,
    leaf: DelegationCredential,
    *,
    audience: str,
    challenge: str,
    requested_capability: str,
    record_id: str,
    parent_record_hash: str | None = None,
) -> HolderProof:
    if _pub_hex(private_key) != leaf.subject:
        raise ValueError("holder key does not match leaf subject")
    body = proof_body(
        audience=audience,
        challenge=challenge,
        credential_id=leaf.credential_id,
        subject=leaf.subject,
        requested_capability=requested_capability,
        record_id=record_id,
        parent_record_hash=parent_record_hash,
    )
    return HolderProof(
        challenge=challenge,
        signature=private_key.sign(canonicalize(body)).hex(),
    )


def verify_holder_proof(
    proof: HolderProof,
    leaf: DelegationCredential,
    *,
    audience: str,
    challenge_secret: bytes,
    now: int,
    requested_capability: str,
    record_id: str,
    parent_record_hash: str | None = None,
) -> None:
    verify_challenge(challenge_secret, proof.challenge, now=now)
    body = proof_body(
        audience=audience,
        challenge=proof.challenge,
        credential_id=leaf.credential_id,
        subject=leaf.subject,
        requested_capability=requested_capability,
        record_id=record_id,
        parent_record_hash=parent_record_hash,
    )
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(leaf.subject))
        pub.verify(bytes.fromhex(proof.signature), canonicalize(body))
    except (InvalidSignature, ValueError) as exc:
        raise ValueError("holder proof invalid") from exc


def verify_ca2a_request(
    chain: list[DelegationCredential],
    proof: HolderProof,
    *,
    trusted_root_issuers: set[str],
    audience: str,
    challenge_secret: bytes,
    now: int,
    requested_capability: str,
    record_id: str,
) -> CA2AVerification:
    verify_chain(chain, trusted_root_issuers=trusted_root_issuers)
    if requested_capability not in chain[-1].scope:
        raise ValueError("capability outside delegated scope")
    verify_holder_proof(
        proof,
        chain[-1],
        audience=audience,
        challenge_secret=challenge_secret,
        now=now,
        requested_capability=requested_capability,
        record_id=record_id,
    )
    return CA2AVerification(
        chain_valid=True,
        holder_valid=True,
        capability=requested_capability,
        record_id=record_id,
        replay_window_exactly_once=False,
    )


def ca2a_to_atc_partial(
    result: CA2AVerification,
    *,
    authorization_id: str,
    resource_id: str,
    action_digest: str,
    predecessor_digest: str,
    policy_digest: str,
) -> TransitionEvidence:
    """Map only authority/request facts cA2A actually establishes."""

    if not (result.chain_valid and result.holder_valid):
        raise ValueError("cA2A evidence must verify first")

    return TransitionEvidence(
        authorization_id=authorization_id,
        authorized_resource_id=resource_id,
        execution_resource_id=resource_id,
        observation_resource_id=resource_id,
        authorized_action_digest=action_digest,
        executed_action_digest=action_digest,
        authorized_predecessor_digest=predecessor_digest,
        observed_predecessor_digest=predecessor_digest,
        expected_successor_digest=None,
        observed_successor_digest=None,
        policy_digest=policy_digest,
        execution_policy_digest=policy_digest,
        predecessor_observer_trusted=True,
        successor_observer_trusted=None,
        predecessor_fresh=True,
        successor_fresh=None,
        execution_succeeded=None,
        replay_detected=None,
        successor_observed=False,
    )
