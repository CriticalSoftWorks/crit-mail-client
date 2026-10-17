"""
CritMail Database - Fast, Local, Encrypted/Protected SQLite Storage
Supports Accounts, Folders, Messages, Attachments, Advanced Contacts,
Blacklist & Filtering Rules, Categories, and Security Preferences.
"""
import sqlite3
import datetime
import json
from pathlib import Path
from critmail.config import DB_PATH
from critmail.security.crypto import encrypt_secret, decrypt_secret

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured for performance and integrity."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")  # High speed WAL mode
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db():
    """Initializes schema and tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email_address TEXT NOT NULL,
            account_type TEXT NOT NULL DEFAULT 'IMAP',
            incoming_host TEXT NOT NULL,
            incoming_port INTEGER NOT NULL DEFAULT 993,
            incoming_security TEXT NOT NULL DEFAULT 'SSL/TLS',
            incoming_username TEXT NOT NULL,
            incoming_password_enc TEXT NOT NULL,
            smtp_host TEXT NOT NULL,
            smtp_port INTEGER NOT NULL DEFAULT 465,
            smtp_security TEXT NOT NULL DEFAULT 'SSL/TLS',
            smtp_username TEXT NOT NULL,
            smtp_password_enc TEXT NOT NULL,
            keep_on_server INTEGER NOT NULL DEFAULT 1,
            signature TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            folder_type TEXT NOT NULL DEFAULT 'inbox',
            UNIQUE(account_id, name)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
            server_uid TEXT,
            message_id TEXT,
            subject TEXT NOT NULL DEFAULT '(No Subject)',
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            cc TEXT,
            bcc TEXT,
            date TIMESTAMP,
            body_plain TEXT,
            body_html TEXT,
            size_bytes INTEGER DEFAULT 0,
            is_read INTEGER DEFAULT 0,
            is_flagged INTEGER DEFAULT 0,
            has_attachments INTEGER DEFAULT 0,
            raw_headers TEXT,
            security_verdict TEXT DEFAULT 'CLEAN',
            category TEXT DEFAULT 'Primary',
            unsubscribe_info TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, server_uid)
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            content_type TEXT,
            size_bytes INTEGER DEFAULT 0,
            file_path TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone1 TEXT DEFAULT '',
            phone1_label TEXT DEFAULT 'Mobile',
            phone2 TEXT DEFAULT '',
            phone2_label TEXT DEFAULT 'Work',
            phone3 TEXT DEFAULT '',
            phone3_label TEXT DEFAULT 'Home',
            employer TEXT DEFAULT '',
            school TEXT DEFAULT '',
            allegiances TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            social_links TEXT DEFAULT '[]',
            relationship TEXT DEFAULT 'Other',
            is_blocked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            rule_type TEXT NOT NULL, -- 'sender', 'domain', 'keyword', 'header'
            pattern TEXT NOT NULL,
            action TEXT NOT NULL DEFAULT 'spam', -- 'spam', 'trash', 'delete', 'move_folder'
            target_folder_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_msg_folder ON messages(folder_id);
        CREATE INDEX IF NOT EXISTS idx_msg_account ON messages(account_id);
        CREATE INDEX IF NOT EXISTS idx_msg_date ON messages(date DESC);
        CREATE INDEX IF NOT EXISTS idx_msg_uid ON messages(account_id, server_uid);
        """)

        # Add any missing columns to existing messages/contacts tables safely
        _upgrade_schema(conn)

        # Create index on category after column is guaranteed to exist
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_cat ON messages(category);")

        # Ensure default folders exist for all accounts
        accs = conn.execute("SELECT id FROM accounts").fetchall()
        for a in accs:
            for fname, ftype in [("Archive", "archive"), ("Trash", "trash"), ("Spam", "spam"), ("Drafts", "drafts")]:
                conn.execute(
                    "INSERT OR IGNORE INTO folders (account_id, name, folder_type) VALUES (?, ?, ?)",
                    (a["id"], fname, ftype)
                )

