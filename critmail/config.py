"""
CritMail - Configuration and Theme Constants
Winamp 3 Blue Aesthetic + High Security Defaults
"""
import os
import sys
from pathlib import Path

APP_NAME = "CritMail"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Ultra-Fast • Secure • Modern Winamp3 Monospace Mail"

# Storage paths
USER_HOME = Path.home()
DATA_DIR = USER_HOME / ".critmail"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "critmail.db"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
KEYSTORE_PATH = DATA_DIR / ".keystore"

# Winamp3 Blue Skin Color Palette (Zero rounded corners, 1px thin crisp borders)
COLORS = {
    "bg_window": "#0c121d",          # Deepest midnight blue
    "bg_panel": "#111a28",           # Main panel background
    "bg_panel_alt": "#0e1522",       # Secondary panel background
    "bg_toolbar": "#142032",         # Sleek toolbar background
    "bg_titlebar": "#162438",        # Winamp3 title bar
    "bg_input": "#090e17",           # Deep dark input field
    "bg_selection": "#004f8c",       # Electric blue selection
    "bg_hover": "#1a2c47",           # Subtle hover state
    "bg_badge": "#12263f",           # Metadata badge
    
    # Borders & Accents (1px crisp borders)
    "border_frame": "#1e3759",       # Outer crisp border
    "border_active": "#00d4ff",      # Active neon cyan border
    "border_subtle": "#162840",      # Subdued divider border
    "border_focus": "#00b4d8",       # Focus highlight
    
    # Text colors
    "text_primary": "#d9e8f5",       # Bright cool white-blue
    "text_secondary": "#7a9ab8",     # Muted slate blue
    "text_accent": "#00e5ff",        # Electric cyan accent
    "text_dim": "#48627e",           # Dimmed / disabled
    
    # Security Badges & Indicators
    "secure_green": "#00f076",       # Verified TLS / clean
    "warning_orange": "#ffb300",     # Untrusted / remote blocked
    "danger_red": "#ff3860",         # Phishing risk / failed TLS
    
    # Winamp 3 Title Bar Controls
    "btn_close_hover": "#e81123",    # Windows/Winamp close red
    "btn_control_hover": "#223d63",  # Title bar button hover
}

# Monospace & Terminal Font Stack (thin, crisp, vintage hacker / classic Linux)
FONT_STACK_MONO = 'Consolas, "Cascadia Code", "JetBrains Mono", "Fira Code", "DejaVu Sans Mono", "Lucida Console", "Liberation Mono", "Terminus", monospace'
FONT_SIZE_BASE = 9
FONT_SIZE_SMALL = 8
FONT_SIZE_TITLE = 9
FONT_SIZE_HEADER = 10

# Security Defaults
SECURITY_SETTINGS = {
    "block_remote_images": True,
    "strip_scripts": True,
    "sanitize_html": True,
    "enforce_tls": True,
    "warn_external_links": True,
    "prefer_plain_text": False,
    "keep_on_server": True,
}
