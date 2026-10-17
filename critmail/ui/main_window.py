"""
CritMail UI - Main Application Window
Winamp 3 Blue Aesthetic • Zero Rounded Corners • 1px Thin Borders • Monospace
Full Navigation Menu Bar (File, Edit, View, Message, Folder, Contacts, Print, Security, Preferences, Help),
Categories Bar, 1-Click Auto-Unsubscribe Banner, Full Right-Click Context Menus, and Complete Printing Suite.
"""
import sys
import shutil
import email
import webbrowser
from email import policy
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QTextBrowser, QLabel, QPushButton,
    QLineEdit, QHeaderView, QFrame, QMessageBox, QApplication, QMenu,
    QComboBox, QFileDialog, QInputDialog, QButtonGroup, QCheckBox
)
from PyQt6.QtGui import QIcon, QFont, QColor, QAction, QKeySequence

from critmail.config import (
    APP_NAME, APP_VERSION, COLORS, FONT_STACK_MONO, FONT_SIZE_BASE
)
from critmail.ui.frameless import FramelessWindow
from critmail.ui.account_dialog import AccountDialog
from critmail.ui.compose_dialog import ComposeDialog
from critmail.ui.contacts_dialog import ContactsDialog, ContactSheetDialog, PreferencesDialog
from critmail.ui.help_about_dialogs import (
    HelpDialog, AboutDialog, RawHeadersDialog, CommsReconDialog, AgentClearanceProDialog
)
from critmail.ui.security_privacy_dialog import SecurityPrivacyDialog
from critmail.ui.url_warning_dialog import LinkGuardDialog
from critmail.ui.print_manager import print_message, print_preview_message, export_message_as_pdf, show_page_setup
from critmail.models.database import (
    get_accounts, get_folders_for_account, get_folder_by_type, create_custom_folder,
    rename_folder, delete_folder, get_messages_in_folder, get_message_full, save_message,
    mark_message_read, mark_all_read_in_folder, toggle_message_flag, set_message_category,
    move_message_to_folder, delete_message, shred_message, archive_message, mark_message_spam,
    empty_trash_for_account, get_unread_count, get_total_count, add_or_update_contact, add_rule, get_setting
)
from critmail.core.pop3_client import Pop3Engine, decode_mime_words
from critmail.core.imap_client import ImapEngine
from critmail.security.sanitizer import (
    sanitize_html, html_to_plain_text, redact_sensitive_text, redact_sensitive_html
)
from critmail.security.unsubscribe import parse_unsubscribe_json, perform_one_click_post_unsubscribe
from critmail.security.crypto import has_classified_cipher, decrypt_classified_message


class MailSyncThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, str)

    def __init__(self, account: dict):
        super().__init__()
        self.account = account

    def run(self):
        try:
            proto = self.account.get("account_type", "IMAP").upper()
            if proto == "IMAP":
                engine = ImapEngine(self.account)
            else:
                engine = Pop3Engine(self.account)

            def _prog(cur, tot, text):
                self.progress.emit(cur, tot, text)

            count = engine.fetch_new_messages(progress_callback=_prog)
            self.finished.emit(count, f"{proto} Sync complete. {count} new message(s) retrieved.")
        except Exception as e:
            self.finished.emit(-1, f"Sync Error: {str(e)}")


class SafeTextBrowser(QTextBrowser):
    """Custom text browser that intercepts link clicks for anti-phishing inspection and provides right-click assistance."""
    def __init__(self, parent_window=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_link_clicked)

    def _on_link_clicked(self, url: QUrl):
        target_str = url.toString()
        if get_setting("link_guard_active", "1") == "1":
            dialog = LinkGuardDialog(target_str, self)
            dialog.exec()
        else:
            webbrowser.open(target_str)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_copy = menu.addAction("📋 Copy Selected Text")
        act_copy.triggered.connect(self.copy)

        act_sel = menu.addAction("Select All (Ctrl+A)")
        act_sel.triggered.connect(self.selectAll)

        menu.addSeparator()

        selected = self.textCursor().selectedText().strip()
        if selected:
            act_search = menu.addAction(f"🔍 Search Web for '{selected[:20]}...'")
            act_search.triggered.connect(lambda: webbrowser.open(f"https://duckduckgo.com/?q={selected}"))

        if self.anchorAt(event.pos()):
            link_url = self.anchorAt(event.pos())
            act_guard = menu.addAction("🛡 Inspect Link with Link Guard...")
            act_guard.triggered.connect(lambda: LinkGuardDialog(link_url, self).exec())

            act_copy_link = menu.addAction("🔗 Copy Link Address")
            act_copy_link.triggered.connect(lambda: QApplication.clipboard().setText(link_url))

        menu.addSeparator()
        if self.parent_window and self.parent_window.current_message_id:
            act_print = menu.addAction("🖨 Print Email...")
            act_print.triggered.connect(self.parent_window._print_current_message)

        menu.exec(event.globalPos())


