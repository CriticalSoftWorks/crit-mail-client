"""
CritMail Theme - Winamp 3 Blue Skin Stylesheet & Typography
Zero rounded corners, 1px crisp borders, thin monospace Linux/retro hacker fonts.
"""
from critmail.config import COLORS, FONT_STACK_MONO, FONT_SIZE_BASE, FONT_SIZE_SMALL

WINAMP3_BLUE_STYLESHEET = f"""
/* Universal Reset - ZERO ROUNDED CORNERS */
* {{
    font-family: {FONT_STACK_MONO};
    font-size: {FONT_SIZE_BASE}pt;
    color: {COLORS['text_primary']};
    border-radius: 0px !important;
    outline: none;
}}

/* Main Window & Frameless Container */
#MainFramelessContainer {{
    background-color: {COLORS['bg_window']};
    border: 1px solid {COLORS['border_active']};
}}

#TitleBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a2a44, stop:1 #101b2d);
    border-bottom: 1px solid {COLORS['border_subtle']};
    min-height: 24px;
    max-height: 24px;
}}

#TitleBarLabel {{
    color: {COLORS['text_accent']};
    font-weight: bold;
    font-size: 8.5pt;
    letter-spacing: 1px;
    padding-left: 2px;
}}

#TitleBarSub {{
    color: {COLORS['text_secondary']};
    font-size: 8pt;
}}

/* Winamp3 Miniature Titlebar Buttons */
.TitleBarBtn {{
    background: #142236;
    border: 1px solid #1f3757;
    color: {COLORS['text_accent']};
    font-size: 8pt;
    font-weight: bold;
    min-width: 15px;
    max-width: 15px;
    min-height: 13px;
    max-height: 13px;
    margin: 4px 1px;
    padding: 0px;
}}

.TitleBarBtn:hover {{
    background: #1c365c;
    border: 1px solid {COLORS['border_active']};
    color: #ffffff;
}}

#BtnClose:hover {{
    background: #d32f2f;
    border: 1px solid #ff5252;
    color: #ffffff;
}}

/* Full Menu Bar Below Title Bar (Winamp 3 Skin) */
QMenuBar {{
    background-color: #121f33;
    border-bottom: 1px solid #1f3b60;
    color: {COLORS['text_primary']};
    font-size: 8.5pt;
    padding: 2px 4px;
    min-height: 25px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 9px;
    color: {COLORS['text_primary']};
    margin: 0px 1px;
}}

QMenuBar::item:selected {{
    background: {COLORS['bg_selection']};
    color: {COLORS['text_accent']};
    border: 1px solid {COLORS['border_active']};
}}

QMenuBar::item:pressed {{
    background: #003861;
    color: #ffffff;
}}

QMenu {{
    background-color: #0d1624;
    border: 1px solid {COLORS['border_active']};
    padding: 2px;
}}

QMenu::item {{
    padding: 4px 24px 4px 18px;
    color: {COLORS['text_primary']};
    font-size: 8.5pt;
}}

QMenu::item:selected {{
    background-color: {COLORS['bg_selection']};
    color: #ffffff;
}}

QMenu::item:disabled {{
    color: {COLORS['text_dim']};
}}

QMenu::separator {{
    height: 1px;
    background: #1b3250;
    margin: 3px 4px;
}}

/* Winamp3 LCD / LED Readout Box */
#LcdReadout {{
    background-color: #070c14;
    border: 1px solid #162b47;
    color: {COLORS['text_accent']};
    font-size: 8pt;
    padding: 2px 6px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

/* Panels and Groupings */
QFrame, QWidget#CentralWidget {{
    background-color: {COLORS['bg_window']};
}}

QGroupBox {{
    border: 1px solid #1c3454;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    color: {COLORS['text_accent']};
    font-size: 8pt;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 4px;
    color: {COLORS['text_accent']};
}}

#ToolbarFrame {{
    background-color: {COLORS['bg_toolbar']};
    border-bottom: 1px solid {COLORS['border_subtle']};
    padding: 2px 4px;
}}

/* Action PushButtons (Winamp3 cyber aesthetic) */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #192a42, stop:1 #111d2e);
    border: 1px solid #1e385c;
    color: {COLORS['text_primary']};
    padding: 3px 8px;
    min-height: 16px;
    font-size: 8.5pt;
    font-weight: normal;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #223a5e, stop:1 #16273f);
    border: 1px solid {COLORS['border_active']};
    color: {COLORS['text_accent']};
}}

QPushButton:pressed {{
    background: #0d1726;
    border: 1px solid {COLORS['border_active']};
    color: #ffffff;
}}

QPushButton:disabled {{
    background: #0d1420;
    border: 1px solid #142236;
    color: {COLORS['text_dim']};
}}

/* Accent Button (Send / Get Mail / Save) */
QPushButton#AccentBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005691, stop:1 #003861);
    border: 1px solid {COLORS['border_active']};
    color: #ffffff;
    font-weight: bold;
}}

QPushButton#AccentBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #006eb8, stop:1 #004578);
    border: 1px solid #5eead4;
}}

/* Line Edits & Search Boxes */
QLineEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid #1b3352;
    color: {COLORS['text_primary']};
    padding: 3px 6px;
    selection-background-color: {COLORS['bg_selection']};
    selection-color: #ffffff;
    font-size: 8.5pt;
}}

QLineEdit:focus {{
    border: 1px solid {COLORS['border_active']};
    background-color: #0c1421;
}}

/* Tree View (Folder Navigation) */
QTreeWidget, QTreeView {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border_subtle']};
    color: {COLORS['text_primary']};
    font-size: 8.5pt;
    padding: 2px;
}}

QTreeWidget::item {{
    padding: 3px 2px;
    border: none;
}}

QTreeWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_accent']};
}}

QTreeWidget::item:selected {{
    background-color: {COLORS['bg_selection']};
    color: #ffffff;
}}

/* Table View (Message List) */
QTableWidget, QTableView {{
    background-color: {COLORS['bg_panel_alt']};
    border: 1px solid {COLORS['border_subtle']};
    gridline-color: #152438;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['bg_selection']};
    selection-color: #ffffff;
    font-size: 8.5pt;
}}

QTableWidget::item {{
    padding: 3px;
    border: none;
}}

QTableWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['bg_selection']};
    color: #ffffff;
}}

/* Table & Tree Headers */
QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a293f, stop:1 #121c2c);
    color: {COLORS['text_secondary']};
    padding: 3px 6px;
    border-top: none;
    border-left: none;
    border-right: 1px solid #1a2d47;
    border-bottom: 1px solid {COLORS['border_active']};
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}}

/* Splitters (Sleek, thin 1px dividers) */
QSplitter::handle {{
    background-color: #15263d;
}}

QSplitter::handle:hover {{
    background-color: {COLORS['border_active']};
}}

/* Text Editors & Reading Viewers */
QTextEdit, QPlainTextEdit, QTextBrowser {{
    background-color: #090e17;
    border: 1px solid {COLORS['border_subtle']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['bg_selection']};
    selection-color: #ffffff;
    font-size: 9pt;
    line-height: 1.4;
    padding: 8px;
}}

/* Tab Widget (For Help & Settings Dialogs) */
QTabWidget::pane {{
    border: 1px solid #1c3555;
    background: #0c1320;
}}

QTabBar::tab {{
    background: #101b2d;
    border: 1px solid #1c3555;
    color: {COLORS['text_secondary']};
    padding: 4px 12px;
    font-size: 8.5pt;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: #172b47;
    border-bottom: 1px solid {COLORS['border_active']};
    color: {COLORS['text_accent']};
    font-weight: bold;
}}

/* Labels & Badges */
QLabel {{
    color: {COLORS['text_primary']};
    font-size: 8.5pt;
}}

#SecurityShieldBanner {{
    background-color: #091321;
    border: 1px solid #18385e;
    padding: 3px 8px;
}}

#SecurityBannerText {{
    color: {COLORS['text_accent']};
    font-size: 8pt;
    font-weight: bold;
}}

/* Scrollbars (Ultra-thin retro Winamp styling) */
QScrollBar:vertical {{
    background: #0b111c;
    width: 9px;
    margin: 0px;
    border: 1px solid #16263b;
}}

QScrollBar::handle:vertical {{
    background: #1c3555;
    min-height: 18px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['border_active']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: #0b111c;
    height: 9px;
    margin: 0px;
    border: 1px solid #16263b;
}}

QScrollBar::handle:horizontal {{
    background: #1c3555;
    min-width: 18px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['border_active']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Combo Boxes & Check Boxes */
QComboBox {{
    background: #0f1827;
    border: 1px solid #1d3657;
    color: {COLORS['text_primary']};
    padding: 2px 6px;
    font-size: 8.5pt;
}}

QComboBox:hover, QComboBox:focus {{
    border: 1px solid {COLORS['border_active']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 14px;
    border-left: 1px solid #1d3657;
}}

QComboBox QAbstractItemView {{
    background: #0b121e;
    border: 1px solid {COLORS['border_active']};
    selection-background-color: {COLORS['bg_selection']};
    selection-color: #ffffff;
}}

QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 8.5pt;
    spacing: 5px;
}}

QCheckBox::indicator, QTableWidget::indicator {{
    width: 12px;
    height: 12px;
    border: 1px solid #1e385c;
    background: #090e17;
}}

QCheckBox::indicator:hover, QTableWidget::indicator:hover {{
    border: 1px solid {COLORS['border_active']};
}}

QCheckBox::indicator:checked, QTableWidget::indicator:checked {{
    background: {COLORS['border_active']};
    border: 1px solid #ffffff;
}}

/* Dialogs */
QDialog {{
    background-color: {COLORS['bg_window']};
    border: 1px solid {COLORS['border_active']};
}}

/* Status Bar */
QStatusBar {{
    background: #0b111c;
    border-top: 1px solid #16273e;
    color: {COLORS['text_secondary']};
    font-size: 8pt;
    min-height: 18px;
    max-height: 18px;
}}
"""
