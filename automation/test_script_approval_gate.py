from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from c4_script_approval_gate import (
    APPROVED, AWAITING, BLOCKED, CASE_ID, REVISION,
    expected_bindings, process_decision,
)
from json_schema_subset import validate_schema_compatibility


AUTOMATION = Path(__file__).resolve().parent
FIXTURE = AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
LIVE = FIXTURE / "output" / "c3_real_writer_editor_chain"
WRITER = next((LIVE / "writer" / "agent_runs").rglob("strategist_handoff.json"))
EDITOR = next((LIVE / "editor" / "agent_runs").rglob("strategist_handoff.json"))
APPROVAL_SCHEMA = FIXTURE / "approval_gate" / "script_approval.schema.json"
REJECTION_SCHEMA = FIXTURE / "approval_gate" / "script_rejection.schema.json"


def approval(identifier: str = "C4-APPROVE-0001") -> dict:
    return {
        "schema_version": "1.0", "approval_id": identifier, "case_id": CASE_ID,
        **expected_bindings(WRITER, EDITOR), "decision": "approve",
        "decision_timestamp_utc": "2026-07-12T12:00:00Z", "reviewer_role": "human_owner",
        "reviewer_note": "Synthetic fixture approved for preflight-gate testing only.",
        "permitted_next_stage": "narration_preflight_only",
        "narration_authorized": False, "asset_authorized": False,
        "rendering_authorized": False, "publishing_enabled": False,
        "real_production_enabled": False,
    }


def rejection(identifier: str = "C4-REJECT-0001") -> dict:
    value = approval(identifier)
    value.pop("permitted_next_stage")
    value.update({"decision": "reject", "rejection_reason_code": "redundancy_revision",
                  "required_return_stage": REVISION})
    return value


class GateHarness:
    def __init__(self, test: unittest.TestCase) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=FIXTURE / "output")
        self.root = Path(self.temp.name)
        self.test = test

    def close(self) -> None:
        self.temp.cleanup()

    def write(self, value: dict, name: str = "human_decision.json") -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def run(self, value: dict | None, *, state: str = AWAITING,
            writer: Path = WRITER, editor: Path = EDITOR, output: Path | None = None) -> dict:
        path = None if value is None else self.write(value)
        return process_decision(
            fixture_root=FIXTURE, output_root=output or self.root / "records",
            current_state=state, artifact_path=path, writer_path=writer, editor_path=editor,
            approval_schema_path=APPROVAL_SCHEMA, rejection_schema_path=REJECTION_SCHEMA,
        )


class C4ApprovalGateTests(unittest.TestCase):
    def setUp(self): self.h = GateHarness(self)
    def tearDown(self): self.h.close()

    def test_01_valid_approval_only_reaches_preflight(self):
        result = self.h.run(approval())
        self.assertEqual(result["state"], APPROVED)
        self.assertNotIn(result["state"], {"NARRATION_GENERATED", "ASSETS_READY", "RENDERED"})

    def test_02_approval_permissions_are_exactly_false(self):
        result = self.h.run(approval())
        for field in ("narration_authorized", "asset_authorized", "rendering_authorized", "publishing_enabled", "real_production_enabled"):
            self.assertIs(result[field], False)

    def test_03_valid_rejection_only_returns_to_writer(self):
        self.assertEqual(self.h.run(rejection())["state"], REVISION)

    def test_04_missing_artifact_preserves_awaiting_state(self):
        self.assertEqual(self.h.run(None)["state"], AWAITING)

    def test_05_editor_hash_mismatch_blocks(self):
        item = approval(); item["upstream_editor_handoff_hash"] = "0" * 64
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_06_writer_hash_mismatch_blocks(self):
        item = approval(); item["upstream_writer_handoff_hash"] = "0" * 64
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_07_case_mismatch_blocks(self):
        item = approval(); item["case_id"] = "different-synthetic-case"
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_08_script_hash_mismatch_blocks(self):
        item = approval(); item["approved_script_hash"] = "0" * 64
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_09_missing_or_invalid_reviewer_blocks(self):
        for mode in ("missing", "agent"):
            item = approval(f"C4-REVIEW-{mode}-001")
            if mode == "missing": item.pop("reviewer_role")
            else: item["reviewer_role"] = "editor_agent"
            with self.subTest(mode=mode): self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_10_invalid_decision_or_stage_blocks(self):
        item = approval("C4-DECISION-0001"); item["decision"] = "auto_approve"
        self.assertEqual(self.h.run(item)["state"], BLOCKED)
        item = approval("C4-STAGE-0001"); item["permitted_next_stage"] = "narration_generation"
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_11_narration_true_blocks(self):
        item = approval(); item["narration_authorized"] = True
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_12_any_later_permission_true_blocks(self):
        for index, field in enumerate(("asset_authorized", "rendering_authorized", "publishing_enabled", "real_production_enabled"), 1):
            item = approval(f"C4-PERMISSION-{index:04d}"); item[field] = True
            with self.subTest(field=field): self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_13_rejection_forward_stage_blocks(self):
        item = rejection(); item["required_return_stage"] = "EDITOR_REVIEW"
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_14_replayed_approval_id_blocks(self):
        item = approval()
        self.assertEqual(self.h.run(item)["state"], APPROVED)
        self.assertEqual(self.h.run(item)["state"], BLOCKED)

    def test_15_changed_c3_handoff_invalidates_prior_approval(self):
        changed = self.h.root / "changed_writer.json"
        value = json.loads(WRITER.read_text(encoding="utf-8"))
        value["result"]["narration_text"] += " Changed."
        changed.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.h.run(approval(), writer=changed)["state"], BLOCKED)

    def test_16_path_escape_blocks(self):
        escaped = FIXTURE.parent / "not_fixture_output"
        self.assertEqual(self.h.run(approval(), output=escaped)["state"], BLOCKED)

    def test_17_strict_schemas_are_locally_compatible(self):
        validate_schema_compatibility(json.loads(APPROVAL_SCHEMA.read_text(encoding="utf-8")))
        validate_schema_compatibility(json.loads(REJECTION_SCHEMA.read_text(encoding="utf-8")))

    def test_18_no_process_or_external_capability_in_record(self):
        item = approval(); result = self.h.run(item)
        self.assertEqual(result["state"], APPROVED)
        record = self.h.root / "records" / "decision_records" / f"{item['approval_id']}.json"
        value = json.loads(record.read_text(encoding="utf-8"))
        self.assertFalse(value["external_process_invoked"])
        self.assertFalse(value["real_production_enabled"])
        self.assertFalse(value["publishing_enabled"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(C4ApprovalGateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"c4_offline_tests": "passed" if result.wasSuccessful() else "failed",
                      "tests_run": result.testsRun, "real_invocation": "not_requested"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
