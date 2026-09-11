from experiments.git_state_transition import build_real_transition


def test_real_git_state_transition_closes_only_after_single_use_evidence():
    result = build_real_transition()

    assert result["git"]["authorized_s0_tree_oid"] == result["git"]["observed_s0_tree_oid"]
    assert result["git"]["expected_s1_tree_oid"] == result["git"]["observed_s1_tree_oid"]

    assert result["commitments"]["expected_s1"] == result["commitments"]["observed_s1"]

    assert result["without_replay_evidence"]["disposition"] == "INDETERMINATE"
    assert "replay status" in result["without_replay_evidence"]["reason"]

    assert result["single_use"]["second_use_blocked"] is True
    assert result["with_replay_evidence"]["disposition"] == "CLOSED"
