import tkinter as tk
from tkinter import ttk, font as tkfont, colorchooser
from desktop.config import load_settings, save_settings, get_theme, get_all_theme_names, save_custom_theme, delete_custom_theme, THEMES, THEME_KEYS, THEME_LABELS
from desktop.theme import Colors, get_font, get_bold_font, load_theme, apply_theme
from desktop.fonts import FONT_CANDIDATES

BUILTIN_LABELS = {'default': 'روشن', 'dark': 'تیره'}


class AppearanceView:
    def __init__(self, parent, app):
        self.app = app
        self.settings = load_settings()
        self.frame = tk.Frame(parent, bg=Colors.bg)
        self.frame.pack(fill='both', expand=True, padx=28, pady=24)

        canvas = tk.Canvas(self.frame, bg=Colors.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=Colors.bg)

        scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='right', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                canvas.yview_scroll(1, 'units')
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))
        canvas.bind('<Button-4>', _on_mousewheel)
        canvas.bind('<Button-5>', _on_mousewheel)

        frame = scroll_frame

        tk.Label(frame, text='⚙️  تنظیمات ظاهر', font=get_bold_font(20),
                 bg=Colors.bg, fg=Colors.text_primary).pack(anchor='e', pady=(0, 24))

        general_card = tk.Frame(frame, bg=Colors.card, highlightbackground=Colors.border,
                                highlightthickness=1, padx=28, pady=24)
        general_card.pack(fill='x')

        row = tk.Frame(general_card, bg=Colors.card)
        row.pack(fill='x', pady=(0, 16))
        tk.Label(row, text='پوسته:', font=get_font(10), bg=Colors.card,
                 fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        theme_var = tk.StringVar(value=self.settings.get('theme', 'default'))
        self.theme_cb = ttk.Combobox(row, textvariable=theme_var,
                                     state='readonly', font=get_font(10), width=20)
        self.theme_cb.pack(side='right', padx=(10, 0), ipady=2)
        self.theme_label = tk.Label(row, text='', font=get_font(9), bg=Colors.card,
                                    fg=Colors.text_muted)
        self.theme_label.pack(side='right', padx=(6, 0))

        self._refresh_theme_list(theme_var)

        def on_theme_change(*_):
            t = theme_var.get()
            label = BUILTIN_LABELS.get(t, t)
            self.theme_label.config(text=label)
            self._load_colors_for_theme(t)

        theme_var.trace('w', on_theme_change)

        row2 = tk.Frame(general_card, bg=Colors.card)
        row2.pack(fill='x', pady=(0, 16))
        tk.Label(row2, text='فونت:', font=get_font(10), bg=Colors.card,
                 fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        font_var = tk.StringVar(value=self.settings.get('font_family') or '')

        try:
            available = sorted(tkfont.families(self.app.root))
        except Exception:
            try:
                temp_root = tk.Tk()
                temp_root.withdraw()
                available = sorted(tkfont.families())
                temp_root.destroy()
            except Exception:
                available = FONT_CANDIDATES

        persian_candidates = [f for f in available if any(
            kw in f.lower() for kw in ['vazir', 'tahoma', 'noto', 'sans', 'farsi',
                                        'arabic', 'amiri', 'dejavu', 'iransans',
                                        'freefarsi', 'farsiweb']
        )]
        font_choices = ['', *persian_candidates[:20]]
        font_cb = ttk.Combobox(row2, textvariable=font_var,
                               values=font_choices,
                               state='normal', font=get_font(10), width=20)
        font_cb.pack(side='right', padx=(10, 0), ipady=2)

        row3 = tk.Frame(general_card, bg=Colors.card)
        row3.pack(fill='x', pady=(0, 16))
        tk.Label(row3, text='اندازه فونت:', font=get_font(10), bg=Colors.card,
                 fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        size_var = tk.StringVar(value=str(self.settings.get('font_size', 10)))
        size_spin = ttk.Spinbox(row3, from_=8, to=24, textvariable=size_var,
                                font=get_font(10), width=8)
        size_spin.pack(side='right', padx=(10, 0), ipady=2)

        preview_card = tk.Frame(frame, bg=Colors.card,
                                highlightbackground=Colors.border,
                                highlightthickness=1, padx=28, pady=24)
        preview_card.pack(fill='x', pady=(16, 0))
        tk.Label(preview_card, text='پیش‌نمایش:', font=get_bold_font(11),
                 bg=Colors.card, fg=Colors.text_primary).pack(anchor='e', pady=(0, 8))
        self.preview_label = tk.Label(
            preview_card,
            text='این یک متن آزمایشی است — RiseStore سیستم مدیریت فروشگاه',
            font=get_font(), bg=Colors.card, fg=Colors.text_primary
        )
        self.preview_label.pack(anchor='e')

        def update_preview(*_):
            try:
                fs = int(size_var.get())
            except ValueError:
                fs = 10
            ff = font_var.get() or None
            self.preview_label.config(font=(ff, fs))

        font_var.trace('w', update_preview)
        size_var.trace('w', update_preview)

        theme_card = tk.Frame(frame, bg=Colors.card, highlightbackground=Colors.border,
                              highlightthickness=1, padx=28, pady=24)
        theme_card.pack(fill='x', pady=(16, 0))

        theme_header = tk.Frame(theme_card, bg=Colors.card)
        theme_header.pack(fill='x', pady=(0, 12))
        tk.Label(theme_header, text='🎨  ویرایشگر پوسته', font=get_bold_font(13),
                 bg=Colors.card, fg=Colors.text_primary).pack(anchor='e')
        tk.Label(theme_header, text='می‌توانید رنگ‌های پوسته را تغییر دهید و به عنوان پوسته جدید ذخیره کنید',
                 font=get_font(9), bg=Colors.card, fg=Colors.text_muted).pack(anchor='e')

        name_row = tk.Frame(theme_card, bg=Colors.card)
        name_row.pack(fill='x', pady=(0, 12))
        tk.Label(name_row, text='نام پوسته:', font=get_font(10), bg=Colors.card,
                 fg=Colors.text_secondary, width=14, anchor='e').pack(side='right')
        custom_name_var = tk.StringVar()
        name_entry = tk.Entry(name_row, textvariable=custom_name_var, font=get_font(10),
                              bd=1, relief='solid', bg=Colors.card,
                              highlightbackground=Colors.border,
                              highlightcolor=Colors.accent,
                              highlightthickness=1)
        name_entry.pack(side='right', fill='x', expand=True, padx=(10, 0), ipady=3)

        color_canvas = tk.Canvas(theme_card, bg=Colors.card, bd=0, highlightthickness=0,
                                 height=400)
        color_scroll = ttk.Scrollbar(theme_card, orient='vertical', command=color_canvas.yview)
        color_inner = tk.Frame(color_canvas, bg=Colors.card)

        def _on_color_configure(e):
            color_canvas.configure(scrollregion=color_canvas.bbox('all'))
            color_canvas.itemconfigure('colors', width=color_canvas.winfo_width())

        color_inner.bind('<Configure>', _on_color_configure)
        color_canvas.create_window((0, 0), window=color_inner, anchor='nw', tags='colors')
        color_canvas.configure(yscrollcommand=color_scroll.set)

        color_canvas.pack(side='right', fill='both', expand=True)
        color_scroll.pack(side='left', fill='y')

        self.color_rows = {}
        self.color_vars = {}

        for key in THEME_KEYS:
            row_f = tk.Frame(color_inner, bg=Colors.card)
            row_f.pack(fill='x', pady=2)

            label = THEME_LABELS.get(key, key)
            tk.Label(row_f, text=label, font=get_font(9), bg=Colors.card,
                     fg=Colors.text_secondary, width=20, anchor='e').pack(side='right')

            var = tk.StringVar()
            self.color_vars[key] = var
            entry = tk.Entry(row_f, textvariable=var, font=('Courier', 9),
                             width=10, bd=1, relief='solid', bg=Colors.card,
                             highlightbackground=Colors.border,
                             highlightcolor=Colors.accent,
                             highlightthickness=1)
            entry.pack(side='right', padx=(6, 0), ipady=2)

            swatch = tk.Canvas(row_f, width=22, height=22, bd=1, relief='solid',
                               highlightbackground=Colors.border,
                               bg=Colors.card)
            swatch.pack(side='right', padx=(6, 0))

            def make_pick(k, v, s):
                def pick():
                    c = colorchooser.askcolor(title=THEME_LABELS.get(k, k),
                                              initialcolor=v.get() or '#000000',
                                              parent=self.frame.winfo_toplevel())
                    if c and c[1]:
                        v.set(c[1])
                        s.configure(bg=c[1])

                return pick

            def make_update_swatch(v, s):
                def upd(*_):
                    val = v.get().strip()
                    if val.startswith('#') and len(val) in (4, 7):
                        s.configure(bg=val)
                    else:
                        s.configure(bg=Colors.card)

                return upd

            picker_btn = tk.Button(row_f, text='🔍', font=get_font(8),
                                   bg=Colors.card, fg=Colors.text_secondary,
                                   bd=1, relief='solid', cursor='hand2',
                                   command=make_pick(key, var, swatch))
            picker_btn.pack(side='right', padx=(2, 0))

            var.trace('w', make_update_swatch(var, swatch))

            self.color_rows[key] = (row_f, entry, swatch, var)

        btn_frame = tk.Frame(theme_card, bg=Colors.card)
        btn_frame.pack(fill='x', pady=(12, 0))

        def save_custom():
            name = custom_name_var.get().strip()
            if not name:
                return
            colors = {}
            for k in THEME_KEYS:
                colors[k] = self.color_vars[k].get().strip() or THEMES['default'][k]
            save_custom_theme(name, colors)
            self._refresh_theme_list(theme_var)
            theme_var.set(name)

        tk.Button(btn_frame, text='💾  ذخیره به عنوان پوسته جدید', font=get_font(10),
                  bg=Colors.accent, fg='#ffffff', bd=0, cursor='hand2',
                  padx=18, pady=8, activebackground=Colors.accent_hover,
                  command=save_custom).pack(side='right')

        def delete_custom():
            current = theme_var.get()
            builtin, custom = get_all_theme_names()
            if current in custom:
                delete_custom_theme(current)
                self._refresh_theme_list(theme_var)
                theme_var.set('default')

        tk.Button(btn_frame, text='🗑️  حذف پوسته', font=get_font(10),
                  bg=Colors.danger, fg='#ffffff', bd=0, cursor='hand2',
                  padx=18, pady=8, activebackground=Colors.danger_hover,
                  command=delete_custom).pack(side='right', padx=(8, 0))

        apply_btn_frame = tk.Frame(frame, bg=Colors.bg)
        apply_btn_frame.pack(fill='x', pady=(20, 0))

        def apply():
            try:
                fs = int(size_var.get())
            except ValueError:
                fs = 10
            ff = font_var.get() or None
            theme = theme_var.get()
            self.settings['font_size'] = fs
            self.settings['font_family'] = ff
            self.settings['theme'] = theme
            save_settings(self.settings)
            load_theme()
            apply_theme(self.app.root)
            self.app._show_main()

        tk.Button(apply_btn_frame, text='✅  اعمال تغییرات', font=get_font(10),
                  bg=Colors.accent, fg='#ffffff', bd=0, cursor='hand2',
                  padx=24, pady=10, activebackground=Colors.accent_hover,
                  command=apply).pack(side='left')

        on_theme_change()

    def _refresh_theme_list(self, theme_var):
        builtin, custom = get_all_theme_names()
        display = {}
        for t in builtin:
            display[t] = BUILTIN_LABELS.get(t, t)
        for t in custom:
            display[t] = t
        values = list(display.keys())
        self.theme_cb['values'] = values

    def _load_colors_for_theme(self, theme_name):
        colors = get_theme(theme_name)
        for k in THEME_KEYS:
            if k in self.color_vars:
                self.color_vars[k].set(colors.get(k, THEMES['default'][k]))
