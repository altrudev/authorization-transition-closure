from reference.verifier import Disposition, TransitionEvidence, verify_transition


BASE = dict(
    authorization_id="auth-1",
    authorized_action_digest="sha256:action",
    executed_action_digest="sha256:action",
    authorized_predecessor_digest="sha256:s0",
    observed_predecessor_digest="sha256:s0",
    expected_successor_digest="sha256:s1",
    observed_successor_digest="sha256:s1",
    policy_digest="sha256:p1",
    execution_policy_digest="sha256:p1",
    execution_succeeded=True,
    replay_detected=False,
    successor_observed=True,
)


def case(**updates):
    data = {**BASE, **updates}
    return TransitionEvidence(**data)


def test_valid_transition_closes():
    result = verify_transition(case())
    assert result.disposition is Disposition.CLOSED


def test_stale_predecessor_fails():
    result = verify_transition(case(observed_predecessor_digest="sha256:s2"))
    assert result.disposition is Disposition.FAILED
    assert "predecessor" in result.reason


def test_action_substitution_fails():
    result = verify_transition(case(executed_action_digest="sha256:other"))
    assert result.disposition is Disposition.FAILED
    assert "action" in result.reason


def test_policy_skew_fails():
    result = verify_transition(case(execution_policy_digest="sha256:p2"))
    assert result.disposition is Disposition.FAILED
    assert "policy" in result.reason


def test_replay_fails():
    result = verify_transition(case(replay_detected=True))
    assert result.disposition is Disposition.FAILED
    assert "replay" in result.reason


def test_missing_successor_is_indeterminate():
    result = verify_transition(
        case(successor_observed=False, observed_successor_digest=None)
    )
    assert result.disposition is Disposition.INDETERMINATE


def test_wrong_successor_fails():
    result = verify_transition(case(observed_successor_digest="sha256:wrong"))
    assert result.disposition is Disposition.FAILED


def test_unknown_replay_status_does_not_close():
    result = verify_transition(case(replay_detected=None))
    assert result.disposition is Disposition.INDETERMINATE


def test_no_expected_successor_is_indeterminate():
    result = verify_transition(case(expected_successor_digest=None))
    assert result.disposition is Disposition.INDETERMINATE
