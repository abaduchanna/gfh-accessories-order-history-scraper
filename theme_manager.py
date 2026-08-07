"""
Simplified Theme Manager - Developed by Abad Umair Channa
Uses only Python standard library for maximum compatibility
"""

import tkinter as tk
import json
import os
from pathlib import Path
from datetime import datetime
import platform


class ThemeManager:
    """Minimal theme manager with Light/Dark modes."""
    
    THEMES = {
        "light": {
            "bg": "#FFFFFF",
            "fg": "#000000",
            "button_bg": "#F0F0F0",
            "button_fg": "#000000",
            "accent": "#090d26",
        },
        "dark": {
            "bg": "#1E1E1E",
            "fg": "#FFFFFF",
            "button_bg": "#2D2D2D",
            "button_fg": "#FFFFFF",
            "accent": "#4A7BA7",
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
        except:
            pass
        return config_dir
    
    def _load_preference(self):
        """Load saved theme preference."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("theme", "dark")
            except:
                pass
        return "dark"
    
    def _save_preference(self, theme):
        """Save theme preference."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": theme}, f)
        except:
            pass
    
    def set_theme(self, theme):
        """Set theme."""
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
        """Get current year."""
        return datetime.now().year
    
    @staticmethod
    def get_copyright_text():
        """Get formatted copyright text."""
        year = datetime.now().year
        return f"© {year} Developed by Abad Umair Channa"


def create_theme_toggle_button(parent, theme_manager, on_toggle=None):
    """Create a simple theme toggle button."""
    colors = theme_manager.get_colors()
    
    def toggle():
        new_theme = theme_manager.toggle_theme()
        btn.config(text="🌙 Dark" if new_theme == "light" else "☀️ Light")
        if on_toggle:
            on_toggle(new_theme)
    
    text = "🌙 Dark" if theme_manager.current_theme == "light" else "☀️ Light"
    btn = tk.Button(
        parent,
        text=text,
        command=toggle,
        bg=colors["accent"],
        fg="white",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        font=("Arial", 9, "bold"),
        cursor="hand2"
    )
    
    return btn
