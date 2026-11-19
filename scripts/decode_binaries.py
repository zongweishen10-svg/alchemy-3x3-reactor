#!/usr/bin/env python3
"""Reconstruct binary web assets from chunks/*.b64.* files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "chunks"
MANIFEST = CHUNKS / "manifest.json"


def decode_one(name: str, expected_size: int, expected_sha: str) -> bool:
    dest = ROOT / name
    if dest.exists() and dest.stat().st_size == expected_size:
        actual = hashlib.sha256(dest.read_bytes()).hexdigest()
        if actual == expected_sha:
            print(f"ok exists {name} ({expected_size} bytes)")
            return False  # no write needed
        print(f"hash mismatch for existing {name}: {actual} != {expected_sha}; rebuilding")

    parts = sorted(CHUNKS.glob(f"{name}.b64.*"))
    if not parts:
        if dest.exists():
            actual = hashlib.sha256(dest.read_bytes()).hexdigest()
            if actual == expected_sha:
                print(f"ok exists {name} (no chunks present)")
                return False
        raise SystemExit(f"missing chunks for {name}")

    data = b"".join(__import__("base64").b64decode(p.read_text().encode("ascii")) for p in parts)
    actual = hashlib.sha256(data).hexdigest()
    if len(data) != expected_size or actual != expected_sha:
        raise SystemExit(
            f"decoded {name} failed: size {len(data)} (expected {expected_size}), sha256 {actual} (expected {expected_sha})"
        )
    dest.write_bytes(data)
    print(f"wrote {name} ({len(data)} bytes) from {len(parts)} chunks")
    return True


def main() -> int:
    if not MANIFEST.exists():
        # Already assembled and chunks removed.
        missing = [
            name
            for name in (
                "index.wasm",
                "index.pck",
                "index.png",
                "index.icon.png",
                "index.apple-touch-icon.png",
            )
            if not (ROOT / name).exists()
        ]
        if missing:
            raise SystemExit(f"manifest missing and binaries not found: {missing}")
        print("no chunks/manifest.json; binaries already present")
        return 0

    manifest = json.loads(MANIFEST.read_text())
    wrote_any = False
    for entry in manifest:
        if decode_one(entry["name"], entry["size"], entry["sha256"]):
            wrote_any = True
    print("wrote_any=" + ("true" if wrote_any else "false"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
