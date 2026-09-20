"""
Extension traces for the IETF commit-boundary probe.

T8 and T9 were proposed and independently exercised by Thorsten during a
relying-party review in September 2026, then incorporated here with permission.

The base probe remains unchanged so its pinned hash and original T1-T7b
reproduction remain independently verifiable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple
import json

from ietf_commit_boundary_probe import World, authorize


def t8_race_inside_guard() -> Dict[str, object]:
    """
    Split the full guard into its actual prerequisite reads and final write,
    then mutate an external prerequisite after the reads but before the write.

    This exposes a finer-grained boundary that a single-process Python call
    otherwise makes look atomic.
    """
    w = World()
    a = authorize(w)

    target_ok = w.resources["target"].version == a.target_version
    external_ok = all(
        w.resources[name].version == expected
        for name, expected in a.external_versions.items()
    )
    compliance_ok = w.resources["compliance"].value == 1
    all_checks_passed_at_read_time = target_ok and external_ok and compliance_ok

    w.mutate_version("budget")

    if all_checks_passed_at_read_time:
        w.resources["target"].value += a.amount
        w.resources["target"].version += 1
        commit = (True, "committed")
    else:
        commit = (False, "precondition_failed_at_read_time")

    return {
        "all_checks_passed_at_read_time": all_checks_passed_at_read_time,
        "budget_changed_between_check_and_write": True,
        "commit": commit,
        "effect": w.resources["target"].value,
        "note": (
            "The guard's read-time verdict can become stale before its write. "
            "Across independently changing authorities, the T7b boundary can "
            "reappear inside the guard itself."
        ),
    }


@dataclass(frozen=True)
class OrderedApproval:
    target_version: int
    external_versions: Dict[str, int]
    action: str = "increment"
    amount: int = 1


class OrderedWorld(World):
    """World with a monotonic logical ordering witness."""

    def __init__(self) -> None:
        super().__init__()
        self._clock = 0
        self.event_log: list[Tuple[int, str, int]] = []

    def _tick(self, resource: str) -> int:
        self._clock += 1
        version = self.resources[resource].version if resource in self.resources else -1
        self.event_log.append((self._clock, resource, version))
        return self._clock

    def mutate_version(self, name: str) -> int:
        super().mutate_version(name)
        return self._tick(name)

    def revoke_compliance(self) -> int:
        super().revoke_compliance()
        return self._tick("compliance")

    def final_read_with_witness(self, approval: OrderedApproval) -> Tuple[bool, int]:
        ok = (
            self.resources["target"].version == approval.target_version
            and all(
                self.resources[name].version == expected
                for name, expected in approval.external_versions.items()
            )
            and self.resources["compliance"].value == 1
        )
        return ok, self._tick("READ")

    def commit_with_witness(self, approval: OrderedApproval) -> Tuple[bool, str, int]:
        if self.resources["target"].version != approval.target_version:
            return False, "target_precondition_failed", self._clock
        self.resources["target"].value += approval.amount
        self.resources["target"].version += 1
        return True, "committed", self._tick("target")


def t9_receipt_with_ordering_witness() -> Dict[str, object]:
    """
    Replay T7b with a monotonic ordering witness for final read, revocation,
    and commit. The witness makes relative event order decidable without a
    synchronized wall clock.
    """
    w = OrderedWorld()
    a = OrderedApproval(
        target_version=w.resources["target"].version,
        external_versions={
            "budget": w.resources["budget"].version,
            "compliance": w.resources["compliance"].version,
        },
    )

    read_ok, read_seq = w.final_read_with_witness(a)
    revoke_seq = w.revoke_compliance()
    commit_ok, commit_status, commit_seq = w.commit_with_witness(a)

    changed_between = read_seq < revoke_seq < commit_seq
    verdict = "reject" if changed_between else "accept"

    return {
        "final_read_passed": read_ok,
        "read_seq": read_seq,
        "compliance_revoke_seq": revoke_seq,
        "commit": (commit_ok, commit_status),
        "commit_seq": commit_seq,
        "compliance_mutated_between_read_and_commit": changed_between,
        "relying_party_verdict_with_witness": verdict,
        "note": (
            "An authoritative ordering relation distinguishes revocation-before-"
            "commit from revocation-after-commit. The distributed question remains "
            "open: how to establish that order across independent authorities "
            "without silently introducing a new trusted coordinator."
        ),
    }


def self_test(results: Dict[str, object]) -> None:
    t8 = results["T8_race_inside_guard"]
    assert t8["all_checks_passed_at_read_time"] is True
    assert t8["budget_changed_between_check_and_write"] is True
    assert t8["commit"][0] is True
    assert t8["effect"] == 1

    t9 = results["T9_receipt_with_ordering_witness"]
    assert t9["final_read_passed"] is True
    assert t9["read_seq"] == 1
    assert t9["compliance_revoke_seq"] == 2
    assert t9["commit"][0] is True
    assert t9["commit_seq"] == 3
    assert t9["compliance_mutated_between_read_and_commit"] is True
    assert t9["relying_party_verdict_with_witness"] == "reject"


if __name__ == "__main__":
    out = {
        "T8_race_inside_guard": t8_race_inside_guard(),
        "T9_receipt_with_ordering_witness": t9_receipt_with_ordering_witness(),
    }
    self_test(out)
    print(json.dumps(out, indent=2))
