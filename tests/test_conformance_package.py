import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "conformance" / "source-mapping-v0.1.json"

def load_mapping() -> dict:
    return json.loads(MAPPING.read_text(encoding="utf-8"))

def test_interop_mapping_profile_and_sources_are_pinned() -> None:
    data = load_mapping()
    assert data["profile"] == "atc.stbp.interop-map.v0.1"
    systems = {item["system"] for item in data["upstream"]}
    assert systems == {"TRACE", "Agent Manifest", "cA2A"}
    for item in data["upstream"]:
        assert item["pinned_revision"]
        assert item["artifact"]
        assert item["supplies"]

def test_no_upstream_source_claims_generic_successor_state() -> None:
    data = load_mapping()
    for item in data["upstream"]:
        successor_entries = [
            entry for entry in item["supplies"]
            if entry["field"] == "successor.state_digest"
        ]
        assert successor_entries
        assert all(entry["coverage"] == "not-established" for entry in successor_entries)

def test_no_upstream_source_claims_execution_success_without_evidence() -> None:
    data = load_mapping()
    entries = [
        entry
        for item in data["upstream"]
        for entry in item["supplies"]
        if entry["field"] == "execution.succeeded"
    ]
    assert entries
    assert all(entry["coverage"] == "not-established" for entry in entries)

def test_replay_not_replayed_remains_external_requirement() -> None:
    data = load_mapping()
    assert "replay.status:not-replayed" in data["external_required"]

def test_state_and_predicate_gap_is_explicit() -> None:
    data = load_mapping()
    required = set(data["external_required"])
    assert {
        "authorization.predecessor_digest",
        "predecessor.state_digest",
        "successor.state_digest",
        "predicate.expected_successor_digest",
    } <= required
