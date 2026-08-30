#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

EXPECTED = {
    "model": {
        "bytes": 86720111552,
        "sha256": "73b86c93e7b0be37f68c4b3a5361c7e17f9b278647aa335ea304ac5dfd784867",
    },
    "drafter": {
        "bytes": 6971241504,
        "sha256": "8fa269560dc76fd73e4233ad9b1938b5f65dd363381fd9b1a5c6183f7d12d686",
    },
    "runtime_revision": "d183482b413ecd2e3b540b290e6497437e9fbb73",
    "measured_binary_sha256": "0289d6522e5ee15cb5082e0903cadecca4d9010d287a3ad187c34f274f9bd2cb",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(16 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def verify_file(label: str, path: Path) -> dict:
    expected = EXPECTED[label]
    size = path.stat().st_size
    digest = sha256(path)
    if size != expected["bytes"]:
        raise SystemExit(f"{label} size mismatch: {size} != {expected['bytes']}")
    if digest != expected["sha256"]:
        raise SystemExit(f"{label} SHA-256 mismatch: {digest}")
    return {"path": str(path), "bytes": size, "sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--drafter", required=True, type=Path)
    parser.add_argument("--require-measured-binary-hash", action="store_true")
    args = parser.parse_args()

    revision = subprocess.run(
        ["git", "-C", str(args.runtime_dir), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if revision != EXPECTED["runtime_revision"]:
        raise SystemExit(f"runtime revision mismatch: {revision}")

    binary = args.runtime_dir / "ds4-server"
    if not binary.is_file():
        raise SystemExit(f"missing runtime binary: {binary}")
    binary_hash = sha256(binary)
    if args.require_measured_binary_hash and binary_hash != EXPECTED["measured_binary_sha256"]:
        raise SystemExit(f"runtime binary SHA-256 mismatch: {binary_hash}")

    result = {
        "status": "verified",
        "runtime_revision": revision,
        "runtime_binary_sha256": binary_hash,
        "runtime_binary_matches_measured_build": binary_hash == EXPECTED["measured_binary_sha256"],
        "model": verify_file("model", args.model),
        "drafter": verify_file("drafter", args.drafter),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
