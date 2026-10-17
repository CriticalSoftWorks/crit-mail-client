"""
CritMail - Main Application Entry Point
Ultra-Fast • Safe & Secure / Hack-Proof • Modern Winamp 3 Monospace Email Client
"""
import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from critmail.config import APP_NAME, APP_VERSION, FONT_SIZE_BASE
from critmail.models.database import (
    init_db, get_accounts, add_account, delete_account,
    get_folder_by_type, save_message, add_or_update_contact
)
from critmail.ui.theme import WINAMP3_BLUE_STYLESHEET
from critmail.ui.icon_factory import create_app_icon
from critmail.ui.splash_screen import CritMailSplashScreen
from critmail.ui.main_window import CritMailWindow


def seed_user_account_if_needed():
    """
    Pre-configures James's email account (james.f@theintelligenceagency.net)
    with IMAP (port 993 SSL/TLS) and SMTP (port 465 SSL/TLS) on mailserver.businessidentity.llc.
    """
    accounts = get_accounts()
    target_email = "james.f@theintelligenceagency.net"
    target_host = "mailserver.businessidentity.llc"

    # Remove old placeholder account if present
    for acc in accounts:
        if acc["email_address"] == "user@critmail.local":
            delete_account(acc["id"])

    accounts = get_accounts()
    has_james = any(acc["email_address"].lower() == target_email for acc in accounts)

    # Seed initial contact
    try:
        add_or_update_contact("James F.", target_email, "The Intelligence Agency", "Primary Account")
    except Exception:
        pass

    if not has_james:
        acc_id = add_account(
            name="The Intelligence Agency",
            email_address=target_email,
            account_type="IMAP",
            incoming_host=target_host,
            incoming_port=993,
            incoming_security="SSL/TLS",
            incoming_username=target_email,
            incoming_password="",  # User enters password securely inside app (encrypted via DPAPI)
            smtp_host=target_host,
            smtp_port=465,
            smtp_security="SSL/TLS",
            smtp_username=target_email,
            smtp_password="",
            keep_on_server=True
        )
        inbox = get_folder_by_type(acc_id, "inbox")
        if inbox:
            welcome_html = f"""
            <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.6;">
                <h2 style="color: #00e5ff; border-bottom: 1px solid #1c3555; padding-bottom: 4px; margin-top: 0px;">
                    [ CRITMAIL CONFIGURED // {target_email.upper()} ]
                </h2>
                <p>Your account <b>{target_email}</b> is pre-configured and ready to connect using <b>IMAP4 over SSL/TLS (Port 993)</b> and <b>SMTP over SSL/TLS (Port 465)</b> via <code>{target_host}</code>.</p>
                
                <h3 style="color: #29b6f6; margin-bottom: 6px;">Why IMAP (993) was selected as your primary protocol:</h3>
                <ul>
                    <li><b>Full Multi-Device &amp; Server Sync:</b> Unlike POP3 (which only downloads Inbox messages one-way), IMAP synchronizes read/unread status and keeps your mailbox intact across all your devices.</li>
                    <li><b>Instant UID Delta Fetching:</b> CritMail caches message UIDs locally in SQLite WAL mode for instant zero-latency searching while staying synced with <code>{target_host}</code>.</li>
                    <li><b>POP3 (Port 995) Also Supported:</b> You can switch between <code>IMAP (993)</code> and <code>POP3 (995)</code> at any time in the <b>[ ✉ ACCOUNTS ]</b> dialog with one click.</li>
                </ul>
                
                <h3 style="color: #00f076; margin-bottom: 6px;">Final Step — Enter Your Mailbox Password:</h3>
                <ol>
                    <li>Click <b>[ ✉ ACCOUNTS ]</b> in the top toolbar (or <code>File &gt; Account Settings</code>).</li>
                    <li>Enter your password for <code>{target_email}</code> (it will be immediately encrypted using Windows DPAPI hardware/OS protection).</li>
                    <li>Click <b>[ ⚡ Test Connection ]</b> to verify your live TLS handshake, then click <b>[ Save Account ]</b>.</li>
                    <li>Click <b>[ ⟳ GET MAIL ]</b> (or press <code>F5</code>) to pull your inbox!</li>
                </ol>
            </div>
            """
            save_message(
                account_id=acc_id,
                folder_id=inbox["id"],
                server_uid="welcome-james-001",
                message_id="<welcome-james-001@critmail.local>",
                subject=f"Account Ready: {target_email} (IMAP 993 / SMTP 465 SSL)",
                sender="CritMail Security Core <security@critmail.local>",
                recipient=target_email,
                cc="",
                bcc="",
                date="2026-10-15 19:00:00",
                body_plain=f"Your account {target_email} is pre-configured for {target_host} (IMAP 993 / SMTP 465).\nClick ACCOUNTS in the top toolbar to enter your password and sync your mail.",
                body_html=welcome_html,
                size_bytes=len(welcome_html),
                raw_headers="X-CritMail-Status: Verified\r\nX-Security-Shield: Active",
                has_attachments=False,
                security_verdict="CLEAN"
            )


def main():
    # Ensure Windows Taskbar displays CritMail custom icon instead of generic Python icon
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CritMail.DesktopClient.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(create_app_icon())

    font = QFont("Consolas", FONT_SIZE_BASE)
    font.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(font)

    app.setStyleSheet(WINAMP3_BLUE_STYLESHEET)

    # Show animated SIGINT splash screen immediately on launch
    splash = CritMailSplashScreen(duration_ms=2100)
    splash.start()
    app.processEvents()

    init_db()
    seed_user_account_if_needed()
    window = CritMailWindow()

    def _transition_to_main():
        splash.close()
        window.show()
        window.raise_()
        window.activateWindow()

    splash.finished.connect(_transition_to_main)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
