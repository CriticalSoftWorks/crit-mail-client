import imaplib
import poplib
import smtplib
from critmail.models.database import get_accounts
from critmail.core.imap_client import ImapEngine
from critmail.core.pop3_client import Pop3Engine
from critmail.core.smtp_client import SmtpEngine

acc = get_accounts()[0]
print("Account email:", acc["email_address"])
print("Configured proto:", acc["account_type"])
print("Incoming host:", acc["incoming_host"])
print("Incoming port:", acc["incoming_port"])

# Test POP3
pop = Pop3Engine(acc)
try:
    p = pop._connect()
    stat = p.stat()
    print("POP3 stat (count, octets):", stat)
    p.quit()
except Exception as e:
    print("POP3 error:", e)

# Test IMAP
imap_acc = dict(acc)
imap_acc["account_type"] = "IMAP"
imap_acc["incoming_port"] = 993
imap = ImapEngine(imap_acc)
try:
    c = imap._connect()
    typ, folders = c.list()
    print("IMAP folders count:", len(folders))
    for f in folders:
        raw = f.decode("utf-8", "replace")
        print("Folder:", raw)
        import re
        m = re.search(r'\((.*?)\)\s+["\']?([^"\']+)["\']?\s+(.*)', raw)
        if m:
            box_name = m.group(3).strip().strip('"')
            status, cnt = c.select(f'"{box_name}"', readonly=True)
            print(f" -> {box_name}: {cnt[0].decode() if cnt else '0'} messages")
    c.logout()
except Exception as e:
    print("IMAP error:", e)

# Test SMTP
smtp = SmtpEngine(acc)
try:
    ok, msg = smtp.test_connection()
    print("SMTP connection test:", ok, msg)
except Exception as e:
    print("SMTP error:", e)
