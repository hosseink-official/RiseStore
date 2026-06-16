import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    daily_sales, monthly_sales, get_debtors, best_selling,
    today_str, month_start, week_ago, fetchall, fetchone, get_all_customers
)
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date
from datetime import date, timedelta


class ReportsView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        tk.Label(self.frame, text='گزارش‌ها', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 20))

        tab_frame = tk.Frame(self.frame, bg='#f0f2f5')
        tab_frame.pack(fill='x', pady=(0, 16))

        self.tabs = {}
        self.active_tab = None
        for key, label in [('daily', 'روزانه'), ('monthly', 'ماهانه'),
                           ('profit', 'سود و زیان'), ('debtors', 'بدهکاران'),
                           ('bestselling', 'پرفروش‌ترین')]:
            btn = tk.Button(tab_frame, text=label, font=get_font(9),
                            bg='#e2e8f0', fg='#475569', bd=1, relief='solid',
                            cursor='hand2', padx=16, pady=4,
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side='right', padx=(4, 0))
            self.tabs[key] = btn

        self.content = tk.Frame(self.frame, bg='#f0f2f5')
        self.content.pack(fill='both', expand=True)

        self._switch_tab('daily')

    def _switch_tab(self, key):
        self.active_tab = key
        for k, btn in self.tabs.items():
            btn.configure(bg='#2563eb' if k == key else '#e2e8f0',
                          fg='#ffffff' if k == key else '#475569')
        for w in self.content.winfo_children():
            w.destroy()

        if key == 'daily':
            self._daily_report()
        elif key == 'monthly':
            self._monthly_report()
        elif key == 'profit':
            self._profit_report()
        elif key == 'debtors':
            self._debtors_report()
        elif key == 'bestselling':
            self._best_selling_report()

    def _daily_report(self):
        d = today_str()
        sales = daily_sales(d)

        total = sum(s['total_amount'] or 0 for s in sales)
        cash = sum(s['total_amount'] or 0 for s in sales if s['payment_type'] == 'cash')
        inst = sum(s['total_amount'] or 0 for s in sales if s['payment_type'] == 'installment')
        count = len(sales)

        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text=f'گزارش روزانه - {format_date(d)}',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('فروش کل', format_number(total), '#3b82f6'),
            ('فروش نقدی', format_number(cash), '#22c55e'),
            ('فروش قسطی', format_number(inst), '#eab308'),
            ('تعداد فاکتور', str(count), '#a855f7'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

    def _monthly_report(self):
        ms = month_start()
        td = today_str()
        sales = monthly_sales(ms)

        total = sum(s['total_amount'] or 0 for s in sales)

        total_cost = 0
        for s in sales:
            items = fetchall(
                "SELECT si.quantity, p.purchase_price FROM store_saleitem si "
                "JOIN store_product p ON p.id=si.product_id WHERE si.sale_id=?",
                [s['id']]
            )
            for item in items:
                total_cost += item['quantity'] * (item['purchase_price'] or 0)
        profit = total - total_cost

        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text=f'گزارش ماهانه - {format_date(ms)} تا {format_date(td)}',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('فروش', format_number(total), '#3b82f6'),
            ('هزینه', format_number(total_cost), '#ef4444'),
            ('سود', format_number(profit), '#22c55e'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

    def _profit_report(self):
        wa = week_ago()
        td = today_str()
        sales = fetchall(
            "SELECT * FROM store_sale WHERE date(sale_date)>=? AND status!='cancelled'",
            [wa]
        )

        total = sum(s['total_amount'] or 0 for s in sales)
        total_cost = 0
        for s in sales:
            items = fetchall(
                "SELECT si.quantity, p.purchase_price FROM store_saleitem si "
                "JOIN store_product p ON p.id=si.product_id WHERE si.sale_id=?",
                [s['id']]
            )
            for item in items:
                total_cost += item['quantity'] * (item['purchase_price'] or 0)
        profit = total - total_cost
        count = len(sales)

        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text='گزارش سود و زیان - ۷ روز گذشته',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('فروش', format_number(total), '#3b82f6'),
            ('هزینه', format_number(total_cost), '#ef4444'),
            ('سود', format_number(profit), '#22c55e'),
            ('تعداد فروش', str(count), '#a855f7'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

    def _debtors_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=0, pady=0)
        frame.pack(fill='both', expand=True)

        cols = ('name', 'phone', 'total', 'paid', 'debt')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        tree.heading('name', text='مشتری', anchor='e')
        tree.heading('phone', text='شماره تماس', anchor='center')
        tree.heading('total', text='کل خرید', anchor='center')
        tree.heading('paid', text='کل پرداخت', anchor='center')
        tree.heading('debt', text='بدهی', anchor='center')
        for col in cols:
            tree.column(col, width=140, anchor='center')
        tree.column('name', width=200, anchor='e')
        tree.pack(fill='both', expand=True)

        debtors = get_debtors()
        for d in debtors:
            debt = (d['total'] or 0) - (d['paid'] or 0)
            if debt <= 0:
                continue
            tree.insert('', 'end', values=(
                f"{d['first_name']} {d['last_name']}",
                d.get('phone') or '—',
                format_number(d['total']), format_number(d['paid']),
                format_number(debt),
            ))

    def _best_selling_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=0, pady=0)
        frame.pack(fill='both', expand=True)

        cols = ('rank', 'name', 'qty', 'revenue')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        tree.heading('rank', text='#')
        tree.heading('name', text='محصول', anchor='e')
        tree.heading('qty', text='تعداد فروش', anchor='center')
        tree.heading('revenue', text='درآمد', anchor='center')
        tree.column('rank', width=50, anchor='center')
        tree.column('name', width=250, anchor='e')
        tree.column('qty', width=120, anchor='center')
        tree.column('revenue', width=120, anchor='center')
        tree.pack(fill='both', expand=True)

        top = best_selling(10)
        for i, p in enumerate(top):
            tree.insert('', 'end', values=(
                i + 1, p['name'], p['qty'],
                format_number(p['rev']),
            ))

        if not top:
            tk.Label(frame, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=30)
