from __future__ import annotations

import inspect
import json
import stat
import unittest
from datetime import datetime
from pathlib import Path

import c8o_direct_elevenlabs_api_contract as direct_contract


AUTOMATION = Path(__file__).resolve().parent
FUTURE = (
    AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace"
    / "narration_preflight" / "future_c8"
)
CHAIN_STATE = (
    AUTOMATION / "fixtures" / "real_writer_editor_fixture_workspace" / "output"
    / "c3_real_writer_editor_chain" / "chain_state.json"
)
NOW = datetime(2026, 7, 13, 12, 5, 0)
FAKE_MP3 = b"ID3" + (b"\x00" * 64)


def valid_authorization():
    record = dict(direct_contract.STATIC_AUTHORIZATION_VALUES)
    record.update(direct_contract.authorization_bindings())
    record.update({
        "authorization_id": "C8O-OFFLINE-HYPOTHETICAL-0001",
        "issued_at_utc": "2026-07-13T12:00:00Z",
        "expires_at_utc": "2026-07-13T12:10:00Z",
    })
    return record


class OpaquePlaceholder:
    __slots__ = ()

    def __repr__(self):
        return "<opaque-placeholder>"


class FakeInMemoryTransport:
    def __init__(self, response=None, fail=False):
        self.response = response or {
            "status_code": 200, "content_type": "audio/mpeg", "body": FAKE_MP3,
        }
        self.fail = fail
        self.call_count = 0
        self.credential_received = False
        self.voice_identifier_received = False
        self.safe_request = None

    def __call__(self, **request):
        self.call_count += 1
        self.credential_received = request.get("credential") is not None
        self.voice_identifier_received = request.get("voice_identifier") is not None
        self.safe_request = {
            key: value for key, value in request.items()
            if key not in {"credential", "voice_identifier"}
        }
        if self.fail:
            raise RuntimeError("synthetic transport failure")
        return self.response


class InMemoryExclusiveWriter:
    def __init__(self, fail=False):
        self.fail = fail
        self.call_count = 0
        self.relative_path = None
        self.byte_count = 0
        self.exclusive_create = None

    def __call__(self, *, relative_path, data, exclusive_create):
        self.call_count += 1
        self.relative_path = relative_path
        self.byte_count = len(data)
        self.exclusive_create = exclusive_create
        if self.fail:
            raise OSError("synthetic exclusive-write failure")


def execute(adapter=None, transport=None, writer=None, authorization=None, **changes):
    values = {
        "authorization": authorization or valid_authorization(),
        "now_utc": NOW,
        "transport": transport or FakeInMemoryTransport(),
        "exclusive_writer": writer or InMemoryExclusiveWriter(),
        "api_credential": OpaquePlaceholder(),
        "voice_identifier": OpaquePlaceholder(),
        "destination_exists": False,
    }
    values.update(changes)
    return (adapter or direct_contract.DirectElevenLabsApiAdapter()).execute(**values)


