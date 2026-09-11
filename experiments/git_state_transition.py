"""Real Git-state STBP experiment.

This experiment uses actual Git tree objects as the state-bearing resource.
An authorization workspace derives S0 and the expected S1 from an exact patch.
A separate execution workspace starts from the same S0, applies the patch, and
is independently observed with Git plumbing.

The final CLOSED result additionally requires an explicit single-use receipt.
DSR execution itself is not treated as exactly-once evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reference.stbp import verify_stbp_v01
from reference.verifier import Disposition


INITIAL_STATE = """balance=100
status=ready
"""

AUTHORIZED_PATCH = """diff --git a/state.txt b/state.txt
index 980f2c6..485031a 100644
--- a/state.txt
+++ b/state.txt
@@ -1,2 +1,2 @@
-balance=100
+balance=75
 status=ready
"""

POLICY_TEXT = """resource=state.txt
allowed_change=balance:100->75
status_must_remain=ready
"""

RESOURCE_ID = "git:atc-real-transition:state"
REPRESENTATION = "git-tree-object-v1"


def _run(cwd: Path, *argv: str, input_bytes: bytes | None = None) -> str:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(argv)}\n"
            f"stdout={proc.stdout.decode(errors='replace')}\n"
            f"stderr={proc.stderr.decode(errors='replace')}"
        )
    return proc.stdout.decode().strip()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _state_commitment(tree_oid: str) -> str:
    # STBP v0.1 requires SHA-256 digests. The underlying Git object id remains
    # visible in the evidence report; this commitment binds its typed identity.
    return _sha256_bytes(f"git-tree:{tree_oid}".encode())


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run(path, "git", "init", "-q")
    _run(path, "git", "config", "user.name", "ATC Experiment")
    _run(path, "git", "config", "user.email", "atc@example.invalid")
    (path / "state.txt").write_text(INITIAL_STATE, encoding="utf-8")
    _run(path, "git", "add", "state.txt")


def _tree_oid(path: Path) -> str:
    return _run(path, "git", "write-tree")


def _apply_patch(path: Path) -> None:
    _run(path, "git", "apply", "--index", "-", input_bytes=AUTHORIZED_PATCH.encode())


@dataclass(frozen=True)
class SingleUseReceipt:
    transition_id: str
    evidence_ref: str


class FileSingleUseStore:
    """Minimal atomic single-use store scoped to one filesystem."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def consume(self, transition_id: str) -> SingleUseReceipt:
        token = self.root / hashlib.sha256(transition_id.encode()).hexdigest()
        try:
            fd = os.open(token, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError("transition token already consumed") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(transition_id + "\n")
        return SingleUseReceipt(
            transition_id=transition_id,
            evidence_ref="single-use-file:" + token.name,
        )


def build_real_transition() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="atc-git-transition-") as td:
        root = Path(td)
        auth_repo = root / "authorization"
        exec_repo = root / "execution"

        # Authorization phase: establish S0 and exact expected S1.
        _init_repo(auth_repo)
        auth_s0_oid = _tree_oid(auth_repo)
        auth_s0 = _state_commitment(auth_s0_oid)

        action_digest = _sha256_bytes(AUTHORIZED_PATCH.encode())
        policy_digest = _sha256_bytes(POLICY_TEXT.encode())

        _apply_patch(auth_repo)
        expected_s1_oid = _tree_oid(auth_repo)
        expected_s1 = _state_commitment(expected_s1_oid)

        # Execution phase: independent workspace begins from the same bytes.
        _init_repo(exec_repo)
        observed_s0_oid = _tree_oid(exec_repo)
        observed_s0 = _state_commitment(observed_s0_oid)
        if observed_s0 != auth_s0:
            raise RuntimeError("execution workspace does not match authorized S0")

        _apply_patch(exec_repo)
        observed_s1_oid = _tree_oid(exec_repo)
        observed_s1 = _state_commitment(observed_s1_oid)

        transition_id = "git-transition:" + hashlib.sha256(
            (auth_s0 + action_digest + expected_s1).encode()
        ).hexdigest()

        base = {
            "profile": "atc.stbp.v0.1",
            "transition_id": transition_id,
            "resource": {
                "resource_id": RESOURCE_ID,
                "representation": REPRESENTATION,
            },
            "authorization": {
                "authorization_id": "auth:" + transition_id,
                "action_digest": action_digest,
                "predecessor_digest": auth_s0,
                "policy_digest": policy_digest,
                "evidence_ref": "git-authorization-workspace:" + auth_s0_oid,
            },
            "execution": {
                "action_digest": action_digest,
                "policy_digest": policy_digest,
                "succeeded": True,
                "evidence_ref": "git-apply:exit-0",
            },
            "predecessor": {
                "state_digest": observed_s0,
                "observer_id": "observer:git-write-tree:pre",
                "observed_at": "experiment:immediately-before-execution",
                "trusted": True,
                "fresh": True,
                "evidence_ref": "git-tree:" + observed_s0_oid,
            },
            "successor": {
                "state_digest": observed_s1,
                "observer_id": "observer:git-write-tree:post",
                "observed_at": "experiment:immediately-after-execution",
                "trusted": True,
                "fresh": True,
                "evidence_ref": "git-tree:" + observed_s1_oid,
            },
            "replay": {
                "status": "unknown",
                "evidence_ref": "replay:not-yet-established",
            },
            "predicate": {
                "type": "exact-successor-digest",
                "expected_successor_digest": expected_s1,
            },
        }

        before_replay = verify_stbp_v01(base)
        if before_replay.verification.disposition is not Disposition.INDETERMINATE:
            raise RuntimeError("unknown replay status should remain INDETERMINATE")

        store = FileSingleUseStore(root / "single-use")
        receipt = store.consume(transition_id)

        closed_doc = json.loads(json.dumps(base))
        closed_doc["replay"] = {
            "status": "not-replayed",
            "evidence_ref": receipt.evidence_ref,
        }
        closed = verify_stbp_v01(closed_doc)
        if closed.verification.disposition is not Disposition.CLOSED:
            raise RuntimeError(
                "complete real transition did not close: "
                + closed.verification.reason
            )

        second_use_blocked = False
        try:
            store.consume(transition_id)
        except RuntimeError:
            second_use_blocked = True
        if not second_use_blocked:
            raise RuntimeError("single-use store allowed duplicate consumption")

        return {
            "schema": "atc-real-git-transition/1",
            "transition_id": transition_id,
            "resource": RESOURCE_ID,
            "git": {
                "authorized_s0_tree_oid": auth_s0_oid,
                "observed_s0_tree_oid": observed_s0_oid,
                "expected_s1_tree_oid": expected_s1_oid,
                "observed_s1_tree_oid": observed_s1_oid,
            },
            "commitments": {
                "s0": auth_s0,
                "action": action_digest,
                "policy": policy_digest,
                "expected_s1": expected_s1,
                "observed_s1": observed_s1,
            },
            "without_replay_evidence": {
                "disposition": before_replay.verification.disposition.value,
                "reason": before_replay.verification.reason,
            },
            "single_use": {
                "evidence_ref": receipt.evidence_ref,
                "second_use_blocked": second_use_blocked,
            },
            "with_replay_evidence": {
                "disposition": closed.verification.disposition.value,
                "reason": closed.verification.reason,
            },
        }


def main() -> None:
    print(json.dumps(build_real_transition(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
