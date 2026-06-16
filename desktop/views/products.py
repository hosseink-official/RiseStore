import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_products, get_product, create_product, update_product, delete_product, get_product_types, get_product_type, create_product_type, update_product_type, delete_product_type, get_product_prices, create_product_price, update_product_price, delete_product_price, create_supply_entry, get_supply_log
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date


def _make_form_dialog(parent, title, fields, obj=None, on_save=None, combobox_data=None):
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry('500x450')
    win.configure(bg='#ffffff')
    win.resizable(False, False)

    form = tk.Frame(win, bg='#ffffff', padx=24, pady=20)
    form.pack(fill='both', expand=True)

    entries = {}
    for label, key, widget_type in fields:
        row = tk.Frame(form, bg='#ffffff')
        row.pack(fill='x', pady=4)
        tk.Label(row, text=label, font=get_font(9), bg='#ffffff',
                 fg='#475569', width=14, anchor='e').pack(side='right')

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
                var.set('')
        else:
            if obj and key in obj:
                val = obj[key]
                var.set(str(val) if val is not None else '')

            if widget_type == 'text':
                w = tk.Entry(row, textvariable=var, font=get_font(10),
                             bd=1, relief='solid')
            elif widget_type == 'number':
                w = tk.Entry(row, textvariable=var, font=get_font(10),
                             bd=1, relief='solid')
            elif widget_type == 'textarea':
                w = tk.Text(row, font=get_font(10), bd=1, relief='solid',
                            height=4)
                if obj and key in obj:
                    w.insert('1.0', obj[key] or '')
            else:
                w = tk.Entry(row, textvariable=var, font=get_font(10),
                             bd=1, relief='solid')

        w.pack(side='right', fill='x', expand=True, padx=(8, 0))
        entries[key] = (var, w)

    def save():
        if on_save:
            data = {}
            for key, (var, w) in entries.items():
                val = var.get().strip() if hasattr(var, 'get') else w.get('1.0', 'end-1c').strip()
                data[key] = val
            on_save(data)
        win.destroy()

    btn_frame = tk.Frame(form, bg='#ffffff')
    btn_frame.pack(fill='x', pady=(20, 0))
    tk.Button(btn_frame, text='ذخیره', font=get_font(10),
              bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
              padx=20, pady=6, command=save).pack(side='left')
    tk.Button(btn_frame, text='انصراف', font=get_font(10),
              bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
              padx=20, pady=6, command=win.destroy).pack(side='left', padx=(8, 0))

    return win


