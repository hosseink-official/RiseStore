import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    daily_sales, monthly_sales, get_debtors, best_selling,
    today_str, month_start, week_ago, fetchall, fetchone, get_all_customers,
    yearly_sales, yearly_cost, sales_by_category, payment_method_summary,
    installment_report, low_stock_products
)
from desktop.theme import Colors, get_font, get_bold_font
from desktop.utils import format_number, format_date, make_dialog
from desktop.views.sales import SaleDetailView
from datetime import date, timedelta, datetime


class ReportsView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        tk.Label(self.frame, text='گزارش‌ها', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 24))

        tab_frame = tk.Frame(self.frame, bg=Colors.bg)
        tab_frame.pack(fill='x', pady=(0, 20))

        self.tabs = {}
        self.active_tab = None
        for key, label in [('daily', '📅  روزانه'), ('monthly', '📆  ماهانه'),
                           ('profit', '💰  سود و زیان'), ('yearly', '📊  سالانه'),
                           ('category', '🏷️  دسته‌بندی'), ('paymethods', '💳  روش پرداخت'),
                           ('installments', '📋  اقساط'), ('stock', '📦  انبار'),
                           ('debtors', '⚠️  بدهکاران'), ('bestselling', '🏆  پرفروش‌ترین')]:
            btn = tk.Button(tab_frame, text=label, font=get_font(9),
                            bg=Colors.border, fg=Colors.text_secondary,
                            bd=1, relief='solid',
                            cursor='hand2', padx=16, pady=6,
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side='right', padx=(4, 0))
            self.tabs[key] = btn

        self.content = tk.Frame(self.frame, bg=Colors.bg)
        self.content.pack(fill='both', expand=True)

        self._switch_tab('daily')

    def _switch_tab(self, key):
        self.active_tab = key
        for k, btn in self.tabs.items():
            btn.configure(bg=Colors.accent if k == key else Colors.border,
                          fg='#ffffff' if k == key else Colors.text_secondary)
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

    def _make_cards(self, parent, stats):
        for title, val, color in stats:
            card = tk.Frame(parent, bg=Colors.card, highlightbackground=Colors.border,
                            highlightthickness=1, padx=16, pady=14)
            card.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(card, text=title, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(anchor='e')
            tk.Label(card, text=val, font=get_bold_font(20), bg=Colors.card,
                     fg=color).pack(anchor='e', pady=(4, 0))

    def _report_card(self, title):
        card = tk.Frame(self.content, bg=Colors.card, highlightbackground=Colors.border,
                        highlightthickness=1, padx=24, pady=20)
        card.pack(fill='x')
        tk.Label(card, text=title, font=get_bold_font(14), bg=Colors.card,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 16))
        return card

    def _table_card(self):
        card = tk.Frame(self.content, bg=Colors.card, highlightbackground=Colors.border,
                        highlightthickness=1, padx=0, pady=0)
        card.pack(fill='both', expand=True, pady=(16, 0))
        return card

    def _daily_report(self):
        d = today_str()
        sales = daily_sales(d)

        total = sum(s['total_amount'] or 0 for s in sales)
        cash = sum(s['total_amount'] or 0 for s in sales if s['payment_type'] == 'cash')
        inst = sum(s['total_amount'] or 0 for s in sales if s['payment_type'] == 'installment')
        count = len(sales)

        card = self._report_card(f'📅  گزارش روزانه - {format_date(d)}')
        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('فروش کل', format_number(total), Colors.blue),
            ('فروش نقدی', format_number(cash), Colors.success),
            ('فروش قسطی', format_number(inst), Colors.warning),
            ('تعداد فاکتور', str(count), Colors.purple),
        ])

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

        card = self._report_card(f'📆  گزارش ماهانه - {format_date(ms)} تا {format_date(td)}')
        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('فروش', format_number(total), Colors.blue),
            ('هزینه', format_number(total_cost), Colors.danger),
            ('سود', format_number(profit), Colors.success),
        ])

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

        card = self._report_card('💰  گزارش سود و زیان - ۷ روز گذشته')
        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('فروش', format_number(total), Colors.blue),
            ('هزینه', format_number(total_cost), Colors.danger),
            ('سود', format_number(profit), Colors.success),
            ('تعداد فروش', str(count), Colors.purple),
        ])

    def _yearly_report(self):
        year = datetime.now().year
        months = yearly_sales(year)
        cost = yearly_cost(year)

        total_sales = sum(r['total'] or 0 for r in months)
        total_count = sum(r['sale_count'] or 0 for r in months)

        card = self._report_card(f'📊  گزارش سالانه - {year}')
        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('فروش کل', format_number(total_sales), Colors.blue),
            ('تعداد فاکتور', str(total_count), Colors.purple),
            ('هزینه کل', format_number(cost), Colors.danger),
            ('سود', format_number(total_sales - cost), Colors.success),
        ])

        tc = self._table_card()
        cols = ('total', 'inst', 'cash', 'count', 'month')
        tree = ttk.Treeview(tc, columns=cols, show='headings', height=12)
        tree.heading('total', text='جمع', anchor='center')
        tree.heading('inst', text='قسطی', anchor='center')
        tree.heading('cash', text='نقدی', anchor='center')
        tree.heading('count', text='تعداد', anchor='center')
        tree.heading('month', text='ماه', anchor='e')
        tree.column('total', width=150, anchor='center')
        tree.column('inst', width=150, anchor='center')
        tree.column('cash', width=150, anchor='center')
        tree.column('count', width=80, anchor='center')
        tree.column('month', width=140, anchor='e')

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        month_names = ['', 'ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن',
                       'ژوئیه', 'اوت', 'سپتامبر', 'اکتبر', 'نوامبر', 'دسامبر']
        for r in months:
            m = int(r['month'])
            tree.insert('', 'end', values=(
                format_number(r['total']),
                format_number(r['inst_total']),
                format_number(r['cash_total']),
                r['sale_count'],
                month_names[m] if 1 <= m <= 12 else str(m),
            ))

        if not months:
            tk.Label(tc, text='هیچ داده‌ای برای این سال وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=20)

    def _category_report(self):
        card = self._report_card('🏷️  گزارش فروش بر اساس دسته‌بندی')

        categories = sales_by_category()
        total_rev = sum(r['revenue'] or 0 for r in categories)
        total_cost = sum(r['cost'] or 0 for r in categories)

        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('درآمد کل', format_number(total_rev), Colors.blue),
            ('هزینه کل', format_number(total_cost), Colors.danger),
            ('سود', format_number(total_rev - total_cost), Colors.success),
        ])

        tc = self._table_card()
        cols = ('profit', 'cost', 'revenue', 'qty', 'sales', 'category')
        tree = ttk.Treeview(tc, columns=cols, show='headings', height=15)
        tree.heading('profit', text='سود', anchor='center')
        tree.heading('cost', text='هزینه', anchor='center')
        tree.heading('revenue', text='درآمد', anchor='center')
        tree.heading('qty', text='تعداد کالا', anchor='center')
        tree.heading('sales', text='تعداد فروش', anchor='center')
        tree.heading('category', text='دسته', anchor='e')
        tree.column('profit', width=130, anchor='center')
        tree.column('cost', width=130, anchor='center')
        tree.column('revenue', width=130, anchor='center')
        tree.column('qty', width=100, anchor='center')
        tree.column('sales', width=100, anchor='center')
        tree.column('category', width=220, anchor='e')

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        for r in categories:
            profit = (r['revenue'] or 0) - (r['cost'] or 0)
            tree.insert('', 'end', values=(
                format_number(profit),
                format_number(r['cost']),
                format_number(r['revenue']),
                r['qty'],
                r['sale_count'],
                r['category'],
            ))

        if not categories:
            tk.Label(tc, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=20)

    def _paymethods_report(self):
        card = self._report_card('💳  گزارش روش‌های پرداخت')

        methods = payment_method_summary()
        grand_total = sum(r['total'] or 0 for r in methods)

        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')

        method_labels = {'cash': 'نقدی', 'installment': 'قسطی',
                         'down_payment': 'پیش پرداخت', 'installment_payment': 'پرداخت قسط'}
        method_colors_map = {'cash': Colors.success, 'installment': Colors.warning,
                             'down_payment': Colors.blue, 'installment_payment': Colors.purple}

        for r in methods:
            ptype = r['payment_type']
            pct = (r['total'] / grand_total * 100) if grand_total else 0
            mc = tk.Frame(grid, bg=Colors.card, highlightbackground=Colors.border,
                          highlightthickness=1, padx=14, pady=12)
            mc.pack(side='right', fill='x', expand=True, padx=(8, 0))
            tk.Label(mc, text=method_labels.get(ptype, ptype),
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(anchor='e')
            tk.Label(mc, text=format_number(r['total']),
                     font=get_bold_font(18), bg=Colors.card,
                     fg=method_colors_map.get(ptype, Colors.text_primary)).pack(anchor='e', pady=(4, 0))
            tk.Label(mc, text=f'{pct:.1f}% از کل',
                     font=get_font(8), bg=Colors.card,
                     fg=Colors.text_muted).pack(anchor='e')

        tc = self._table_card()
        cols = ('percent', 'total', 'count', 'method')
        tree = ttk.Treeview(tc, columns=cols, show='headings', height=10)
        tree.heading('percent', text='درصد', anchor='center')
        tree.heading('total', text='جمع مبلغ', anchor='center')
        tree.heading('count', text='تعداد', anchor='center')
        tree.heading('method', text='روش پرداخت', anchor='e')
        tree.column('percent', width=100, anchor='center')
        tree.column('total', width=160, anchor='center')
        tree.column('count', width=100, anchor='center')
        tree.column('method', width=220, anchor='e')

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        for r in methods:
            pct = (r['total'] / grand_total * 100) if grand_total else 0
            tree.insert('', 'end', values=(
                f'{pct:.1f}%',
                format_number(r['total']),
                r['sale_count'],
                method_labels.get(r['payment_type'], r['payment_type']),
            ))

        if not methods:
            tk.Label(tc, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=20)

    def _installments_report(self):
        tc = self._table_card()

        filter_card = tk.Frame(tc, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1,
                               padx=12, pady=8)
        filter_card.pack(fill='x', padx=0)

        tk.Label(filter_card, text='مشتری:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary).pack(side='right', padx=(4, 0))
        customer_var = tk.StringVar(value='')
        all_customer_names = []
        customer_cb = ttk.Combobox(filter_card, textvariable=customer_var,
                                    state='normal', font=get_font(9), width=16)
        customer_cb.pack(side='right', padx=4)

        def _filter_customers(*_):
            q = customer_var.get().strip()
            if q:
                customer_cb['values'] = [c for c in all_customer_names if q in c]
            else:
                customer_cb['values'] = all_customer_names
            customer_cb.event_generate('<Down>')

        customer_cb.bind('<KeyRelease>', _filter_customers)

        tk.Label(filter_card, text='فاکتور #:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary).pack(side='right', padx=(4, 0))
        sale_var = tk.StringVar()
        sale_cb = ttk.Combobox(filter_card, textvariable=sale_var,
                                state='normal', font=get_font(9), width=10)
        sale_cb.pack(side='right', padx=4)

        info_frame = tk.Frame(tc, bg=Colors.card)
        info_frame.pack(fill='x', padx=24, pady=(12, 16))

        cols = ('sale_id', 'next_due', 'status', 'progress', 'remaining', 'paid', 'per_term', 'total',
                'phone', 'customer')
        tree = ttk.Treeview(tc, columns=cols, show='headings', height=15)
        tree.heading('sale_id', text='#', anchor='center')
        tree.heading('next_due', text='سررسید بعدی', anchor='center')
        tree.heading('status', text='وضعیت', anchor='center')
        tree.heading('progress', text='پیشرفت', anchor='center')
        tree.heading('remaining', text='باقی‌مانده', anchor='center')
        tree.heading('paid', text='پرداخت شده', anchor='center')
        tree.heading('per_term', text='مبلغ هر قسط', anchor='center')
        tree.heading('total', text='مبلغ کل', anchor='center')
        tree.heading('phone', text='تلفن', anchor='center')
        tree.heading('customer', text='مشتری', anchor='e')
        tree.column('sale_id', width=80, anchor='center')
        tree.column('next_due', width=110, anchor='center')
        tree.column('status', width=70, anchor='center')
        tree.column('progress', width=70, anchor='center')
        tree.column('remaining', width=110, anchor='center')
        tree.column('paid', width=110, anchor='center')
        tree.column('per_term', width=90, anchor='center')
        tree.column('total', width=110, anchor='center')
        tree.column('phone', width=100, anchor='center')
        tree.column('customer', width=200, anchor='e')

        def _next_due(start_date_str, last_payment_date_str, due_days, status, total_count, paid_count):
            if status != 'active':
                return '—'
            if total_count <= 0:
                return '—'
            try:
                interval = max(1, due_days // total_count) if due_days > 0 else 30
                base = last_payment_date_str or start_date_str
                due = paid_count * interval
                nd = datetime.strptime(base, '%Y-%m-%d').date() + timedelta(days=due)
                return format_date(nd.isoformat())
            except Exception:
                return '—'

        def _build_cname(i):
            return f"{i['first_name'] or ''} {i['last_name'] or ''}".strip()

        def load_data(*_):
            for item in tree.get_children():
                tree.delete(item)
            for w in info_frame.winfo_children():
                w.destroy()
            installments = installment_report()
            cq = customer_var.get().strip()
            sq = sale_var.get().strip()
            cq = cq if cq in all_customer_names else ''
            sale_ids = set()
            for i in installments:
                cname = _build_cname(i)
                if cname not in all_customer_names:
                    all_customer_names.append(cname)
                if cq and cq != cname:
                    continue
                sale_ids.add(i['sale_id'])
            all_customer_names.sort()
            customer_cb['values'] = [''] + all_customer_names
            sale_cb['values'] = [''] + sorted(sale_ids)
            if sq and sq not in sale_cb['values']:
                sq = ''
                sale_var.set('')
            active = [x for x in installments if x['status'] == 'active']
            paid_inst = [x for x in installments if x['status'] == 'paid']
            total_remaining = 0
            self._make_cards(info_frame, [
                ('کل اقساط', str(len(installments)), Colors.blue),
                ('قسط‌های فعال', str(len(active)), Colors.warning),
                ('تسویه شده', str(len(paid_inst)), Colors.success),
                ('باقی‌مانده', '—', Colors.danger),
            ])
            remaining_label = info_frame.winfo_children()[-1].winfo_children()[-1]
            for i in installments:
                cname = _build_cname(i)
                if cq and cq != cname:
                    continue
                if sq:
                    try:
                        if int(sq) != i['sale_id']:
                            continue
                    except ValueError:
                        pass
                remaining = max(0, (i['total_amount'] or 0) - (i['amount_paid'] or 0))
                total_remaining += remaining
                progress = f"{i['paid_count']}/{i['total_count']}"
                status_text = 'فعال' if i['status'] == 'active' else 'تسویه'
                next_due = _next_due(i['start_date'], i.get('last_payment_date'), i['due_day'], i['status'], i['total_count'], i['paid_count'])
                tree.insert('', 'end', values=(
                    i['sale_id'],
                    next_due,
                    status_text,
                    progress,
                    format_number(remaining),
                    format_number(i['amount_paid']),
                    format_number(i['amount_per_term']),
                    format_number(i['total_amount']),
                    i.get('phone') or '—',
                    _build_cname(i),
                ))
            remaining_label.config(text=format_number(total_remaining))

            if not installments:
                tk.Label(tc, text='هیچ قسطی ثبت نشده است',
                         font=get_font(9), bg=Colors.card,
                         fg=Colors.text_muted).pack(pady=20)

        def _open_sale(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            values = tree.item(item, 'values')
            if values:
                win = make_dialog(self.frame, f'فروش #{values[0]}', 900, 680)
                win.configure(bg=Colors.bg)
                SaleDetailView(win, int(values[0]), self.app)

        tree.bind('<Double-1>', _open_sale)

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        customer_var.trace('w', load_data)
        sale_var.trace('w', load_data)
        load_data()

    def _stock_report(self):
        card = self._report_card('📦  گزارش موجودی انبار')

        from desktop.db import get_all_products
        all_products = get_all_products()
        low = [p for p in all_products if (p['stock'] or 0) <= 5]
        out = [p for p in all_products if (p['stock'] or 0) == 0]
        total_items = len(all_products)
        total_stock = sum(p['stock'] or 0 for p in all_products)

        grid = tk.Frame(card, bg=Colors.card)
        grid.pack(fill='x')
        self._make_cards(grid, [
            ('کل محصولات', str(total_items), Colors.blue),
            ('موجودی کل', str(total_stock), Colors.success),
            ('کم‌موجودی', str(len(low)), Colors.warning),
            ('اتمام موجودی', str(len(out)), Colors.danger),
        ])

        low_items = low_stock_products(5)
        tc = self._table_card()
        tk.Label(tc, text='⚠️  محصولات با موجودی کم (≤۵)',
                 font=get_bold_font(10), bg=Colors.card,
                 fg=Colors.danger).pack(anchor='e', padx=20, pady=(8, 4))

        cols = ('price', 'unit', 'stock', 'category', 'name')
        tree = ttk.Treeview(tc, columns=cols, show='headings', height=12)
        tree.heading('price', text='قیمت فروش', anchor='center')
        tree.heading('unit', text='واحد', anchor='center')
        tree.heading('stock', text='موجودی', anchor='center')
        tree.heading('category', text='دسته', anchor='e')
        tree.heading('name', text='محصول', anchor='e')
        tree.column('price', width=130, anchor='center')
        tree.column('unit', width=80, anchor='center')
        tree.column('stock', width=80, anchor='center')
        tree.column('category', width=160, anchor='e')
        tree.column('name', width=220, anchor='e')

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        for p in low_items:
            tree.insert('', 'end', values=(
                format_number(p['selling_price']),
                p.get('unit') or '—',
                p['stock'],
                p.get('product_type_name') or '—',
                p['name'],
            ))

        if not low_items:
            tk.Label(tc, text='همه محصولات به مقدار کافی موجود هستند',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=20)

    def _debtors_report(self):
        cols = ('debt', 'paid', 'total', 'invoices', 'phone', 'name')
        tree = ttk.Treeview(self.content, columns=cols, show='headings', height=20)
        tree.heading('debt', text='بدهی', anchor='center')
        tree.heading('paid', text='کل پرداخت', anchor='center')
        tree.heading('total', text='کل خرید', anchor='center')
        tree.heading('invoices', text='فاکتورهای باز', anchor='center')
        tree.heading('phone', text='شماره تماس', anchor='center')
        tree.heading('name', text='مشتری', anchor='e')
        for col in cols:
            tree.column(col, width=120, anchor='center')
        tree.column('name', width=220, anchor='e')
        tree.column('invoices', width=110, anchor='center')

        scrollbar = ttk.Scrollbar(self.content, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

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
                format_number(debt),
                format_number(d['paid']),
                format_number(d['total']),
                open_count,
                d.get('phone') or '—',
                f"{d['first_name']} {d['last_name']}",
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
        win.geometry('650x450')
        win.configure(bg=Colors.bg)
        from desktop.db import sale_remaining
        from desktop.utils import format_datetime

        main = tk.Frame(win, bg=Colors.bg, padx=20, pady=16)
        main.pack(fill='both', expand=True)

        tk.Label(main, text=f'📋  فاکتورهای باز - {name}',
                 font=get_bold_font(13), bg=Colors.bg,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))

        tc = tk.Frame(main, bg=Colors.card, highlightbackground=Colors.border,
                      highlightthickness=1)
        tc.pack(fill='both', expand=True)

        cols = ('status', 'remaining', 'amount', 'date', 'id')
        t = ttk.Treeview(tc, columns=cols, show='headings', height=15)
        t.heading('status', text='وضعیت', anchor='center')
        t.heading('remaining', text='باقی‌مانده', anchor='center')
        t.heading('amount', text='مبلغ', anchor='center')
        t.heading('date', text='تاریخ', anchor='center')
        t.heading('id', text='#', anchor='center')
        for col in cols:
            t.column(col, width=100, anchor='center')

        scrollbar = ttk.Scrollbar(tc, orient='vertical', command=t.yview)
        t.configure(yscrollcommand=scrollbar.set)
        t.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        for s in sales:
            rem = sale_remaining(s['id'])
            t.insert('', 'end', values=(
                s['status'],
                format_number(rem),
                format_number(s['total_amount']),
                format_datetime(s['sale_date']),
                s['id'],
            ))

    def _best_selling_report(self):
        cols = ('revenue', 'qty', 'name', 'rank')
        tree = ttk.Treeview(self.content, columns=cols, show='headings', height=20)
        tree.heading('revenue', text='درآمد', anchor='center')
        tree.heading('qty', text='تعداد فروش', anchor='center')
        tree.heading('name', text='محصول', anchor='e')
        tree.heading('rank', text='#', anchor='center')
        tree.column('revenue', width=150, anchor='center')
        tree.column('qty', width=130, anchor='center')
        tree.column('name', width=300, anchor='e')
        tree.column('rank', width=50, anchor='center')

        scrollbar = ttk.Scrollbar(self.content, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        top = best_selling(10)
        for i, p in enumerate(top):
            tree.insert('', 'end', values=(
                format_number(p['rev']),
                p['qty'],
                p['name'],
                i + 1,
            ))

        if not top:
            tk.Label(tree, text='هیچ داده‌ای وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=30)
