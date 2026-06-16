import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from desktop.db import (
    get_all_sales, get_sale, get_all_products, get_product,
    get_sale_items, get_sale_payments, sale_remaining,
    sale_total_paid, update_sale_status,
    create_sale, create_sale_item, create_payment, create_installment,
    get_customer, get_all_customers, fetchall, fetchone,
    get_product_prices
)
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date, format_datetime


class SalesListView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        header = tk.Frame(self.frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text='فروش‌ها', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(side='right')
        tk.Button(header, text='+ فروش جدید', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=16, pady=6,
                  command=self._new_sale).pack(side='left')

        filter_frame = tk.Frame(self.frame, bg='#ffffff',
                                highlightbackground='#e2e8f0', highlightthickness=1)
        filter_frame.pack(fill='x', pady=(0, 12))
        self.status_var = tk.StringVar(value='')
        self.type_var = tk.StringVar(value='')
        ttk.Combobox(filter_frame, textvariable=self.status_var,
                     values=['', 'paid', 'pending', 'partial', 'cancelled'],
                     state='readonly', font=get_font(9), width=15).pack(
                         side='left', padx=8, pady=6)
        ttk.Combobox(filter_frame, textvariable=self.type_var,
                     values=['', 'cash', 'installment'],
                     state='readonly', font=get_font(9), width=15).pack(
                         side='left', padx=8, pady=6)
        tk.Button(filter_frame, text='فیلتر', font=get_font(9),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=12, pady=2, command=self._load).pack(
                      side='left', padx=8, pady=6)

        columns = ('id', 'customer', 'date', 'total', 'remaining', 'type', 'status')
        self.tree = ttk.Treeview(self.frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('id', text='#', anchor='center')
        self.tree.heading('customer', text='مشتری', anchor='e')
        self.tree.heading('date', text='تاریخ', anchor='center')
        self.tree.heading('total', text='مبلغ', anchor='center')
        self.tree.heading('remaining', text='باقی‌مانده', anchor='center')
        self.tree.heading('type', text='نوع', anchor='center')
        self.tree.heading('status', text='وضعیت', anchor='center')
        for col in columns:
            self.tree.column(col, width=110, anchor='center')
        self.tree.column('id', width=50)
        self.tree.column('customer', width=180, anchor='e')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<Double-1>', self._open_detail)

        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        sales = get_all_sales(
            status=self.status_var.get() or None,
            payment_type=self.type_var.get() or None
        )
        status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                      'partial': 'جزئی', 'cancelled': 'لغو'}
        type_map = {'cash': 'نقدی', 'installment': 'قسطی'}
        for s in sales:
            remaining = sale_remaining(s['id'])
            self.tree.insert('', 'end', values=(
                s['id'],
                f"{s['c_first']} {s['c_last']}" if s.get('c_first') else '—',
                format_date(s['sale_date']),
                format_number(s['total_amount']),
                format_number(remaining),
                type_map.get(s['payment_type'], s['payment_type']),
                status_map.get(s['status'], s['status']),
            ))

    def _new_sale(self):
        win = tk.Toplevel(self.frame)
        win.title('ثبت فروش جدید')
        win.geometry('800x600')
        SaleForm(win, self.app, on_save=lambda: (win.destroy(), self._load()))

    def _open_detail(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            win = tk.Toplevel(self.frame)
            win.title(f'فروش #{values[0]}')
            win.geometry('850x650')
            SaleDetailView(win, int(values[0]), self.app)


class SaleForm:
    def __init__(self, parent, app, on_save=None):
        self.app = app
        self.on_save = on_save
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=16, pady=12)

        self.step = 1
        self.selected_customer = None
        self.cart = []
        self.payment_type = 'cash'
        self.down_payment = 0

        self._build_step1()

    def _clear(self):
        for w in self.frame.winfo_children():
            w.destroy()

    def _build_step1(self):
        self._clear()
        tk.Label(self.frame, text='مرحله ۱: انتخاب مشتری',
                 font=get_bold_font(14), bg='#f0f2f5',
                 fg='#1e293b').pack(anchor='e', pady=(0, 12))

        search_var = tk.StringVar()
        search_entry = tk.Entry(self.frame, textvariable=search_var,
                                font=get_font(10), bd=1, relief='solid')
        search_entry.pack(fill='x', ipady=6, pady=(0, 8))

        list_frame = tk.Frame(self.frame, bg='#ffffff',
                              highlightbackground='#e2e8f0', highlightthickness=1)
        list_frame.pack(fill='both', expand=True)

        customers_list = tk.Frame(list_frame, bg='#ffffff')
        customers_list.pack(fill='both', expand=True, padx=4, pady=4)

        def search():
            for w in customers_list.winfo_children():
                w.destroy()
            q = search_var.get().strip()
            customers = get_all_customers(q) if q else get_all_customers()
            for c in customers[:20]:
                btn = tk.Button(customers_list,
                                text=f"{c['first_name']} {c['last_name']} — {c.get('phone') or ''}",
                                font=get_font(9), bg='#ffffff', fg='#334155',
                                bd=0, anchor='w', padx=8, pady=6,
                                cursor='hand2',
                                command=lambda cid=c['id']: self._select_customer(cid))
                btn.pack(fill='x')

        search_var.trace('w', lambda *a: search())
        search()

        nav = tk.Frame(self.frame, bg='#f0f2f5')
        nav.pack(fill='x', pady=(12, 0))
        tk.Button(nav, text='مرحله بعد', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=self._go_step2).pack(side='left')

    def _select_customer(self, cid):
        self.selected_customer = get_customer(cid)

    def _go_step2(self):
        if not self.selected_customer:
            messagebox.showwarning('', 'مشتری را انتخاب کنید')
            return
        self._build_step2()

    def _build_step2(self):
        self._clear()
        tk.Label(self.frame, text='مرحله ۲: انتخاب محصولات',
                 font=get_bold_font(14), bg='#f0f2f5',
                 fg='#1e293b').pack(anchor='e', pady=(0, 12))

        content = tk.Frame(self.frame, bg='#f0f2f5')
        content.pack(fill='both', expand=True)

        left = tk.Frame(content, bg='#ffffff', highlightbackground='#e2e8f0',
                        highlightthickness=1)
        left.pack(side='right', fill='both', expand=True, padx=(6, 0))
        tk.Label(left, text='محصولات', font=get_bold_font(10),
                 bg='#ffffff', fg='#1e293b').pack(anchor='e', padx=8, pady=4)

        prod_frame = tk.Frame(left, bg='#ffffff')
        prod_frame.pack(fill='both', expand=True, padx=4, pady=4)

        for p in get_all_products()[:30]:
            u = p.get('unit') or ''
            btn = tk.Button(prod_frame,
                            text=f"{p['name']} ({u}) — {format_number(p['selling_price'])}",
                            font=get_font(9), bg='#ffffff', fg='#334155',
                            bd=0, anchor='w', padx=8, pady=4,
                            cursor='hand2',
                            command=lambda pid=p['id']: self._add_to_cart(pid))
            btn.pack(fill='x')

        right = tk.Frame(content, bg='#ffffff', highlightbackground='#e2e8f0',
                         highlightthickness=1)
        right.pack(side='right', fill='both', expand=True)
        tk.Label(right, text='سبد خرید', font=get_bold_font(10),
                 bg='#ffffff', fg='#1e293b').pack(anchor='e', padx=8, pady=4)

        self.cart_frame = tk.Frame(right, bg='#ffffff')
        self.cart_frame.pack(fill='both', expand=True, padx=4, pady=4)
        self._render_cart()

        total = sum(item['subtotal'] for item in self.cart)
        total_frame = tk.Frame(right, bg='#f8fafc', highlightbackground='#e2e8f0',
                               highlightthickness=1)
        total_frame.pack(fill='x', padx=4, pady=4)
        tk.Label(total_frame, text=f'جمع کل: {format_number(total)}',
                 font=get_bold_font(12), bg='#f8fafc',
                 fg='#16a34a').pack(anchor='e', padx=8, pady=6)

        nav = tk.Frame(self.frame, bg='#f0f2f5')
        nav.pack(fill='x', pady=(8, 0))
        tk.Button(nav, text='مرحله قبل', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=self._build_step1).pack(side='right', padx=(8, 0))
        tk.Button(nav, text='مرحله بعد', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=self._go_step3).pack(side='left')

    def _add_to_cart(self, pid):
        p = get_product(pid)
        if not p:
            return
        qty = tk.simpledialog.askinteger('مقدار', f'{p["unit"]} {p["name"]}:',
                                         minvalue=1, maxvalue=9999,
                                         parent=self.frame.winfo_toplevel())
        if qty is None:
            return
        prices = get_product_prices(pid)
        price_id = None
        unit_price = p['selling_price']
        avail = [(None, p['selling_price'],
                  f'پیش‌فرض: {format_number(p["selling_price"])} تومان')]
        for pr in prices:
            if pr['stock'] > 0:
                avail.append((pr['id'], pr['amount'],
                              f'{pr["price_label"]}: {format_number(pr["amount"])} تومان (موجودی: {pr["stock"]})'))
        if len(avail) > 1:
            price_win = tk.Toplevel(self.frame.winfo_toplevel())
            price_win.title('انتخاب قیمت')
            price_win.geometry('450x350')
            price_win.configure(bg='#ffffff')
            frm = tk.Frame(price_win, bg='#ffffff', padx=20, pady=16)
            frm.pack(fill='both', expand=True)
            tk.Label(frm, text=f'{p["name"]} - انتخاب قیمت:', font=get_font(10),
                     bg='#ffffff', fg='#1e293b').pack(anchor='e')
            var = tk.StringVar(value=str(avail[0][0]))
            for pid_, amt, label in avail:
                rb = tk.Radiobutton(frm, text=label, variable=var,
                                    value=str(pid_),
                                    font=get_font(9), bg='#ffffff', fg='#475569',
                                    anchor='e', padx=10, pady=4)
                rb.pack(fill='x', pady=2)
            def confirm():
                nonlocal price_id, unit_price
                selected = var.get()
                for pid_, amt, _ in avail:
                    if str(pid_) == selected:
                        price_id = pid_
                        unit_price = amt
                        break
                price_win.destroy()
            tk.Button(frm, text='تأیید', font=get_font(10),
                      bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                      padx=20, pady=4, command=confirm).pack(pady=(12, 0))
            self.frame.wait_window(price_win)
        for item in self.cart:
            if item['product']['id'] == pid:
                item['quantity'] += qty
                item['unit_price'] = unit_price
                item['subtotal'] = item['quantity'] * item['unit_price']
                self._render_cart()
                return
        self.cart.append({
            'product': p,
            'quantity': qty,
            'unit_price': unit_price,
            'subtotal': qty * unit_price,
            'price_id': price_id,
        })
        self._render_cart()

    def _render_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()
        if not self.cart:
            tk.Label(self.cart_frame, text='محصولی انتخاب نشده',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=20)
            return
        for i, item in enumerate(self.cart):
            row = tk.Frame(self.cart_frame, bg='#f9fafb',
                           highlightbackground='#e2e8f0', highlightthickness=1)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=item['product']['name'], font=get_font(9),
                     bg='#f9fafb', fg='#334155').pack(side='right', padx=4)
            unit = item['product'].get('unit') or ''
            tk.Label(row, text=f"{item['quantity']} {unit} × {format_number(item['unit_price'])}",
                     font=get_font(9), bg='#f9fafb',
                     fg='#64748b').pack(side='right', padx=4)
            tk.Label(row, text=format_number(item['subtotal']),
                     font=get_bold_font(9), bg='#f9fafb',
                     fg='#16a34a').pack(side='left', padx=4)
            tk.Button(row, text='✕', font=get_font(8), bg='#f9fafb',
                      fg='#dc2626', bd=0, cursor='hand2',
                      command=lambda idx=i: self._remove_from_cart(idx)).pack(
                          side='left', padx=2)

    def _remove_from_cart(self, idx):
        self.cart.pop(idx)
        self._render_cart()

    def _go_step3(self):
        if not self.cart:
            messagebox.showwarning('', 'محصولی انتخاب نشده')
            return
        self._build_step3()

    def _build_step3(self):
        self._clear()
        tk.Label(self.frame, text='مرحله ۳: نوع پرداخت',
                 font=get_bold_font(14), bg='#f0f2f5',
                 fg='#1e293b').pack(anchor='e', pady=(0, 12))

        form = tk.Frame(self.frame, bg='#ffffff', highlightbackground='#e2e8f0',
                        highlightthickness=1, padx=24, pady=20)
        form.pack(fill='x', pady=12)

        type_frame = tk.Frame(form, bg='#ffffff')
        type_frame.pack(fill='x', pady=(0, 16))

        def set_type(t):
            self.payment_type = t
            for b in type_btns:
                b.configure(bg='#ffffff')
            type_btns[0 if t == 'cash' else 1].configure(bg='#dbeafe')

        type_btns = []
        for t, label in [('cash', 'نقدی'), ('installment', 'قسطی')]:
            btn = tk.Button(type_frame, text=label, font=get_font(12),
                            bg='#dbeafe' if t == 'cash' else '#ffffff',
                            fg='#1e293b', bd=1, relief='solid',
                            cursor='hand2', padx=40, pady=12,
                            command=lambda vt=t: set_type(vt))
            btn.pack(side='right', padx=(8, 0))
            type_btns.append(btn)

        self.dp_var = tk.StringVar()
        dp_frame = tk.Frame(form, bg='#ffffff')
        dp_frame.pack(fill='x', pady=(0, 12))
        tk.Label(dp_frame, text='پیش‌پرداخت:', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right')
        tk.Entry(dp_frame, textvariable=self.dp_var, font=get_font(10),
                 bd=1, relief='solid', width=20).pack(side='right', padx=(8, 0))

        self.due_days_var = tk.StringVar(value='0')
        due_frame = tk.Frame(form, bg='#ffffff')
        due_frame.pack(fill='x', pady=(0, 12))
        tk.Label(due_frame, text='مهلت پرداخت (روز):', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right')
        tk.Spinbox(due_frame, from_=0, to=365, textvariable=self.due_days_var,
                   font=get_font(10), bd=1, relief='solid', width=10).pack(
                       side='right', padx=(8, 0))
        tk.Label(due_frame, text='(صفر = نقدی)', font=get_font(8),
                 bg='#ffffff', fg='#94a3b8').pack(side='right')

        notes_frame = tk.Frame(form, bg='#ffffff')
        notes_frame.pack(fill='x', pady=(0, 12))
        tk.Label(notes_frame, text='یادداشت:', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right')
        self.notes_text = tk.Text(notes_frame, font=get_font(10),
                                  bd=1, relief='solid', height=3)
        self.notes_text.pack(side='right', fill='x', expand=True, padx=(8, 0))

        total = sum(item['subtotal'] for item in self.cart)
        info = tk.Frame(form, bg='#f8fafc', highlightbackground='#e2e8f0',
                        highlightthickness=1, padx=12, pady=8)
        info.pack(fill='x')
        c = self.selected_customer
        tk.Label(info, text=f"مشتری: {c['first_name']} {c['last_name']}",
                 font=get_font(9), bg='#f8fafc', fg='#334155').pack(anchor='e')
        tk.Label(info, text=f'مبلغ کل: {format_number(total)}',
                 font=get_bold_font(12), bg='#f8fafc',
                 fg='#16a34a').pack(anchor='e')

        nav = tk.Frame(self.frame, bg='#f0f2f5')
        nav.pack(fill='x', pady=(8, 0))
        tk.Button(nav, text='مرحله قبل', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=self._build_step2).pack(side='right', padx=(8, 0))
        tk.Button(nav, text='ثبت فروش', font=get_font(10),
                  bg='#16a34a', fg='#ffffff', bd=0, cursor='hand2',
                  padx=20, pady=6, command=self._submit).pack(side='left')

    def _submit(self):
        total = sum(item['subtotal'] for item in self.cart)
        dp = int(self.dp_var.get() or 0)
        notes = self.notes_text.get('1.0', 'end-1c').strip()

        for item in self.cart:
            p = item['product']
            pdata = get_product(p['id'])
            if not pdata or (pdata['stock'] or 0) < item['quantity']:
                messagebox.showwarning(
                    'موجودی ناکافی',
                    f"موجودی {p['name']} کافی نیست\n"
                    f"موجودی فعلی: {pdata['stock'] if pdata else 0}"
                )
                return

        customer_id = self.selected_customer['id']
        due_days = int(self.due_days_var.get() or 0)
        if self.payment_type == 'installment' or due_days > 0:
            status = 'pending'
        else:
            status = 'paid'

        sale_id = create_sale(customer_id, total, self.payment_type, status, notes,
                              payment_due_days=due_days)

        for item in self.cart:
            p = item['product']
            create_sale_item(sale_id, p['id'], item['quantity'], item['unit_price'], item['subtotal'],
                             price_id=item.get('price_id'))

        if self.payment_type == 'cash':
            create_payment(sale_id, customer_id, total, 'cash', '')
        elif self.payment_type == 'installment' and dp > 0:
            create_payment(sale_id, customer_id, dp, 'down_payment', '')
            remaining = total - dp
            if remaining > 0:
                count = 6
                per_term = max(1, remaining // count)
                from desktop.db import execute as db_execute
                db_execute(
                    "INSERT INTO store_installment (sale_id, customer_id, total_count, paid_count, amount_per_term, due_day, status, start_date, amount_paid) VALUES (?,?,?,0,?,1,'active',date('now'),?)",
                    [sale_id, customer_id, count, per_term, dp]
                )

        if self.on_save:
            self.on_save()


class SaleDetailView:
    def __init__(self, parent, sale_id, app):
        self.app = app
        self._parent = parent
        self._sale_id = sale_id
        sale = get_sale(sale_id)
        if not sale:
            tk.Label(parent, text='فروش یافت نشد').pack()
            return

        self.frame = tk.Frame(parent, bg='#f0f2f5', padx=20, pady=16)
        self.frame.pack(fill='both', expand=True)

        self._build(sale)

    def _build(self, sale):
        sale_id = self._sale_id
        frame = self.frame

        header = tk.Frame(frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 12))
        status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                      'partial': 'جزئی', 'cancelled': 'لغو'}
        tk.Label(header, text=f'فروش #{sale["id"]}',
                 font=get_bold_font(16), bg='#f0f2f5',
                 fg='#1e293b').pack(side='right')
        tk.Label(header, text=status_map.get(sale['status'], sale['status']),
                 font=get_font(10), bg='#f0f2f5').pack(side='left')

        remaining = sale_remaining(sale_id)
        if remaining > 0:
            tk.Button(header, text='+ ثبت پرداخت', font=get_font(10),
                      bg='#16a34a', fg='#ffffff', bd=0, cursor='hand2',
                      padx=14, pady=4,
                      command=lambda: self._add_payment(sale_id)).pack(
                          side='left', padx=(8, 0))

        info_card = tk.Frame(frame, bg='#ffffff', highlightbackground='#e2e8f0',
                             highlightthickness=1, padx=16, pady=12)
        info_card.pack(fill='x', pady=(0, 12))

        customer = get_customer(sale['customer_id'])
        for label, val in [
            ('مشتری', f"{customer['first_name']} {customer['last_name']}" if customer else '—'),
            ('تاریخ', format_datetime(sale['sale_date'])),
            ('نوع', 'نقدی' if sale['payment_type'] == 'cash' else 'قسطی'),
            ('مبلغ کل', format_number(sale['total_amount'])),
            ('باقی‌مانده', format_number(remaining)),
        ]:
            row = tk.Frame(info_card, bg='#ffffff')
            row.pack(fill='x', pady=1)
            tk.Label(row, text=label, font=get_font(9), bg='#ffffff',
                     fg='#64748b', width=12, anchor='e').pack(side='right')
            tk.Label(row, text=val, font=get_bold_font(9), bg='#ffffff',
                     fg='#334155').pack(side='right', padx=(8, 0))

        tk.Label(frame, text='اقلام', font=get_bold_font(12),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 8))

        items = get_sale_items(sale_id)
        if items:
            cols = ('product', 'qty', 'price', 'subtotal')
            tree = ttk.Treeview(frame, columns=cols, show='headings', height=6)
            tree.heading('product', text='محصول', anchor='e')
            tree.heading('qty', text='تعداد', anchor='center')
            tree.heading('price', text='قیمت واحد', anchor='center')
            tree.heading('subtotal', text='جمع', anchor='center')
            tree.column('product', width=250, anchor='e')
            tree.column('qty', width=80, anchor='center')
            tree.column('price', width=100, anchor='center')
            tree.column('subtotal', width=100, anchor='center')
            tree.pack(fill='x', pady=(0, 12))
            for item in items:
                tree.insert('', 'end', values=(
                    item.get('product_name') or '—',
                    item['quantity'], format_number(item['unit_price']),
                    format_number(item['subtotal']),
                ))

        tk.Label(frame, text='پرداخت‌ها', font=get_bold_font(12),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 8))

        payments = get_sale_payments(sale_id)
        if payments:
            cols = ('id', 'date', 'amount', 'type')
            tree2 = ttk.Treeview(frame, columns=cols, show='headings', height=5)
            tree2.heading('id', text='#')
            tree2.heading('date', text='تاریخ')
            tree2.heading('amount', text='مبلغ')
            tree2.heading('type', text='نوع')
            tree2.column('id', width=50, anchor='center')
            tree2.column('date', width=120, anchor='center')
            tree2.column('amount', width=120, anchor='center')
            tree2.column('type', width=100, anchor='center')
            tree2.pack(fill='x', pady=(0, 12))
            for p in payments:
                tree2.insert('', 'end', values=(
                    p['id'], format_date(p['payment_date']),
                    format_number(p['amount']),
                    p['payment_type'],
                ))

    def _add_payment(self, sale_id):
        sale = get_sale(sale_id)
        remaining = sale_remaining(sale_id)
        if remaining <= 0:
            messagebox.showinfo('', 'این فاکتور تسویه شده است')
            return
        amt = tk.simpledialog.askinteger('ثبت پرداخت',
                                         f'مبلغ پرداختی (باقی‌مانده: {format_number(remaining)}):',
                                         minvalue=1, maxvalue=remaining,
                                         parent=self.frame.winfo_toplevel())
        if amt is None:
            return
        create_payment(sale_id, sale['customer_id'], amt, 'cash', '')
        update_sale_status(sale_id)
        messagebox.showinfo('', 'پرداخت با موفقیت ثبت شد')
        for w in self.frame.winfo_children():
            w.destroy()
        sale = get_sale(sale_id)
        self._build(sale)
