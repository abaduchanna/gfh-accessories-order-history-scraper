"""
Unified Theme Manager with One-Click Toggle
Developed by Abad Umair Channa
Uses only Python standard library for maximum PyInstaller compatibility.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path
from datetime import datetime
import platform


class ThemeManager:
    """Manages Light/Dark themes with persistent storage."""

    THEMES = {
        "light": {
            "bg": "#FFFFFF",
            "fg": "#000000",
            "button_bg": "#F0F0F0",
            "button_fg": "#000000",
            "entry_bg": "#FFFFFF",
            "entry_fg": "#000000",
            "frame_bg": "#F5F5F5",
            "accent": "#090d26",
            "accent_alt": "#f0541c",
            "button_hover": "#E0E0E0",
        },
        "dark": {
            "bg": "#1E1E1E",
            "fg": "#FFFFFF",
            "button_bg": "#2D2D2D",
            "button_fg": "#FFFFFF",
            "entry_bg": "#2D2D2D",
            "entry_fg": "#FFFFFF",
            "frame_bg": "#262626",
            "accent": "#4A7BA7",
            "accent_alt": "#FF7A45",
            "button_hover": "#3D3D3D",
        },
    }

    def __init__(self, app_name="App"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "theme_config.json"
        self.current_theme = self._load_preference()

    def _get_config_dir(self):
        """Get platform-specific config directory."""
        if platform.system() == "Windows":
            base = Path(os.getenv("APPDATA", "~")).expanduser()
            config_dir = base / "3S Verse" / self.app_name
        else:
            base = Path.home() / ".config"
            config_dir = base / "3s-verse" / self.app_name

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return config_dir

    def _load_preference(self):
        """Load saved theme preference."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    saved = data.get("theme", "dark")
                    return saved if saved in self.THEMES else "dark"
            except Exception:
                pass
        return "dark"

    def _save_preference(self, theme):
        """Save theme preference."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": theme, "updated": datetime.now().isoformat()}, f)
        except Exception:
            pass

    def set_theme(self, theme):
        """Set theme and save."""
        if theme in self.THEMES:
            self.current_theme = theme
            self._save_preference(theme)

    def toggle_theme(self):
        """Toggle between light and dark."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def get_colors(self):
        """Get current theme colors."""
        return self.THEMES[self.current_theme].copy()

    @staticmethod
    def get_copyright_year():
        """Get current year dynamically."""
        return datetime.now().year

    @staticmethod
    def get_copyright_text():
        """Get formatted copyright text with dynamic year."""
        return f"© {ThemeManager.get_copyright_year()} Developed by Abad Umair Channa"


def get_copyright_year():
    """Module-level current year for dynamic copyright."""
    return datetime.now().year


def get_copyright_text():
    """Module-level formatted copyright text with dynamic year."""
    return f"© {get_copyright_year()} Developed by Abad Umair Channa"


def apply_theme_to_window(root, theme_manager, refresh_callback=None):
    """Apply theme colors to the root window and configure ttk styles.

    Also walks the widget tree and recolors plain tk widgets so the whole
    window reflects the selected light/dark theme. Returns the colors dict.
    """
    colors = theme_manager.get_colors()

    def _apply():
        try:
            root.configure(bg=colors["bg"])
        except Exception:
            pass
        try:
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("TFrame", background=colors["frame_bg"])
            style.configure(
                "TLabel", background=colors["frame_bg"], foreground=colors["fg"]
            )
            style.configure(
                "TButton",
                background=colors["button_bg"],
                foreground=colors["button_fg"],
                bordercolor=colors["button_bg"],
            )
            style.map(
                "TButton",
                background=[("active", colors["button_hover"])],
            )
            style.configure(
                "TEntry",
                fieldbackground=colors["entry_bg"],
                foreground=colors["entry_fg"],
                insertcolor=colors["entry_fg"],
                bordercolor=colors["button_hover"],
                lightcolor=colors["button_hover"],
                darkcolor=colors["button_hover"],
            )
            style.map(
                "TEntry",
                fieldbackground=[("focus", colors["entry_bg"])],
                bordercolor=[("focus", colors["accent"])],
            )
        except Exception:
            pass
        _walk(root, colors)

    def _walk(widget, c):
        tag = getattr(widget, "_tag", None)
        try:
            if tag in ("header", "header_label", "brand"):
                # Keep the brand navy header fixed across themes.
                if isinstance(widget, tk.Label):
                    widget.configure(bg="#090d26", fg="#ffffff")
                else:
                    widget.configure(bg="#090d26")
                return
            if tag == "run":
                widget.configure(bg="#e8212a", fg="#ffffff",
                                 activebackground="#c01820",
                                 activeforeground="#ffffff")
                return
            if isinstance(widget, tk.Button):
                widget.configure(
                    bg=c["button_bg"],
                    fg=c["button_fg"],
                    activebackground=c["button_hover"],
                    activeforeground=c["button_fg"],
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg=c["entry_bg"],
                    fg=c["entry_fg"],
                    insertbackground=c["entry_fg"],
                )
            elif isinstance(widget, tk.Label):
                widget.configure(bg=c["frame_bg"], fg=c["fg"])
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=c["frame_bg"])
            elif isinstance(widget, tk.Text):
                widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                                 insertbackground=c["entry_fg"])
            elif isinstance(widget, tk.Checkbutton):
                widget.configure(bg=c["frame_bg"], fg=c["fg"],
                                 activebackground=c["frame_bg"],
                                 activeforeground=c["fg"],
                                 selectcolor=c["entry_bg"])
            elif isinstance(widget, tk.Radiobutton):
                widget.configure(bg=c["frame_bg"], fg=c["fg"],
                                 activebackground=c["frame_bg"],
                                 activeforeground=c["fg"],
                                 selectcolor=c["entry_bg"])
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=c["entry_bg"], fg=c["entry_fg"])
            elif isinstance(widget, tk.Menu):
                widget.configure(bg=c["entry_bg"], fg=c["entry_fg"])
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
    """Create a one-click theme toggle button.

    Clicking it toggles the persisted theme and re-applies it to the window
    via ``apply_theme_to_window`` when ``parent`` is a Tk/Toplevel root.
    """
    def toggle():
        new_theme = theme_manager.toggle_theme()
        try:
            root = parent.winfo_toplevel()
            apply_theme_to_window(root, theme_manager)
        except Exception:
            pass
        if on_toggle:
            try:
                on_toggle(new_theme)
            except Exception:
                pass

    text = "Switch to Light" if theme_manager.current_theme == "dark" else "Switch to Dark"
    btn = tk.Button(
        parent,
        text=text,
        command=toggle,
        bg=theme_manager.get_colors()["accent"],
        fg="white",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        font=("Arial", 9, "bold"),
        cursor="hand2",
    )
    return btn
