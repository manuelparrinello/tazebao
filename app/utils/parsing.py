from datetime import date, datetime


def parse_optional_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_optional_datetime(value):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def parse_optional_id(value):
    if value in (None, ""):
        return None
    return int(value)


def parse_optional_float(value):
    if value in (None, ""):
        return 0
    return float(str(value).replace(",", "."))
