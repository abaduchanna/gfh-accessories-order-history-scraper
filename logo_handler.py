"""
Logo Handler for Theme-Safe Display
Preserves transparent logos across light/dark theme changes
Developed by Abad Umair Channa
"""

import tkinter as tk
from tkinter import Canvas
import os
from pathlib import Path


# Tag used to mark logo labels so ThemeManager._walk() knows to leave them
# alone (keep their bg in sync with the parent header instead of recoloring
# them with the body theme).
LOGO_TAG = "logo"


class LogoHandler:
    """Manages logo display with theme compatibility.

    Tkinter Labels do NOT support a true transparent background — `bg="transparent"`
    is silently ignored and the label falls back to the system default. To get a
    logo that visually blends with the header, we instead read the parent
    frame's current background color and apply it to the label.
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.logo_widget = None
        self.logo_path = None
        self.logo_label = None
        self.photo_image = None

    def _parent_bg(self):
        """Best-effort lookup of the parent frame's current background color."""
        try:
            return self.parent.cget("bg") or "#090d26"
        except Exception:
            return "#090d26"

    def load_logo_from_file(self, logo_path, width=108, height=40):
        """Load and display logo from file."""
        try:
            from PIL import Image, ImageTk

            if not os.path.exists(logo_path):
                return False

            img = Image.open(logo_path)

            # Resize maintaining aspect ratio
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(img)

            # Create label — use parent's bg so the logo visually blends.
            # (tk.Label does not support true transparency; bg="transparent"
            # is a no-op that silently uses the system default.)
            bg = self._parent_bg()
            self.logo_label = tk.Label(
                self.parent,
                image=self.photo_image,
                bg=bg,
                highlightthickness=0,
                borderwidth=0,
            )
            self.logo_label._tag = LOGO_TAG
            return True

        except ImportError:
            return False
        except Exception as e:
            print(f"Error loading logo: {e}")
            return False

    def load_logo_base64(self, base64_data, width=108, height=40):
        """Load logo from base64 encoded data."""
        try:
            from PIL import Image, ImageTk
            import base64
            import io

            image_data = base64.b64decode(base64_data)
            image_stream = io.BytesIO(image_data)
            img = Image.open(image_stream)
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            self.photo_image = ImageTk.PhotoImage(img)

            bg = self._parent_bg()
            self.logo_label = tk.Label(
                self.parent,
                image=self.photo_image,
                bg=bg,
                highlightthickness=0,
                borderwidth=0,
            )
            self.logo_label._tag = LOGO_TAG
            return True

        except Exception as e:
            print(f"Error loading logo from base64: {e}")
            return False

    def create_text_logo(self, text="GFH TELECOM", color="#e8212a", size=12):
        """Create text-based logo when image unavailable."""
        bg = self._parent_bg()
        self.logo_label = tk.Label(
            self.parent,
            text=text,
            font=("Arial", size, "bold"),
            fg=color,
            bg=bg,
            highlightthickness=0,
            borderwidth=0,
        )
        self.logo_label._tag = LOGO_TAG
        return True

    def pack(self, side=tk.LEFT, padx=10, pady=5):
        """Pack the logo widget."""
        if self.logo_label:
            self.logo_label.pack(side=side, padx=padx, pady=pady)
            return True
        return False

    def update_theme(self, theme_colors):
        """Re-sync logo background with parent after a theme switch.

        The logo image itself is never recolored — only the label's bg is
        refreshed to match whatever the parent header now uses.
        """
        if self.logo_label is None:
            return
        try:
            bg = self._parent_bg()
            self.logo_label.configure(bg=bg)
        except Exception:
            pass

    @staticmethod
    def create_image_placeholder(canvas, width=100, height=40, text="Logo"):
        """Create a placeholder logo on canvas."""
        canvas.create_rectangle(
            0, 0, width, height,
            fill="#090d26",
            outline="gray",
            width=2,
        )
        canvas.create_text(
            width / 2, height / 2,
            text=text,
            fill="white",
            font=("Arial", 8),
        )


def add_logo_to_header(header_frame, logo_path=None, text="GFH TELECOM"):
    """Easy function to add logo to header frame.

    Args:
        header_frame: tk.Frame to add logo to
        logo_path: Optional path to logo image file
        text: Text to show if no image (default: "GFH TELECOM")

    Returns:
        LogoHandler instance
    """
    handler = LogoHandler(header_frame)

    if logo_path and os.path.exists(logo_path):
        if handler.load_logo_from_file(logo_path):
            handler.pack()
            return handler

    handler.create_text_logo(text)
    handler.pack()
    return handler
