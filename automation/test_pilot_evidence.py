"""Disposable byte fixtures and mocked probes only; no provider/media execution."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import pilot_evidence as p


class PilotEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.human = {"human_approved": True, "approved_by": "fixture-only", "approved_on": "2026-10-20",
                      "scope": "inert test evidence", "user_quote": "fixture decision, not real authority"}
        self.prepare_audio()

    def tearDown(self):
        self.temp.cleanup()

    def file(self, name, content):
        (self.root / name).write_bytes(content.encode() if isinstance(content, str) else content)
        return p.describe(self.root, name)

    def json(self, name, value):
        return self.file(name, json.dumps(value))

    def prepare_audio(self, target="youtube-longform"):
        draft = self.file("draft.md", "# Metadata\n<!-- NARRATION_START -->\n\n## Section\n\n[B-ROLL: cue]\n\n<!-- P01 -->\nOne two three.\n\n<!-- NARRATION_END -->\n")
        outline = self.file("outline.md", "fixture outline")
        final = self.file("final.md", (self.root / "draft.md").read_text().replace("# Metadata", "# Approved"))
        text = self.file("text.txt", p.narration_text(self.root / "final.md"))
        packet = self.json("packet.json", {"review_id": "fixture-review", "case_id": "fixture", "target_format": target,
                                           "script": draft, "reverse_outline": outline, "supporting_inputs": []})
        approved = self.json("approval.json", {**self.human, "schema_version": "cold_truth.paired_script_approval.v1",
                                               "review_id": "fixture-review", "case_id": "fixture", "target_format": target,
                                               "review_packet": packet, "script": draft, "reverse_outline": outline,
                                               "final_script": final, "narration_text": text})
        audio = self.file("audio.bin", b"inert audio stand-in; never decoded")
        scope = self.json("scope.json", {**self.human, "case_id": "fixture", "target_format": target,
                                        "script": final, "narration_text": text, "authorized_actions": ["narration"],
                                        "output_paths": ["audio.bin"], "settings": {"voice": "inert"}})
        qa = self.json("qa.json", {**self.human, "audio": audio, "script": final, "full_listen_passed": True})
        event = {"event_id": "fixture-event", "case_id": "fixture", "target_format": target,
                 "script": final, "narration_text": text, "phase_2_scope": scope, "outputs": [audio],
                 "tool": "inert fixture", "recorded_at_utc": "2026-10-20T00:00:00Z", "settings": {"voice": "inert"}}
        manifest = self.json("manifest.json", {"entries": [event]})
        self.request = {"case_id": "fixture", "case_name": "Fixture Case", "target_format": target,
                        "script_approval": approved, "script": final, "narration_text": text, "audio": audio,
                        "phase_2_scope": scope, "audio_qa": qa, "generation_manifest": manifest,
                        "generation_event_id": "fixture-event"}
        self.json("request.json", self.request)

    def preflight(self, duration="480"):
        return p.audio_preflight(self.root, "request.json", probe=lambda path: duration)

    def test_exact_paired_approval_and_narration_extraction(self):
        self.assertEqual(p.approval(self.root, "approval.json")["final_script"], self.request["script"])
        self.assertEqual((self.root / "text.txt").read_text(), "One two three.\n")

    def test_unrecognized_editorial_markup_rejected(self):
        self.file("bad.md", "<!-- NARRATION_START -->\n[[source]]\n<!-- NARRATION_END -->")
        with self.assertRaises(p.EvidenceError):
            p.narration_text(self.root / "bad.md")

    def test_reviewed_draft_outline_packet_and_final_are_bound(self):
        for filename in ("draft.md", "outline.md", "packet.json", "final.md", "text.txt", "approval.json"):
            with self.subTest(filename=filename):
                original = (self.root / filename).read_bytes()
                (self.root / filename).write_bytes(original + b" ")
                with self.assertRaises(p.EvidenceError):
                    self.preflight()
                (self.root / filename).write_bytes(original)

    def test_unrounded_longform_boundary(self):
        self.assertFalse(self.preflight("479.9999999")["assembly_allowed"])
        self.assertTrue(self.preflight("480")["assembly_allowed"])
        self.assertTrue(self.preflight("480.0000001")["assembly_allowed"])
        self.assertIn("below_preferred_working_range", self.preflight("480")["flags"])
        self.assertEqual(self.preflight("495")["status"], "pass_preferred_range")
        self.assertIn("above_preferred_working_range", self.preflight("630.0000001")["flags"])

    def test_unrounded_shorts_boundary(self):
        self.prepare_audio("shorts")
        self.assertTrue(self.preflight("60")["assembly_allowed"])
        self.assertFalse(self.preflight("60.0000001")["assembly_allowed"])
        self.assertIn("below_shorts_target", self.preflight("29.99")["flags"])

    def test_nonfinite_zero_negative_and_invalid_durations(self):
        for value in ("NaN", "Infinity", "-Infinity", "0", "-1", "garbage"):
            with self.subTest(value=value), self.assertRaises(p.EvidenceError):
                self.preflight(value)

    def test_probe_requires_audio_stream_duration_not_container(self):
        for output in ('{"streams": [], "format":{"duration":"500"}}', '{"streams":[{"duration":"N/A"}]}',
                       '{"streams":[{"duration":"Infinity"}]}', 'not json'):
            with self.subTest(output=output), patch.object(p.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output)):
                with self.assertRaises(p.EvidenceError):
                    p.probe_audio(self.root / "audio.bin", "fixture-ffprobe")

    def test_probe_timeout_and_failure_block(self):
        for error in (subprocess.TimeoutExpired("ffprobe", 30), subprocess.CalledProcessError(1, "ffprobe"), OSError("absent")):
            with self.subTest(error=error), patch.object(p.subprocess, "run", side_effect=error):
                with self.assertRaises(p.EvidenceError):
                    p.probe_audio(self.root / "audio.bin", "fixture-ffprobe")

    def test_probe_uses_timeout_and_exact_decimal(self):
        with patch.object(p.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"streams":[{"duration":"479.9999999"}]}')) as run:
            self.assertEqual(p.probe_audio(self.root / "audio.bin", "fixture-ffprobe"), Decimal("479.9999999"))
            self.assertEqual(run.call_args.kwargs["timeout"], 30)
            self.assertEqual(run.call_args.args[0][-1], str(self.root / "audio.bin"))

    def test_missing_authority_qa_or_provenance_blocks(self):
        for filename, field, value in (("scope.json", "human_approved", False), ("qa.json", "full_listen_passed", False),
                                        ("manifest.json", "entries", [])):
            with self.subTest(filename=filename):
                original = (self.root / filename).read_bytes()
                record = p.read(self.root / filename)
                record[field] = value
                binding = self.json(filename, record)
                key = {"scope.json": "phase_2_scope", "qa.json": "audio_qa", "manifest.json": "generation_manifest"}[filename]
                old = self.request[key]
                self.request[key] = binding
                self.json("request.json", self.request)
                with self.assertRaises(p.EvidenceError):
                    self.preflight()
                (self.root / filename).write_bytes(original)
                self.request[key] = old
        self.json("request.json", self.request)

    def test_wrong_format_rejected(self):
        self.request["target_format"] = "shorts"
        self.json("request.json", self.request)
        with self.assertRaises(p.EvidenceError):
            self.preflight()

    def test_audio_changed_during_probe_rejected(self):
        def mutate(path):
            path.write_bytes(b"changed")
            return Decimal(500)
        with self.assertRaises(p.EvidenceError):
            p.audio_preflight(self.root, "request.json", probe=mutate)

    def exception(self, target="youtube-longform"):
        record = {**self.human, "approved_at": "2026-10-20T00:00:00Z", "case": "Fixture Case", "case_id": "fixture",
                  "target_format": target, "exception_type": "short-format" if target == "youtube-longform" else "shorts-over-60",
                  "reason": "inert exception test", "script": self.request["script"], "audio": self.request["audio"]}
        if target == "youtube-longform":
            record["production_summary"] = self.file("summary.md", "Short-Format")
        self.request["exception"] = self.json("exception.json", record)
        self.json("request.json", self.request)
        return record

    def test_valid_short_format_and_shorts_exceptions(self):
        self.exception()
        self.assertTrue(self.preflight("470")["assembly_allowed"])
        self.assertEqual(self.preflight("470")["status"], "pass_with_short_format_exception")
        self.prepare_audio("shorts")
        self.exception("shorts")
        self.assertTrue(self.preflight("61")["assembly_allowed"])

    def test_exception_needs_exact_audio_label_and_case(self):
        original = self.exception()
        for key, value in (("audio", {"path": "other"}), ("case", "Other Case"), ("human_approved", False),
                            ("approved_at", ""), ("reason", ""), ("production_summary", self.file("wrong-summary.md", "standard"))):
            with self.subTest(key=key):
                record = copy.deepcopy(original)
                record[key] = value
                self.request["exception"] = self.json("exception.json", record)
                self.json("request.json", self.request)
                with self.assertRaises(p.EvidenceError):
                    self.preflight("470")

    def registry(self):
        result = {"synthetic": False}
        for track, prefix, kind in (("youtube-longform", "lf", "pexels_broll"), ("shorts", "sh", "orbital_gameplay")):
            media = self.file(prefix + ".bin", prefix + " inert byte fixture")
            evidence = self.file(prefix + "-license.txt", "fixture rights evidence, no actual license")
            source = prefix + ":source-1"
            review = self.json(prefix + "-rights.json", {**self.human, "asset": media, "license_evidence": evidence,
                                                        "source_identity": source, "permitted_track": track,
                                                        "commercial_use_reviewed": True, "credits": "fixture attribution"})
            result[track] = [{"asset_id": prefix + "-1", "source_identity": source, "asset_class": kind,
                              "file": media, "license_evidence": evidence, "rights_review": review}]
        self.json("registry.json", result)
        return result

    def test_actual_bytes_rights_and_distinct_tracks_pass(self):
        self.registry()
        result = p.assets(self.root, "registry.json")
        self.assertEqual(result["counts"], {"youtube-longform": 1, "shorts": 1})
        self.assertFalse(result["media_content_or_legal_validity_certified"])

    def test_missing_file_or_changed_license_rejected(self):
        self.registry()
        (self.root / "sh.bin").unlink()
        with self.assertRaises(p.EvidenceError):
            p.assets(self.root, "registry.json")
        self.registry()
        self.file("lf-license.txt", "changed")
        with self.assertRaises(p.EvidenceError):
            p.assets(self.root, "registry.json")

    def test_cross_track_id_and_source_relabelling_detected(self):
        for key in ("asset_id", "source_identity"):
            registry = self.registry()
            registry["shorts"][0][key] = registry["youtube-longform"][0][key]
            self.json("registry.json", registry)
            with self.subTest(key=key), self.assertRaises(p.EvidenceError):
                p.assets(self.root, "registry.json")

    def test_duplicate_content_rejected_even_with_new_paths_ids_and_rights(self):
        registry = self.registry()
        entry = registry["shorts"][0]
        entry["file"] = self.file("sh.bin", (self.root / "lf.bin").read_bytes())
        rights = p.read(self.root / "sh-rights.json")
        rights["asset"] = entry["file"]
        entry["rights_review"] = self.json("sh-rights.json", rights)
        self.json("registry.json", registry)
        with self.assertRaisesRegex(p.EvidenceError, "Cross-track collision: sha256"):
            p.assets(self.root, "registry.json")

    def test_empty_pool_wrong_class_synthetic_and_unreviewed_rights(self):
        for mutation in (lambda r: r.update(shorts=[]), lambda r: r.update(synthetic=True),
                         lambda r: r["shorts"][0].update(asset_class="case_graphic"),
                         lambda r: r["youtube-longform"][0].update(rights_review={"path": "absent"})):
            registry = self.registry()
            mutation(registry)
            self.json("registry.json", registry)
            with self.assertRaises(p.EvidenceError):
                p.assets(self.root, "registry.json")

    def test_rights_review_requires_identity_track_credit_and_named_human(self):
        for key, value in (("human_approved", False), ("approved_by", ""), ("approved_on", " "),
                           ("commercial_use_reviewed", False), ("permitted_track", "shorts"),
                           ("source_identity", "other"), ("credits", "")):
            registry = self.registry()
            review = p.read(self.root / "lf-rights.json")
            review[key] = value
            registry["youtube-longform"][0]["rights_review"] = self.json("lf-rights.json", review)
            self.json("registry.json", registry)
            with self.subTest(key=key), self.assertRaises(p.EvidenceError):
                p.assets(self.root, "registry.json")

    def test_symlink_escape_rejected_when_platform_supports_it(self):
        # Target outside the fixture root but still inside the disposable test parent.
        outside = self.root.parent / (self.root.name + "-outside.bin")
        outside.write_bytes(b"inert outside fixture")
        try:
            try:
                (self.root / "alias.bin").symlink_to(outside)
            except OSError:
                self.skipTest("Symlink creation unavailable to this Windows account")
            with self.assertRaisesRegex(p.EvidenceError, "escapes"):
                p.describe(self.root, "alias.bin")
        finally:
            outside.unlink()

    def test_path_traversal_and_empty_files_block(self):
        for path in ("../outside.txt", str(self.root / "audio.bin"), "empty.txt"):
            (self.root / "empty.txt").write_bytes(b"")
            with self.subTest(path=path), self.assertRaises(p.EvidenceError):
                p.describe(self.root, path)

    def aligned(self):
        record = {"audio": self.request["audio"], "script": self.request["script"],
                  "narration_text": self.request["narration_text"], "tool": "fixture manual timing",
                  "recorded_at_utc": "2026-10-20T00:00:00Z", "timing_review": {**self.human, "full_listen_passed": True},
                  "segments": [{"start": 0, "end": 1.5, "text": "One two"}, {"start": 1.5, "end": 3, "text": "three."}]}
        self.json("alignment.json", record)
        return record

    def test_alignment_and_srt_exact_interface(self):
        self.aligned()
        record = p.alignment(self.root, "alignment.json", self.preflight())
        self.assertIn("00:00:01,500 --> 00:00:03,000", p.srt(record))

    def test_alignment_missing_words_overlap_out_of_bounds_and_missing_listen(self):
        for mutation in (lambda r: r["segments"][1].update(text="different"),
                         lambda r: r["segments"][1].update(start=1),
                         lambda r: r["segments"][1].update(end=481),
                         lambda r: r["timing_review"].update(full_listen_passed=False),
                         lambda r: r.update(audio={"path": "other"})):
            record = self.aligned()
            mutation(record)
            self.json("alignment.json", record)
            with self.assertRaises(p.EvidenceError):
                p.alignment(self.root, "alignment.json", self.preflight())

    def test_output_cannot_overwrite_or_escape(self):
        with self.assertRaises(FileExistsError):
            p.new_output(self.root, self.root / "audio.bin")
        with self.assertRaises(p.EvidenceError):
            p.new_output(self.root, self.root.parent / "outside.json")


if __name__ == "__main__":
    unittest.main()