class CritMailWindow(FramelessWindow):
    """
    CritMail Main Window - Complete standalone email client with Winamp 3 blue + Spy/SIGINT aesthetic.
    """
    def __init__(self):
        super().__init__(title=APP_NAME.upper(), subtitle="SIGINT COMMS // IMAP4 & POP3 SSL/TLS ENGINE")
        self.resize(1160, 760)
        self.setMinimumSize(860, 530)

        self.current_account_id = None
        self.current_folder_id = None
        self.current_folder_type = "inbox"
        self.current_message_id = None
        self.safe_mode_plain_text = False
        self.allow_remote_images = (get_setting("block_remote_images", "1") == "0")
        self.stealth_redact_mode = False
        self.decrypted_cache = {}  # msg_id -> decrypted plaintext
        self.filter_mode = "ALL"
        self.current_category = "ALL"

        self._init_ui()
        self._build_full_menu_bar()
        self._refresh_accounts_and_folders()
        self._setup_auto_sync_timer()

    # -------------------------------------------------------------------------
    # Streamlined, Spy-Grade Classic Navigation Menu Bar (8 Menus)
    # -------------------------------------------------------------------------
    def _build_full_menu_bar(self):
        mb = self.menu_bar

        # 1. FILE MENU (Includes Complete Print & Export Suite)
        file_menu = mb.addMenu("&File")

        act_new = QAction("⚡ &New Transmission...", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._open_compose)
        file_menu.addAction(act_new)

        act_sync = QAction("⟳ &Check Mail / Sync Account", self)
        act_sync.setShortcut(QKeySequence("F5"))
        act_sync.triggered.connect(self._fetch_mail)
        file_menu.addAction(act_sync)

        file_menu.addSeparator()

        act_import = QAction("📂 &Import Message from .eml File...", self)
        act_import.triggered.connect(self._import_eml_file)
        file_menu.addAction(act_import)

        act_export = QAction("💾 &Export Selected Message (.eml / .txt)...", self)
        act_export.setShortcut(QKeySequence("Ctrl+S"))
        act_export.triggered.connect(self._export_selected_message)
        file_menu.addAction(act_export)

        act_save_att = QAction("📎 Save &Attachments to Disk...", self)
        act_save_att.triggered.connect(self._save_attachments_to_disk)
        file_menu.addAction(act_save_att)

        file_menu.addSeparator()

        act_print = QAction("🖨 &Print Message...", self)
        act_print.setShortcut(QKeySequence("Ctrl+P"))
        act_print.triggered.connect(self._print_current_message)
        file_menu.addAction(act_print)

        act_prev = QAction("🔍 Print Pre&view...", self)
        act_prev.triggered.connect(self._print_preview_current)
        file_menu.addAction(act_prev)

        act_pdf = QAction("📄 Export Email as &PDF...", self)
        act_pdf.triggered.connect(self._export_current_pdf)
        file_menu.addAction(act_pdf)

        act_setup = QAction("⚙ Printer Page &Setup...", self)
        act_setup.triggered.connect(lambda: show_page_setup(self))
        file_menu.addAction(act_setup)

        file_menu.addSeparator()

        act_acc = QAction("✉ &Account Settings...", self)
        act_acc.setShortcut(QKeySequence("Ctrl+Shift+A"))
        act_acc.triggered.connect(self._open_accounts)
        file_menu.addAction(act_acc)

        file_menu.addSeparator()

        act_exit = QAction("✕ E&xit CritMail", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 2. EDIT MENU
        edit_menu = mb.addMenu("&Edit")

        act_copy = QAction("📋 &Copy Selected Text", self)
        act_copy.setShortcut(QKeySequence("Ctrl+C"))
        act_copy.triggered.connect(self.browser_body.copy)
        edit_menu.addAction(act_copy)

        act_sel_all = QAction("&Select All in Reader", self)
        act_sel_all.setShortcut(QKeySequence("Ctrl+A"))
        act_sel_all.triggered.connect(self.browser_body.selectAll)
        edit_menu.addAction(act_sel_all)

        edit_menu.addSeparator()

        act_find = QAction("🔍 &Find / Filter in Folder", self)
        act_find.setShortcut(QKeySequence("Ctrl+F"))
        act_find.triggered.connect(lambda: self.txt_search.setFocus())
        edit_menu.addAction(act_find)

        act_clear_find = QAction("✕ Clear Search Filter", self)
        act_clear_find.setShortcut(QKeySequence("Esc"))
        act_clear_find.triggered.connect(lambda: self.txt_search.clear())
        edit_menu.addAction(act_clear_find)

        edit_menu.addSeparator()

        act_prefs = QAction("⚙ &Preferences && Signature...", self)
        act_prefs.setShortcut(QKeySequence("Ctrl+Shift+P"))
        act_prefs.triggered.connect(self._open_preferences)
        edit_menu.addAction(act_prefs)

        # 3. VIEW MENU
        view_menu = mb.addMenu("&View")

        act_safe = QAction("🛡 Toggle &Safe Mode (HTML / Plain Text)", self)
        act_safe.setShortcut(QKeySequence("Ctrl+M"))
        act_safe.triggered.connect(self._toggle_safe_mode)
        view_menu.addAction(act_safe)

        act_img = QAction("🖼 Toggle &Remote Images", self)
        act_img.setShortcut(QKeySequence("Ctrl+I"))
        act_img.triggered.connect(self._toggle_remote_images)
        view_menu.addAction(act_img)

        act_stealth = QAction("🕵 Toggle &Stealth Redaction Mode (Hide Emails/IPs)", self)
        act_stealth.setShortcut(QKeySequence("Ctrl+Shift+X"))
        act_stealth.triggered.connect(self._toggle_stealth_redact)
        view_menu.addAction(act_stealth)

        view_menu.addSeparator()

        act_zoom_in = QAction("🔍+ Zoom &In Reader", self)
        act_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        act_zoom_in.triggered.connect(lambda: self.browser_body.zoomIn(1))
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction("🔍- Zoom &Out Reader", self)
        act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        act_zoom_out.triggered.connect(lambda: self.browser_body.zoomOut(1))
        view_menu.addAction(act_zoom_out)

        view_menu.addSeparator()

        # Categories Submenu
        cat_menu = view_menu.addMenu("🏷 Filter by &Category")
        for cat in ["ALL", "Primary", "Social", "Updates", "Promotions", "Forums"]:
            c_act = cat_menu.addAction(cat)
            c_act.triggered.connect(lambda checked=False, c=cat: self._set_category_filter(c))

        # Flags Submenu
        flg_menu = view_menu.addMenu("🎯 Filter by &Status")
        flg_menu.addAction("All Messages").triggered.connect(lambda: self._set_status_filter("ALL"))
        flg_menu.addAction("Unread Only").triggered.connect(lambda: self._set_status_filter("UNREAD"))
        flg_menu.addAction("★ Starred Only").triggered.connect(lambda: self._set_status_filter("FLAGGED"))
        flg_menu.addAction("📎 With Attachments").triggered.connect(lambda: self._set_status_filter("ATTACHMENTS"))

        view_menu.addSeparator()

        act_toggle_pane = QAction("◧ Toggle &Folder Tree Sidebar", self)
        act_toggle_pane.triggered.connect(self._toggle_folder_sidebar)
        view_menu.addAction(act_toggle_pane)

        act_raw = QAction("🔍 View Raw &Headers && Forensic Source...", self)
        act_raw.setShortcut(QKeySequence("Ctrl+U"))
        act_raw.triggered.connect(self._view_raw_headers)
        view_menu.addAction(act_raw)

        act_refresh = QAction("🔄 Refresh Mailbox", self)
        act_refresh.triggered.connect(self._refresh_accounts_and_folders)
        view_menu.addAction(act_refresh)

        # 4. MESSAGE MENU
        msg_menu = mb.addMenu("&Message")

        act_reply = QAction("↩ &Reply", self)
        act_reply.setShortcut(QKeySequence("Ctrl+R"))
        act_reply.triggered.connect(self._reply_to_current)
        msg_menu.addAction(act_reply)

        act_reply_all = QAction("↩↩ Reply &All", self)
        act_reply_all.setShortcut(QKeySequence("Ctrl+Shift+R"))
        act_reply_all.triggered.connect(self._reply_all_to_current)
        msg_menu.addAction(act_reply_all)

        act_forward = QAction("↪ &Forward", self)
        act_forward.setShortcut(QKeySequence("Ctrl+L"))
        act_forward.triggered.connect(self._forward_current)
        msg_menu.addAction(act_forward)

        act_decrypt = QAction("🔓 &Decrypt TIA Classified Cipher...", self)
        act_decrypt.setShortcut(QKeySequence("Ctrl+D"))
        act_decrypt.triggered.connect(self._decrypt_current_message)
        msg_menu.addAction(act_decrypt)

        msg_menu.addSeparator()

        act_mark_read = QAction("● Mark Selected as &Read", self)
        act_mark_read.setShortcut(QKeySequence("Ctrl+Q"))
        act_mark_read.triggered.connect(lambda: self._set_selected_read_state(True))
        msg_menu.addAction(act_mark_read)

        act_mark_unread = QAction("○ Mark Selected as &Unread", self)
        act_mark_unread.triggered.connect(lambda: self._set_selected_read_state(False))
        msg_menu.addAction(act_mark_unread)

        act_star = QAction("★ Toggle &Star / Flag", self)
        act_star.triggered.connect(self._toggle_flag_current)
        msg_menu.addAction(act_star)

        act_archive = QAction("📦 Move to &Archive", self)
        act_archive.setShortcut(QKeySequence("Ctrl+E"))
        act_archive.triggered.connect(self._archive_selected_message)
        msg_menu.addAction(act_archive)

        act_spam = QAction("⚠ Mark as &Spam / Junk", self)
        act_spam.setShortcut(QKeySequence("Ctrl+J"))
        act_spam.triggered.connect(self._spam_selected_message)
        msg_menu.addAction(act_spam)

        # Set Category Submenu
        set_cat_menu = msg_menu.addMenu("🏷 Assign &Category")
        for cat in ["Primary", "Social", "Updates", "Promotions", "Forums"]:
            set_cat_menu.addAction(cat).triggered.connect(lambda checked=False, c=cat: self._set_current_message_category(c))

        # Move to Folder Submenu
        self.move_menu = msg_menu.addMenu("📁 &Move to Folder")
        self.move_menu.aboutToShow.connect(self._populate_move_menu)

        msg_menu.addSeparator()

        act_unsub = QAction("⚡ 1-Click &Unsubscribe from Mailing List...", self)
        act_unsub.triggered.connect(self._execute_unsubscribe)
        msg_menu.addAction(act_unsub)

        act_add_sender = QAction("📇 Add &Sender to Agent Dossiers", self)
        act_add_sender.triggered.connect(self._add_current_sender_to_contacts)
        msg_menu.addAction(act_add_sender)

        act_block_sender = QAction("🚫 &Block Sender (Add to Blacklist)...", self)
        act_block_sender.triggered.connect(self._block_current_sender)
        msg_menu.addAction(act_block_sender)

        msg_menu.addSeparator()

        act_del = QAction("✕ &Delete Message (Move to Trash)", self)
        act_del.setShortcut(QKeySequence("Delete"))
        act_del.triggered.connect(self._delete_selected_message)
        msg_menu.addAction(act_del)

        act_shred = QAction("🔥 &Burn / Shred Message Permanently...", self)
        act_shred.setShortcut(QKeySequence("Shift+Delete"))
        act_shred.triggered.connect(self._shred_selected_message)
        msg_menu.addAction(act_shred)

        # 5. FOLDER MENU
        folder_menu = mb.addMenu("F&older")

        act_new_folder = QAction("📁 + Create &New Custom Folder...", self)
        act_new_folder.triggered.connect(self._create_new_folder)
        folder_menu.addAction(act_new_folder)

        act_rename_fld = QAction("✏ &Rename Custom Folder...", self)
        act_rename_fld.triggered.connect(self._rename_current_folder)
        folder_menu.addAction(act_rename_fld)

        act_del_fld = QAction("✕ &Delete Custom Folder...", self)
        act_del_fld.triggered.connect(self._delete_current_folder)
        folder_menu.addAction(act_del_fld)

        folder_menu.addSeparator()

        act_fld_read = QAction("✔ Mark &All Messages in Folder as Read", self)
        act_fld_read.triggered.connect(self._mark_all_read)
        folder_menu.addAction(act_fld_read)

        act_empty_tr = QAction("🗑 &Empty Trash Folder", self)
        act_empty_tr.triggered.connect(self._empty_trash)
        folder_menu.addAction(act_empty_tr)

        # 6. SECURITY & OPS MENU (Properly opens matching tab!)
        sec_menu = mb.addMenu("&Security")

        act_sec_center = QAction("🛡 &Security Defense && Privacy Shields...", self)
        act_sec_center.triggered.connect(lambda: self._open_security_dialog(0))
        sec_menu.addAction(act_sec_center)

        act_bl = QAction("🚫 &Blacklist && Spam Blocker Rules...", self)
        act_bl.triggered.connect(lambda: self._open_security_dialog(1))
        sec_menu.addAction(act_bl)

        act_fwd_cfg = QAction("↪ &Mail Forwarding && Auto-Responder...", self)
        act_fwd_cfg.triggered.connect(lambda: self._open_security_dialog(2))
        sec_menu.addAction(act_fwd_cfg)

        act_rules = QAction("📁 &Folder Routing Rules...", self)
        act_rules.triggered.connect(lambda: self._open_security_dialog(3))
        sec_menu.addAction(act_rules)

        sec_menu.addSeparator()

        act_sec_stealth = QAction("🕵 Toggle &Stealth Redaction Mode", self)
        act_sec_stealth.triggered.connect(self._toggle_stealth_redact)
        sec_menu.addAction(act_sec_stealth)

        act_sec_dec = QAction("🔓 &Decrypt Classified Cipher in Message...", self)
        act_sec_dec.triggered.connect(self._decrypt_current_message)
        sec_menu.addAction(act_sec_dec)

        # 7. TOOLS & DOSSIERS MENU (Consolidates Dossiers, Recon, Clearance & Config)
        tools_menu = mb.addMenu("&Tools")

        act_dir = QAction("📇 &Agent Dossiers && Address Book...", self)
        act_dir.setShortcut(QKeySequence("Ctrl+B"))
        act_dir.triggered.connect(lambda: self._open_contacts(filter_blocked=False))
        tools_menu.addAction(act_dir)

        act_new_contact = QAction("+ &New Agent Dossier Sheet...", self)
        act_new_contact.triggered.connect(self._open_new_contact_sheet)
        tools_menu.addAction(act_new_contact)

        act_blocked_list = QAction("🚫 View &Blocked Targets...", self)
        act_blocked_list.triggered.connect(lambda: self._open_contacts(filter_blocked=True))
        tools_menu.addAction(act_blocked_list)

        tools_menu.addSeparator()

        act_recon = QAction("📡 &Comms && DNS Recon Diagnostics...", self)
        act_recon.triggered.connect(self._open_comms_recon)
        tools_menu.addAction(act_recon)

        act_pro = QAction("🎖 &Level-5 Clearance && @theintelligenceagency.net Portal...", self)
        act_pro.triggered.connect(self._open_clearance_pro)
        tools_menu.addAction(act_pro)

        tools_menu.addSeparator()

        act_acc_cfg = QAction("✉ &Account Settings...", self)
        act_acc_cfg.triggered.connect(self._open_accounts)
        tools_menu.addAction(act_acc_cfg)

        act_prefs_t = QAction("⚙ &General Preferences && Signature...", self)
        act_prefs_t.triggered.connect(self._open_preferences)
        tools_menu.addAction(act_prefs_t)

        # 8. HELP MENU
        help_menu = mb.addMenu("&Help")

        act_help = QAction("📖 &CritMail Field Manual && User Guide", self)
        act_help.setShortcut(QKeySequence("F1"))
        act_help.triggered.connect(self._open_help)
        help_menu.addAction(act_help)

        act_help_recon = QAction("📡 &Verify Mail Server && Domain DNS...", self)
        act_help_recon.triggered.connect(self._open_comms_recon)
        help_menu.addAction(act_help_recon)

        act_help_pro = QAction("🎖 &Classified Pro && Callsign Registration...", self)
        act_help_pro.triggered.connect(self._open_clearance_pro)
        help_menu.addAction(act_help_pro)

        help_menu.addSeparator()

        act_about = QAction("ℹ &About CritMail", self)
        act_about.triggered.connect(self._open_about)
        help_menu.addAction(act_about)

    # -------------------------------------------------------------------------
    # Main Client Workspace UI
    # -------------------------------------------------------------------------
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 2, 4, 4)
        main_layout.setSpacing(4)

        # 1. Action Toolbar & Winamp 3 LED/LCD Readout Pane
        top_bar = QFrame()
        top_bar.setObjectName("ToolbarFrame")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(4, 3, 4, 3)
        top_layout.setSpacing(4)

        self.btn_compose = QPushButton("⚡ COMPOSE")
        self.btn_compose.setObjectName("AccentBtn")
        self.btn_compose.setToolTip("Compose a new secure email (Ctrl+N)")
        self.btn_compose.clicked.connect(self._open_compose)
        top_layout.addWidget(self.btn_compose)

        self.btn_get_mail = QPushButton("⟳ GET MAIL")
        self.btn_get_mail.setObjectName("AccentBtn")
        self.btn_get_mail.setToolTip("Synchronize mail from server (F5)")
        self.btn_get_mail.clicked.connect(self._fetch_mail)
        top_layout.addWidget(self.btn_get_mail)

        self.btn_contacts = QPushButton("📇 DOSSIERS")
        self.btn_contacts.setToolTip("Open Agent Dossiers & Contacts Directory (Ctrl+B)")
        self.btn_contacts.clicked.connect(lambda: self._open_contacts(False))
        top_layout.addWidget(self.btn_contacts)

        self.btn_accounts = QPushButton("✉ ACCOUNTS")
        self.btn_accounts.setToolTip("Configure IMAP / POP3 / SMTP Accounts")
        self.btn_accounts.clicked.connect(self._open_accounts)
        top_layout.addWidget(self.btn_accounts)

        self.btn_safe_mode = QPushButton("🛡 SAFE MODE: HTML")
        self.btn_safe_mode.setToolTip("Switch between Sanitized HTML and Plain Text (Ctrl+M)")
        self.btn_safe_mode.clicked.connect(self._toggle_safe_mode)
        top_layout.addWidget(self.btn_safe_mode)

        self.btn_stealth = QPushButton("🕵 STEALTH: OFF")
        self.btn_stealth.setToolTip("Redact emails, IPs, and phone numbers on screen (Ctrl+Shift+X)")
        self.btn_stealth.clicked.connect(self._toggle_stealth_redact)
        top_layout.addWidget(self.btn_stealth)

        self.btn_security = QPushButton("🔒 SECURITY")
        self.btn_security.setToolTip("Security, Blacklist & Mail Forwarding Settings")
        self.btn_security.clicked.connect(lambda: self._open_security_dialog(0))
        top_layout.addWidget(self.btn_security)

        self.btn_recon = QPushButton("📡 RECON")
        self.btn_recon.setToolTip("Live DNS (MX/SPF) & Mail Server TLS Diagnostics")
        self.btn_recon.clicked.connect(self._open_comms_recon)
        top_layout.addWidget(self.btn_recon)

        self.btn_pro = QPushButton("🎖 LEVEL-5 PRO")
        self.btn_pro.setToolTip("Claim @theintelligenceagency.net Callsign & Classified Pro Features")
        self.btn_pro.setStyleSheet("color: #00f076; border: 1px solid #00f076; font-weight: bold;")
        self.btn_pro.clicked.connect(self._open_clearance_pro)
        top_layout.addWidget(self.btn_pro)

        self.btn_delete = QPushButton("✕ DELETE")
        self.btn_delete.setToolTip("Move selected message to Trash / Delete (Del)")
        self.btn_delete.clicked.connect(self._delete_selected_message)
        top_layout.addWidget(self.btn_delete)

        top_layout.addStretch()

        # Winamp 3 LED/LCD Readout Display
        self.lcd_status = QLabel("DEFCON 5 // TLS 1.3 ACTIVE • SIGINT IDLE")
        self.lcd_status.setObjectName("LcdReadout")
        top_layout.addWidget(self.lcd_status)

        main_layout.addWidget(top_bar)

        # 2. Category Selector Bar (Primary, Social, Updates, Promotions, Forums)
        cat_bar = QFrame()
        cat_bar.setStyleSheet("background: #090e17; border-bottom: 1px solid #14243b; padding: 1px 4px;")
        cat_layout = QHBoxLayout(cat_bar)
        cat_layout.setContentsMargins(4, 2, 4, 2)
        cat_layout.setSpacing(4)

        lbl_cat = QLabel("CHANNEL:")
        lbl_cat.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 7.5pt; font-weight: bold;")
        cat_layout.addWidget(lbl_cat)

        self.cat_group = QButtonGroup(self)
        self.cat_btns = {}
        for cat_name in ["ALL", "Primary", "Social", "Updates", "Promotions", "Forums"]:
            btn = QPushButton(f"[{cat_name.upper()}]")
            btn.setCheckable(True)
            btn.setStyleSheet("font-size: 7.5pt; padding: 2px 7px; min-height: 14px;")
            if cat_name == "ALL":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked=False, c=cat_name: self._set_category_filter(c))
            self.cat_group.addButton(btn)
            self.cat_btns[cat_name] = btn
            cat_layout.addWidget(btn)

        cat_layout.addStretch()

        lbl_clearance = QLabel("CLEARANCE: FIELD AGENT // ENCRYPTION: DPAPI+AES256")
        lbl_clearance.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 7.5pt;")
        cat_layout.addWidget(lbl_clearance)

        main_layout.addWidget(cat_bar)

        # 3. Main 3-Pane Splitter (Folders | Messages List | Reader Pane)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(2)

        # Left Pane: Account / Folder Tree + Quick Actions
        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(3)

        self.tree_folders = QTreeWidget()
        self.tree_folders.setHeaderLabel("ACCOUNTS & CHANNELS")
        self.tree_folders.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_folders.customContextMenuRequested.connect(self._show_folder_context_menu)
        self.tree_folders.itemClicked.connect(self._on_folder_selected)
        left_layout.addWidget(self.tree_folders, 1)

        folder_btn_row = QHBoxLayout()
        folder_btn_row.setSpacing(3)
        btn_new_fld = QPushButton("+ Folder")
        btn_new_fld.setStyleSheet("font-size: 7.5pt; padding: 2px 5px;")
        btn_new_fld.clicked.connect(self._create_new_folder)
        folder_btn_row.addWidget(btn_new_fld)

        btn_empty_tr = QPushButton("Empty Trash")
        btn_empty_tr.setStyleSheet("font-size: 7.5pt; padding: 2px 5px;")
        btn_empty_tr.clicked.connect(self._empty_trash)
        folder_btn_row.addWidget(btn_empty_tr)
        left_layout.addLayout(folder_btn_row)

        self.left_widget.setFixedWidth(245)
        self.main_splitter.addWidget(self.left_widget)

        # Right Vertical Splitter (Message Table on top, Message Reader on bottom)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setHandleWidth(2)

        # Right Top: Search bar, Filter buttons & Mail List Table
        mail_list_widget = QWidget()
        mail_list_layout = QVBoxLayout(mail_list_widget)
        mail_list_layout.setContentsMargins(0, 0, 0, 0)
        mail_list_layout.setSpacing(3)

        # Search, Select-All Checkbox & Filter Bar
        search_box = QHBoxLayout()
        search_box.setSpacing(6)

        self.chk_select_all = QCheckBox("☑ All")
        self.chk_select_all.setToolTip("Check / Uncheck all messages in current view")
        self.chk_select_all.setStyleSheet(f"color: {COLORS['text_accent']}; font-size: 8pt; font-weight: bold;")
        self.chk_select_all.toggled.connect(self._on_select_all_toggled)
        search_box.addWidget(self.chk_select_all)

        lbl_search = QLabel("FILTER:")
        lbl_search.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt; font-weight: bold;")
        search_box.addWidget(lbl_search)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search sender, subject, recipient, content... (Ctrl+F)")
        self.txt_search.textChanged.connect(self._on_search_changed)
        search_box.addWidget(self.txt_search, 1)

        self.combo_filter = QComboBox()
        self.combo_filter.addItem("All Messages", "ALL")
        self.combo_filter.addItem("Unread Only", "UNREAD")
        self.combo_filter.addItem("★ Starred / Flagged", "FLAGGED")
        self.combo_filter.addItem("📎 With Attachments", "ATTACHMENTS")
        self.combo_filter.currentIndexChanged.connect(self._on_filter_mode_changed)
        search_box.addWidget(self.combo_filter)

        mail_list_layout.addLayout(search_box)

        # Dynamic Bulk Action Bar (Appears when 1+ checkboxes are checked or 2+ rows selected)
        self.bulk_action_bar = QFrame()
        self.bulk_action_bar.setStyleSheet(
            "background: #0d2138; border: 1px solid #00e5ff; padding: 2px 6px;"
        )
        self.bulk_action_bar.setVisible(False)
        bulk_layout = QHBoxLayout(self.bulk_action_bar)
        bulk_layout.setContentsMargins(4, 2, 4, 2)
        bulk_layout.setSpacing(4)

        self.lbl_bulk_count = QLabel("☑ 0 SELECTED")
        self.lbl_bulk_count.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 8pt;")
        bulk_layout.addWidget(self.lbl_bulk_count)

        bulk_layout.addStretch()

        btn_bulk_read = QPushButton("✔ Mark Read")
        btn_bulk_read.setFixedHeight(19)
        btn_bulk_read.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_read.clicked.connect(lambda: self._set_selected_read_state(True))
        bulk_layout.addWidget(btn_bulk_read)

        btn_bulk_unread = QPushButton("● Mark Unread")
        btn_bulk_unread.setFixedHeight(19)
        btn_bulk_unread.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_unread.clicked.connect(lambda: self._set_selected_read_state(False))
        bulk_layout.addWidget(btn_bulk_unread)

        btn_bulk_arch = QPushButton("📦 Archive")
        btn_bulk_arch.setFixedHeight(19)
        btn_bulk_arch.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_arch.clicked.connect(self._archive_selected_message)
        bulk_layout.addWidget(btn_bulk_arch)

        btn_bulk_spam = QPushButton("⚠ Spam")
        btn_bulk_spam.setFixedHeight(19)
        btn_bulk_spam.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_spam.clicked.connect(self._spam_selected_message)
        bulk_layout.addWidget(btn_bulk_spam)

        self.btn_bulk_move = QPushButton("📁 Move To ▾")
        self.btn_bulk_move.setFixedHeight(19)
        self.btn_bulk_move.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        self.bulk_move_menu = QMenu(self)
        self.bulk_move_menu.aboutToShow.connect(self._populate_bulk_move_menu)
        self.btn_bulk_move.setMenu(self.bulk_move_menu)
        bulk_layout.addWidget(self.btn_bulk_move)

        btn_bulk_del = QPushButton("✕ Delete")
        btn_bulk_del.setFixedHeight(19)
        btn_bulk_del.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_del.clicked.connect(self._delete_selected_message)
        bulk_layout.addWidget(btn_bulk_del)

        btn_bulk_burn = QPushButton("🔥 Burn")
        btn_bulk_burn.setFixedHeight(19)
        btn_bulk_burn.setStyleSheet("font-size: 7.5pt; padding: 1px 6px; color: #ff3860;")
        btn_bulk_burn.clicked.connect(self._shred_selected_message)
        bulk_layout.addWidget(btn_bulk_burn)

        btn_bulk_clear = QPushButton("Clear ☑")
        btn_bulk_clear.setFixedHeight(19)
        btn_bulk_clear.setStyleSheet("font-size: 7.5pt; padding: 1px 6px;")
        btn_bulk_clear.clicked.connect(lambda: self._set_all_checkboxes(False))
        bulk_layout.addWidget(btn_bulk_clear)

        mail_list_layout.addWidget(self.bulk_action_bar)

        # Messages Table (With per-row Checkboxes & Extended Multi-Selection)
        self.table_messages = QTableWidget()
        self.table_messages.setColumnCount(6)
        self.table_messages.setHorizontalHeaderLabels(["☑ / FLAGS", "FROM", "SUBJECT", "CATEGORY", "DATE", "SIZE"])
        self.table_messages.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_messages.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table_messages.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_messages.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_messages.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table_messages.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_messages.setColumnWidth(1, 195)
        self.table_messages.setColumnWidth(4, 140)
        self.table_messages.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_messages.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table_messages.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_messages.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_messages.customContextMenuRequested.connect(self._show_message_context_menu)
        self.table_messages.itemSelectionChanged.connect(self._on_message_selected)
        self.table_messages.itemChanged.connect(self._on_message_item_changed)
        self.table_messages.itemDoubleClicked.connect(self._on_message_double_clicked)
        mail_list_layout.addWidget(self.table_messages)

        self.right_splitter.addWidget(mail_list_widget)

        # Right Bottom: Message Reader Pane
        reader_widget = QWidget()
        reader_layout = QVBoxLayout(reader_widget)
        reader_layout.setContentsMargins(0, 0, 0, 0)
        reader_layout.setSpacing(3)

        # 1-Click Auto-Unsubscribe Banner (Google-Style)
        self.unsub_banner = QFrame()
        self.unsub_banner.setStyleSheet("background: #0f253d; border: 1px solid #00e5ff; padding: 2px 6px;")
        self.unsub_banner.setVisible(False)
        unsub_layout = QHBoxLayout(self.unsub_banner)
        unsub_layout.setContentsMargins(4, 2, 4, 2)
        unsub_layout.setSpacing(6)

        self.lbl_unsub_text = QLabel("⚡ MAILING LIST DETECTED // Sender provided an automated unsubscribe option.")
        self.lbl_unsub_text.setStyleSheet(f"color: {COLORS['text_accent']}; font-size: 8pt; font-weight: bold;")
        unsub_layout.addWidget(self.lbl_unsub_text, 1)

        self.btn_unsub_action = QPushButton("⚡ 1-Click Unsubscribe")
        self.btn_unsub_action.setObjectName("AccentBtn")
        self.btn_unsub_action.setFixedHeight(20)
        self.btn_unsub_action.setStyleSheet("font-size: 8pt; padding: 1px 8px;")
        self.btn_unsub_action.clicked.connect(self._execute_unsubscribe)
        unsub_layout.addWidget(self.btn_unsub_action)

        reader_layout.addWidget(self.unsub_banner)

        # Security Shield Banner & Reader Action Bar
        self.shield_banner = QFrame()
        self.shield_banner.setObjectName("SecurityShieldBanner")
        shield_layout = QHBoxLayout(self.shield_banner)
        shield_layout.setContentsMargins(6, 2, 6, 2)
        shield_layout.setSpacing(4)

        self.lbl_shield = QLabel("🛡 CRITMAIL SHIELD ACTIVE: Sandboxed • Scripts Neutralized • Tracking Protected")
        self.lbl_shield.setObjectName("SecurityBannerText")
        shield_layout.addWidget(self.lbl_shield)

        shield_layout.addStretch()

        self.btn_decrypt_cipher = QPushButton("🔓 Decrypt Cipher")
        self.btn_decrypt_cipher.setFixedHeight(18)
        self.btn_decrypt_cipher.setStyleSheet("font-size: 7.5pt; padding: 1px 6px; color: #00f076; border: 1px solid #00f076; font-weight: bold;")
        self.btn_decrypt_cipher.setVisible(False)
        self.btn_decrypt_cipher.clicked.connect(self._decrypt_current_message)
        shield_layout.addWidget(self.btn_decrypt_cipher)

        self.btn_save_att = QPushButton("📎 Attachments")
        self.btn_save_att.setFixedHeight(18)
        self.btn_save_att.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_save_att.setVisible(False)
        self.btn_save_att.clicked.connect(self._save_attachments_to_disk)
        shield_layout.addWidget(self.btn_save_att)

        self.btn_load_images = QPushButton("🖼 Block Images" if self.allow_remote_images else "🖼 Load Images")
        self.btn_load_images.setFixedHeight(18)
        self.btn_load_images.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_load_images.clicked.connect(self._toggle_remote_images)
        shield_layout.addWidget(self.btn_load_images)

        self.btn_headers = QPushButton("🔍 Headers")
        self.btn_headers.setFixedHeight(18)
        self.btn_headers.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_headers.clicked.connect(self._view_raw_headers)
        shield_layout.addWidget(self.btn_headers)

        self.btn_archive = QPushButton("📦 Archive")
        self.btn_archive.setFixedHeight(18)
        self.btn_archive.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_archive.clicked.connect(self._archive_selected_message)
        shield_layout.addWidget(self.btn_archive)

        self.btn_shred = QPushButton("🔥 Burn")
        self.btn_shred.setFixedHeight(18)
        self.btn_shred.setToolTip("Permanently shred message & attachments (Shift+Del)")
        self.btn_shred.setStyleSheet("font-size: 7.5pt; padding: 1px 5px; color: #ff3860;")
        self.btn_shred.clicked.connect(self._shred_selected_message)
        shield_layout.addWidget(self.btn_shred)

        self.btn_reply = QPushButton("↩ Reply")
        self.btn_reply.setFixedHeight(18)
        self.btn_reply.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_reply.clicked.connect(self._reply_to_current)
        shield_layout.addWidget(self.btn_reply)

        self.btn_reply_all = QPushButton("↩↩ Reply All")
        self.btn_reply_all.setFixedHeight(18)
        self.btn_reply_all.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_reply_all.clicked.connect(self._reply_all_to_current)
        shield_layout.addWidget(self.btn_reply_all)

        self.btn_forward = QPushButton("↪ Forward")
        self.btn_forward.setFixedHeight(18)
        self.btn_forward.setStyleSheet("font-size: 7.5pt; padding: 1px 5px;")
        self.btn_forward.clicked.connect(self._forward_current)
        shield_layout.addWidget(self.btn_forward)

        reader_layout.addWidget(self.shield_banner)

        # Message Headers Display Area + Spy Classification Stamp
        self.header_panel = QFrame()
        self.header_panel.setStyleSheet("background: #090e17; border: 1px solid #14243b; padding: 5px;")
        hdr_layout = QVBoxLayout(self.header_panel)
        hdr_layout.setContentsMargins(4, 3, 4, 3)
        hdr_layout.setSpacing(2)

        subj_row = QHBoxLayout()
        self.lbl_msg_subject = QLabel("(Select a transmission to inspect)")
        self.lbl_msg_subject.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9.5pt;")
        subj_row.addWidget(self.lbl_msg_subject, 1)

        self.lbl_classification_stamp = QLabel("[ CLEARANCE: STANDBY ]")
        self.lbl_classification_stamp.setStyleSheet(
            "background: #102136; color: #00e5ff; border: 1px solid #00d4ff; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
        )
        subj_row.addWidget(self.lbl_classification_stamp)
        hdr_layout.addLayout(subj_row)

        self.lbl_msg_meta = QLabel("")
        self.lbl_msg_meta.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        hdr_layout.addWidget(self.lbl_msg_meta)

        reader_layout.addWidget(self.header_panel)

        # Body Text Browser
        self.browser_body = SafeTextBrowser(self)
        reader_layout.addWidget(self.browser_body, 1)

        self.right_splitter.addWidget(reader_widget)
        self.right_splitter.setSizes([260, 390])

        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([245, 870])

        main_layout.addWidget(self.main_splitter, 1)

        # 4. Status Bar
        self.status_bar = QLabel("CritMail SIGINT Terminal Ready • DPAPI Hardware Vault • TLS 1.3 Active • Link Guard Online")
        self.status_bar.setStyleSheet(
            f"background: #090e17; color: {COLORS['text_secondary']}; border: 1px solid #14243b; padding: 2px 6px; font-size: 8pt;"
        )
        main_layout.addWidget(self.status_bar)

        self.set_content_layout(main_layout)

    # -------------------------------------------------------------------------
    # Auto-Sync Timer
    # -------------------------------------------------------------------------
    def _setup_auto_sync_timer(self):
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._auto_sync_tick)
        self._apply_auto_sync_interval()

    def _apply_auto_sync_interval(self):
        mins = int(get_setting("auto_sync_minutes", "5") or "0")
        if mins > 0:
            self.sync_timer.start(mins * 60 * 1000)
        else:
            self.sync_timer.stop()

    def _auto_sync_tick(self):
        accounts = get_accounts()
        if accounts and accounts[0].get("incoming_password") and self.btn_get_mail.isEnabled():
            self._fetch_mail()

    # -------------------------------------------------------------------------
    # Categories & Filters
    # -------------------------------------------------------------------------
    def _set_category_filter(self, category: str):
        self.current_category = category
        for name, btn in self.cat_btns.items():
            btn.setChecked(name == category)
        self._load_messages_table(search_term=self.txt_search.text().strip())

    def _set_status_filter(self, filter_mode: str):
        self.filter_mode = filter_mode
        idx = self.combo_filter.findData(filter_mode)
        if idx >= 0:
            self.combo_filter.setCurrentIndex(idx)
        self._load_messages_table(search_term=self.txt_search.text().strip())

    def _on_filter_mode_changed(self, idx: int):
        self.filter_mode = self.combo_filter.currentData() or "ALL"
        if self.current_folder_id:
            self._load_messages_table(search_term=self.txt_search.text().strip())

    def _on_search_changed(self, text: str):
        if self.current_folder_id:
            self._load_messages_table(search_term=text.strip())

    # -------------------------------------------------------------------------
    # Folder & Message Management
    # -------------------------------------------------------------------------
    def _refresh_accounts_and_folders(self):
        prev_folder_id = self.current_folder_id
        self.tree_folders.clear()
        accounts = get_accounts()

        if not accounts:
            item = QTreeWidgetItem(self.tree_folders, ["[ NO ACCOUNTS CONFIGURED ]"])
            item.setDisabled(True)
            self.lcd_status.setText("CRITMAIL // NO ACCOUNTS • CLICK 'ACCOUNTS' TO SETUP")
            return

        selected_item = None
        for acc in accounts:
            proto_badge = acc.get("account_type", "IMAP")
            acc_item = QTreeWidgetItem(self.tree_folders, [f"✉ {acc['email_address']} [{proto_badge}]"])
            acc_item.setData(0, Qt.ItemDataRole.UserRole, ("account", acc["id"]))
            acc_item.setExpanded(True)

            folders = get_folders_for_account(acc["id"])
            icon_map = {
                "inbox": "📥",
                "sent": "📤",
                "drafts": "📝",
                "archive": "📦",
                "spam": "⚠",
                "trash": "🗑"
            }
            for f in folders:
                unread = get_unread_count(f["id"])
                total = get_total_count(f["id"])
                badge = f" ({unread}/{total})" if unread > 0 else (f" ({total})" if total > 0 else "")
                icon_glyph = icon_map.get(f["folder_type"], "📁")
                f_item = QTreeWidgetItem(acc_item, [f" {icon_glyph} {f['name']}{badge}"])
                f_item.setData(0, Qt.ItemDataRole.UserRole, ("folder", f["id"], acc["id"], f["folder_type"], f["name"]))
                if prev_folder_id == f["id"]:
                    selected_item = f_item

        if selected_item:
            self.tree_folders.setCurrentItem(selected_item)
            self._on_folder_selected(selected_item, 0)
        elif self.tree_folders.topLevelItemCount() > 0:
            first_acc_item = self.tree_folders.topLevelItem(0)
            if first_acc_item.childCount() > 0:
                self.tree_folders.setCurrentItem(first_acc_item.child(0))
                self._on_folder_selected(first_acc_item.child(0), 0)

    def _on_folder_selected(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        if data[0] == "account":
            self.current_account_id = data[1]
            return
        elif data[0] == "folder":
            _, folder_id, account_id, folder_type, _ = data
            self.current_folder_id = folder_id
            self.current_account_id = account_id
            self.current_folder_type = folder_type
            self._load_messages_table(search_term=self.txt_search.text().strip())

    def _load_messages_table(self, search_term: str = ""):
        self.table_messages.blockSignals(True)
        self.table_messages.setRowCount(0)
        self.table_messages.blockSignals(False)

        self.chk_select_all.blockSignals(True)
        self.chk_select_all.setChecked(False)
        self.chk_select_all.blockSignals(False)
        self.bulk_action_bar.setVisible(False)

        self.current_message_id = None
        self.browser_body.clear()
        self.lbl_msg_subject.setText("(Select a message to view)")
        self.lbl_msg_meta.setText("")
        self.btn_save_att.setVisible(False)
        self.unsub_banner.setVisible(False)

        if not self.current_folder_id:
            return

        messages = get_messages_in_folder(
            self.current_folder_id,
            search_term=search_term,
            filter_mode=self.filter_mode,
            category=self.current_category
        )
        self.table_messages.blockSignals(True)
        self.table_messages.setRowCount(len(messages))

        for row, msg in enumerate(messages):
            flags = []
            if not msg["is_read"]:
                flags.append("●")
            if msg["is_flagged"]:
                flags.append("★")
            if msg["has_attachments"]:
                flags.append("📎")
            status_text = " ".join(flags) if flags else " "

            item_status = QTableWidgetItem(status_text)
            item_status.setFlags(item_status.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item_status.setCheckState(Qt.CheckState.Unchecked)
            if msg["is_flagged"]:
                item_status.setForeground(QColor(COLORS["warning_orange"]))
            elif not msg["is_read"]:
                item_status.setForeground(QColor(COLORS["text_accent"]))
            item_status.setData(Qt.ItemDataRole.UserRole, msg["id"])
            self.table_messages.setItem(row, 0, item_status)

            party = msg["recipient"] if self.current_folder_type in ("sent", "drafts") else msg["sender"]
            item_from = QTableWidgetItem(party)
            self.table_messages.setItem(row, 1, item_from)

            item_subj = QTableWidgetItem(msg["subject"])
            if not msg["is_read"]:
                f = item_subj.font()
                f.setBold(True)
                item_subj.setFont(f)
            self.table_messages.setItem(row, 2, item_subj)

            item_cat = QTableWidgetItem(f"[{msg.get('category', 'Primary')}]")
            self.table_messages.setItem(row, 3, item_cat)

            item_date = QTableWidgetItem(msg["date"][:19] if msg["date"] else "")
            self.table_messages.setItem(row, 4, item_date)

            size_kb = f"{msg['size_bytes'] / 1024:.1f} KB" if msg["size_bytes"] else "0 KB"
            item_size = QTableWidgetItem(size_kb)
            self.table_messages.setItem(row, 5, item_size)

        self.table_messages.blockSignals(False)
        self.lcd_status.setText(f"LOADED // {len(messages)} MESSAGES • CAT: {self.current_category}")

        if len(messages) > 0:
            self.table_messages.selectRow(0)

    def _on_select_all_toggled(self, checked: bool):
        self._set_all_checkboxes(checked)

    def _set_all_checkboxes(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.table_messages.blockSignals(True)
        for row in range(self.table_messages.rowCount()):
            item = self.table_messages.item(row, 0)
            if item:
                item.setCheckState(state)
        self.table_messages.blockSignals(False)
        self.chk_select_all.blockSignals(True)
        self.chk_select_all.setChecked(checked)
        self.chk_select_all.blockSignals(False)
        self._update_bulk_action_bar()

    def _on_message_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            self._update_bulk_action_bar()

    def _get_checked_message_ids(self) -> list[int]:
        checked_ids = []
        for row in range(self.table_messages.rowCount()):
            item = self.table_messages.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                mid = item.data(Qt.ItemDataRole.UserRole)
                if mid is not None:
                    checked_ids.append(int(mid))
        return checked_ids

    def _get_selected_row_message_ids(self) -> list[int]:
        rows = sorted({idx.row() for idx in self.table_messages.selectionModel().selectedRows()})
        ids = []
        for r in rows:
            item = self.table_messages.item(r, 0)
            if item:
                mid = item.data(Qt.ItemDataRole.UserRole)
                if mid is not None:
                    ids.append(int(mid))
        return ids

    def _get_target_message_ids(self) -> list[int]:
        """Returns checked message IDs if any checkboxes are checked; otherwise selected rows or current message."""
        checked = self._get_checked_message_ids()
        if checked:
            return checked
        selected = self._get_selected_row_message_ids()
        if selected:
            return selected
        if self.current_message_id:
            return [self.current_message_id]
        return []

    def _update_bulk_action_bar(self):
        checked_ids = self._get_checked_message_ids()
        selected_ids = self._get_selected_row_message_ids()
        total_rows = self.table_messages.rowCount()

        self.chk_select_all.blockSignals(True)
        self.chk_select_all.setChecked(total_rows > 0 and len(checked_ids) == total_rows)
        self.chk_select_all.blockSignals(False)

        if len(checked_ids) > 0:
            self.lbl_bulk_count.setText(f"☑ {len(checked_ids)} CHECKED")
            self.bulk_action_bar.setVisible(True)
        elif len(selected_ids) > 1:
            self.lbl_bulk_count.setText(f"☑ {len(selected_ids)} SELECTED")
            self.bulk_action_bar.setVisible(True)
        else:
            self.bulk_action_bar.setVisible(False)

    def _on_message_selected(self):
        self._update_bulk_action_bar()
        selected = self.table_messages.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        item_status = self.table_messages.item(row, 0)
        msg_id = item_status.data(Qt.ItemDataRole.UserRole)
        self._display_message(msg_id)

    def _on_message_double_clicked(self, item: QTableWidgetItem):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return
        if self.current_folder_type == "drafts":
            dlg = ComposeDialog(self, reply_to_msg=msg, mode="draft", active_account_id=self.current_account_id)
            if dlg.exec():
                delete_message(self.current_message_id)
                self._refresh_accounts_and_folders()

    def _update_current_folder_badge_in_tree(self):
        """Refresh the unread/total badge on the currently selected folder tree item without losing selection."""
        current_item = self.tree_folders.currentItem()
        if not current_item:
            return
        data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "folder":
            return
        _, folder_id, _, folder_type, folder_name = data
        icon_map = {
            "inbox": "📥",
            "sent": "📤",
            "drafts": "📝",
            "archive": "📦",
            "spam": "⚠",
            "trash": "🗑"
        }
        unread = get_unread_count(folder_id)
        total = get_total_count(folder_id)
        badge = f" ({unread}/{total})" if unread > 0 else (f" ({total})" if total > 0 else "")
        icon_glyph = icon_map.get(folder_type, "📁")
        current_item.setText(0, f" {icon_glyph} {folder_name}{badge}")

    def _display_message(self, message_id: int):
        self.current_message_id = message_id
        msg = get_message_full(message_id)
        if not msg:
            return

        was_unread = not msg.get("is_read")
        mark_message_read(message_id, True)

        # Immediately update row bolding/dot and folder unread badge if it was unread
        if was_unread:
            selected = self.table_messages.selectedItems()
            if selected:
                row = selected[0].row()
                item_status = self.table_messages.item(row, 0)
                item_subj = self.table_messages.item(row, 2)
                if item_status:
                    flags = []
                    if msg.get("is_flagged"):
                        flags.append("★")
                    if msg.get("has_attachments"):
                        flags.append("📎")
                    item_status.setText(" ".join(flags) if flags else " ")
                if item_subj:
                    f = item_subj.font()
                    f.setBold(False)
                    item_subj.setFont(f)
            self._update_current_folder_badge_in_tree()

        star_prefix = "★ " if msg.get("is_flagged") else ""
        self.lbl_msg_subject.setText(f"{star_prefix}[{msg.get('category', 'Primary')}] {msg['subject'] or '(No Subject)'}")
        meta_parts = [
            f"From: {msg['sender']}",
            f"To: {msg['recipient']}"
        ]
        if msg.get("cc"):
            meta_parts.append(f"Cc: {msg['cc']}")
        meta_parts.append(f"Date: {msg['date']}")

        attachments = msg.get("attachments", [])
        if attachments:
            att_names = ", ".join(a["filename"] for a in attachments)
            meta_parts.append(f"📎 Attachments ({len(attachments)}): {att_names}")
            self.btn_save_att.setVisible(True)
        else:
            self.btn_save_att.setVisible(False)

        meta_line = "  |  ".join(meta_parts)
        if self.stealth_redact_mode:
            meta_line = redact_sensitive_text(meta_line)
        self.lbl_msg_meta.setText(meta_line)

        # Check for TIA Classified Cipher block
        body_plain = msg.get("body_plain") or ""
        body_html = msg.get("body_html") or ""
        is_cipher = has_classified_cipher(body_plain) or has_classified_cipher(body_html)
        self.btn_decrypt_cipher.setVisible(is_cipher)

        # Spy Classification Stamp
        if is_cipher:
            self.lbl_classification_stamp.setText("[ 🔐 TOP SECRET // AES-256-GCM CIPHER ]")
            self.lbl_classification_stamp.setStyleSheet(
                "background: #2b0f1c; color: #ff3860; border: 1px solid #ff3860; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
            )
        elif self.current_folder_type == "spam":
            self.lbl_classification_stamp.setText("[ ⚠ QUARANTINE // HOSTILE SIGNAL ]")
            self.lbl_classification_stamp.setStyleSheet(
                "background: #2b1d0f; color: #ffb300; border: 1px solid #ffb300; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
            )
        elif "@theintelligenceagency.net" in (msg.get("sender") or "").lower():
            self.lbl_classification_stamp.setText("[ 🎖 INTERNAL AGENCY // EYES ONLY ]")
            self.lbl_classification_stamp.setStyleSheet(
                "background: #0d2b1d; color: #00e676; border: 1px solid #00e676; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
            )
        else:
            self.lbl_classification_stamp.setText("[ 📡 EXTERNAL INTERCEPT // CLEARED ]")
            self.lbl_classification_stamp.setStyleSheet(
                "background: #102136; color: #00e5ff; border: 1px solid #00d4ff; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
            )

        # Check Unsubscribe data
        unsub_data = parse_unsubscribe_json(msg.get("unsubscribe_info", ""))
        self.unsub_banner.setVisible(bool(unsub_data.get("has_unsubscribe")))

        if self.safe_mode_plain_text or not body_html:
            shown_text = body_plain or "(Empty message body)"
            if self.stealth_redact_mode:
                shown_text = redact_sensitive_text(shown_text)
            self.browser_body.setPlainText(shown_text)
            mode_suffix = " • STEALTH REDACTION ACTIVE" if self.stealth_redact_mode else ""
            self.lbl_shield.setText(f"🛡 CRITMAIL SHIELD: Plain-Text Mode (Zero Execution Risk){mode_suffix}")
            self.lbl_shield.setStyleSheet(f"color: {COLORS['secure_green']};")
        else:
            sanitized, blocked_count = sanitize_html(body_html, block_remote_images=not self.allow_remote_images)
            if self.stealth_redact_mode:
                sanitized = redact_sensitive_html(sanitized)
            self.browser_body.setHtml(sanitized)
            mode_suffix = " • STEALTH REDACTION" if self.stealth_redact_mode else ""
            if blocked_count > 0:
                self.lbl_shield.setText(
                    f"🛡 CRITMAIL SHIELD: {blocked_count} Remote Beacon(s) Blocked • HTML Sanitized{mode_suffix}"
                )
                self.lbl_shield.setStyleSheet(f"color: {COLORS['warning_orange']};")
            else:
                self.lbl_shield.setText(f"🛡 CRITMAIL SHIELD: Verified Safe Content • No Trackers{mode_suffix}")
                self.lbl_shield.setStyleSheet(f"color: {COLORS['secure_green']};")

    # -------------------------------------------------------------------------
    # Classified Cipher Decryption & Stealth Redaction
    # -------------------------------------------------------------------------
    def _decrypt_current_message(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return
        body_plain = msg.get("body_plain") or msg.get("body_html") or ""
        if not has_classified_cipher(body_plain):
            QMessageBox.information(self, "No Classified Cipher", "This transmission does not contain an AES-256-GCM TIA Cipher block.")
            return

        key, ok = QInputDialog.getText(
            self,
            "Decrypt Classified Transmission",
            "Enter shared clearance passphrase to decrypt AES-256-GCM payload:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not key:
            return

        try:
            decrypted = decrypt_classified_message(body_plain, key)
            if self.stealth_redact_mode:
                decrypted = redact_sensitive_text(decrypted)
            self.browser_body.setPlainText(decrypted)
            self.lbl_classification_stamp.setText("[ 🔓 DECRYPTED // EYES ONLY ]")
            self.lbl_classification_stamp.setStyleSheet(
                "background: #0d2b1d; color: #00e676; border: 1px solid #00e676; padding: 1px 6px; font-size: 7.5pt; font-weight: bold;"
            )
            self.status_bar.setText("Classified transmission decrypted in volatile memory (never written to disk).")
        except ValueError as e:
            QMessageBox.critical(self, "Decryption Failed", str(e))

    def _toggle_stealth_redact(self):
        self.stealth_redact_mode = not self.stealth_redact_mode
        self.btn_stealth.setText("🕵 STEALTH: ON" if self.stealth_redact_mode else "🕵 STEALTH: OFF")
        if self.stealth_redact_mode:
            self.btn_stealth.setStyleSheet("color: #ff3860; border: 1px solid #ff3860; font-weight: bold;")
        else:
            self.btn_stealth.setStyleSheet("")
        state = "ENGAGED (Emails/IPs/Phones Masked)" if self.stealth_redact_mode else "DISENGAGED"
        self.status_bar.setText(f"🕵 Stealth Redaction Mode: {state}")
        if self.current_message_id:
            self._display_message(self.current_message_id)

    def _toggle_folder_sidebar(self):
        self.left_widget.setVisible(not self.left_widget.isVisible())

    # -------------------------------------------------------------------------
    # One-Click Auto-Unsubscribe
    # -------------------------------------------------------------------------
    def _execute_unsubscribe(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return

        unsub = parse_unsubscribe_json(msg.get("unsubscribe_info", ""))
        if not unsub.get("has_unsubscribe"):
            QMessageBox.information(self, "No Unsubscribe Link", "No automated unsubscribe header or link was detected in this email.")
            return

        res = QMessageBox.question(
            self,
            "Confirm 1-Click Unsubscribe",
            f"CritMail detected an automated unsubscribe route for:\n'{msg.get('sender')}'.\n\nProceed to unsubscribe from this mailing list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        # 1. Try RFC 8058 One-Click HTTPS POST first if supported
        if unsub.get("one_click_post") and unsub.get("url"):
            ok, status_msg = perform_one_click_post_unsubscribe(unsub["url"])
            if ok:
                QMessageBox.information(self, "1-Click Unsubscribe Complete", status_msg)
                self.status_bar.setText(status_msg)
                return

        # 2. Prefer mailto unsubscribe if present
        if unsub.get("mailto"):
            mailto_uri = unsub["mailto"]
            target_addr = mailto_uri.replace("mailto:", "").split("?")[0].strip()
            subj = "unsubscribe"
            if "subject=" in mailto_uri.lower():
                try:
                    subj = mailto_uri.split("subject=")[1].split("&")[0]
                except Exception:
                    pass
            cd = ComposeDialog(self, initial_to=target_addr, active_account_id=self.current_account_id)
            cd.txt_subject.setText(subj)
            cd.txt_body.setPlainText("Unsubscribe request generated by CritMail.")
            cd.exec()
        elif unsub.get("url"):
            # Open via LinkGuard
            LinkGuardDialog(unsub["url"], self).exec()

        self.status_bar.setText("Unsubscribe request initiated.")

    # -------------------------------------------------------------------------
    # Context Menus (Table & Folder)
    # -------------------------------------------------------------------------
    def _show_message_context_menu(self, pos):
        target_ids = self._get_target_message_ids()
        if not target_ids and not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id) if self.current_message_id else None
        count = len(target_ids)
        suffix = f" ({count} Checked)" if count > 1 else ""

        menu = QMenu(self)

        if count <= 1 and msg:
            act_reply = menu.addAction("↩ Reply (Ctrl+R)")
            act_reply.triggered.connect(self._reply_to_current)

            act_reply_all = menu.addAction("↩↩ Reply All (Ctrl+Shift+R)")
            act_reply_all.triggered.connect(self._reply_all_to_current)

            act_fwd = menu.addAction("↪ Forward (Ctrl+L)")
            act_fwd.triggered.connect(self._forward_current)

            if has_classified_cipher(msg.get("body_plain", "")) or has_classified_cipher(msg.get("body_html", "")):
                act_dec = menu.addAction("🔓 Decrypt Classified Cipher (Ctrl+Shift+D)...")
                act_dec.triggered.connect(self._decrypt_current_message)

            menu.addSeparator()

        act_read = menu.addAction(f"✔ Mark as Read{suffix}")
        act_read.triggered.connect(lambda: self._set_selected_read_state(True))

        act_unread = menu.addAction(f"● Mark as Unread{suffix}")
        act_unread.triggered.connect(lambda: self._set_selected_read_state(False))

        act_star = menu.addAction(f"★ Toggle Star / Flag{suffix}")
        act_star.triggered.connect(self._toggle_flag_current)

        act_arch = menu.addAction(f"📦 Archive{suffix} (Ctrl+E)")
        act_arch.triggered.connect(self._archive_selected_message)

        act_spam = menu.addAction(f"⚠ Mark as Spam / Quarantine{suffix} (Ctrl+J)")
        act_spam.triggered.connect(self._spam_selected_message)

        # Categorize
        cat_m = menu.addMenu(f"🏷 Assign Category{suffix}")
        for c in ["Primary", "Social", "Updates", "Promotions", "Forums"]:
            cat_m.addAction(c).triggered.connect(lambda checked=False, cat=c: self._set_current_message_category(cat))

        # Move to folder
        move_m = menu.addMenu(f"📁 Move to Folder{suffix}")
        if self.current_account_id:
            for f in get_folders_for_account(self.current_account_id):
                if f["id"] != self.current_folder_id:
                    fid = f["id"]
                    move_m.addAction(f["name"]).triggered.connect(lambda checked=False, target_id=fid: self._move_current_to_folder(target_id))

        if count <= 1 and msg:
            menu.addSeparator()

            unsub = parse_unsubscribe_json(msg.get("unsubscribe_info", ""))
            if unsub.get("has_unsubscribe"):
                act_un = menu.addAction("⚡ 1-Click Unsubscribe from List...")
                act_un.triggered.connect(self._execute_unsubscribe)

            act_contact = menu.addAction("📇 Add Sender to Contacts...")
            act_contact.triggered.connect(self._add_current_sender_to_contacts)

            act_block = menu.addAction("🚫 Block Sender (Add to Blacklist)...")
            act_block.triggered.connect(self._block_current_sender)

            menu.addSeparator()

            act_print = menu.addAction("🖨 Print Message... (Ctrl+P)")
            act_print.triggered.connect(self._print_current_message)

            act_pdf = menu.addAction("📄 Export as PDF...")
            act_pdf.triggered.connect(self._export_current_pdf)

            act_exp = menu.addAction("💾 Export as .eml / .txt...")
            act_exp.triggered.connect(self._export_selected_message)

            act_hdr = menu.addAction("🔍 View Raw Headers & Source")
            act_hdr.triggered.connect(self._view_raw_headers)

        menu.addSeparator()

        act_del = menu.addAction(f"✕ Delete{suffix} (Del)")
        act_del.triggered.connect(self._delete_selected_message)

        act_burn = menu.addAction(f"🔥 Burn / Shred Permanently{suffix} (Shift+Del)")
        act_burn.triggered.connect(self._shred_selected_message)

        menu.exec(self.table_messages.viewport().mapToGlobal(pos))

    def _show_folder_context_menu(self, pos):
        item = self.tree_folders.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "folder":
            return
        _, folder_id, account_id, folder_type, folder_name = data

        menu = QMenu(self)
        act_new = menu.addAction("+ Create Subfolder...")
        act_new.triggered.connect(self._create_new_folder)

        if folder_type == "custom":
            act_ren = menu.addAction(f"✏ Rename '{folder_name}'...")
            act_ren.triggered.connect(lambda: self._rename_folder_by_id(folder_id, folder_name))

            act_del = menu.addAction(f"✕ Delete '{folder_name}'...")
            act_del.triggered.connect(lambda: self._delete_folder_by_id(folder_id, folder_name))

        menu.addSeparator()

        act_read = menu.addAction("✔ Mark All as Read")
        act_read.triggered.connect(lambda: self._mark_all_read_in_fld(folder_id))

        if folder_type == "trash":
            act_empty = menu.addAction("🗑 Empty Trash")
            act_empty.triggered.connect(self._empty_trash)

        menu.exec(self.tree_folders.viewport().mapToGlobal(pos))

    # -------------------------------------------------------------------------
    # Printing & PDF Actions
    # -------------------------------------------------------------------------
    def _print_current_message(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            print_message(self, msg)

    def _print_preview_current(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            print_preview_message(self, msg)

    def _export_current_pdf(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            export_message_as_pdf(self, msg)

    # -------------------------------------------------------------------------
    # Message Actions & Categories (Single + Bulk Multi-Select Support)
    # -------------------------------------------------------------------------
    def _set_current_message_category(self, category: str):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        for mid in target_ids:
            set_message_category(mid, category)
        label = f"{len(target_ids)} messages" if len(target_ids) > 1 else "Message"
        self.status_bar.setText(f"{label} categorized as [{category}].")
        self._load_messages_table(search_term=self.txt_search.text().strip())

    def _toggle_flag_current(self):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        flagged = False
        for mid in target_ids:
            flagged = toggle_message_flag(mid)
        if len(target_ids) > 1:
            self.status_bar.setText(f"Toggled ★ star on {len(target_ids)} messages.")
        else:
            self.status_bar.setText("Message starred ★" if flagged else "Message star removed.")
        self._load_messages_table(search_term=self.txt_search.text().strip())

    def _archive_selected_message(self):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        for mid in target_ids:
            archive_message(mid)
        label = f"{len(target_ids)} messages" if len(target_ids) > 1 else "Message"
        self.status_bar.setText(f"📦 {label} moved to Archive.")
        self._refresh_accounts_and_folders()

    def _spam_selected_message(self):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        for mid in target_ids:
            mark_message_spam(mid)
        label = f"{len(target_ids)} messages" if len(target_ids) > 1 else "Message"
        self.status_bar.setText(f"⚠ {label} quarantined in Spam folder.")
        self._refresh_accounts_and_folders()

    def _shred_selected_message(self):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        count = len(target_ids)
        target_desc = f"these {count} selected messages" if count > 1 else "this message"
        res = QMessageBox.warning(
            self,
            "🔥 Burn / Cryptographic Shred",
            f"WARNING: This will overwrite cached attachments with random bytes, redact database fields, and permanently destroy {target_desc}.\n\nProceed with Burn protocol?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return
        for mid in target_ids:
            shred_message(mid)
        if self.current_message_id in target_ids:
            self.current_message_id = None
        label = f"{count} messages" if count > 1 else "Message"
        self.status_bar.setText(f"🔥 {label} and attachments cryptographically shredded.")
        self._refresh_accounts_and_folders()

    def _populate_move_menu(self):
        self.move_menu.clear()
        if not self.current_account_id:
            return
        for f in get_folders_for_account(self.current_account_id):
            if f["id"] != self.current_folder_id:
                fid = f["id"]
                self.move_menu.addAction(f["name"]).triggered.connect(
                    lambda checked=False, target_id=fid: self._move_current_to_folder(target_id)
                )

    def _populate_bulk_move_menu(self):
        self.bulk_move_menu.clear()
        if not self.current_account_id:
            return
        for f in get_folders_for_account(self.current_account_id):
            if f["id"] != self.current_folder_id:
                fid = f["id"]
                self.bulk_move_menu.addAction(f["name"]).triggered.connect(
                    lambda checked=False, target_id=fid: self._move_current_to_folder(target_id)
                )

    def _move_current_to_folder(self, target_folder_id: int):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        for mid in target_ids:
            move_message_to_folder(mid, target_folder_id)
        label = f"{len(target_ids)} messages" if len(target_ids) > 1 else "Message"
        self.status_bar.setText(f"📁 {label} moved to folder.")
        self._refresh_accounts_and_folders()

    def _set_selected_read_state(self, is_read: bool):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        for mid in target_ids:
            mark_message_read(mid, is_read)
        label = f"{len(target_ids)} messages" if len(target_ids) > 1 else "Message"
        state_str = "read" if is_read else "unread"
        self.status_bar.setText(f"Marked {label.lower()} as {state_str}.")
        self._refresh_accounts_and_folders()

    def _mark_all_read(self):
        if not self.current_folder_id:
            return
        mark_all_read_in_folder(self.current_folder_id)
        self._refresh_accounts_and_folders()

    def _mark_all_read_in_fld(self, folder_id: int):
        mark_all_read_in_folder(folder_id)
        self._refresh_accounts_and_folders()

    def _block_current_sender(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return
        sender = msg.get("sender", "")
        email_addr = sender.split("<")[-1].rstrip(">").strip() if "<" in sender else sender.strip()
        res = QMessageBox.question(
            self,
            "Block Sender",
            f"Add '{email_addr}' to the Blacklist and automatically route future emails to Spam?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            add_rule(rule_type="sender", pattern=email_addr, action="spam", account_id=self.current_account_id)
            QMessageBox.information(self, "Sender Blocked", f"'{email_addr}' has been added to your Blacklist.")

    def _add_current_sender_to_contacts(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return
        raw_sender = msg.get("sender", "")
        email_addr = raw_sender.split("<")[-1].rstrip(">").strip() if "<" in raw_sender else raw_sender.strip()
        name_part = raw_sender.split("<")[0].strip().strip('"') if "<" in raw_sender else email_addr.split("@")[0]

        # Open Contact Sheet with pre-filled details
        contact_stub = {"name": name_part, "email": email_addr}
        dlg = ContactSheetDialog(contact_data=contact_stub, parent=self)
        dlg.exec()

    def _save_attachments_to_disk(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg or not msg.get("attachments"):
            QMessageBox.information(self, "No Attachments", "This message has no attachments.")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Select Destination Folder for Attachments")
        if not dest_dir:
            return

        saved = 0
        for att in msg["attachments"]:
            src = Path(att["file_path"])
            if src.is_file():
                dst = Path(dest_dir) / att["filename"]
                shutil.copy2(src, dst)
                saved += 1

        QMessageBox.information(self, "Attachments Saved", f"Saved {saved} attachment(s) to:\n{dest_dir}")

    def _export_selected_message(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if not msg:
            return
        safe_subj = "".join(c if c.isalnum() or c in " -_" else "_" for c in (msg.get("subject") or "message"))[:40]
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Email Message",
            f"{safe_subj}.eml",
            "RFC822 Email (*.eml);;Plain Text (*.txt)"
        )
        if not file_path:
            return
        content = (
            f"From: {msg.get('sender', '')}\n"
            f"To: {msg.get('recipient', '')}\n"
            f"Cc: {msg.get('cc', '')}\n"
            f"Date: {msg.get('date', '')}\n"
            f"Subject: {msg.get('subject', '')}\n"
            f"Message-ID: {msg.get('message_id', '')}\n\n"
            f"{msg.get('body_plain', '')}"
        )
        Path(file_path).write_text(content, encoding="utf-8")
        self.status_bar.setText(f"Exported message to {file_path}")

    def _import_eml_file(self):
        if not self.current_account_id or not self.current_folder_id:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import .eml Message", "", "Email Files (*.eml);;All Files (*.*)"
        )
        if not file_path:
            return
        raw_bytes = Path(file_path).read_bytes()
        parsed_msg = email.message_from_bytes(raw_bytes, policy=policy.default)
        subject = decode_mime_words(parsed_msg.get("Subject", "(Imported Email)"))
        sender = decode_mime_words(parsed_msg.get("From", "(Unknown)"))
        recipient = decode_mime_words(parsed_msg.get("To", ""))
        date_str = parsed_msg.get("Date", "")
        body_plain = ""
        body_html = ""
        if parsed_msg.is_multipart():
            for part in parsed_msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain" and not body_plain:
                    try:
                        body_plain = part.get_content()
                    except Exception:
                        pass
                elif ct == "text/html" and not body_html:
                    try:
                        body_html = part.get_content()
                    except Exception:
                        pass
        else:
            try:
                body_plain = parsed_msg.get_content()
            except Exception:
                pass
        if not body_plain and body_html:
            body_plain = html_to_plain_text(body_html)

        save_message(
            account_id=self.current_account_id,
            folder_id=self.current_folder_id,
            server_uid=f"imported-{Path(file_path).name}-{len(raw_bytes)}",
            message_id=parsed_msg.get("Message-ID", ""),
            subject=subject,
            sender=sender,
            recipient=recipient,
            cc="",
            bcc="",
            date=date_str,
            body_plain=body_plain,
            body_html=body_html,
            size_bytes=len(raw_bytes),
            raw_headers="\n".join(f"{k}: {v}" for k, v in parsed_msg.items()),
            has_attachments=False
        )
        self._refresh_accounts_and_folders()
        self.status_bar.setText(f"Imported {Path(file_path).name}")

    def _delete_selected_message(self):
        target_ids = self._get_target_message_ids()
        if not target_ids:
            return
        count = len(target_ids)
        target_desc = f"these {count} selected messages" if count > 1 else "this message"
        prompt_text = (
            f"Permanently delete {target_desc} from Trash?"
            if self.current_folder_type == "trash"
            else f"Move {target_desc} to Trash?"
        )
        if get_setting("confirm_delete", "1") == "1":
            res = QMessageBox.question(
                self,
                "Delete Message(s)",
                prompt_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if res != QMessageBox.StandardButton.Yes:
                return

        for mid in target_ids:
            delete_message(mid)
        if self.current_message_id in target_ids:
            self.current_message_id = None
        label = f"{count} messages" if count > 1 else "Message"
        self.status_bar.setText(f"✕ {label} deleted.")
        self._refresh_accounts_and_folders()

    # -------------------------------------------------------------------------
    # Custom Folder Management
    # -------------------------------------------------------------------------
    def _create_new_folder(self):
        if not self.current_account_id:
            return
        name, ok = QInputDialog.getText(self, "Create Custom Folder", "Enter new folder name:")
        if ok and name.strip():
            create_custom_folder(self.current_account_id, name.strip())
            self._refresh_accounts_and_folders()

    def _rename_current_folder(self):
        if not self.current_folder_id or self.current_folder_type != "custom":
            QMessageBox.information(self, "Rename Folder", "Please select a custom folder to rename.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Custom Folder", "Enter new folder name:")
        if ok and new_name.strip():
            rename_folder(self.current_folder_id, new_name.strip())
            self._refresh_accounts_and_folders()

    def _rename_folder_by_id(self, folder_id: int, current_name: str):
        new_name, ok = QInputDialog.getText(self, "Rename Custom Folder", "Enter new folder name:", text=current_name)
        if ok and new_name.strip():
            rename_folder(folder_id, new_name.strip())
            self._refresh_accounts_and_folders()

    def _delete_current_folder(self):
        if not self.current_folder_id or self.current_folder_type != "custom":
            QMessageBox.information(self, "Delete Folder", "Only custom user folders can be deleted.")
            return
        self._delete_folder_by_id(self.current_folder_id, "this folder")

    def _delete_folder_by_id(self, folder_id: int, folder_name: str):
        res = QMessageBox.question(
            self,
            "Delete Folder",
            f"Are you sure you want to delete the folder '{folder_name}'?\nAny messages inside will be moved to Trash.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            delete_folder(folder_id)
            self._refresh_accounts_and_folders()

    def _empty_trash(self):
        if not self.current_account_id:
            return
        res = QMessageBox.question(
            self,
            "Empty Trash",
            "Permanently delete all messages in the Trash folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            empty_trash_for_account(self.current_account_id)
            self._refresh_accounts_and_folders()
            self.status_bar.setText("Trash emptied.")

    # -------------------------------------------------------------------------
    # Dialog Openers
    # -------------------------------------------------------------------------
    def _open_compose(self):
        dialog = ComposeDialog(self, active_account_id=self.current_account_id)
        if dialog.exec():
            self._refresh_accounts_and_folders()

    def _reply_to_current(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            dialog = ComposeDialog(self, reply_to_msg=msg, mode="reply", active_account_id=self.current_account_id)
            if dialog.exec():
                self._refresh_accounts_and_folders()

    def _reply_all_to_current(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            dialog = ComposeDialog(self, reply_to_msg=msg, mode="reply_all", active_account_id=self.current_account_id)
            if dialog.exec():
                self._refresh_accounts_and_folders()

    def _forward_current(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            dialog = ComposeDialog(self, reply_to_msg=msg, mode="forward", active_account_id=self.current_account_id)
            if dialog.exec():
                self._refresh_accounts_and_folders()

    def _open_contacts(self, filter_blocked: bool = False):
        dlg = ContactsDialog(self, picker_mode=False, filter_blocked_only=filter_blocked)
        def _compose_to(addr: str):
            cd = ComposeDialog(self, initial_to=addr, active_account_id=self.current_account_id)
            if cd.exec():
                self._refresh_accounts_and_folders()
        dlg.contact_selected.connect(_compose_to)
        dlg.exec()

    def _open_new_contact_sheet(self):
        dlg = ContactSheetDialog(parent=self)
        dlg.exec()

    def _open_security_dialog(self, initial_tab: int = 0):
        dlg = SecurityPrivacyDialog(self, active_account_id=self.current_account_id, initial_tab=initial_tab)
        if dlg.exec():
            self.allow_remote_images = (get_setting("block_remote_images", "1") == "0")
            self.btn_load_images.setText("🖼 Block Images" if self.allow_remote_images else "🖼 Load Images")
            if self.current_message_id:
                self._display_message(self.current_message_id)

    def _open_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.exec():
            self._apply_auto_sync_interval()
            self.status_bar.setText("Preferences and signature saved.")

    def _open_accounts(self):
        dialog = AccountDialog(self, edit_account_id=self.current_account_id)
        if dialog.exec():
            self._refresh_accounts_and_folders()

    def _open_comms_recon(self):
        dlg = CommsReconDialog(self)
        dlg.exec()

    def _open_clearance_pro(self):
        dlg = AgentClearanceProDialog(self)
        dlg.exec()

    def _view_raw_headers(self):
        if not self.current_message_id:
            return
        msg = get_message_full(self.current_message_id)
        if msg:
            dlg = RawHeadersDialog(msg, self)
            dlg.exec()

    def _open_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _open_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _toggle_safe_mode(self):
        self.safe_mode_plain_text = not self.safe_mode_plain_text
        mode_str = "PLAIN TEXT" if self.safe_mode_plain_text else "HTML"
        self.btn_safe_mode.setText(f"🛡 SAFE MODE: {mode_str}")
        if self.current_message_id:
            self._display_message(self.current_message_id)

    def _toggle_remote_images(self):
        self.allow_remote_images = not self.allow_remote_images
        self.btn_load_images.setText("🖼 Block Images" if self.allow_remote_images else "🖼 Load Images")
        if self.current_message_id:
            self._display_message(self.current_message_id)

    def _fetch_mail(self):
        accounts = get_accounts()
        if not accounts:
            QMessageBox.information(self, "No Accounts", "Please configure an email account first.")
            return

        target_acc = accounts[0]
        if self.current_account_id:
            for acc in accounts:
                if acc["id"] == self.current_account_id:
                    target_acc = acc
                    break

        if not target_acc.get("incoming_password"):
            res = QMessageBox.information(
                self,
                "Password Required",
                f"Please enter your password for {target_acc['email_address']} in Account Settings first.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
            if res == QMessageBox.StandardButton.Ok:
                self._open_accounts()
            return

        proto = target_acc.get("account_type", "IMAP").upper()
        self.lcd_status.setText(
            f"CONNECTING // {proto} SSL/TLS TO {target_acc['incoming_host']}:{target_acc['incoming_port']}..."
        )
        self.btn_get_mail.setEnabled(False)

        self._fetch_thread = MailSyncThread(target_acc)
        self._fetch_thread.progress.connect(self._on_fetch_progress)
        self._fetch_thread.finished.connect(self._on_fetch_finished)
        self._fetch_thread.start()

    def _on_fetch_progress(self, current: int, total: int, text: str):
        self.lcd_status.setText(f"MAIL SYNC // {text}")
        self.status_bar.setText(text)

    def _on_fetch_finished(self, count: int, msg: str):
        self.btn_get_mail.setEnabled(True)
        self.lcd_status.setText(f"CRITMAIL // {msg}")
        self.status_bar.setText(msg)
        self._refresh_accounts_and_folders()

