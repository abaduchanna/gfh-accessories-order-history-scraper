"""
Logo Handler for Theme-Safe Display
Preserves transparent logos across light/dark theme changes
Developed by Abad Umair Channa
"""

import tkinter as tk
from tkinter import Canvas
import os
from pathlib import Path


class LogoHandler:
    """Manages logo display with theme compatibility."""
    
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.logo_widget = None
        self.logo_path = None
        self.logo_label = None
    
    def load_logo_from_file(self, logo_path, width=108, height=40):
        """Load and display logo from file."""
        try:
            # Import PIL only when needed
            from PIL import Image, ImageTk
            
            if not os.path.exists(logo_path):
                return False
            
            # Load image
            img = Image.open(logo_path)
            
            # Resize maintaining aspect ratio
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(img)
            
            # Create label with transparent background
            self.logo_label = tk.Label(
                self.parent,
                image=self.photo_image,
                bg="transparent",
                highlightthickness=0,
                borderwidth=0
            )
            
            return True
        
        except ImportError:
            # PIL not available, use text placeholder
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
            
            # Decode base64
            image_data = base64.b64decode(base64_data)
            image_stream = io.BytesIO(image_data)
            
            # Open image
            img = Image.open(image_stream)
            
            # Resize
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Convert
            self.photo_image = ImageTk.PhotoImage(img)
            
            # Create label
            self.logo_label = tk.Label(
                self.parent,
                image=self.photo_image,
                bg="transparent",
                highlightthickness=0,
                borderwidth=0
            )
            
            return True
        
        except Exception as e:
            print(f"Error loading logo from base64: {e}")
            return False
    
    def create_text_logo(self, text="3⚡Verse", color="#090d26", size=12):
        """Create text-based logo when image unavailable."""
        self.logo_label = tk.Label(
            self.parent,
            text=text,
            font=("Arial", size, "bold"),
            fg=color,
            bg="transparent",
            highlightthickness=0,
            borderwidth=0
        )
        return True
    
    def pack(self, side=tk.LEFT, padx=10, pady=5):
        """Pack the logo widget."""
        if self.logo_label:
            self.logo_label.pack(side=side, padx=padx, pady=pady)
            return True
        return False
    
    def update_theme(self, theme_colors):
        """Update logo for new theme (logo stays same, frame changes)."""
        if self.logo_label:
            # Don't modify logo colors - keep them consistent
            # Only update parent frame background if needed
            self.parent.configure(bg=theme_colors.get("frame_bg", "#FFFFFF"))
    
    @staticmethod
    def create_image_placeholder(canvas, width=100, height=40, text="Logo"):
        """Create a placeholder logo on canvas."""
        canvas.create_rectangle(
            0, 0, width, height,
            fill="transparent",
            outline="gray",
            width=2
        )
        canvas.create_text(
            width/2, height/2,
            text=text,
            fill="gray",
            font=("Arial", 8)
        )


def add_logo_to_header(header_frame, logo_path=None, text="3⚡Verse"):
    """
    Easy function to add logo to header frame.
    
    Args:
        header_frame: tk.Frame to add logo to
        logo_path: Optional path to logo image file
        text: Text to show if no image
    
    Returns:
        LogoHandler instance
    """
    handler = LogoHandler(header_frame)
    
    if logo_path and os.path.exists(logo_path):
        if handler.load_logo_from_file(logo_path):
            handler.pack()
            return handler
    
    # Fallback to text
    handler.create_text_logo(text)
    handler.pack()
    return handler