class ProductTypesView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        header = tk.Frame(self.frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text='انواع محصول', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(side='right')
        tk.Button(header, text='+ نوع جدید', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=16, pady=6, command=self._add).pack(side='left')

        columns = ('id', 'name', 'description', 'created_at', 'actions')
        self.tree = ttk.Treeview(self.frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('id', text='#', anchor='center')
        self.tree.heading('name', text='نام', anchor='e')
        self.tree.heading('description', text='توضیحات', anchor='e')
        self.tree.heading('created_at', text='تاریخ ثبت', anchor='center')
        self.tree.heading('actions', text='', anchor='center')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('name', width=200, anchor='e')
        self.tree.column('description', width=300, anchor='e')
        self.tree.column('created_at', width=120, anchor='center')
        self.tree.column('actions', width=80, anchor='center')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<ButtonRelease-1>', self._on_click)

        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for t in get_product_types():
            self.tree.insert('', 'end', values=(
                t['id'], t['name'], t.get('description') or '—',
                format_date(t['created_at']), '✏️  🗑️'))

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item or col != '#5':
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        tid = int(values[0])
        x_rel = event.x - self.tree.bbox(item, '#5')[0]
        if x_rel < 40:
            self._edit(tid)
        else:
            self._delete(tid)

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
                          on_save=lambda d: self._save_edit(tid, d))

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
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        header = tk.Frame(self.frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text='محصولات', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(side='right')
        tk.Button(header, text='+ محصول جدید', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=16, pady=6, command=self._add).pack(side='left')
        tk.Button(header, text='💲 قیمت‌ها', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=12, pady=6,
                  command=self._manage_prices).pack(side='left', padx=(8, 0))
        tk.Button(header, text='🔄', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=12, pady=6,
                  command=self._load).pack(side='left', padx=(8, 0))

        columns = ('id', 'name', 'type', 'unit', 'price', 'cost', 'stock', 'actions')
        self.tree = ttk.Treeview(self.frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('id', text='#', anchor='center')
        self.tree.heading('name', text='نام محصول', anchor='e')
        self.tree.heading('type', text='نوع', anchor='e')
        self.tree.heading('unit', text='واحد', anchor='center')
        self.tree.heading('price', text='قیمت فروش', anchor='center')
        self.tree.heading('cost', text='قیمت خرید', anchor='center')
        self.tree.heading('stock', text='موجودی', anchor='center')
        self.tree.heading('actions', text='', anchor='center')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('name', width=180, anchor='e')
        self.tree.column('type', width=110, anchor='e')
        self.tree.column('unit', width=70, anchor='center')
        self.tree.column('price', width=110, anchor='center')
        self.tree.column('cost', width=110, anchor='center')
        self.tree.column('stock', width=70, anchor='center')
        self.tree.column('actions', width=80, anchor='center')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<ButtonRelease-1>', self._on_click)

        self._load()

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in get_all_products():
            self.tree.insert('', 'end', values=(
                p['id'], p['name'],
                p.get('product_type_name') or '—',
                p.get('unit') or '',
                format_number(p['selling_price']),
                format_number(p['purchase_price']),
                p['stock'],
                '✏️  🗑️'))

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item or col != '#8':
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        pid = int(values[0])
        x_rel = event.x - self.tree.bbox(item, '#8')[0]
        if x_rel < 40:
            self._edit(pid)
        else:
            self._delete(pid)

    def _add(self):
        types = get_product_types()
        type_items = [f'{t["id"]}: {t["name"]}' for t in types]
        unit_items = ['', 'عدد', 'کیلوگرم', 'گرم', 'لیتر', 'متر', 'بسته', 'کارتن', 'جعبه', 'بطری']
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
        unit_items = ['', 'عدد', 'کیلوگرم', 'گرم', 'لیتر', 'متر', 'بسته', 'کارتن', 'جعبه', 'بطری']
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
                                         'unit': unit_items})

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
        win = tk.Toplevel(self.frame)
        win.title('مدیریت قیمت‌های محصول')
        win.geometry('650x550')
        win.configure(bg='#f0f2f5')

        main = tk.Frame(win, bg='#f0f2f5', padx=16, pady=12)
        main.pack(fill='both', expand=True)

        tk.Label(main, text='انتخاب محصول:', font=get_font(9),
                 bg='#f0f2f5', fg='#475569').pack(anchor='e')
        prod_var = tk.StringVar()
        prod_items = [f'{p["id"]}: {p["name"]}' for p in products]
        prod_cb = ttk.Combobox(main, textvariable=prod_var,
                               values=prod_items, state='readonly',
                               font=get_font(10), width=40)
        prod_cb.pack(fill='x', pady=(4, 12))

        list_frame = tk.Frame(main, bg='#ffffff',
                              highlightbackground='#e2e8f0', highlightthickness=1)
        list_frame.pack(fill='both', expand=True)

        def load_prices(*_):
            for w in list_frame.winfo_children():
                w.destroy()
            raw = prod_var.get()
            if not raw or ': ' not in raw:
                return
            pid = int(raw.split(': ')[0])
            prices = get_product_prices(pid)
            if not prices:
                tk.Label(list_frame, text='هیچ قیمت اضافی تعریف نشده',
                         font=get_font(9), bg='#ffffff',
                         fg='#94a3b8').pack(pady=20)
            else:
                cols = ('id', 'label', 'amount', 'stock', 'actions')
                tree = ttk.Treeview(list_frame, columns=cols,
                                    show='headings', height=10)
                tree.heading('id', text='#')
                tree.heading('label', text='عنوان')
                tree.heading('amount', text='قیمت')
                tree.heading('stock', text='موجودی')
                tree.heading('actions', text='')
                tree.column('id', width=40, anchor='center')
                tree.column('label', width=160, anchor='e')
                tree.column('amount', width=120, anchor='center')
                tree.column('stock', width=70, anchor='center')
                tree.column('actions', width=100, anchor='center')
                tree.pack(fill='both', expand=True, padx=4, pady=4)
                for pr in prices:
                    tree.insert('', 'end', values=(
                        pr['id'], pr['price_label'],
                        format_number(pr['amount']), pr['stock'], '✏️  🗑️'))
                tree.bind('<ButtonRelease-1>', lambda e: _on_price_click(e, tree, pid))

            btn_frame = tk.Frame(list_frame, bg='#ffffff')
            btn_frame.pack(fill='x', pady=(4, 2))
            tk.Button(btn_frame, text='+ قیمت جدید', font=get_font(9),
                      bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                      padx=14, pady=4,
                      command=lambda: _add_price(pid)).pack(side='right', padx=(4, 0))
            tk.Button(btn_frame, text='📦 تامین', font=get_font(9),
                      bg='#059669', fg='#ffffff', bd=0, cursor='hand2',
                      padx=14, pady=4,
                      command=lambda: _supply(pid, tree)).pack(side='right', padx=4)
            tk.Button(btn_frame, text='📋 تاریخچه', font=get_font(9),
                      bg='#d97706', fg='#ffffff', bd=0, cursor='hand2',
                      padx=14, pady=4,
                      command=lambda: _show_history(pid, tree)).pack(side='right', padx=4)

        def _add_price(pid):
            fwin = tk.Toplevel(win)
            fwin.title('قیمت جدید')
            fwin.geometry('380x340')
            fwin.configure(bg='#ffffff')
            frm = tk.Frame(fwin, bg='#ffffff', padx=20, pady=16)
            frm.pack(fill='both', expand=True)
            tk.Label(frm, text='عنوان:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            label_var = tk.StringVar()
            tk.Entry(frm, textvariable=label_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='قیمت خرید:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            buy_var = tk.StringVar(value='0')
            tk.Entry(frm, textvariable=buy_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='قیمت فروش:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            sell_var = tk.StringVar()
            tk.Entry(frm, textvariable=sell_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='تعداد:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            stock_var = tk.StringVar(value='0')
            tk.Entry(frm, textvariable=stock_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='تاریخ:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            date_var = tk.StringVar()
            try:
                from jdatetime import date as jdate
                date_var.set(str(jdate.today()))
            except Exception:
                from datetime import date as gdate
                date_var.set(str(gdate.today()))
            tk.Entry(frm, textvariable=date_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 10))
            def save():
                if not label_var.get().strip() or not sell_var.get().strip():
                    return
                qty = int(stock_var.get() or 0)
                sell = int(sell_var.get())
                buy = int(buy_var.get() or 0)
                price_id = create_product_price(pid, label_var.get().strip(), sell, qty)
                if qty > 0:
                    try:
                        from jdatetime import date as jdate
                        from datetime import datetime
                        jd = jdate.fromisoformat(str(date_var.get()))
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
                fwin.destroy()
                load_prices()
            tk.Button(frm, text='ذخیره', font=get_font(10),
                      bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                      padx=20, pady=4, command=save).pack()

        def _edit_price(pid, price_id, old_label, old_amt, old_stock):
            fwin = tk.Toplevel(win)
            fwin.title('ویرایش قیمت')
            fwin.geometry('350x240')
            fwin.configure(bg='#ffffff')
            frm = tk.Frame(fwin, bg='#ffffff', padx=20, pady=16)
            frm.pack(fill='both', expand=True)
            tk.Label(frm, text='عنوان:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            label_var = tk.StringVar(value=old_label)
            tk.Entry(frm, textvariable=label_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(4, 8))
            tk.Label(frm, text='قیمت:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            amt_var = tk.StringVar(value=str(old_amt))
            tk.Entry(frm, textvariable=amt_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(4, 8))
            tk.Label(frm, text='موجودی:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            stock_var = tk.StringVar(value=str(old_stock))
            tk.Entry(frm, textvariable=stock_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(4, 12))
            def save():
                if not label_var.get().strip() or not amt_var.get().strip():
                    return
                update_product_price(price_id, label_var.get().strip(), int(amt_var.get()),
                                     int(stock_var.get() or 0))
                fwin.destroy()
                load_prices()
            tk.Button(frm, text='ذخیره', font=get_font(10),
                      bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                      padx=20, pady=4, command=save).pack()

        def _selected_price(tree):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('', 'ابتدا یک قیمت را انتخاب کنید')
                return None
            vals = tree.item(sel[0], 'values')
            if not vals:
                return None
            return int(vals[0]), vals[1], int(vals[2]), int(vals[3])

        def _supply(pid, tree):
            sp = _selected_price(tree)
            if not sp:
                return
            price_id, label, amt, stock = sp
            fwin = tk.Toplevel(win)
            fwin.title('تامین کالا')
            fwin.geometry('350x270')
            fwin.configure(bg='#ffffff')
            frm = tk.Frame(fwin, bg='#ffffff', padx=20, pady=16)
            frm.pack(fill='both', expand=True)
            tk.Label(frm, text=f'تامین {label}', font=get_font(10),
                     bg='#ffffff', fg='#1e293b').pack(anchor='e')
            tk.Label(frm, text='تعداد:', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e', pady=(8, 0))
            qty_var = tk.StringVar(value='1')
            tk.Entry(frm, textvariable=qty_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='قیمت خرید (تومان):', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            buy_var = tk.StringVar(value='0')
            tk.Entry(frm, textvariable=buy_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            tk.Label(frm, text='قیمت فروش (تومان):', font=get_font(9), bg='#ffffff',
                     fg='#475569').pack(anchor='e')
            sell_var = tk.StringVar(value=str(amt))
            tk.Entry(frm, textvariable=sell_var, font=get_font(10),
                     bd=1, relief='solid').pack(fill='x', pady=(2, 6))
            def save():
                qty = int(qty_var.get() or 0)
                buy = int(buy_var.get() or 0)
                sell = int(sell_var.get() or 0)
                if qty < 1 or sell < 1:
                    return
                update_product_price(price_id, label, sell, stock + qty)
                create_supply_entry(price_id, qty, buy, sell)
                fwin.destroy()
                load_prices()
            tk.Button(frm, text='ذخیره', font=get_font(10),
                      bg='#059669', fg='#ffffff', bd=0, cursor='hand2',
                      padx=20, pady=4, command=save).pack(pady=(6, 0))

        def _show_history(pid, tree):
            sp = _selected_price(tree)
            if not sp:
                return
            price_id, label, amt, stock = sp
            log = get_supply_log(price_id)
            hwin = tk.Toplevel(win)
            hwin.title(f'تاریخچه تامین - {label}')
            hwin.geometry('700x400')
            hwin.configure(bg='#f0f2f5')
            main = tk.Frame(hwin, bg='#f0f2f5', padx=16, pady=12)
            main.pack(fill='both', expand=True)
            if not log:
                tk.Label(main, text='هیچ تامینی ثبت نشده',
                         font=get_font(10), bg='#f0f2f5',
                         fg='#94a3b8').pack(pady=30)
                return
            cols = ('id', 'date', 'qty', 'buy', 'sell')
            tree2 = ttk.Treeview(main, columns=cols, show='headings', height=16)
            tree2.heading('id', text='#')
            tree2.heading('date', text='تاریخ')
            tree2.heading('qty', text='تعداد')
            tree2.heading('buy', text='قیمت خرید')
            tree2.heading('sell', text='قیمت فروش')
            tree2.column('id', width=40, anchor='center')
            tree2.column('date', width=160, anchor='center')
            tree2.column('qty', width=80, anchor='center')
            tree2.column('buy', width=150, anchor='center')
            tree2.column('sell', width=150, anchor='center')
            for row in log:
                try:
                    from jdatetime import datetime as jdt
                    from datetime import datetime
                    d = jdt.fromgregorian(datetime=datetime.strptime(row['supplied_at'], '%Y-%m-%d %H:%M:%S'))
                    ds = d.strftime('%Y/%m/%d %H:%M')
                except Exception:
                    ds = row['supplied_at']
                tree2.insert('', 'end', values=(
                    row['id'], ds, row['quantity'],
                    format_number(row['buy_price']),
                    format_number(row['sale_price'])))
            tree2.pack(fill='both', expand=True, padx=4, pady=4)

        def _on_price_click(event, tree, pid):
            col = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            if not item or col != '#5':
                return
            vals = tree.item(item, 'values')
            if not vals:
                return
            price_id = int(vals[0])
            x_rel = event.x - tree.bbox(item, '#5')[0]
            if x_rel < 50:
                _edit_price(pid, price_id, vals[1], int(vals[2]), int(vals[3]))
            else:
                if messagebox.askyesno('تأیید', 'حذف شود؟'):
                    delete_product_price(price_id)
                    load_prices()

        prod_var.trace('w', load_prices)
