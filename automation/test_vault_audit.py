from pathlib import Path
import json
import tempfile
import unittest

from vault_audit import audit


class VaultAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name)

    def write(self, name, text):
        path = self.vault / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_root_relative_alias_and_heading_links(self):
        self.write("Home.md", "[[admin/Plan#Next|Plan]]")
        self.write("admin/Plan.md", "[[../Home]]")
        result = audit(self.vault)
        self.assertEqual(result["issues"], [])
        self.assertEqual(len(result["components"]), 1)
        self.assertEqual(result["edge_count"], 2)

    def test_duplicate_basename_is_ambiguous_outside_its_folder(self):
        self.write("Home.md", "[[Draft]]")
        self.write("a/Draft.md", "[[../Home]]")
        self.write("b/Draft.md", "[[../Home]]")
        result = audit(self.vault)
        self.assertEqual(result["issues"][0]["status"], "ambiguous")
        self.assertEqual(len(result["duplicate_basenames"]["draft"]), 2)

    def test_local_basename_resolves_before_global_ambiguity(self):
        self.write("a/Review.md", "[[Draft]]")
        self.write("a/Draft.md", "# Draft")
        self.write("b/Draft.md", "# Draft")
        result = audit(self.vault)
        self.assertEqual(result["issues"], [])
        self.assertIn(["a/Review.md", "a/Draft.md"], result["edges"])

    def test_code_examples_are_not_links_and_lines_remain_correct(self):
        self.write("Home.md", "```md\n[[Example]]\n```\n`[[Inline]]`\n[[Missing]]")
        self.assertEqual(audit(self.vault)["issues"], [{"source": "Home.md", "line": 5, "target": "Missing", "status": "missing", "candidates": []}])

    def test_encoded_markdown_path_and_external_url(self):
        self.write("Home.md", "[Note](My%20Note.md) [Web](https://example.invalid) [Next](#next)")
        self.write("My Note.md", "# Note")
        result = audit(self.vault)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["external_link_count"], 1)
        self.assertEqual(result["edge_count"], 1)

    def test_private_and_hidden_content_never_decoded(self):
        self.write("Home.md", "[[API_KEYS]] [[1_LIFE/Private]]")
        for name in ("API_KEYS.md", "1_LIFE/Private.md", ".obsidian/plugin/secret.md"):
            path = self.vault / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\xff\xfe\x00")
        result = audit(self.vault)
        self.assertEqual(result["note_count"], 1)
        self.assertEqual(result["issues"], [])

    def test_disconnected_note_is_reported(self):
        self.write("Home.md", "[[Plan]]")
        self.write("Plan.md", "# Plan")
        self.write("Lost.md", "# Lost")
        result = audit(self.vault)
        self.assertEqual(result["orphan_notes"], ["Lost.md"])
        self.assertEqual(len(result["components"]), 2)

    def test_canvas_file_and_edge_validation(self):
        self.write("Home.md", "[[Flow.canvas]]")
        data = {"nodes": [{"id": "a", "type": "file", "file": "Home.md"}], "edges": []}
        self.write("Flow.canvas", json.dumps(data))
        self.assertEqual(audit(self.vault)["issues"], [])
        data["nodes"][0]["file"] = "Missing.md"
        data["edges"] = [{"id": "e", "fromNode": "a", "toNode": "absent"}]
        self.write("Flow.canvas", json.dumps(data))
        self.assertEqual({i["status"] for i in audit(self.vault)["issues"]}, {"missing_canvas_file", "invalid_canvas_edge"})

    def test_invalid_canvas_json_is_reported(self):
        self.write("Home.md", "[[Flow.canvas]]")
        self.write("Flow.canvas", "{")
        self.assertEqual(audit(self.vault)["issues"][0]["status"], "invalid_canvas")

    def test_missing_vault_cannot_pass_as_empty(self):
        with self.assertRaises(ValueError):
            audit(self.vault / "does-not-exist")

    def test_backlink_only_note_is_connected_but_unreachable_from_home(self):
        self.write("00_START_HERE.md", "[[Plan]]")
        self.write("Plan.md", "# Plan")
        self.write("New Research.md", "[[Plan]]")
        result = audit(self.vault)
        self.assertEqual(len(result["components"]), 1)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["reachable_note_count"], 2)
        self.assertEqual(result["unreachable_from_entry"], ["New Research.md"])

    def test_hub_forward_link_makes_research_reachable(self):
        self.write("00_START_HERE.md", "[[Research Hub]]")
        self.write("Research Hub.md", "[[case/Research]]")
        self.write("case/Research.md", "[[00_START_HERE]]")
        result = audit(self.vault)
        self.assertEqual(result["reachable_note_count"], 3)
        self.assertEqual(result["unreachable_from_entry"], [])

    def test_explicit_missing_entry_does_not_pass_an_empty_graph(self):
        self.write("Other.md", "# Other")
        result = audit(self.vault, entry_note="Home.md")
        self.assertIs(result["entry_note_exists"], False)
        self.assertEqual(result["reachable_note_count"], 0)
        self.assertEqual(result["unreachable_from_entry"], ["Other.md"])


if __name__ == "__main__":
    unittest.main()
