"""
CritMail Core - IMAP4 SSL/TLS Protocol Client
High-Speed, Secure IMAP4_SSL Engine with Rules Evaluation, Auto-Categorization & Unsubscribe Extraction
"""
import imaplib
import email
from email import policy
from pathlib import Path
from critmail.config import CACHE_DIR
from critmail.core.pop3_client import decode_mime_words, create_secure_ssl_context
from critmail.security.sanitizer import sanitize_html, html_to_plain_text
from critmail.security.unsubscribe import extract_unsubscribe_info, format_unsubscribe_json
from critmail.core.rules_engine import (
    evaluate_message_routing, auto_categorize_message, process_automated_forwarding_and_vacation
)
from critmail.models.database import (
    get_known_uids, get_known_message_ids, save_message, get_folder_by_type
)

class ImapEngine:
    """Safe, fast IMAP4_SSL client with UID synchronization."""
    def __init__(self, account: dict):
        self.account = account
        self.host = account["incoming_host"]
        raw_port = int(account["incoming_port"])
        self.port = 993 if raw_port == 995 else raw_port
        self.security = account["incoming_security"]
        self.username = account["incoming_username"]
        self.password = account["incoming_password"]
        self.account_id = account["id"]

    def test_connection(self) -> tuple[bool, str]:
        """Tests login and connectivity to the IMAP4 server."""
        try:
            client = self._connect()
            client.logout()
            return True, f"IMAP4 ({self.host}:{self.port}) SSL/TLS Connection & Auth Successful!"
        except Exception as e:
            return False, f"IMAP4 Error: {e}"

    def _connect(self) -> imaplib.IMAP4:
        """Establishes authenticated IMAP4_SSL / STARTTLS connection."""
        context = create_secure_ssl_context()
        if self.security == "SSL/TLS":
            client = imaplib.IMAP4_SSL(self.host, self.port, ssl_context=context, timeout=20)
        else:
            client = imaplib.IMAP4(self.host, self.port, timeout=20)
            if self.security == "STARTTLS":
                client.starttls(ssl_context=context)

        if not self.password:
            raise ValueError("Password not configured yet. Click 'ACCOUNTS' to enter your password.")

        client.login(self.username, self.password)
        return client

    def fetch_new_messages(self, progress_callback=None) -> int:
        """
        Synchronizes incoming messages from IMAP INBOX using UIDs.
        Applies rules, categorizes, and extracts unsubscribe metadata.
        """
        inbox_folder = get_folder_by_type(self.account_id, "inbox")
        if not inbox_folder:
            return 0
        default_folder_id = inbox_folder["id"]
        known_uids = get_known_uids(self.account_id)
        known_msg_ids = get_known_message_ids(self.account_id)

        client = self._connect()
        try:
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                raise RuntimeError("Could not select INBOX on IMAP server.")

            status, data = client.uid("search", None, "ALL")
            if status != "OK" or not data or not data[0]:
                if progress_callback:
                    progress_callback(0, 0, "IMAP Inbox is empty.")
                return 0

            all_uids = [u.decode("ascii") for u in data[0].split()]
            new_uids = [uid for uid in all_uids if f"imap-{uid}" not in known_uids]
            total_new = len(new_uids)

            if total_new == 0:
                if progress_callback:
                    progress_callback(0, 0, "IMAP Inbox up to date. No new messages.")
                return 0

            downloaded_count = 0
            target_uids = new_uids[-100:]
            total_target = len(target_uids)

            for i, uid in enumerate(target_uids, 1):
                if progress_callback:
                    progress_callback(i, total_target, f"IMAP Sync {i}/{total_target} (UID {uid})...")

                status, msg_data = client.uid("fetch", uid, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_bytes = msg_data[0][1]
                if not isinstance(raw_bytes, bytes):
                    continue

                parsed_msg = email.message_from_bytes(raw_bytes, policy=policy.default)

                subject = decode_mime_words(parsed_msg.get("Subject", "(No Subject)"))
                sender = decode_mime_words(parsed_msg.get("From", "(Unknown Sender)"))
                recipient = decode_mime_words(parsed_msg.get("To", self.account.get("email_address", "")))
                cc = decode_mime_words(parsed_msg.get("Cc", ""))
                bcc = decode_mime_words(parsed_msg.get("Bcc", ""))
                message_id = (parsed_msg.get("Message-ID", "") or "").strip()
                date_str = parsed_msg.get("Date", "")

                if message_id and message_id in known_msg_ids:
                    continue

                body_plain = ""
                body_html = ""
                has_attachments = False
                attachments_meta = []

                if parsed_msg.is_multipart():
                    for part in parsed_msg.walk():
                        content_type = part.get_content_type()
                        content_disp = str(part.get("Content-Disposition", ""))

                        if "attachment" in content_disp or part.get_filename():
                            filename = part.get_filename()
                            if filename:
                                has_attachments = True
                                filename = decode_mime_words(filename)
                                att_info = self._cache_attachment(part, filename, uid)
                                if att_info:
                                    attachments_meta.append(att_info)
                                continue

                        if content_type == "text/plain" and not body_plain:
                            try:
                                body_plain = part.get_content()
                            except Exception:
                                payload = part.get_payload(decode=True)
                                body_plain = payload.decode("latin1", errors="replace") if payload else ""
                        elif content_type == "text/html" and not body_html:
                            try:
                                body_html = part.get_content()
                            except Exception:
                                payload = part.get_payload(decode=True)
                                body_html = payload.decode("latin1", errors="replace") if payload else ""
                else:
                    content_type = parsed_msg.get_content_type()
                    try:
                        content = parsed_msg.get_content()
                    except Exception:
                        payload = parsed_msg.get_payload(decode=True)
                        content = payload.decode("latin1", errors="replace") if payload else ""

                    if content_type == "text/html":
                        body_html = content
                    else:
                        body_plain = content

                if not body_plain and body_html:
                    body_plain = html_to_plain_text(body_html)

                verdict = "CLEAN"
                if body_html:
                    _, blocked_count = sanitize_html(body_html, block_remote_images=True)
                    if blocked_count > 0:
                        verdict = f"BLOCKED_REMOTE_{blocked_count}"

                raw_hdrs = "\n".join(f"{k}: {v}" for k, v in parsed_msg.items())

                # Unsubscribe detection
                unsub_info = extract_unsubscribe_info(raw_hdrs, body_html, body_plain)
                unsub_json = format_unsubscribe_json(unsub_info)

                # Automatic Categorization
                category = auto_categorize_message(sender, subject, raw_hdrs)

                # Rules and Blacklist Filtering
                action, target_folder_id = evaluate_message_routing(
                    self.account_id, sender, subject, body_plain, raw_hdrs
                )
                if action == "delete":
                    continue  # Discard immediately per user rule

                if action not in ("spam", "trash"):
                    keep_local = process_automated_forwarding_and_vacation(
                        self.account, sender, subject, body_plain, raw_hdrs
                    )
                    if not keep_local:
                        continue

                final_folder_id = target_folder_id or default_folder_id

                save_message(
                    account_id=self.account_id,
                    folder_id=final_folder_id,
                    server_uid=f"imap-{uid}",
                    message_id=message_id,
                    subject=subject,
                    sender=sender,
                    recipient=recipient,
                    cc=cc,
                    bcc=bcc,
                    date=date_str,
                    body_plain=body_plain,
                    body_html=body_html,
                    size_bytes=len(raw_bytes),
                    raw_headers=raw_hdrs,
                    has_attachments=has_attachments,
                    security_verdict=verdict,
                    category=category,
                    unsubscribe_info=unsub_json,
                    attachments_meta=attachments_meta
                )
                if message_id:
                    known_msg_ids.add(message_id)
                downloaded_count += 1

            return downloaded_count

        finally:
            try:
                client.logout()
            except Exception:
                pass

    def _cache_attachment(self, part, filename: str, uid: str) -> dict | None:
        safe_name = Path(filename).name
        save_dir = CACHE_DIR / f"acc_{self.account_id}" / f"msg_{uid}"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / safe_name

        payload = part.get_payload(decode=True)
        if payload:
            save_path.write_bytes(payload)
            return {
                "filename": safe_name,
                "content_type": part.get_content_type(),
                "size_bytes": len(payload),
                "file_path": str(save_path)
            }
        return None
