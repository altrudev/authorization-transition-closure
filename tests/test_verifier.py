from reference.verifier import Disposition, TransitionEvidence, verify_transition


D = lambda ch: "sha256:" + ch * 64

BASE = dict(
    authorization_id="auth-1",
    authorized_resource_id="acct:wallet-a",
    execution_resource_id="acct:wallet-a",
    observation_resource_id="acct:wallet-a",
    authorized_action_digest=D("a"),
    executed_action_digest=D("a"),
    authorized_predecessor_digest=D("b"),
    observed_predecessor_digest=D("b"),
    expected_successor_digest=D("c"),
    observed_successor_digest=D("c"),
    policy_digest=D("d"),
    execution_policy_digest=D("d"),
    predecessor_observer_trusted=True,
    successor_observer_trusted=True,
    predecessor_fresh=True,
    successor_fresh=True,
    execution_succeeded=True,
    replay_detected=False,
    successor_observed=True,
)


def case(**updates):
    return TransitionEvidence(**{**BASE, **updates})


def test_valid_transition_closes():
    assert verify_transition(case()).disposition is Disposition.CLOSED


def test_stale_predecessor_fails():
    result = verify_transition(case(predecessor_fresh=False))
    assert result.disposition is Disposition.FAILED
    assert "stale" in result.reason


def test_predecessor_mismatch_fails():
    result = verify_transition(case(observed_predecessor_digest=D("e")))
    assert result.disposition is Disposition.FAILED
    assert "predecessor" in result.reason


def test_action_substitution_fails():
    result = verify_transition(case(executed_action_digest=D("e")))
    assert result.disposition is Disposition.FAILED
    assert "action" in result.reason


def test_resource_substitution_fails():
    result = verify_transition(case(execution_resource_id="acct:wallet-b"))
    assert result.disposition is Disposition.FAILED
    assert "resources" in result.reason


def test_policy_skew_fails():
    result = verify_transition(case(execution_policy_digest=D("e")))
    assert result.disposition is Disposition.FAILED
    assert "policy" in result.reason


def test_replay_fails():
    result = verify_transition(case(replay_detected=True))
    assert result.disposition is Disposition.FAILED


def test_missing_successor_is_indeterminate():
    result = verify_transition(case(successor_observed=False, observed_successor_digest=None))
    assert result.disposition is Disposition.INDETERMINATE


def test_wrong_successor_fails():
    result = verify_transition(case(observed_successor_digest=D("e")))
    assert result.disposition is Disposition.FAILED


def test_unknown_replay_status_does_not_close():
    result = verify_transition(case(replay_detected=None))
    assert result.disposition is Disposition.INDETERMINATE


def test_unknown_observer_trust_does_not_close():
    result = verify_transition(case(successor_observer_trusted=None))
    assert result.disposition is Disposition.INDETERMINATE


def test_stale_successor_fails():
    result = verify_transition(case(successor_fresh=False))
    assert result.disposition is Disposition.FAILED


def test_no_expected_successor_is_indeterminate():
    result = verify_transition(case(expected_successor_digest=None))
    assert result.disposition is Disposition.INDETERMINATE


def test_malformed_digest_fails():
    result = verify_transition(case(executed_action_digest="sha256:not-a-digest"))
    assert result.disposition is Disposition.FAILED
