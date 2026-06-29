import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_products, get_product, create_product, update_product, delete_product, get_product_types, get_product_type, create_product_type, update_product_type, delete_product_type, get_product_prices, create_product_price, update_product_price, delete_product_price, create_supply_entry, get_supply_log
from desktop.theme import Colors, get_font, get_bold_font
from desktop.utils import persian_digits, format_number, format_date, add_number_comma_formatting, clean_number, make_dialog


def _make_button(parent, text, bg, active_bg, command):
    return tk.Button(parent, text=text, font=get_font(10),
                     bg=bg, fg='#ffffff', bd=0, cursor='hand2',
                     padx=18, pady=8, activebackground=active_bg,
                     command=command)


def _make_form_dialog(parent, title, fields, obj=None, on_save=None, combobox_data=None, on_delete=None):
    win = make_dialog(parent, title, 520, 480)
    win.configure(bg=Colors.card)
    win.resizable(False, False)

    header = tk.Frame(win, bg=Colors.accent, height=48)
    header.pack(fill='x')
    header.pack_propagate(False)
    tk.Label(header, text=title, font=get_bold_font(12),
             bg=Colors.accent, fg='#ffffff').pack(expand=True)

    form = tk.Frame(win, bg=Colors.card, padx=28, pady=22)
    form.pack(fill='both', expand=True)

    entries = {}
    for label, key, widget_type in fields:
        row = tk.Frame(form, bg=Colors.card)
        row.pack(fill='x', pady=5)
        tk.Label(row, text=label, font=get_font(9), bg=Colors.card,
                 fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')

        var = tk.StringVar()

        if widget_type == 'combobox':
            items = combobox_data.get(key, []) if combobox_data else []
            w = ttk.Combobox(row, textvariable=var, values=items,
                             state='readonly', font=get_font(10), width=22)
            if obj and key in obj:
                val = obj[key]
                for item in items:
                    if item.startswith(str(val)):
                        var.set(item)
                        break
        else:
            if obj and key in obj:
                val = obj[key]
                var.set(str(val) if val is not None else '')

            if widget_type == 'textarea':
                w = tk.Text(row, font=get_font(10), bd=1, relief='solid',
                            height=4, bg=Colors.card,
                            highlightbackground=Colors.border,
                            highlightcolor=Colors.accent,
                            highlightthickness=1)
                if obj and key in obj:
                    w.insert('1.0', obj[key] or '')
            else:
                w = tk.Entry(row, textvariable=var, font=get_font(10),
                             bd=1, relief='solid', bg=Colors.card,
                             highlightbackground=Colors.border,
                             highlightcolor=Colors.accent,
                             highlightthickness=1)

        w.pack(side='right', fill='x', expand=True, padx=(10, 0), ipady=4 if widget_type != 'textarea' else 0)
        entries[key] = (var, w)
        if widget_type == 'number':
            add_number_comma_formatting(var, w)

    def save():
        if on_save:
            data = {}
            for key, (var, w) in entries.items():
                val = clean_number(var.get()) if hasattr(var, 'get') else w.get('1.0', 'end-1c').strip()
                data[key] = val
            on_save(data)
        win.destroy()

    btn_frame = tk.Frame(form, bg=Colors.card)
    btn_frame.pack(fill='x', pady=(24, 0))
    _make_button(btn_frame, '💾  ذخیره', Colors.accent, Colors.accent_hover,
                 save).pack(side='left', padx=(0, 8))
    _make_button(btn_frame, '✕  انصراف', Colors.text_muted, Colors.border,
                 win.destroy).pack(side='left')
    if on_delete:
        _make_button(btn_frame, '🗑️  حذف', Colors.danger, Colors.danger,
                     on_delete).pack(side='right')

    return win


class ProductTypesView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='انواع محصول', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')
        _make_button(header, '➕  نوع جدید', Colors.accent, Colors.accent_hover,
                     self._add).pack(side='left')

        table_card = tk.Frame(self.frame, bg=Colors.card,
                              highlightbackground=Colors.border, highlightthickness=1)
        table_card.pack(fill='both', expand=True)

        columns = ('created_at', 'description', 'name', 'id')
        self.tree = ttk.Treeview(table_card, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('created_at', text='تاریخ ثبت', anchor='center')
        self.tree.heading('description', text='توضیحات', anchor='e')
        self.tree.heading('name', text='نام', anchor='e')
        self.tree.heading('id', text='#', anchor='center')
        self.tree.column('created_at', width=140, anchor='center')
        self.tree.column('description', width=350, anchor='e')
        self.tree.column('name', width=220, anchor='e')
        self.tree.column('id', width=50, anchor='center')

        scrollbar = ttk.Scrollbar(table_card, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for t in get_product_types():
            self.tree.insert('', 'end', values=(
                format_date(t['created_at']), t.get('description') or '—',
                t['name'], persian_digits(t['id'])))

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        tid = int(clean_number(values[-1]))
        menu = tk.Menu(self.frame, tearoff=0, font=get_font(9),
                       bg=Colors.card, fg=Colors.text_primary,
                       activebackground=Colors.accent, activeforeground='#ffffff')
        menu.add_command(label='✏️  ویرایش', command=lambda: self._edit(tid))
        menu.add_command(label='🗑️  حذف', command=lambda: self._delete(tid))
        menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            self._edit(int(clean_number(values[-1])))

    def _add(self):
        fields = [('نام', 'name', 'text'), ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'نوع جدید', fields, on_save=self._save_new)

    def _save_new(self, data):
        create_product_type(data)
        self._load()

    def _edit(self, tid):
        t = get_product_type(tid)
        if not t:
            return
        fields = [('نام', 'name', 'text'), ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'ویرایش نوع', fields, obj=t,
                          on_save=lambda d: self._save_edit(tid, d),
                          on_delete=lambda: self._delete(tid))

    def _save_edit(self, tid, data):
        update_product_type(tid, data)
        self._load()

    def _delete(self, tid):
        if messagebox.askyesno('تأیید', 'حذف شود؟'):
            delete_product_type(tid)
            self._load()


class ProductsView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='محصولات', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')
        _make_button(header, '➕  محصول جدید', Colors.accent, Colors.accent_hover,
                     self._add).pack(side='left')
        _make_button(header, '💰  قیمت‌ها', Colors.success, Colors.success_hover,
                     self._manage_prices).pack(side='left', padx=(8, 0))

        table_card = tk.Frame(self.frame, bg=Colors.card,
                              highlightbackground=Colors.border, highlightthickness=1)
        table_card.pack(fill='both', expand=True)

        columns = ('stock', 'cost', 'price', 'unit', 'type', 'name', 'id')
        self.tree = ttk.Treeview(table_card, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('stock', text='موجودی', anchor='center')
        self.tree.heading('cost', text='قیمت خرید', anchor='center')
        self.tree.heading('price', text='قیمت فروش', anchor='center')
        self.tree.heading('unit', text='واحد', anchor='center')
        self.tree.heading('type', text='نوع', anchor='e')
        self.tree.heading('name', text='نام محصول', anchor='e')
        self.tree.heading('id', text='#', anchor='center')
        self.tree.column('stock', width=80, anchor='center')
        self.tree.column('cost', width=120, anchor='center')
        self.tree.column('price', width=120, anchor='center')
        self.tree.column('unit', width=70, anchor='center')
        self.tree.column('type', width=120, anchor='e')
        self.tree.column('name', width=200, anchor='e')
        self.tree.column('id', width=50, anchor='center')

        scrollbar = ttk.Scrollbar(table_card, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in get_all_products():
            self.tree.insert('', 'end', values=(
                persian_digits(p['stock']),
                format_number(p['purchase_price']),
                format_number(p['selling_price']),
                p.get('unit') or '',
                p.get('product_type_name') or '—',
                p['name'],
                persian_digits(p['id']),
            ))

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        pid = int(clean_number(values[-1]))
        menu = tk.Menu(self.frame, tearoff=0, font=get_font(9),
                       bg=Colors.card, fg=Colors.text_primary,
                       activebackground=Colors.accent, activeforeground='#ffffff')
        menu.add_command(label='✏️  ویرایش', command=lambda: self._edit(pid))
        menu.add_command(label='🗑️  حذف', command=lambda: self._delete(pid))
        menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            self._edit(int(clean_number(values[-1])))

    def _add(self):
        types = get_product_types()
        type_items = [f'{t["id"]}: {t["name"]}' for t in types]
        unit_items = ['', 'کیسه',  'عدد', 'کیلوگرم', 'گرم', 'لیتر', 'متر', 'بسته', 'کارتن', 'جعبه', 'بطری']
        fields = [('نام محصول', 'name', 'text'),
                  ('نوع محصول', 'product_type_id', 'combobox'),
                  ('واحد', 'unit', 'combobox'),
                  ('قیمت فروش', 'selling_price', 'number'),
                  ('قیمت خرید', 'purchase_price', 'number'),
                  ('موجودی', 'stock', 'number'),
                  ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'محصول جدید', fields,
                          on_save=self._save_new,
                          combobox_data={'product_type_id': type_items,
                                         'unit': unit_items})

    def _save_new(self, data):
        raw = data.get('product_type_id', '')
        if raw and ': ' in raw:
            data['product_type_id'] = int(raw.split(': ')[0])
        else:
            data['product_type_id'] = None
        create_product(data)
        self._load()

    def _edit(self, pid):
        p = get_product(pid)
        if not p:
            return
        types = get_product_types()
        type_items = [f'{t["id"]}: {t["name"]}' for t in types]
        unit_items = ['', 'کیسه', 'عدد', 'کیلوگرم', 'گرم', 'لیتر', 'متر', 'بسته', 'کارتن', 'جعبه', 'بطری']
        fields = [('نام محصول', 'name', 'text'),
                  ('نوع محصول', 'product_type_id', 'combobox'),
                  ('واحد', 'unit', 'combobox'),
                  ('قیمت فروش', 'selling_price', 'number'),
                  ('قیمت خرید', 'purchase_price', 'number'),
                  ('موجودی', 'stock', 'number'),
                  ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'ویرایش محصول', fields, obj=p,
                          on_save=lambda d: self._save_edit(pid, d),
                          combobox_data={'product_type_id': type_items,
                                         'unit': unit_items},
                          on_delete=lambda: self._delete(pid))

    def _save_edit(self, pid, data):
        raw = data.get('product_type_id', '')
        if raw and ': ' in raw:
            data['product_type_id'] = int(raw.split(': ')[0])
        else:
            data['product_type_id'] = None
        update_product(pid, data)
        self._load()

    def _delete(self, pid):
        if messagebox.askyesno('تأیید', 'حذف شود؟'):
            delete_product(pid)
            self._load()

    def _manage_prices(self):
        products = get_all_products()
        if not products:
            messagebox.showinfo('', 'محصولی وجود ندارد')
            return
        win = make_dialog(self.frame, 'مدیریت قیمت‌های محصول', 700, 600)
        win.configure(bg=Colors.bg)

        main = tk.Frame(win, bg=Colors.bg, padx=20, pady=16)
        main.pack(fill='both', expand=True)

        tk.Label(main, text='انتخاب محصول:', font=get_font(9),
                 bg=Colors.bg, fg=Colors.text_secondary).pack(anchor='e')
        prod_var = tk.StringVar()
        prod_items = [f'{p["id"]}: {p["name"]}' for p in products]
        prod_cb = ttk.Combobox(main, textvariable=prod_var,
                               values=prod_items, state='readonly',
                               font=get_font(10), width=40)
        prod_cb.pack(fill='x', pady=(4, 16))

        list_card = tk.Frame(main, bg=Colors.card,
                             highlightbackground=Colors.border, highlightthickness=1)
        list_card.pack(fill='both', expand=True)

        def load_prices(*_):
            for w in list_card.winfo_children():
                w.destroy()
            raw = prod_var.get()
            if not raw or ': ' not in raw:
                return
            pid = int(raw.split(': ')[0])
            prices = get_product_prices(pid)

            tree = None
            if not prices:
                tk.Label(list_card, text='هیچ قیمت اضافی تعریف نشده',
                         font=get_font(9), bg=Colors.card,
                         fg=Colors.text_muted).pack(pady=20)
            else:
                cols = ('stock', 'amount', 'label', 'id')
                tree = ttk.Treeview(list_card, columns=cols,
                                    show='headings', height=10)
                tree.heading('stock', text='موجودی', anchor='center')
                tree.heading('amount', text='قیمت', anchor='center')
                tree.heading('label', text='عنوان', anchor='e')
                tree.heading('id', text='#', anchor='center')
                tree.column('stock', width=80, anchor='center')
                tree.column('amount', width=150, anchor='center')
                tree.column('label', width=200, anchor='e')
                tree.column('id', width=40, anchor='center')

                scrollbar = ttk.Scrollbar(list_card, orient='vertical',
                                          command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                tree.pack(side='right', fill='both', expand=True)
                scrollbar.pack(side='left', fill='y')

                for pr in prices:
                    tree.insert('', 'end', values=(
                        persian_digits(pr['stock']), format_number(pr['amount']),
                        pr['price_label'], persian_digits(pr['id'])))

                tree.bind('<Button-3>', lambda e: _on_price_right_click(e, tree, pid))

            btn_frame = tk.Frame(list_card, bg=Colors.card)
            btn_frame.pack(fill='x', pady=(6, 4))
            _make_button(btn_frame, '➕  قیمت جدید', Colors.accent, Colors.accent_hover,
                         lambda: _add_price(pid)).pack(side='right', padx=(4, 0))
            _make_button(btn_frame, '📦  تامین', Colors.success, Colors.success_hover,
                         lambda: _supply(pid, tree)).pack(side='right', padx=4)
            _make_button(btn_frame, '📋  تاریخچه', Colors.warning, Colors.warning,
                         lambda: _show_history(pid, tree)).pack(side='right', padx=4)

        def _price_form_dialog(title, fields_data, on_save_cb):
            fwin = make_dialog(win, title, 400, 320 + len(fields_data) * 40)
            fwin.configure(bg=Colors.card)
            fwin.resizable(False, False)

            header = tk.Frame(fwin, bg=Colors.accent, height=42)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text=title, font=get_bold_font(11),
                     bg=Colors.accent, fg='#ffffff').pack(expand=True)

            frm = tk.Frame(fwin, bg=Colors.card, padx=24, pady=20)
            frm.pack(fill='both', expand=True)

            vars_dict = {}
            for label, key, default in fields_data:
                tk.Label(frm, text=label, font=get_font(9), bg=Colors.card,
                         fg=Colors.text_secondary).pack(anchor='e')
                var = tk.StringVar(value=default)
                entry = tk.Entry(frm, textvariable=var, font=get_font(10),
                                 bd=1, relief='solid', bg=Colors.card,
                                 highlightbackground=Colors.border,
                                 highlightcolor=Colors.accent,
                                 highlightthickness=1)
                entry.pack(fill='x', pady=(2, 8), ipady=4)
                vars_dict[key] = var
                if key in ('buy_price', 'sell_price', 'stock', 'amount'):
                    add_number_comma_formatting(var, entry)

            def do_save():
                data = {k: clean_number(v.get()) for k, v in vars_dict.items()}
                on_save_cb(data)
                fwin.destroy()

            btn_frame = tk.Frame(frm, bg=Colors.card)
            btn_frame.pack(fill='x', pady=(8, 0))
            _make_button(btn_frame, '💾  ذخیره', Colors.accent, Colors.accent_hover,
                         do_save).pack(side='left', padx=(0, 8))
            _make_button(btn_frame, '✕  انصراف', Colors.text_muted, Colors.border,
                         fwin.destroy).pack(side='left')

            return fwin

        def _add_price(pid):
            try:
                from jdatetime import date as jdate
                default_date = str(jdate.today())
            except Exception:
                from datetime import date as gdate
                default_date = str(gdate.today())

            fields_data = [
                ('عنوان:', 'label', ''),
                ('قیمت خرید:', 'buy_price', '0'),
                ('قیمت فروش:', 'sell_price', ''),
                ('تعداد:', 'stock', '0'),
                ('تاریخ:', 'date', default_date),
            ]

            def save(data):
                if not data.get('label') or not data.get('sell_price'):
                    return
                qty = int(data.get('stock') or 0)
                sell = int(data.get('sell_price'))
                buy = int(data.get('buy_price') or 0)
                price_id = create_product_price(pid, data['label'], sell, qty)
                if qty > 0:
                    try:
                        from jdatetime import date as jdate
                        from datetime import datetime
                        jd = jdate.fromisoformat(str(data['date']))
                        gd = jd.togregorian()
                        supplied_at = datetime(gd.year, gd.month, gd.day).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        supplied_at = None
                    if supplied_at:
                        from desktop.db import execute as db_execute
                        db_execute(
                            "INSERT INTO store_supply_log (price_id, quantity, buy_price, sale_price, supplied_at) VALUES (?,?,?,?,?)",
                            [price_id, qty, buy, sell, supplied_at]
                        )
                    else:
                        create_supply_entry(price_id, qty, buy, sell)
                load_prices()

            _price_form_dialog('قیمت جدید', fields_data, save)

        def _edit_price(pid, price_id, old_label, old_amt, old_stock):
            fields_data = [
                ('عنوان:', 'label', old_label),
                ('قیمت:', 'amount', str(old_amt)),
                ('موجودی:', 'stock', str(old_stock)),
            ]

            def save(data):
                if not data.get('label') or not data.get('amount'):
                    return
                update_product_price(price_id, data['label'], int(data['amount']),
                                     int(data.get('stock') or 0))
                load_prices()

            _price_form_dialog('ویرایش قیمت', fields_data, save)

        def _selected_price(tree):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('', 'ابتدا یک قیمت را انتخاب کنید')
                return None
            vals = tree.item(sel[0], 'values')
            if not vals:
                return None
            return int(clean_number(vals[-1])), vals[-2], int(clean_number(vals[-3])), int(clean_number(vals[-4]))

        def _supply(pid, tree):
            if tree is None:
                messagebox.showwarning('', 'ابتدا یک قیمت اضافه کنید')
                return
            sp = _selected_price(tree)
            if not sp:
                return
            price_id, label, amt, stock = sp
            fwin = make_dialog(win, 'تامین کالا', 380, 300)
            fwin.configure(bg=Colors.card)
            fwin.resizable(False, False)

            header = tk.Frame(fwin, bg=Colors.success, height=42)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text=f'تامین {label}', font=get_bold_font(11),
                     bg=Colors.success, fg='#ffffff').pack(expand=True)

            frm = tk.Frame(fwin, bg=Colors.card, padx=24, pady=20)
            frm.pack(fill='both', expand=True)

            tk.Label(frm, text='تعداد:', font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary).pack(anchor='e')
            qty_var = tk.StringVar(value='1')
            qty_entry = tk.Entry(frm, textvariable=qty_var, font=get_font(10),
                     bd=1, relief='solid', bg=Colors.card,
                     highlightbackground=Colors.border,
                     highlightcolor=Colors.accent,
                     highlightthickness=1)
            qty_entry.pack(fill='x', pady=(2, 8), ipady=4)
            add_number_comma_formatting(qty_var, qty_entry)

            tk.Label(frm, text='قیمت خرید (تومان):', font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary).pack(anchor='e')
            buy_var = tk.StringVar(value='0')
            buy_entry = tk.Entry(frm, textvariable=buy_var, font=get_font(10),
                     bd=1, relief='solid', bg=Colors.card,
                     highlightbackground=Colors.border,
                     highlightcolor=Colors.accent,
                     highlightthickness=1)
            buy_entry.pack(fill='x', pady=(2, 8), ipady=4)
            add_number_comma_formatting(buy_var, buy_entry)

            tk.Label(frm, text='قیمت فروش (تومان):', font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary).pack(anchor='e')
            sell_var = tk.StringVar(value=str(amt))
            sell_entry = tk.Entry(frm, textvariable=sell_var, font=get_font(10),
                     bd=1, relief='solid', bg=Colors.card,
                     highlightbackground=Colors.border,
                     highlightcolor=Colors.accent,
                     highlightthickness=1)
            sell_entry.pack(fill='x', pady=(2, 12), ipady=4)
            add_number_comma_formatting(sell_var, sell_entry)

            def save():
                qty = int(clean_number(qty_var.get() or '0'))
                buy = int(clean_number(buy_var.get() or '0'))
                sell = int(clean_number(sell_var.get() or '0'))
                if qty < 1 or sell < 1:
                    return
                update_product_price(price_id, label, sell, stock + qty)
                create_supply_entry(price_id, qty, buy, sell)
                fwin.destroy()
                load_prices()

            _make_button(frm, '💾  ذخیره', Colors.success, Colors.success_hover,
                         save).pack(pady=(4, 0))

        def _show_history(pid, tree):
            if tree is None:
                messagebox.showwarning('', 'ابتدا یک قیمت اضافه کنید')
                return
            sp = _selected_price(tree)
            if not sp:
                return
            price_id, label, amt, stock = sp
            log = get_supply_log(price_id)
            hwin = make_dialog(win, f'تاریخچه تامین - {label}', 750, 420)
            hwin.configure(bg=Colors.bg)

            main = tk.Frame(hwin, bg=Colors.bg, padx=20, pady=16)
            main.pack(fill='both', expand=True)

            tk.Label(main, text=f'📋  تاریخچه تامین - {label}',
                     font=get_bold_font(13), bg=Colors.bg,
                     fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))

            if not log:
                tk.Label(main, text='هیچ تامینی ثبت نشده',
                         font=get_font(10), bg=Colors.bg,
                         fg=Colors.text_muted).pack(pady=30)
                return

            table_card = tk.Frame(main, bg=Colors.card,
                                  highlightbackground=Colors.border, highlightthickness=1)
            table_card.pack(fill='both', expand=True)

            cols = ('sell', 'buy', 'qty', 'date', 'id')
            tree2 = ttk.Treeview(table_card, columns=cols, show='headings', height=16)
            tree2.heading('sell', text='قیمت فروش', anchor='center')
            tree2.heading('buy', text='قیمت خرید', anchor='center')
            tree2.heading('qty', text='تعداد', anchor='center')
            tree2.heading('date', text='تاریخ', anchor='center')
            tree2.heading('id', text='#', anchor='center')
            tree2.column('sell', width=160, anchor='center')
            tree2.column('buy', width=160, anchor='center')
            tree2.column('qty', width=80, anchor='center')
            tree2.column('date', width=180, anchor='center')
            tree2.column('id', width=40, anchor='center')

            scrollbar = ttk.Scrollbar(table_card, orient='vertical',
                                      command=tree2.yview)
            tree2.configure(yscrollcommand=scrollbar.set)
            tree2.pack(side='right', fill='both', expand=True)
            scrollbar.pack(side='left', fill='y')

            for row in log:
                try:
                    from jdatetime import datetime as jdt
                    from datetime import datetime
                    d = jdt.fromgregorian(datetime=datetime.strptime(row['supplied_at'], '%Y-%m-%d %H:%M:%S'))
                    ds = d.strftime('%Y/%m/%d %H:%M')
                except Exception:
                    ds = row['supplied_at']
                tree2.insert('', 'end', values=(
                    format_number(row['sale_price']),
                    format_number(row['buy_price']),
                    persian_digits(row['quantity']), ds, persian_digits(row['id'])))

        def _on_price_right_click(event, tree, pid):
            item = tree.identify_row(event.y)
            if not item:
                return
            vals = tree.item(item, 'values')
            if not vals:
                return
            price_id = int(clean_number(vals[-1]))
            menu = tk.Menu(win, tearoff=0, font=get_font(9),
                           bg=Colors.card, fg=Colors.text_primary,
                           activebackground=Colors.accent, activeforeground='#ffffff')
            menu.add_command(label='✏️  ویرایش',
                             command=lambda: _edit_price(pid, price_id, vals[-2], int(clean_number(vals[-3])), int(clean_number(vals[-4]))))
            menu.add_command(label='🗑️  حذف',
                             command=lambda: self._delete_price(price_id, tree))
            menu.post(event.x_root, event.y_root)

        def _delete_price(price_id, tree):
            if messagebox.askyesno('تأیید', 'حذف شود؟'):
                delete_product_price(price_id)
                load_prices()
        self._delete_price = _delete_price

        prod_var.trace('w', load_prices)
