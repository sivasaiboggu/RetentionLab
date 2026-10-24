"""Read the frozen dashboard bundle only after checking cross-file integrity.

This detects accidental edits or mixed runs, not malicious provenance. A writer
who can replace both the files and manifest can replace this evidence too.
"""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd


REQUIRED_FILES = frozenset(['results.json', 'holdout_scores.csv', 'splits.json'])


def checked_entries(root: Path) -> dict:
    manifest = json.loads((root / "artifacts/manifest.json").read_text())
    if not isinstance(manifest, dict) or manifest.get("algorithm") != "sha256":
        raise ValueError("Invalid artifact manifest")
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("Invalid artifact manifest files")
    for name, expected in entries.items():
        if not isinstance(name, str) or Path(name).name != name or name in (".", "..") or "\\" in name:
            raise ValueError("Invalid artifact filename")
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise ValueError("Invalid artifact checksum")
    if not REQUIRED_FILES.issubset(entries):
        raise ValueError("Manifest omits required evidence files")
    return entries


def verify_bundle(root: Path) -> None:
    """Reject incomplete/mixed artifact bundles before displaying their metrics."""
    for name, expected in checked_entries(root).items():
        actual = hashlib.sha256((root / "artifacts" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Artifact checksum mismatch: {name}")


def bundle_fingerprint(root: Path) -> str:
    """Key cached reads by validated manifest coverage and actual artifact bytes."""
    entries = checked_entries(root)
    digest = hashlib.sha256((root / "artifacts/manifest.json").read_bytes())
    for name in sorted(entries):
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
    splits = json.loads((root / "artifacts/splits.json").read_text())
    if not isinstance(splits, dict) or set(splits) != {"train", "validation", "holdout"}:
        raise ValueError("Invalid frozen split structure")
    populations = []
    for ids in splits.values():
        if not isinstance(ids, list) or any(not isinstance(value, int) or isinstance(value, bool) for value in ids) or len(ids) != len(set(ids)):
            raise ValueError("Invalid frozen split IDs")
        populations.append(set(ids))
    if any(populations[a] & populations[b] for a, b in [(0, 1), (0, 2), (1, 2)]):
        raise ValueError("Frozen splits overlap")
    if set(splits["holdout"]) != set(rows.customer_id):
        raise ValueError("Displayed population does not match frozen holdout IDs")
    return result, rows
