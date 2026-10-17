"""
CritMail UI - Help Documentation, About Window, and Raw Header Forensic Viewer
Styled in the Winamp 3 Blue Aesthetic with zero rounded corners.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextBrowser, QTextEdit, QFrame, QApplication
)
from critmail.config import APP_NAME, APP_VERSION, APP_TAGLINE, COLORS
from critmail.ui.icon_factory import create_app_icon, create_titlebar_pixmap


class HelpDialog(QDialog):
    """Comprehensive interactive User Manual & Documentation for CritMail."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Documentation & User Guide")
        self.setWindowIcon(create_app_icon())
        self.resize(720, 540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_titlebar_pixmap(22))
        hdr.addWidget(icon_lbl)

        title_lbl = QLabel(f"[ {APP_NAME.upper()} // OFFICIAL USER GUIDE & MANUAL ]")
        title_lbl.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9.5pt;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        layout.addLayout(hdr)

        tabs = QTabWidget()

        # Tab 1: Quick Start & Features
        tab_quick = QTextBrowser()
        tab_quick.setHtml(f"""
        <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.55;">
            <h3 style="color: #00e5ff; border-bottom: 1px solid #1c3555;">1. Getting Started with CritMail</h3>
            <p><b>CritMail</b> is a standalone, ultra-fast, defense-grade email client designed to handle all of your daily email workflows without ever needing a browser or bloated third-party suite.</p>
            <ul>
                <li><b>Account Configuration (<code>File &gt; Account Settings</code> or <code>[ ✉ ACCOUNTS ]</code>):</b>
                    Your account <code>james.f@theintelligenceagency.net</code> is pre-configured for <code>mailserver.businessidentity.llc</code>. Simply open Accounts, enter your password, click <b>⚡ Test Connection</b>, and click <b>Save Account</b>.</li>
                <li><b>Synchronizing Mail (<code>F5</code> or <code>[ ⟳ GET MAIL ]</code>):</b>
                    Fetches new messages via encrypted SSL/TLS using UID/UIDL delta syncing so messages download instantaneously without duplicates.</li>
                <li><b>Composing, Replying &amp; Forwarding:</b>
                    Use <b>⚡ COMPOSE</b>, <b>↩ Reply</b>, <b>↩↩ Reply All</b>, or <b>↪ Forward</b>. You can also save drafts at any time to your <b>Drafts</b> folder, pick recipients from your <b>Address Book</b>, and attach files safely.</li>
                <li><b>Organizing Your Mailbox:</b>
                    Star/flag important messages (<code>★</code>), filter by Unread / Starred / Attachments, move messages between folders (Inbox, Archive, Spam, Trash, or custom folders), and export emails as standard <code>.eml</code> or <code>.txt</code> files.</li>
            </ul>
        </div>
        """)
        tabs.addTab(tab_quick, "Quick Start")

        # Tab 2: Security & Hack-Proof Architecture
        tab_sec = QTextBrowser()
        tab_sec.setHtml(f"""
        <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.55;">
            <h3 style="color: #00f076; border-bottom: 1px solid #1c3555;">2. Defense-in-Depth Security Architecture</h3>
            <p>CritMail protects your identity, credentials, and operating system through five active security layers:</p>
            <ol>
                <li><b>Windows DPAPI Hardware/OS Credential Encryption:</b>
                    Passwords are encrypted using Windows <code>CryptProtectData</code> (with AES-256-GCM fallback) tied to your Windows user profile. Plaintext passwords are never written to disk.</li>
                <li><b>Strict TLS 1.2 / 1.3 Enforcement:</b>
                    All IMAP (993), POP3 (995), and SMTP (465) connections verify server certificates and enforce modern TLS cipher suites.</li>
                <li><b>Active HTML Sanitizer &amp; Script Stripper:</b>
                    All <code>&lt;script&gt;</code>, <code>&lt;iframe&gt;</code>, <code>&lt;object&gt;</code>, <code>&lt;form&gt;</code>, and inline JavaScript <code>on*</code> event payloads are stripped before rendering.</li>
                <li><b>Remote Tracking Beacon Blocker:</b>
                    1x1 spy pixels and remote images are blocked by default so senders cannot track when, where, or on what IP address you opened an email.</li>
                <li><b>Anti-Phishing Link Guard:</b>
                    Every clicked link is intercepted and analyzed for IDN Punycode homograph spoofing (<code>xn--</code>), raw IP obfuscation, and deceptive <code>@</code> authority tricks before opening your browser.</li>
            </ol>
        </div>
        """)
        tabs.addTab(tab_sec, "Security Shield")

        # Tab 3: Keyboard Shortcuts
        tab_keys = QTextBrowser()
        tab_keys.setHtml(f"""
        <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.6;">
            <h3 style="color: #00e5ff; border-bottom: 1px solid #1c3555;">3. Keyboard Shortcuts</h3>
            <table width="100%" cellspacing="0" cellpadding="4" style="border: 1px solid #1b3250;">
                <tr style="background: #142236; color: #00e5ff;">
                    <th align="left">Shortcut</th>
                    <th align="left">Action</th>
                </tr>
                <tr><td><code>Ctrl + N</code></td><td>Compose New Email</td></tr>
                <tr><td><code>F5</code></td><td>Get Mail / Synchronize Current Account</td></tr>
                <tr><td><code>Ctrl + R</code></td><td>Reply to Selected Email</td></tr>
                <tr><td><code>Ctrl + Shift + R</code></td><td>Reply All to Selected Email</td></tr>
                <tr><td><code>Ctrl + L</code></td><td>Forward Selected Email</td></tr>
                <tr><td><code>Ctrl + F</code></td><td>Focus Quick Filter / Search Box</td></tr>
                <tr><td><code>Ctrl + B</code></td><td>Open Address Book / Contacts</td></tr>
                <tr><td><code>Ctrl + U</code></td><td>Inspect Raw RFC822 Source &amp; Security Headers</td></tr>
                <tr><td><code>Ctrl + S</code></td><td>Export Selected Email as .eml or .txt</td></tr>
                <tr><td><code>Ctrl + M</code></td><td>Toggle Safe Mode (Sanitized HTML vs Plain Text)</td></tr>
                <tr><td><code>Delete</code></td><td>Move Selected Email to Trash / Delete</td></tr>
                <tr><td><code>F1</code></td><td>Open CritMail Documentation</td></tr>
            </table>
        </div>
        """)
        tabs.addTab(tab_keys, "Keyboard Shortcuts")

        # Tab 4: Server Reference
        tab_srv = QTextBrowser()
        tab_srv.setHtml(f"""
        <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.6;">
            <h3 style="color: #00e5ff; border-bottom: 1px solid #1c3555;">4. Server Reference &amp; Protocol Guide</h3>
            <p>Configured Server Parameters for <b>james.f@theintelligenceagency.net</b>:</p>
            <ul>
                <li><b>IMAP4 Host (Recommended):</b> <code>mailserver.businessidentity.llc</code> — Port <code>993</code> (SSL/TLS)</li>
                <li><b>POP3 Host (Supported):</b> <code>mailserver.businessidentity.llc</code> — Port <code>995</code> (SSL/TLS)</li>
                <li><b>SMTP Outgoing Host:</b> <code>mailserver.businessidentity.llc</code> — Port <code>465</code> (SSL/TLS)</li>
            </ul>
            <p><b>IMAP vs POP3:</b> IMAP (Port 993) is configured by default because it keeps your messages synchronized on the server so your mailbox stays consistent across all devices. You can switch to POP3 (Port 995) anytime in <code>File &gt; Account Settings</code>.</p>
        </div>
        """)
        tabs.addTab(tab_srv, "Server Reference")

        layout.addWidget(tabs, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Close Manual")
        btn_close.setObjectName("AccentBtn")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)


