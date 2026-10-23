"""Fetch the fixed UCI source, verify checksum, and extract only its CSV."""

from pathlib import Path
import hashlib
import io
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip"
EXPECTED = "90d5fb6bd1630cd4de4b4d28fcf8b4cb92a8f6ab7484605b0799d47386f7dbe1"


def main():
    with urllib.request.urlopen(URL, timeout=30) as response:
        archive = response.read(5_000_000)
    raw = zipfile.ZipFile(io.BytesIO(archive)).read("Customer Churn.csv")
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError(
            "Source changed; review provenance before replacing the pinned data"
        )
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/raw.csv").write_bytes(raw)
    print("Verified UCI source downloaded")


if __name__ == "__main__":
    main()