def _upgrade_schema(conn: sqlite3.Connection):
    """Safely adds newly required columns to existing databases without data loss."""
    msg_cols = [r["name"] for r in conn.execute("PRAGMA table_info(messages)").fetchall()]
    if "category" not in msg_cols:
        conn.execute("ALTER TABLE messages ADD COLUMN category TEXT DEFAULT 'Primary'")
    if "unsubscribe_info" not in msg_cols:
        conn.execute("ALTER TABLE messages ADD COLUMN unsubscribe_info TEXT DEFAULT ''")

    cnt_cols = [r["name"] for r in conn.execute("PRAGMA table_info(contacts)").fetchall()]
    new_contact_cols = {
        "phone1": "TEXT DEFAULT ''",
        "phone1_label": "TEXT DEFAULT 'Mobile'",
        "phone2": "TEXT DEFAULT ''",
        "phone2_label": "TEXT DEFAULT 'Work'",
        "phone3": "TEXT DEFAULT ''",
        "phone3_label": "TEXT DEFAULT 'Home'",
        "employer": "TEXT DEFAULT ''",
        "school": "TEXT DEFAULT ''",
        "allegiances": "TEXT DEFAULT ''",
        "social_links": "TEXT DEFAULT '[]'",
        "relationship": "TEXT DEFAULT 'Other'",
        "is_blocked": "INTEGER DEFAULT 0"
    }
    for col, col_def in new_contact_cols.items():
        if col not in cnt_cols:
            conn.execute(f"ALTER TABLE contacts ADD COLUMN {col} {col_def}")

# -------------------------------------------------------------------------
# Accounts Management
# -------------------------------------------------------------------------
def add_account(
    name: str,
    email_address: str,
    account_type: str,
    incoming_host: str,
    incoming_port: int,
    incoming_security: str,
    incoming_username: str,
    incoming_password: str,
    smtp_host: str,
    smtp_port: int,
    smtp_security: str,
    smtp_username: str,
    smtp_password: str,
    keep_on_server: bool = True,
    signature: str = ""
) -> int:
    enc_in_pass = encrypt_secret(incoming_password)
    enc_smtp_pass = encrypt_secret(smtp_password)
    
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO accounts (
                name, email_address, account_type,
                incoming_host, incoming_port, incoming_security, incoming_username, incoming_password_enc,
                smtp_host, smtp_port, smtp_security, smtp_username, smtp_password_enc,
                keep_on_server, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email_address, account_type.upper(),
            incoming_host, incoming_port, incoming_security, incoming_username, enc_in_pass,
            smtp_host, smtp_port, smtp_security, smtp_username, enc_smtp_pass,
            1 if keep_on_server else 0, signature
        ))
        acc_id = cur.lastrowid
        
        default_folders = [
            ("Inbox", "inbox"),
            ("Sent", "sent"),
            ("Drafts", "drafts"),
            ("Archive", "archive"),
            ("Spam", "spam"),
            ("Trash", "trash"),
        ]
        for fname, ftype in default_folders:
            conn.execute("INSERT OR IGNORE INTO folders (account_id, name, folder_type) VALUES (?, ?, ?)",
                         (acc_id, fname, ftype))
        return acc_id

