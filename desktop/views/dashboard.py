import tkinter as tk
from desktop.db import fetchall, fetchone, daily_sales, monthly_sales, best_selling, get_debtors, today_str, month_start
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date
from datetime import date


class DashboardView:
    def __init__(self, parent, app):
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        tk.Label(self.frame, text='داشبورد', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 20))

        self._load_data()

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

        cards_frame = tk.Frame(self.frame, bg='#f0f2f5')
        cards_frame.pack(fill='x', pady=(0, 24))

        stats = [
            ('فروش امروز', f'{format_number(today_total)} تومان',
             f'{today_count} فاکتور', '#eff6ff', '#3b82f6'),
            ('فروش ماه', f'{format_number(month_total)} تومان',
             f'{month_count} فاکتور', '#f0fdf4', '#22c55e'),
            ('سود ماه', f'{format_number(month_profit)} تومان',
             '', '#fefce8', '#eab308'),
            ('بدهکاران', f'{debtors_count} نفر', '',
             '#fef2f2', '#ef4444'),
        ]

        for i, (title, value, sub, bg_color, accent) in enumerate(stats):
            card = tk.Frame(cards_frame, bg='#ffffff', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=16, pady=14)
            card.pack(side='right', fill='x', expand=True, padx=(0, 12))
            tk.Label(card, text=title, font=get_font(9), bg='#ffffff',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=value, font=get_bold_font(18),
                     bg='#ffffff', fg=accent).pack(anchor='e', pady=(4, 0))
            if sub:
                tk.Label(card, text=sub, font=get_font(8),
                         bg='#ffffff', fg='#94a3b8').pack(anchor='e')

        lower = tk.Frame(self.frame, bg='#f0f2f5')
        lower.pack(fill='both', expand=True)

        best_frame = tk.Frame(lower, bg='#ffffff', highlightbackground='#e2e8f0',
                              highlightthickness=1, padx=16, pady=12)
        best_frame.pack(side='right', fill='both', expand=True, padx=(12, 0))

        tk.Label(best_frame, text='پرفروش‌ترین محصولات',
                 font=get_bold_font(12), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 10))

        if best:
            for p in best:
                row = tk.Frame(best_frame, bg='#ffffff')
                row.pack(fill='x', pady=2)
                tk.Label(row, text=p['name'], font=get_font(9),
                         bg='#ffffff', fg='#334155').pack(side='right')
                tk.Label(row, text=f'{p["qty"]} عدد | {format_number(p["rev"])}',
                         font=get_font(9), bg='#ffffff',
                         fg='#16a34a').pack(side='left')
        else:
            tk.Label(best_frame, text='هنوز فروشی ثبت نشده',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

        debt_frame = tk.Frame(lower, bg='#ffffff', highlightbackground='#e2e8f0',
                              highlightthickness=1, padx=16, pady=12)
        debt_frame.pack(side='right', fill='both', expand=True)

        tk.Label(debt_frame, text='بدهکاران',
                 font=get_bold_font(12), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 10))

        if debtors:
            for d in debtors:
                debt = (d['total'] or 0) - (d['paid'] or 0)
                if debt <= 0:
                    continue
                row = tk.Frame(debt_frame, bg='#ffffff')
                row.pack(fill='x', pady=2)
                name = f"{d['first_name']} {d['last_name']}"
                tk.Label(row, text=name, font=get_font(9),
                         bg='#ffffff', fg='#334155').pack(side='right')
                tk.Label(row, text=format_number(debt),
                         font=get_bold_font(9), bg='#ffffff',
                         fg='#dc2626').pack(side='left')
        else:
            tk.Label(debt_frame, text='هیچ بدهکاری وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)
