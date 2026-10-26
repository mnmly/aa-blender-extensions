"""Build the AA extension repository into an output folder.

Zips every add-on in extensions/ and writes an index.json listing them,
merged with the entries from each upstream repository in UPSTREAM_INDEXES
(whose archives stay hosted upstream).

Usage: python scripts/build_index.py [output_dir]
"""

import hashlib
import json
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS = ROOT / "extensions"

UPSTREAM_INDEXES = [
    "https://github.com/mnmly/BlenderGIS/releases/latest/download/index.json",
]

# Manifest keys that are copied into the index entry when present.
INDEX_KEYS = (
    "schema_version", "id", "name", "tagline", "version", "type", "maintainer",
    "license", "blender_version_min", "blender_version_max", "website",
    "permissions", "tags", "platforms",
)
SKIP = {"__pycache__", ".DS_Store"}


def build_extension(source, out_dir):
    manifest = tomllib.loads((source / "blender_manifest.toml").read_text())
    archive = out_dir / f"{manifest['id']}-{manifest['version']}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            rel = path.relative_to(source)
            if path.is_file() and not SKIP.intersection(rel.parts) and path.suffix != ".pyc":
                # Fixed timestamps keep the archive hash stable across rebuilds.
                info = zipfile.ZipInfo(rel.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, path.read_bytes())
    data = archive.read_bytes()
    entry = {key: manifest[key] for key in INDEX_KEYS if key in manifest}
    entry.update(
        archive_url=f"./{archive.name}",
        archive_size=len(data),
        archive_hash=f"sha256:{hashlib.sha256(data).hexdigest()}",
    )
    return entry


def fetch_upstream(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        index = json.load(response)
    return index["data"]


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "_site").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = [
        build_extension(source, out_dir)
        for source in sorted(EXTENSIONS.iterdir())
        if (source / "blender_manifest.toml").is_file()
    ]
    local_ids = {entry["id"] for entry in entries}
    for url in UPSTREAM_INDEXES:
        upstream = fetch_upstream(url)
        clash = local_ids.intersection(entry["id"] for entry in upstream)
        if clash:
            sys.exit(f"Extension id(s) {sorted(clash)} exist both locally and in {url}")
        entries += upstream

    index = {"version": "v1", "blocklist": [], "data": entries}
    (out_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    for entry in entries:
        print(f"{entry['id']} {entry['version']} {entry.get('platforms', ['any'])}")


if __name__ == "__main__":
    main()
