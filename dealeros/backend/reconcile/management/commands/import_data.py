
import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand
from reconcile.models import Location, SystemARecord, SystemBEntry
from reconcile.helpers import normalize_ref, parse_amount, clean_text, parse_date


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import CSV data"

    def handle(self, *args, **kwargs):

        data_folder = Path("data")

        # Import Locations
        with open(data_folder / "locations.csv", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):

                Location.objects.update_or_create(
                    location_code=clean_text(row["location_id"]),
                    defaults={
                        "org_id": clean_text(row["org_id"]) or "",
                        "name": clean_text(row["location_name"]) or "",
                    }
                )

        # Import System A
        with open(data_folder / "system_a.csv", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):

                try:
                    location = Location.objects.get(
                        location_code=clean_text(row["location_id"])
                    )

                    reference = normalize_ref(row["record_id"])

                    SystemARecord.objects.update_or_create(
                        location=location,
                        reference=reference,
                        defaults={
                            "event_date": parse_date(row["event_date"]),
                            "category_code": clean_text(row["category_code"]) or "",
                            "actor_id": clean_text(row["actor_id"]) or "",
                            "base_value": parse_amount(row["base_value"]),
                            "adjustment": parse_amount(row["adjustment"]),
                            "amount": parse_amount(row["total_value"]),
                            "state": clean_text(row["state"]) or "",
                            "original_data": row,
                        }
                    )

                except Exception as error:
                    logger.warning("System A row skipped: %s | %s", row, error)

        # Import System B
        with open(data_folder / "system_b.csv", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):

                try:
                    location = Location.objects.get(
                        location_code=clean_text(row["location_id"])
                    )

                    reference = normalize_ref(row["record_ref"])

                    SystemBEntry.objects.update_or_create(
                        location=location,
                        entry_id=clean_text(row["entry_id"]),
                        defaults={
                            "reference": reference,
                            "recorded_on": parse_date(row["recorded_on"]),
                            "amount": parse_amount(row["value"]),
                            "label": clean_text(row["label"]) or "",
                            "original_data": row,
                        }
                    )

                except Exception as error:
                    logger.warning("System B row skipped: %s | %s", row, error)

        self.stdout.write(
            self.style.SUCCESS("CSV import completed successfully!")
        )
