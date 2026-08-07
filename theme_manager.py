"""
Unified Theme Manager with One-Click Toggle
Developed by Abad Umair Channa
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path
from datetime import datetime
import platform

class ThemeManager:
    """Manages Light/Dark/System themes with persistent storage."""
    
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
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "theme_config.json"
        self.current_theme = self._load_preference()
    
    def _get_config_dir(self) -> Path:
        """Get platform-specific config directory."""
        if platform.system() == "Windows":
            base = Path(os.getenv("APPDATA", "~")).expanduser()
            config_dir = base / "3S Verse" / self.app_name
        else:
            base = Path.home() / ".config"
            config_dir = base / "3s-verse" / self.app_name
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _load_preference(self) -> str:
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
    
    def _save_preference(self, theme: str):
        """Save theme preference."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": theme, "updated": datetime.now().isoformat()}, f)
        except Exception:
            pass
    
    def set_theme(self, theme: str):
        """Set theme and save."""
        if theme in self.THEMES:
            self.current_theme = theme
            self._save_preference(theme)
    
    def toggle_theme(self):
        """Toggle between light and dark."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme
    
    def get_colors(self) -> dict:
        """Get current theme colors."""
        return self.THEMES[self.current_theme].copy()
    
    @staticmethod
    def get_copyright_year() -> int:
        """Get current year dynamically."""
        return datetime.now().year
    
    @staticmethod
    def get_copyright_text() -> str:
        """Get formatted copyright text with dynamic year."""
        year = ThemeManager.get_copyright_year()
        return f"© {year} Developed by Abad Umair Channa"


def apply_theme_to_window(root: tk.Tk, theme_manager: ThemeManager):
    """Apply theme colors to window."""
    colors = theme_manager.get_colors()
    root.configure(bg=colors["bg"])
    
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure("TFrame", background=colors["frame_bg"])
    style.configure("TLabel", background=colors["frame_bg"], foreground=colors["fg"])
    style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
    style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
    
    return colors


def create_theme_toggle_button(parent: tk.Widget, theme_manager: ThemeManager, refresh_callback=None) -> tk.Button:
    """Create one-click theme toggle button."""
    colors = theme_manager.get_colors()
    
    def toggle_and_refresh():
        new_theme = theme_manager.toggle_theme()
        if refresh_callback:
            refresh_callback()
    
    btn = tk.Button(
        parent,
        text="☀️ Light" if theme_manager.current_theme == "dark" else "🌙 Dark",
        command=toggle_and_refresh,
        bg=colors["accent"],
        fg="white",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        font=("Arial", 9, "bold"),
        cursor="hand2"
    )
    
    return btn
