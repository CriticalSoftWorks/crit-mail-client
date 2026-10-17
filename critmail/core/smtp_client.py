"""
CritMail Core - SMTP Protocol Client
Safe, authenticated message transmission with TLS 1.2+
"""
import ssl
import time
import socket
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, getaddresses, formataddr
import mimetypes
from pathlib import Path
from critmail.core.pop3_client import create_secure_ssl_context
from critmail.models.database import save_message, get_folder_by_type

class SmtpEngine:
    """Safe, fast SMTP client with automatic retry handling."""
    def __init__(self, account: dict):
        self.account = account
        self.host = account["smtp_host"]
        self.port = int(account["smtp_port"])
        self.security = account["smtp_security"]
        self.username = account["smtp_username"]
        self.password = account["smtp_password"]
        self.account_id = account["id"]

    def test_connection(self) -> tuple[bool, str]:
        """Tests SMTP authentication and server reachability."""
        try:
            client = self._connect()
            client.quit()
            return True, "SMTP Connection and Authentication Successful!"
        except Exception as e:
            return False, f"SMTP Error: {e}"

    def _connect(self) -> smtplib.SMTP:
        """Establishes authenticated SMTP / SMTP_SSL connection with resilient retry."""
        context = create_secure_ssl_context()
        last_err = None
        for attempt in range(3):
            try:
                if self.security == "SSL/TLS":
                    client = smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=20)
                else:
                    client = smtplib.SMTP(self.host, self.port, timeout=20)
                    if self.security == "STARTTLS":
                        client.starttls(context=context)

                if self.username and self.password:
                    client.login(self.username, self.password)
                return client
            except Exception as e:
                last_err = e
                time.sleep(1.2)
        raise last_err or Exception("Failed to connect to SMTP server after retries")

    def send_message(
        self,
        to_addrs: list[str],
        subject: str,
        body_text: str,
        body_html: str = "",
        cc_addrs: list[str] = None,
        bcc_addrs: list[str] = None,
        attachment_paths: list[str] = None
    ) -> bool:
        """Constructs RFC5322 MIME message, sends via SMTP, and saves to Sent folder."""
        msg = EmailMessage()
        msg["Subject"] = subject
        sender_name = (self.account.get("name") or "").strip()
        sender_email = self.account["email_address"].strip()
        msg["From"] = formataddr((sender_name, sender_email)) if sender_name else sender_email
        msg["To"] = ", ".join(to_addrs)
        
        if cc_addrs:
            msg["Cc"] = ", ".join(cc_addrs)
        if bcc_addrs:
            msg["Bcc"] = ", ".join(bcc_addrs)
            
        msg["Date"] = formatdate(localtime=True)
        msg_id = make_msgid(domain=self.account.get("email_address", "").split("@")[-1] or None)
        msg["Message-ID"] = msg_id

        # Body: Plain text and optional HTML
        if body_html:
            msg.set_content(body_text)
            msg.add_alternative(body_html, subtype="html")
        else:
            msg.set_content(body_text)

        # Attachments
        if attachment_paths:
            for p_str in attachment_paths:
                path = Path(p_str)
                if not path.is_file():
                    continue
                ctype, encoding = mimetypes.guess_type(str(path))
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                
                with open(path, "rb") as f:
                    msg.add_attachment(
                        f.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=path.name
                    )

        # Send via server
        client = self._connect()
        try:
            raw_list = list(to_addrs) + list(cc_addrs or []) + list(bcc_addrs or [])
            parsed_rcpts = [addr for _, addr in getaddresses(raw_list) if addr and "@" in addr]
            all_recipients = list(dict.fromkeys(parsed_rcpts)) or raw_list
            client.send_message(msg, to_addrs=all_recipients)
        finally:
            try:
                client.quit()
            except Exception:
                pass

        # Save to local Sent folder
        sent_folder = get_folder_by_type(self.account_id, "sent")
        if sent_folder:
            save_message(
                account_id=self.account_id,
                folder_id=sent_folder["id"],
                server_uid=f"sent-{msg_id}",
                message_id=msg_id,
                subject=subject,
                sender=self.account["email_address"],
                recipient=", ".join(to_addrs),
                cc=", ".join(cc_addrs or []),
                bcc=", ".join(bcc_addrs or []),
                date=formatdate(localtime=True),
                body_plain=body_text,
                body_html=body_html,
                size_bytes=len(msg.as_bytes()),
                raw_headers=str(msg.items()),
                has_attachments=bool(attachment_paths),
                security_verdict="CLEAN"
            )
        return True
