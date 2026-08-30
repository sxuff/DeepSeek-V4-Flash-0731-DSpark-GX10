from __future__ import annotations

import json
import hashlib
import math
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResultContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = json.loads((ROOT / "results/analysis.json").read_text())
        cls.receipt = json.loads((ROOT / "results/structured-json-receipt.json").read_text())
        cls.card = json.loads((ROOT / "card-values.json").read_text())

    def test_headline_values_match_receipt(self) -> None:
        plain = self.receipt["plain"]["median_served_wall_tok_s"]
        dspark = self.receipt["dspark"]["median_served_wall_tok_s"]
        ratio = self.receipt["speedup_x"]
        self.assertAlmostEqual(plain, 21.322550405748803)
        self.assertAlmostEqual(dspark, 46.38977337700436)
        self.assertAlmostEqual(ratio, dspark / plain)
        self.assertEqual(self.card["plain_baseline"], "21.32")
        self.assertEqual(self.card["dspark_median"], "46.39")
        self.assertEqual(self.card["speedup"], "2.18×")

    def test_three_matched_runs(self) -> None:
        self.assertEqual(len(self.receipt["plain"]["served_wall_tok_s_runs"]), 3)
        self.assertEqual(len(self.receipt["dspark"]["served_wall_tok_s_runs"]), 3)
        self.assertEqual(self.receipt["request_payload_hash_matches"], 3)
        self.assertEqual(self.receipt["exact_output_hash_matches"], 3)
        self.assertEqual(self.receipt["plain"]["completion_tokens"], [611, 611, 611])
        self.assertEqual(self.receipt["dspark"]["completion_tokens"], [611, 611, 611])

    def test_broader_claim_boundary_is_retained(self) -> None:
        quality = self.analysis["quality"]
        self.assertEqual((quality["plain_semantic_passes"], quality["plain_semantic_total"]), (21, 24))
        self.assertEqual((quality["dspark_semantic_passes"], quality["dspark_semantic_total"]), (18, 24))
        self.assertEqual(quality["repeated_dspark_only_regression"]["dspark_last_integer"], 18713)
        self.assertEqual(self.analysis["protocol_verdict"], "NO_GO_FOR_QUALITY_NEUTRAL_DEPLOYMENT_CLAIM")
        self.assertIn("broader protocol", self.card["mandatory_repo_disclosure"].lower())

    def test_safety_and_activation(self) -> None:
        safety = self.analysis["safety"]
        self.assertGreaterEqual(safety["plain_minimum_mem_available_gib"], 6)
        self.assertGreaterEqual(safety["dspark_minimum_mem_available_gib"], 6)
        self.assertLessEqual(safety["plain_maximum_swap_growth_mib"], 512)
        self.assertLessEqual(safety["dspark_maximum_swap_growth_mib"], 512)
        self.assertEqual(safety["watchdog_incidents"], 0)
        self.assertTrue(self.analysis["dspark"]["continuous_path_confirmed"])
        self.assertEqual(self.analysis["dspark"]["fallback_requests"], 0)

    def test_final_card_identity(self) -> None:
        data = (ROOT / "card.png").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.card["final_card"]["sha256"])
        self.assertEqual(len(data), self.card["final_card"]["bytes"])
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (1472, 1158))


if __name__ == "__main__":
    unittest.main()
