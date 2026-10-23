"""Synthetic corruption checks. Never alter the repository evidence."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from retentionlab.evidence import load_dashboard, verify_bundle, bundle_fingerprint

ROOT = Path(__file__).resolve().parents[1]

class EvidenceTests(unittest.TestCase):
    def test_versioned_bundle_loads(self):
        result, rows = load_dashboard(ROOT)
        self.assertEqual(len(rows), 620)
        self.assertIn(result["selected_model"], result["models"])

    def test_mixed_or_missing_artifacts_fail_before_display(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "artifacts", root / "artifacts")
            path = root / "artifacts/holdout_scores.csv"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_dashboard(root)
            path.unlink()
            with self.assertRaises(OSError):
                verify_bundle(root)

    def test_manifest_cannot_escape_artifact_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "artifacts").mkdir()
            (root / "artifacts/manifest.json").write_text(json.dumps({"algorithm":"sha256","files":{"../private":"fake"}}))
            with self.assertRaisesRegex(ValueError, "filename"):
                verify_bundle(root)

    def test_cache_fingerprint_changes_with_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "artifacts", root / "artifacts")
            before = bundle_fingerprint(root)
            path = root / "artifacts/results.json"
            path.write_bytes(path.read_bytes() + b" ")
            self.assertNotEqual(before, bundle_fingerprint(root))
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_dashboard(root)
