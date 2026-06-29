import tkinter as tk
import re
import jdatetime
from datetime import datetime, date

_PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
_ENGLISH_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')


def persian_digits(s: str | int) -> str:
    return str(s).translate(_PERSIAN_DIGITS)


def clean_number(s: str) -> str:
    return s.translate(_ENGLISH_DIGITS).replace(',', '').strip()


def make_dialog(parent, title, width, height):
    root = parent.winfo_toplevel()
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry(f'{width}x{height}')
    win.transient(root)
    win.attributes('-topmost', True)
    win.after(100, lambda: win.attributes('-topmost', False))

    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - width) // 2
    y = root.winfo_y() + (root.winfo_height() - height) // 2
    win.geometry(f'+{x}+{y}')
    win._dx = x - root.winfo_x()
    win._dy = y - root.winfo_y()

    def _repos(*args):
        try:
            win.geometry(f'+{root.winfo_x() + win._dx}+{root.winfo_y() + win._dy}')
        except tk.TclError:
            pass

    root.bind('<Configure>', _repos, add='+')
    return win


def validate_phone(phone: str) -> str:
    phone = clean_number(phone)
    phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    if phone:
        if len(phone) != 11 or not phone.startswith('0'):
            raise ValueError('شماره تماس باید ۱۱ رقمی و با ۰ شروع شود')
    return phone


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
    g = jdatetime.JalaliToGregorian(jy, jm, jd).getGregorianList()
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


def persian_askinteger(title, prompt, minvalue=1, maxvalue=9999, parent=None):
    return _ask_number(title, prompt, minvalue, maxvalue, parent, is_float=False)


def persian_askfloat(title, prompt, minvalue=1, maxvalue=9999, parent=None):
    return _ask_number(title, prompt, minvalue, maxvalue, parent, is_float=True)


def _ask_number(title, prompt, minvalue, maxvalue, parent, is_float):
    import tkinter as tk
    from tkinter import ttk
    from desktop.theme import Colors

    win = make_dialog(parent, title, 380, 250)
    win.configure(bg=Colors.card)
    win.resizable(False, False)
    win.grab_set()

    result = [None]

    header = tk.Frame(win, bg=Colors.accent, height=36)
    header.pack(fill='x')
    header.pack_propagate(False)
    tk.Label(header, text=title, font=('TkDefaultFont', 10, 'bold'),
             bg=Colors.accent, fg='#ffffff').pack(expand=True)

    body = tk.Frame(win, bg=Colors.card, padx=24, pady=16)
    body.pack(fill='both', expand=True)

    prompt_label = tk.Label(body, text=prompt, font=('TkDefaultFont', 10),
                            bg=Colors.card, fg=Colors.text_primary)
    prompt_label.pack(anchor='e', pady=(0, 4))

    range_text = f'حداقل: {persian_digits(f"{minvalue:,}")}  —  حداکثر: {persian_digits(f"{maxvalue:,}")}'
    tk.Label(body, text=range_text,
             font=('TkDefaultFont', 8), bg=Colors.card, fg=Colors.text_muted).pack(anchor='e', pady=(0, 8))

    var = tk.StringVar()
    entry = tk.Entry(body, textvariable=var, font=('TkDefaultFont', 14),
                     bd=1, relief='solid', highlightbackground=Colors.border,
                     highlightcolor=Colors.accent, highlightthickness=1,
                     justify='center')
    entry.pack(fill='x', ipady=6, pady=(0, 4))
    entry.focus_set()
    add_number_comma_formatting(var, entry)

    warn_label = tk.Label(body, text='', font=('TkDefaultFont', 9),
                          bg=Colors.card, fg=Colors.danger)
    warn_label.pack(anchor='e', pady=(0, 8))

    def validate(val):
        if val > maxvalue:
            warn_label.config(text=f'حداکثر مقدار مجاز: {persian_digits(str(maxvalue))}')
            return False
        if val < minvalue:
            warn_label.config(text=f'حداقل مقدار مجاز: {persian_digits(str(minvalue))}')
            return False
        warn_label.config(text='')
        return True

    def submit():
        raw = clean_number(var.get())
        try:
            val = float(raw) if is_float else int(raw)
        except ValueError:
            val = minvalue
        if not validate(val):
            return
        result[0] = val
        win.destroy()

    def cancel():
        win.destroy()

    entry.bind('<Return>', lambda e: submit())

    btn_frame = tk.Frame(body, bg=Colors.card)
    btn_frame.pack(fill='x')
    tk.Button(btn_frame, text='✅  تأیید', font=('TkDefaultFont', 10),
              bg=Colors.accent, fg='#ffffff', bd=0, cursor='hand2',
              padx=20, pady=6, activebackground=Colors.accent_hover,
              command=submit).pack(side='left')
    tk.Button(btn_frame, text='✕  انصراف', font=('TkDefaultFont', 10),
              bg=Colors.text_muted, fg='#ffffff', bd=0, cursor='hand2',
              padx=14, pady=6, activebackground=Colors.border,
              command=cancel).pack(side='left', padx=(8, 0))

    win.protocol('WM_DELETE_WINDOW', cancel)
    win.wait_window()
    return result[0]


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
            if '.' in raw:
                parts = raw.split('.')
                formatted = persian_digits(f'{int(parts[0]):,}') + '.' + persian_digits(parts[1])
            else:
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
