import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import (
    get_all_customers, get_customer, get_all_sales, get_sale,
    create_payment, get_installments, get_installment, update_sale_status,
    sale_total_paid, get_all_payments
)
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_number, format_date


class PaymentsView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True, padx=24, pady=20)

        header = tk.Frame(self.frame, bg='#f0f2f5')
        header.pack(fill='x', pady=(0, 16))
        tk.Label(header, text='پرداخت‌ها', font=get_bold_font(18),
                 bg='#f0f2f5', fg='#1e293b').pack(side='right')

        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill='both', expand=True)

        new_pay_frame = tk.Frame(notebook, bg='#f0f2f5')
        history_frame = tk.Frame(notebook, bg='#f0f2f5')
        notebook.add(new_pay_frame, text='  ثبت پرداخت  ')
        notebook.add(history_frame, text='  تاریخچه  ')

        for attr in ('customer_search_var', 'customer_list_frame',
                     'step2_frame', 'amount_frame', 'selected_customer',
                     'selected_sale', 'selected_installment', 'amount_var',
                     'pay_notes_var'):
            setattr(self, attr, None)

        self._build_new_payment(new_pay_frame)
        self._build_history(history_frame)

    def _build_new_payment(self, parent):
        main = tk.Frame(parent, bg='#f0f2f5')
        main.pack(fill='both', expand=True, pady=8)

        self.step1_frame = tk.Frame(main, bg='#ffffff',
                                    highlightbackground='#e2e8f0',
                                    highlightthickness=1, padx=16, pady=12)
        self.step1_frame.pack(fill='x', pady=(0, 12))
        tk.Label(self.step1_frame, text='۱. انتخاب مشتری',
                 font=get_bold_font(12), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 8))

        self.customer_search_var = tk.StringVar()
        self.customer_search_var.trace('w', lambda *a: self._search_customers())
        tk.Entry(self.step1_frame, textvariable=self.customer_search_var,
                 font=get_font(10), bd=1, relief='solid').pack(
                     fill='x', ipady=6, pady=(0, 8))

        self.customer_list_frame = tk.Frame(self.step1_frame, bg='#ffffff')
        self.customer_list_frame.pack(fill='x')

        self.step2_frame = tk.Frame(main, bg='#ffffff',
                                    highlightbackground='#e2e8f0',
                                    highlightthickness=1, padx=16, pady=12)
        self.selected_customer = None
        self.selected_sale = None
        self._search_customers()

        self.amount_frame = tk.Frame(main, bg='#ffffff',
                                     highlightbackground='#e2e8f0',
                                     highlightthickness=1, padx=16, pady=12)

        self._reset()

    def _build_history(self, parent):
        main = tk.Frame(parent, bg='#f0f2f5')
        main.pack(fill='both', expand=True, pady=8)

        filter_bar = tk.Frame(main, bg='#ffffff',
                              highlightbackground='#e2e8f0', highlightthickness=1)
        filter_bar.pack(fill='x', pady=(0, 8))

        tk.Label(filter_bar, text='جستجوی مشتری:', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right', padx=(4, 0), pady=6)
        search_var = tk.StringVar()
        tk.Entry(filter_bar, textvariable=search_var, font=get_font(9),
                 bd=1, relief='solid', width=18).pack(side='right', padx=4, pady=6)

        tk.Label(filter_bar, text='نوع:', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right', padx=(4, 0), pady=6)
        type_var = tk.StringVar(value='')
        type_cb = ttk.Combobox(filter_bar, textvariable=type_var,
                               values=['', 'cash', 'installment_payment', 'down_payment'],
                               state='readonly', font=get_font(9), width=14)
        type_cb.pack(side='right', padx=4, pady=6)

        table_frame = tk.Frame(main, bg='#ffffff',
                               highlightbackground='#e2e8f0', highlightthickness=1)
        table_frame.pack(fill='both', expand=True)

        cols = ('id', 'date', 'customer', 'amount', 'type', 'sale')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=20)
        tree.heading('id', text='#', anchor='center')
        tree.heading('date', text='تاریخ', anchor='center')
        tree.heading('customer', text='مشتری', anchor='e')
        tree.heading('amount', text='مبلغ', anchor='center')
        tree.heading('type', text='نوع', anchor='center')
        tree.heading('sale', text='فاکتور', anchor='center')
        tree.column('id', width=50, anchor='center')
        tree.column('date', width=140, anchor='center')
        tree.column('customer', width=200, anchor='e')
        tree.column('amount', width=120, anchor='center')
        tree.column('type', width=100, anchor='center')
        tree.column('sale', width=80, anchor='center')
        tree.pack(fill='both', expand=True, padx=8, pady=8)

        def load_history(*_):
            for item in tree.get_children():
                tree.delete(item)
            q = search_var.get().strip()
            pt = type_var.get()
            all_payments = get_all_payments(limit=500)
            for p in all_payments:
                name = f"{p['first_name']} {p['last_name']}"
                if q and q.lower() not in name.lower():
                    continue
                if pt and p['payment_type'] != pt:
                    continue
                tree.insert('', 'end', values=(
                    p['id'],
                    format_date(p['payment_date']),
                    name,
                    format_number(p['amount']),
                    p['payment_type'],
                    f"#{p['sale_id']}",
                ))

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
                            font=get_font(9), bg='#ffffff', fg='#334155',
                            bd=0, anchor='w', padx=8, pady=4,
                            cursor='hand2',
                            command=lambda cid=c['id']: self._select_customer(cid))
            btn.pack(fill='x')

    def _select_customer(self, cid):
        self.selected_customer = get_customer(cid)
        self._show_sales()

    def _show_sales(self):
        for w in self.step2_frame.winfo_children():
            w.destroy()

        tk.Label(self.step2_frame, text='۲. انتخاب فاکتور',
                 font=get_bold_font(12), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 8))

        pending_sales = [
            s for s in get_all_sales()
            if s['customer_id'] == self.selected_customer['id']
            and s['status'] in ('pending', 'partial')
        ]
        if not pending_sales:
            tk.Label(self.step2_frame, text='فاکتوری با بدهی وجود ندارد',
                     font=get_font(9), bg='#ffffff',
                     fg='#94a3b8').pack(pady=10)
        else:
            for s in pending_sales:
                from desktop.db import sale_remaining
                remaining = sale_remaining(s['id'])
                btn = tk.Button(self.step2_frame,
                                text=f"#{s['id']} — {format_number(s['total_amount'])} "
                                     f"(باقی‌مانده: {format_number(remaining)})",
                                font=get_font(9), bg='#ffffff', fg='#334155',
                                bd=0, anchor='w', padx=8, pady=4,
                                cursor='hand2',
                                command=lambda sid=s['id']: self._select_sale(sid))
                btn.pack(fill='x')

        self.step2_frame.pack(fill='x', pady=(0, 12))

    def _select_sale(self, sid):
        self.selected_sale = get_sale(sid)
        self._show_amount_form()

    def _show_amount_form(self):
        for w in self.amount_frame.winfo_children():
            w.destroy()

        tk.Label(self.amount_frame, text='۳. مشخصات پرداخت',
                 font=get_bold_font(12), bg='#ffffff',
                 fg='#1e293b').pack(anchor='e', pady=(0, 8))

        installments = get_installments(self.selected_sale['id'], self.selected_customer['id'])
        self.selected_installment = None

        if installments:
            for inst in installments:
                btn = tk.Button(self.amount_frame,
                                text=f"قسط {inst['paid_count'] + 1}/{inst['total_count']} — "
                                     f"{format_number(inst['amount_per_term'])}",
                                font=get_font(9), bg='#ffffff', fg='#334155',
                                bd=0, anchor='w', padx=8, pady=2,
                                cursor='hand2',
                                command=lambda ii=inst: self._select_installment(ii))
                btn.pack(fill='x')

        row = tk.Frame(self.amount_frame, bg='#ffffff')
        row.pack(fill='x', pady=8)
        tk.Label(row, text='مبلغ:', font=get_font(9), bg='#ffffff',
                 fg='#475569').pack(side='right')
        self.amount_var = tk.StringVar()
        tk.Entry(row, textvariable=self.amount_var, font=get_font(10),
                 bd=1, relief='solid', width=25).pack(side='right', padx=(8, 0))

        notes_frame = tk.Frame(self.amount_frame, bg='#ffffff')
        notes_frame.pack(fill='x', pady=(0, 8))
        tk.Label(notes_frame, text='توضیحات:', font=get_font(9),
                 bg='#ffffff', fg='#475569').pack(side='right')
        self.pay_notes_var = tk.StringVar()
        tk.Entry(notes_frame, textvariable=self.pay_notes_var,
                 font=get_font(10), bd=1, relief='solid').pack(
                     side='right', padx=(8, 0), fill='x', expand=True)

        tk.Button(self.amount_frame, text='ثبت پرداخت', font=get_font(10),
                  bg='#16a34a', fg='#ffffff', bd=0, cursor='hand2',
                  padx=20, pady=6,
                  command=self._submit).pack(pady=(8, 0))

        self.amount_frame.pack(fill='x')

    def _select_installment(self, inst):
        self.selected_installment = inst
        self.amount_var.set(str(inst['amount_per_term']))

    def _submit(self):
        if not self.amount_var.get().strip():
            messagebox.showwarning('', 'مبلغ را وارد کنید')
            return
        amount = int(self.amount_var.get())
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
