"""
CritMail UI - Full-Featured Compose Message Dialog
Supports To/Cc/Bcc, Reply/Reply-All/Forward, Save to Drafts, Address Book Picker,
Signature insertion, and Attachment Safety Analysis.
"""
import datetime
from email.utils import formatdate, make_msgid, getaddresses
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QInputDialog
)
from critmail.config import COLORS
from critmail.ui.icon_factory import create_app_icon
from critmail.ui.contacts_dialog import ContactsDialog
from critmail.models.database import (
    get_accounts, get_folder_by_type, save_message,
    get_setting, add_or_update_contact
)
from critmail.core.smtp_client import SmtpEngine
from critmail.core.pop3_client import DANGEROUS_EXTENSIONS
from critmail.security.crypto import encrypt_classified_message, has_classified_cipher


class SmtpSendThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account: dict, to_list, subject, body, attachments, cc_list=None, bcc_list=None):
        super().__init__()
        self.account = account
        self.to_list = to_list
        self.subject = subject
        self.body = body
        self.attachments = attachments
        self.cc_list = cc_list
        self.bcc_list = bcc_list

    def run(self):
        try:
            engine = SmtpEngine(self.account)
            engine.send_message(
                to_addrs=self.to_list,
                subject=self.subject,
                body_text=self.body,
                cc_addrs=self.cc_list,
                bcc_addrs=self.bcc_list,
                attachment_paths=self.attachments
            )
            self.finished.emit(True, "Message delivered successfully via TLS!")
        except Exception as e:
            self.finished.emit(False, str(e))


