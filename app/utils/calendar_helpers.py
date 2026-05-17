from calendar import monthrange
from datetime import date, timedelta


MONTH_NAMES = (
    "",
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
)


def month_bounds(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    next_month = last_day + timedelta(days=1)
    return first_day, last_day, next_month


def month_navigation(year, month):
    first_day = date(year, month, 1)
    prev_day = first_day - timedelta(days=1)
    next_day = month_bounds(year, month)[2]
    return prev_day.year, prev_day.month, next_day.year, next_day.month
