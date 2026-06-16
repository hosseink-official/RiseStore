import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_customers, get_customer, create_customer, update_customer, delete_customer, get_customer_sales, get_customer_payments, fetchone, fetchall
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date


class CustomersView:
    def __init__(self, parent, app):
        self.app = app
        self.parent_frame = parent
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        header = tk.Frame(self.frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text='مشتریان', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(side='right')
        tk.Button(header, text='+ مشتری جدید', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=16, pady=6, command=self._add_customer).pack(side='left')

        search_frame = tk.Frame(self.frame, bg='#ffffff',
                                highlightbackground='#e2e8f0', highlightthickness=1)
        search_frame.pack(fill='x', pady=(0, 12))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self._load_data())
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=get_font(10), bd=0, bg='#ffffff',
                 fg='#334155').pack(fill='x', ipady=6, padx=12)

        self.tree_frame = tk.Frame(self.frame, bg='#ffffff')
        self.tree_frame.pack(fill='both', expand=True)

        columns = ('id', 'name', 'phone', 'national_id', 'created_at', 'total_debt', 'actions')
        self.tree = ttk.Treeview(self.tree_frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('id', text='#', anchor='center')
        self.tree.heading('name', text='نام', anchor='e')
        self.tree.heading('phone', text='شماره تماس', anchor='center')
        self.tree.heading('national_id', text='کد ملی', anchor='center')
        self.tree.heading('created_at', text='تاریخ ثبت', anchor='center')
        self.tree.heading('total_debt', text='بدهی', anchor='center')
        self.tree.heading('actions', text='', anchor='center')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('name', width=180, anchor='e')
        self.tree.column('phone', width=120, anchor='center')
        self.tree.column('national_id', width=120, anchor='center')
        self.tree.column('created_at', width=120, anchor='center')
        self.tree.column('total_debt', width=120, anchor='center')
        self.tree.column('actions', width=120, anchor='center')

        scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<ButtonRelease-1>', self._on_click)

        self._load_data()

    def _load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        q = self.search_var.get().strip()
        customers = get_all_customers(q) if q else get_all_customers()

        for c in customers:
            total = fetchone("SELECT COALESCE(SUM(total_amount),0) as s FROM store_sale WHERE customer_id=? AND status IN ('pending','partial')", [c['id']])
            paid = fetchone("SELECT COALESCE(SUM(amount),0) as s FROM store_payment WHERE customer_id=?", [c['id']])
            debt_total = max(0, (total['s'] or 0) - (paid['s'] or 0))

            self.tree.insert('', 'end', values=(
                c['id'],
                f"{c['first_name']} {c['last_name']}",
                c['phone'] or '—',
                c['national_id'] or '—',
                format_date(c['created_at']),
                format_number(debt_total),
                '✏️  🗑️',
            ))

    def _add_customer(self):
        self._show_customer_form()

    def _edit_customer(self, customer_id):
        c = get_customer(customer_id)
        if c:
            self._show_customer_form(c)

    def _show_customer_form(self, customer=None):
        win = tk.Toplevel(self.frame)
        win.title('ویرایش مشتری' if customer else 'مشتری جدید')
        win.geometry('450x350')
        win.configure(bg='#ffffff')
        win.resizable(False, False)

        form = tk.Frame(win, bg='#ffffff', padx=24, pady=20)
        form.pack(fill='both', expand=True)

        fields = {}
        for label, key in [('نام', 'first_name'), ('نام خانوادگی', 'last_name'),
                           ('شماره تماس', 'phone'), ('کد ملی', 'national_id'),
                           ('آدرس', 'address')]:
            row = tk.Frame(form, bg='#ffffff')
            row.pack(fill='x', pady=4)
            tk.Label(row, text=label, font=get_font(9), bg='#ffffff',
                     fg='#475569', width=12, anchor='e').pack(side='right')
            var = tk.StringVar()
            if customer:
                var.set(customer.get(key) or '')
            tk.Entry(row, textvariable=var, font=get_font(10),
                     bd=1, relief='solid', bg='#ffffff').pack(
                         side='right', fill='x', expand=True, padx=(8, 0))
            fields[key] = var

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            if customer:
                update_customer(customer['id'], data)
            else:
                create_customer(data)
            win.destroy()
            self._load_data()

        btn_frame = tk.Frame(form, bg='#ffffff')
        btn_frame.pack(fill='x', pady=(20, 0))
        tk.Button(btn_frame, text='ذخیره', font=get_font(10),
                  bg='#2563eb', fg='#ffffff', bd=0, cursor='hand2',
                  padx=20, pady=6, command=save).pack(side='left')
        tk.Button(btn_frame, text='انصراف', font=get_font(10),
                  bg='#e2e8f0', fg='#475569', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=win.destroy).pack(side='left', padx=(8, 0))

    def _delete_customer(self, customer_id):
        if messagebox.askyesno('تأیید حذف', 'آیا از حذف این مشتری اطمینان دارید؟'):
            delete_customer(customer_id)
            self._load_data()

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        cid = int(values[0])
        if col == '#7':
            bbox = self.tree.bbox(item, '#7')
            if not bbox:
                return
            x_rel = event.x - bbox[0]
            if x_rel < 60:
                self._edit_customer(cid)
            else:
                self._delete_customer(cid)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            self._show_customer_detail(int(values[0]))

    def _show_customer_detail(self, customer_id):
        c = get_customer(customer_id)
        if not c:
            return

        win = tk.Toplevel(self.frame)
        win.title(f"{c['first_name']} {c['last_name']}")
        win.geometry('800x600')
        win.configure(bg='#f0f2f5')

        main = tk.Frame(win, bg='#f0f2f5', padx=20, pady=16)
        main.pack(fill='both', expand=True)

        info = tk.Frame(main, bg='#ffffff', highlightbackground='#e2e8f0',
                        highlightthickness=1, padx=16, pady=12)
        info.pack(fill='x', pady=(0, 12))

        tk.Label(info, text=f"{c['first_name']} {c['last_name']}",
                 font=get_bold_font(14), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e')
        for label, val in [('شماره تماس', c.get('phone')), ('کد ملی', c.get('national_id')),
                           ('آدرس', c.get('address')), ('تاریخ ثبت', format_date(c.get('created_at')))]:
            r = tk.Frame(info, bg='#ffffff')
            r.pack(fill='x', pady=1)
            tk.Label(r, text=label, font=get_font(9), bg='#ffffff',
                     fg='#64748b', width=12, anchor='e').pack(side='right')
            tk.Label(r, text=val or '—', font=get_font(9), bg='#ffffff',
                     fg='#334155').pack(side='right', padx=(8, 0))

        tk.Label(main, text='فروش‌ها', font=get_bold_font(12),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 8))

        sales = get_customer_sales(customer_id)
        if sales:
            cols = ('id', 'date', 'total', 'status', 'type')
            tree = ttk.Treeview(main, columns=cols, show='headings', height=6)
            tree.heading('id', text='#')
            tree.heading('date', text='تاریخ')
            tree.heading('total', text='مبلغ')
            tree.heading('status', text='وضعیت')
            tree.heading('type', text='نوع')
            tree.column('id', width=50, anchor='center')
            tree.column('date', width=120, anchor='center')
            tree.column('total', width=120, anchor='center')
            tree.column('status', width=100, anchor='center')
            tree.column('type', width=100, anchor='center')
            tree.pack(fill='x', pady=(0, 12))

            status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                          'partial': 'جزئی', 'cancelled': 'لغو'}
            type_map = {'cash': 'نقدی', 'installment': 'قسطی'}
            for s in sales:
                tree.insert('', 'end', values=(
                    s['id'], format_date(s['sale_date']),
                    format_number(s['total_amount']),
                    status_map.get(s['status'], s['status']),
                    type_map.get(s['payment_type'], s['payment_type']),
                ))
        else:
            tk.Label(main, text='هیچ فروشی وجود ندارد', font=get_font(9),
                     bg='#f0f2f5', fg='#94a3b8').pack(pady=10)

        tk.Label(main, text='پرداخت‌ها', font=get_bold_font(12),
                 bg='#f0f2f5', fg='#1e293b').pack(anchor='e', pady=(0, 8))

        payments = get_customer_payments(customer_id)
        if payments:
            cols = ('id', 'date', 'amount', 'sale')
            tree2 = ttk.Treeview(main, columns=cols, show='headings', height=6)
            tree2.heading('id', text='#')
            tree2.heading('date', text='تاریخ')
            tree2.heading('amount', text='مبلغ')
            tree2.heading('sale', text='فروش')
            tree2.column('id', width=50, anchor='center')
            tree2.column('date', width=120, anchor='center')
            tree2.column('amount', width=120, anchor='center')
            tree2.column('sale', width=100, anchor='center')
            tree2.pack(fill='x')

            for p in payments:
                tree2.insert('', 'end', values=(
                    p['id'], format_date(p['payment_date']),
                    format_number(p['amount']),
                    f"#{p['sale_id']}" if p.get('sale_id') else '—',
                ))
        else:
            tk.Label(main, text='هیچ پرداختی وجود ندارد', font=get_font(9),
                     bg='#f0f2f5', fg='#94a3b8').pack(pady=10)