class ComposeDialog(QDialog):
    """Winamp 3 styled full-featured email composer window."""
    def __init__(
        self,
        parent=None,
        reply_to_msg=None,
        mode: str = "compose",
        initial_to: str = "",
        active_account_id: int = None
    ):
        """
        mode: 'compose', 'reply', 'reply_all', 'forward', 'draft'
        """
        super().__init__(parent)
        self.setWindowTitle("CritMail - Compose Classified Transmission")
        self.setWindowIcon(create_app_icon())
        self.resize(720, 590)
        self.attachments = []
        self.accounts = get_accounts()
        self.mode = mode

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header Badge
        lbl_head = QLabel("[ COMPOSE // SECURE SMTP & AES-256 CIPHER TRANSMISSION ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 8.5pt;")
        layout.addWidget(lbl_head)

        grid = QGridLayout()
        grid.setSpacing(5)

        # From Account
        grid.addWidget(QLabel("From:"), 0, 0)
        self.combo_from = QComboBox()
        selected_idx = 0
        for idx, acc in enumerate(self.accounts):
            self.combo_from.addItem(f"{acc['name']} <{acc['email_address']}>", acc)
            if active_account_id and acc["id"] == active_account_id:
                selected_idx = idx
        if self.accounts:
            self.combo_from.setCurrentIndex(selected_idx)
        grid.addWidget(self.combo_from, 0, 1, 1, 2)

        # To + Address Book Button
        grid.addWidget(QLabel("To:"), 1, 0)
        self.txt_to = QLineEdit()
        self.txt_to.setPlaceholderText("recipient@example.com (comma separated)")
        if initial_to:
            self.txt_to.setText(initial_to)
        grid.addWidget(self.txt_to, 1, 1)

        btn_contacts = QPushButton("📇 Dossiers")
        btn_contacts.setFixedWidth(95)
        btn_contacts.clicked.connect(lambda: self._pick_contact(self.txt_to))
        grid.addWidget(btn_contacts, 1, 2)

        # Cc
        grid.addWidget(QLabel("Cc:"), 2, 0)
        self.txt_cc = QLineEdit()
        self.txt_cc.setPlaceholderText("cc@example.com (optional)")
        grid.addWidget(self.txt_cc, 2, 1)

        btn_cc_contacts = QPushButton("📇 Add Cc")
        btn_cc_contacts.setFixedWidth(95)
        btn_cc_contacts.clicked.connect(lambda: self._pick_contact(self.txt_cc))
        grid.addWidget(btn_cc_contacts, 2, 2)

        # Bcc
        grid.addWidget(QLabel("Bcc:"), 3, 0)
        self.txt_bcc = QLineEdit()
        self.txt_bcc.setPlaceholderText("bcc@example.com (optional)")
        grid.addWidget(self.txt_bcc, 3, 1, 1, 2)

        # Subject
        grid.addWidget(QLabel("Subject:"), 4, 0)
        self.txt_subject = QLineEdit()
        self.txt_subject.setPlaceholderText("Subject line...")
        grid.addWidget(self.txt_subject, 4, 1, 1, 2)

        layout.addLayout(grid)

        # Body Editor (Monospace)
        self.txt_body = QTextEdit()
        self.txt_body.setPlaceholderText("Type your secure message here...")
        layout.addWidget(self.txt_body, 1)

        # Attachment bar
        att_row = QHBoxLayout()
        self.lbl_att = QLabel("Attachments: None")
        self.lbl_att.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        att_row.addWidget(self.lbl_att, 1)

        self.btn_clear_att = QPushButton("Clear Attachments")
        self.btn_clear_att.setFixedHeight(18)
        self.btn_clear_att.setVisible(False)
        self.btn_clear_att.clicked.connect(self._clear_attachments)
        att_row.addWidget(self.btn_clear_att)
        layout.addLayout(att_row)

        # Status
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 8pt;")
        layout.addWidget(self.lbl_status)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.btn_attach = QPushButton("📎 Attach File")
        self.btn_attach.clicked.connect(self._attach_file)
        btn_layout.addWidget(self.btn_attach)

        self.btn_encrypt = QPushButton("🔐 Encrypt Body (TIA Cipher)")
        self.btn_encrypt.setToolTip("Armor message body with AES-256-GCM PBKDF2 Classified Cipher")
        self.btn_encrypt.clicked.connect(self._encrypt_body_cipher)
        btn_layout.addWidget(self.btn_encrypt)

        self.btn_draft = QPushButton("💾 Save Draft")
        self.btn_draft.clicked.connect(self._save_draft)
        btn_layout.addWidget(self.btn_draft)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Discard")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_send = QPushButton("⚡ Send Transmission")
        self.btn_send.setObjectName("AccentBtn")
        self.btn_send.clicked.connect(self._send_mail)
        btn_layout.addWidget(self.btn_send)

        layout.addLayout(btn_layout)

        # Insert signature or setup reply/forward
        sig = get_setting(
            "signature",
            "-- \nJames F.\nThe Intelligence Agency\njames.f@theintelligenceagency.net"
        )
        if reply_to_msg:
            self._setup_from_message(reply_to_msg, mode, sig)
        elif sig:
            self.txt_body.setPlainText(f"\n\n{sig}")

    def _encrypt_body_cipher(self):
        current_text = self.txt_body.toPlainText().strip()
        if not current_text:
            QMessageBox.information(self, "Empty Body", "Please type a message body before encrypting.")
            return
        if has_classified_cipher(current_text):
            QMessageBox.information(self, "Already Encrypted", "This message body is already armored with TIA Classified Cipher.")
            return

        passphrase, ok = QInputDialog.getText(
            self,
            "TIA Classified Cipher (AES-256-GCM)",
            "Enter shared Agent Passphrase to encrypt this transmission:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not passphrase:
            return

        armored = encrypt_classified_message(current_text, passphrase)
        self.txt_body.setPlainText(armored)
        cur_subj = self.txt_subject.text().strip()
        if "[CLASSIFIED]" not in cur_subj.upper():
            self.txt_subject.setText(f"[CLASSIFIED] {cur_subj}" if cur_subj else "[CLASSIFIED TRANSMISSION]")
        self.lbl_status.setStyleSheet(f"color: {COLORS['secure_green']}; font-weight: bold;")
        self.lbl_status.setText("🔐 Body encrypted with AES-256-GCM (PBKDF2-SHA256).")

    def _pick_contact(self, target_line_edit: QLineEdit):
        dlg = ContactsDialog(self, picker_mode=True)
        def _on_picked(addr: str):
            existing = target_line_edit.text().strip()
            if existing:
                target_line_edit.setText(f"{existing}, {addr}")
            else:
                target_line_edit.setText(addr)
        dlg.contact_selected.connect(_on_picked)
        dlg.exec()

    def _setup_from_message(self, msg: dict, mode: str, sig: str):
        subj = msg.get("subject", "")
        orig_sender = msg.get("sender", "")
        orig_recip = msg.get("recipient", "")
        orig_cc = msg.get("cc", "")
        orig_date = msg.get("date", "")
        orig_body = msg.get("body_plain", "")
        sig_block = f"\n\n{sig}\n" if sig else "\n"

        if mode in ("reply", "reply_all"):
            self.txt_to.setText(orig_sender)
            if mode == "reply_all" and orig_cc:
                self.txt_cc.setText(orig_cc)
            if not subj.lower().startswith("re:"):
                subj = "Re: " + subj
            self.txt_subject.setText(subj)
            quoted = "\n".join(f"> {line}" for line in orig_body.splitlines())
            self.txt_body.setPlainText(
                f"{sig_block}\n--- On {orig_date}, {orig_sender} wrote: ---\n{quoted}"
            )
        elif mode == "forward":
            if not subj.lower().startswith("fwd:"):
                subj = "Fwd: " + subj
            self.txt_subject.setText(subj)
            self.txt_body.setPlainText(
                f"{sig_block}\n---------- Forwarded Message ----------\n"
                f"From: {orig_sender}\n"
                f"Date: {orig_date}\n"
                f"Subject: {msg.get('subject', '')}\n"
                f"To: {orig_recip}\n\n"
                f"{orig_body}"
            )
        elif mode == "draft":
            self.txt_to.setText(orig_recip)
            self.txt_cc.setText(orig_cc)
            self.txt_bcc.setText(msg.get("bcc", ""))
            self.txt_subject.setText(subj)
            self.txt_body.setPlainText(orig_body)

    def _attach_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        warn_exec = get_setting("warn_exec_attachments", "1") == "1"
        if files:
            for f in files:
                ext = Path(f).suffix.lower()
                if warn_exec and ext in DANGEROUS_EXTENSIONS:
                    res = QMessageBox.warning(
                        self,
                        "Executable File Warning",
                        f"Warning: '{Path(f).name}' is an executable script or binary file. Proceed?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if res != QMessageBox.StandardButton.Yes:
                        continue
                if f not in self.attachments:
                    self.attachments.append(f)

            names = [Path(p).name for p in self.attachments]
            self.lbl_att.setText("Attachments: " + ", ".join(names))
            self.btn_clear_att.setVisible(bool(self.attachments))

    def _clear_attachments(self):
        self.attachments.clear()
        self.lbl_att.setText("Attachments: None")
        self.btn_clear_att.setVisible(False)

    def _save_draft(self):
        if not self.accounts:
            return
        selected_acc = self.combo_from.currentData()
        drafts_folder = get_folder_by_type(selected_acc["id"], "drafts")
        if not drafts_folder:
            return

        msg_id = make_msgid(domain="critmail.draft")
        body = self.txt_body.toPlainText()
        save_message(
            account_id=selected_acc["id"],
            folder_id=drafts_folder["id"],
            server_uid=f"draft-{msg_id}",
            message_id=msg_id,
            subject=self.txt_subject.text().strip() or "(Draft - No Subject)",
            sender=selected_acc["email_address"],
            recipient=self.txt_to.text().strip(),
            cc=self.txt_cc.text().strip(),
            bcc=self.txt_bcc.text().strip(),
            date=formatdate(localtime=True),
            body_plain=body,
            body_html="",
            size_bytes=len(body.encode("utf-8")),
            raw_headers="X-CritMail-Draft: True",
            has_attachments=bool(self.attachments),
            security_verdict="CLEAN"
        )
        QMessageBox.information(self, "Draft Saved", "Your message has been saved to the Drafts folder.")
        self.accept()

    @staticmethod
    def _extract_addr_list(raw_str: str) -> list[str]:
        if not raw_str.strip():
            return []
        parsed = getaddresses([raw_str])
        out = []
        for name, addr in parsed:
            if addr:
                out.append(f"{name} <{addr}>" if name else addr)
        return out

    def _send_mail(self):
        if not self.accounts:
            QMessageBox.critical(self, "No Account", "Please set up an email account first!")
            return

        selected_acc = self.combo_from.currentData()
        if not selected_acc.get("smtp_password") and not selected_acc.get("incoming_password"):
            QMessageBox.warning(
                self,
                "Password Required",
                f"Please enter your password for {selected_acc['email_address']} in Account Settings before sending."
            )
            return

        to_raw = self.txt_to.text().strip()
        if not to_raw:
            QMessageBox.warning(self, "Missing Recipient", "Please enter at least one recipient email address.")
            return

        to_list = self._extract_addr_list(to_raw)
        cc_list = self._extract_addr_list(self.txt_cc.text())
        bcc_list = self._extract_addr_list(self.txt_bcc.text())
        subject = self.txt_subject.text().strip() or "(No Subject)"
        body = self.txt_body.toPlainText()

        # Auto-save recipients to Contacts if enabled
        if get_setting("auto_save_contacts", "1") == "1":
            for name, addr in getaddresses([to_raw, self.txt_cc.text()]):
                if addr and "@" in addr:
                    try:
                        add_or_update_contact(name.strip() or addr.split("@")[0], addr.strip())
                    except Exception:
                        pass

        self.btn_send.setEnabled(False)
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_accent']};")
        self.lbl_status.setText("Transmitting via secure SMTP with TLS...")

        self._thread = SmtpSendThread(selected_acc, to_list, subject, body, self.attachments, cc_list, bcc_list)
        self._thread.finished.connect(self._on_send_done)
        self._thread.start()

    def _on_send_done(self, success: bool, msg: str):
        self.btn_send.setEnabled(True)
        if success:
            QMessageBox.information(self, "Message Sent", msg)
            self.accept()
        else:
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger_red']};")
            self.lbl_status.setText("✖ " + msg)
