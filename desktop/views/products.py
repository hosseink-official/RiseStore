import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_products, get_product, create_product, update_product, delete_product, get_product_types, get_product_type, create_product_type, update_product_type, delete_product_type
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
        tk.Button(header, text='🔄', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=12, pady=6,
                  command=self._load).pack(side='left', padx=(8, 0))

        columns = ('id', 'name', 'type', 'price', 'cost', 'stock', 'actions')
        self.tree = ttk.Treeview(self.frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('id', text='#', anchor='center')
        self.tree.heading('name', text='نام محصول', anchor='e')
        self.tree.heading('type', text='نوع', anchor='e')
        self.tree.heading('price', text='قیمت فروش', anchor='center')
        self.tree.heading('cost', text='قیمت خرید', anchor='center')
        self.tree.heading('stock', text='موجودی', anchor='center')
        self.tree.heading('actions', text='', anchor='center')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('name', width=200, anchor='e')
        self.tree.column('type', width=120, anchor='e')
        self.tree.column('price', width=120, anchor='center')
        self.tree.column('cost', width=120, anchor='center')
        self.tree.column('stock', width=80, anchor='center')
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
        if not item or col != '#7':
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        pid = int(values[0])
        x_rel = event.x - self.tree.bbox(item, '#7')[0]
        if x_rel < 40:
            self._edit(pid)
        else:
            self._delete(pid)

    def _add(self):
        types = get_product_types()
        type_items = [f'{t["id"]}: {t["name"]}' for t in types]
        fields = [('نام محصول', 'name', 'text'),
                  ('نوع محصول', 'product_type_id', 'combobox'),
                  ('قیمت فروش', 'selling_price', 'number'),
                  ('قیمت خرید', 'purchase_price', 'number'),
                  ('موجودی', 'stock', 'number'),
                  ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'محصول جدید', fields,
                          on_save=self._save_new,
                          combobox_data={'product_type_id': type_items})

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
        fields = [('نام محصول', 'name', 'text'),
                  ('نوع محصول', 'product_type_id', 'combobox'),
                  ('قیمت فروش', 'selling_price', 'number'),
                  ('قیمت خرید', 'purchase_price', 'number'),
                  ('موجودی', 'stock', 'number'),
                  ('توضیحات', 'description', 'textarea')]
        _make_form_dialog(self.frame, 'ویرایش محصول', fields, obj=p,
                          on_save=lambda d: self._save_edit(pid, d),
                          combobox_data={'product_type_id': type_items})

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
