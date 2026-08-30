#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--out", default="analysis.json")
    args = parser.parse_args()

    rows = {arm: load_jsonl(args.run / arm / "rows.jsonl") for arm in ("plain", "dspark")}
    for arm, selected in rows.items():
        if len(selected) != 36:
            raise SystemExit(f"{arm}: expected 36 rows, observed {len(selected)}")
        if any(row.get("error") for row in selected):
            raise SystemExit(f"{arm}: runtime error row present")

    pmap = {(r["kind"], r["fixture_id"], r["rep"]): r for r in rows["plain"]}
    dmap = {(r["kind"], r["fixture_id"], r["rep"]): r for r in rows["dspark"]}
    if pmap.keys() != dmap.keys():
        raise SystemExit("paired row keys differ")
    if not all(pmap[key]["request_sha256"] == dmap[key]["request_sha256"] for key in pmap):
        raise SystemExit("paired request payload hashes differ")

    fixture_ids = sorted({r["fixture_id"] for r in rows["plain"] if r["kind"] == "speed"})
    fixtures = []
    ratios = []
    for fixture_id in fixture_ids:
        plain_runs = [r["wall_tokens_per_second"] for r in rows["plain"] if r["kind"] == "speed" and r["fixture_id"] == fixture_id]
        dspark_runs = [r["wall_tokens_per_second"] for r in rows["dspark"] if r["kind"] == "speed" and r["fixture_id"] == fixture_id]
        plain_median = statistics.median(plain_runs)
        dspark_median = statistics.median(dspark_runs)
        ratio = dspark_median / plain_median
        ratios.append(ratio)
        fixtures.append({
            "fixture_id": fixture_id,
            "plain_runs": plain_runs,
            "dspark_runs": dspark_runs,
            "plain_median_served_wall_tok_s": plain_median,
            "dspark_median_served_wall_tok_s": dspark_median,
            "speedup_x": ratio,
        })

    weighted = {}
    for arm in rows:
        speed_rows = [r for r in rows[arm] if r["kind"] == "speed"]
        weighted[arm] = sum(r["completion_tokens"] for r in speed_rows) / sum(r["elapsed_seconds"] for r in speed_rows)

    semantic = json.loads((args.run / "semantic-rescore-summary.json").read_text())
    result = {
        "schema": "deepseek-v4-flash-0731-dspark-analysis-v1",
        "rows_per_arm": {arm: len(selected) for arm, selected in rows.items()},
        "paired_request_hash_matches": len(pmap),
        "exact_output_hash_matches": sum(pmap[key]["output_sha256"] == dmap[key]["output_sha256"] for key in pmap),
        "fixtures": fixtures,
        "geometric_mean_fixture_speedup_x": math.prod(ratios) ** (1 / len(ratios)),
        "weighted_served_wall_tok_s": weighted,
        "weighted_speedup_x": weighted["dspark"] / weighted["plain"],
        "quality": semantic,
        "quality_neutral_go": semantic["dspark"]["quality_passes"] >= semantic["plain"]["quality_passes"] - 1,
    }
    output = args.run / args.out
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
