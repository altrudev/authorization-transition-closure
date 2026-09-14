from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class Resource:
    version: int
    value: int = 0

@dataclass(frozen=True)
class Approval:
    target_version: int
    external_versions: Dict[str, int]
    action: str = "increment"
    amount: int = 1

class World:
    def __init__(self) -> None:
        self.resources = {
            "target": Resource(7, 0),
            "budget": Resource(12, 100),
            "compliance": Resource(4, 1),
        }

    def snapshot(self) -> Dict[str, int]:
        return {name: r.version for name, r in self.resources.items()}

    def mutate_version(self, name: str) -> None:
        self.resources[name].version += 1

    def revoke_compliance(self) -> None:
        self.resources["compliance"].version += 1
        self.resources["compliance"].value = 0

    def execute_if_match_only(self, approval: Approval) -> Tuple[bool, str]:
        if self.resources["target"].version != approval.target_version:
            return False, "target_precondition_failed"
        self.resources["target"].value += approval.amount
        self.resources["target"].version += 1
        return True, "committed"

    def execute_full_guarded(self, approval: Approval) -> Tuple[bool, str]:
        if self.resources["target"].version != approval.target_version:
            return False, "target_precondition_failed"
        for name, expected in approval.external_versions.items():
            if self.resources[name].version != expected:
                return False, f"{name}_version_precondition_failed"
        if self.resources["compliance"].value != 1:
            return False, "compliance_predicate_failed"
        self.resources["target"].value += approval.amount
        self.resources["target"].version += 1
        return True, "committed"

    def final_read_then_commit(self, approval: Approval, *, revoke_after_final_read: bool) -> Dict[str, object]:
        target_ok = self.resources["target"].version == approval.target_version
        external_ok = all(
            self.resources[name].version == expected
            for name, expected in approval.external_versions.items()
        )
        compliance_ok = self.resources["compliance"].value == 1
        if not (target_ok and external_ok and compliance_ok):
            return {
                "final_read_passed": False,
                "commit": (False, "final_read_failed"),
                "effect": self.resources["target"].value,
            }
        if revoke_after_final_read:
            self.revoke_compliance()
        result = self.execute_if_match_only(approval)
        return {
            "final_read_passed": True,
            "compliance_version_still_matches_at_commit":
                self.resources["compliance"].version == approval.external_versions["compliance"],
            "compliance_approved_at_commit": self.resources["compliance"].value == 1,
            "commit": result,
            "effect": self.resources["target"].value,
        }

def authorize(world: World) -> Approval:
    s = world.snapshot()
    return Approval(
        target_version=s["target"],
        external_versions={"budget": s["budget"], "compliance": s["compliance"]},
    )

def verifier_passes(world: World, approval: Approval) -> bool:
    return (
        world.resources["target"].version == approval.target_version
        and all(
            world.resources[name].version == expected
            for name, expected in approval.external_versions.items()
        )
        and world.resources["compliance"].value == 1
    )

def run_matrix() -> Dict[str, object]:
    out: Dict[str, object] = {}

    w = World(); a = authorize(w)
    out["T1_control"] = {"verifier": verifier_passes(w, a), "result": w.execute_if_match_only(a), "effect": w.resources["target"].value}

    w = World(); a = authorize(w); assert verifier_passes(w, a); w.mutate_version("target")
    out["T2_target_race_if_match"] = {"result": w.execute_if_match_only(a), "effect": w.resources["target"].value}

    w = World(); a = authorize(w); assert verifier_passes(w, a); w.mutate_version("budget")
    out["T3_external_race_if_match_only"] = {
        "target_version_still_matches": w.resources["target"].version == a.target_version,
        "budget_version_matches": w.resources["budget"].version == a.external_versions["budget"],
        "result": w.execute_if_match_only(a),
        "effect": w.resources["target"].value,
    }

    w = World(); a = authorize(w)
    out["T4a_full_guard_no_race"] = {"result": w.execute_full_guarded(a), "effect": w.resources["target"].value}

    w = World(); a = authorize(w); assert verifier_passes(w, a); w.mutate_version("budget")
    out["T4b_external_race_full_guard"] = {"result": w.execute_full_guarded(a), "effect": w.resources["target"].value}

    w = World(); a = authorize(w); before = verifier_passes(w, a); w.mutate_version("target")
    out["T5_verifier_to_commit_target_race"] = {"verifier_before_race": before, "result": w.execute_if_match_only(a), "effect": w.resources["target"].value}

    w = World(); a = authorize(w); before = verifier_passes(w, a); w.revoke_compliance()
    out["T6_verifier_to_commit_external_race"] = {
        "verifier_before_race": before,
        "target_version_still_matches": w.resources["target"].version == a.target_version,
        "compliance_approved": w.resources["compliance"].value == 1,
        "result_if_match_only": w.execute_if_match_only(a),
        "effect": w.resources["target"].value,
    }

    w = World(); a = authorize(w)
    out["T7a_final_read_no_race"] = w.final_read_then_commit(a, revoke_after_final_read=False)

    w = World(); a = authorize(w)
    out["T7b_revoked_after_final_read"] = w.final_read_then_commit(a, revoke_after_final_read=True)

    return out

def self_test(results: Dict[str, object]) -> None:
    assert results["T1_control"]["result"][0] is True
    assert results["T2_target_race_if_match"]["result"][0] is False
    assert results["T3_external_race_if_match_only"]["target_version_still_matches"] is True
    assert results["T3_external_race_if_match_only"]["budget_version_matches"] is False
    assert results["T3_external_race_if_match_only"]["result"][0] is True
    assert results["T4a_full_guard_no_race"]["result"][0] is True
    assert results["T4a_full_guard_no_race"]["effect"] == 1
    assert results["T4b_external_race_full_guard"]["result"][0] is False
    assert results["T4b_external_race_full_guard"]["effect"] == 0
    assert results["T5_verifier_to_commit_target_race"]["verifier_before_race"] is True
    assert results["T5_verifier_to_commit_target_race"]["result"][0] is False
    assert results["T6_verifier_to_commit_external_race"]["verifier_before_race"] is True
    assert results["T6_verifier_to_commit_external_race"]["target_version_still_matches"] is True
    assert results["T6_verifier_to_commit_external_race"]["compliance_approved"] is False
    assert results["T6_verifier_to_commit_external_race"]["result_if_match_only"][0] is True
    assert results["T7a_final_read_no_race"]["final_read_passed"] is True
    assert results["T7a_final_read_no_race"]["compliance_approved_at_commit"] is True
    assert results["T7a_final_read_no_race"]["commit"][0] is True
    assert results["T7b_revoked_after_final_read"]["final_read_passed"] is True
    assert results["T7b_revoked_after_final_read"]["compliance_version_still_matches_at_commit"] is False
    assert results["T7b_revoked_after_final_read"]["compliance_approved_at_commit"] is False
    assert results["T7b_revoked_after_final_read"]["commit"][0] is True
    assert results["T7b_revoked_after_final_read"]["effect"] == 1

if __name__ == "__main__":
    import json
    results = run_matrix()
    self_test(results)
    print(json.dumps(results, indent=2))
