import math
from desktop.utils import persian_digits


def draw_label(canvas, x, y, text, color='#475569', font_size=8, anchor='center'):
    canvas.create_text(x, y, text=str(text), fill=color,
                       font=('TkDefaultFont', font_size), anchor=anchor)


def draw_bar_chart(canvas, data, x0, y0, x1, y1, title='', bar_color='#6366f1',
                   max_value=None, show_values=True):
    w = x1 - x0
    h = y1 - y0
    title_h = 24 if title else 0
    pad_left = 40
    pad_right = 8
    pad_top = title_h + 4
    pad_bottom = 28

    chart_x0 = x0 + pad_left
    chart_y0 = y0 + pad_top
    chart_x1 = x1 - pad_right
    chart_y1 = y1 - pad_bottom

    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0

    if title:
        draw_label(canvas, (x0 + x1) / 2, y0 + title_h / 2, title,
                   color='#0f172a', font_size=10, anchor='center')

    if not data:
        draw_label(canvas, (x0 + x1) / 2, (y0 + y1) / 2, 'داده‌ای موجود نیست',
                   color='#94a3b8', font_size=9, anchor='center')
        return

    values = [v for _, v in data]
    if max_value is None:
        max_value = max(values) if values else 1
    if max_value <= 0:
        max_value = 1

    n = len(data)
    bar_gap = max(4, chart_w * 0.08 / max(n, 1))
    bar_w = max(6, (chart_w - bar_gap * (n + 1)) / n)

    canvas.create_line(chart_x0, chart_y0, chart_x0, chart_y1, fill='#cbd5e1', width=1)
    canvas.create_line(chart_x0, chart_y1, chart_x1, chart_y1, fill='#cbd5e1', width=1)

    y_ticks = 4
    for i in range(y_ticks + 1):
        frac = i / y_ticks
        y = chart_y1 - frac * chart_h
        val = int(max_value * frac)
        label = persian_digits(f'{val:,}')
        draw_label(canvas, chart_x0 - 6, y, label, color='#94a3b8', font_size=7, anchor='e')
        if i > 0:
            canvas.create_line(chart_x0 + 2, y, chart_x1, y, fill='#f1f5f9', width=1)

    for i, (label, val) in enumerate(data):
        x = chart_x0 + bar_gap + i * (bar_w + bar_gap)
        bar_h = (val / max_value) * chart_h
        canvas.create_rectangle(x, chart_y1 - bar_h, x + bar_w, chart_y1,
                                fill=bar_color, outline='', width=0)

        if show_values and val > 0:
            canvas.create_text(x + bar_w / 2, chart_y1 - bar_h - 4,
                               text=persian_digits(f'{val:,}'), fill=bar_color,
                               font=('TkDefaultFont', 7), anchor='s')

        label_text = label if len(str(label)) <= 6 else str(label)[:5] + '..'
        canvas.create_text(x + bar_w / 2, chart_y1 + 8, text=label_text,
                           fill='#475569', font=('TkDefaultFont', 7), anchor='n')

    canvas.create_text(x0 + pad_left / 2, (chart_y0 + chart_y1) / 2,
                       text=title, fill='#94a3b8', font=('TkDefaultFont', 7),
                       anchor='c', angle=90)


def draw_pie_chart(canvas, data, cx, cy, radius, title='', hole_r=0):
    total = sum(v for _, v, _ in data)
    if total <= 0:
        draw_label(canvas, cx, cy, 'داده‌ای موجود نیست',
                   color='#94a3b8', font_size=9, anchor='center')
        return

    if title:
        draw_label(canvas, cx, cy - radius - 16, title,
                   color='#0f172a', font_size=10, anchor='center')

    start_angle = 90
    for label, val, color in data:
        extent = -360 * (val / total)
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                          start=start_angle, extent=extent, fill=color,
                          outline='#ffffff', width=2)
        start_angle += extent

    if hole_r > 0:
        canvas.create_oval(cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r,
                           fill='#ffffff', outline='')

    mid_angle = 90
    for label, val, color in data:
        extent = -360 * (val / total)
        label_angle = math.radians(mid_angle + extent / 2)
        lx = cx + (radius + 14) * math.cos(label_angle)
        ly = cy - (radius + 14) * math.sin(label_angle)
        pct = round(val / total * 100)
        canvas.create_text(lx, ly, text=f'{label} {persian_digits(pct)}%',
                           fill='#475569', font=('TkDefaultFont', 8), anchor='center')
        mid_angle += extent


def draw_hbar_chart(canvas, data, x0, y0, x1, y1, title='', bar_color='#10b981',
                    max_value=None, show_values=True):
    w = x1 - x0
    h = y1 - y0
    title_h = 24 if title else 0
    pad_left = 8
    pad_right = 50
    pad_top = title_h + 4
    pad_bottom = 28

    chart_x0 = x0 + pad_left
    chart_y0 = y0 + pad_top
    chart_x1 = x1 - pad_right
    chart_y1 = y1 - pad_bottom

    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0

    if title:
        draw_label(canvas, (x0 + x1) / 2, y0 + title_h / 2, title,
                   color='#0f172a', font_size=10, anchor='center')

    if not data:
        draw_label(canvas, (x0 + x1) / 2, (y0 + y1) / 2, 'داده‌ای موجود نیست',
                   color='#94a3b8', font_size=9, anchor='center')
        return

    values = [v for _, v in data]
    if max_value is None:
        max_value = max(values) if values else 1
    if max_value <= 0:
        max_value = 1

    n = len(data)
    bar_gap = max(4, chart_h * 0.06 / max(n, 1))
    bar_h = max(8, (chart_h - bar_gap * (n + 1)) / n)

    canvas.create_line(chart_x0, chart_y0, chart_x0, chart_y1, fill='#cbd5e1', width=1)
    canvas.create_line(chart_x0, chart_y1, chart_x1, chart_y1, fill='#cbd5e1', width=1)

    for i, (label, val) in enumerate(data):
        y = chart_y0 + bar_gap + i * (bar_h + bar_gap)
        bar_w = (val / max_value) * chart_w if max_value > 0 else 0
        canvas.create_rectangle(chart_x0, y, chart_x0 + bar_w, y + bar_h,
                                fill=bar_color, outline='', width=0)

        canvas.create_text(chart_x0 - 4, y + bar_h / 2, text=str(label),
                           fill='#475569', font=('TkDefaultFont', 7), anchor='e')

        if show_values and val > 0:
            canvas.create_text(chart_x0 + bar_w + 4, y + bar_h / 2,
                               text=persian_digits(f'{val:,}'), fill=bar_color,
                               font=('TkDefaultFont', 7), anchor='w')
