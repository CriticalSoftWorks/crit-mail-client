"""
CritMail Security, Privacy, Blacklist, Mail Forwarding & Rules Control Center
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QCheckBox, QComboBox, QTextEdit, QMessageBox, QWidget
)
from critmail.config import COLORS
from critmail.ui.icon_factory import create_app_icon
from critmail.models.database import (
    get_rules, add_rule, delete_rule, toggle_rule,
    get_folders_for_account, get_accounts, get_setting, set_setting
)


class SecurityPrivacyDialog(QDialog):
    """Central Security, Privacy, Blacklist, and Forwarding Configuration Window."""
    def __init__(self, parent=None, active_account_id: int = None, initial_tab: int = 0):
        super().__init__(parent)
        self.active_account_id = active_account_id
        self.setWindowTitle("CritMail - Security, Privacy & Rules Center")
        self.setWindowIcon(create_app_icon())
        self.resize(760, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl_head = QLabel("[ SECURITY DEFENSE, BLACKLIST & ROUTING CONTROLS ]")
        lbl_head.setStyleSheet(f"color: {COLORS['text_accent']}; font-weight: bold; font-size: 9.5pt;")
        layout.addWidget(lbl_head)

        self.tabs = QTabWidget()

        # TAB 1: Privacy & Defense Shields
        tab_defense = QWidget()
        def_layout = QVBoxLayout(tab_defense)
        def_layout.setSpacing(8)

        grp_tls = QGroupBox("NETWORK ENCRYPTION & CIPHERS")
        tls_layout = QVBoxLayout(grp_tls)
        self.chk_tls_strict = QCheckBox("Enforce Strict TLS 1.2 / 1.3 (Reject obsolete SSLv3/TLS 1.0/1.1)")
        self.chk_tls_strict.setChecked(True)
        self.chk_tls_strict.setEnabled(False)  # Always enforced in CritMail
        tls_layout.addWidget(self.chk_tls_strict)
        self.chk_cert_val = QCheckBox("Strict CA Certificate Validation & Hostname Verification")
        self.chk_cert_val.setChecked(get_setting("cert_validation", "1") == "1")
        tls_layout.addWidget(self.chk_cert_val)
        def_layout.addWidget(grp_tls)

        grp_content = QGroupBox("CONTENT SANDBOXING & PRIVACY")
        c_layout = QVBoxLayout(grp_content)
        self.chk_block_trackers = QCheckBox("Block Remote Images & 1x1 Tracking Beacons by Default")
        self.chk_block_trackers.setChecked(get_setting("block_remote_images", "1") == "1")
        c_layout.addWidget(self.chk_block_trackers)

        self.chk_strip_scripts = QCheckBox("Strip <script>, <iframe>, <object>, and inline on* event handlers")
        self.chk_strip_scripts.setChecked(True)
        self.chk_strip_scripts.setEnabled(False)
        c_layout.addWidget(self.chk_strip_scripts)

        self.chk_link_guard = QCheckBox("Anti-Phishing Link Guard (Inspect Punycode, Spoofed Hostnames & Raw IPs)")
        self.chk_link_guard.setChecked(get_setting("link_guard_active", "1") == "1")
        c_layout.addWidget(self.chk_link_guard)

        self.chk_warn_exec = QCheckBox("Warn & Quarantine Dangerous Executable Attachments (.exe, .scr, .vbs, .bat)")
        self.chk_warn_exec.setChecked(get_setting("warn_exec_attachments", "1") == "1")
        c_layout.addWidget(self.chk_warn_exec)
        def_layout.addWidget(grp_content)

        def_layout.addStretch()
        self.tabs.addTab(tab_defense, "🛡 Privacy & Shields")

        # TAB 2: Blacklist & Spam Shield
        tab_black = QWidget()
        bl_layout = QVBoxLayout(tab_black)
        bl_layout.setSpacing(6)

        grp_add_bl = QGroupBox("ADD TO BLACKLIST")
        abl_layout = QHBoxLayout(grp_add_bl)
        abl_layout.setSpacing(6)

        abl_layout.addWidget(QLabel("Type:"))
        self.combo_bl_type = QComboBox()
        self.combo_bl_type.addItems(["Sender Email", "Sender Domain", "Subject/Body Keyword"])
        abl_layout.addWidget(self.combo_bl_type)

        self.txt_bl_pattern = QLineEdit()
        self.txt_bl_pattern.setPlaceholderText("e.g. spammer@bad.com or bad-domain.xyz or 'free bitcoin'")
        abl_layout.addWidget(self.txt_bl_pattern, 1)

        abl_layout.addWidget(QLabel("Action:"))
        self.combo_bl_action = QComboBox()
        self.combo_bl_action.addItem("Move to Spam", "spam")
        self.combo_bl_action.addItem("Move to Trash", "trash")
        self.combo_bl_action.addItem("Permanently Discard", "delete")
        abl_layout.addWidget(self.combo_bl_action)

        btn_add_bl = QPushButton("+ Add Block Rule")
        btn_add_bl.setObjectName("AccentBtn")
        btn_add_bl.clicked.connect(self._add_blacklist_rule)
        abl_layout.addWidget(btn_add_bl)

        bl_layout.addWidget(grp_add_bl)

        self.table_rules = QTableWidget()
        self.table_rules.setColumnCount(4)
        self.table_rules.setHorizontalHeaderLabels(["ACTIVE", "TYPE", "PATTERN / TARGET", "ACTION"])
        self.table_rules.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_rules.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_rules.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_rules.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_rules.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_rules.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        bl_layout.addWidget(self.table_rules, 1)

        bl_btn_row = QHBoxLayout()
        btn_toggle_r = QPushButton("Toggle Active State")
        btn_toggle_r.clicked.connect(lambda: self._toggle_rule_in_table(self.table_rules))
        bl_btn_row.addWidget(btn_toggle_r)

        btn_del_r = QPushButton("✕ Remove Block Rule")
        btn_del_r.clicked.connect(lambda: self._delete_rule_in_table(self.table_rules))
        bl_btn_row.addWidget(btn_del_r)
        bl_btn_row.addStretch()
        bl_layout.addLayout(bl_btn_row)

        self.tabs.addTab(tab_black, "🚫 Blacklist & Spam")

        # TAB 3: Mail Forwarding & Auto-Reply
        tab_fwd = QWidget()
        fwd_layout = QVBoxLayout(tab_fwd)
        fwd_layout.setSpacing(8)

        grp_fwd = QGroupBox("MAIL FORWARDING")
        gf_layout = QGridLayout(grp_fwd)
        gf_layout.setSpacing(6)

        self.chk_fwd_enable = QCheckBox("Enable Outgoing Mail Forwarding")
        self.chk_fwd_enable.setChecked(get_setting("fwd_enabled", "0") == "1")
        gf_layout.addWidget(self.chk_fwd_enable, 0, 0, 1, 2)

        gf_layout.addWidget(QLabel("Forward All Incoming Mail To:"), 1, 0)
        self.txt_fwd_email = QLineEdit(get_setting("fwd_email", ""))
        self.txt_fwd_email.setPlaceholderText("backup@domain.com")
        gf_layout.addWidget(self.txt_fwd_email, 1, 1)

        self.chk_fwd_keep = QCheckBox("Keep a local copy in CritMail Inbox after forwarding")
        self.chk_fwd_keep.setChecked(get_setting("fwd_keep", "1") == "1")
        gf_layout.addWidget(self.chk_fwd_keep, 2, 0, 1, 2)

        fwd_layout.addWidget(grp_fwd)

        grp_vac = QGroupBox("OUT-OF-OFFICE / AUTO-RESPONDER")
        gv_layout = QVBoxLayout(grp_vac)
        self.chk_vac_enable = QCheckBox("Enable Automatic Vacation / Auto-Reply")
        self.chk_vac_enable.setChecked(get_setting("vac_enabled", "0") == "1")
        gv_layout.addWidget(self.chk_vac_enable)

        self.txt_vac_msg = QTextEdit()
        self.txt_vac_msg.setPlaceholderText("Auto-response message body...")
        default_vac = "Thank you for your email. I am currently out of the office with limited connectivity and will respond upon my return."
        self.txt_vac_msg.setPlainText(get_setting("vac_msg", default_vac))
        self.txt_vac_msg.setFixedHeight(85)
        gv_layout.addWidget(self.txt_vac_msg)

        fwd_layout.addWidget(grp_vac)
        fwd_layout.addStretch()
        self.tabs.addTab(tab_fwd, "↪ Forwarding & Auto-Reply")

        # TAB 4: Folder Routing Rules
        tab_route = QWidget()
        r_layout = QVBoxLayout(tab_route)
        r_layout.setSpacing(6)

        grp_add_route = QGroupBox("CREATE INCOMING ROUTING RULE")
        ar_layout = QHBoxLayout(grp_add_route)
        ar_layout.setSpacing(6)

        ar_layout.addWidget(QLabel("Match Field:"))
        self.combo_route_type = QComboBox()
        self.combo_route_type.addItems(["Subject/Body Keyword", "Sender Email", "Sender Domain", "Header Text"])
        ar_layout.addWidget(self.combo_route_type)

        self.txt_route_keyword = QLineEdit()
        self.txt_route_keyword.setPlaceholderText("Keyword, sender, or header pattern...")
        ar_layout.addWidget(self.txt_route_keyword, 1)

        ar_layout.addWidget(QLabel("Route to Folder:"))
        self.combo_target_folder = QComboBox()
        self.folder_name_map = {}
        self._populate_folders_combo()
        ar_layout.addWidget(self.combo_target_folder)

        btn_add_route = QPushButton("+ Add Routing Rule")
        btn_add_route.setObjectName("AccentBtn")
        btn_add_route.clicked.connect(self._add_routing_rule)
        ar_layout.addWidget(btn_add_route)

        r_layout.addWidget(grp_add_route)

        self.table_routing = QTableWidget()
        self.table_routing.setColumnCount(4)
        self.table_routing.setHorizontalHeaderLabels(["ACTIVE", "MATCH FIELD", "PATTERN", "TARGET FOLDER"])
        self.table_routing.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_routing.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_routing.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_routing.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_routing.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_routing.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        r_layout.addWidget(self.table_routing, 1)

        rt_btn_row = QHBoxLayout()
        btn_toggle_rt = QPushButton("Toggle Active State")
        btn_toggle_rt.clicked.connect(lambda: self._toggle_rule_in_table(self.table_routing))
        rt_btn_row.addWidget(btn_toggle_rt)

        btn_del_rt = QPushButton("✕ Remove Routing Rule")
        btn_del_rt.clicked.connect(lambda: self._delete_rule_in_table(self.table_routing))
        rt_btn_row.addWidget(btn_del_rt)
        rt_btn_row.addStretch()
        r_layout.addLayout(rt_btn_row)

        self.tabs.addTab(tab_route, "📁 Folder Routing Rules")

        if 0 <= initial_tab < self.tabs.count():
            self.tabs.setCurrentIndex(initial_tab)

        layout.addWidget(self.tabs, 1)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_row.addStretch()

        btn_save = QPushButton("Apply All Settings")
        btn_save.setObjectName("AccentBtn")
        btn_save.clicked.connect(self._save_all_settings)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

        self._load_rules_table()

    def _populate_folders_combo(self):
        self.combo_target_folder.clear()
        self.folder_name_map.clear()
        accs = get_accounts()
        if not accs:
            return
        target_acc_id = self.active_account_id or accs[0]["id"]
        folders = get_folders_for_account(target_acc_id)
        for f in folders:
            self.folder_name_map[f["id"]] = f["name"]
            self.combo_target_folder.addItem(f["name"], f["id"])

    def _load_rules_table(self):
        all_rules = get_rules(self.active_account_id)
        bl_rules = [r for r in all_rules if r["action"] != "move_folder"]
        rt_rules = [r for r in all_rules if r["action"] == "move_folder"]

        self.table_rules.setRowCount(len(bl_rules))
        for r, rule in enumerate(bl_rules):
            it_active = QTableWidgetItem("✔ ACTIVE" if rule["is_active"] else "OFF")
            it_active.setData(Qt.ItemDataRole.UserRole, rule["id"])
            it_active.setForeground(Qt.GlobalColor.green if rule["is_active"] else Qt.GlobalColor.gray)
            self.table_rules.setItem(r, 0, it_active)
            self.table_rules.setItem(r, 1, QTableWidgetItem(rule["rule_type"].upper()))
            self.table_rules.setItem(r, 2, QTableWidgetItem(rule["pattern"]))
            self.table_rules.setItem(r, 3, QTableWidgetItem(rule["action"].upper()))

        self.table_routing.setRowCount(len(rt_rules))
        for r, rule in enumerate(rt_rules):
            it_active = QTableWidgetItem("✔ ACTIVE" if rule["is_active"] else "OFF")
            it_active.setData(Qt.ItemDataRole.UserRole, rule["id"])
            it_active.setForeground(Qt.GlobalColor.green if rule["is_active"] else Qt.GlobalColor.gray)
            self.table_routing.setItem(r, 0, it_active)
            self.table_routing.setItem(r, 1, QTableWidgetItem(rule["rule_type"].upper()))
            self.table_routing.setItem(r, 2, QTableWidgetItem(rule["pattern"]))
            fld_name = self.folder_name_map.get(rule.get("target_folder_id"), f"Folder #{rule.get('target_folder_id')}")
            self.table_routing.setItem(r, 3, QTableWidgetItem(f"📁 {fld_name}"))

    def _add_blacklist_rule(self):
        pat = self.txt_bl_pattern.text().strip()
        if not pat:
            QMessageBox.warning(self, "Missing Pattern", "Please enter a sender email, domain, or keyword to block.")
            return

        type_map = {
            "Sender Email": "sender",
            "Sender Domain": "domain",
            "Subject/Body Keyword": "keyword"
        }
        rtype = type_map.get(self.combo_bl_type.currentText(), "sender")
        action = self.combo_bl_action.currentData() or "spam"

        add_rule(rule_type=rtype, pattern=pat, action=action, account_id=self.active_account_id)
        self.txt_bl_pattern.clear()
        self._load_rules_table()

    def _add_routing_rule(self):
        pat = self.txt_route_keyword.text().strip()
        fld_id = self.combo_target_folder.currentData()
        if not pat or not fld_id:
            QMessageBox.warning(self, "Missing Information", "Please enter a pattern and select a target folder.")
            return

        type_map = {
            "Subject/Body Keyword": "keyword",
            "Sender Email": "sender",
            "Sender Domain": "domain",
            "Header Text": "header"
        }
        rtype = type_map.get(self.combo_route_type.currentText(), "keyword")

        add_rule(
            rule_type=rtype,
            pattern=pat,
            action="move_folder",
            target_folder_id=fld_id,
            account_id=self.active_account_id
        )
        self.txt_route_keyword.clear()
        self._load_rules_table()

    def _toggle_rule_in_table(self, table: QTableWidget):
        items = table.selectedItems()
        if not items:
            return
        r = items[0].row()
        rule_id = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        toggle_rule(rule_id)
        self._load_rules_table()

    def _delete_rule_in_table(self, table: QTableWidget):
        items = table.selectedItems()
        if not items:
            return
        r = items[0].row()
        rule_id = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        delete_rule(rule_id)
        self._load_rules_table()

    def _save_all_settings(self):
        set_setting("cert_validation", "1" if self.chk_cert_val.isChecked() else "0")
        set_setting("block_remote_images", "1" if self.chk_block_trackers.isChecked() else "0")
        set_setting("link_guard_active", "1" if self.chk_link_guard.isChecked() else "0")
        set_setting("warn_exec_attachments", "1" if self.chk_warn_exec.isChecked() else "0")
        set_setting("fwd_enabled", "1" if self.chk_fwd_enable.isChecked() else "0")
        set_setting("fwd_email", self.txt_fwd_email.text().strip())
        set_setting("fwd_keep", "1" if self.chk_fwd_keep.isChecked() else "0")
        set_setting("vac_enabled", "1" if self.chk_vac_enable.isChecked() else "0")
        set_setting("vac_msg", self.txt_vac_msg.toPlainText().strip())
        self.accept()