def update_account(
    account_id: int,
    name: str,
    email_address: str,
    account_type: str,
    incoming_host: str,
    incoming_port: int,
    incoming_security: str,
    incoming_username: str,
    incoming_password: str,
    smtp_host: str,
    smtp_port: int,
    smtp_security: str,
    smtp_username: str,
    smtp_password: str,
    keep_on_server: bool = True,
    signature: str = ""
):
    enc_in_pass = encrypt_secret(incoming_password)
    enc_smtp_pass = encrypt_secret(smtp_password)
    
    with get_connection() as conn:
        conn.execute("""
            UPDATE accounts SET
                name = ?, email_address = ?, account_type = ?,
                incoming_host = ?, incoming_port = ?, incoming_security = ?,
                incoming_username = ?, incoming_password_enc = ?,
                smtp_host = ?, smtp_port = ?, smtp_security = ?,
                smtp_username = ?, smtp_password_enc = ?,
                keep_on_server = ?, signature = ?
            WHERE id = ?
        """, (
            name, email_address, account_type.upper(),
            incoming_host, incoming_port, incoming_security,
            incoming_username, enc_in_pass,
            smtp_host, smtp_port, smtp_security,
            smtp_username, enc_smtp_pass,
            1 if keep_on_server else 0, signature,
            account_id
        ))

def delete_account(account_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))

def get_accounts() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
        accounts = []
        for r in rows:
            acc = dict(r)
            acc["incoming_password"] = decrypt_secret(acc["incoming_password_enc"])
            acc["smtp_password"] = decrypt_secret(acc["smtp_password_enc"])
            accounts.append(acc)
        return accounts

