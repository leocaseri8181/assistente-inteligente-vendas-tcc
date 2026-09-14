"""Download only the five data files from a pinned public mirror; no remote code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REVISION = "9738c487307eb45d270c6ee5d641607bbb8f2a12"
BASE = f"https://raw.githubusercontent.com/ChitikaneniVarsha/Maven-Sales-Challenge/{REVISION}"
FILES = ("accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv", "data_dictionary.csv")


def main():
    folder = ROOT / "data/raw/maven"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "Maven CRM Sales Opportunities (fictitious)",
        "source_page": "https://mavenanalytics.io/data-playground/crm-sales-opportunities",
        "license_as_declared_by_source": "Public Domain",
        "provenance_note": "Public third-party mirror; not byte-verified against an authenticated original download.",
        "mirror_revision": REVISION,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    for name in FILES:
        url = f"{BASE}/{name}"
        with urlopen(url, timeout=30) as response:
            content = response.read(5_000_001)
        if len(content) > 5_000_000 or b"<html" in content[:1000].lower():
            raise ValueError(f"Unexpected response for {name}")
        destination = folder / name
        if destination.exists() and destination.read_bytes() != content:
            raise ValueError(f"Refusing to overwrite a different raw file: {name}")
        destination.write_bytes(content)
        manifest["files"][name] = {"url": url, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    path = ROOT / "data/manifest.json"
    # Preserve the first retrieval timestamp on an identical repeat download.
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing["files"] == manifest["files"]:
            manifest["retrieved_at_utc"] = existing["retrieved_at_utc"]
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": list(manifest["files"]), "revision": REVISION}))


if __name__ == "__main__":
    main()
