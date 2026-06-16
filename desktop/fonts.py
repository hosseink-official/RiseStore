import os
import platform
import shutil

FONT_CANDIDATES = [
    'Vazirmatn',
    'Tahoma',
    'Noto Naskh Arabic',
    'Noto Sans Arabic',
    'Vazir',
    'IRANSans',
    'DejaVu Sans',
    'FreeFarsi',
    'FarsiWeb',
    'Amiri',
    'sans-serif',
    'TkDefaultFont',
]

PERSIAN_FONT = None


def _install_bundled_fonts():
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    target_dir = os.path.expanduser('~/.local/share/fonts')
    os.makedirs(target_dir, exist_ok=True)

    installed = False
    for fname in os.listdir(font_dir):
        if fname.endswith('.ttf'):
            src = os.path.join(font_dir, fname)
            dst = os.path.join(target_dir, fname)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                installed = True

    if installed:
        import subprocess
        subprocess.run(['fc-cache', '-f'], capture_output=True, timeout=30)


def find_persian_font():
    global PERSIAN_FONT
    if PERSIAN_FONT:
        return PERSIAN_FONT

    _install_bundled_fonts()

    try:
        import tkinter as tk
        from tkinter import font as tkfont
        root = tk.Tk()
        root.withdraw()
        available = set(tkfont.families())
        root.destroy()
    except Exception:
        available = set()

    for font in FONT_CANDIDATES:
        if font in available:
            PERSIAN_FONT = font
            return font

    PERSIAN_FONT = 'TkDefaultFont'
    return PERSIAN_FONT


def get_font(size=10, weight='normal'):
    family = find_persian_font()
    return (family, size, weight)


def get_bold_font(size=10):
    return get_font(size, 'bold')
