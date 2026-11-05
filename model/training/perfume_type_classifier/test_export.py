"""Small synthetic compatibility check; no customer data or saved weights required."""

import tempfile
import unittest
from pathlib import Path

from model import PerfumeTypeModel


class ExportTests(unittest.TestCase):
    def test_export_matches_sklearn_on_unigrams_bigrams_and_repeated_tokens(self) -> None:
        texts = [
            "rose amber",
            "rose rose amber",
            "rose musk",
            "citrus lime",
            "citrus citrus lime",
            "citrus lemon",
            "wood cedar",
            "wood wood cedar",
            "wood oak",
        ]
        labels = ["ДУХИ"] * 3 + ["ОДЕКОЛОН"] * 3 + ["ТУАЛЕТНАЯ ВОДА"] * 3
        model = PerfumeTypeModel().fit(texts, labels)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / ".venv") as temporary:
            path = model.export(Path(temporary), texts + ["rose lime", "wood amber", "unknown"])
            self.assertTrue(path.is_file())
            self.assertTrue(path.with_suffix(".json.sha256").is_file())


if __name__ == "__main__":
    unittest.main()
