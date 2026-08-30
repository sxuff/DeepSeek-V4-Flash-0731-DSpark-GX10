#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest = ROOT / "SHA256SUMS"
    if not manifest.is_file():
        raise SystemExit("missing SHA256SUMS")
    expected = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest

    actual_files = sorted(
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name != "SHA256SUMS"
    )
    if sorted(expected) != actual_files:
        missing = sorted(set(expected) - set(actual_files))
        extra = sorted(set(actual_files) - set(expected))
        raise SystemExit(f"manifest file-set mismatch: missing={missing}, extra={extra}")

    for name in actual_files:
        digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if digest != expected[name]:
            raise SystemExit(f"SHA-256 mismatch: {name}")
    print(f"SHA256SUMS_OK files={len(actual_files)}")


if __name__ == "__main__":
    main()
