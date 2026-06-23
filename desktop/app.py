import tkinter as tk
from tkinter import ttk
from desktop.theme import Colors, get_font, get_bold_font, apply_theme


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.user = None
        apply_theme(root)

        self.container = tk.Frame(root, bg=Colors.bg)
        self.container.pack(fill='both', expand=True)

        self._show_login()

    def _show_login(self):
        for w in self.container.winfo_children():
            w.destroy()
        from desktop.views.login import LoginView
        self.current_view = LoginView(self.container, self)

    def _show_main(self):
        for w in self.container.winfo_children():
            w.destroy()
        self._create_sidebar()
        self._show_dashboard()

    def _create_sidebar(self):
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=0, minsize=200)
        self.container.grid_rowconfigure(0, weight=1)

        self.content_frame = tk.Frame(self.container, bg=Colors.bg)
        self.content_frame.grid(row=0, column=0, sticky='nsew')

        sidebar = tk.Frame(self.container, bg=Colors.primary)
        sidebar.grid(row=0, column=1, sticky='nsew')

        header = tk.Frame(sidebar, bg=Colors.primary)
        header.pack(fill='x')
        tk.Label(header, text='RiseStore', font=get_bold_font(16),
                 bg=Colors.primary, fg='#ffffff').pack(pady=(14, 0))
        tk.Label(header, text='سیستم مدیریت فروشگاه', font=get_font(8),
                 bg=Colors.primary, fg=Colors.sidebar_text).pack()

        sep = tk.Frame(sidebar, bg=Colors.primary_light, height=1)
        sep.pack(fill='x', padx=16, pady=(0, 8))

        nav_items = [
            ('dashboard', 'داشبورد', '📊'),
            ('customers', 'مشتریان', '👥'),
            ('product_types', 'انواع محصول', '📦'),
            ('products', 'محصولات', '🏷️'),
            ('sales', 'فروش‌ها', '🧾'),
            ('reports', 'گزارش‌ها', '📈'),
            ('appearance', 'تنظیمات ظاهر', '🎨'),
        ]

        nav_frame = tk.Frame(sidebar, bg=Colors.primary)
        nav_frame.pack(fill='both', expand=True, padx=10, pady=(4, 0))

        self.nav_buttons = {}
        for key, label, icon in nav_items:
            btn_frame = tk.Frame(nav_frame, bg=Colors.primary)
            btn_frame.pack(fill='x', pady=1)

            indicator = tk.Frame(btn_frame, bg=Colors.primary, width=3)
            indicator.pack(side='right', fill='y')

            btn = tk.Button(btn_frame, text=f'  {icon}  {label}',
                            font=get_font(11),
                            bg=Colors.primary, fg=Colors.sidebar_text,
                            activebackground=Colors.primary_light,
                            activeforeground=Colors.sidebar_text_hover,
                            bd=0, anchor='w', padx=14, pady=6,
                            cursor='hand2',
                            command=lambda k=key: self._navigate(k))
            btn.pack(fill='both', expand=True, side='right')

            btn.indicator = indicator
            self.nav_buttons[key] = (btn, indicator)

        footer = tk.Frame(sidebar, bg=Colors.primary)
        footer.pack(fill='x', side='bottom')

        sep3 = tk.Frame(sidebar, bg=Colors.primary_light, height=1)
        sep3.pack(fill='x', padx=16, side='bottom', before=footer)

        user_frame = tk.Frame(sidebar, bg=Colors.primary)
        user_frame.pack(fill='x', side='bottom', before=sep3)

        user_btn_frame = tk.Frame(user_frame, bg=Colors.primary)
        user_btn_frame.pack(fill='x', pady=1)

        user_indicator = tk.Frame(user_btn_frame, bg=Colors.primary, width=3)
        user_indicator.pack(side='right', fill='y')

        user_btn = tk.Button(user_btn_frame, text='  🔐  کاربران',
                             font=get_font(11),
                             bg=Colors.primary, fg=Colors.sidebar_text,
                             activebackground=Colors.primary_light,
                             activeforeground=Colors.sidebar_text_hover,
                             bd=0, anchor='w', padx=14, pady=6,
                             cursor='hand2',
                             command=lambda: self._navigate('users'))
        user_btn.pack(fill='both', expand=True, side='right')

        user_btn.indicator = user_indicator
        self.nav_buttons['users'] = (user_btn, user_indicator)

        sep2 = tk.Frame(sidebar, bg=Colors.primary_light, height=1)
        sep2.pack(fill='x', padx=16, side='bottom', before=user_frame)

        logout_btn = tk.Button(footer, text='🚪  خروج',
                               font=get_font(11),
                               bg=Colors.primary, fg=Colors.sidebar_text,
                               activebackground=Colors.danger,
                               activeforeground='#ffffff',
                               bd=0, anchor='w', padx=24, pady=8,
                               cursor='hand2',
                               command=self._logout)
        logout_btn.pack(fill='both', expand=True)

    def _navigate(self, key):
        for k, (btn, indicator) in self.nav_buttons.items():
            btn.configure(bg=Colors.primary, fg=Colors.sidebar_text)
            indicator.configure(bg=Colors.primary)

        btn, indicator = self.nav_buttons.get(key)
        if btn:
            btn.configure(bg=Colors.primary_light, fg=Colors.sidebar_text_hover)
            indicator.configure(bg=Colors.accent)

        for w in self.content_frame.winfo_children():
            w.destroy()

        if key == 'dashboard':
            from desktop.views.dashboard import DashboardView
            DashboardView(self.content_frame, self)
        elif key == 'customers':
            from desktop.views.customers import CustomersView
            CustomersView(self.content_frame, self)
        elif key == 'product_types':
            from desktop.views.products import ProductTypesView
            ProductTypesView(self.content_frame, self)
        elif key == 'products':
            from desktop.views.products import ProductsView
            ProductsView(self.content_frame, self)
        elif key == 'sales':
            from desktop.views.sales import SalesListView
            SalesListView(self.content_frame, self)
        elif key == 'users':
            from desktop.views.users import UsersView
            UsersView(self.content_frame, self)
        elif key == 'reports':
            from desktop.views.reports import ReportsView
            ReportsView(self.content_frame, self)
        elif key == 'appearance':
            from desktop.views.appearance import AppearanceView
            AppearanceView(self.content_frame, self)

    def _show_dashboard(self):
        self._navigate('dashboard')

    def _logout(self):
        self.user = None
        for w in self.container.winfo_children():
            w.destroy()
        self._show_login()

    def on_login(self, user):
        self.user = user
        self._show_main()
