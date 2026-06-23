import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'risestore')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'settings.json')

THEME_KEYS = [
    'bg', 'card', 'accent', 'accent_hover', 'accent_light',
    'success', 'success_hover', 'success_light',
    'warning', 'warning_light',
    'danger', 'danger_hover', 'danger_light',
    'text_primary', 'text_secondary', 'text_muted',
    'border', 'border_light',
    'primary', 'primary_light',
    'sidebar_text', 'sidebar_text_hover', 'sidebar_active', 'sidebar_active_bg',
    'blue', 'purple',
]

THEME_LABELS = {
    'bg': 'پس‌زمینه اصلی', 'card': 'پس‌زمینه کارت',
    'accent': 'رنگ اصلی', 'accent_hover': 'رنگ اصلی (هاور)', 'accent_light': 'رنگ اصلی (روشن)',
    'success': 'موفقیت', 'success_hover': 'موفقیت (هاور)', 'success_light': 'موفقیت (روشن)',
    'warning': 'هشدار', 'warning_light': 'هشدار (روشن)',
    'danger': 'خطا', 'danger_hover': 'خطا (هاور)', 'danger_light': 'خطا (روشن)',
    'text_primary': 'متن اصلی', 'text_secondary': 'متن فرعی', 'text_muted': 'متن کدر',
    'border': 'حاشیه', 'border_light': 'حاشیه (روشن)',
    'primary': 'رنگ اولیه', 'primary_light': 'رنگ اولیه (روشن)',
    'sidebar_text': 'متن سایدبار', 'sidebar_text_hover': 'متن سایدبار (هاور)',
    'sidebar_active': 'سایدبار فعال', 'sidebar_active_bg': 'پس‌زمینه سایدبار فعال',
    'blue': 'آبی', 'purple': 'بنفش',
}

DEFAULT_SETTINGS = {
    'font_family': None,
    'font_size': 10,
    'theme': 'default',
    'custom_themes': {},
}

THEMES = {
    'default': {
        'bg': '#f1f5f9',
        'card': '#ffffff',
        'accent': '#6366f1',
        'accent_hover': '#4f46e5',
        'accent_light': '#eef2ff',
        'success': '#10b981',
        'success_hover': '#059669',
        'success_light': '#ecfdf5',
        'warning': '#f59e0b',
        'warning_light': '#fffbeb',
        'danger': '#ef4444',
        'danger_hover': '#dc2626',
        'danger_light': '#fef2f2',
        'text_primary': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#94a3b8',
        'border': '#e2e8f0',
        'border_light': '#f1f5f9',
        'primary': '#0f172a',
        'primary_light': '#1e293b',
        'sidebar_text': '#cbd5e1',
        'sidebar_text_hover': '#ffffff',
        'sidebar_active': '#6366f1',
        'sidebar_active_bg': '#1e293b',
        'blue': '#3b82f6',
        'purple': '#a855f7',
    },
    'dark': {
        'bg': '#0f172a',
        'card': '#1e293b',
        'accent': '#818cf8',
        'accent_hover': '#6366f1',
        'accent_light': '#1e1b4b',
        'success': '#34d399',
        'success_hover': '#10b981',
        'success_light': '#064e3b',
        'warning': '#fbbf24',
        'warning_light': '#451a03',
        'danger': '#f87171',
        'danger_hover': '#ef4444',
        'danger_light': '#450a0a',
        'text_primary': '#f1f5f9',
        'text_secondary': '#cbd5e1',
        'text_muted': '#64748b',
        'border': '#334155',
        'border_light': '#1e293b',
        'primary': '#020617',
        'primary_light': '#0f172a',
        'sidebar_text': '#94a3b8',
        'sidebar_text_hover': '#f1f5f9',
        'sidebar_active': '#818cf8',
        'sidebar_active_bg': '#0f172a',
        'blue': '#60a5fa',
        'purple': '#c084fc',
    },
}

_settings = None


def load_settings():
    global _settings
    if _settings is not None:
        return _settings
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH) as f:
            _settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _settings = dict(DEFAULT_SETTINGS)
        save_settings(_settings)
    for k in DEFAULT_SETTINGS:
        _settings.setdefault(k, DEFAULT_SETTINGS[k])
    return _settings


def save_settings(settings):
    global _settings
    _settings = settings
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def get_all_theme_names():
    settings = load_settings()
    builtin = list(THEMES.keys())
    custom = list(settings.get('custom_themes', {}).keys())
    return builtin, custom


def get_theme(theme_name):
    settings = load_settings()
    if theme_name in THEMES:
        return dict(THEMES[theme_name])
    custom = settings.get('custom_themes', {})
    if theme_name in custom:
        return dict(custom[theme_name])
    return dict(THEMES['default'])


def get_theme_colors(theme_name=None):
    if theme_name is None:
        settings = load_settings()
        theme_name = settings.get('theme', 'default')
    return get_theme(theme_name)


def save_custom_theme(name, colors):
    settings = load_settings()
    custom = settings.setdefault('custom_themes', {})
    theme = {}
    for k in THEME_KEYS:
        if k in colors:
            theme[k] = colors[k]
        else:
            theme[k] = THEMES['default'][k]
    custom[name] = theme
    settings['custom_themes'] = custom
    save_settings(settings)


def delete_custom_theme(name):
    settings = load_settings()
    custom = settings.get('custom_themes', {})
    if name in custom:
        del custom[name]
        settings['custom_themes'] = custom
        if settings.get('theme') == name:
            settings['theme'] = 'default'
        save_settings(settings)
