import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    get_all_customers, get_customer, get_all_sales, get_sale,
    create_payment, get_installments, get_installment, update_sale_status,
    sale_total_paid, get_all_payments, get_customer_payments, fetchall
)
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date, add_number_comma_formatting, clean_number


class Colors:
    bg = '#f1f5f9'
    card = '#ffffff'
    accent = '#6366f1'
    accent_hover = '#4f46e5'
    success = '#10b981'
    success_hover = '#059669'
    danger = '#ef4444'
    text_primary = '#0f172a'
    text_secondary = '#475569'
    text_muted = '#94a3b8'
    border = '#e2e8f0'


def _make_button(parent, text, bg, active_bg, command):
    return tk.Button(parent, text=text, font=get_font(10),
                     bg=bg, fg='#ffffff', bd=0, cursor='hand2',
                     padx=18, pady=8, activebackground=active_bg,
                     command=command)


class PaymentsView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='پرداخت‌ها', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')

        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill='both', expand=True)

        new_pay_frame = tk.Frame(notebook, bg=Colors.bg)
        history_frame = tk.Frame(notebook, bg=Colors.bg)
        notebook.add(new_pay_frame, text='  💳  ثبت پرداخت  ')
        notebook.add(history_frame, text='  📋  تاریخچه  ')

        for attr in ('customer_search_var', 'customer_list_frame',
                     'step2_frame', 'amount_frame', 'selected_customer',
                     'selected_sale', 'selected_installment', 'amount_var',
                     'pay_notes_var'):
            setattr(self, attr, None)

        self._build_new_payment(new_pay_frame)
        self._build_history(history_frame)

    def _build_new_payment(self, parent):
        main = tk.Frame(parent, bg=Colors.bg)
        main.pack(fill='both', expand=True, pady=8)

        self.step1_frame = tk.Frame(main, bg=Colors.card,
                                    highlightbackground=Colors.border,
                                    highlightthickness=1, padx=20, pady=16)
        self.step1_frame.pack(fill='x', pady=(0, 12))

        tk.Label(self.step1_frame, text='۱. انتخاب مشتری',
                 font=get_bold_font(12), bg=Colors.card,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 10))

        search_row = tk.Frame(self.step1_frame, bg=Colors.card)
        search_row.pack(fill='x')
        self.customer_search_var = tk.StringVar()
        self.customer_search_var.trace('w', lambda *a: self._search_customers())
        search_entry = tk.Entry(search_row, textvariable=self.customer_search_var,
                                font=get_font(10), bd=1, relief='solid',
                                bg=Colors.card,
                                highlightbackground=Colors.border,
                                highlightcolor=Colors.accent,
                                highlightthickness=1)
        search_entry.pack(fill='x', ipady=6)

        self.customer_list_frame = tk.Frame(self.step1_frame, bg=Colors.card)
        self.customer_list_frame.pack(fill='x', pady=(6, 0))

        self.step2_frame = tk.Frame(main, bg=Colors.card,
                                    highlightbackground=Colors.border,
                                    highlightthickness=1, padx=20, pady=16)
        self.selected_customer = None
        self.selected_sale = None
        self._search_customers()

        self.amount_frame = tk.Frame(main, bg=Colors.card,
                                     highlightbackground=Colors.border,
                                     highlightthickness=1, padx=20, pady=16)

        self._reset()

    def _build_history(self, parent):
        main = tk.Frame(parent, bg=Colors.bg)
        main.pack(fill='both', expand=True, pady=8)

        filter_card = tk.Frame(main, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1,
                               padx=12, pady=8)
        filter_card.pack(fill='x', pady=(0, 12))

        tk.Label(filter_card, text='جستجوی مشتری:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary).pack(side='right', padx=(4, 0))
        search_var = tk.StringVar()
        search_entry = tk.Entry(filter_card, textvariable=search_var, font=get_font(9),
                                bd=1, relief='solid', bg=Colors.card,
                                highlightbackground=Colors.border,
                                highlightcolor=Colors.accent,
                                highlightthickness=1, width=18)
        search_entry.pack(side='right', padx=4, ipady=3)

        tk.Label(filter_card, text='نوع:', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary).pack(side='right', padx=(4, 0))
        type_var = tk.StringVar(value='')
        PTYPE_MAP_REV = {'نقدی': 'cash', 'پرداخت قسط': 'installment_payment', 'پیش پرداخت': 'down_payment'}
        PTYPE_MAP = {'cash': 'نقدی', 'installment_payment': 'پرداخت قسط', 'down_payment': 'پیش پرداخت'}

        type_cb = ttk.Combobox(filter_card, textvariable=type_var,
                                values=['', 'نقدی', 'پرداخت قسط', 'پیش پرداخت'],
                                state='readonly', font=get_font(9), width=14)
        type_cb.pack(side='right', padx=4)

        table_card = tk.Frame(main, bg=Colors.card,
                               highlightbackground=Colors.border, highlightthickness=1)
        table_card.pack(fill='both', expand=True)

        cols = ('sale', 'type', 'amount', 'customer', 'date', 'id')
        tree = ttk.Treeview(table_card, columns=cols, show='headings', height=20)
        tree.heading('sale', text='فاکتور', anchor='center')
        tree.heading('type', text='نوع', anchor='center')
        tree.heading('amount', text='مبلغ', anchor='center')
        tree.heading('customer', text='مشتری', anchor='e')
        tree.heading('date', text='تاریخ', anchor='center')
        tree.heading('id', text='#', anchor='center')
        tree.column('sale', width=80, anchor='center')
        tree.column('type', width=110, anchor='center')
        tree.column('amount', width=130, anchor='center')
        tree.column('customer', width=220, anchor='e')
        tree.column('date', width=150, anchor='center')
        tree.column('id', width=50, anchor='center')
        tree.pack(fill='both', expand=True, padx=6, pady=6)

        sale_index_map = {}

        def _get_sale_index_map(payments):
            mapping = {}
            customer_ids = set(p['customer_id'] for p in payments)
            for cid in customer_ids:
                sales = fetchall(
                    "SELECT id FROM store_sale WHERE customer_id=? ORDER BY sale_date, id",
                    [cid]
                )
                for i, s in enumerate(sales, 1):
                    mapping[(cid, s['id'])] = i
            return mapping

        def load_history(*_):
            nonlocal sale_index_map
            for item in tree.get_children():
                tree.delete(item)
            q = search_var.get().strip()
            pt = PTYPE_MAP_REV.get(type_var.get()) if type_var.get() else None
            all_payments = get_all_payments(limit=500)
            sale_index_map = _get_sale_index_map(all_payments)
            for p in all_payments:
                name = f"{p['first_name']} {p['last_name']}"
                if q and q.lower() not in name.lower():
                    continue
                if pt and p['payment_type'] != pt:
                    continue
                idx = sale_index_map.get((p['customer_id'], p['sale_id']), '')
                factor_text = f"{name} {idx}" if idx else f"#{p['sale_id']}"
                tree.insert('', 'end', values=(
                    factor_text,
                    PTYPE_MAP.get(p['payment_type'], p['payment_type']),
                    format_number(p['amount']),
                    name,
                    format_date(p['payment_date']),
                    p['id'],
                ))

        def on_payment_click(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            values = tree.item(item, 'values')
            if not values:
                return
            pid = values[-1]
            all_payments = get_all_payments(limit=500)
            target = next((p for p in all_payments if str(p['id']) == pid), None)
            if not target:
                return
            win = tk.Toplevel(self.frame.winfo_toplevel())
            win.title(f"تاریخچه پرداخت‌ها — {target['first_name']} {target['last_name']}")
            win.geometry('700x500')
            win.configure(bg=Colors.bg)
            main = tk.Frame(win, bg=Colors.bg, padx=20, pady=16)
            main.pack(fill='both', expand=True)
            tk.Label(main, text=f"همه پرداخت‌های {target['first_name']} {target['last_name']}",
                     font=get_bold_font(14), bg=Colors.bg,
                     fg=Colors.text_primary).pack(anchor='e', pady=(0, 12))
            cols = ('sale', 'type', 'amount', 'date', 'id')
            t2 = ttk.Treeview(main, columns=cols, show='headings', height=18)
            t2.heading('sale', text='فاکتور', anchor='center')
            t2.heading('type', text='نوع', anchor='center')
            t2.heading('amount', text='مبلغ', anchor='center')
            t2.heading('date', text='تاریخ', anchor='center')
            t2.heading('id', text='#', anchor='center')
            t2.column('sale', width=100, anchor='center')
            t2.column('type', width=120, anchor='center')
            t2.column('amount', width=140, anchor='center')
            t2.column('date', width=150, anchor='center')
            t2.column('id', width=50, anchor='center')
            t2.pack(fill='both', expand=True)
            cust_payments = get_customer_payments(target['customer_id'])
            for cp in cust_payments:
                cidx = sale_index_map.get((target['customer_id'], cp['sale_id']), '')
                cfactor = f"{target['first_name']} {target['last_name']} {cidx}" if cidx else f"#{cp['sale_id']}"
                t2.insert('', 'end', values=(
                    cfactor,
                    PTYPE_MAP.get(cp['payment_type'], cp['payment_type']),
                    format_number(cp['amount']),
                    format_date(cp['payment_date']),
                    cp['id'],
                ))

        tree.bind('<Double-1>', on_payment_click)

        search_var.trace('w', load_history)
        type_var.trace('w', load_history)
        load_history()

    def _reset(self):
        self.selected_customer = None
        self.selected_sale = None
        self.step2_frame.pack_forget()
        self.amount_frame.pack_forget()

    def _search_customers(self):
        for w in self.customer_list_frame.winfo_children():
            w.destroy()
        q = self.customer_search_var.get().strip()
        customers = get_all_customers(q) if q else get_all_customers()
        for c in customers[:15]:
            btn = tk.Button(self.customer_list_frame,
                            text=f"{c['first_name']} {c['last_name']} — {c.get('phone') or ''}",
                            font=get_font(9), bg=Colors.card, fg=Colors.text_secondary,
                            bd=0, anchor='w', padx=10, pady=6,
                            cursor='hand2',
                            command=lambda cid=c['id']: self._select_customer(cid))
            btn.pack(fill='x', pady=1)

    def _select_customer(self, cid):
        self.selected_customer = get_customer(cid)
        self._show_sales()

    def _show_sales(self):
        for w in self.step2_frame.winfo_children():
            w.destroy()

        tk.Label(self.step2_frame, text='۲. انتخاب فاکتور',
                 font=get_bold_font(12), bg=Colors.card,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 10))

        pending_sales = [
            s for s in get_all_sales()
            if s['customer_id'] == self.selected_customer['id']
            and s['status'] in ('pending', 'partial')
        ]
        if not pending_sales:
            tk.Label(self.step2_frame, text='فاکتوری با بدهی وجود ندارد',
                     font=get_font(9), bg=Colors.card,
                     fg=Colors.text_muted).pack(pady=10)
        else:
            for s in pending_sales:
                from desktop.db import sale_remaining
                remaining = sale_remaining(s['id'])
                btn = tk.Button(self.step2_frame,
                                text=f"#{s['id']} — {format_number(s['total_amount'])} "
                                     f"(باقی‌مانده: {format_number(remaining)})",
                                font=get_font(9), bg=Colors.card, fg=Colors.text_secondary,
                                bd=0, anchor='w', padx=10, pady=6,
                                cursor='hand2',
                                command=lambda sid=s['id']: self._select_sale(sid))
                btn.pack(fill='x', pady=1)

        self.step2_frame.pack(fill='x', pady=(0, 12))

    def _select_sale(self, sid):
        self.selected_sale = get_sale(sid)
        self._show_amount_form()

    def _show_amount_form(self):
        for w in self.amount_frame.winfo_children():
            w.destroy()

        tk.Label(self.amount_frame, text='۳. مشخصات پرداخت',
                 font=get_bold_font(12), bg=Colors.card,
                 fg=Colors.text_primary).pack(anchor='e', pady=(0, 10))

        installments = get_installments(self.selected_sale['id'], self.selected_customer['id'])
        self.selected_installment = None

        if installments:
            inst_label = tk.Label(self.amount_frame, text='قسط‌ها:',
                                  font=get_font(9), bg=Colors.card,
                                  fg=Colors.text_secondary).pack(anchor='e')
            for inst in installments:
                btn = tk.Button(self.amount_frame,
                                text=f"قسط {inst['paid_count'] + 1}/{inst['total_count']} — "
                                     f"{format_number(inst['amount_per_term'])}",
                                font=get_font(9), bg=Colors.card, fg=Colors.text_secondary,
                                bd=0, anchor='w', padx=10, pady=4,
                                cursor='hand2',
                                command=lambda ii=inst: self._select_installment(ii))
                btn.pack(fill='x', pady=1)

        row = tk.Frame(self.amount_frame, bg=Colors.card)
        row.pack(fill='x', pady=(10, 8))
        tk.Label(row, text='مبلغ:', font=get_font(9), bg=Colors.card,
                 fg=Colors.text_secondary, width=10, anchor='e').pack(side='right')
        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(row, textvariable=self.amount_var, font=get_font(10),
                 bd=1, relief='solid', bg=Colors.card,
                 highlightbackground=Colors.border,
                 highlightcolor=Colors.accent,
                 highlightthickness=1, width=25)
        amount_entry.pack(side='right', padx=(10, 0), ipady=4)
        add_number_comma_formatting(self.amount_var, amount_entry)

        notes_frame = tk.Frame(self.amount_frame, bg=Colors.card)
        notes_frame.pack(fill='x', pady=(0, 12))
        tk.Label(notes_frame, text='توضیحات:', font=get_font(9), bg=Colors.card,
                 fg=Colors.text_secondary, width=10, anchor='e').pack(side='right')
        self.pay_notes_var = tk.StringVar()
        tk.Entry(notes_frame, textvariable=self.pay_notes_var,
                 font=get_font(10), bd=1, relief='solid', bg=Colors.card,
                 highlightbackground=Colors.border,
                 highlightcolor=Colors.accent,
                 highlightthickness=1).pack(side='right', padx=(10, 0), fill='x', expand=True, ipady=4)

        _make_button(self.amount_frame, '✅  ثبت پرداخت', Colors.success, Colors.success_hover,
                     self._submit).pack(pady=(8, 0))

        self.amount_frame.pack(fill='x')

    def _select_installment(self, inst):
        self.selected_installment = inst
        remaining_total = (self.selected_sale['total_amount'] or 0) - sale_total_paid(self.selected_sale['id'])
        remaining_count = inst['total_count'] - inst['paid_count']
        default = max(1, remaining_total // remaining_count) if remaining_count > 0 else inst['amount_per_term']
        self.amount_var.set(str(default))

    def _submit(self):
        if not self.amount_var.get().strip():
            messagebox.showwarning('', 'مبلغ را وارد کنید')
            return
        amount = int(clean_number(self.amount_var.get()))
        notes = self.pay_notes_var.get().strip()

        payment_type = 'installment_payment' if self.selected_installment else 'cash'

        create_payment(
            self.selected_sale['id'],
            self.selected_customer['id'],
            amount,
            payment_type,
            notes
        )

        if self.selected_installment:
            inst = self.selected_installment
            new_paid = inst['paid_count'] + 1
            new_status = 'paid' if new_paid >= inst['total_count'] else 'active'
            from desktop.db import execute as db_exe
            db_exe(
                "UPDATE store_installment SET paid_count=?, amount_paid=COALESCE(amount_paid,0)+?, status=? WHERE id=?",
                [new_paid, amount, new_status, inst['id']]
            )

        from desktop.db import execute as db_exe2
        total_paid = sale_total_paid(self.selected_sale['id'])
        remaining = (self.selected_sale['total_amount'] or 0) - total_paid
        if remaining <= 0:
            db_exe2("UPDATE store_sale SET status='paid' WHERE id=?",
                    [self.selected_sale['id']])
        elif total_paid > 0:
            db_exe2("UPDATE store_sale SET status='partial' WHERE id=?",
                    [self.selected_sale['id']])

        messagebox.showinfo('', 'پرداخت با موفقیت ثبت شد')
        self._reset()
