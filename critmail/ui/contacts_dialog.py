"""
CritMail UI - Advanced Address Book & Contact Sheet
Full Contact Sheet with 3 Clickable Phone Numbers, Employer, School, Notable Allegiances,
Social/Web Links with Custom 'Other' Option, Relationship Status, and Block/Ignore Mail Toggle.
"""
import webbrowser
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QTextEdit, QComboBox, QCheckBox, QMessageBox, QMenu, QWidget, QScrollArea,
    QApplication
)
from critmail.config import COLORS
from critmail.ui.icon_factory import create_app_icon
from critmail.models.database import (
    get_contacts, save_contact, delete_contact, set_contact_blocked,
    get_setting, set_setting
)


class ContactSheetDialog(QDialog):
    """Detailed Contact Sheet editor dialog with dynamic phones, allegiances, and social links."""
    def __init__(self, contact_data: dict = None, parent=None):
        super().__init__(parent)
        self.contact_data = contact_data or {}
        self.setWindowTitle("CritMail - Contact Sheet")
        self.setWindowIcon(create_app_icon())
        self.resize(640, 680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl_head = QLabel("[ CONTACT DOSSIER & PROFILE SHEET ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9pt;")
        layout.addWidget(lbl_head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: #090e17; border: 1px solid #1a2d47;")
        inner_widget = QWidget()
        form_layout = QVBoxLayout(inner_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)

        # 1. Primary Identity
        grp_id = QGroupBox("PRIMARY IDENTITY")
        id_layout = QGridLayout(grp_id)
        id_layout.setSpacing(6)

        id_layout.addWidget(QLabel("Full Name:"), 0, 0)
        self.txt_name = QLineEdit(self.contact_data.get("name", ""))
        self.txt_name.setPlaceholderText("e.g. John Doe")
        id_layout.addWidget(self.txt_name, 0, 1)

        id_layout.addWidget(QLabel("Email Address:"), 1, 0)
        self.txt_email = QLineEdit(self.contact_data.get("email", ""))
        self.txt_email.setPlaceholderText("user@example.com")
        id_layout.addWidget(self.txt_email, 1, 1)

        id_layout.addWidget(QLabel("Relationship:"), 2, 0)
        self.combo_rel = QComboBox()
        self.combo_rel.addItems([
            "Co-Worker", "Friend", "Close Friend", "Relative",
            "Acquaintance", "Neighbor", "Client / Partner", "Other"
        ])
        cur_rel = self.contact_data.get("relationship", "Other")
        idx_rel = self.combo_rel.findText(cur_rel)
        if idx_rel >= 0:
            self.combo_rel.setCurrentIndex(idx_rel)
        id_layout.addWidget(self.combo_rel, 2, 1)

        form_layout.addWidget(grp_id)

        # 2. Phone Numbers (Clickable, up to 3)
        grp_phone = QGroupBox("PHONE NUMBERS (UP TO 3)")
        self.phone_layout = QGridLayout(grp_phone)
        self.phone_layout.setSpacing(6)

        # Phone 1 (Always visible)
        self.phone_layout.addWidget(QLabel("Phone 1:"), 0, 0)
        self.combo_p1 = QComboBox()
        self.combo_p1.addItems(["Mobile", "Work", "Home", "Direct", "Main", "Pager", "Other"])
        self.combo_p1.setCurrentText(self.contact_data.get("phone1_label") or "Mobile")
        self.phone_layout.addWidget(self.combo_p1, 0, 1)

        self.txt_p1 = QLineEdit(self.contact_data.get("phone1", ""))
        self.txt_p1.setPlaceholderText("+1 (555) 012-3456")
        self.phone_layout.addWidget(self.txt_p1, 0, 2)

        btn_call1 = QPushButton("📞 Call")
        btn_call1.setFixedHeight(22)
        btn_call1.clicked.connect(lambda: self._call_number(self.txt_p1.text()))
        self.phone_layout.addWidget(btn_call1, 0, 3)

        # Phone 2 (Optional)
        self.lbl_p2 = QLabel("Phone 2:")
        self.combo_p2 = QComboBox()
        self.combo_p2.addItems(["Work", "Mobile", "Home", "Direct", "Main", "Pager", "Other"])
        self.combo_p2.setCurrentText(self.contact_data.get("phone2_label") or "Work")
        self.txt_p2 = QLineEdit(self.contact_data.get("phone2", ""))
        self.txt_p2.setPlaceholderText("Second phone...")
        self.btn_call2 = QPushButton("📞 Call")
        self.btn_call2.setFixedHeight(22)
        self.btn_call2.clicked.connect(lambda: self._call_number(self.txt_p2.text()))

        self.phone_layout.addWidget(self.lbl_p2, 1, 0)
        self.phone_layout.addWidget(self.combo_p2, 1, 1)
        self.phone_layout.addWidget(self.txt_p2, 1, 2)
        self.phone_layout.addWidget(self.btn_call2, 1, 3)

        # Phone 3 (Optional)
        self.lbl_p3 = QLabel("Phone 3:")
        self.combo_p3 = QComboBox()
        self.combo_p3.addItems(["Home", "Mobile", "Work", "Direct", "Main", "Pager", "Other"])
        self.combo_p3.setCurrentText(self.contact_data.get("phone3_label") or "Home")
        self.txt_p3 = QLineEdit(self.contact_data.get("phone3", ""))
        self.txt_p3.setPlaceholderText("Third phone...")
        self.btn_call3 = QPushButton("📞 Call")
        self.btn_call3.setFixedHeight(22)
        self.btn_call3.clicked.connect(lambda: self._call_number(self.txt_p3.text()))

        self.phone_layout.addWidget(self.lbl_p3, 2, 0)
        self.phone_layout.addWidget(self.combo_p3, 2, 1)
        self.phone_layout.addWidget(self.txt_p3, 2, 2)
        self.phone_layout.addWidget(self.btn_call3, 2, 3)

        # Dynamic Add Buttons for Phone 2 and 3
        has_p2 = bool(self.contact_data.get("phone2"))
        has_p3 = bool(self.contact_data.get("phone3"))

        self._set_phone_row_visible(2, has_p2)
        self._set_phone_row_visible(3, has_p3)

        phone_btn_row = QHBoxLayout()
        self.btn_add_p2 = QPushButton("+ Add Second Phone")
        self.btn_add_p2.setStyleSheet("font-size: 7.5pt; padding: 2px 6px;")
        self.btn_add_p2.clicked.connect(lambda: self._reveal_phone_row(2))
        self.btn_add_p2.setVisible(not has_p2)
        phone_btn_row.addWidget(self.btn_add_p2)

        self.btn_add_p3 = QPushButton("+ Add Third Phone")
        self.btn_add_p3.setStyleSheet("font-size: 7.5pt; padding: 2px 6px;")
        self.btn_add_p3.clicked.connect(lambda: self._reveal_phone_row(3))
        self.btn_add_p3.setVisible(has_p2 and not has_p3)
        phone_btn_row.addWidget(self.btn_add_p3)
        phone_btn_row.addStretch()

        self.phone_layout.addLayout(phone_btn_row, 3, 0, 1, 4)
        form_layout.addWidget(grp_phone)

        # 3. Organization, Education & Notable Allegiances
        grp_org = QGroupBox("AFFILIATIONS & NOTABLE ALLEGIANCES")
        org_layout = QGridLayout(grp_org)
        org_layout.setSpacing(6)

        org_layout.addWidget(QLabel("Employer / Company:"), 0, 0)
        self.txt_employer = QLineEdit(self.contact_data.get("employer", ""))
        self.txt_employer.setPlaceholderText("Organization / Agency / Business")
        org_layout.addWidget(self.txt_employer, 0, 1)

        org_layout.addWidget(QLabel("School / University:"), 1, 0)
        self.txt_school = QLineEdit(self.contact_data.get("school", ""))
        self.txt_school.setPlaceholderText("Alumni / Academic Affiliation")
        org_layout.addWidget(self.txt_school, 1, 1)

        org_layout.addWidget(QLabel("Notable Allegiances:"), 2, 0)
        self.txt_allegiances = QLineEdit(self.contact_data.get("allegiances", ""))
        self.txt_allegiances.setPlaceholderText("Political / Agency / Defense / Corporate Ties")
        org_layout.addWidget(self.txt_allegiances, 2, 1)

        form_layout.addWidget(grp_org)

        # 4. Social Media & Website Links
        grp_social = QGroupBox("WEBSITES & SOCIAL MEDIA PROFILES")
        self.social_layout = QVBoxLayout(grp_social)
        self.social_layout.setSpacing(5)

        self.social_entries = []
        links = self.contact_data.get("social_links_parsed", [])
        for link in links:
            self._add_social_row(link.get("platform", "Website"), link.get("custom_platform", ""), link.get("url", ""))

        if not self.social_entries:
            # Default empty row
            self._add_social_row("LinkedIn", "", "")

        btn_add_social = QPushButton("+ Add Social / Web Link")
        btn_add_social.setStyleSheet("font-size: 7.5pt; padding: 2px 6px;")
        btn_add_social.clicked.connect(lambda: self._add_social_row("Website", "", ""))
        self.social_layout.addWidget(btn_add_social)

        form_layout.addWidget(grp_social)

        # 5. Notes & Security / Block Control
        grp_notes = QGroupBox("DOSSIER NOTES & SECURITY CONTROLS")
        notes_layout = QVBoxLayout(grp_notes)
        notes_layout.setSpacing(6)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Confidential contact notes, background details, encrypted keys...")
        self.txt_notes.setPlainText(self.contact_data.get("notes", ""))
        self.txt_notes.setFixedHeight(75)
        notes_layout.addWidget(self.txt_notes)

        self.chk_block = QCheckBox("🚫 Block & Ignore All Mail from this Contact (Auto-route to Spam/Trash)")
        self.chk_block.setChecked(bool(self.contact_data.get("is_blocked", 0)))
        self.chk_block.setStyleSheet(f"color: {COLORS['danger_red']}; font-weight: bold;")
        notes_layout.addWidget(self.chk_block)

        form_layout.addWidget(grp_notes)

        scroll.setWidget(inner_widget)
        layout.addWidget(scroll, 1)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_row.addStretch()

        btn_save = QPushButton("Save Contact Sheet")
        btn_save.setObjectName("AccentBtn")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _set_phone_row_visible(self, row_num: int, visible: bool):
        if row_num == 2:
            self.lbl_p2.setVisible(visible)
            self.combo_p2.setVisible(visible)
            self.txt_p2.setVisible(visible)
            self.btn_call2.setVisible(visible)
        elif row_num == 3:
            self.lbl_p3.setVisible(visible)
            self.combo_p3.setVisible(visible)
            self.txt_p3.setVisible(visible)
            self.btn_call3.setVisible(visible)

    def _reveal_phone_row(self, row_num: int):
        self._set_phone_row_visible(row_num, True)
        if row_num == 2:
            self.btn_add_p2.setVisible(False)
            self.btn_add_p3.setVisible(True)
        elif row_num == 3:
            self.btn_add_p3.setVisible(False)

    def _call_number(self, num: str):
        cleaned = "".join(c for c in num if c.isdigit() or c == "+")
        if not cleaned:
            QMessageBox.information(self, "No Phone Number", "Please enter a valid phone number first.")
            return
        # Open via tel: URI scheme on Windows / mobile
        webbrowser.open(f"tel:{cleaned}")

    def _add_social_row(self, platform="Website", custom_platform="", url=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        combo_plat = QComboBox()
        platforms = ["LinkedIn", "Twitter / X", "GitHub", "Website", "Facebook", "Instagram", "Telegram", "Signal", "Other"]
        combo_plat.addItems(platforms)
        if platform in platforms:
            combo_plat.setCurrentText(platform)
        else:
            combo_plat.setCurrentText("Other")
        row_layout.addWidget(combo_plat)

        txt_custom = QLineEdit(custom_platform)
        txt_custom.setPlaceholderText("Specify Platform...")
        txt_custom.setFixedWidth(110)
        txt_custom.setVisible(combo_plat.currentText() == "Other")
        row_layout.addWidget(txt_custom)

        combo_plat.currentTextChanged.connect(lambda txt: txt_custom.setVisible(txt == "Other"))

        txt_url = QLineEdit(url)
        txt_url.setPlaceholderText("https://...")
        row_layout.addWidget(txt_url, 1)

        btn_open = QPushButton("🔗")
        btn_open.setToolTip("Open in Browser")
        btn_open.setFixedWidth(28)
        btn_open.clicked.connect(lambda: webbrowser.open(txt_url.text()) if txt_url.text() else None)
        row_layout.addWidget(btn_open)

        btn_del = QPushButton("✕")
        btn_del.setToolTip("Remove Link")
        btn_del.setFixedWidth(24)
        btn_del.clicked.connect(lambda: self._remove_social_row(row_widget))
        row_layout.addWidget(btn_del)

        self.social_layout.insertWidget(len(self.social_entries), row_widget)
        self.social_entries.append({
            "widget": row_widget,
            "combo": combo_plat,
            "custom": txt_custom,
            "url": txt_url
        })

    def _remove_social_row(self, widget: QWidget):
        for entry in self.social_entries:
            if entry["widget"] == widget:
                self.social_entries.remove(entry)
                widget.deleteLater()
                break

    def _save(self):
        email_addr = self.txt_email.text().strip()
        if not email_addr:
            QMessageBox.warning(self, "Missing Email", "Email address is required.")
            return

        social_links = []
        for entry in self.social_entries:
            u = entry["url"].text().strip()
            if u:
                social_links.append({
                    "platform": entry["combo"].currentText(),
                    "custom_platform": entry["custom"].text().strip() if entry["combo"].currentText() == "Other" else "",
                    "url": u
                })

        save_contact(
            name=self.txt_name.text().strip() or email_addr.split("@")[0],
            email_addr=email_addr,
            phone1=self.txt_p1.text().strip(),
            phone1_label=self.combo_p1.currentText(),
            phone2=self.txt_p2.text().strip() if self.txt_p2.isVisible() else "",
            phone2_label=self.combo_p2.currentText(),
            phone3=self.txt_p3.text().strip() if self.txt_p3.isVisible() else "",
            phone3_label=self.combo_p3.currentText(),
            employer=self.txt_employer.text().strip(),
            school=self.txt_school.text().strip(),
            allegiances=self.txt_allegiances.text().strip(),
            notes=self.txt_notes.toPlainText().strip(),
            social_links=social_links,
            relationship=self.combo_rel.currentText(),
            is_blocked=self.chk_block.isChecked(),
            contact_id=self.contact_data.get("id")
        )
        self.accept()


class ContactsDialog(QDialog):
    """Winamp 3 styled Address Book & Directory with full context menus and search."""
    contact_selected = pyqtSignal(str)

    def __init__(self, parent=None, picker_mode: bool = False, filter_blocked_only: bool = False):
        super().__init__(parent)
        self.picker_mode = picker_mode
        self.filter_blocked_only = filter_blocked_only
        self.setWindowTitle("CritMail - Agent Dossiers & Contact Directory")
        self.setWindowIcon(create_app_icon())
        self.resize(900, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header bar & Search
        top_bar = QHBoxLayout()
        lbl_head = QLabel("[ AGENT DOSSIERS // SECURE CONTACTS DIRECTORY ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9pt;")
        top_bar.addWidget(lbl_head)
        top_bar.addStretch()

        self.chk_blocked_only = QCheckBox("🚫 Blocked Only")
        self.chk_blocked_only.setChecked(filter_blocked_only)
        self.chk_blocked_only.stateChanged.connect(lambda _: self._filter_contacts(self.txt_search.text()))
        top_bar.addWidget(self.chk_blocked_only)

        top_bar.addWidget(QLabel("Search:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter name, email, employer...")
        self.txt_search.setFixedWidth(200)
        self.txt_search.textChanged.connect(self._filter_contacts)
        top_bar.addWidget(self.txt_search)

        btn_new = QPushButton("+ New Contact Sheet...")
        btn_new.setObjectName("AccentBtn")
        btn_new.clicked.connect(self._create_contact)
        top_bar.addWidget(btn_new)

        layout.addLayout(top_bar)

        # Contacts Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["STATUS", "NAME", "EMAIL", "PRIMARY PHONE", "EMPLOYER / ALLEGIANCES", "RELATIONSHIP"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 180)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

        # Bottom Actions
        btn_row = QHBoxLayout()
        btn_call = QPushButton("📞 Call")
        btn_call.clicked.connect(self._call_selected)
        btn_row.addWidget(btn_call)

        btn_edit = QPushButton("✏ Edit Sheet...")
        btn_edit.clicked.connect(self._edit_selected)
        btn_row.addWidget(btn_edit)

        btn_block = QPushButton("🚫 Toggle Block")
        btn_block.clicked.connect(self._toggle_block_selected)
        btn_row.addWidget(btn_block)

        btn_del = QPushButton("✕ Delete")
        btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(btn_del)

        btn_row.addStretch()

        if self.picker_mode:
            btn_use = QPushButton("✔ Insert Selected Recipient")
            btn_use.setObjectName("AccentBtn")
            btn_use.clicked.connect(self._use_selected)
            btn_row.addWidget(btn_use)
        else:
            btn_compose = QPushButton("⚡ Compose to Selected")
            btn_compose.setObjectName("AccentBtn")
            btn_compose.clicked.connect(self._use_selected)
            btn_row.addWidget(btn_compose)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.all_contacts = []
        self._load_contacts()

    def _load_contacts(self):
        self.all_contacts = get_contacts()
        self._filter_contacts(self.txt_search.text())

    def _filter_contacts(self, text: str):
        t = text.strip().lower()
        blocked_only = self.chk_blocked_only.isChecked()
        filtered = []
        for c in self.all_contacts:
            if blocked_only and not c.get("is_blocked"):
                continue
            if t and not (
                t in c.get("name", "").lower()
                or t in c.get("email", "").lower()
                or t in c.get("employer", "").lower()
                or t in c.get("allegiances", "").lower()
            ):
                continue
            filtered.append(c)
        self._render_table(filtered)

    def _render_table(self, contacts: list[dict]):
        self.table.setRowCount(len(contacts))
        for r, c in enumerate(contacts):
            status_text = "🚫 BLOCKED" if c.get("is_blocked") else "✔ OK"
            it_status = QTableWidgetItem(status_text)
            if c.get("is_blocked"):
                it_status.setForeground(Qt.GlobalColor.red)
            else:
                it_status.setForeground(Qt.GlobalColor.green)
            it_status.setData(Qt.ItemDataRole.UserRole, c)
            self.table.setItem(r, 0, it_status)

            self.table.setItem(r, 1, QTableWidgetItem(c["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(c["email"]))

            phone_display = f"{c.get('phone1')} ({c.get('phone1_label')})" if c.get("phone1") else ""
            self.table.setItem(r, 3, QTableWidgetItem(phone_display))

            affil = c.get("employer", "")
            if c.get("allegiances"):
                affil += f" // {c.get('allegiances')}"
            self.table.setItem(r, 4, QTableWidgetItem(affil))

            self.table.setItem(r, 5, QTableWidgetItem(c.get("relationship", "Other")))

    def _get_selected_contact(self) -> dict | None:
        items = self.table.selectedItems()
        if not items:
            return None
        r = items[0].row()
        return self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)

    def _show_context_menu(self, pos):
        c = self._get_selected_contact()
        if not c:
            return
        menu = QMenu(self)

        act_comp = menu.addAction(f"⚡ Compose Email to {c['email']}")
        act_comp.triggered.connect(self._use_selected)

        if c.get("phone1"):
            act_call = menu.addAction(f"📞 Call {c['phone1']} ({c.get('phone1_label', 'Mobile')})")
            act_call.triggered.connect(lambda: webbrowser.open(f"tel:{c['phone1']}"))

            act_copy_p = menu.addAction("📋 Copy Phone Number")
            act_copy_p.triggered.connect(lambda: QApplication.clipboard().setText(c['phone1']))

        menu.addSeparator()

        links = c.get("social_links_parsed", [])
        if links:
            social_menu = menu.addMenu("🔗 Open Web / Social Link")
            for link in links:
                url = link.get("url", "")
                plat = link.get("custom_platform") or link.get("platform", "Link")
                act_l = social_menu.addAction(f"{plat}: {url[:30]}...")
                act_l.triggered.connect(lambda checked=False, target=url: webbrowser.open(target))

        menu.addSeparator()

        act_edit = menu.addAction("✏ Edit Full Contact Sheet...")
        act_edit.triggered.connect(self._edit_selected)

        block_text = "🟢 Unblock Contact" if c.get("is_blocked") else "🚫 Block / Ignore Contact"
        act_block = menu.addAction(block_text)
        act_block.triggered.connect(self._toggle_block_selected)

        menu.addSeparator()

        act_del = menu.addAction("✕ Delete Contact")
        act_del.triggered.connect(self._delete_selected)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _create_contact(self):
        dlg = ContactSheetDialog(parent=self)
        if dlg.exec():
            self._load_contacts()

    def _edit_selected(self):
        c = self._get_selected_contact()
        if not c:
            return
        dlg = ContactSheetDialog(contact_data=c, parent=self)
        if dlg.exec():
            self._load_contacts()

    def _on_double_click(self, item: QTableWidgetItem):
        if self.picker_mode:
            self._use_selected()
        else:
            self._edit_selected()

    def _call_selected(self):
        c = self._get_selected_contact()
        if not c or not c.get("phone1"):
            QMessageBox.information(self, "No Phone Number", "Selected contact has no phone number recorded.")
            return
        webbrowser.open(f"tel:{c['phone1']}")

    def _toggle_block_selected(self):
        c = self._get_selected_contact()
        if not c:
            return
        new_state = not bool(c.get("is_blocked", 0))
        set_contact_blocked(c["email"], new_state)
        self._load_contacts()

    def _delete_selected(self):
        c = self._get_selected_contact()
        if not c:
            return
        res = QMessageBox.question(self, "Delete Contact", f"Delete '{c['name']}' from Address Book?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            delete_contact(c["id"])
            self._load_contacts()

    def _use_selected(self):
        c = self._get_selected_contact()
        if not c:
            return
        formatted = f"{c['name']} <{c['email']}>" if c.get("name") else c['email']
        self.contact_selected.emit(formatted)
        self.accept()


class PreferencesDialog(QDialog):
    """Preferences for Email Signature, Auto-Sync Interval, and Security Defaults."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CritMail - Preferences & Signature")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(540, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl = QLabel("[ PREFERENCES // SIGNATURE & SYNC OPTIONS ]")
        lbl.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9pt;")
        layout.addWidget(lbl)

        # Auto-Sync & Security
        grp_sync = QGroupBox("SYNC & AUTOMATION DEFAULTS")
        s_layout = QGridLayout(grp_sync)

        s_layout.addWidget(QLabel("Auto-Check Mail Interval:"), 0, 0)
        self.combo_interval = QComboBox()
        self.combo_interval.addItem("Manual Only (Off)", "0")
        self.combo_interval.addItem("Every 1 Minute", "1")
        self.combo_interval.addItem("Every 5 Minutes", "5")
        self.combo_interval.addItem("Every 15 Minutes", "15")
        self.combo_interval.addItem("Every 30 Minutes", "30")
        cur_int = get_setting("auto_sync_minutes", "5")
        idx = self.combo_interval.findData(cur_int)
        if idx >= 0:
            self.combo_interval.setCurrentIndex(idx)
        s_layout.addWidget(self.combo_interval, 0, 1)

        self.chk_auto_contacts = QCheckBox("Automatically add recipients to Address Book on Send")
        self.chk_auto_contacts.setChecked(get_setting("auto_save_contacts", "1") == "1")
        s_layout.addWidget(self.chk_auto_contacts, 1, 0, 1, 2)

        self.chk_confirm_delete = QCheckBox("Ask for confirmation before moving messages to Trash")
        self.chk_confirm_delete.setChecked(get_setting("confirm_delete", "1") == "1")
        s_layout.addWidget(self.chk_confirm_delete, 2, 0, 1, 2)

        layout.addWidget(grp_sync)

        # Signature
        grp_sig = QGroupBox("OUTGOING EMAIL SIGNATURE")
        sig_layout = QVBoxLayout(grp_sig)
        self.txt_sig = QTextEdit()
        self.txt_sig.setPlaceholderText("Optional signature appended to outgoing messages...")
        default_sig = "-- \nJames F.\nThe Intelligence Agency\njames.f@theintelligenceagency.net"
        self.txt_sig.setPlainText(get_setting("signature", default_sig))
        sig_layout.addWidget(self.txt_sig)
        layout.addWidget(grp_sig, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Preferences")
        btn_save.setObjectName("AccentBtn")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _save(self):
        set_setting("auto_sync_minutes", self.combo_interval.currentData())
        set_setting("auto_save_contacts", "1" if self.chk_auto_contacts.isChecked() else "0")
        set_setting("confirm_delete", "1" if self.chk_confirm_delete.isChecked() else "0")
        set_setting("signature", self.txt_sig.toPlainText().strip())
        self.accept()
