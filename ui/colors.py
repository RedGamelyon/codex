"""
Codex Color Palette
Colors are represented as (r, g, b, a) tuples for raylib.
"""

# Color definitions as tuples (r, g, b, a)
COLORS = {
    "bg_dark": (20, 20, 30, 255),
    "bg_panel": (30, 30, 45, 255),
    "bg_hover": (50, 50, 70, 255),
    "bg_selected": (80, 80, 120, 255),
    "bg_button": (40, 40, 60, 255),
    "border": (70, 70, 100, 255),
    "border_active": (100, 150, 255, 255),
    "text": (230, 230, 240, 255),
    "text_dim": (150, 150, 170, 255),
    "accent": (100, 150, 255, 255),
    "tag": (150, 200, 150, 255),
    "danger": (255, 100, 100, 255),
    "success": (100, 255, 150, 255),
}

# Direct color references for convenience
BG_DARK = COLORS["bg_dark"]
BG_PANEL = COLORS["bg_panel"]
BG_HOVER = COLORS["bg_hover"]
BG_SELECTED = COLORS["bg_selected"]
BG_BUTTON = COLORS["bg_button"]
BORDER = COLORS["border"]
BORDER_ACTIVE = COLORS["border_active"]
TEXT = COLORS["text"]
TEXT_DIM = COLORS["text_dim"]
ACCENT = COLORS["accent"]
TAG = COLORS["tag"]
DANGER = COLORS["danger"]
SUCCESS = COLORS["success"]

# Predefined raylib colors we'll use
RAYWHITE = (245, 245, 245, 255)
