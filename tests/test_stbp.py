import copy

import pytest

from reference.stbp import ProfileError, verify_stbp_v01
from reference.verifier import Disposition


D = lambda ch: "sha256:" + ch * 64

BASE = {
    "profile": "atc.stbp.v0.1",
    "transition_id": "tx-001",
    "resource": {
        "resource_id": "acct:17",
        "representation": "database-row-canonical-json",
    },
    "authorization": {
        "authorization_id": "auth-001",
        "action_digest": D("a"),
        "predecessor_digest": D("b"),
        "policy_digest": D("c"),
        "evidence_ref": "trace:receipt:1",
    },
    "execution": {
        "action_digest": D("a"),
        "policy_digest": D("c"),
        "succeeded": True,
        "evidence_ref": "dsr:result:1",
    },
    "predecessor": {
        "state_digest": D("b"),
        "observer_id": "observer:db-primary",
        "observed_at": "2026-09-11T20:00:00Z",
        "trusted": True,
        "fresh": True,
        "evidence_ref": "observer:receipt:s0",
    },
    "successor": {
        "state_digest": D("d"),
        "observer_id": "observer:db-primary",
        "observed_at": "2026-09-11T20:00:01Z",
        "trusted": True,
        "fresh": True,
        "evidence_ref": "observer:receipt:s1",
    },
    "replay": {
        "status": "not-replayed",
        "evidence_ref": "nonce-store:receipt:1",
    },
    "predicate": {
        "type": "exact-successor-digest",
        "expected_successor_digest": D("d"),
    },
}


def doc():
    return copy.deepcopy(BASE)


def test_complete_profile_closes():
    result = verify_stbp_v01(doc())
    assert result.verification.disposition is Disposition.CLOSED


def test_replay_fails():
    x = doc()
    x["replay"]["status"] = "replayed"
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.FAILED


def test_unknown_replay_is_indeterminate():
    x = doc()
    x["replay"]["status"] = "unknown"
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.INDETERMINATE


def test_stale_predecessor_fails():
    x = doc()
    x["predecessor"]["fresh"] = False
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.FAILED


def test_unknown_successor_trust_is_indeterminate():
    x = doc()
    x["successor"]["trusted"] = None
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.INDETERMINATE


def test_wrong_successor_fails():
    x = doc()
    x["successor"]["state_digest"] = D("e")
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.FAILED


def test_action_mismatch_fails():
    x = doc()
    x["execution"]["action_digest"] = D("e")
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.FAILED


def test_policy_mismatch_fails():
    x = doc()
    x["execution"]["policy_digest"] = D("e")
    result = verify_stbp_v01(x)
    assert result.verification.disposition is Disposition.FAILED


def test_unknown_top_level_field_is_rejected():
    x = doc()
    x["future_field"] = 1
    with pytest.raises(ProfileError, match="unknown fields"):
        verify_stbp_v01(x)


def test_malformed_digest_is_rejected():
    x = doc()
    x["authorization"]["action_digest"] = "sha256:not-valid"
    with pytest.raises(ProfileError, match="canonical sha256"):
        verify_stbp_v01(x)


def test_unknown_predicate_type_is_rejected():
    x = doc()
    x["predicate"]["type"] = "semantic-magic"
    with pytest.raises(ProfileError, match="unsupported predicate"):
        verify_stbp_v01(x)


def test_missing_required_field_is_rejected():
    x = doc()
    del x["resource"]["representation"]
    with pytest.raises(ProfileError, match="missing required"):
        verify_stbp_v01(x)
