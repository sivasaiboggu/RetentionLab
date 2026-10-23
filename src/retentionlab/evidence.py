"""Read the frozen dashboard bundle only after checking cross-file integrity.

This detects accidental edits or mixed runs, not malicious provenance. A writer
who can replace both the files and manifest can replace this evidence too.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd


def verify_bundle(root: Path) -> None:
    """Reject incomplete/mixed artifact bundles before displaying their metrics."""
    manifest = json.loads((root / "artifacts/manifest.json").read_text())
    if manifest.get("algorithm") != "sha256" or not manifest.get("files"):
        raise ValueError("Invalid artifact manifest")
    for name, expected in manifest["files"].items():
        # Manifests name flat artifact files, never paths outside the bundle.
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("Invalid artifact filename")
        actual = hashlib.sha256((root / "artifacts" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Artifact checksum mismatch: {name}")


def bundle_fingerprint(root: Path) -> str:
    """Key cached reads by the actual bytes, including accidental bundle edits."""
    digest = hashlib.sha256()
    manifest = root / "artifacts/manifest.json"
    digest.update(manifest.read_bytes())
    entries = json.loads(manifest.read_text()).get("files", {})
    for name in sorted(entries):
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("Invalid artifact filename")
        digest.update(name.encode())
        digest.update((root / "artifacts" / name).read_bytes())
    return digest.hexdigest()


def load_dashboard(root: Path):
    """Return checked evidence without fitting models or modifying any files."""
    verify_bundle(root)
    result = json.loads((root / "artifacts/results.json").read_text())
    rows = pd.read_csv(root / "artifacts/holdout_scores.csv")
    if len(rows) != 620 or rows.customer_id.duplicated().any():
        raise ValueError("Invalid frozen holdout population")
    if not rows.risk.between(0, 1).all() or not rows.churn.isin([0, 1]).all():
        raise ValueError("Invalid holdout scores")
    return result, rows
