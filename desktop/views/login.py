import tkinter as tk
from tkinter import ttk, messagebox
from desktop.fonts import get_font, get_bold_font
from desktop.db import auth_user


class LoginView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#f0f2f5')
        self.frame.pack(fill='both', expand=True)

        center = tk.Frame(self.frame, bg='#ffffff', highlightbackground='#e2e8f0',
                          highlightthickness=1)
        center.place(relx=0.5, rely=0.45, anchor='center', width=380)

        tk.Label(center, text='RiseStore', font=get_bold_font(22),
                 bg='#ffffff', fg='#1e293b').pack(pady=(30, 4))
        tk.Label(center, text='سیستم مدیریت فروشگاه', font=get_font(10),
                 bg='#ffffff', fg='#94a3b8').pack(pady=(0, 24))

        form = tk.Frame(center, bg='#ffffff')
        form.pack(padx=32, fill='x')

        tk.Label(form, text='نام کاربری', font=get_font(9),
                 bg='#ffffff', fg='#475569', anchor='w').pack(fill='x', pady=(0, 4))
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(form, textvariable=self.username_var,
                                  font=get_font(11), bd=1, relief='solid',
                                  highlightthickness=1)
        username_entry.pack(fill='x', ipady=6, pady=(0, 12))
        username_entry.focus()

        tk.Label(form, text='رمز عبور', font=get_font(9),
                 bg='#ffffff', fg='#475569', anchor='w').pack(fill='x', pady=(0, 4))
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(form, textvariable=self.password_var,
                                  font=get_font(11), bd=1, relief='solid',
                                  show='*', highlightthickness=1)
        password_entry.pack(fill='x', ipady=6, pady=(0, 20))

        self.error_var = tk.StringVar()
        tk.Label(form, textvariable=self.error_var,
                 font=get_font(9), bg='#ffffff', fg='#dc2626').pack(pady=(0, 8))

        login_btn = tk.Button(form, text='ورود', font=get_bold_font(12),
                               bg='#2563eb', fg='#ffffff',
                               activebackground='#1d4ed8',
                               activeforeground='#ffffff',
                               bd=0, cursor='hand2', pady=10,
                               command=self._login)
        login_btn.pack(fill='x', pady=(0, 30))

        password_entry.bind('<Return>', lambda e: self._login())

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.error_var.set('نام کاربری و رمز عبور را وارد کنید')
            return

        user = auth_user(username, password)
        if user:
            self.app.on_login(user)
        else:
            self.error_var.set('نام کاربری یا رمز عبور اشتباه است')
