import json
from pathlib import Path

import pytest

from reference.verifier import Disposition, TransitionEvidence, verify_transition


VECTOR_DIR = Path(__file__).resolve().parents[1] / "vectors"
VECTOR_FILES = sorted(VECTOR_DIR.glob("[0-9][0-9]-*.json"))


def load_vector(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", VECTOR_FILES, ids=lambda p: p.stem)
def test_conformance_vector(path: Path) -> None:
    vector = load_vector(path)
    evidence = TransitionEvidence(**vector["evidence"])
    result = verify_transition(evidence)

    assert result.disposition is Disposition(vector["expected"]["disposition"])
    assert vector["expected"]["reason_contains"] in result.reason


def test_vector_ids_are_unique() -> None:
    ids = [load_vector(path)["id"] for path in VECTOR_FILES]
    assert len(ids) == len(set(ids))


def test_vector_corpus_contains_all_three_dispositions() -> None:
    dispositions = {
        load_vector(path)["expected"]["disposition"] for path in VECTOR_FILES
    }
    assert dispositions == {"CLOSED", "FAILED", "INDETERMINATE"}


def test_vectors_state_upstream_assumptions_explicitly() -> None:
    for path in VECTOR_FILES:
        assumptions = load_vector(path).get("source_assumptions")
        assert isinstance(assumptions, list) and assumptions
        assert all(isinstance(item, str) and item for item in assumptions)
