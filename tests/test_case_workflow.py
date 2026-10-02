"""Offline CLI regressions using only copies of the committed fictional case."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/acme_payments_case.json"


class CaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.case = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.path = self.work / "fictional-case.json"

    def write_case(self):
        self.path.write_text(json.dumps(self.case, ensure_ascii=False), encoding="utf-8")

    def run_cli(self, script, *args):
        # Exercise default Windows code-page file IO, even if CI enables UTF-8 mode.
        env = os.environ.copy()
        env["PYTHONUTF8"] = "0"
        return subprocess.run(
            [sys.executable, "-X", "utf8=0", str(ROOT / script), *map(str, args)],
            cwd=self.work, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15,
        )

    def assert_rejected(self, result, diagnostic):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_default_example_passes_from_another_directory(self):
        result = self.run_cli("validate.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("30.98", result.stdout)

    def test_external_unicode_case_validates_and_renders_utf8(self):
        self.case["intake"]["vendor_name"] = "Fictional Caf\u00e9 \u96ea"
        self.write_case()
        result = self.run_cli("validate.py", self.path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.work / "packet.md"
        result = self.run_cli("scripts/render_case_packet.py", self.path, "--out", output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Fictional Caf\u00e9 \u96ea", output.read_text(encoding="utf-8"))

    def test_missing_required_fields_reject_the_supplied_case(self):
        for field in ("schema_version", "created_at"):
            with self.subTest(field=field):
                self.case = json.loads(EXAMPLE.read_text(encoding="utf-8"))
                del self.case[field]
                self.write_case()
                self.assert_rejected(self.run_cli("validate.py", self.path), field)
        self.case = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        del self.case["intake"]["vendor_name"]
        self.write_case()
        self.assert_rejected(self.run_cli("validate.py", self.path), "vendor_name")

    def test_schema_types_enums_and_constants_are_enforced(self):
        for section, field, value in (
            ("intake", "contract_value_usd", "not a number"),
            ("intake", "data_access_level", "unknown"),
            ("council_thread", "manager_agent", "unknown"),
        ):
            with self.subTest(field=field):
                self.case = json.loads(EXAMPLE.read_text(encoding="utf-8"))
                self.case[section][field] = value
                self.write_case()
                self.assert_rejected(self.run_cli("validate.py", self.path), field)

    def test_existing_score_and_evidence_checks_apply_to_supplied_case(self):
        self.case["risk_assessment"]["weighted_score"] = 0
        self.case["risk_assessment"]["domain_scores"]["cybersecurity"]["evidence_ids"] = ["missing-fictional-evidence"]
        self.write_case()
        result = self.run_cli("validate.py", self.path)
        self.assert_rejected(result, "weighted score mismatch")
        self.assertIn("references missing evidence", result.stdout)

    def test_missing_or_malformed_file_fails_without_falling_back_to_example(self):
        self.assert_rejected(self.run_cli("validate.py", self.path), "Cannot read JSON")
        self.path.write_text("{malformed", encoding="utf-8")
        self.assert_rejected(self.run_cli("validate.py", self.path), "Cannot read JSON")

    def test_incomplete_assessment_fails_without_traceback(self):
        self.case["risk_assessment"] = {}
        self.write_case()
        self.assert_rejected(self.run_cli("validate.py", self.path), "Incomplete or invalid case data")

    def test_bundled_packet_remains_unchanged(self):
        output = self.work / "packet.md"
        result = self.run_cli("scripts/render_case_packet.py", EXAMPLE, "--out", output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8"),
                         (ROOT / "examples/acme_payments_packet.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
