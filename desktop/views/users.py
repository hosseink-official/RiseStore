import tkinter as tk
from tkinter import ttk, messagebox
from desktop.db import get_all_users, get_user, create_user, update_user, delete_user
from desktop.fonts import get_font, get_bold_font
from desktop.utils import format_date, persian_digits


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
    border_light = '#f1f5f9'


class UsersView:
    def __init__(self, parent, app):
        self.app = app
        self.parent_frame = parent
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        header = tk.Frame(self.frame, bg=Colors.bg)
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text='کاربران', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(side='right')
        self._make_button(header, '➕  کاربر جدید', Colors.accent, Colors.accent_hover,
                          self._add_user).pack(side='left')

        self.tree_frame = tk.Frame(self.frame, bg=Colors.card,
                                   highlightbackground=Colors.border, highlightthickness=1)
        self.tree_frame.pack(fill='both', expand=True)

        columns = ('is_active', 'is_staff', 'date_joined', 'email', 'last_name', 'username', 'id')
        self.tree = ttk.Treeview(self.tree_frame, columns=columns,
                                 show='headings', height=20)
        self.tree.heading('is_active', text='فعال', anchor='center')
        self.tree.heading('is_staff', text='مدیر', anchor='center')
        self.tree.heading('date_joined', text='تاریخ ثبت', anchor='center')
        self.tree.heading('email', text='ایمیل', anchor='center')
        self.tree.heading('last_name', text='نام خانوادگی', anchor='e')
        self.tree.heading('username', text='نام کاربری', anchor='e')
        self.tree.heading('id', text='#', anchor='center')

        self.tree.column('is_active', width=70, anchor='center')
        self.tree.column('is_staff', width=70, anchor='center')
        self.tree.column('date_joined', width=120, anchor='center')
        self.tree.column('email', width=180, anchor='center')
        self.tree.column('last_name', width=140, anchor='e')
        self.tree.column('username', width=140, anchor='e')
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

        for u in get_all_users():
            self.tree.insert('', 'end', values=(
                '✅' if u['is_active'] else '❌',
                '✅' if u['is_staff'] else '—',
                format_date(u['date_joined']),
                u['email'] or '—',
                u['last_name'] or '—',
                u['username'],
                persian_digits(u['id']),
            ))

    def _add_user(self):
        self._show_user_form()

    def _edit_user(self, user_id):
        u = get_user(user_id)
        if u:
            self._show_user_form(u)

    def _show_user_form(self, user=None):
        win = tk.Toplevel(self.frame)
        win.title('ویرایش کاربر' if user else 'کاربر جدید')
        win.geometry('480x500')
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
        for label, key, show in [('نام کاربری', 'username', True),
                                  ('رمز عبور', 'password', not user),
                                  ('تکرار رمز عبور', 'password2', not user),
                                  ('نام', 'first_name', True),
                                  ('نام خانوادگی', 'last_name', True),
                                  ('ایمیل', 'email', True)]:
            row = tk.Frame(form, bg=Colors.card)
            row.pack(fill='x', pady=5)
            tk.Label(row, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')

            if key in ('password', 'password2'):
                var = tk.StringVar()
                entry = tk.Entry(row, textvariable=var, font=get_font(10),
                                 show='*',
                                 bd=1, relief='solid', bg=Colors.card,
                                 highlightbackground=Colors.border,
                                 highlightcolor=Colors.accent,
                                 highlightthickness=1)
                entry.pack(side='right', fill='x', expand=True, padx=(10, 0), ipady=4)
                fields[key] = var
            elif show:
                var = tk.StringVar()
                if user:
                    var.set(user.get(key) or '')
                entry = tk.Entry(row, textvariable=var, font=get_font(10),
                                 bd=1, relief='solid', bg=Colors.card,
                                 highlightbackground=Colors.border,
                                 highlightcolor=Colors.accent,
                                 highlightthickness=1)
                entry.pack(side='right', fill='x', expand=True, padx=(10, 0), ipady=4)
                fields[key] = var

        is_staff_var = tk.BooleanVar(value=user['is_staff'] if user else False)
        is_active_var = tk.BooleanVar(value=user['is_active'] if user else True)

        for label, var in [('مدیر', is_staff_var), ('فعال', is_active_var)]:
            row = tk.Frame(form, bg=Colors.card)
            row.pack(fill='x', pady=5)
            tk.Label(row, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
            cb = tk.Checkbutton(row, variable=var, bg=Colors.card,
                                font=get_font(9))
            cb.pack(side='right', padx=(10, 0))

        def save():
            data = {}
            for k, v in fields.items():
                data[k] = v.get().strip()
            data['is_staff'] = is_staff_var.get()
            data['is_active'] = is_active_var.get()

            if not data.get('username'):
                messagebox.showwarning('', 'نام کاربری الزامی است')
                return
            if user and data.get('password') and data['password'] != data.get('password2', ''):
                messagebox.showwarning('', 'رمز عبور و تکرار آن مطابقت ندارند')
                return
            if not user:
                if not data.get('password'):
                    messagebox.showwarning('', 'رمز عبور الزامی است')
                    return
                if data['password'] != data.get('password2', ''):
                    messagebox.showwarning('', 'رمز عبور و تکرار آن مطابقت ندارند')
                    return

            if user:
                update_user(user['id'], data)
            else:
                create_user(data)
            win.destroy()
            self._load_data()

        btn_frame = tk.Frame(form, bg=Colors.card)
        btn_frame.pack(fill='x', pady=(24, 0))
        self._make_button(btn_frame, '💾  ذخیره', Colors.accent, Colors.accent_hover,
                          save).pack(side='left', padx=(0, 8))
        self._make_button(btn_frame, '✕  انصراف', Colors.text_muted, Colors.border,
                          win.destroy).pack(side='left')

    def _delete_user(self, user_id):
        if user_id == self.app.user.get('id'):
            messagebox.showwarning('', 'نمی‌توانید خودتان را حذف کنید')
            return
        if messagebox.askyesno('تأیید حذف', 'آیا از حذف این کاربر اطمینان دارید؟'):
            delete_user(user_id)
            self._load_data()

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        uid = int(values[-1])
        menu = tk.Menu(self.frame, tearoff=0, font=get_font(9),
                       bg=Colors.card, fg=Colors.text_primary,
                       activebackground=Colors.accent, activeforeground='#ffffff')
        menu.add_command(label='✏️  ویرایش', command=lambda: self._edit_user(uid))
        menu.add_command(label='🗑️  حذف', command=lambda: self._delete_user(uid))
        menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values:
            self._edit_user(int(values[-1]))
