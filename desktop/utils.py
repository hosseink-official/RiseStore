import jdatetime
from datetime import datetime, date


def to_jalali(d: date | datetime | str | None) -> jdatetime.date | None:
    if not d:
        return None
    if isinstance(d, str):
        d = datetime.strptime(d[:10], '%Y-%m-%d').date()
    if isinstance(d, datetime):
        d = d.date()
    return jdatetime.date.fromgregorian(date=d)


def format_date(d: date | datetime | str | None, sep: str = '/') -> str:
    j = to_jalali(d)
    if not j:
        return '-'
    return f'{j.year}{sep}{j.month:02d}{sep}{j.day:02d}'


def format_datetime(d: datetime | str | None) -> str:
    if not d:
        return '-'
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    j = to_jalali(d)
    if not j:
        return '-'
    return f'{j.year}/{j.month:02d}/{j.day:02d} {d.hour:02d}:{d.minute:02d}'


def to_gregorian_iso(jy: int, jm: int, jd: int) -> str:
    g = jdatetime.jalali_to_gregorian(jy, jm, jd)
    return f'{g[0]:04d}-{g[1]:02d}-{g[2]:02d}'


def today_iso() -> str:
    return date.today().isoformat()


def today_jalali(sep: str = '/') -> str:
    j = jdatetime.date.today()
    return f'{j.year}{sep}{j.month:02d}{sep}{j.day:02d}'


def format_number(n: int | float | None) -> str:
    if n is None:
        return '0'
    return f'{n:,}'
