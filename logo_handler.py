"""
Logo Handler - Theme-Safe Transparent Logo Display
Developed by Abad Umair Channa
"""
_LOGO_HANDLER_VERSION = "2.1.0"

import os
from pathlib import Path


def _get_resampling():
    """Compatibility shim for Pillow < 9.1."""
    try:
        from PIL import Image
        return Image.Resampling.LANCZOS
    except AttributeError:
        try:
            from PIL import Image
            return Image.ANTIALIAS
        except AttributeError:
            return 1


class LogoHandler:
    """Manages logo display with theme compatibility."""

    def __init__(self, parent_frame):
        import tkinter as tk  # lazy import
        self.parent = parent_frame
        self.logo_widget = None
        self.photo_image = None
        self._photo_ref = None  # prevent GC

    def load_logo_from_file(self, logo_path, width=108, height=40, bg=None):
        """Load and display logo from file (PNG/JPG).

        bg: background color to set on the label immediately, so the
        widget never flashes/shows the default Tk gray or a mismatched
        theme color behind a transparent-PNG logo before it's themed.
        """
        import tkinter as tk  # lazy import
        try:
            from PIL import Image, ImageTk

            if not os.path.exists(logo_path):
                return False

            img = Image.open(logo_path)
            if img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
            img.thumbnail((width, height), _get_resampling())

            self.photo_image = ImageTk.PhotoImage(img)
            self._photo_ref = self.photo_image  # prevent GC
            try:
                self.parent._logo_photo_ref = self.photo_image  # also on parent
            except Exception:
                pass

            label_kwargs = dict(
                image=self.photo_image,
                highlightthickness=0,
                borderwidth=0
            )
            if bg is not None:
                label_kwargs["bg"] = bg

            self.logo_widget = tk.Label(self.parent, **label_kwargs)

            return True
        except Exception:
            return False

    def create_text_placeholder(self, text="App", color="#090d26", size=12, bg=None):
        """Create text placeholder when image unavailable."""
        import tkinter as tk  # lazy import
        label_kwargs = dict(
            text=text,
            font=("Segoe UI", size, "bold"),
            fg=color,
            highlightthickness=0,
            borderwidth=0
        )
        if bg is not None:
            label_kwargs["bg"] = bg
        self.logo_widget = tk.Label(self.parent, **label_kwargs)
        return True

    def pack(self, side=None, padx=10, pady=5, **kwargs):
        """Pack the logo widget. Extra kwargs (e.g. anchor) are forwarded."""
        import tkinter as tk  # lazy import
        if side is None:
            side = tk.LEFT
        if self.logo_widget:
            self.logo_widget.pack(side=side, padx=padx, pady=pady, **kwargs)
            return True
        return False

    def update_theme(self, theme_colors):
        """Logo doesn't change colors - theme changes only affect other widgets."""
        pass


def add_logo_to_header(header_frame, logo_path=None, text_fallback="Logo"):
    """
    Easy function to add logo to header.

    Args:
        header_frame: tk.Frame to add logo to
        logo_path: Optional path to logo image file
        text_fallback: Text to show if no image (app-specific)

    Returns:
        LogoHandler instance
    """
    handler = LogoHandler(header_frame)

    if logo_path and os.path.exists(logo_path):
        if handler.load_logo_from_file(logo_path):
            handler.pack()
            return handler

    # Fallback to text
    handler.create_text_placeholder(text_fallback)
    handler.pack()
    return handler
