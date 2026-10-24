"""Synthetic corruption checks. Never alter the repository evidence."""
import json
import hashlib
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

    def rewrite_fixture(self, root, filename, data):
        """Rehash only a disposable fixture to exercise semantic validation."""
        path = root / "artifacts" / filename
        path.write_text(data)
        manifest_path = root / "artifacts/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))

    def test_invalid_risk_and_duplicate_population_are_rejected(self):
        import pandas as pd
        for mutation, message in [("risk", "scores"), ("duplicate", "population")]:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                shutil.copytree(ROOT / "artifacts", root / "artifacts")
                rows = pd.read_csv(root / "artifacts/holdout_scores.csv")
                if mutation == "risk":
                    rows.loc[0, "risk"] = 2
                else:
                    rows.loc[0, "customer_id"] = rows.loc[1, "customer_id"]
                self.rewrite_fixture(root, "holdout_scores.csv", rows.to_csv(index=False))
                with self.assertRaisesRegex(ValueError, message):
                    load_dashboard(root)

    def test_missing_holdout_row_is_rejected(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "artifacts", root / "artifacts")
            rows = pd.read_csv(root / "artifacts/holdout_scores.csv").iloc[1:]
            self.rewrite_fixture(root, "holdout_scores.csv", rows.to_csv(index=False))
            with self.assertRaisesRegex(ValueError, "population"):
                load_dashboard(root)


    def test_manifest_must_cover_every_required_evidence_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);shutil.copytree(ROOT / "artifacts",root / "artifacts")
            path=root / "artifacts/manifest.json";manifest=json.loads(path.read_text())
            del manifest["files"]["results.json"];path.write_text(json.dumps(manifest))
            for check in [verify_bundle,bundle_fingerprint]:
                with self.assertRaisesRegex(ValueError,"omits required"):
                    check(root)

    def test_malformed_manifest_shapes_and_digest_values_fail_closed(self):
        variants=[[],{"algorithm":"sha256","files":[]},{"algorithm":"sha256","files":{"results.json":42}},
                  {"algorithm":"sha256","files":{"results.json":"not-a-digest"}}]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root / "artifacts").mkdir()
            for manifest in variants:
                (root / "artifacts/manifest.json").write_text(json.dumps(manifest))
                for check in [verify_bundle,bundle_fingerprint]:
                    with self.assertRaises(ValueError):check(root)


    def test_rehashed_split_overlap_and_population_mismatch_are_rejected(self):
        for mutation in ["overlap", "population"]:
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);shutil.copytree(ROOT / "artifacts",root / "artifacts")
                splits=json.loads((root / "artifacts/splits.json").read_text())
                if mutation=="overlap":splits["train"][0]=splits["holdout"][0]
                else:splits["holdout"][0]=-999999
                self.rewrite_fixture(root,"splits.json",json.dumps(splits))
                with self.assertRaisesRegex(ValueError,"overlap|holdout IDs"):load_dashboard(root)
