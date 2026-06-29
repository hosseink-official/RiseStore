import tkinter as tk
from tkinter import ttk
from desktop.db import fetchall, fetchone, daily_sales, monthly_sales, best_selling, get_debtors, today_str, month_start, get_overdue_sales, yearly_sales, yearly_cost, payment_method_summary, sales_by_category
from desktop.theme import Colors, get_font, get_bold_font
from desktop.utils import format_number, format_date, persian_digits
from desktop.charts import draw_bar_chart, draw_pie_chart, draw_hbar_chart
from datetime import date, datetime


class DashboardView:
    def __init__(self, parent, app):
        self.app = app
        outer = tk.Frame(parent, bg=Colors.bg)
        outer.pack(fill='both', expand=True, padx=28, pady=24)

        canvas = tk.Canvas(outer, bg=Colors.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        self.frame = tk.Frame(canvas, bg=Colors.bg)

        self.frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                canvas.yview_scroll(1, 'units')
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))
        canvas.bind('<Button-4>', _on_mousewheel)
        canvas.bind('<Button-5>', _on_mousewheel)

        self._build()

    def _make_card(self, parent, icon, title, value, subtitle, accent_color, bg_light, row=0, col=0):
        card = tk.Frame(parent, bg=Colors.card, highlightbackground=Colors.border,
                        highlightthickness=1, padx=20, pady=18)
        card.grid(row=row, column=col, sticky='nsew', padx=(0, 12), pady=(0, 12))

        icon_frame = tk.Frame(card, bg=bg_light, width=40, height=40)
        icon_frame.pack(side='right')
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=icon, font=get_font(16),
                 bg=bg_light, fg=accent_color).pack(expand=True)

        text_frame = tk.Frame(card, bg=Colors.card)
        text_frame.pack(side='right', fill='x', expand=True, padx=(0, 12))

        tk.Label(text_frame, text=title, font=get_font(9),
                 bg=Colors.card, fg=Colors.text_muted).pack(anchor='e')
        tk.Label(text_frame, text=value, font=get_bold_font(20),
                 bg=Colors.card, fg=accent_color).pack(anchor='e', pady=(2, 0))
        if subtitle:
            tk.Label(text_frame, text=subtitle, font=get_font(8),
                     bg=Colors.card, fg=Colors.text_muted).pack(anchor='e')

    def _make_chart_card(self, parent, title, canvas_height=220, **grid_kw):
        frame = tk.Frame(parent, bg=Colors.card, highlightbackground=Colors.border,
                         highlightthickness=1, padx=12, pady=12)
        frame.grid(**grid_kw, sticky='nsew', padx=(0, 12), pady=(0, 12))

        tk.Label(frame, text=title, font=get_bold_font(11),
                 bg=Colors.card, fg=Colors.text_primary).pack(anchor='e', pady=(0, 6))

        canvas = tk.Canvas(frame, bg=Colors.card, bd=0, highlightthickness=0,
                           height=canvas_height)
        canvas.pack(fill='both', expand=True)

        return frame, canvas

    def _make_section(self, parent, title, accent_color=None, **pack_kw):
        frame = tk.Frame(parent, bg=Colors.card, highlightbackground=Colors.border,
                         highlightthickness=1, padx=20, pady=16)
        if pack_kw:
            frame.pack(**pack_kw)
        else:
            frame.pack(fill='x', pady=(0, 12))

        tk.Label(frame, text=title, font=get_bold_font(12),
                 bg=Colors.card,
                 fg=accent_color if accent_color else Colors.text_primary
                 ).pack(anchor='e', pady=(0, 10))

        return frame

    def _make_info_row(self, parent, col_text, val_text, val_color=None):
        row = tk.Frame(parent, bg=Colors.card)
        row.pack(fill='x', pady=2)
        tk.Label(row, text=col_text, font=get_font(9),
                 bg=Colors.card, fg=Colors.text_muted).pack(side='right', padx=(4, 0))
        tk.Label(row, text=val_text, font=get_font(9),
                 bg=Colors.card,
                 fg=val_color if val_color else Colors.text_secondary
                 ).pack(side='left')

    def _build(self):
        tk.Label(self.frame, text='داشبورد', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 24))

        d = today_str()
        ms = month_start()
        year = datetime.now().year

        today_sales = daily_sales(d)
        month_sales = monthly_sales(ms)

        today_total = sum(s['total_amount'] or 0 for s in today_sales)
        today_count = len(today_sales)

        month_total = sum(s['total_amount'] or 0 for s in month_sales)
        month_count = len(month_sales)

        month_cost = 0
        for s in month_sales:
            items = fetchall(
                "SELECT si.quantity, p.purchase_price FROM store_saleitem si "
                "JOIN store_product p ON p.id=si.product_id WHERE si.sale_id=?",
                [s['id']]
            )
            for item in items:
                month_cost += item['quantity'] * (item['purchase_price'] or 0)
        month_profit = month_total - month_cost

        debtors = get_debtors()
        debtors_count = len(debtors)

        overdue = get_overdue_sales()
        overdue_count = len(overdue)

        best = best_selling(5)

        yearly = yearly_sales(year)
        month_labels = ['ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن', 'ژوئیه', 'اوت', 'سپتامبر', 'اکتبر', 'نوامبر', 'دسامبر']
        month_data = []
        for r in yearly:
            m = int(r['month'])
            month_data.append((month_labels[m - 1], r['total'] or 0))
        for m in range(1, 13):
            if not any(int(r['month']) == m for r in yearly):
                month_data.insert(m - 1, (month_labels[m - 1], 0))

        methods = payment_method_summary()
        method_labels = {'cash': 'نقدی', 'installment': 'قسطی',
                         'installment_payment': 'پرداخت قسط', 'down_payment': 'پیش پرداخت'}
        method_colors = {'cash': '#10b981', 'installment': '#6366f1',
                         'installment_payment': '#f59e0b', 'down_payment': '#3b82f6'}
        pie_data = []
        for r in methods:
            label = method_labels.get(r['payment_type'], r['payment_type'])
            color = method_colors.get(r['payment_type'], '#94a3b8')
            pie_data.append((label, r['total'] or 0, color))

        categories = sales_by_category()

        self.frame.grid_columnconfigure(0, weight=1)

        cards_frame = tk.Frame(self.frame, bg=Colors.bg)
        cards_frame.pack(fill='x', pady=(0, 24))
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1, uniform='card')

        stats = [
            ('💰', 'فروش امروز', f'{format_number(today_total)} تومان',
             f'{persian_digits(today_count)} فاکتور', '#3b82f6', '#eff6ff'),
            ('📈', 'فروش ماه', f'{format_number(month_total)} تومان',
             f'{persian_digits(month_count)} فاکتور', '#10b981', '#ecfdf5'),
            ('🎯', 'سود ماه', f'{format_number(month_profit)} تومان',
             '', '#f59e0b', '#fffbeb'),
            ('⚠️', 'بدهکاران', f'{persian_digits(debtors_count)} نفر',
             '', '#ef4444', '#fef2f2'),
            ('⏰', 'تاخیر در پرداختها', f'{persian_digits(overdue_count)} فاکتور',
             '', '#dc2626' if overdue_count else '#10b981',
             '#fef2f2' if overdue_count else '#ecfdf5'),
        ]

        for idx, (icon, title, value, sub, accent, bg_light) in enumerate(stats):
            row = idx // 3
            col = idx % 3
            self._make_card(cards_frame, icon, title, value, sub, accent, bg_light, row, col)

        charts_row1 = tk.Frame(self.frame, bg=Colors.bg)
        charts_row1.pack(fill='x')
        charts_row1.grid_columnconfigure(0, weight=3)
        charts_row1.grid_columnconfigure(1, weight=2)

        f1, c1 = self._make_chart_card(charts_row1, '📊  فروش ماهانه', canvas_height=200, row=0, column=0)

        def draw_c1(event=None):
            w, h = c1.winfo_width(), c1.winfo_height()
            if w > 50 and h > 50:
                c1.delete('all')
                draw_bar_chart(c1, month_data, 10, 10, w - 10, h - 10, bar_color=Colors.accent)

        c1.bind('<Configure>', draw_c1)

        f2, c2 = self._make_chart_card(charts_row1, '💳  روش‌های پرداخت', canvas_height=200, row=0, column=1)

        def draw_c2(event=None):
            w, h = c2.winfo_width(), c2.winfo_height()
            if w > 50 and h > 50:
                c2.delete('all')
                draw_pie_chart(c2, pie_data, w // 2, h // 2 + 10, min(w, h) // 2 - 20, hole_r=18)

        c2.bind('<Configure>', draw_c2)

        charts_row2 = tk.Frame(self.frame, bg=Colors.bg)
        charts_row2.pack(fill='x')
        charts_row2.grid_columnconfigure(0, weight=2)
        charts_row2.grid_columnconfigure(1, weight=3)

        best_data = [(p['name'], p['qty']) for p in best]
        f3, c3 = self._make_chart_card(charts_row2, '📦  پرفروش‌ترین محصولات', canvas_height=180, row=0, column=0)

        def draw_c3(event=None):
            w, h = c3.winfo_width(), c3.winfo_height()
            if w > 50 and h > 50:
                c3.delete('all')
                draw_hbar_chart(c3, best_data, 10, 10, w - 10, h - 10, bar_color=Colors.success)

        c3.bind('<Configure>', draw_c3)

        cat_data = [(r['category'], r['revenue'] or 0) for r in categories]
        f4, c4 = self._make_chart_card(charts_row2, '🏷️  فروش بر اساس دسته‌بندی', canvas_height=180, row=0, column=1)

        def draw_c4(event=None):
            w, h = c4.winfo_width(), c4.winfo_height()
            if w > 50 and h > 50:
                c4.delete('all')
                draw_hbar_chart(c4, cat_data, 10, 10, w - 10, h - 10, bar_color=Colors.accent)

        c4.bind('<Configure>', draw_c4)

        lower = tk.Frame(self.frame, bg=Colors.bg)
        lower.pack(fill='both', expand=True, pady=(12, 0))

        overdue_frame = self._make_section(
            lower, '⏰  تاخیر در پرداخت ها',
            Colors.danger if overdue_count else Colors.success
        )

        if overdue:
            for s in overdue[:10]:
                due_date = date.fromisoformat(s['sale_date'][:10])
                import jdatetime
                from datetime import timedelta
                due_j = jdatetime.date.fromgregorian(
                    date=due_date + timedelta(days=s['payment_due_days']))
                name = f"{s['first_name']} {s['last_name']}"
                self._make_info_row(
                    overdue_frame,
                    f"{name} — فاکتور #{persian_digits(s['id'])}",
                    f"سررسید: {persian_digits(due_j.strftime('%Y/%m/%d'))} | {format_number(s['total_amount'])}",
                    Colors.danger
                )
        else:
            tk.Label(overdue_frame, text='همه پرداخت‌ها به‌موقع انجام شده',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=8)

        cols = tk.Frame(lower, bg=Colors.bg)
        cols.pack(fill='both', expand=True)

        debt_frame = self._make_section(cols, '👥  بدهکاران',
                                        side='right', fill='both', expand=True)

        if debtors:
            for d in debtors:
                debt = (d['total'] or 0) - (d['paid'] or 0)
                if debt <= 0:
                    continue
                name = f"{d['first_name']} {d['last_name']}"
                self._make_info_row(
                    debt_frame,
                    name,
                    format_number(debt),
                    Colors.danger
                )
        else:
            tk.Label(debt_frame, text='هیچ بدهکاری وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=16)


