#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--arm", choices=["plain", "dspark"], required=True)
    args = parser.parse_args()

    text = args.log.read_text(errors="replace")
    if "persistent batch ctx ready" not in text:
        raise SystemExit("persistent batch context did not activate")
    if "speculative decode is ARMED but has no engine to run on" in text:
        raise SystemExit("speculation loaded without an execution engine")
    if args.arm == "dspark" and "DSpark drafter loaded" not in text:
        raise SystemExit("DSpark drafter activation was not observed")
    print(f"STARTUP_OK arm={args.arm}")


if __name__ == "__main__":
    main()
