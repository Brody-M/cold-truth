from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_event_chain import AuditChainError, ZERO_HASH, append_event, read_events, verify_event_chain
from orchestrator import CaseQueueOrchestrator, OrchestrationError


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "simulated_case" / "queue.json"


class AuditEventChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "event_log.jsonl"
        self.entries: list[dict] = []
        self.head = ZERO_HASH

    def tearDown(self) -> None:
        self.temp.cleanup()

    def append(self, stage: str) -> dict:
        event = append_event(
            self.path,
            {"event_id": f"event-{stage}", "stage": stage, "status": "completed"},
            expected_count=len(self.entries),
            expected_head=self.head,
            expected_entries=self.entries,
        )
        self.entries.append(event)
        self.head = event["event_sha256"]
        return event

    def write_events(self, events: list[dict]) -> None:
        self.path.write_text(
            "".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n" for event in events),
            encoding="utf-8",
        )

    def test_sequential_append_and_full_verification(self) -> None:
        self.append("one")
        self.append("two")
        self.append("three")
        verified = verify_event_chain(
            self.path,
            expected_count=3,
            expected_head=self.head,
            expected_entries=self.entries,
        )
        self.assertEqual(verified["event_count"], 3)
        self.assertEqual([event["sequence"] for event in verified["events"]], [1, 2, 3])

    def test_modified_middle_event_is_detected(self) -> None:
        self.append("one")
        self.append("two")
        self.append("three")
        events = read_events(self.path)
        events[1]["status"] = "tampered"
        self.write_events(events)
        with self.assertRaisesRegex(AuditChainError, "invalid event hash"):
            verify_event_chain(self.path)

    def test_truncation_is_detected_against_manifest_anchor(self) -> None:
        self.append("one")
        self.append("two")
        self.append("three")
        self.write_events(read_events(self.path)[:-1])
        with self.assertRaisesRegex(AuditChainError, "count"):
            verify_event_chain(self.path, expected_count=3, expected_head=self.head)

    def test_reordering_is_detected(self) -> None:
        self.append("one")
        self.append("two")
        events = read_events(self.path)
        self.write_events([events[1], events[0]])
        with self.assertRaisesRegex(AuditChainError, "sequence"):
            verify_event_chain(self.path)

    def test_manifest_entry_divergence_is_detected(self) -> None:
        self.append("one")
        divergent = [dict(self.entries[0])]
        divergent[0]["status"] = "different-manifest-value"
        with self.assertRaisesRegex(AuditChainError, "manifest entries"):
            verify_event_chain(
                self.path,
                expected_count=1,
                expected_head=self.head,
                expected_entries=divergent,
            )

    def test_orchestrator_refuses_resume_after_ledger_tamper(self) -> None:
        run_root = self.root / "run"
        orchestrator = CaseQueueOrchestrator(FIXTURE, run_root, run_id="h2-tamper-test", dry_run=True)
        state = orchestrator.run_until_blocked()
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        events = read_events(orchestrator.event_path)
        events[0]["status"] = "tampered"
        self.write_events_to(orchestrator.event_path, events)
        with self.assertRaises(OrchestrationError):
            orchestrator.run_until_blocked()

    @staticmethod
    def write_events_to(path: Path, events: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n" for event in events),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
