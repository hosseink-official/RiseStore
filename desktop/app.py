import tkinter as tk
from tkinter import ttk
from desktop.fonts import get_font, get_bold_font


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.user = None
        self._setup_styles()

        self.container = tk.Frame(root, bg='#f0f2f5')
        self.container.pack(fill='both', expand=True)

        self._show_login()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Sidebar.TFrame', background='#1e293b')
        style.configure('SidebarNav.TButton', font=get_font(11),
                        background='#1e293b', foreground='#cbd5e1',
                        borderwidth=0, padding=(16, 10), anchor='w')
        style.map('SidebarNav.TButton',
                  background=[('active', '#334155'), ('selected', '#2563eb')],
                  foreground=[('active', '#ffffff'), ('selected', '#ffffff')])

        style.configure('Card.TFrame', background='#ffffff', relief='solid',
                        borderwidth=1)
        style.configure('CardTitle.TLabel', font=get_bold_font(12),
                        background='#ffffff', foreground='#1e293b')
        style.configure('StatValue.TLabel', font=get_bold_font(22),
                        background='#ffffff', foreground='#1e293b')
        style.configure('StatLabel.TLabel', font=get_font(9),
                        background='#ffffff', foreground='#64748b')
        style.configure('Primary.TButton', font=get_font(10),
                        background='#2563eb', foreground='#ffffff',
                        padding=(16, 8))
        style.map('Primary.TButton',
                  background=[('active', '#1d4ed8'), ('disabled', '#94a3b8')])
        style.configure('Success.TButton', font=get_font(10),
                        background='#16a34a', foreground='#ffffff',
                        padding=(16, 8))
        style.map('Success.TButton',
                  background=[('active', '#15803d')])
        style.configure('Ghost.TButton', font=get_font(10),
                        background='#f8fafc', foreground='#475569',
                        padding=(12, 6))
        style.map('Ghost.TButton',
                  background=[('active', '#e2e8f0')])
        style.configure('Danger.TButton', font=get_font(10),
                        background='#dc2626', foreground='#ffffff',
                        padding=(8, 4))
        style.map('Danger.TButton',
                  background=[('active', '#b91c1c')])
        style.configure('Heading.TLabel', font=get_bold_font(16),
                        foreground='#1e293b', background='#f0f2f5')
        style.configure('Subheading.TLabel', font=get_font(10),
                        foreground='#64748b', background='#f0f2f5')
        style.configure('TableHeading.TLabel', font=get_bold_font(9),
                        background='#f1f5f9', foreground='#475569',
                        padding=(8, 6), borderwidth=1, relief='solid')
        style.configure('TableData.TLabel', font=get_font(9),
                        background='#ffffff', foreground='#334155',
                        padding=(8, 6), borderwidth=1, relief='solid')

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
        self.sidebar = tk.Frame(self.container, bg='#1e293b', width=220)
        self.sidebar.pack(side='right', fill='y')
        self.sidebar.pack_propagate(False)

        header = tk.Frame(self.sidebar, bg='#1e293b', height=60)
        header.pack(fill='x', pady=(0, 10))
        header.pack_propagate(False)
        tk.Label(header, text='RiseStore', font=get_bold_font(14),
                 bg='#1e293b', fg='#ffffff').pack(pady=12)

        self.nav_buttons = {}
        nav_items = [
            ('dashboard', 'داشبورد', '📊'),
            ('customers', 'مشتریان', '👥'),
            ('product_types', 'انواع محصول', '📦'),
            ('products', 'محصولات', '🏷️'),
            ('sales', 'فروش‌ها', '🧾'),
            ('payments', 'پرداخت‌ها', '💳'),
            ('reports', 'گزارش‌ها', '📈'),
        ]

        nav_frame = tk.Frame(self.sidebar, bg='#1e293b')
        nav_frame.pack(fill='both', expand=True, padx=8)

        for key, label, icon in nav_items:
            btn = tk.Button(nav_frame, text=f'  {icon}  {label}',
                            font=get_font(11),
                            bg='#1e293b', fg='#cbd5e1',
                            activebackground='#334155',
                            activeforeground='#ffffff',
                            bd=0, anchor='w', padx=16, pady=10,
                            cursor='hand2',
                            command=lambda k=key: self._navigate(k))
            btn.pack(fill='x', pady=1)
            self.nav_buttons[key] = btn

        footer = tk.Frame(self.sidebar, bg='#1e293b', height=50)
        footer.pack(fill='x', side='bottom')
        tk.Button(footer, text='🚪  خروج',
                  font=get_font(11),
                  bg='#1e293b', fg='#cbd5e1',
                  activebackground='#dc2626', activeforeground='#ffffff',
                  bd=0, anchor='w', padx=16, pady=10,
                  cursor='hand2',
                  command=self._logout).pack(fill='x', padx=8, pady=8)

        self.content_frame = tk.Frame(self.container, bg='#f0f2f5')
        self.content_frame.pack(side='left', fill='both', expand=True)

    def _navigate(self, key):
        for k, btn in self.nav_buttons.items():
            btn.configure(bg='#1e293b', fg='#cbd5e1')

        btn = self.nav_buttons.get(key)
        if btn:
            btn.configure(bg='#2563eb', fg='#ffffff')

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
        elif key == 'payments':
            from desktop.views.payments import PaymentsView
            PaymentsView(self.content_frame, self)
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
