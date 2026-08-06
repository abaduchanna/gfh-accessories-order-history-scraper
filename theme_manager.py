"""
Unified Theme Manager for Abad Umair Channa Applications
Handles Light/Dark/System mode with persistent storage
Auto-updates copyright year
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path
from datetime import datetime
import platform

class ThemeManager:
    """Manages application themes with persistent user preference."""
    
    # Theme configurations
    THEMES = {
        "light": {
            "bg": "#FFFFFF",
            "fg": "#000000",
            "button_bg": "#F0F0F0",
            "button_fg": "#000000",
            "entry_bg": "#FFFFFF",
            "entry_fg": "#000000",
            "frame_bg": "#F5F5F5",
            "accent": "#090d26",  # BRAND_NAVY
            "accent_alt": "#f0541c"  # BRAND_RED
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
            "accent_alt": "#FF7A45"
        },
        "system": None  # Follows OS preference
    }
    
    def __init__(self, app_name: str):
        """Initialize theme manager with app-specific config directory."""
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
        """Load saved theme preference from config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    saved = data.get("theme", "system")
                    if saved in self.THEMES:
                        return saved
            except Exception:
                pass
        return "system"
    
    def _save_preference(self, theme: str):
        """Save theme preference to config file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": theme, "updated": datetime.now().isoformat()}, f)
        except Exception as e:
            print(f"Warning: Could not save theme preference: {e}")
    
    def set_theme(self, theme: str):
        """Set active theme and save preference."""
        if theme not in self.THEMES:
            raise ValueError(f"Unknown theme: {theme}")
        self.current_theme = theme
        self._save_preference(theme)
    
    def get_colors(self) -> dict:
        """Get current theme colors, respecting system preference."""
        if self.current_theme == "system":
            # Detect system theme (simplified)
            if platform.system() == "Windows":
                is_dark = self._detect_windows_dark_mode()
            else:
                is_dark = False  # Default to light on non-Windows
            active_theme = "dark" if is_dark else "light"
        else:
            active_theme = self.current_theme
        
        return self.THEMES[active_theme].copy()
    
    def _detect_windows_dark_mode(self) -> bool:
        """Detect Windows 10/11 dark mode setting."""
        try:
            import winreg
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
            value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return False
    
    @staticmethod
    def get_copyright_year() -> int:
        """Get current year for dynamic copyright."""
        return datetime.now().year
    
    @staticmethod
    def get_copyright_text() -> str:
        """Get formatted copyright text."""
        year = ThemeManager.get_copyright_year()
        return f"© {year} Developed by Abad Umair Channa"


def apply_theme_to_window(root: tk.Tk, theme_manager: ThemeManager):
    """Apply theme colors to root window and configure styles."""
    colors = theme_manager.get_colors()
    
    # Configure window
    root.configure(bg=colors["bg"])
    
    # Configure ttk styles
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure("TFrame", background=colors["frame_bg"])
    style.configure("TLabel", background=colors["frame_bg"], foreground=colors["fg"])
    style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
    style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
    
    return colors


def create_theme_menu(root: tk.Tk, theme_manager: ThemeManager, refresh_callback=None):
    """Create a theme selector menu."""
    menu = tk.Menu(root, tearoff=0)
    
    for theme_name in ["light", "dark", "system"]:
        menu.add_command(
            label=theme_name.capitalize(),
            command=lambda t=theme_name: (
                theme_manager.set_theme(t),
                refresh_callback() if refresh_callback else None
            )
        )
    
    return menu
