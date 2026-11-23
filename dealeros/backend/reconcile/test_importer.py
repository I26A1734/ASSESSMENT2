
from django.test import TestCase
from reconcile.models import Location, SystemARecord, SystemBEntry


class ImportDataTest(TestCase):

    def setUp(self):
        self.location = Location.objects.create(
            name="Chennai",
            org_id="DealerOS"
        )

        SystemARecord.objects.create(
            location=self.location,
            reference="REC-1034",
            amount="125400.00",
            original_data={
                "reference": "rec1034",
                "amount": "125400.00"
            }
        )

        SystemBEntry.objects.create(
            location=self.location,
            entry_id="ENTRY-1034",
            reference="REC-1034",
            amount="125400.00",
            original_data={
                "reference": "REC-1034",
                "amount": "125400.00"
            }
        )

    def test_record_counts(self):
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(SystemARecord.objects.count(), 1)
        self.assertEqual(SystemBEntry.objects.count(), 1)

    def test_blank_amounts(self):
        self.assertEqual(
            SystemARecord.objects.filter(amount=None).count(), 0
        )

    def test_normalized_reference(self):
        record = SystemARecord.objects.first()
        self.assertEqual(record.reference, "REC-1034")

    def test_original_data(self):
        record = SystemARecord.objects.first()
        self.assertEqual(record.original_data["reference"], "rec1034")

    def test_no_duplicate_records(self):
        SystemARecord.objects.update_or_create(
            location=self.location,
            reference="REC-1034",
            defaults={"amount": "125400.00"}
        )

        self.assertEqual(SystemARecord.objects.count(), 1)