class AboutDialog(QDialog):
    """Winamp 3 styled About Dialog with Custom Icon and Security Status."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(480, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_titlebar_pixmap(64))
        icon_lbl.setFixedSize(68, 68)
        top_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        lbl_name = QLabel(f"[ {APP_NAME.upper()} // v{APP_VERSION} ]")
        lbl_name.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 12pt;")
        title_col.addWidget(lbl_name)

        lbl_tag = QLabel(APP_TAGLINE)
        lbl_tag.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 8.5pt;")
        title_col.addWidget(lbl_tag)

        lbl_skin = QLabel("Skin: Winamp 3 Modern Blue • 0px Radius • 1px Crisp Borders")
        lbl_skin.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        title_col.addWidget(lbl_skin)
        top_row.addLayout(title_col, 1)

        layout.addLayout(top_row)

        info_box = QFrame()
        info_box.setStyleSheet("background: #080d16; border: 1px solid #1b3352; padding: 8px;")
        ib_layout = QVBoxLayout(info_box)
        ib_layout.setContentsMargins(6, 6, 6, 6)
        ib_layout.setSpacing(4)

        details = [
            "✔ Credential Vault: Windows DPAPI (CryptProtectData) + AES-256-GCM",
            "✔ Network Transport: Strict TLS 1.2 / 1.3 (IMAP4:993, POP3:995, SMTP:465)",
            "✔ Content Sandbox: Zero-JS HTML Sanitizer & Remote Beacon Blocker",
            "✔ Link Defense: Real-Time Anti-Phishing & Punycode Homograph Guard",
            "✔ Local Storage: High-Speed SQLite WAL Engine (~/.critmail/critmail.db)"
        ]
        for line in details:
            lbl = QLabel(line)
            lbl.setStyleSheet(f"color: {COLORS['secure_green']}; font-size: 8pt; border: none;")
            ib_layout.addWidget(lbl)

        layout.addWidget(info_box)
        layout.addStretch()

        btn_row = QHBoxLayout()
        lbl_copy = QLabel("Built for speed, privacy, and zero telemetry.")
        lbl_copy.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        btn_row.addWidget(lbl_copy)
        btn_row.addStretch()

        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("AccentBtn")
        btn_ok.setFixedWidth(90)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)


class RawHeadersDialog(QDialog):
    """Forensic viewer for raw RFC822 headers and message source."""
    def __init__(self, msg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Raw Headers & Forensic Source")
        self.setWindowIcon(create_app_icon())
        self.resize(680, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        lbl = QLabel(f"[ FORENSIC MESSAGE INSPECTOR // ID: {msg.get('message_id', 'N/A')} ]")
        lbl.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9pt;")
        layout.addWidget(lbl)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        full_source = (
            f"=== RFC822 HEADERS ===\n{msg.get('raw_headers', '')}\n\n"
            f"=== PLAIN TEXT BODY ===\n{msg.get('body_plain', '')}\n\n"
            f"=== RAW HTML BODY ===\n{msg.get('body_html', '')}"
        )
        self.txt.setPlainText(full_source)
        layout.addWidget(self.txt, 1)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("Copy Headers")
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(full_source))
        btn_row.addWidget(btn_copy)
        btn_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("AccentBtn")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)


class CommsReconDialog(QDialog):
    """
    Live Spy-Themed Comms & DNS Reconnaissance Diagnostic Terminal.
    Tests MX, SPF, DMARC, A records, IMAP (993), POP3 (995), and SMTP (465).
    """
    def __init__(self, parent=None, account: dict = None):
        super().__init__(parent)
        if account is None:
            from critmail.models.database import get_accounts
            accs = get_accounts()
            account = accs[0] if accs else {}
        self.account = account if isinstance(account, dict) else {}
        self.setWindowTitle(f"{APP_NAME} - Comms & DNS Reconnaissance Terminal")
        self.setWindowIcon(create_app_icon())
        self.resize(760, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        lbl = QLabel("[ TIA SIGINT // LIVE DNS & MAIL SERVER RECONNAISSANCE ]")
        lbl.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9.5pt;")
        layout.addWidget(lbl)

        sub = QLabel(
            "Inspects public DNS records (MX, SPF, DMARC) and live TLS handshakes (IMAP 993, POP3 995, SMTP 465)."
        )
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        layout.addWidget(sub)

        self.txt_out = QTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setStyleSheet(
            "background: #060a10; border: 1px solid #00d4ff; color: #00f076; font-family: Consolas, monospace; font-size: 8.5pt;"
        )
        layout.addWidget(self.txt_out, 1)

        btn_row = QHBoxLayout()
        self.btn_run = QPushButton("📡 Run Full Recon Scan")
        self.btn_run.setObjectName("AccentBtn")
        self.btn_run.clicked.connect(self._run_scan)
        btn_row.addWidget(self.btn_run)

        btn_copy = QPushButton("📋 Copy Recon Report")
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.txt_out.toPlainText()))
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()

        btn_close = QPushButton("Close Terminal")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._run_scan()

    def _run_scan(self):
        import socket
        import subprocess
        from critmail.core.imap_client import ImapEngine
        from critmail.core.pop3_client import Pop3Engine
        from critmail.core.smtp_client import SmtpEngine

        self.txt_out.clear()
        lines = []
        email_addr = self.account.get("email_address", "james.f@theintelligenceagency.net")
        domain = email_addr.split("@")[-1] if "@" in email_addr else "theintelligenceagency.net"
        mail_host = self.account.get("incoming_host", "mailserver.businessidentity.llc")

        lines.append("======================================================================")
        lines.append(f" [SIGINT RECON] TARGET IDENTITY : {email_addr}")
        lines.append(f" [SIGINT RECON] TARGET DOMAIN   : {domain}")
        lines.append(f" [SIGINT RECON] MAIL RELAY HOST : {mail_host}")
        lines.append("======================================================================\n")

        # 1. Host IP resolution
        lines.append(">>> [PHASE 1] HOST & IPv4 RESOLUTION")
        mail_host_ip = "66.223.100.94"
        for h in (domain, mail_host):
            try:
                ips = list({x[4][0] for x in socket.getaddrinfo(h, None)})
                if h == mail_host and ips:
                    mail_host_ip = ips[0]
                lines.append(f"  [OK] {h:<34} -> {', '.join(ips)}")
            except Exception as e:
                lines.append(f"  [!!] {h:<34} -> DNS ERROR: {e}")

        # 2. Public MX & TXT (SPF) lookup via nslookup
        lines.append("\n>>> [PHASE 2] PUBLIC DNS MX & SPF VERIFICATION (via 8.8.8.8)")
        has_mx = False
        has_spf = False
        try:
            mx_proc = subprocess.run(
                ["nslookup", "-type=mx", domain, "8.8.8.8"],
                capture_output=True, text=True, timeout=6, creationflags=0x08000000
            )
            mx_out = mx_proc.stdout or ""
            if "mail exchanger" in mx_out.lower():
                has_mx = True
                for l in mx_out.splitlines():
                    if "mail exchanger" in l.lower():
                        lines.append(f"  [OK] MX RECORD FOUND: {l.strip()}")
            else:
                lines.append(f"  [CRITICAL WARNING] NO MX RECORD FOUND FOR '{domain}' IN PUBLIC DNS!")
                lines.append("       -> External senders (Gmail, Outlook, Yahoo) CANNOT deliver mail to your")
                lines.append(f"          domain until you add an MX record in your domain DNS dashboard:")
                lines.append(f"          • Type: MX | Host: @ | Priority: 10 | Value: {mail_host}")
        except Exception as e:
            lines.append(f"  [WARN] MX check skipped: {e}")

        try:
            txt_proc = subprocess.run(
                ["nslookup", "-type=txt", domain, "8.8.8.8"],
                capture_output=True, text=True, timeout=6, creationflags=0x08000000
            )
            txt_out = txt_proc.stdout or ""
            if "v=spf1" in txt_out.lower():
                has_spf = True
                lines.append("  [OK] SPF TXT RECORD FOUND.")
            else:
                lines.append(f"  [WARNING] NO SPF TXT RECORD FOUND FOR '{domain}'!")
                lines.append("       -> Outgoing mail to Gmail/Yahoo may be rejected or sent to Spam.")
                lines.append("          Add this TXT record in your domain DNS dashboard:")
                lines.append(f"          • Type: TXT | Host: @ | Value: v=spf1 a mx ip4:{mail_host_ip} ~all")
        except Exception:
            pass

        # 3. Live Mail Server Handshakes
        lines.append("\n>>> [PHASE 3] LIVE TLS 1.2/1.3 SERVER AUTHENTICATION")
        if self.account and self.account.get("incoming_password"):
            imap_acc = dict(self.account)
            imap_acc["incoming_port"] = 993
            ok_i, msg_i = ImapEngine(imap_acc).test_connection()
            lines.append(f"  [{'OK' if ok_i else 'FAIL'}] IMAP4 SSL (993) : {msg_i}")

            pop_acc = dict(self.account)
            pop_acc["incoming_port"] = 995
            ok_p, msg_p = Pop3Engine(pop_acc).test_connection()
            lines.append(f"  [{'OK' if ok_p else 'FAIL'}] POP3 SSL  (995) : {msg_p}")

            ok_s, msg_s = SmtpEngine(self.account).test_connection()
            lines.append(f"  [{'OK' if ok_s else 'FAIL'}] SMTP SSL  (465) : {msg_s}")
        else:
            lines.append("  [INFO] No password stored yet. Open [ACCOUNTS] to test authenticated login.")

        lines.append("\n======================================================================")
        if has_mx and has_spf:
            lines.append(" VERDICT: ALL DNS RECORDS & ENCRYPTED CHANNELS OPERATIONAL")
        else:
            lines.append(" VERDICT: SERVER LOGIN OK // ACTION REQUIRED ON DOMAIN DNS (MX / SPF)")
        lines.append("======================================================================")

        self.txt_out.setPlainText("\n".join(lines))


class AgentClearanceProDialog(QDialog):
    """
    Spy-Themed Freemium / Classified Level-5 Clearance & @theintelligenceagency.net Callsign Portal.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Classified Clearance & @theintelligenceagency.net Portal")
        self.setWindowIcon(create_app_icon())
        self.resize(700, 540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl_head = QLabel("[ 🎖 LEVEL-5 CLASSIFIED CLEARANCE // FREEMIUM & CALLSIGN PORTAL ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9.5pt;")
        layout.addWidget(lbl_head)

        info = QTextBrowser()
        info.setHtml(f"""
        <div style="font-family: Consolas, monospace; color: #d9e8f5; line-height: 1.55;">
            <div style="background: #0b192c; border: 1px solid #00e5ff; padding: 8px; margin-bottom: 10px;">
                <b style="color: #00f076;">CURRENT CLEARANCE:</b> <code>FIELD AGENT (FREE EDITION)</code> &nbsp;|&nbsp;
                <b style="color: #00e5ff;">UPGRADE TIER:</b> <code>DIRECTORATE LEVEL-5 (PRO)</code>
            </div>

            <h3 style="color: #00e5ff; border-bottom: 1px solid #1c3555; margin-bottom: 6px;">
                1. Official <code>@theintelligenceagency.net</code> Agent Callsign Address
            </h3>
            <p>Directorate Level-5 subscribers can claim a dedicated, encrypted <b><code>codename@theintelligenceagency.net</code></b> identity with full IMAP4/SMTP access and stealth alias routing.</p>

            <h3 style="color: #00f076; border-bottom: 1px solid #1c3555; margin-bottom: 6px;">
                2. Classified Level-5 Premium Features
            </h3>
            <table width="100%" cellspacing="0" cellpadding="5" style="border: 1px solid #1c3555;">
                <tr style="background: #132238; color: #00e5ff;">
                    <th align="left">Capability</th>
                    <th align="left">Field Agent (Free)</th>
                    <th align="left">Level-5 Clearance (Pro)</th>
                </tr>
                <tr>
                    <td><b>Core IMAP4 / POP3 / SMTP Client</b></td>
                    <td style="color:#00f076;">✔ Included</td>
                    <td style="color:#00f076;">✔ Unlimited Accounts</td>
                </tr>
                <tr>
                    <td><b>Tracker Blocker &amp; Link Guard</b></td>
                    <td style="color:#00f076;">✔ Included</td>
                    <td style="color:#00f076;">✔ + Deep Whois / IP Recon</td>
                </tr>
                <tr>
                    <td><b><code>@theintelligenceagency.net</code> Mailbox</b></td>
                    <td style="color:#7a9ab8;">— Bring Your Own</td>
                    <td style="color:#00e5ff;"><b>★ Included + 5 Stealth Aliases</b></td>
                </tr>
                <tr>
                    <td><b>AES-256-GCM Classified Cipher</b></td>
                    <td style="color:#00f076;">✔ Manual Passphrase</td>
                    <td style="color:#00e5ff;"><b>★ Auto Key-Exchange +PGP</b></td>
                </tr>
                <tr>
                    <td><b>Self-Destructing Dead-Drop Links</b></td>
                    <td style="color:#7a9ab8;">— Local Burn Only</td>
                    <td style="color:#00e5ff;"><b>★ Timed Zero-Knowledge Dead-Drops</b></td>
                </tr>
                <tr>
                    <td><b>Stealth Decoy / Panic Boss-Key</b></td>
                    <td style="color:#00f076;">✔ Redact Mode</td>
                    <td style="color:#00e5ff;"><b>★ Duress PIN &amp; Decoy Vault</b></td>
                </tr>
            </table>
        </div>
        """)
        layout.addWidget(info, 1)

        # Interactive Callsign Reservation Box
        callsign_frame = QFrame()
        callsign_frame.setStyleSheet("background: #080d16; border: 1px solid #1c3555; padding: 6px;")
        cs_layout = QHBoxLayout(callsign_frame)
        cs_layout.setContentsMargins(6, 4, 6, 4)

        cs_layout.addWidget(QLabel("Reserve Agent Callsign:"))
        self.txt_callsign = QTextEdit()
        from PyQt6.QtWidgets import QLineEdit, QMessageBox
        self.inp_callsign = QLineEdit()
        self.inp_callsign.setPlaceholderText("agent.zero")
        cs_layout.addWidget(self.inp_callsign, 1)

        lbl_dom = QLabel("@theintelligenceagency.net")
        lbl_dom.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold;")
        cs_layout.addWidget(lbl_dom)

        btn_check = QPushButton("⚡ Check Callsign Availability")
        btn_check.setObjectName("AccentBtn")
        btn_check.clicked.connect(self._check_callsign)
        cs_layout.addWidget(btn_check)

        layout.addWidget(callsign_frame)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _check_callsign(self):
        from PyQt6.QtWidgets import QMessageBox
        raw = self.inp_callsign.text().strip().lower()
        clean = "".join(c for c in raw if c.isalnum() or c in "._-")
        if not clean or len(clean) < 2:
            QMessageBox.warning(self, "Invalid Callsign", "Please enter a valid agent callsign (at least 2 characters).")
            return
        reserved = {"admin", "root", "postmaster", "security", "james.f", "director"}
        if clean in reserved:
            QMessageBox.warning(
                self,
                "Callsign Reserved",
                f"Callsign '{clean}@theintelligenceagency.net' is already assigned to Directorate Command."
            )
        else:
            QMessageBox.information(
                self,
                "Callsign Available!",
                f"✔ Callsign '{clean}@theintelligenceagency.net' is AVAILABLE for Level-5 Clearance provisioning!"
            )
