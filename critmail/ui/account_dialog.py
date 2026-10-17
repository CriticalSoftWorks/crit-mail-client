"""
CritMail UI - Account Setup and Management Dialog
Supports IMAP (993) and POP3 (995) configuration with live TLS connection testing.
"""
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox, QGroupBox
)
from critmail.config import COLORS
from critmail.models.database import add_account, update_account, delete_account, get_accounts
from critmail.core.pop3_client import Pop3Engine
from critmail.core.imap_client import ImapEngine
from critmail.core.smtp_client import SmtpEngine

class ConnectionTestThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, account_data: dict):
        super().__init__()
        self.account_data = account_data

    def run(self):
        try:
            proto = self.account_data.get("account_type", "IMAP").upper()
            if proto == "IMAP":
                engine = ImapEngine(self.account_data)
            else:
                engine = Pop3Engine(self.account_data)
            in_ok, in_msg = engine.test_connection()
            if not in_ok:
                self.finished.emit(False, in_msg)
                return

            smtp_engine = SmtpEngine(self.account_data)
            smtp_ok, smtp_msg = smtp_engine.test_connection()
            if not smtp_ok:
                self.finished.emit(False, f"{in_msg} | {smtp_msg}")
                return

            self.finished.emit(True, f"{proto} & SMTP Verified! Both TLS handshakes succeeded.")
        except Exception as e:
            self.finished.emit(False, str(e))

