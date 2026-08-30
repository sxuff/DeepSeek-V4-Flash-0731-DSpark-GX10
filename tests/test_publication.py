from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = [
    "/home/sxuf",
    "/opt/data",
    "gx10-fe09",
    "100.65.244.79",
    "PRIVATE KEY",
    "HF_TOKEN=",
    "API_KEY=",
]


class PublicationHygieneTests(unittest.TestCase):
    def test_no_private_paths_hosts_or_credentials(self) -> None:
        findings = []
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ".git" in path.parts
                or "__pycache__" in path.parts
                or path.suffix == ".pyc"
                or path.name == "test_publication.py"
            ):
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            for token in BLOCKED:
                if token in text:
                    findings.append(f"{path.relative_to(ROOT)}: {token}")
        self.assertEqual(findings, [])

    def test_no_internal_editorial_or_raw_logs(self) -> None:
        names = {path.name for path in ROOT.rglob("*") if path.is_file()}
        self.assertNotIn("POSTS.md", names)
        self.assertFalse(any(name.endswith(".log") for name in names))
        self.assertFalse((ROOT / "run").exists())

    def test_readme_card_reference_is_live(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertIn("card.png", readme)
        self.assertNotIn("result-card.png", readme)
        self.assertTrue((ROOT / "card.png").is_file())
        self.assertIn("Quality boundary", readme)


if __name__ == "__main__":
    unittest.main()
