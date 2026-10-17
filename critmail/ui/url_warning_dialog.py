"""
CritMail UI - Anti-Phishing Link Guard Modal Dialog
Inspects outbound links and alerts the user to spoofing, punycode, or untrusted URLs.
"""
import webbrowser
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QApplication
)
from critmail.security.link_guard import inspect_url_security
from critmail.config import COLORS

class LinkGuardDialog(QDialog):
    """Winamp 3 styled security check before navigating to external web links."""
    def __init__(self, target_url: str, parent=None):
        super().__init__(parent)
        self.target_url = target_url
        self.setWindowTitle("CritMail Link Guard - Security Verification")
        self.setFixedSize(540, 290)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        info = inspect_url_security(target_url)
        risk = info["risk_level"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header Badge
        header_color = COLORS['danger_red'] if risk == "HIGH" else (COLORS['warning_orange'] if risk == "MEDIUM" else COLORS['secure_green'])
        lbl_badge = QLabel(f"[ LINK GUARD // RISK LEVEL: {risk} ]")
        lbl_badge.setStyleSheet(f"color: {header_color}; font-weight: bold; font-size: 9pt;")
        layout.addWidget(lbl_badge)

        lbl_desc = QLabel("CritMail intercepted an outbound link request. Verify destination before proceeding:")
        lbl_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(lbl_desc)

        # Target URL display box
        txt_url = QTextEdit()
        txt_url.setReadOnly(True)
        txt_url.setPlainText(target_url)
        txt_url.setFixedHeight(50)
        txt_url.setStyleSheet(f"background: #080d15; border: 1px solid #1a2d47; color: {COLORS['text_accent']}; font-size: 8.5pt;")
        layout.addWidget(txt_url)

        # Warnings / Security Findings
        if info["warnings"]:
            findings_text = "⚠ WARNINGS DETECTED:\n" + "\n".join(f" • {w}" for w in info["warnings"])
            lbl_findings = QLabel(findings_text)
            lbl_findings.setStyleSheet(f"color: {COLORS['danger_red']}; font-size: 8pt; font-weight: bold;")
        else:
            lbl_findings = QLabel("✔ Domain structure appears normal. Standard TLS web link.")
            lbl_findings.setStyleSheet(f"color: {COLORS['secure_green']}; font-size: 8pt;")
        layout.addWidget(lbl_findings)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_copy = QPushButton("Copy URL")
        btn_copy.clicked.connect(self._copy_url)
        btn_layout.addWidget(btn_copy)

        btn_cancel = QPushButton("Abort / Cancel")
        btn_cancel.setDefault(True)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_open = QPushButton("Open in Browser")
        btn_open.setObjectName("AccentBtn")
        btn_open.clicked.connect(self._open_in_browser)
        btn_layout.addWidget(btn_open)

        layout.addLayout(btn_layout)

    def _copy_url(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.target_url)
        self.accept()

    def _open_in_browser(self):
        webbrowser.open(self.target_url)
        self.accept()
