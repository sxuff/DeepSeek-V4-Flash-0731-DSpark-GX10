from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProtocolContractTests(unittest.TestCase):
    def test_protocol_and_manifests_agree(self) -> None:
        protocol = json.loads((ROOT / "protocol/PROTOCOL.json").read_text())
        target = json.loads((ROOT / "manifests/target.json").read_text())
        drafter = json.loads((ROOT / "manifests/drafter.json").read_text())
        runtime = json.loads((ROOT / "manifests/runtime.json").read_text())
        self.assertEqual(protocol["frozen_inputs"]["target"], target)
        self.assertEqual(protocol["frozen_inputs"]["drafter"], drafter)
        self.assertEqual(protocol["frozen_inputs"]["runtime"], runtime)
        self.assertEqual(protocol["request_contract"]["repetitions_per_fixture"], 3)
        self.assertTrue(protocol["request_contract"]["matched_request_bytes"])
        self.assertTrue(protocol["eligibility"]["continuous_path_required"])
        self.assertEqual(protocol["eligibility"]["fallback_requests_required"], 0)

    def test_exact_identity(self) -> None:
        target = json.loads((ROOT / "manifests/target.json").read_text())
        drafter = json.loads((ROOT / "manifests/drafter.json").read_text())
        runtime = json.loads((ROOT / "manifests/runtime.json").read_text())
        self.assertEqual(target["sha256"], "73b86c93e7b0be37f68c4b3a5361c7e17f9b278647aa335ea304ac5dfd784867")
        self.assertEqual(drafter["sha256"], "8fa269560dc76fd73e4233ad9b1938b5f65dd363381fd9b1a5c6183f7d12d686")
        self.assertEqual(runtime["revision"], "d183482b413ecd2e3b540b290e6497437e9fbb73")


if __name__ == "__main__":
    unittest.main()
