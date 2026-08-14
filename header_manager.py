"""
Fixed Header Manager - Proper Theme Support
Header stays navy blue - doesn't change on theme toggle
Developed by Abad Umair Channa
"""
import os

_HEADER_MANAGER_VERSION = "2.1.0"


# tkinter imported lazily inside methods



def _get_resampling():
    """Compatibility shim for Pillow < 9.1 (_get_resampling())."""
    try:
        from PIL import Image
        return Image.Resampling.LANCZOS
    except AttributeError:
        try:
            from PIL import Image
            return Image.ANTIALIAS
        except AttributeError:
            return 1  # LANCZOS constant

class FixedHeaderManager:
    """Manages header with centered title, logo, and theme toggle."""
    
    BRAND_NAVY = "#090d26"
    BRAND_RED = "#f0541c"
    
    def __init__(self, parent, title="App", height=108):
        import tkinter as tk  # lazy import
        self.parent = parent
        self.title = title
        self.height = height
        self.theme_manager = None
        
        # Create header frame - ALWAYS NAVY
        self.header_frame = tk.Frame(
            parent,
            height=height,
            bg=self.BRAND_NAVY
        )
        self.header_frame.pack(fill=tk.X)
        self.header_frame.pack_propagate(False)
        
        # LEFT: Logo
        self.left_frame = tk.Frame(self.header_frame, bg=self.BRAND_NAVY)
        self.left_frame.pack(side=tk.LEFT, padx=15, pady=10)
        
        self.logo_label = tk.Label(
            self.left_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=self.BRAND_RED,
            bg=self.BRAND_NAVY,
            highlightthickness=0,
            borderwidth=0
        )
        self.logo_label.pack()
        
        # CENTER: Title (centered)
        self.center_frame = tk.Frame(self.header_frame, bg=self.BRAND_NAVY)
        self.center_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.title_label = tk.Label(
            self.center_frame,
            text=title,
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg=self.BRAND_NAVY,
            highlightthickness=0,
            borderwidth=0,
            anchor="center"
        )
        self.title_label.pack(expand=True, fill=tk.BOTH)
        
        # RIGHT: Theme toggle + Copyright
        self.right_frame = tk.Frame(self.header_frame, bg=self.BRAND_NAVY)
        self.right_frame.pack(side=tk.RIGHT, padx=15, pady=5)
        
        self.theme_toggle_btn = None
        self.copyright_label = None
    
    def set_logo(self, logo_path=None, text="Logo"):
        """Set the logo in the header."""
        if logo_path and os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                img.thumbnail((120, 45), _get_resampling())
                self.photo = ImageTk.PhotoImage(img)
                self.logo_label.configure(image=self.photo, text="")
                return
            except:
                pass
        
        # Fallback to text
        self.logo_label.configure(text=text)
    
    def add_theme_toggle(self, theme_manager, callback=None):
        """Add theme toggle button to header."""
        self.theme_manager = theme_manager
        
        def toggle_and_callback():
            theme_manager.toggle()
            # Update ONLY the button text, not header colors
            self.update_button_text()
            if callback:
                callback()
        
        colors = theme_manager.get_colors()
        
        self.theme_toggle_btn = tk.Button(
            self.right_frame,
            text="☀️ Light" if theme_manager.current_theme == "dark" else "🌙 Dark",
            command=toggle_and_callback,
            bg=self.BRAND_RED,
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            highlightthickness=0,
            borderwidth=0
        )
        self.theme_toggle_btn.pack(side=tk.TOP, pady=5)
    
    def add_copyright(self, theme_manager):
        """Add copyright text to header."""
        copyright_text = theme_manager.get_copyright_text()
        
        self.copyright_label = tk.Label(
            self.right_frame,
            text=copyright_text,
            font=("Segoe UI", 7),
            fg="white",
            bg=self.BRAND_NAVY,
            highlightthickness=0,
            borderwidth=0
        )
        self.copyright_label.pack(side=tk.BOTTOM, pady=2)
    
    def update_button_text(self):
        """Update toggle button text ONLY - never change header colors."""
        if self.theme_toggle_btn and self.theme_manager:
            new_text = "🌙 Dark" if self.theme_manager.current_theme == "light" else "☀️ Light"
            self.theme_toggle_btn.configure(text=new_text)
        
        if self.copyright_label and self.theme_manager:
            self.copyright_label.configure(
                text=self.theme_manager.get_copyright_text()
            )
    
    def update_for_theme(self, colors):
        """
        Called when theme changes - update ONLY non-header elements.
        Header NEVER changes color.
        """
        # IMPORTANT: Do NOT update header colors
        # Only update the toggle button text
        self.update_button_text()


