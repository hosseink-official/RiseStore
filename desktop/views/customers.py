import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_customers, get_customer, create_customer, update_customer, delete_customer, get_customer_sales, get_customer_payments, fetchone
from desktop.theme import Colors, get_font, get_bold_font
from desktop.utils import format_number, format_date


class CustomersView:
    def __init__(self, parent, app):
        self.app = app
        self.parent_frame = parent
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='مشتریان', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')
        self._make_button(header, '➕  مشتری جدید', Colors.accent, Colors.accent_hover,
                          self._add_customer).pack(side='left')

        search_card = tk.Frame(self.frame, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1,
                               padx=4, pady=4)
        search_card.pack(fill='x', pady=(0, 16))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self._load_data())
        search_entry = tk.Entry(search_card, textvariable=self.search_var,
                                font=get_font(10), bd=0, bg=Colors.card,
                                fg=Colors.text_primary)
        search_entry.pack(fill='x', ipady=8, padx=8)
        search_entry.insert(0, '')
        search_placeholder = tk.Label(search_card, text='🔍  جستجوی مشتری...',
                                      font=get_font(9), bg=Colors.card,
                                      fg=Colors.text_muted)
        search_placeholder.pack()

        def on_focus_in(e):
            search_placeholder.pack_forget()
            search_entry.focus()

        def on_focus_out(e):
            if not search_entry.get():
                search_placeholder.pack()

        def on_search_changed(*_):
            if not search_entry.get():
                search_placeholder.pack()
            else:
                search_placeholder.pack_forget()

        search_entry.bind('<FocusIn>', on_focus_in)
        search_entry.bind('<FocusOut>', on_focus_out)
        search_placeholder.bind('<Button-1>', on_focus_in)
        self.search_var.trace('w', on_search_changed)

        self.tree_frame = tk.Frame(self.frame, bg=Colors.card,
                                   highlightbackground=Colors.border, highlightthickness=1)
        self.tree_frame.pack(fill='both', expand=True)

        columns = ('total_debt', 'created_at', 'national_id', 'phone', 'name', 'id')
        self.tree = ttk.Treeview(self.tree_frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('total_debt', text='بدهی', anchor='center')
        self.tree.heading('created_at', text='تاریخ ثبت', anchor='center')
        self.tree.heading('national_id', text='کد ملی', anchor='center')
        self.tree.heading('phone', text='شماره تماس', anchor='center')
        self.tree.heading('name', text='نام', anchor='e')
        self.tree.heading('id', text='#', anchor='center')

        self.tree.column('total_debt', width=120, anchor='center')
        self.tree.column('created_at', width=120, anchor='center')
        self.tree.column('national_id', width=120, anchor='center')
        self.tree.column('phone', width=130, anchor='center')
        self.tree.column('name', width=200, anchor='e')
        self.tree.column('id', width=50, anchor='center')

        scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

        self._load_data()

    def _make_button(self, parent, text, bg, active_bg, command):
        return tk.Button(parent, text=text, font=get_font(10),
                         bg=bg, fg='#ffffff', bd=0, cursor='hand2',
                         padx=18, pady=8, activebackground=active_bg,
                         command=command)

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
                format_number(debt_total),
                format_date(c['created_at']),
                c['national_id'] or '—',
                c['phone'] or '—',
                f"{c['first_name']} {c['last_name']}",
                c['id'],
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
        win.geometry('480x420')
        win.configure(bg=Colors.card)
        win.resizable(False, False)

        header = tk.Frame(win, bg=Colors.accent, height=48)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text=win.title(), font=get_bold_font(12),
                 bg=Colors.accent, fg='#ffffff').pack(expand=True)

        form = tk.Frame(win, bg=Colors.card, padx=32, pady=24)
        form.pack(fill='both', expand=True)

        fields = {}
        for label, key in [('نام', 'first_name'), ('نام خانوادگی', 'last_name'),
                           ('شماره تماس', 'phone'), ('کد ملی', 'national_id'),
                           ('آدرس', 'address')]:
            row = tk.Frame(form, bg=Colors.card)
            row.pack(fill='x', pady=5)
            tk.Label(row, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary, width=12, anchor='e').pack(side='right')
            var = tk.StringVar()
            if customer:
                var.set(customer.get(key) or '')
            entry = tk.Entry(row, textvariable=var, font=get_font(10),
                             bd=1, relief='solid', bg=Colors.card,
                             highlightbackground=Colors.border,
                             highlightcolor=Colors.accent,
                             highlightthickness=1)
            entry.pack(side='right', fill='x', expand=True, padx=(10, 0), ipady=4)
            fields[key] = var

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            if customer:
                update_customer(customer['id'], data)
            else:
                create_customer(data)
            win.destroy()
            self._load_data()

        btn_frame = tk.Frame(form, bg=Colors.card)
        btn_frame.pack(fill='x', pady=(24, 0))
        self._make_button(btn_frame, '💾  ذخیره', Colors.accent, Colors.accent_hover,
                          save).pack(side='left', padx=(0, 8))
        self._make_button(btn_frame, '✕  انصراف', Colors.text_muted, Colors.border,
                          win.destroy).pack(side='left')

    def _delete_customer(self, customer_id):
        if messagebox.askyesno('تأیید حذف', 'آیا از حذف این مشتری اطمینان دارید؟'):
            delete_customer(customer_id)
            self._load_data()

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        cid = int(values[-1])
        menu = tk.Menu(self.frame, tearoff=0, font=get_font(9),
                       bg=Colors.card, fg=Colors.text_primary,
                       activebackground=Colors.accent, activeforeground='#ffffff')
        menu.add_command(label='✏️  ویرایش', command=lambda: self._edit_customer(cid))
        menu.add_command(label='🗑️  حذف', command=lambda: self._delete_customer(cid))
        menu.add_separator()
        menu.add_command(label='📋  مشاهده جزئیات',
                         command=lambda: self._show_customer_detail(cid))
        menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            self._show_customer_detail(int(values[-1]))

    def _show_customer_detail(self, customer_id):
        c = get_customer(customer_id)
        if not c:
            return

        win = tk.Toplevel(self.frame)
        win.title(f"{c['first_name']} {c['last_name']}")
        win.geometry('820x620')
        win.configure(bg=Colors.bg)

        main = tk.Frame(win, bg=Colors.bg, padx=24, pady=20)
        main.pack(fill='both', expand=True)

        info = tk.Frame(main, bg=Colors.card, highlightbackground=Colors.border,
                        highlightthickness=1, padx=20, pady=16)
        info.pack(fill='x', pady=(0, 16))

        name_frame = tk.Frame(info, bg=Colors.card)
        name_frame.pack(fill='x')
        tk.Label(name_frame, text=f"{c['first_name']} {c['last_name']}",
                 font=get_bold_font(16), bg=Colors.card,
                 fg=Colors.text_primary).pack(side='right')
        tk.Button(name_frame, text='✏️  ویرایش', font=get_font(9),
                  bg=Colors.accent, fg='#ffffff', bd=0, cursor='hand2',
                  padx=10, pady=4, activebackground=Colors.accent_hover,
                  command=lambda: self._edit_customer(c['id'])).pack(side='left', padx=(0, 6))
        tk.Button(name_frame, text='🗑️  حذف', font=get_font(9),
                  bg=Colors.danger, fg='#ffffff', bd=0, cursor='hand2',
                  padx=10, pady=4, activebackground=Colors.danger,
                  command=lambda: (win.destroy(), self._delete_customer(c['id']))).pack(side='left')

        info_grid = tk.Frame(info, bg=Colors.card)
        info_grid.pack(fill='x', pady=(8, 0))
        for i, (label, val) in enumerate([('شماره تماس', c.get('phone')),
                                          ('کد ملی', c.get('national_id')),
                                          ('آدرس', c.get('address')),
                                          ('تاریخ ثبت', format_date(c.get('created_at')))]):
            r = tk.Frame(info_grid, bg=Colors.card)
            r.pack(fill='x', pady=1)
            tk.Label(r, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted, width=12, anchor='e').pack(side='right')
            tk.Label(r, text=val or '—', font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary).pack(side='right', padx=(10, 0))

        tk.Label(main, text='فروش‌ها', font=get_bold_font(13),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 8))

        sales = get_customer_sales(customer_id)
        if sales:
            cols = ('type', 'status', 'total', 'date', 'id')
            tree = ttk.Treeview(main, columns=cols, show='headings', height=6)
            tree.heading('type', text='نوع', anchor='center')
            tree.heading('status', text='وضعیت', anchor='center')
            tree.heading('total', text='مبلغ', anchor='center')
            tree.heading('date', text='تاریخ', anchor='center')
            tree.heading('id', text='#', anchor='center')
            tree.column('type', width=100, anchor='center')
            tree.column('status', width=100, anchor='center')
            tree.column('total', width=120, anchor='center')
            tree.column('date', width=120, anchor='center')
            tree.column('id', width=50, anchor='center')
            tree.pack(fill='x', pady=(0, 16))

            status_map = {'paid': 'تسویه', 'pending': 'در انتظار',
                          'partial': 'جزئی', 'cancelled': 'لغو'}
            type_map = {'cash': 'نقدی', 'installment': 'قسطی'}
            for s in sales:
                tree.insert('', 'end', values=(
                    type_map.get(s['payment_type'], s['payment_type']),
                    status_map.get(s['status'], s['status']),
                    format_number(s['total_amount']),
                    format_date(s['sale_date']),
                    s['id'],
                ))
        else:
            tk.Label(main, text='هیچ فروشی وجود ندارد', font=get_font(9),
                     bg=Colors.bg, fg=Colors.text_muted).pack(pady=10)

        tk.Label(main, text='پرداخت‌ها', font=get_bold_font(13),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 8))

        payments = get_customer_payments(customer_id)
        if payments:
            cols = ('sale', 'amount', 'date', 'id')
            tree2 = ttk.Treeview(main, columns=cols, show='headings', height=6)
            tree2.heading('sale', text='فروش', anchor='center')
            tree2.heading('amount', text='مبلغ', anchor='center')
            tree2.heading('date', text='تاریخ', anchor='center')
            tree2.heading('id', text='#', anchor='center')
            tree2.column('sale', width=100, anchor='center')
            tree2.column('amount', width=120, anchor='center')
            tree2.column('date', width=120, anchor='center')
            tree2.column('id', width=50, anchor='center')
            tree2.pack(fill='x')

            for p in payments:
                tree2.insert('', 'end', values=(
                    f"#{p['sale_id']}" if p.get('sale_id') else '—',
                    format_number(p['amount']),
                    format_date(p['payment_date']),
                    p['id'],
                ))
        else:
            tk.Label(main, text='هیچ پرداختی وجود ندارد', font=get_font(9),
                     bg=Colors.bg, fg=Colors.text_muted).pack(pady=10)
