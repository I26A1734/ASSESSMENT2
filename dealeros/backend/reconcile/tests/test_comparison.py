
from decimal import Decimal

from django.test import SimpleTestCase

from reconcile.comparison import compare_records


class ComparisonEngineTest(SimpleTestCase):

    def test_clean_matching_records(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [{"reference": "REC-1001", "amount": "1000"}]

        result = compare_records(a, b)

        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["amounts_match"], True)
        self.assertEqual(result["disagreements"], [])

    def test_missing_in_b(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]

        result = compare_records(a, [])

        self.assertEqual(result["disagreements"][0]["reason"], "MISSING_IN_B")

    def test_orphan_in_b(self):
        b = [{"reference": "REC-9999", "amount": "100"}]

        result = compare_records([], b)

        self.assertEqual(result["disagreements"][0]["reason"], "ORPHAN_IN_B")

    def test_valid_split_entries(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [
            {"reference": "REC-1001", "amount": "400"},
            {"reference": "REC-1001", "amount": "600"},
        ]

        result = compare_records(a, b)

        self.assertTrue(result["results"][0]["amounts_match"])
        self.assertNotIn(
            "DUPLICATE_IN_B",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_duplicate_in_b(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [
            {"reference": "REC-1001", "amount": "400"},
            {"reference": "REC-1001", "amount": "500"},
        ]

        result = compare_records(a, b)

        self.assertIn(
            "DUPLICATE_IN_B",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_value_mismatch(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [{"reference": "REC-1001", "amount": "900"}]

        result = compare_records(a, b)

        self.assertIn(
            "VALUE_MISMATCH",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_blank_b_amount(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [{"reference": "REC-1001", "amount": None}]

        result = compare_records(a, b)

        self.assertIn(
            "VALUE_MISMATCH",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_messy_reference_normalization(self):
        a = [{"reference": "REC-1001", "amount": "1000"}]
        b = [{"reference": " rec - 1001 ", "amount": "1000"}]

        result = compare_records(a, b)

        self.assertTrue(result["results"][0]["amounts_match"])
        self.assertEqual(result["disagreements"], [])

    def test_location_mismatch(self):
        a = [{
            "reference": "REC-1001",
            "amount": "1000",
            "location_code": "LOC-101",
        }]
        b = [{
            "reference": "REC-1001",
            "amount": "1000",
            "location_code": "LOC-201",
        }]

        result = compare_records(a, b)

        self.assertIn(
            "LOCATION_MISMATCH",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_date_mismatch(self):
        a = [{
            "reference": "REC-1001",
            "amount": "1000",
            "event_date": "2026-04-03",
        }]
        b = [{
            "reference": "REC-1001",
            "amount": "1000",
            "recorded_on": "2026-04-05",
        }]

        result = compare_records(a, b)

        self.assertIn(
            "DATE_MISMATCH",
            [item["reason"] for item in result["disagreements"]]
        )

    def test_voided_record_is_ignored(self):
        a = [{
            "reference": "REC-1001",
            "amount": "1000",
            "state": "VOIDED",
        }]

        result = compare_records(a, [])

        self.assertEqual(len(result["ignored_voided"]), 1)
        self.assertEqual(len(result["results"]), 0)
        self.assertEqual(result["disagreements"], [])
