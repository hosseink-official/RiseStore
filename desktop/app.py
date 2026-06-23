import tkinter as tk
from tkinter import ttk
from desktop.fonts import get_font, get_bold_font


class Colors:
    primary = '#0f172a'
    primary_light = '#1e293b'
    accent = '#6366f1'
    accent_hover = '#4f46e5'
    accent_light = '#eef2ff'
    success = '#10b981'
    success_hover = '#059669'
    success_light = '#ecfdf5'
    warning = '#f59e0b'
    warning_light = '#fffbeb'
    danger = '#ef4444'
    danger_hover = '#dc2626'
    danger_light = '#fef2f2'
    bg = '#f1f5f9'
    card = '#ffffff'
    text_primary = '#0f172a'
    text_secondary = '#475569'
    text_muted = '#94a3b8'
    border = '#e2e8f0'
    border_light = '#f1f5f9'
    sidebar_text = '#cbd5e1'
    sidebar_text_hover = '#ffffff'
    sidebar_active = '#6366f1'
    sidebar_active_bg = '#1e293b'


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.user = None
        self._setup_styles()

        self.container = tk.Frame(root, bg=Colors.bg)
        self.container.pack(fill='both', expand=True)

        self._show_login()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', font=get_font(10))
        style.configure('TFrame', background=Colors.bg)
        style.configure('TLabel', background=Colors.bg, foreground=Colors.text_primary)

        style.configure('Card.TFrame', background=Colors.card, relief='solid', borderwidth=1)
        style.map('Card.TFrame', background=[('active', Colors.card)])

        style.configure('CardTitle.TLabel', font=get_bold_font(13),
                        background=Colors.card, foreground=Colors.text_primary)
        style.configure('StatValue.TLabel', font=get_bold_font(24),
                        background=Colors.card, foreground=Colors.text_primary)
        style.configure('StatLabel.TLabel', font=get_font(9),
                        background=Colors.card, foreground=Colors.text_muted)

        style.configure('Primary.TButton', font=get_font(10),
                        background=Colors.accent, foreground='#ffffff',
                        padding=(18, 9), borderwidth=0)
        style.map('Primary.TButton',
                  background=[('active', Colors.accent_hover), ('disabled', Colors.text_muted)],
                  relief=[('pressed', 'sunken')])

        style.configure('Success.TButton', font=get_font(10),
                        background=Colors.success, foreground='#ffffff',
                        padding=(18, 9), borderwidth=0)
        style.map('Success.TButton',
                  background=[('active', Colors.success_hover)],
                  relief=[('pressed', 'sunken')])

        style.configure('Ghost.TButton', font=get_font(10),
                        background=Colors.card, foreground=Colors.text_secondary,
                        padding=(14, 7), borderwidth=1, relief='solid')
        style.map('Ghost.TButton',
                  background=[('active', Colors.bg)],
                  relief=[('pressed', 'sunken')])

        style.configure('Danger.TButton', font=get_font(10),
                        background=Colors.danger, foreground='#ffffff',
                        padding=(14, 7), borderwidth=0)
        style.map('Danger.TButton',
                  background=[('active', Colors.danger_hover)],
                  relief=[('pressed', 'sunken')])

        style.configure('Heading.TLabel', font=get_bold_font(18),
                        foreground=Colors.text_primary, background=Colors.bg)
        style.configure('Subheading.TLabel', font=get_font(10),
                        foreground=Colors.text_muted, background=Colors.bg)

        style.configure('Sidebar.TFrame', background=Colors.primary)
        style.configure('SidebarTitle.TLabel', font=get_bold_font(15),
                        background=Colors.primary, foreground='#ffffff')
        style.configure('SidebarSubtitle.TLabel', font=get_font(8),
                        background=Colors.primary, foreground=Colors.sidebar_text)

        style.configure('Treeview', font=get_font(9), foreground=Colors.text_primary,
                        background=Colors.card, fieldbackground=Colors.card,
                        borderwidth=0, rowheight=32)
        style.configure('Treeview.Heading', font=get_bold_font(9),
                        background=Colors.border_light, foreground=Colors.text_secondary,
                        borderwidth=1, relief='solid', padding=(6, 5))
        style.map('Treeview',
                  background=[('selected', Colors.accent_light)],
                  foreground=[('selected', Colors.accent)])

        style.configure('TNotebook', background=Colors.bg, borderwidth=0)
        style.configure('TNotebook.Tab', font=get_font(9),
                        padding=(12, 6), background=Colors.border_light,
                        foreground=Colors.text_secondary)
        style.map('TNotebook.Tab',
                  background=[('selected', Colors.card)],
                  foreground=[('selected', Colors.accent)])

        style.configure('TCombobox', font=get_font(9), padding=(4, 2))
        style.map('TCombobox',
                  fieldbackground=[('readonly', Colors.card)],
                  selectbackground=[('readonly', Colors.card)],
                  selectforeground=[('readonly', Colors.text_primary)])

        style.configure('TSpinbox', font=get_font(9), padding=(2, 2))

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

            ('users', 'کاربران', '🔐'),
            ('reports', 'گزارش‌ها', '📈'),
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

        sep2 = tk.Frame(sidebar, bg=Colors.primary_light, height=1)
        sep2.pack(fill='x', padx=16, side='bottom', before=footer)

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
