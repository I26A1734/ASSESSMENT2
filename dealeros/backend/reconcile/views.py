
from decimal import Decimal, InvalidOperation

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from reconcile.models import Location
from reconcile.comparison import compare_database_records


VALID_REASONS = {
    "MISSING_IN_B",
    "ORPHAN_IN_B",
    "DUPLICATE_IN_B",
    "VALUE_MISMATCH",
    "LOCATION_MISMATCH",
    "DATE_MISMATCH",
}


def get_disagreement_value(disagreement):
    """
    Get a common amount value for sorting disagreements.
    """
    value = disagreement.get("system_a_amount")

    if value is None:
        system_a = disagreement.get("system_a")

        if system_a:
            value = system_a.get("amount")

    if value is None:
        system_b_entries = disagreement.get("system_b_entries", [])

        value = sum(
            (
                Decimal(str(entry["amount"]))
                for entry in system_b_entries
                if entry.get("amount") is not None
            ),
            Decimal("0")
        )

    try:
        return Decimal(str(value)) if value is not None else Decimal("0")
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


@api_view(["GET"])
def disagreement_list(request):

    org = request.query_params.get("org")
    reason = request.query_params.get("reason")
    sort = request.query_params.get("sort")

    # Validate organisation
    if org and not Location.objects.filter(org_id=org).exists():
        return Response(
            {"error": "Invalid organisation"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate disagreement reason
    if reason and reason not in VALID_REASONS:
        return Response(
            {"error": "Invalid disagreement reason"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate sorting
    if sort and sort not in ["value", "-value"]:
        return Response(
            {"error": "Invalid sort parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Fetch comparison results
    comparison = compare_database_records(org_id=org)

    disagreements = comparison["disagreements"]

    # Filter by reason
    if reason:
        disagreements = [
            item for item in disagreements
            if item["reason"] == reason
        ]

    # Add a common value field
    for item in disagreements:
        item["value"] = get_disagreement_value(item)

    # Sort by value
    if sort:
        disagreements.sort(
            key=lambda item: item["value"],
            reverse=(sort == "-value")
        )

    return Response({
        "count": len(disagreements),
        "disagreements": disagreements
    })
