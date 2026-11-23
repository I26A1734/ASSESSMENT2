
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from reconcile.helpers import normalize_ref, parse_date


def convert_amount(value):
    if value is None or str(value).strip() == "":
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def normalize_date(value):
    if value is None or str(value).strip() == "":
        return None

    return parse_date(value)


def group_system_b(system_b_entries):
    grouped_entries = defaultdict(list)

    for entry in system_b_entries:
        reference = normalize_ref(entry.get("reference"))

        if reference is not None:
            grouped_entries[reference].append(entry)

    return dict(grouped_entries)


def compare_records(system_a_records, system_b_entries):

    grouped_b = group_system_b(system_b_entries)

    a_references = {
        normalize_ref(record.get("reference"))
        for record in system_a_records
        if normalize_ref(record.get("reference")) is not None
    }

    results = []
    missing_in_b = []
    multiple_matches = []
    unmatched_b = []
    disagreements = []
    ignored_voided = []

    for a_record in system_a_records:

        reference = normalize_ref(a_record.get("reference"))

        # VOIDED records are excluded from reconciliation.
        state = str(a_record.get("state") or "").strip().upper()

        if state == "VOIDED":
            ignored_voided.append(a_record)
            continue

        b_entries = grouped_b.get(reference, []) if reference else []

        a_amount = convert_amount(a_record.get("amount"))

        # No matching B entry.
        if not b_entries:

            result = {
                "reference": reference,
                "system_a": a_record,
                "system_b_entries": [],
                "system_b_count": 0,
                "system_a_amount": a_amount,
                "system_b_total": None,
                "difference": None,
                "amounts_match": None,
                "match_status": "MISSING_IN_B",
            }

            results.append(result)
            missing_in_b.append(result)

            disagreements.append({
                "reference": reference,
                "reason": "MISSING_IN_B",
                "system_a": a_record,
                "system_b_entries": [],
            })

            continue

        b_amounts = [
            convert_amount(entry.get("amount"))
            for entry in b_entries
        ]

        all_b_amounts_valid = all(
            amount is not None for amount in b_amounts
        )

        if all_b_amounts_valid:
            b_total = sum(b_amounts, Decimal("0.00"))
        else:
            b_total = None

        if a_amount is not None and b_total is not None:
            difference = a_amount - b_total
            amounts_match = difference == Decimal("0.00")
        else:
            difference = None
            amounts_match = None

        match_status = (
            "MULTIPLE_MATCHES" if len(b_entries) > 1
            else "SINGLE_MATCH"
        )

        result = {
            "reference": reference,
            "system_a": a_record,
            "system_b_entries": b_entries,
            "system_b_count": len(b_entries),
            "system_a_amount": a_amount,
            "system_b_total": b_total,
            "difference": difference,
            "amounts_match": amounts_match,
            "match_status": match_status,
        }

        results.append(result)

        if len(b_entries) > 1:
            multiple_matches.append(result)

        # VALUE_MISMATCH
        if a_amount is None or not all_b_amounts_valid:

            disagreements.append({
                "reference": reference,
                "reason": "VALUE_MISMATCH",
                "system_a": a_record,
                "system_b_entries": b_entries,
                "system_a_amount": a_amount,
                "system_b_total": b_total,
            })

        elif len(b_entries) > 1 and not amounts_match:

            disagreements.append({
                "reference": reference,
                "reason": "DUPLICATE_IN_B",
                "system_a": a_record,
                "system_b_entries": b_entries,
                "system_a_amount": a_amount,
                "system_b_total": b_total,
                "difference": difference,
            })

        elif len(b_entries) == 1 and not amounts_match:

            disagreements.append({
                "reference": reference,
                "reason": "VALUE_MISMATCH",
                "system_a": a_record,
                "system_b_entries": b_entries,
                "system_a_amount": a_amount,
                "system_b_total": b_total,
                "difference": difference,
            })

        # LOCATION_MISMATCH
        a_location = a_record.get("location_code")

        location_mismatches = [
            entry for entry in b_entries
            if a_location is not None
            and entry.get("location_code") is not None
            and str(a_location).strip() != str(entry.get("location_code")).strip()
        ]

        if location_mismatches:
            disagreements.append({
                "reference": reference,
                "reason": "LOCATION_MISMATCH",
                "system_a": a_record,
                "system_b_entries": location_mismatches,
            })

        # DATE_MISMATCH
        a_date = normalize_date(a_record.get("event_date"))

        date_mismatches = [
            entry for entry in b_entries
            if a_date is not None
            and normalize_date(entry.get("recorded_on")) is not None
            and a_date != normalize_date(entry.get("recorded_on"))
        ]

        if date_mismatches:
            disagreements.append({
                "reference": reference,
                "reason": "DATE_MISMATCH",
                "system_a": a_record,
                "system_b_entries": date_mismatches,
            })

    # ORPHAN_IN_B
    for entry in system_b_entries:

        reference = normalize_ref(entry.get("reference"))

        if reference is None or reference not in a_references:

            unmatched_b.append(entry)

            disagreements.append({
                "reference": reference,
                "reason": "ORPHAN_IN_B",
                "system_a": None,
                "system_b_entries": [entry],
            })

    return {
        "results": results,
        "missing_in_b": missing_in_b,
        "multiple_matches": multiple_matches,
        "unmatched_b": unmatched_b,
        "disagreements": disagreements,
        "ignored_voided": ignored_voided,
    }


def compare_database_records(org_id=None):
    """
    Fetch records from the Django database and pass them
    to the pure Python comparison engine.

    Optionally filter records by organisation.
    """
    from reconcile.models import SystemARecord, SystemBEntry

    system_a_queryset = SystemARecord.objects.select_related("location")
    system_b_queryset = SystemBEntry.objects.select_related("location")

    if org_id:
        system_a_queryset = system_a_queryset.filter(
            location__org_id=org_id
        )
        system_b_queryset = system_b_queryset.filter(
            location__org_id=org_id
        )

    system_a_records = [
        {
            "reference": record.reference,
            "amount": record.amount,
            "location_code": record.location.location_code,
            "event_date": record.event_date,
            "state": record.state,
        }
        for record in system_a_queryset
    ]

    system_b_entries = [
        {
            "reference": entry.reference,
            "amount": entry.amount,
            "location_code": entry.location.location_code,
            "recorded_on": entry.recorded_on,
            "entry_id": entry.entry_id,
        }
        for entry in system_b_queryset
    ]

    return compare_records(system_a_records, system_b_entries)
