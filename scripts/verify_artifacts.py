"""Verify the checked-in evidence bundle without training or changing files."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from retentionlab.evidence import load_dashboard

if __name__ == "__main__":
    result, rows = load_dashboard(ROOT)
    print(f"Verified {len(rows)} rows; selected model: {result['selected_model']}")
