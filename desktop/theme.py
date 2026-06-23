import tkinter as tk
from tkinter import ttk
from desktop.config import load_settings, save_settings, get_theme_colors, THEMES
from desktop.fonts import find_persian_font


class Colors:
    pass


_current_font_family = None
_current_font_size = 10


def load_theme():
    settings = load_settings()
    colors = get_theme_colors(settings.get('theme', 'default'))
    for k, v in colors.items():
        setattr(Colors, k, v)
    global _current_font_family, _current_font_size
    _current_font_family = settings.get('font_family') or find_persian_font()
    _current_font_size = settings.get('font_size', 10)


def get_font(size=None, weight='normal'):
    if size is None:
        size = _current_font_size
    return (_current_font_family, size, weight)


def get_bold_font(size=None):
    return get_font(size, 'bold')


def apply_theme(root):
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('.', font=get_font())
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


load_theme()
