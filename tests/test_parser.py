"""Tests for the Auckland Council collection page parser."""

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

PARSER_PATH = (
    Path(__file__).parents[1] / "custom_components" / "akl_bin_collection" / "parser.py"
)
SPEC = importlib.util.spec_from_file_location("akl_bin_collection_parser", PARSER_PATH)
assert SPEC is not None and SPEC.loader is not None
PARSER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PARSER
SPEC.loader.exec_module(PARSER)

CollectionPageError = PARSER.CollectionPageError
parse_collection_date = PARSER.parse_collection_date
parse_collection_page = PARSER.parse_collection_page


SAMPLE_PAGE = """
<html><body>
  <h2>
    <span>12 Example Street</span>
    <span>Suburbia, Auckland 1010</span>
  </h2>
  <div class="acpl-schedule-card">
    <h4 class="card-title h4">Household collection</h4>
    <p class="mb-0 lead">
      <span class="acpl-icon-with-attribute left">
        <i class="acpl-icon rubbish"></i>
        <span>Rubbish: <b>Tuesday, 28 July</b></span>
      </span>
    </p>
    <p class="mb-0 lead">
      <span class="acpl-icon-with-attribute left">
        <i class="acpl-icon food-waste"></i>
        <span>Food scraps: <b>Tuesday, 28 July</b></span>
      </span>
    </p>
    <p class="mb-0 lead">
      <span class="acpl-icon-with-attribute left">
        <i class="acpl-icon recycle"></i>
        <span>Recycling: <b>Tuesday, 4 August</b></span>
      </span>
    </p>
  </div>
  <div class="acpl-schedule-card">
    <h4 class="card-title h4">Commercial collection</h4>
    <span class="acpl-icon-with-attribute left">
      <i class="acpl-icon rubbish"></i><b>Monday, 27 July</b>
    </span>
  </div>
</body></html>
"""


class CollectionPageParserTests(unittest.TestCase):
    def test_parses_household_dates_and_address(self) -> None:
        result = parse_collection_page(SAMPLE_PAGE, date(2026, 7, 27))

        self.assertEqual(
            result.address,
            "12 Example Street Suburbia, Auckland 1010",
        )
        self.assertEqual(result.dates["rubbish"], date(2026, 7, 28))
        self.assertEqual(result.dates["food_scraps"], date(2026, 7, 28))
        self.assertEqual(result.dates["recycling"], date(2026, 8, 4))

    def test_missing_collection_type_is_none(self) -> None:
        result = parse_collection_page(
            SAMPLE_PAGE.replace(
                '<i class="acpl-icon food-waste"></i>',
                '<i class="acpl-icon unknown"></i>',
            ),
            date(2026, 7, 27),
        )

        self.assertIsNone(result.dates["food_scraps"])

    def test_date_rolls_into_next_year(self) -> None:
        self.assertEqual(
            parse_collection_date("Friday, 2 January", date(2026, 12, 29)),
            date(2027, 1, 2),
        )

    def test_rejects_page_without_household_card(self) -> None:
        with self.assertRaises(CollectionPageError):
            parse_collection_page("<html><body>No schedule</body></html>", date.today())


if __name__ == "__main__":
    unittest.main()
