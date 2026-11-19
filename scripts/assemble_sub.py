#!/usr/bin/env python3
"""Assemble binary web assets for a subfolder build (e.g. slime/).

SUBDIR/_chunks/manifest.json lists files. Each entry is either
  - decoded from SUBDIR/_chunks/<name>.b64.* chunks, or
  - copied from a repo-root file ("source"), e.g. the shared Godot engine index.wasm.
Every file is verified by size + sha256 before being written; on success _chunks is removed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(sub: str) -> int:
    subdir = ROOT / sub
    chunks = subdir / "_chunks"
    manifest = chunks / "manifest.json"
    if not manifest.exists():
        print(f"{sub}: no _chunks/manifest.json; nothing to assemble")
        return 0
    for e in json.loads(manifest.read_text()):
        name, size, want = e["name"], e["size"], e["sha256"]
        if "source" in e:
            data = (ROOT / e["source"]).read_bytes()
            how = f"copied from /{e['source']}"
        else:
            parts = sorted(chunks.glob(f"{name}.b64.*"))
            data = b"".join(base64.b64decode(p.read_text().encode("ascii")) for p in parts)
            how = f"decoded from {len(parts)} chunks"
        got = hashlib.sha256(data).hexdigest()
        if len(data) != size or got != want:
            raise SystemExit(f"{sub}/{name}: size {len(data)} sha {got} != expected {size} {want}")
        (subdir / name).write_bytes(data)
        print(f"wrote {sub}/{name} ({size} bytes) {how}")
    shutil.rmtree(chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "slime"))
