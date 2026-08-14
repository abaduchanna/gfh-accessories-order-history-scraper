"""
Logo Handler - Theme-Safe Transparent Logo Display
Developed by Abad Umair Channa
"""
_LOGO_HANDLER_VERSION = "2.1.0"


# tkinter imported lazily inside methods
import os
from pathlib import Path



def _get_resampling():
    """Compatibility shim for Pillow < 9.1."""
    try:
        from PIL import Image
        return _get_resampling()
    except AttributeError:
        try:
            from PIL import Image
            return Image.ANTIALIAS
        except AttributeError:
            return 1

class LogoHandler:
    """Manages logo display with theme compatibility."""
    
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.logo_widget = None
        self.photo_image = None
    
    def load_logo_from_file(self, logo_path, width=108, height=40):
        """Load and display logo from file (PNG/JPG)."""
        try:
            from PIL import Image, ImageTk
            
            if not os.path.exists(logo_path):
                return False
            
            img = Image.open(logo_path)
            img.thumbnail((width, height), _get_resampling())
            
            self.photo_image = ImageTk.PhotoImage(img)
            self._photo_ref = self.photo_image  # prevent GC
            
            self.logo_widget = tk.Label(
                self.parent,
                image=self.photo_image,
                bg="transparent",
                highlightthickness=0,
                borderwidth=0
            )
            
            return True
        except:
            return False
    
    def create_text_placeholder(self, text="App", color="#090d26", size=12):
        """Create text placeholder when image unavailable."""
        self.logo_widget = tk.Label(
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
        if self.logo_widget:
            self.logo_widget.pack(side=side, padx=padx, pady=pady)
            return True
        return False
    
    def update_theme(self, theme_colors):
        """Logo doesn't change colors - theme changes only affect other widgets."""
        if self.logo_widget:
            # Logo stays same - don't change its colors
            self.parent.configure(bg=theme_colors.get("frame_bg", "#FFFFFF"))


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
