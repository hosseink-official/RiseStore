#!/usr/bin/env python
import os
import sys
import tkinter as tk

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from desktop.db import init
from desktop.app import App


def main():
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    init(db_path)

    from desktop.fonts import find_persian_font
    font = find_persian_font()
    print(f'Using font: {font}')

    root = tk.Tk()
    root.title('RiseStore - سیستم مدیریت فروشگاه')
    root.geometry('1280x800')
    root.minsize(1024, 600)

    try:
        img = tk.PhotoImage(file=os.path.join(BASE_DIR, 'desktop', 'icon.png'))
        root.iconphoto(True, img)
    except Exception:
        pass

    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
