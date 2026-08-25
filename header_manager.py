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

        # Create header frame - ALWAYS NAVY, fixed height matching audit
        self.header_frame = tk.Frame(
            parent,
            height=90,
            bg=self.BRAND_NAVY
        )
        self.header_frame.pack(fill=tk.X)
        self.header_frame.pack_propagate(False)

        # LEFT: Logo
        self.left_frame = tk.Frame(self.header_frame, bg=self.BRAND_NAVY)
        self.left_frame.pack(side=tk.LEFT, padx=(18, 0), pady=9)

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
        self.logo_label._tag = "header"

        # Red vertical divider
        self.divider_frame = tk.Frame(self.header_frame, bg=self.BRAND_RED, width=3)
        self.divider_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(14, 0), pady=12)
        self.divider_frame._tag = "header"

        # RIGHT: Theme toggle — must pack BEFORE center so it anchors to the right
        # edge and the center title can truly center in the remaining middle space.
        self.right_frame = tk.Frame(self.header_frame, bg=self.BRAND_NAVY)
        self.right_frame.pack(side=tk.RIGHT, padx=(0, 18), pady=9)

        self.theme_toggle_btn = None
        self.copyright_label = None

        # CENTER: Title — spans the ENTIRE header (relwidth=1.0, relheight=1.0)
        # so anchor="center" centers text both H and V within the full header.
        # lower() puts it behind logo/divider/theme button so they stay visible.
        self.title_label = tk.Label(
            self.header_frame,
            text=title,
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg=self.BRAND_NAVY,
            highlightthickness=0,
            borderwidth=0,
            anchor="center"
        )
        self.title_label.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)
        self.title_label.lower()

        # Tag ALL header widgets
        self.header_frame._tag = "header"
        self.left_frame._tag   = "header"
        self.right_frame._tag  = "header"
        self.logo_label._tag   = "header"
        self.title_label._tag  = "header"
    
    def set_logo(self, logo_path=None, text="Logo"):
        """Set the logo in the header."""
        if logo_path and os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                if img.mode not in ("RGBA", "LA"):
                    img = img.convert("RGBA")
                img.thumbnail((190, 72), _get_resampling())
                self.photo = ImageTk.PhotoImage(img)
                self.logo_label.configure(image=self.photo, text="")
                return
            except:
                pass
        
        # Fallback to text
        self.logo_label.configure(text=text)
    
    def add_theme_toggle(self, theme_manager, callback=None):
        import tkinter as tk  # lazy import
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
            text="☀️" if theme_manager.current_theme == "dark" else "🌙",
            command=toggle_and_callback,
            bg=self.BRAND_RED,
            fg="white",
            activebackground="#c9401a",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            width=3,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            highlightthickness=0,
            borderwidth=0
        )
        self.theme_toggle_btn.pack(side=tk.TOP, pady=5)
        self.theme_toggle_btn._tag = "header"

    def add_copyright(self, theme_manager):
        """Build a pinned footer bar (dark navy, never theme-changes) with centered copyright text."""
        copyright_text = theme_manager.get_copyright_text()

        # Footer bar pinned to bottom of the PARENT window — not inside the header frame
        self.footer_frame = tk.Frame(
            self.parent,
            bg=self.BRAND_NAVY,
            height=24,
        )
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.footer_frame.pack_propagate(False)
        self.footer_frame._tag = "footer"

        self.copyright_label = tk.Label(
            self.footer_frame,
            text=copyright_text,
            font=("Segoe UI", 8),
            fg="#c7cbe0",
            bg=self.BRAND_NAVY,
            highlightthickness=0,
            borderwidth=0
        )
        self.copyright_label.pack(expand=True, fill="both")
        self.copyright_label._tag = "footer"
    
    def update_button_text(self):
        """Update toggle button text ONLY - never change header colors."""
        if self.theme_toggle_btn and self.theme_manager:
            new_text = "🌙" if self.theme_manager.current_theme == "light" else "☀️"
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