def get_account_by_id(account_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not row:
            return None
        acc = dict(row)
        acc["incoming_password"] = decrypt_secret(acc["incoming_password_enc"])
        acc["smtp_password"] = decrypt_secret(acc["smtp_password_enc"])
        return acc

# -------------------------------------------------------------------------
# Folder Management
# -------------------------------------------------------------------------
def get_folders_for_account(account_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM folders WHERE account_id = ? ORDER BY id ASC", (account_id,)).fetchall()
        return [dict(r) for r in rows]

def get_folder_by_type(account_id: int, folder_type: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM folders WHERE account_id = ? AND folder_type = ?", (account_id, folder_type)).fetchone()
        return dict(row) if row else None

def create_custom_folder(account_id: int, folder_name: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO folders (account_id, name, folder_type) VALUES (?, ?, 'custom')",
            (account_id, folder_name.strip())
        )
        return cur.lastrowid

def rename_folder(folder_id: int, new_name: str):
    with get_connection() as conn:
        conn.execute("UPDATE folders SET name = ? WHERE id = ? AND folder_type = 'custom'", (new_name.strip(), folder_id))

def delete_folder(folder_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT account_id, folder_type FROM folders WHERE id = ?", (folder_id,)).fetchone()
        if row and row["folder_type"] == "custom":
            trash = conn.execute("SELECT id FROM folders WHERE account_id = ? AND folder_type = 'trash'", (row["account_id"],)).fetchone()
            if trash:
                conn.execute("UPDATE messages SET folder_id = ? WHERE folder_id = ?", (trash["id"], folder_id))
            conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))

# -------------------------------------------------------------------------
# Message Storage & Querying
# -------------------------------------------------------------------------
def get_known_uids(account_id: int) -> set[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT server_uid FROM messages WHERE account_id = ? AND server_uid IS NOT NULL", (account_id,)).fetchall()
        return {r["server_uid"] for r in rows}

def get_known_message_ids(account_id: int) -> set[str]:
    """Returns known RFC Message-IDs for cross-protocol (IMAP <-> POP3) deduplication."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT message_id FROM messages WHERE account_id = ? AND message_id IS NOT NULL AND message_id != ''",
            (account_id,)
        ).fetchall()
        return {r["message_id"].strip() for r in rows}

def save_message(
    account_id: int,
    folder_id: int,
    server_uid: str | None,
    message_id: str | None,
    subject: str,
    sender: str,
    recipient: str,
    cc: str,
    bcc: str,
    date: str,
    body_plain: str,
    body_html: str,
    size_bytes: int,
    raw_headers: str,
    has_attachments: bool,
    security_verdict: str = "CLEAN",
    category: str = "Primary",
    unsubscribe_info: str = "",
    attachments_meta: list[dict] = None
) -> int:
    with get_connection() as conn:
        # Check if message already exists by (account_id, server_uid) or non-empty message_id
        existing = None
        if server_uid:
            existing = conn.execute(
                "SELECT id FROM messages WHERE account_id = ? AND server_uid = ?",
                (account_id, server_uid)
            ).fetchone()
        if not existing and message_id and message_id.strip():
            existing = conn.execute(
                "SELECT id FROM messages WHERE account_id = ? AND message_id = ?",
                (account_id, message_id.strip())
            ).fetchone()

        if existing:
            return existing["id"]

        cur = conn.execute("""
            INSERT INTO messages (
                account_id, folder_id, server_uid, message_id, subject, sender, recipient,
                cc, bcc, date, body_plain, body_html, size_bytes, has_attachments,
                raw_headers, security_verdict, category, unsubscribe_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_id, folder_id, server_uid, message_id, subject or "(No Subject)", sender, recipient,
            cc, bcc, date, body_plain, body_html, size_bytes, 1 if has_attachments else 0,
            raw_headers, security_verdict, category, unsubscribe_info
        ))
        msg_db_id = cur.lastrowid
        if attachments_meta and msg_db_id:
            for att in attachments_meta:
                conn.execute("""
                    INSERT INTO attachments (message_id, filename, content_type, size_bytes, file_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    msg_db_id,
                    att.get("filename", "attachment.bin"),
                    att.get("content_type", "application/octet-stream"),
                    att.get("size_bytes", 0),
                    str(att.get("file_path", ""))
                ))
        return msg_db_id

def get_messages_in_folder(
    folder_id: int,
    search_term: str = "",
    filter_mode: str = "ALL",
    category: str = "ALL"
) -> list[dict]:
    with get_connection() as conn:
        clauses = ["folder_id = ?"]
        params = [folder_id]

        if filter_mode == "UNREAD":
            clauses.append("is_read = 0")
        elif filter_mode == "FLAGGED":
            clauses.append("is_flagged = 1")
        elif filter_mode == "ATTACHMENTS":
            clauses.append("has_attachments = 1")

        if category and category != "ALL":
            clauses.append("category = ?")
            params.append(category)

        if search_term:
            clauses.append("(subject LIKE ? OR sender LIKE ? OR recipient LIKE ? OR body_plain LIKE ?)")
            like_term = f"%{search_term}%"
            params.extend([like_term, like_term, like_term, like_term])

        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT id, account_id, folder_id, server_uid, subject, sender, recipient,
                   date, size_bytes, is_read, is_flagged, has_attachments, security_verdict,
                   category, unsubscribe_info
            FROM messages
            WHERE {where_sql}
            ORDER BY date DESC, id DESC
        """
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

def get_message_full(message_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return None
        msg = dict(row)
        att_rows = conn.execute("SELECT * FROM attachments WHERE message_id = ?", (message_id,)).fetchall()
        msg["attachments"] = [dict(a) for a in att_rows]
        return msg

def mark_message_read(message_id: int, is_read: bool = True):
    with get_connection() as conn:
        conn.execute("UPDATE messages SET is_read = ? WHERE id = ?", (1 if is_read else 0, message_id))

def mark_all_read_in_folder(folder_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE messages SET is_read = 1 WHERE folder_id = ?", (folder_id,))

def toggle_message_flag(message_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT is_flagged FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["is_flagged"] else 1
        conn.execute("UPDATE messages SET is_flagged = ? WHERE id = ?", (new_val, message_id))
        return bool(new_val)

def set_message_category(message_id: int, category: str):
    with get_connection() as conn:
        conn.execute("UPDATE messages SET category = ? WHERE id = ?", (category, message_id))

def move_message_to_folder(message_id: int, target_folder_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE messages SET folder_id = ? WHERE id = ?", (target_folder_id, message_id))

def delete_message(message_id: int):
    """If message is not in Trash, moves it to Trash; if already in Trash, permanently deletes it."""
    with get_connection() as conn:
        row = conn.execute("SELECT account_id, folder_id FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return
        trash = conn.execute(
            "SELECT id FROM folders WHERE account_id = ? AND folder_type = 'trash'",
            (row["account_id"],)
        ).fetchone()
        if trash and row["folder_id"] != trash["id"]:
            conn.execute("UPDATE messages SET folder_id = ? WHERE id = ?", (trash["id"], message_id))
        else:
            conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))

def shred_message(message_id: int):
    """Permanently shreds a message and overwrites cached attachment files on disk (Burn After Reading)."""
    import os
    with get_connection() as conn:
        att_rows = conn.execute("SELECT file_path FROM attachments WHERE message_id = ?", (message_id,)).fetchall()
        for att in att_rows:
            fp = Path(att["file_path"])
            if fp.is_file():
                try:
                    size = fp.stat().st_size
                    if size > 0:
                        fp.write_bytes(os.urandom(min(size, 1024 * 1024)))
                    fp.unlink(missing_ok=True)
                except Exception:
                    pass
        # Overwrite sensitive columns in SQLite before deleting row
        conn.execute(
            "UPDATE messages SET subject='[REDACTED]', sender='[REDACTED]', body_plain='', body_html='', raw_headers='' WHERE id = ?",
            (message_id,)
        )
        conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))

def archive_message(message_id: int):
    """Moves a message to the account's Archive folder."""
    with get_connection() as conn:
        row = conn.execute("SELECT account_id FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return
        arc = conn.execute(
            "SELECT id FROM folders WHERE account_id = ? AND folder_type = 'archive'",
            (row["account_id"],)
        ).fetchone()
        if arc:
            conn.execute("UPDATE messages SET folder_id = ? WHERE id = ?", (arc["id"], message_id))

def mark_message_spam(message_id: int):
    """Moves a message to the account's Spam folder."""
    with get_connection() as conn:
        row = conn.execute("SELECT account_id FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return
        spam = conn.execute(
            "SELECT id FROM folders WHERE account_id = ? AND folder_type = 'spam'",
            (row["account_id"],)
        ).fetchone()
        if spam:
            conn.execute("UPDATE messages SET folder_id = ? WHERE id = ?", (spam["id"], message_id))

def empty_trash_for_account(account_id: int):
    with get_connection() as conn:
        trash = conn.execute(
            "SELECT id FROM folders WHERE account_id = ? AND folder_type = 'trash'",
            (account_id,)
        ).fetchone()
        if trash:
            conn.execute("DELETE FROM messages WHERE folder_id = ?", (trash["id"],))

def get_unread_count(folder_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM messages WHERE folder_id = ? AND is_read = 0", (folder_id,)).fetchone()
        return row["cnt"] if row else 0

def get_total_count(folder_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM messages WHERE folder_id = ?", (folder_id,)).fetchone()
        return row["cnt"] if row else 0

# -------------------------------------------------------------------------
# Advanced Contact List / Sheet Management
# -------------------------------------------------------------------------
def get_contacts() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM contacts ORDER BY name ASC, email ASC").fetchall()
        contacts = []
        for r in rows:
            c = dict(r)
            try:
                c["social_links_parsed"] = json.loads(c.get("social_links") or "[]")
            except Exception:
                c["social_links_parsed"] = []
            contacts.append(c)
        return contacts

def get_contact_by_email(email_addr: str) -> dict | None:
    with get_connection() as conn:
        clean = email_addr.strip().lower()
        row = conn.execute("SELECT * FROM contacts WHERE LOWER(email) = ?", (clean,)).fetchone()
        if not row:
            return None
        c = dict(row)
        try:
            c["social_links_parsed"] = json.loads(c.get("social_links") or "[]")
        except Exception:
            c["social_links_parsed"] = []
        return c

def save_contact(
    name: str,
    email_addr: str,
    phone1: str = "",
    phone1_label: str = "Mobile",
    phone2: str = "",
    phone2_label: str = "Work",
    phone3: str = "",
    phone3_label: str = "Home",
    employer: str = "",
    school: str = "",
    allegiances: str = "",
    notes: str = "",
    social_links: list[dict] = None,
    relationship: str = "Other",
    is_blocked: bool = False,
    contact_id: int = None
) -> int:
    social_json = json.dumps(social_links or [])
    with get_connection() as conn:
        if contact_id:
            conn.execute("""
                UPDATE contacts SET
                    name = ?, email = ?,
                    phone1 = ?, phone1_label = ?,
                    phone2 = ?, phone2_label = ?,
                    phone3 = ?, phone3_label = ?,
                    employer = ?, school = ?, allegiances = ?,
                    notes = ?, social_links = ?, relationship = ?, is_blocked = ?
                WHERE id = ?
            """, (
                name.strip(), email_addr.strip(),
                phone1.strip(), phone1_label,
                phone2.strip(), phone2_label,
                phone3.strip(), phone3_label,
                employer.strip(), school.strip(), allegiances.strip(),
                notes.strip(), social_json, relationship, 1 if is_blocked else 0,
                contact_id
            ))
            return contact_id
        else:
            cur = conn.execute("""
                INSERT INTO contacts (
                    name, email, phone1, phone1_label, phone2, phone2_label, phone3, phone3_label,
                    employer, school, allegiances, notes, social_links, relationship, is_blocked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    phone1 = excluded.phone1, phone1_label = excluded.phone1_label,
                    phone2 = excluded.phone2, phone2_label = excluded.phone2_label,
                    phone3 = excluded.phone3, phone3_label = excluded.phone3_label,
                    employer = excluded.employer, school = excluded.school, allegiances = excluded.allegiances,
                    notes = excluded.notes, social_links = excluded.social_links,
                    relationship = excluded.relationship, is_blocked = excluded.is_blocked
            """, (
                name.strip(), email_addr.strip(),
                phone1.strip(), phone1_label,
                phone2.strip(), phone2_label,
                phone3.strip(), phone3_label,
                employer.strip(), school.strip(), allegiances.strip(),
                notes.strip(), social_json, relationship, 1 if is_blocked else 0
            ))
            return cur.lastrowid

def add_or_update_contact(name: str, email_addr: str, organization: str = "", notes: str = ""):
    """Convenience helper for quick contact insertion."""
    save_contact(name=name, email_addr=email_addr, employer=organization, notes=notes)

def delete_contact(contact_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

def set_contact_blocked(email_addr: str, is_blocked: bool = True):
    with get_connection() as conn:
        conn.execute("UPDATE contacts SET is_blocked = ? WHERE LOWER(email) = ?", (1 if is_blocked else 0, email_addr.strip().lower()))

# -------------------------------------------------------------------------
# Rules, Blacklist & Filters
# -------------------------------------------------------------------------
def get_rules(account_id: int = None) -> list[dict]:
    with get_connection() as conn:
        if account_id:
            rows = conn.execute("SELECT * FROM rules WHERE account_id = ? OR account_id IS NULL ORDER BY id DESC", (account_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM rules ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def add_rule(rule_type: str, pattern: str, action: str = "spam", target_folder_id: int = None, account_id: int = None) -> int:
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO rules (account_id, rule_type, pattern, action, target_folder_id, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (account_id, rule_type, pattern.strip().lower(), action, target_folder_id))
        return cur.lastrowid

def delete_rule(rule_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,))

def toggle_rule(rule_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT is_active FROM rules WHERE id = ?", (rule_id,)).fetchone()
        if row:
            new_val = 0 if row["is_active"] else 1
            conn.execute("UPDATE rules SET is_active = ? WHERE id = ?", (new_val, rule_id))

# -------------------------------------------------------------------------
# App Settings
# -------------------------------------------------------------------------
def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
