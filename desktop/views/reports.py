import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    daily_sales, monthly_sales, get_debtors, best_selling,
    today_str, month_start, week_ago, fetchall, fetchone, get_all_customers,
    yearly_sales, yearly_cost, sales_by_category, payment_method_summary,
    installment_report, low_stock_products
)
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date
from datetime import date, timedelta, datetime


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
                           ('profit', 'سود و زیان'), ('yearly', 'سالانه'),
                           ('category', 'دسته‌بندی'), ('paymethods', 'روش پرداخت'),
                           ('installments', 'اقساط'), ('stock', 'انبار'),
                           ('debtors', 'بدهکاران'), ('bestselling', 'پرفروش‌ترین')]:
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
        elif key == 'yearly':
            self._yearly_report()
        elif key == 'category':
            self._category_report()
        elif key == 'paymethods':
            self._paymethods_report()
        elif key == 'installments':
            self._installments_report()
        elif key == 'stock':
            self._stock_report()
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

    def _yearly_report(self):
        year = datetime.now().year
        months = yearly_sales(year)
        cost = yearly_cost(year)

        total_sales = sum(r['total'] or 0 for r in months)
        total_count = sum(r['sale_count'] or 0 for r in months)

        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text=f'گزارش سالانه - {year}',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('فروش کل', format_number(total_sales), '#3b82f6'),
            ('تعداد فاکتور', str(total_count), '#a855f7'),
            ('هزینه کل', format_number(cost), '#ef4444'),
            ('سود', format_number(total_sales - cost), '#22c55e'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

        months_frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                                highlightthickness=1, padx=0, pady=0)
        months_frame.pack(fill='both', expand=True, pady=(16, 0))

        cols = ('month', 'count', 'cash', 'inst', 'total')
        tree = ttk.Treeview(months_frame, columns=cols, show='headings', height=12)
        tree.heading('month', text='ماه', anchor='e')
        tree.heading('count', text='تعداد', anchor='center')
        tree.heading('cash', text='نقدی', anchor='center')
        tree.heading('inst', text='قسطی', anchor='center')
        tree.heading('total', text='جمع', anchor='center')
        tree.column('month', width=120, anchor='e')
        tree.column('count', width=80, anchor='center')
        tree.column('cash', width=140, anchor='center')
        tree.column('inst', width=140, anchor='center')
        tree.column('total', width=140, anchor='center')
        tree.pack(fill='both', expand=True, padx=0, pady=0)

        month_names = ['', 'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                       'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        for r in months:
            m = int(r['month'])
            tree.insert('', 'end', values=(
                month_names[m] if 1 <= m <= 12 else str(m),
                r['sale_count'],
                format_number(r['cash_total']),
                format_number(r['inst_total']),
                format_number(r['total']),
            ))

        if not months:
            tk.Label(months_frame, text='هیچ داده‌ای برای این سال وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

    def _category_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text='گزارش فروش بر اساس دسته‌بندی',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        categories = sales_by_category()
        total_rev = sum(r['revenue'] or 0 for r in categories)
        total_cost = sum(r['cost'] or 0 for r in categories)

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('درآمد کل', format_number(total_rev), '#3b82f6'),
            ('هزینه کل', format_number(total_cost), '#ef4444'),
            ('سود', format_number(total_rev - total_cost), '#22c55e'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

        table_frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                               highlightthickness=1, padx=0, pady=0)
        table_frame.pack(fill='both', expand=True, pady=(16, 0))

        cols = ('category', 'sales', 'qty', 'revenue', 'cost', 'profit')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)
        tree.heading('category', text='دسته', anchor='e')
        tree.heading('sales', text='تعداد فروش', anchor='center')
        tree.heading('qty', text='تعداد کالا', anchor='center')
        tree.heading('revenue', text='درآمد', anchor='center')
        tree.heading('cost', text='هزینه', anchor='center')
        tree.heading('profit', text='سود', anchor='center')
        tree.column('category', width=200, anchor='e')
        tree.column('sales', width=100, anchor='center')
        tree.column('qty', width=100, anchor='center')
        tree.column('revenue', width=120, anchor='center')
        tree.column('cost', width=120, anchor='center')
        tree.column('profit', width=120, anchor='center')
        tree.pack(fill='both', expand=True)

        for r in categories:
            profit = (r['revenue'] or 0) - (r['cost'] or 0)
            tree.insert('', 'end', values=(
                r['category'],
                r['sale_count'],
                r['qty'],
                format_number(r['revenue']),
                format_number(r['cost']),
                format_number(profit),
            ))

        if not categories:
            tk.Label(table_frame, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

    def _paymethods_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text='گزارش روش‌های پرداخت',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        methods = payment_method_summary()
        grand_total = sum(r['total'] or 0 for r in methods)

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')

        method_labels = {'cash': 'نقدی', 'installment': 'قسطی',
                         'down_payment': 'پیش پرداخت', 'installment_payment': 'پرداخت قسط'}
        method_colors = {'cash': '#22c55e', 'installment': '#eab308',
                         'down_payment': '#3b82f6', 'installment_payment': '#a855f7'}

        for r in methods:
            ptype = r['payment_type']
            pct = (r['total'] / grand_total * 100) if grand_total else 0
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=method_labels.get(ptype, ptype),
                     font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=format_number(r['total']),
                     font=get_bold_font(18), bg='#f8fafc',
                     fg=method_colors.get(ptype, '#334155')).pack(anchor='e', pady=(4, 0))
            tk.Label(card, text=f'{pct:.1f}% از کل',
                     font=get_font(8), bg='#f8fafc',
                     fg='#94a3b8').pack(anchor='e')

        table_frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                               highlightthickness=1, padx=0, pady=0)
        table_frame.pack(fill='both', expand=True, pady=(16, 0))

        cols = ('method', 'count', 'total', 'percent')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=10)
        tree.heading('method', text='روش پرداخت', anchor='e')
        tree.heading('count', text='تعداد', anchor='center')
        tree.heading('total', text='جمع مبلغ', anchor='center')
        tree.heading('percent', text='درصد', anchor='center')
        tree.column('method', width=200, anchor='e')
        tree.column('count', width=100, anchor='center')
        tree.column('total', width=150, anchor='center')
        tree.column('percent', width=100, anchor='center')
        tree.pack(fill='both', expand=True)

        for r in methods:
            pct = (r['total'] / grand_total * 100) if grand_total else 0
            tree.insert('', 'end', values=(
                method_labels.get(r['payment_type'], r['payment_type']),
                r['sale_count'],
                format_number(r['total']),
                f'{pct:.1f}%',
            ))

        if not methods:
            tk.Label(table_frame, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

    def _installments_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=0, pady=0)
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text='وضعیت اقساط',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', padx=20, pady=(16, 0))

        installments = installment_report()
        active = [i for i in installments if i['status'] == 'active']
        paid_inst = [i for i in installments if i['status'] == 'paid']

        info_frame = tk.Frame(frame, bg='#ffffff')
        info_frame.pack(fill='x', padx=20, pady=(8, 12))

        stats = [
            ('کل اقساط', str(len(installments)), '#3b82f6'),
            ('قسط‌های فعال', str(len(active)), '#eab308'),
            ('تسویه شده', str(len(paid_inst)), '#22c55e'),
        ]
        for title, val, color in stats:
            card = tk.Frame(info_frame, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=8)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(2, 0))

        cols = ('customer', 'phone', 'total', 'per_term', 'paid', 'remaining',
                'progress', 'status')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=15)
        tree.heading('customer', text='مشتری', anchor='e')
        tree.heading('phone', text='تلفن', anchor='center')
        tree.heading('total', text='مبلغ کل', anchor='center')
        tree.heading('per_term', text='مبلغ هر قسط', anchor='center')
        tree.heading('paid', text='پرداخت شده', anchor='center')
        tree.heading('remaining', text='باقی‌مانده', anchor='center')
        tree.heading('progress', text='پیشرفت', anchor='center')
        tree.heading('status', text='وضعیت', anchor='center')
        tree.column('customer', width=180, anchor='e')
        tree.column('phone', width=100, anchor='center')
        tree.column('total', width=110, anchor='center')
        tree.column('per_term', width=100, anchor='center')
        tree.column('paid', width=100, anchor='center')
        tree.column('remaining', width=100, anchor='center')
        tree.column('progress', width=80, anchor='center')
        tree.column('status', width=80, anchor='center')
        tree.pack(fill='both', expand=True, padx=0, pady=(0, 0))

        for i in installments:
            total_inst = i['total_count'] * i['amount_per_term']
            remaining = max(0, total_inst - (i['amount_paid'] or 0))
            progress = f"{i['paid_count']}/{i['total_count']}"
            status_text = 'فعال' if i['status'] == 'active' else 'تسویه'
            tree.insert('', 'end', values=(
                f"{i['first_name']} {i['last_name']}",
                i.get('phone') or '—',
                format_number(total_inst),
                format_number(i['amount_per_term']),
                format_number(i['amount_paid']),
                format_number(remaining),
                progress,
                status_text,
            ))

        if not installments:
            tk.Label(frame, text='هیچ قسطی ثبت نشده است',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

    def _stock_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=20, pady=16)
        frame.pack(fill='x')

        tk.Label(frame, text='گزارش موجودی انبار',
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 16))

        from desktop.db import get_all_products
        all_products = get_all_products()
        low = [p for p in all_products if (p['stock'] or 0) <= 5]
        out = [p for p in all_products if (p['stock'] or 0) == 0]
        total_items = len(all_products)
        total_stock = sum(p['stock'] or 0 for p in all_products)

        grid = tk.Frame(frame, bg='#ffffff')
        grid.pack(fill='x')
        stats = [
            ('کل محصولات', str(total_items), '#3b82f6'),
            ('موجودی کل', str(total_stock), '#22c55e'),
            ('کم‌موجودی', str(len(low)), '#eab308'),
            ('اتمام موجودی', str(len(out)), '#ef4444'),
        ]
        for title, val, color in stats:
            card = tk.Frame(grid, bg='#f8fafc', highlightbackground='#e2e8f0',
                            highlightthickness=1, padx=12, pady=10)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg='#f8fafc',
                     fg='#64748b').pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(18), bg='#f8fafc',
                     fg=color).pack(anchor='e', pady=(4, 0))

        low_items = low_stock_products(5)
        table_frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                               highlightthickness=1, padx=0, pady=0)
        table_frame.pack(fill='both', expand=True, pady=(16, 0))

        tk.Label(table_frame, text='محصولات با موجودی کم (≤۵)',
                 font=get_bold_font(10), bg='#ffffff',
                 fg='#ef4444').pack(anchor='e', padx=16, pady=(8, 4))

        cols = ('name', 'category', 'stock', 'unit', 'price')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=12)
        tree.heading('name', text='محصول', anchor='e')
        tree.heading('category', text='دسته', anchor='e')
        tree.heading('stock', text='موجودی', anchor='center')
        tree.heading('unit', text='واحد', anchor='center')
        tree.heading('price', text='قیمت فروش', anchor='center')
        tree.column('name', width=200, anchor='e')
        tree.column('category', width=150, anchor='e')
        tree.column('stock', width=80, anchor='center')
        tree.column('unit', width=80, anchor='center')
        tree.column('price', width=120, anchor='center')
        tree.pack(fill='both', expand=True)

        for p in low_items:
            tree.insert('', 'end', values=(
                p['name'],
                p.get('product_type_name') or '—',
                p['stock'],
                p.get('unit') or '—',
                format_number(p['selling_price']),
            ))

        if not low_items:
            tk.Label(table_frame, text='همه محصولات به مقدار کافی موجود هستند',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)

    def _debtors_report(self):
        frame = tk.Frame(self.content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1, padx=0, pady=0)
        frame.pack(fill='both', expand=True)

        cols = ('name', 'phone', 'invoices', 'total', 'paid', 'debt')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        tree.heading('name', text='مشتری', anchor='e')
        tree.heading('phone', text='شماره تماس', anchor='center')
        tree.heading('invoices', text='فاکتورهای باز', anchor='center')
        tree.heading('total', text='کل خرید', anchor='center')
        tree.heading('paid', text='کل پرداخت', anchor='center')
        tree.heading('debt', text='بدهی', anchor='center')
        for col in cols:
            tree.column(col, width=120, anchor='center')
        tree.column('name', width=200, anchor='e')
        tree.column('invoices', width=100, anchor='center')
        tree.pack(fill='both', expand=True)

        debtors = get_debtors()
        for d in debtors:
            debt = (d['total'] or 0) - (d['paid'] or 0)
            if debt <= 0:
                continue
            cid = d['id']
            open_sales = fetchall(
                "SELECT id, total_amount FROM store_sale WHERE customer_id=? AND status IN ('pending','partial')",
                [cid]
            )
            open_count = len(open_sales)
            tree.insert('', 'end', values=(
                f"{d['first_name']} {d['last_name']}",
                d.get('phone') or '—',
                open_count,
                format_number(d['total']), format_number(d['paid']),
                format_number(debt),
            ))

        tree.bind('<Double-1>', lambda e: self._show_debtor_invoices(tree, e))

    def _show_debtor_invoices(self, tree, event):
        item = tree.identify_row(event.y)
        if not item:
            return
        values = tree.item(item, 'values')
        if not values:
            return
        name = values[0]
        cid = None
        for d in get_debtors():
            fn = f"{d['first_name']} {d['last_name']}"
            if fn == name:
                cid = d['id']
                break
        if not cid:
            return
        sales = fetchall(
            "SELECT id, sale_date, total_amount, status FROM store_sale WHERE customer_id=? AND status IN ('pending','partial') ORDER BY sale_date DESC",
            [cid]
        )
        if not sales:
            return
        win = tk.Toplevel(tree.winfo_toplevel())
        win.title(f'فاکتورهای باز - {name}')
        win.geometry('600x400')
        win.configure(bg='#f0f2f5')
        from desktop.db import sale_remaining
        from desktop.utils import format_datetime
        cols = ('id', 'date', 'amount', 'remaining', 'status')
        t = ttk.Treeview(win, columns=cols, show='headings', height=15)
        t.heading('id', text='#')
        t.heading('date', text='تاریخ')
        t.heading('amount', text='مبلغ')
        t.heading('remaining', text='باقی‌مانده')
        t.heading('status', text='وضعیت')
        for col in cols:
            t.column(col, width=100, anchor='center')
        t.pack(fill='both', expand=True, padx=16, pady=16)
        for s in sales:
            rem = sale_remaining(s['id'])
            t.insert('', 'end', values=(
                s['id'],
                format_datetime(s['sale_date']),
                format_number(s['total_amount']),
                format_number(rem),
                s['status'],
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
