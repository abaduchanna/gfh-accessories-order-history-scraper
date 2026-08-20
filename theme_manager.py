"""
Theme Manager - Standardized for GFH/VidaPay Ecosystem
Developed by Abad Umair Channa | Copyright © {year} | All rights reserved.
"""
import os

_THEME_MANAGER_VERSION = "2.1.0"
import json
from datetime import datetime

# ── Lazy tkinter import ──
# tkinter is imported inside methods that need it, not at module level.
# This prevents ModuleNotFoundError when the module is imported before
# tkinter availability is verified.


class ThemeManager:
    """Manages light/dark themes with protected widget tags."""


    BRAND_NAVY = "#090d26"
    BRAND_RED = "#f0541c"
    BRAND_WHITE = "#ffffff"

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
        }
    }

    _PROTECTED_TAGS = {"header", "header_label", "brand", "logo", "run", "sched", "stop", "footer"}

    def __init__(self, default="dark", app_name="GFH"):
        self.app_name = app_name
        self.CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "gfh-telecom", app_name)
        self.CONFIG_FILE = os.path.join(self.CONFIG_DIR, "theme.json")
        self.current_theme = self._load_theme() or default
        os.makedirs(self.CONFIG_DIR, exist_ok=True)

    def _load_theme(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    return json.load(f).get("theme", "dark")
            except Exception:
                pass
        return None

    def save_theme(self, theme_name):
        self.current_theme = theme_name
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump({"theme": theme_name}, f)
        except Exception:
            pass

    def get_colors(self):
        return self.THEMES.get(self.current_theme, self.THEMES["dark"]).copy()

    def toggle(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.save_theme(self.current_theme)
        return self.current_theme

    def apply_theme_to_window(self, window):
        """Apply theme to a tkinter window."""
        import tkinter as tk
        from tkinter import ttk

        colors = self.get_colors()
        style = ttk.Style(window)
        style.theme_use("clam")

        # Configure ttk styles
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 9))
        style.configure("TCombobox", fieldbackground=colors.get("input", "#ffffff"), background=colors.get("panel_alt", "#eef0f6"), foreground=colors.get("text", "#16213a"))
        style.configure("TButton", background=colors["panel_alt"], foreground=colors["text"], font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground=colors["input"], foreground=colors["text"])
        style.configure("TNotebook", background=colors["bg"])
        style.configure("TNotebook.Tab", background=colors["panel_alt"], foreground=colors["text"], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", colors["panel"])])
        style.configure("Treeview", background=colors["panel"], foreground=colors["text"], fieldbackground=colors["panel"])
        style.configure("Treeview.Heading", background=self.BRAND_NAVY, foreground=self.BRAND_WHITE, font=("Segoe UI", 9, "bold"))
        style.map("Treeview.Heading", background=[("active", self.BRAND_NAVY)], foreground=[("active", self.BRAND_WHITE)])
        style.configure("Horizontal.TProgressbar", background=colors["red"], troughcolor=colors["panel_alt"])
        style.configure("TCheckbutton", background=colors["bg"], foreground=colors["text"])
        style.configure("TRadiobutton", background=colors["bg"], foreground=colors["text"])
        style.configure("TLabelframe", background=colors["bg"], foreground=colors["text"])
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 9, "bold"))

        window.configure(background=colors["bg"])
        self._walk(window, colors)

    def _walk(self, widget, colors):
        """Walk widget tree and apply colors, skipping protected widgets."""
        import tkinter as tk

        for child in widget.winfo_children():
            # Skip ALL protected tags — header, footer, logo, etc.
            tag = getattr(child, "_tag", None)
            if tag in self._PROTECTED_TAGS:
                continue
            tags = set(child.bindtags())
            if tags & self._PROTECTED_TAGS:
                continue

            wtype = child.winfo_class()
            bg = colors["bg"]
            panel = colors.get("panel", colors["bg"])
            panel_alt = colors.get("panel_alt", colors["bg"])
            text_fg = colors["text"]
            input_bg = colors.get("input", panel)

            try:
                if wtype in ("Frame", "Tk", "Toplevel"):
                    child.configure(bg=bg)
                elif wtype in ("Labelframe", "labelframe"):
                    child.configure(bg=panel, fg=text_fg)
                elif wtype == "Label":
                    child.configure(bg=bg, fg=text_fg)
                elif wtype == "Button":
                    child.configure(bg=panel_alt, fg=text_fg,
                                    activebackground=panel,
                                    activeforeground=text_fg)
                elif wtype == "Entry":
                    child.configure(bg=input_bg, fg=text_fg,
                                    insertbackground=text_fg,
                                    disabledbackground=panel_alt)
                elif wtype == "Text":
                    # Also covers ScrolledText (winfo_class returns "Text")
                    child.configure(bg=panel, fg=text_fg,
                                    insertbackground=text_fg,
                                    selectbackground=colors.get("red", "#f0541c"),
                                    selectforeground="#ffffff")
                elif wtype == "Listbox":
                    child.configure(bg=input_bg, fg=text_fg,
                                    selectbackground=colors.get("red", "#f0541c"),
                                    selectforeground="#ffffff")
                elif wtype in ("Canvas", "canvas"):
                    child.configure(bg=bg, highlightbackground=colors.get("border", bg))
                elif wtype == "PanedWindow":
                    child.configure(bg=bg)
                elif wtype == "Checkbutton":
                    child.configure(bg=bg, fg=text_fg,
                                    activebackground=bg,
                                    activeforeground=text_fg,
                                    selectcolor=panel)
                elif wtype == "Radiobutton":
                    child.configure(bg=bg, fg=text_fg,
                                    activebackground=bg,
                                    activeforeground=text_fg,
                                    selectcolor=panel)
                elif wtype == "Scale":
                    child.configure(bg=bg, fg=text_fg,
                                    troughcolor=panel_alt,
                                    activebackground=colors.get("red", "#f0541c"))
                elif wtype == "Spinbox":
                    child.configure(bg=input_bg, fg=text_fg,
                                    insertbackground=text_fg,
                                    buttonbackground=panel_alt)
                elif wtype == "OptionMenu":
                    child.configure(bg=panel_alt, fg=text_fg,
                                    activebackground=panel,
                                    activeforeground=text_fg)
                elif wtype == "Message":
                    child.configure(bg=bg, fg=text_fg)
                elif wtype == "Scrollbar":
                    child.configure(bg=panel_alt, troughcolor=bg,
                                    activebackground=colors.get("red", "#f0541c"))
            except tk.TclError:
                pass

            # Recurse into children regardless of whether this widget matched
            self._walk(child, colors)

    def create_theme_toggle_button(self, parent, callback=None):
        """Create a theme toggle button."""
        import tkinter as tk

        colors = self.get_colors()
        btn = tk.Label(
            parent,
            text="🌙" if self.current_theme == "dark" else "☀️",
            bg=self.BRAND_RED,
            fg=self.BRAND_WHITE,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn.bind("<Button-1>", lambda e: self._on_toggle(btn, callback))
        return btn

    def _on_toggle(self, btn, callback):
        new_theme = self.toggle()
        btn.configure(text="🌙" if new_theme == "dark" else "☀️")
        if callback:
            callback(new_theme)

    @staticmethod
    def get_copyright_year():
        return datetime.now().year

    @staticmethod
    def get_copyright_text():
        return f"Developed by Abad Umair Channa | Copyright © {datetime.now().year} | All rights reserved."


def apply_theme_to_window(window, theme_manager=None):
    """Convenience function."""
    if theme_manager is None:
        theme_manager = ThemeManager()
    theme_manager.apply_theme_to_window(window)


def get_copyright_year():
    return ThemeManager.get_copyright_year()
