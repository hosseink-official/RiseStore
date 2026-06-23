import tkinter as tk
from tkinter import ttk, messagebox
from desktop.theme import Colors, get_font, get_bold_font
from desktop.db import auth_user


class LoginView:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True)

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        outer = tk.Frame(self.frame, bg=Colors.card)
        outer.place(relx=0.5, rely=0.5, anchor='center')

        shadow = tk.Frame(outer, bg=Colors.border)
        shadow.place(x=2, y=2, relwidth=1, relheight=1)

        card = tk.Frame(outer, bg=Colors.card, padx=40, pady=32)
        card.pack()

        tk.Label(card, text='RiseStore', font=get_bold_font(26),
                 bg=Colors.card, fg=Colors.accent).pack(pady=(0, 2))
        tk.Label(card, text='سیستم مدیریت فروشگاه', font=get_font(11),
                 bg=Colors.card, fg=Colors.text_muted).pack(pady=(0, 28))

        form = tk.Frame(card, bg=Colors.card)
        form.pack(fill='x')

        tk.Label(form, text='نام کاربری', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, anchor='w').pack(fill='x', pady=(0, 4))
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(form, textvariable=self.username_var,
                                  font=get_font(11), bd=1, relief='solid',
                                  highlightbackground=Colors.border,
                                  highlightcolor=Colors.accent,
                                  highlightthickness=1)
        username_entry.pack(fill='x', ipady=8, pady=(0, 14))
        username_entry.focus()

        tk.Label(form, text='رمز عبور', font=get_font(9),
                 bg=Colors.card, fg=Colors.text_secondary, anchor='w').pack(fill='x', pady=(0, 4))
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(form, textvariable=self.password_var,
                                  font=get_font(11), bd=1, relief='solid',
                                  highlightbackground=Colors.border,
                                  highlightcolor=Colors.accent,
                                  highlightthickness=1, show='*')
        password_entry.pack(fill='x', ipady=8, pady=(0, 22))

        self.error_var = tk.StringVar()
        self.error_label = tk.Label(form, textvariable=self.error_var,
                                     font=get_font(9), bg=Colors.card,
                                     fg=Colors.danger, anchor='w')
        self.error_label.pack(fill='x', pady=(0, 10))

        login_btn = tk.Button(form, text='ورود به سیستم', font=get_bold_font(12),
                              bg=Colors.accent, fg='#ffffff',
                              activebackground=Colors.accent_hover,
                              activeforeground='#ffffff',
                              bd=0, cursor='hand2', pady=12,
                              command=self._login)
        login_btn.pack(fill='x', pady=(0, 8))

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
