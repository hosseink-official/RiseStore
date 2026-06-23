import jdatetime
from datetime import datetime, date

_PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
_ENGLISH_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')


def persian_digits(s: str | int) -> str:
    return str(s).translate(_PERSIAN_DIGITS)


def clean_number(s: str) -> str:
    return s.translate(_ENGLISH_DIGITS).replace(',', '').strip()


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
    return persian_digits(f'{j.year}{sep}{j.month:02d}{sep}{j.day:02d}')


def format_datetime(d: datetime | str | None) -> str:
    if not d:
        return '-'
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    j = to_jalali(d)
    if not j:
        return '-'
    return persian_digits(f'{j.year}/{j.month:02d}/{j.day:02d} {d.hour:02d}:{d.minute:02d}')


def to_gregorian_iso(jy: int, jm: int, jd: int) -> str:
    g = jdatetime.jalali_to_gregorian(jy, jm, jd)
    return f'{g[0]:04d}-{g[1]:02d}-{g[2]:02d}'


def today_iso() -> str:
    return date.today().isoformat()


def today_jalali(sep: str = '/') -> str:
    j = jdatetime.date.today()
    return persian_digits(f'{j.year}{sep}{j.month:02d}{sep}{j.day:02d}')


def format_number(n: int | float | None) -> str:
    if n is None:
        return persian_digits('0')
    return persian_digits(f'{n:,}')


def add_number_comma_formatting(var, entry=None):
    import tkinter as tk

    def _format():
        value = var.get()
        if not value or value == '-':
            return
        try:
            cursor_pos = entry.index(tk.INSERT) if entry else 0
            digits_before = len(''.join(c for c in value[:cursor_pos] if c.isdigit()))
            raw = clean_number(value)
            formatted = persian_digits(f'{int(raw):,}')
            if formatted != value:
                var.set(formatted)
                if entry:
                    count = 0
                    new_pos = 0
                    for i, ch in enumerate(formatted):
                        if ch.isdigit():
                            count += 1
                        if count > digits_before:
                            new_pos = i
                            break
                    else:
                        new_pos = len(formatted)
                    entry.icursor(new_pos)
        except ValueError:
            pass

    def _schedule(*args):
        entry.after_idle(_format)

    if entry:
        var.trace_add('write', _schedule)