class AccountDialog(QDialog):
    """Winamp 3 style account configuration modal."""
    def __init__(self, parent=None, edit_account_id: int = None):
        super().__init__(parent)
        self.setWindowTitle("CritMail - Account Configuration")
        self.setFixedSize(580, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        self.accounts = get_accounts()
        self.current_account_id = edit_account_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header Badge + Account Switcher
        top_row = QHBoxLayout()
        lbl_head = QLabel("[ ACCOUNT SETUP // IMAP4 & POP3 ENGINE ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9pt;")
        top_row.addWidget(lbl_head)
        top_row.addStretch()

        top_row.addWidget(QLabel("Select Profile:"))
        self.combo_profile = QComboBox()
        self.combo_profile.setMinimumWidth(210)
        self.combo_profile.currentIndexChanged.connect(self._on_profile_selected)
        top_row.addWidget(self.combo_profile)
        layout.addLayout(top_row)

        # General Identity
        grp_id = QGroupBox("IDENTITY")
        id_layout = QGridLayout(grp_id)
        id_layout.setSpacing(6)

        id_layout.addWidget(QLabel("Account Label:"), 0, 0)
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Intelligence Agency (IMAP)")
        id_layout.addWidget(self.txt_name, 0, 1)

        id_layout.addWidget(QLabel("Email Address:"), 1, 0)
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("james.f@theintelligenceagency.net")
        id_layout.addWidget(self.txt_email, 1, 1)
        layout.addWidget(grp_id)

        # Incoming Server
        grp_in = QGroupBox("INCOMING SERVER (IMAP 993 OR POP3 995)")
        in_layout = QGridLayout(grp_in)
        in_layout.setSpacing(6)

        in_layout.addWidget(QLabel("Protocol:"), 0, 0)
        self.combo_proto = QComboBox()
        self.combo_proto.addItems(["IMAP", "POP3"])
        self.combo_proto.currentTextChanged.connect(self._on_proto_changed)
        in_layout.addWidget(self.combo_proto, 0, 1)

        in_layout.addWidget(QLabel("Server Host:"), 1, 0)
        self.txt_in_host = QLineEdit()
        self.txt_in_host.setPlaceholderText("mailserver.businessidentity.llc")
        in_layout.addWidget(self.txt_in_host, 1, 1)

        in_layout.addWidget(QLabel("Port:"), 1, 2)
        self.txt_in_port = QLineEdit("993")
        self.txt_in_port.setFixedWidth(55)
        in_layout.addWidget(self.txt_in_port, 1, 3)

        in_layout.addWidget(QLabel("Security:"), 2, 0)
        self.combo_in_sec = QComboBox()
        self.combo_in_sec.addItems(["SSL/TLS", "STARTTLS", "PLAIN"])
        in_layout.addWidget(self.combo_in_sec, 2, 1)

        in_layout.addWidget(QLabel("Username:"), 3, 0)
        self.txt_in_user = QLineEdit()
        in_layout.addWidget(self.txt_in_user, 3, 1, 1, 3)

        in_layout.addWidget(QLabel("Password:"), 4, 0)
        self.txt_in_pass = QLineEdit()
        self.txt_in_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_in_pass.setPlaceholderText("Enter your mailbox password (encrypted with Windows DPAPI)")
        in_layout.addWidget(self.txt_in_pass, 4, 1, 1, 3)

        self.chk_keep = QCheckBox("Keep messages synchronized on server (Recommended)")
        self.chk_keep.setChecked(True)
        in_layout.addWidget(self.chk_keep, 5, 0, 1, 4)
        layout.addWidget(grp_in)

        # Outgoing SMTP Server
        grp_out = QGroupBox("OUTGOING SERVER (SMTP 465 SSL/TLS)")
        out_layout = QGridLayout(grp_out)
        out_layout.setSpacing(6)

        out_layout.addWidget(QLabel("Server Host:"), 0, 0)
        self.txt_smtp_host = QLineEdit()
        self.txt_smtp_host.setPlaceholderText("mailserver.businessidentity.llc")
        out_layout.addWidget(self.txt_smtp_host, 0, 1)

        out_layout.addWidget(QLabel("Port:"), 0, 2)
        self.txt_smtp_port = QLineEdit("465")
        self.txt_smtp_port.setFixedWidth(55)
        out_layout.addWidget(self.txt_smtp_port, 0, 3)

        out_layout.addWidget(QLabel("Security:"), 1, 0)
        self.combo_smtp_sec = QComboBox()
        self.combo_smtp_sec.addItems(["SSL/TLS", "STARTTLS", "PLAIN"])
        out_layout.addWidget(self.combo_smtp_sec, 1, 1)

        self.chk_same_cred = QCheckBox("Use incoming credentials for SMTP")
        self.chk_same_cred.setChecked(True)
        self.chk_same_cred.stateChanged.connect(self._toggle_smtp_creds)
        out_layout.addWidget(self.chk_same_cred, 2, 0, 1, 4)

        out_layout.addWidget(QLabel("SMTP User:"), 3, 0)
        self.txt_smtp_user = QLineEdit()
        self.txt_smtp_user.setEnabled(False)
        out_layout.addWidget(self.txt_smtp_user, 3, 1, 1, 3)

        out_layout.addWidget(QLabel("SMTP Pass:"), 4, 0)
        self.txt_smtp_pass = QLineEdit()
        self.txt_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_smtp_pass.setEnabled(False)
        out_layout.addWidget(self.txt_smtp_pass, 4, 1, 1, 3)
        layout.addWidget(grp_out)

        # Status Label for Test Connection
        self.lbl_status = QLabel("Ready. Enter your password and click Test Connection or Save Account.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        layout.addWidget(self.lbl_status)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.btn_test = QPushButton("⚡ Test Connection")
        self.btn_test.clicked.connect(self._test_connection)
        btn_layout.addWidget(self.btn_test)

        self.btn_delete = QPushButton("✕ Delete Account")
        self.btn_delete.clicked.connect(self._delete_current_account)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Account")
        self.btn_save.setObjectName("AccentBtn")
        self.btn_save.clicked.connect(self._save_account)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        self._populate_profiles()

    def _populate_profiles(self):
        self.combo_profile.blockSignals(True)
        self.combo_profile.clear()
        for acc in self.accounts:
            self.combo_profile.addItem(f"{acc['name']} ({acc['email_address']})", acc["id"])
        self.combo_profile.addItem("+ Add New Account...", None)
        self.combo_profile.blockSignals(False)

        if self.accounts:
            idx = 0
            if self.current_account_id:
                for i, acc in enumerate(self.accounts):
                    if acc["id"] == self.current_account_id:
                        idx = i
                        break
            self.combo_profile.setCurrentIndex(idx)
            self._load_account_into_form(self.accounts[idx])
        else:
            self.combo_profile.setCurrentIndex(0)
            self.btn_delete.setEnabled(False)

    def _on_profile_selected(self, index: int):
        acc_id = self.combo_profile.itemData(index)
        self.current_account_id = acc_id
        if acc_id is None:
            self.btn_delete.setEnabled(False)
            # Clear form for new account
            self.txt_name.clear()
            self.txt_email.clear()
            self.combo_proto.setCurrentText("IMAP")
            self.txt_in_host.clear()
            self.txt_in_port.setText("993")
            self.txt_in_user.clear()
            self.txt_in_pass.clear()
            self.txt_smtp_host.clear()
            self.txt_smtp_port.setText("465")
            self.chk_same_cred.setChecked(True)
        else:
            self.btn_delete.setEnabled(True)
            for acc in self.accounts:
                if acc["id"] == acc_id:
                    self._load_account_into_form(acc)
                    break

    def _load_account_into_form(self, acc: dict):
        self.current_account_id = acc["id"]
        self.btn_delete.setEnabled(True)
        self.txt_name.setText(acc.get("name", ""))
        self.txt_email.setText(acc.get("email_address", ""))
        self.combo_proto.setCurrentText(acc.get("account_type", "IMAP").upper())
        self.txt_in_host.setText(acc.get("incoming_host", ""))
        self.txt_in_port.setText(str(acc.get("incoming_port", 993)))
        self.combo_in_sec.setCurrentText(acc.get("incoming_security", "SSL/TLS"))
        in_u = acc.get("incoming_username", "")
        in_p = acc.get("incoming_password", "")
        self.txt_in_user.setText(in_u)
        self.txt_in_pass.setText(in_p)
        self.chk_keep.setChecked(bool(acc.get("keep_on_server", 1)))
        self.txt_smtp_host.setText(acc.get("smtp_host", ""))
        self.txt_smtp_port.setText(str(acc.get("smtp_port", 465)))
        self.combo_smtp_sec.setCurrentText(acc.get("smtp_security", "SSL/TLS"))
        sm_u = acc.get("smtp_username", "")
        sm_p = acc.get("smtp_password", "")
        self.txt_smtp_user.setText(sm_u)
        self.txt_smtp_pass.setText(sm_p)
        same = (not sm_u or sm_u == in_u) and (not sm_p or sm_p == in_p)
        self.chk_same_cred.setChecked(same)

    def _delete_current_account(self):
        if self.current_account_id is None:
            return
        res = QMessageBox.question(
            self,
            "Delete Account",
            f"Are you sure you want to remove '{self.txt_email.text()}' and its local folder cache from CritMail?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            delete_account(self.current_account_id)
            self.accept()

    def _on_proto_changed(self, proto_text: str):
        if proto_text == "IMAP" and self.txt_in_port.text() == "995":
            self.txt_in_port.setText("993")
        elif proto_text == "POP3" and self.txt_in_port.text() == "993":
            self.txt_in_port.setText("995")

    def _toggle_smtp_creds(self, state):
        custom = (state != Qt.CheckState.Checked.value)
        self.txt_smtp_user.setEnabled(custom)
        self.txt_smtp_pass.setEnabled(custom)

    def _gather_account_dict(self) -> dict:
        email_addr = self.txt_email.text().strip()
        in_user = self.txt_in_user.text().strip() or email_addr
        in_pass = self.txt_in_pass.text()
        if self.chk_same_cred.isChecked():
            smtp_user = in_user
            smtp_pass = in_pass
        else:
            smtp_user = self.txt_smtp_user.text().strip()
            smtp_pass = self.txt_smtp_pass.text()

        default_in_port = 993 if self.combo_proto.currentText() == "IMAP" else 995
        try:
            in_port = int(self.txt_in_port.text().strip() or str(default_in_port))
        except ValueError:
            in_port = default_in_port

        try:
            smtp_port = int(self.txt_smtp_port.text().strip() or "465")
        except ValueError:
            smtp_port = 465

        return {
            "id": self.current_account_id or 0,
            "name": self.txt_name.text().strip() or "Mail Account",
            "email_address": email_addr,
            "account_type": self.combo_proto.currentText(),
            "incoming_host": self.txt_in_host.text().strip(),
            "incoming_port": in_port,
            "incoming_security": self.combo_in_sec.currentText(),
            "incoming_username": in_user,
            "incoming_password": in_pass,
            "smtp_host": self.txt_smtp_host.text().strip(),
            "smtp_port": smtp_port,
            "smtp_security": self.combo_smtp_sec.currentText(),
            "smtp_username": smtp_user,
            "smtp_password": smtp_pass,
            "keep_on_server": self.chk_keep.isChecked()
        }

    def _test_connection(self):
        acc_data = self._gather_account_dict()
        if not acc_data["incoming_host"]:
            self.lbl_status.setText("⚠ Please enter Incoming Server Host.")
            return
        if not acc_data["incoming_password"]:
            self.lbl_status.setStyleSheet(f"color: {COLORS['warning_orange']}; font-weight: bold;")
            self.lbl_status.setText("⚠ Please enter your account password to test authentication.")
            return

        self.lbl_status.setStyleSheet(f"color: {COLORS['text_accent']};")
        self.lbl_status.setText(f"Testing {acc_data['account_type']} ({acc_data['incoming_port']}) & SMTP ({acc_data['smtp_port']}) TLS handshakes...")
        self.btn_test.setEnabled(False)

        self._thread = ConnectionTestThread(acc_data)
        self._thread.finished.connect(self._on_test_done)
        self._thread.start()

    def _on_test_done(self, success: bool, msg: str):
        self.btn_test.setEnabled(True)
        if success:
            self.lbl_status.setStyleSheet(f"color: {COLORS['secure_green']}; font-weight: bold;")
            self.lbl_status.setText("✔ " + msg)
        else:
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger_red']}; font-weight: bold;")
            self.lbl_status.setText("✖ " + msg)

    def _save_account(self):
        acc = self._gather_account_dict()
        if not acc["email_address"] or not acc["incoming_host"] or not acc["smtp_host"]:
            QMessageBox.warning(self, "Missing Fields", "Please provide email address, incoming host, and SMTP host.")
            return

        if self.current_account_id is not None:
            update_account(
                account_id=self.current_account_id,
                name=acc["name"],
                email_address=acc["email_address"],
                account_type=acc["account_type"],
                incoming_host=acc["incoming_host"],
                incoming_port=acc["incoming_port"],
                incoming_security=acc["incoming_security"],
                incoming_username=acc["incoming_username"],
                incoming_password=acc["incoming_password"],
                smtp_host=acc["smtp_host"],
                smtp_port=acc["smtp_port"],
                smtp_security=acc["smtp_security"],
                smtp_username=acc["smtp_username"],
                smtp_password=acc["smtp_password"],
                keep_on_server=acc["keep_on_server"]
            )
        else:
            add_account(
                name=acc["name"],
                email_address=acc["email_address"],
                account_type=acc["account_type"],
                incoming_host=acc["incoming_host"],
                incoming_port=acc["incoming_port"],
                incoming_security=acc["incoming_security"],
                incoming_username=acc["incoming_username"],
                incoming_password=acc["incoming_password"],
                smtp_host=acc["smtp_host"],
                smtp_port=acc["smtp_port"],
                smtp_security=acc["smtp_security"],
                smtp_username=acc["smtp_username"],
                smtp_password=acc["smtp_password"],
                keep_on_server=acc["keep_on_server"]
            )
        self.accept()
