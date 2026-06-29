import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    get_all_sales, get_sale, get_all_products, get_product,
    get_sale_items, get_sale_payments, sale_remaining,
    sale_total_paid, update_sale_status,
    create_sale, create_sale_item, create_payment, create_installment,
    get_customer, get_all_customers, create_customer, fetchall, fetchone,
    get_product_prices, get_installments, delete_payment, update_payment
)
from desktop.theme import Colors, get_font, get_bold_font
from desktop.utils import format_number, format_date, format_datetime, add_number_comma_formatting, clean_number, persian_askinteger, persian_askfloat, persian_digits, validate_phone, make_dialog




def _make_button(parent, text, bg, active_bg, command):
    return tk.Button(parent, text=text, font=get_font(10),
                     bg=bg, fg='#ffffff', bd=0, cursor='hand2',
                     padx=18, pady=8, activebackground=active_bg,
                     command=command)


class SalesListView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='فروش‌ها', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')
        _make_button(header, '➕  فروش جدید', Colors.accent, Colors.accent_hover,
                     self._new_sale).pack(side='left')

        self._sort_col = None
        self._sort_rev = False
        self._all_data = []

        filter_card = tk.Frame(self.frame, bg=Colors.card,
                                highlightbackground=Colors.border, highlightthickness=1,
                                padx=12, pady=8)
        filter_card.pack(fill='x', pady=(0, 12))

        self.filter_vars = {}
        cols_cfg = [
            ('status', 'وضعیت', 100, ['', 'تسویه', 'در انتظار', 'جزئی', 'لغو']),
            ('type', 'نوع', 100, ['', 'نقدی', 'قسطی']),
            ('remaining', 'باقی‌مانده', 130, []),
            ('total', 'مبلغ', 130, []),
            ('date', 'تاریخ', 120, []),
            ('customer', 'مشتری', 200, []),
            ('id', '#', 50, []),
        ]
        self._filter_combos = {}
        for key, label, width, values in cols_cfg:
            f = tk.Frame(filter_card, bg=Colors.card)
            f.pack(side='right', padx=1)
            tk.Label(f, text=label, font=get_font(8), bg=Colors.card,
                     fg=Colors.text_muted).pack(anchor='center')
            var = tk.StringVar(value='')
            var.trace('w', lambda *_: self._load())
            self.filter_vars[key] = var
            w = ttk.Combobox(f, textvariable=var, values=values,
                             state='readonly', font=get_font(9), width=max(1, width // 8))
            w.pack(ipady=1)
            self._filter_combos[key] = w

        table_card = tk.Frame(self.frame, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1)
        table_card.pack(fill='both', expand=True)

        columns = ('status', 'type', 'remaining', 'total', 'date', 'customer', 'id')
        self.tree = ttk.Treeview(table_card, columns=columns,
                                 show='headings', height=20)
        self.tree.tag_configure('even', background=Colors.card)
        self.tree.tag_configure('odd', background=Colors.border_light)

        col_headers = {
            'status': 'وضعیت', 'type': 'نوع', 'remaining': 'باقی‌مانده',
            'total': 'مبلغ', 'date': 'تاریخ', 'customer': 'مشتری', 'id': '#'
        }
        col_widths = {
            'status': 100, 'type': 100, 'remaining': 130,
            'total': 130, 'date': 120, 'customer': 200, 'id': 50
        }
        col_anchors = {
            'status': 'center', 'type': 'center', 'remaining': 'center',
            'total': 'center', 'date': 'center', 'customer': 'e', 'id': 'center'
        }
        for col in columns:
            self.tree.heading(col, text=col_headers[col], anchor='center',
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=col_widths[col], anchor=col_anchors[col])

        scrollbar = ttk.Scrollbar(table_card, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self.tree.bind('<Double-1>', self._open_detail)

        self._load()

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        sales = get_all_sales()
        status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                      'partial': 'جزئی', 'cancelled': 'لغو'}
        type_map = {'cash': 'نقدی', 'installment': 'قسطی'}
        fv = {k: v.get().strip() for k, v in self.filter_vars.items()}
        rows = []
        uniq = {'remaining': set(), 'total': set(), 'date': set(), 'customer': set(), 'id': set()}
        for s in sales:
            remaining = sale_remaining(s['id'])
            row = (
                status_map.get(s['status'], s['status']),
                type_map.get(s['payment_type'], s['payment_type']),
                format_number(remaining),
                format_number(s['total_amount']),
                format_date(s['sale_date']),
                f"{s['c_first']} {s['c_last']}" if s.get('c_first') else '—',
                str(s['id']),
            )
            uniq['remaining'].add(row[2])
            uniq['total'].add(row[3])
            uniq['date'].add(row[4])
            uniq['customer'].add(row[5])
            uniq['id'].add(row[6])
            if fv['status'] and fv['status'].lower() not in row[0].lower():
                continue
            if fv['type'] and fv['type'].lower() not in row[1].lower():
                continue
            if fv['remaining'] and fv['remaining'] not in row[2]:
                continue
            if fv['total'] and fv['total'] not in row[3]:
                continue
            if fv['date'] and fv['date'] not in row[4]:
                continue
            if fv['customer'] and fv['customer'].lower() not in row[5].lower():
                continue
            if fv['id'] and fv['id'] not in row[6]:
                continue
            sort_key = row[{'status': 0, 'type': 1, 'remaining': 2, 'total': 3,
                            'date': 4, 'customer': 5, 'id': 6}.get(self._sort_col, 0)]
            if self._sort_col in ('remaining', 'total', 'id'):
                try:
                    sort_key = int(clean_number(sort_key))
                except Exception:
                    sort_key = 0
            rows.append((sort_key, row))
        if self._sort_col:
            rows.sort(key=lambda x: x[0], reverse=self._sort_rev)
        for i, (_, row) in enumerate(rows):
            self.tree.insert('', 'end', values=row, tags=('even' if i % 2 == 0 else 'odd',))
        for key in uniq:
            vals = sorted(uniq[key], key=lambda x: int(clean_number(x)) if key in ('remaining', 'total', 'id') else x)
            self._filter_combos[key]['values'] = ['', *vals]

    def _new_sale(self):
        win = make_dialog(self.frame, 'ثبت فروش جدید', 850, 650)
        win.configure(bg=Colors.bg)
        SaleForm(win, self.app, on_save=lambda: (win.destroy(), self._load()))

    def _open_detail(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            win = make_dialog(self.frame, f'فروش #{values[-1]}', 900, 680)
            win.configure(bg=Colors.bg)
            SaleDetailView(win, int(values[-1]), self.app)


class SaleForm:
    def __init__(self, parent, app, on_save=None):
        self.app = app
        self.on_save = on_save
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=20, pady=16)

        self.step = 1
        self.selected_customer = None
        self.cart = []
        self.payment_type = 'cash'
        self.down_payment = 0

        self._build_step1()

    def _clear(self):
        for w in self.frame.winfo_children():
            w.destroy()

    def _nav_buttons(self, back_cmd=None, next_text=None, next_cmd=None):
        nav = tk.Frame(self.frame, bg=Colors.bg)
        nav.pack(fill='x', pady=(12, 0))

        if next_cmd:
            btn_color = Colors.success if next_text == 'ثبت فروش' else Colors.accent
            btn_hover = Colors.success_hover if next_text == 'ثبت فروش' else Colors.accent_hover
            _make_button(nav, next_text, btn_color, btn_hover, next_cmd).pack(side='left')

        if back_cmd:
            _make_button(nav, '⬅  مرحله قبل', Colors.text_muted, Colors.border,
                         back_cmd).pack(side='right')

        return nav

    def _step_indicator(self, current):
        steps_frame = tk.Frame(self.frame, bg=Colors.bg)
        steps_frame.pack(fill='x', pady=(0, 16))

        for i, label in enumerate(['انتخاب مشتری', 'محصولات', 'پرداخت'], 1):
            f = tk.Frame(steps_frame, bg=Colors.card if i == current else Colors.border,
                         padx=14, pady=6)
            f.pack(side='right', padx=(4, 0))
            tk.Label(f, text=f'{i}. {label}', font=get_font(9),
                     bg=Colors.card if i == current else Colors.border,
                     fg=Colors.accent if i == current else Colors.text_muted).pack()

    def _build_step1(self):
        self._clear()
        self._selected_customer_btn = None
        self._step_indicator(1)
        tk.Label(self.frame, text='مرحله ۱: انتخاب مشتری',
                 font=get_bold_font(14), bg=Colors.bg,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))

        search_card = tk.Frame(self.frame, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1,
                               padx=4, pady=4)
        search_card.pack(fill='x', pady=(0, 12))

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_card, textvariable=search_var,
                                font=get_font(10), bd=0, bg=Colors.card,
                                fg=Colors.text_primary)
        search_entry.pack(fill='x', ipady=8, padx=8)
        search_placeholder = tk.Label(search_card, text='🔍  جستجوی مشتری...',
                                      font=get_font(9), bg=Colors.card,
                                      fg=Colors.text_muted)
        search_placeholder.pack()

        def on_search_focus_in(e):
            search_placeholder.pack_forget()
            search_entry.focus()

        def on_search_focus_out(e):
            if not search_entry.get():
                search_placeholder.pack()

        search_entry.bind('<FocusIn>', on_search_focus_in)
        search_placeholder.bind('<Button-1>', on_search_focus_in)

        list_card = tk.Frame(self.frame, bg=Colors.card,
                             highlightbackground=Colors.border, highlightthickness=1)
        list_card.pack(fill='both', expand=True)

        customers_list = tk.Frame(list_card, bg=Colors.card)
        customers_list.pack(fill='both', expand=True, padx=4, pady=4)

        def search():
            for w in customers_list.winfo_children():
                w.destroy()
            self._selected_customer_btn = None
            q = search_var.get().strip()
            customers = get_all_customers(q) if q else get_all_customers()
            for c in customers[:20]:
                btn = tk.Button(customers_list,
                                text=f"{c['first_name']} {c['last_name']} — {c.get('phone') or ''}",
                                font=get_font(9), bg=Colors.card, fg=Colors.text_secondary,
                                bd=0, anchor='w', padx=12, pady=8,
                                cursor='hand2')
                btn.configure(command=lambda cid=c['id'], b=btn: self._select_customer(cid, b))
                btn.pack(fill='x', pady=1)
                if self.selected_customer and c['id'] == self.selected_customer['id']:
                    btn.configure(bg=Colors.accent_light, fg=Colors.accent)
                    self._selected_customer_btn = btn

            if not customers:
                add_frame = tk.Frame(customers_list, bg=Colors.card)
                add_frame.pack(fill='x', padx=8, pady=8)

                tk.Label(add_frame, text='مشتری یافت نشد. مشتری جدید اضافه کنید:',
                         font=get_font(9), bg=Colors.card, fg=Colors.danger).pack(anchor='e', pady=(0, 8))

                for label, key in [('نام:', 'first_name'), ('نام خانوادگی:', 'last_name'), ('تلفن:', 'phone')]:
                    r = tk.Frame(add_frame, bg=Colors.card)
                    r.pack(fill='x', pady=2)
                    tk.Label(r, text=label, font=get_font(9), bg=Colors.card,
                             fg=Colors.text_secondary, width=12, anchor='e').pack(side='right')
                    var = tk.StringVar()
                    setattr(add_frame, key, var)
                    entry = tk.Entry(r, textvariable=var, font=get_font(9),
                                     bd=1, relief='solid', bg=Colors.card,
                                     highlightbackground=Colors.border,
                                     highlightcolor=Colors.accent,
                                     highlightthickness=1)
                    entry.pack(side='right', fill='x', expand=True, padx=(8, 0), ipady=3)

                def add_customer():
                    first_name = add_frame.first_name.get().strip()
                    last_name = add_frame.last_name.get().strip()
                    phone = add_frame.phone.get().strip()
                    if not first_name:
                        messagebox.showwarning('', 'نام الزامی است')
                        return
                    try:
                        phone = validate_phone(phone)
                    except ValueError as e:
                        messagebox.showwarning('خطا', str(e))
                        return
                    data = {'first_name': first_name, 'last_name': last_name, 'phone': phone}
                    create_customer(data)
                    customers = get_all_customers(phone or first_name)
                    if customers:
                        self._select_customer(customers[0]['id'])
                        search_var.set('')
                        search()

                tk.Button(add_frame, text='➕  افزودن مشتری', font=get_font(9),
                          bg=Colors.accent, fg='#ffffff', bd=0, cursor='hand2',
                          padx=16, pady=6, command=add_customer).pack(pady=(6, 0))

        search_var.trace('w', lambda *a: search())
        search()

        self._nav_buttons(next_text='مرحله بعد ➡', next_cmd=self._go_step2)

    def _select_customer(self, cid, btn=None):
        self.selected_customer = get_customer(cid)
        if self._selected_customer_btn and self._selected_customer_btn.winfo_exists():
            self._selected_customer_btn.configure(bg=Colors.card, fg=Colors.text_secondary)
        if btn:
            btn.configure(bg=Colors.accent_light, fg=Colors.accent)
            self._selected_customer_btn = btn

    def _go_step2(self):
        if not self.selected_customer:
            messagebox.showwarning('', 'مشتری را انتخاب کنید')
            return
        self._build_step2()

    def _build_step2(self):
        self._clear()
        self._step_indicator(2)
        tk.Label(self.frame, text='مرحله ۲: انتخاب محصولات',
                 font=get_bold_font(14), bg=Colors.bg,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))

        content = tk.Frame(self.frame, bg=Colors.bg)
        content.pack(fill='both', expand=True)
        content.grid_columnconfigure(0, weight=2, uniform='col')
        content.grid_columnconfigure(1, weight=3, uniform='col')
        content.grid_rowconfigure(0, weight=1)

        right = tk.Frame(content, bg=Colors.card, highlightbackground=Colors.border,
                         highlightthickness=1)
        right.grid(row=0, column=0, sticky='nsew', padx=(6, 0))
        tk.Label(right, text='🛒  سبد خرید', font=get_bold_font(10),
                 bg=Colors.card, fg=Colors.text_primary).pack(anchor='e', padx=10, pady=6)

        cart_canvas = tk.Canvas(right, bg=Colors.card, bd=0, highlightthickness=0)
        cart_scroll = ttk.Scrollbar(right, orient='vertical', command=cart_canvas.yview)
        self.cart_frame = tk.Frame(cart_canvas, bg=Colors.card)
        def _on_cart_configure(e):
            cart_canvas.configure(scrollregion=cart_canvas.bbox('all'))
            cart_canvas.itemconfigure('cart', width=cart_canvas.winfo_width())
        self.cart_frame.bind('<Configure>', _on_cart_configure)
        cart_canvas.create_window((0, 0), window=self.cart_frame, anchor='nw', tags='cart')
        cart_canvas.configure(yscrollcommand=cart_scroll.set)
        cart_canvas.pack(side='right', fill='both', expand=True, padx=4, pady=4)
        cart_scroll.pack(side='left', fill='y')
        self._total_frame = tk.Frame(right, bg=Colors.bg, highlightbackground=Colors.border,
                                     highlightthickness=1, padx=12, pady=8)
        self._total_frame.pack(fill='x', padx=4, pady=4)
        self._render_cart()

        left = tk.Frame(content, bg=Colors.card, highlightbackground=Colors.border,
                        highlightthickness=1)
        left.grid(row=0, column=1, sticky='nsew')
        tk.Label(left, text='📦  محصولات', font=get_bold_font(10),
                 bg=Colors.card, fg=Colors.text_primary).pack(anchor='e', padx=10, pady=6)

        prod_canvas = tk.Canvas(left, bg=Colors.card, bd=0, highlightthickness=0)
        prod_scroll = ttk.Scrollbar(left, orient='vertical', command=prod_canvas.yview)
        prod_frame = tk.Frame(prod_canvas, bg=Colors.card)
        def _on_prod_configure(e):
            prod_canvas.configure(scrollregion=prod_canvas.bbox('all'))
            prod_canvas.itemconfigure('prod', width=prod_canvas.winfo_width())
        prod_frame.bind('<Configure>', _on_prod_configure)
        prod_canvas.create_window((0, 0), window=prod_frame, anchor='nw', tags='prod')
        prod_canvas.configure(yscrollcommand=prod_scroll.set)
        prod_canvas.pack(side='right', fill='both', expand=True, padx=4, pady=4)
        prod_scroll.pack(side='left', fill='y')

        def _on_mousewheel(event):
            if event.num == 4:
                prod_canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                prod_canvas.yview_scroll(1, 'units')
            else:
                prod_canvas.yview_scroll(-1 * (event.delta // 120), 'units')
        prod_canvas.bind('<Enter>', lambda e: prod_canvas.bind_all('<MouseWheel>', _on_mousewheel))
        prod_canvas.bind('<Leave>', lambda e: prod_canvas.unbind_all('<MouseWheel>'))
        prod_canvas.bind('<Button-4>', _on_mousewheel)
        prod_canvas.bind('<Button-5>', _on_mousewheel)

        for p in get_all_products()[:30]:
            u = p.get('unit') or ''
            prices = get_product_prices(p['id'])
            prices_with_stock = [pr for pr in prices if pr['stock'] > 0]

            if (p['stock'] or 0) > 0:
                btn = tk.Button(prod_frame,
                                text=f"{p['name']} ({u}) — {format_number(p['selling_price'])} (موجودی: {persian_digits(p['stock'])})",
                                font=get_font(9), bg=Colors.card, fg=Colors.text_secondary,
                                bd=0, anchor='w', padx=10, pady=6,
                                cursor='hand2',
                                command=lambda pid=p['id']: self._add_to_cart(pid))
                btn.pack(fill='x', pady=1)

            for pr in prices_with_stock:
                btn = tk.Button(prod_frame,
                                text=f"{p['name']} ({u}) — {pr['price_label']}: {format_number(pr['amount'])} (موجودی: {persian_digits(pr['stock'])})",
                                font=get_font(9), bg=Colors.card, fg=Colors.accent,
                                bd=0, anchor='w', padx=10, pady=6,
                                cursor='hand2',
                                command=lambda pid=p['id'], ppr=pr: self._add_to_cart(pid, price_id=ppr['id'], preset_price=ppr['amount'], preset_label=ppr['price_label']))
                btn.pack(fill='x', pady=1)

        self._nav_buttons(back_cmd=self._build_step1,
                          next_text='مرحله بعد ➡', next_cmd=self._go_step3)

    _FLOAT_UNITS = {'کیلوگرم', 'گرم', 'لیتر', 'متر'}

    def _add_to_cart(self, pid, price_id=None, preset_price=None, preset_label=None):
        p = get_product(pid)
        if not p:
            return
        if price_id:
            pp = fetchone("SELECT stock FROM store_product_price WHERE id=?", [price_id])
            avail = pp['stock'] if pp else 0
        else:
            avail = p['stock'] or 0
        if avail <= 0:
            messagebox.showwarning('موجودی ناکافی', f'موجودی {p["name"]} به اتمام رسیده')
            return
        is_float = p.get('unit') in self._FLOAT_UNITS
        max_qty = min(float(avail), 9999) if is_float else min(avail, 9999)
        qty = persian_askfloat('مقدار', f'{p["unit"]} {p["name"]}: (موجودی: {persian_digits(avail)})',
                               minvalue=0.1 if is_float else 1, maxvalue=max_qty,
                               parent=self.frame.winfo_toplevel()) if is_float else \
               persian_askinteger('مقدار', f'{p["unit"]} {p["name"]}: (موجودی: {persian_digits(avail)})',
                                  minvalue=1, maxvalue=max_qty,
                                  parent=self.frame.winfo_toplevel())
        if qty is None:
            return
        if preset_price is not None:
            unit_price = preset_price
        else:
            unit_price = p['selling_price']

        for item in self.cart:
            if item['product']['id'] == pid and item.get('price_id') == price_id:
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
            'price_label': preset_label,
        })
        self._render_cart()

    def _update_total(self):
        if not hasattr(self, '_total_frame'):
            return
        total = sum(item['subtotal'] for item in self.cart)
        for w in self._total_frame.winfo_children():
            w.destroy()
        tk.Label(self._total_frame, text=f'جمع کل: {format_number(total)} تومان',
                 font=get_bold_font(14), bg=Colors.bg,
                 fg=Colors.accent).pack(anchor='e')

    def _render_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()
        self._update_total()
        if not self.cart:
            tk.Label(self.cart_frame, text='🛒  محصولی انتخاب نشده',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=20)
            return
        for i, item in enumerate(self.cart):
            row = tk.Frame(self.cart_frame, bg=Colors.bg,
                           highlightbackground=Colors.border, highlightthickness=1)
            row.pack(fill='x', pady=2)

            tk.Button(row, text='✕', font=get_font(8), bg=Colors.bg,
                      fg=Colors.danger, bd=0, cursor='hand2',
                      command=lambda idx=i: self._remove_from_cart(idx)).pack(
                          side='left', padx=4)

            name_text = item['product']['name']
            if item.get('price_label'):
                name_text += f" ({item['price_label']})"
            tk.Label(row, text=name_text, font=get_font(9),
                     bg=Colors.bg, fg=Colors.text_secondary).pack(side='right', padx=6)

            tk.Label(row, text=f"{format_number(item['unit_price'])} × {persian_digits(item['quantity'])}",
                     font=get_font(9), bg=Colors.bg,
                     fg=Colors.text_muted).pack(side='right', padx=4)

            tk.Label(row, text=format_number(item['subtotal']),
                     font=get_bold_font(9), bg=Colors.bg,
                     fg=Colors.accent).pack(side='left', padx=4)

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
        self._step_indicator(3)
        tk.Label(self.frame, text='مرحله ۳: نوع پرداخت',
                 font=get_bold_font(14), bg=Colors.bg,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))

        form_card = tk.Frame(self.frame, bg=Colors.card, highlightbackground=Colors.border,
                             highlightthickness=1, padx=28, pady=24)
        form_card.pack(fill='x', pady=12)

        type_frame = tk.Frame(form_card, bg=Colors.card)
        type_frame.pack(fill='x', pady=(0, 20))

        self.dp_var = tk.StringVar()
        self.dp_frame = tk.Frame(form_card, bg=Colors.card)
        tk.Label(self.dp_frame, text='پیش‌پرداخت:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        dp_entry = tk.Entry(self.dp_frame, textvariable=self.dp_var, font=get_font(10),
                 bd=1, relief='solid', bg=Colors.card,
                 highlightbackground=Colors.border,
                 highlightcolor=Colors.accent,
                 highlightthickness=1, width=22)
        dp_entry.pack(side='right', padx=(10, 0), ipady=4)
        add_number_comma_formatting(self.dp_var, dp_entry)

        self.due_frame = tk.Frame(form_card, bg=Colors.card)
        self.due_days_var = tk.StringVar(value='0')
        tk.Label(self.due_frame, text='مهلت پرداخت (روز):', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        sp = tk.Spinbox(self.due_frame, from_=0, to=365, textvariable=self.due_days_var,
                        font=get_font(10), bd=1, relief='solid', bg=Colors.card,
                        highlightbackground=Colors.border,
                        width=8)
        sp.pack(side='right', padx=(10, 0), ipady=4)
        tk.Label(self.due_frame, text='روز', font=get_font(8),
                 bg=Colors.card, fg=Colors.text_muted).pack(side='right', padx=(4, 0))

        self.inst_count_frame = tk.Frame(form_card, bg=Colors.card)
        self.inst_count_var = tk.StringVar(value='6')
        tk.Label(self.inst_count_frame, text='تعداد اقساط:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        sp2 = tk.Spinbox(self.inst_count_frame, from_=1, to=60, textvariable=self.inst_count_var,
                         font=get_font(10), bd=1, relief='solid', bg=Colors.card,
                         highlightbackground=Colors.border,
                         width=8)
        sp2.pack(side='right', padx=(10, 0), ipady=4)
        tk.Label(self.inst_count_frame, text='قسط', font=get_font(8),
                 bg=Colors.card, fg=Colors.text_muted).pack(side='right', padx=(4, 0))

        self.inst_amt_frame = tk.Frame(form_card, bg=Colors.card)
        self.inst_amt_label = tk.Label(self.inst_amt_frame, text='', font=get_bold_font(11),
                                       bg=Colors.card, fg=Colors.accent)
        self.inst_amt_label.pack(anchor='e')

        def _update_inst_amt(*_):
            total = sum(item['subtotal'] for item in self.cart)
            dp = int(clean_number(self.dp_var.get() or '0'))
            count = int(clean_number(self.inst_count_var.get() or '6'))
            remaining = max(0, total - dp)
            per_term = max(1, remaining // count) if count > 0 else 0
            self.inst_amt_label.config(
                text=f'مبلغ هر قسط: {format_number(per_term)} تومان ({format_number(count)} قسط)'
            )

        self.dp_var.trace_add('write', _update_inst_amt)
        self.inst_count_var.trace_add('write', _update_inst_amt)

        def set_type(t):
            self.payment_type = t
            for b in type_btns:
                b.configure(bg=Colors.card, fg=Colors.text_secondary)
            type_btns[0 if t == 'cash' else 1].configure(bg=Colors.accent_light,
                                                           fg=Colors.accent)
            if t == 'cash':
                self.dp_frame.pack_forget()
                self.due_frame.pack_forget()
                self.inst_count_frame.pack_forget()
                self.inst_amt_frame.pack_forget()
            else:
                self.due_days_var.set('30')
                self.dp_frame.pack(fill='x', pady=(0, 12))
                self.due_frame.pack(fill='x', pady=(0, 12))
                self.inst_count_frame.pack(fill='x', pady=(0, 12))
                self.inst_amt_frame.pack(fill='x', pady=(0, 12))
                _update_inst_amt()

        type_btns = []
        for t, label in [('cash', '💰  نقدی'), ('installment', '📅  قسطی')]:
            btn = tk.Button(type_frame, text=label, font=get_font(12),
                            bg=Colors.card,
                            fg=Colors.text_secondary,
                            bd=1, relief='solid', cursor='hand2',
                            highlightbackground=Colors.border,
                            padx=40, pady=12,
                            command=lambda vt=t: set_type(vt))
            btn.pack(side='right', padx=(8, 0))
            type_btns.append(btn)
        set_type('cash')

        notes_frame = tk.Frame(form_card, bg=Colors.card)
        notes_frame.pack(fill='x', pady=(0, 12))
        tk.Label(notes_frame, text='یادداشت:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        self.notes_text = tk.Text(notes_frame, font=get_font(10),
                                  bd=1, relief='solid', bg=Colors.card,
                                  highlightbackground=Colors.border,
                                  highlightcolor=Colors.accent,
                                  highlightthickness=1, height=3)
        self.notes_text.pack(side='right', fill='x', expand=True, padx=(10, 0))

        total = sum(item['subtotal'] for item in self.cart)
        c = self.selected_customer
        info = tk.Frame(form_card, bg=Colors.bg, highlightbackground=Colors.border,
                        highlightthickness=1, padx=16, pady=12)
        info.pack(fill='x')

        info_inner = tk.Frame(info, bg=Colors.bg)
        info_inner.pack(fill='x')
        tk.Label(info_inner, text=f"👤  {c['first_name']} {c['last_name']}",
                 font=get_font(9), bg=Colors.bg, fg=Colors.text_secondary).pack(anchor='e')
        tk.Label(info_inner, text=f'مبلغ کل: {format_number(total)} تومان',
                 font=get_bold_font(14), bg=Colors.bg,
                 fg=Colors.accent).pack(anchor='e', pady=(2, 0))

        self._nav_buttons(back_cmd=self._build_step2,
                          next_text='✅  ثبت فروش', next_cmd=self._submit)

    def _submit(self):
        total = sum(item['subtotal'] for item in self.cart)
        dp = int(clean_number(self.dp_var.get() or '0'))
        notes = self.notes_text.get('1.0', 'end-1c').strip()

        for item in self.cart:
            p = item['product']
            if item.get('price_id'):
                from desktop.db import fetchone
                pp = fetchone("SELECT stock FROM store_product_price WHERE id=?", [item['price_id']])
                avail = pp['stock'] if pp else 0
            else:
                pdata = get_product(p['id'])
                avail = pdata['stock'] if pdata else 0
            if avail < item['quantity']:
                messagebox.showwarning(
                    'موجودی ناکافی',
                    f"موجودی {p['name']} کافی نیست\n"
                    f"موجودی فعلی: {avail}"
                )
                return

        customer_id = self.selected_customer['id']
        due_days = int(clean_number(self.due_days_var.get() or '0'))
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
        elif self.payment_type == 'installment':
            if dp > 0:
                create_payment(sale_id, customer_id, dp, 'down_payment', '')
            remaining = total - dp
            if remaining > 0:
                count = int(clean_number(self.inst_count_var.get() or '6'))
                per_term = max(1, remaining // count)
                from desktop.db import execute as db_execute
                db_execute(
                    "INSERT INTO store_installment (sale_id, customer_id, total_count, paid_count, amount_per_term, due_day, status, start_date, amount_paid) VALUES (?,?,?,0,?,?,'active',date('now'),?)",
                    [sale_id, customer_id, count, per_term, due_days, dp]
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

        canvas = tk.Canvas(parent, bg=Colors.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        self.frame = tk.Frame(canvas, bg=Colors.bg, padx=24, pady=20)

        self.frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self._bind_mousewheel(canvas)

        self._build(sale)

    def _bind_mousewheel(self, canvas):
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

    def _build(self, sale):
        sale_id = self._sale_id
        frame = self.frame

        status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                      'partial': 'جزئی', 'cancelled': 'لغو'}
        status_color = {'paid': Colors.success, 'pending': Colors.warning,
                        'partial': Colors.accent, 'cancelled': Colors.danger}
        st_color = status_color.get(sale['status'], Colors.text_muted)

        header = tk.Frame(frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text=f'فروش #{sale["id"]}',
                 font=get_bold_font(18), bg=Colors.bg,
                 fg=Colors.text_primary).pack(side='right')
        tk.Label(header, text=status_map.get(sale['status'], sale['status']),
                 font=get_font(10), bg=Colors.bg,
                 fg=st_color).pack(side='left')

        remaining = sale_remaining(sale_id)
        if remaining > 0:
            _make_button(header, '➕  ثبت پرداخت', Colors.success, Colors.success_hover,
                         lambda: self._add_payment(sale_id)).pack(side='left', padx=(8, 0))
        _make_button(header, '✏️  تغییر وضعیت', Colors.accent, Colors.accent_hover,
                     lambda: self._edit_status(sale_id)).pack(side='left', padx=(8, 0))
        _make_button(header, '🗑️  حذف', Colors.danger, Colors.danger,
                     lambda: self._delete_sale(sale_id)).pack(side='left')

        info_card = tk.Frame(frame, bg=Colors.card, highlightbackground=Colors.border,
                             highlightthickness=1, padx=20, pady=16)
        info_card.pack(fill='x', pady=(0, 16))

        customer = get_customer(sale['customer_id'])
        for i, (label, val) in enumerate([
            ('مشتری', f"{customer['first_name']} {customer['last_name']}" if customer else '—'),
            ('تاریخ', format_datetime(sale['sale_date'])),
            ('نوع', 'نقدی' if sale['payment_type'] == 'cash' else 'قسطی'),
            ('مبلغ کل', format_number(sale['total_amount'])),
            ('باقی‌مانده', format_number(remaining)),
        ]):
            row = tk.Frame(info_card, bg=Colors.card)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted, width=12, anchor='e').pack(side='right')
            tk.Label(row, text=val, font=get_bold_font(9), bg=Colors.card,
                     fg=Colors.text_primary).pack(side='right', padx=(10, 0))

        tk.Label(frame, text='🧾  اقلام', font=get_bold_font(13),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 8))

        payment_type_map = {'cash': 'نقدی', 'installment_payment': 'پرداخت قسط', 'down_payment': 'پیش پرداخت'}

        items = get_sale_items(sale_id)
        if items:
            items_card = tk.Frame(frame, bg=Colors.card,
                                  highlightbackground=Colors.border, highlightthickness=1)
            items_card.pack(fill='both', pady=(0, 16))

            cols = ('subtotal', 'price', 'qty', 'product')
            tree = ttk.Treeview(items_card, columns=cols, show='headings', height=6)
            tree.tag_configure('even', background=Colors.card)
            tree.tag_configure('odd', background=Colors.border_light)
            tree.heading('subtotal', text='جمع', anchor='center')
            tree.heading('price', text='قیمت واحد', anchor='center')
            tree.heading('qty', text='تعداد', anchor='center')
            tree.heading('product', text='محصول', anchor='e')
            tree.column('subtotal', width=120, anchor='center')
            tree.column('price', width=120, anchor='center')
            tree.column('qty', width=80, anchor='center')
            tree.column('product', width=300, anchor='e')
            vsb1 = ttk.Scrollbar(items_card, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=vsb1.set)
            tree.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
            vsb1.grid(row=0, column=1, sticky='ns')
            items_card.grid_rowconfigure(0, weight=1)
            items_card.grid_columnconfigure(0, weight=1)
            for i, item in enumerate(items):
                tree.insert('', 'end', values=(
                    format_number(item['subtotal']),
                    format_number(item['unit_price']),
                    item['quantity'],
                    item.get('product_name') or '—',
                ), tags=('even' if i % 2 == 0 else 'odd',))

        tk.Label(frame, text='💳  پرداخت‌ها', font=get_bold_font(13),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 8))

        payments = get_sale_payments(sale_id)
        if payments:
            pay_card = tk.Frame(frame, bg=Colors.card,
                                highlightbackground=Colors.border, highlightthickness=1)
            pay_card.pack(fill='both')

            cols = ('type', 'amount', 'date', 'id')
            tree2 = ttk.Treeview(pay_card, columns=cols, show='headings', height=5)
            tree2.tag_configure('even', background=Colors.card)
            tree2.tag_configure('odd', background=Colors.border_light)
            tree2.heading('type', text='نوع', anchor='center')
            tree2.heading('amount', text='مبلغ', anchor='center')
            tree2.heading('date', text='تاریخ', anchor='center')
            tree2.heading('id', text='#', anchor='center')
            tree2.column('type', width=120, anchor='center')
            tree2.column('amount', width=140, anchor='center')
            tree2.column('date', width=140, anchor='center')
            tree2.column('id', width=50, anchor='center')
            vsb2 = ttk.Scrollbar(pay_card, orient='vertical', command=tree2.yview)
            tree2.configure(yscrollcommand=vsb2.set)
            tree2.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
            vsb2.grid(row=0, column=1, sticky='ns')
            pay_card.grid_rowconfigure(0, weight=1)
            pay_card.grid_columnconfigure(0, weight=1)
            def _edit_payment():
                sel = tree2.selection()
                if not sel:
                    return
                values = tree2.item(sel[0], 'values')
                pid = int(values[3])
                cur_amount = int(clean_number(values[1]))
                new_amt = persian_askinteger('ویرایش مبلغ پرداخت',
                                             f'مبلغ جدید (مقدار فعلی: {format_number(cur_amount)}):',
                                             minvalue=1, maxvalue=sale['total_amount'],
                                             parent=self.frame.winfo_toplevel())
                if new_amt is None:
                    return
                update_payment(pid, new_amt)
                update_sale_status(sale_id)
                for w in self.frame.winfo_children():
                    w.destroy()
                self._build(get_sale(sale_id))

            def _delete_payment():
                sel = tree2.selection()
                if not sel:
                    return
                pid = tree2.item(sel[0], 'values')[3]
                if messagebox.askyesno('تأیید حذف', 'آیا از حذف این پرداخت اطمینان دارید؟'):
                    delete_payment(pid)
                    update_sale_status(sale_id)
                    for w in self.frame.winfo_children():
                        w.destroy()
                    self._build(get_sale(sale_id))

            menu = tk.Menu(self.frame, tearoff=0, bg=Colors.card, fg=Colors.text_primary,
                           font=get_font(9))
            menu.add_command(label='✏️  ویرایش مبلغ', command=_edit_payment)
            menu.add_separator()
            menu.add_command(label='🗑️  حذف پرداخت', command=_delete_payment)

            def _on_right_click(e):
                item = tree2.identify_row(e.y)
                if item:
                    tree2.selection_set(item)
                    menu.post(e.x_root, e.y_root)

            tree2.bind('<Button-3>', _on_right_click)

            for i, p in enumerate(payments):
                tree2.insert('', 'end', values=(
                    payment_type_map.get(p['payment_type'], p['payment_type']),
                    format_number(p['amount']),
                    format_date(p['payment_date']),
                    p['id'],
                ), tags=('even' if i % 2 == 0 else 'odd',))

    def _edit_status(self, sale_id):
        sale = get_sale(sale_id)
        if not sale:
            return
        status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                      'partial': 'جزئی', 'cancelled': 'لغو'}
        rev = {v: k for k, v in status_map.items()}
        win = make_dialog(self.frame, 'تغییر وضعیت', 350, 200)
        win.configure(bg=Colors.card)
        win.resizable(False, False)

        header = tk.Frame(win, bg=Colors.accent, height=42)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='تغییر وضعیت فروش', font=get_bold_font(11),
                 bg=Colors.accent, fg='#ffffff').pack(expand=True)

        form = tk.Frame(win, bg=Colors.card, padx=24, pady=20)
        form.pack(fill='both', expand=True)

        tk.Label(form, text='وضعیت جدید:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary).pack(anchor='e')
        var = tk.StringVar(value=status_map.get(sale['status'], ''))
        cb = ttk.Combobox(form, textvariable=var,
                          values=['تسویه', 'در انتظار', 'جزئی', 'لغو'],
                          state='readonly', font=get_font(10))
        cb.pack(fill='x', pady=(4, 16))

        def save():
            new_status = rev.get(var.get())
            if new_status and new_status != sale['status']:
                from desktop.db import execute as db_exe
                db_exe("UPDATE store_sale SET status=? WHERE id=?", [new_status, sale_id])
                if new_status == 'paid':
                    inst = fetchone("SELECT id, total_count FROM store_installment WHERE sale_id=? AND status='active'", [sale_id])
                    if inst:
                        db_exe("UPDATE store_installment SET paid_count=?, status='paid' WHERE id=?", [inst['total_count'], inst['id']])
            win.destroy()
            for w in self.frame.winfo_children():
                w.destroy()
            self._build(get_sale(sale_id))

        _make_button(form, '💾  ذخیره', Colors.accent, Colors.accent_hover,
                     save).pack(side='left', padx=(0, 8))
        _make_button(form, '✕  انصراف', Colors.text_muted, Colors.border,
                     win.destroy).pack(side='left')

    def _delete_sale(self, sale_id):
        sale = get_sale(sale_id)
        if not sale:
            return
        if messagebox.askyesno('تأیید حذف', 'آیا از حذف این فروش اطمینان دارید؟'):
            from desktop.db import execute as db_exe, fetchall
            items = fetchall("SELECT * FROM store_saleitem WHERE sale_id=?", [sale_id])
            for item in items:
                db_exe("UPDATE store_product SET stock=stock+? WHERE id=?", [item['quantity'], item['product_id']])
            db_exe("DELETE FROM store_saleitem WHERE sale_id=?", [sale_id])
            db_exe("DELETE FROM store_payment WHERE sale_id=?", [sale_id])
            db_exe("DELETE FROM store_installment WHERE sale_id=?", [sale_id])
            db_exe("DELETE FROM store_sale WHERE id=?", [sale_id])
            self._parent.destroy()

    def _add_payment(self, sale_id):
        sale = get_sale(sale_id)
        remaining = sale_remaining(sale_id)
        if remaining <= 0:
            messagebox.showinfo('', 'این فاکتور تسویه شده است')
            return
        installments = get_installments(sale_id, sale['customer_id'])
        if installments:
            inst = installments[0]
            remaining_count = inst['total_count'] - inst['paid_count']
            default = max(1, remaining // remaining_count) if remaining_count > 0 else remaining
        else:
            default = remaining
        amt = persian_askinteger('ثبت پرداخت',
                                 f'مبلغ پرداختی (باقی‌مانده: {format_number(remaining)}):',
                                 minvalue=1, maxvalue=remaining,
                                 parent=self.frame.winfo_toplevel())
        if amt is None:
            return
        if installments:
            inst = installments[0]
            payment_type = 'installment_payment'
            new_paid = inst['paid_count'] + 1
            new_status = 'paid' if new_paid >= inst['total_count'] else 'active'
            from desktop.db import execute as db_exe
            db_exe(
                "UPDATE store_installment SET paid_count=?, amount_paid=COALESCE(amount_paid,0)+?, status=? WHERE id=?",
                [new_paid, amt, new_status, inst['id']]
            )
        else:
            payment_type = 'cash'
        create_payment(sale_id, sale['customer_id'], amt, payment_type, '')
        update_sale_status(sale_id)
        messagebox.showinfo('', 'پرداخت با موفقیت ثبت شد')
        for w in self.frame.winfo_children():
            w.destroy()
        sale = get_sale(sale_id)
        self._build(sale)