class C8oDirectElevenLabsApiContractTests(unittest.TestCase):
    def test_01_exact_request_shape_uses_opaque_injected_values(self):
        transport = FakeInMemoryTransport()
        result = execute(transport=transport)
        self.assertEqual(result["state"], direct_contract.READY)
        self.assertEqual(transport.call_count, 1)
        self.assertTrue(transport.credential_received)
        self.assertTrue(transport.voice_identifier_received)
        self.assertEqual(set(transport.safe_request), {"method", "route", "output_format", "body"})
        self.assertEqual(transport.safe_request["method"], "POST")
        self.assertEqual(transport.safe_request["route"], direct_contract.DIRECT_ROUTE)
        self.assertEqual(transport.safe_request["output_format"], direct_contract.OUTPUT_FORMAT)
        self.assertEqual(transport.safe_request["body"], {
            "text": direct_contract.SYNTHETIC_TEXT,
            "model_id": direct_contract.MODEL_ID,
            "voice_settings": dict(direct_contract.LOCKED_SETTINGS),
        })

    def test_02_only_named_future_placeholders_exist_without_environment_access(self):
        self.assertEqual(direct_contract.CREDENTIAL_PLACEHOLDER_NAMES, (
            "COLD_TRUTH_ELEVENLABS_API_KEY",
            "COLD_TRUTH_ELEVENLABS_MIA_VOICE_ID",
        ))
        source = inspect.getsource(direct_contract).lower()
        for term in ("os.environ", "getenv(", "environ[", "dotenv", "keyring",
                     "private_config", "mcp__", "tool_search", "import requests",
                     "import httpx", "import urllib", "import socket", "import subprocess",
                     "powershell", "cmd.exe", "node", "codex", "browser"):
            self.assertNotIn(term, source)

    def test_03_single_use_adapter_calls_transport_and_writer_at_most_once(self):
        adapter = direct_contract.DirectElevenLabsApiAdapter()
        transport = FakeInMemoryTransport()
        writer = InMemoryExclusiveWriter()
        first = execute(adapter=adapter, transport=transport, writer=writer)
        second = execute(adapter=adapter, transport=transport, writer=writer)
        self.assertEqual(first["state"], direct_contract.READY)
        self.assertEqual(second["state"], direct_contract.BLOCKED)
        self.assertEqual(second["safe_reason_code"], "authorization_replayed")
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(writer.call_count, 1)

    def test_04_changed_request_bindings_fail_before_transport(self):
        mutations = (
            {"text": "changed"},
            {"model_id": "other"},
            {"voice_settings": {**direct_contract.LOCKED_SETTINGS, "stability": 0.7}},
            {"voice_settings": {**direct_contract.LOCKED_SETTINGS, "speed": 1.0}},
            {"output_format": "wav"},
            {"route": "existing_configured_elevenlabs_mcp"},
            {"output_path": "other/output.mp3"},
            {"api_credential": None},
            {"voice_identifier": None},
        )
        for changes in mutations:
            transport = FakeInMemoryTransport()
            writer = InMemoryExclusiveWriter()
            result = execute(transport=transport, writer=writer, **changes)
            with self.subTest(changes=tuple(changes)):
                self.assertEqual(result["state"], direct_contract.BLOCKED)
                self.assertEqual(transport.call_count, 0)
                self.assertEqual(writer.call_count, 0)

    def test_05_missing_malformed_expired_or_mismatched_authorization_fails_closed(self):
        records = []
        missing = valid_authorization(); missing.pop("single_use"); records.append(missing)
        extra = valid_authorization(); extra["endpoint"] = "forbidden"; records.append(extra)
        changed = valid_authorization(); changed["synthetic_text_sha256"] = "0" * 64; records.append(changed)
        wrong_route = valid_authorization(); wrong_route["execution_transport"] = "other"; records.append(wrong_route)
        consumed = valid_authorization(); consumed["consumed"] = True; records.append(consumed)
        expired = valid_authorization(); expired["expires_at_utc"] = "2026-07-13T12:04:59Z"; records.append(expired)
        too_long = valid_authorization(); too_long["expires_at_utc"] = "2026-07-13T13:00:00Z"; records.append(too_long)
        for record in records:
            transport = FakeInMemoryTransport()
            result = execute(transport=transport, authorization=record)
            with self.subTest(fields=len(record)):
                self.assertEqual(result["state"], direct_contract.BLOCKED)
                self.assertEqual(transport.call_count, 0)

    def test_06_valid_fake_mp3_permits_one_canonical_exclusive_create(self):
        writer = InMemoryExclusiveWriter()
        result = execute(writer=writer)
        self.assertEqual(result["state"], direct_contract.READY)
        self.assertEqual(writer.call_count, 1)
        self.assertEqual(writer.relative_path, direct_contract.OUTPUT_PATH)
        self.assertEqual(writer.byte_count, len(FAKE_MP3))
        self.assertIs(writer.exclusive_create, True)
        self.assertEqual(result["audit"]["exists"], True)

    def test_07_response_destination_and_write_failures_do_not_retry(self):
        responses = (
            {"status_code": 500, "content_type": "audio/mpeg", "body": FAKE_MP3},
            {"status_code": 200, "content_type": "audio/mpeg", "body": b""},
            {"status_code": 200, "content_type": "text/plain", "body": FAKE_MP3},
            {"status_code": 200, "content_type": "audio/mpeg", "body": b"not-mp3"},
            {"status_code": 200, "content_type": "audio/mpeg",
             "body": b"ID3" + (b"0" * direct_contract.MAX_RESPONSE_BYTES)},
            {"status_code": 200, "content_type": "audio/mpeg", "body": bytearray(FAKE_MP3)},
            {"status_code": 200, "content_type": "audio/mpeg", "body": FAKE_MP3,
             "headers": {"forbidden": "extra"}},
        )
        for response in responses:
            transport = FakeInMemoryTransport(response=response)
            writer = InMemoryExclusiveWriter()
            result = execute(transport=transport, writer=writer)
            with self.subTest(response_fields=tuple(response)):
                self.assertEqual(result["state"], direct_contract.BLOCKED)
                self.assertEqual(transport.call_count, 1)
                self.assertEqual(writer.call_count, 0)
        transport = FakeInMemoryTransport(); writer = InMemoryExclusiveWriter()
        self.assertEqual(execute(transport=transport, writer=writer, destination_exists=True)["state"], direct_contract.BLOCKED)
        self.assertEqual(transport.call_count, 0); self.assertEqual(writer.call_count, 0)
        transport = FakeInMemoryTransport(); writer = InMemoryExclusiveWriter(fail=True)
        self.assertEqual(execute(transport=transport, writer=writer)["state"], direct_contract.BLOCKED)
        self.assertEqual(transport.call_count, 1); self.assertEqual(writer.call_count, 1)
        transport = FakeInMemoryTransport(fail=True); writer = InMemoryExclusiveWriter()
        self.assertEqual(execute(transport=transport, writer=writer)["state"], direct_contract.BLOCKED)
        self.assertEqual(transport.call_count, 1); self.assertEqual(writer.call_count, 0)

    def test_08_no_retry_redirect_fallback_or_later_action_is_permitted(self):
        record = valid_authorization()
        for field in ("retry_allowed", "redirect_allowed", "fallback_allowed", "polling_allowed",
                      "status_call_allowed", "cleanup_allowed", "deletion_allowed", "copy_allowed",
                      "overwrite_allowed", "batch_mode_allowed", "multi_output_allowed",
                      "alternate_provider_allowed", "publishing_enabled", "real_production_enabled"):
            self.assertIs(record[field], False)
        self.assertEqual(record["maximum_transport_call_count"], 1)
        self.assertEqual(record["authorized_output_count"], 1)
        self.assertEqual(record["maximum_exclusive_create_write_count"], 1)

    def test_09_safe_audit_has_only_non_sensitive_metadata(self):
        result = execute()
        audit = result["audit"]
        self.assertEqual(set(audit), direct_contract.AUDIT_FIELDS)
        self.assertEqual(audit["authorization_relative_path"], direct_contract.OUTPUT_PATH)
        self.assertEqual(audit["transport_count"], 1)
        rendered = json.dumps(dict(audit)).lower()
        for term in ("credential", "voice_id", "voice_identifier", "endpoint", "request_body",
                     "response_body", "headers", "account", "provider", "api_key"):
            self.assertNotIn(term, rendered)

    def test_10_c3_c4_real_case_and_production_boundaries_remain_closed(self):
        state = json.loads(CHAIN_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "AWAITING_SCRIPT_APPROVAL")
        self.assertFalse(state["narration_authorized"])
        record = valid_authorization()
        self.assertFalse(record["real_case_content_allowed"])
        self.assertFalse(record["c4_approval_artifact_allowed"])
        self.assertFalse(record["publishing_enabled"])
        self.assertFalse(record["real_production_enabled"])

    def test_11_historical_mcp_records_are_regular_files_and_never_parsed(self):
        names = (
            "c8_one_time_live_authorization.json", "c8_one_time_live_safe_audit.json",
            "c8n_one_time_live_authorization.json", "c8n_one_time_live_safe_audit.json",
        )
        for name in names:
            metadata = (FUTURE / name).lstat()
            self.assertTrue(stat.S_ISREG(metadata.st_mode))
            self.assertFalse(getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        C8oDirectElevenLabsApiContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "c8o_offline_tests": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "provider_or_network_request": "not_performed",
        "mcp_invocation": "not_performed",
        "audio_or_media_creation": "not_performed",
    }, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
