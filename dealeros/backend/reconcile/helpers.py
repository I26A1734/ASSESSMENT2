
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime


def clean_text(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def normalize_ref(value):
    value = clean_text(value)

    if not value:
        return None

    value = re.sub(r'[\s-]+', '', value).upper()

    if value.isdigit():
        return "REC-" + value

    if value.startswith("REC"):
        return "REC-" + value[3:]

    return value


def parse_amount(value):
    value = clean_text(value)

    if not value:
        return None

    value = value.replace(",", "")

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_date(value):
    value = clean_text(value)

    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None
