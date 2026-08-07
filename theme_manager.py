"""
Unified Theme Manager — matches VidaPay Transfer Bot theme system.
Developed by Abad Umair Channa.

Light/dark themes with the GFH brand palette:
  - Navy (#090d26) and red (#f0541c) stay constant in both themes.
  - Background, panel, text, input, border switch between light and dark.
  - Header/header_label/run tagged widgets are preserved by the walker
    so branding never gets clobbered on toggle.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path
from datetime import datetime
import platform


# Brand constants (match VidaPay_Transfer_Bot.py)
BRAND_NAVY = "#090d26"
BRAND_RED = "#f0541c"
BRAND_WHITE = "#ffffff"

# Tags that mark widgets whose colors must NOT be touched by the theme walker.
_PROTECTED_TAGS = {"header", "header_label", "brand", "logo", "run", "sched", "stop"}


# ── THEMES (matches VidaPay_Transfer_Bot THEMES dict exactly) ──
THEMES = {
    "light": {
        "bg": "#f6f7fb",
        "panel": "#ffffff",
        "panel_alt": "#eef0f6",
        "text": "#16213a",
        "text_dim": "#5b6478",
        "input": "#ffffff",
        "border": "#d5d9e5",
        "navy": "#090d26",
        "red": "#f0541c",
        "log_bg": "#0f1830",
        "log_fg": "#e2e8f0",
    },
    "dark": {
        "bg": "#0b1020",
        "panel": "#141b38",
        "panel_alt": "#1c2447",
        "text": "#e8ecf7",
        "text_dim": "#9aa4c0",
        "input": "#1c2447",
        "border": "#2b3561",
        "navy": "#090d26",
        "red": "#f0541c",
        "log_bg": "#05070f",
        "log_fg": "#cbd5e1",
    },
}


class ThemeManager:
    """Manages Light/Dark themes with persistent storage."""

    def __init__(self, app_name="App"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "theme_config.json"
        self.current_theme = self._load_preference()

    def _get_config_dir(self):
        if platform.system() == "Windows":
            base = Path(os.getenv("APPDATA", "~")).expanduser()
            config_dir = base / "GFH Telecom" / self.app_name
        else:
            base = Path.home() / ".config"
            config_dir = base / "gfh-telecom" / self.app_name
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return config_dir

    def _load_preference(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    saved = data.get("theme", "dark")
                    return saved if saved in THEMES else "dark"
            except Exception:
                pass
        return "dark"

    def _save_preference(self, theme):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": theme, "updated": datetime.now().isoformat()}, f)
        except Exception:
            pass

    def set_theme(self, theme):
        if theme in THEMES:
            self.current_theme = theme
            self._save_preference(theme)

    def toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def get_colors(self):
        return THEMES[self.current_theme].copy()

    @staticmethod
    def get_copyright_year():
        return datetime.now().year

    @staticmethod
    def get_copyright_text():
        return f"\u00a9 {ThemeManager.get_copyright_year()} Developed by Abad Umair Channa"


def get_copyright_year():
    return datetime.now().year


def get_copyright_text():
    return f"\u00a9 {get_copyright_year()} Developed by Abad Umair Channa"


def _widget_has_image(widget):
    """Return True if a tk.Label is currently displaying a PhotoImage."""
    try:
        img = widget.cget("image")
        return bool(img) and str(img) != ""
    except Exception:
        return False


def apply_theme_to_window(root, theme_manager, refresh_callback=None):
    """Apply theme colors to the root window and configure ttk styles.

    Mirrors VidaPay_Transfer_Bot._apply_theme + _style_ttk + _theme_walk:
      - Sets root bg
      - Configures BASE ttk styles (TFrame, TLabel, TButton, TEntry,
        TNotebook, Treeview, TCombobox, Horizontal.TProgressbar) with the
        current theme colors. Custom styles (Header.TFrame, Accent.TButton,
        etc.) are NOT touched — they keep whatever configure_style() set.
      - Walks the widget tree and recolors plain tk widgets. Widgets tagged
        'header'/'header_label'/'brand'/'logo' are set to navy. 'run' tagged
        widgets get red. Labels displaying images are skipped entirely.
    """
    colors = theme_manager.get_colors()

    def _apply():
        try:
            root.configure(bg=colors["bg"])
        except Exception:
            pass

        # ── Configure BASE ttk styles (matches _style_ttk) ──
        try:
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("TFrame", background=colors["bg"])
            style.configure("TLabel", background=colors["bg"], foreground=colors["text"],
                            font=("Segoe UI", 9))
            style.configure("TButton", background=colors["panel_alt"],
                            foreground=colors["text"], bordercolor=colors["border"],
                            padding=[10, 5], font=("Segoe UI", 9))
            style.map("TButton",
                      background=[("active", colors["border"])],
                      foreground=[("active", colors["text"])])
            style.configure("TEntry", fieldbackground=colors["input"],
                            foreground=colors["text"], insertcolor=colors["text"],
                            bordercolor=colors["border"],
                            lightcolor=colors["border"], darkcolor=colors["border"])
            style.map("TEntry",
                      fieldbackground=[("focus", colors["input"])],
                      bordercolor=[("focus", colors["red"])])
            style.configure("TCombobox", fieldbackground=colors["input"],
                            background=colors["panel_alt"], foreground=colors["text"],
                            arrowcolor=colors["text_dim"], bordercolor=colors["border"])
            style.map("TCombobox",
                      fieldbackground=[("readonly", colors["input"])],
                      foreground=[("readonly", colors["text"])],
                      selectbackground=[("readonly", colors["input"])],
                      selectforeground=[("readonly", colors["text"])])
            style.configure("TNotebook", background=colors["bg"], borderwidth=0)
            style.configure("TNotebook.Tab", background=colors["panel_alt"],
                            foreground=colors["text_dim"],
                            font=("Segoe UI", 10, "bold"), padding=[12, 6])
            style.map("TNotebook.Tab",
                      background=[("selected", colors["red"])],
                      foreground=[("selected", "#ffffff")])
            style.configure("Treeview", background=colors["panel"],
                            fieldbackground=colors["panel"], foreground=colors["text"],
                            bordercolor=colors["border"], rowheight=26)
            style.configure("Treeview.Heading", background=colors["navy"],
                            foreground="#ffffff", font=("Segoe UI", 9, "bold"),
                            relief="flat")
            style.map("Treeview",
                      background=[("selected", colors["red"])],
                      foreground=[("selected", "#ffffff")])
            style.configure("Horizontal.TProgressbar", background=colors["red"],
                            troughcolor=colors["panel_alt"], bordercolor=colors["border"],
                            lightcolor=colors["red"], darkcolor=colors["red"])
            style.configure("TLabelframe", background=colors["bg"],
                            bordercolor=colors["border"], relief="solid")
            style.configure("TLabelframe.Label", background=colors["bg"],
                            foreground=colors["text"], font=("Segoe UI", 10, "bold"))
            style.configure("TCheckbutton", background=colors["bg"],
                            foreground=colors["text"])
            style.map("TCheckbutton",
                      background=[("active", colors["bg"])],
                      foreground=[("active", colors["text"])])
            style.configure("TRadiobutton", background=colors["bg"],
                            foreground=colors["text"])
            style.map("TRadiobutton",
                      background=[("active", colors["bg"])],
                      foreground=[("active", colors["text"])])
        except Exception:
            pass

        # ── Walk widget tree and recolor plain tk widgets ──
        _walk(root, colors)

    def _walk(widget, c):
        tag = getattr(widget, "_tag", None)
        try:
            # Protected widgets: header/header_label/brand → navy
            if tag in ("header", "header_label", "brand"):
                if isinstance(widget, tk.Label):
                    widget.configure(bg=c["navy"], fg="#ffffff")
                else:
                    widget.configure(bg=c["navy"])
                # Still recurse into children (they may be themeable)
                for child in widget.winfo_children():
                    _walk(child, c)
                return
            # Run button → red
            if tag == "run":
                widget.configure(bg=c["red"], fg="#ffffff",
                                 activebackground="#d84410",
                                 activeforeground="#ffffff")
                for child in widget.winfo_children():
                    _walk(child, c)
                return
            # Scheduler button → navy
            if tag == "sched":
                widget.configure(bg=c["navy"], fg="#ffffff",
                                 activebackground="#1b2047",
                                 activeforeground="#ffffff")
                for child in widget.winfo_children():
                    _walk(child, c)
                return
            # Stop button → grey
            if tag == "stop":
                widget.configure(bg="#6b7280", fg="#ffffff",
                                 activebackground="#565e6c",
                                 activeforeground="#ffffff")
                for child in widget.winfo_children():
                    _walk(child, c)
                return
            # Logo label (displays an image) → sync bg with parent, don't touch fg
            if tag == "logo" or (isinstance(widget, tk.Label) and _widget_has_image(widget)):
                try:
                    parent_bg = widget.master.cget("bg") if widget.master else c["navy"]
                    widget.configure(bg=parent_bg)
                except Exception:
                    pass
                for child in widget.winfo_children():
                    _walk(child, c)
                return

            # ── Recolor plain tk widgets by type ──
            if isinstance(widget, tk.Button):
                widget.configure(bg=c["panel_alt"], fg=c["text"],
                                 activebackground=c["border"],
                                 activeforeground=c["text"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=c["input"], fg=c["text"],
                                 insertbackground=c["text"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=c["bg"], fg=c["text"])
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=c["bg"])
            elif isinstance(widget, tk.Text):
                widget.configure(bg=c["log_bg"], fg=c["log_fg"],
                                 insertbackground=c["log_fg"])
            elif isinstance(widget, tk.Checkbutton):
                widget.configure(bg=c["bg"], fg=c["text"],
                                 activebackground=c["bg"],
                                 activeforeground=c["text"],
                                 selectcolor=c["input"])
            elif isinstance(widget, tk.Radiobutton):
                widget.configure(bg=c["bg"], fg=c["text"],
                                 activebackground=c["bg"],
                                 activeforeground=c["text"],
                                 selectcolor=c["input"])
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=c["input"], fg=c["text"])
            elif isinstance(widget, tk.Menu):
                widget.configure(bg=c["input"], fg=c["text"])
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                _walk(child, c)
        except Exception:
            pass

    _apply()
    if refresh_callback:
        try:
            refresh_callback(colors)
        except Exception:
            pass
    return colors


def create_theme_toggle_button(parent, theme_manager, on_toggle=None):
    """Create a one-click theme toggle button (ttk.Button with ThemeToggle style).

    Matches VidaPay_Transfer_Bot's toggle: flips light/dark, re-applies to the
    window, and refreshes the button label + style to match the new theme.
    """
    def toggle():
        new_theme = theme_manager.toggle_theme()
        try:
            root = parent.winfo_toplevel()
            apply_theme_to_window(root, theme_manager)
        except Exception:
            pass
        # Refresh button label + style
        try:
            _update_btn()
        except Exception:
            pass
        if on_toggle:
            try:
                on_toggle(new_theme)
            except Exception:
                pass

    def _update_btn():
        c = theme_manager.get_colors()
        next_theme = "dark" if theme_manager.current_theme == "light" else "light"
        btn_text = "Switch to Dark" if next_theme == "dark" else "Switch to Light"
        try:
            btn.config(text=btn_text)
            style = ttk.Style()
            style.configure("ThemeToggle.TButton",
                            background=c["navy"], foreground="#ffffff",
                            bordercolor=c["navy"], focusthickness=0,
                            font=("Segoe UI", 9, "bold"), padding=[10, 5])
            style.map("ThemeToggle.TButton",
                      background=[("active", c["red"])])
            btn.configure(style="ThemeToggle.TButton")
        except Exception:
            pass

    text = "Switch to Light" if theme_manager.current_theme == "dark" else "Switch to Dark"
    btn = ttk.Button(parent, text=text, command=toggle, style="ThemeToggle.TButton")
    # Configure the style immediately so the button looks right on first paint
    try:
        c = theme_manager.get_colors()
        style = ttk.Style()
        style.configure("ThemeToggle.TButton",
                        background=c["navy"], foreground="#ffffff",
                        bordercolor=c["navy"], focusthickness=0,
                        font=("Segoe UI", 9, "bold"), padding=[10, 5])
        style.map("ThemeToggle.TButton",
                  background=[("active", c["red"])])
    except Exception:
        pass
    return btn
