import tkinter as tk
from desktop.db import fetchall, fetchone, daily_sales, monthly_sales, best_selling, get_debtors, today_str, month_start, get_overdue_sales
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date
from datetime import date, datetime


class Colors:
    bg = '#f1f5f9'
    card = '#ffffff'
    text_primary = '#0f172a'
    text_secondary = '#475569'
    text_muted = '#94a3b8'
    border = '#e2e8f0'
    accent = '#6366f1'
    success = '#10b981'
    warning = '#f59e0b'
    danger = '#ef4444'


class DashboardView:
    def __init__(self, parent, app):
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        tk.Label(self.frame, text='داشبورد', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 24))

        self._load_data()

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

        return card

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

    def _load_data(self):
        d = today_str()
        ms = month_start()

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

        best = best_selling(5)

        overdue = get_overdue_sales()
        overdue_count = len(overdue)

        cards_frame = tk.Frame(self.frame, bg=Colors.bg)
        cards_frame.pack(fill='x', pady=(0, 24))
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1, uniform='card')

        stats = [
            ('💰', 'فروش امروز', f'{format_number(today_total)} تومان',
             f'{today_count} فاکتور', '#3b82f6', '#eff6ff'),
            ('📈', 'فروش ماه', f'{format_number(month_total)} تومان',
             f'{month_count} فاکتور', '#10b981', '#ecfdf5'),
            ('🎯', 'سود ماه', f'{format_number(month_profit)} تومان',
             '', '#f59e0b', '#fffbeb'),
            ('⚠️', 'بدهکاران', f'{debtors_count} نفر',
             '', '#ef4444', '#fef2f2'),
            ('⏰', 'پرداخت‌های گذشته', f'{overdue_count} فاکتور',
             '', '#dc2626' if overdue_count else '#10b981',
             '#fef2f2' if overdue_count else '#ecfdf5'),
        ]

        for idx, (icon, title, value, sub, accent, bg_light) in enumerate(stats):
            row = idx // 3
            col = idx % 3
            self._make_card(cards_frame, icon, title, value, sub, accent, bg_light, row, col)

        lower = tk.Frame(self.frame, bg=Colors.bg)
        lower.pack(fill='both', expand=True)

        overdue_frame = self._make_section(
            lower, '⏰  پرداخت‌های گذشته',
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
                    f"{name} — فاکتور #{s['id']}",
                    f"سررسید: {due_j.strftime('%Y/%m/%d')} | {format_number(s['total_amount'])}",
                    Colors.danger
                )
        else:
            tk.Label(overdue_frame, text='همه پرداخت‌ها به‌موقع انجام شده',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=8)

        cols = tk.Frame(lower, bg=Colors.bg)
        cols.pack(fill='both', expand=True)

        best_frame = self._make_section(cols, '📦  پرفروش‌ترین محصولات',
                                        side='right', fill='both', expand=True, padx=(12, 0))

        if best:
            for p in best:
                row = tk.Frame(best_frame, bg=Colors.card)
                row.pack(fill='x', pady=2)
                tk.Label(row, text=p['name'], font=get_font(9),
                         bg=Colors.card, fg=Colors.text_secondary).pack(side='right')
                tk.Label(row, text=f'{p["qty"]} عدد | {format_number(p["rev"])}',
                         font=get_font(9), bg=Colors.card,
                         fg=Colors.success).pack(side='left')
        else:
            tk.Label(best_frame, text='هنوز فروشی ثبت نشده',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=16)

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
