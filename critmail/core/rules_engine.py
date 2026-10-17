"""
CritMail Core - Rules & Blacklist Filtering Engine
Evaluates incoming messages against blocked senders, blocked domains, keyword filters,
and routes mail to Spam, Trash, or designated folders automatically.
"""
from critmail.models.database import (
    get_rules, get_contact_by_email, get_folder_by_type
)

def evaluate_message_routing(
    account_id: int,
    sender: str,
    subject: str,
    body_plain: str = "",
    raw_headers: str = ""
) -> tuple[str, int | None]:
    """
    Evaluates message against contacts blacklist and user-defined rules.
    Returns:
        (verdict_action: str, target_folder_id: int | None)
        actions: 'inbox', 'spam', 'trash', 'delete', 'custom_folder'
    """
    clean_sender = sender.lower()
    email_addr = clean_sender.split("<")[-1].rstrip(">").strip() if "<" in clean_sender else clean_sender.strip()
    domain = email_addr.split("@")[-1].strip() if "@" in email_addr else ""

    # 1. Check if contact is marked as Blocked / Ignored
    contact = get_contact_by_email(email_addr)
    if contact and contact.get("is_blocked"):
        spam_folder = get_folder_by_type(account_id, "spam")
        return "spam", spam_folder["id"] if spam_folder else None

    # 2. Check User-Defined Rules & Blacklist
    rules = get_rules(account_id)
    subject_lower = subject.lower()
    body_lower = body_plain.lower() if body_plain else ""

    for r in rules:
        if not r.get("is_active"):
            continue

        rtype = r["rule_type"]
        pat = r["pattern"].lower()
        matched = False

        if rtype == "sender" and pat in email_addr:
            matched = True
        elif rtype == "domain" and pat in domain:
            matched = True
        elif rtype == "keyword" and (pat in subject_lower or pat in body_lower):
            matched = True
        elif rtype == "header" and pat in raw_headers.lower():
            matched = True

        if matched:
            action = r["action"]
            if action == "spam":
                spam_fld = get_folder_by_type(account_id, "spam")
                return "spam", spam_fld["id"] if spam_fld else None
            elif action == "trash":
                trash_fld = get_folder_by_type(account_id, "trash")
                return "trash", trash_fld["id"] if trash_fld else None
            elif action == "move_folder" and r.get("target_folder_id"):
                return "custom_folder", r["target_folder_id"]
            elif action == "delete":
                return "delete", None

    # Default to standard Inbox
    inbox_folder = get_folder_by_type(account_id, "inbox")
    return "inbox", inbox_folder["id"] if inbox_folder else None

def auto_categorize_message(sender: str, subject: str, raw_headers: str = "") -> str:
    """
    Categorizes message into Primary, Social, Updates, Promotions, or Forums.
    """
    s_lower = sender.lower()
    subj_lower = subject.lower()
    hdr_lower = raw_headers.lower()

    # Social markers
    social_domains = ["facebookmail.com", "linkedin.com", "twitter.com", "x.com", "instagram.com", "threads.net", "tiktok.com"]
    if any(d in s_lower for d in social_domains):
        return "Social"

    # Forums / Mailing list markers
    if "list-id:" in hdr_lower or "mailing-list:" in hdr_lower or "groups.google.com" in s_lower or "github.com" in s_lower:
        return "Forums"

    # Promotional / Marketing markers
    promo_words = ["sale", "discount", "% off", "clearance", "exclusive deal", "special offer", "save big", "coupon"]
    if any(w in subj_lower for w in promo_words) or "list-unsubscribe" in hdr_lower:
        if "order confirmation" not in subj_lower and "receipt" not in subj_lower and "invoice" not in subj_lower:
            return "Promotions"

    # Transactional / Updates
    update_words = ["invoice", "receipt", "statement", "security alert", "password reset", "account notification", "verification code"]
    if any(w in subj_lower for w in update_words):
        return "Updates"

    return "Primary"


def process_automated_forwarding_and_vacation(
    account: dict,
    sender: str,
    subject: str,
    body_plain: str = "",
    raw_headers: str = ""
) -> bool:
    """
    Executes automated Mail Forwarding and Vacation Auto-Reply if enabled in Security Settings.
    Returns:
        keep_local_copy (bool): True if the message should still be saved in the local Inbox.
    """
    from email.utils import parseaddr
    from critmail.models.database import get_setting
    from critmail.core.smtp_client import SmtpEngine

    _, sender_email = parseaddr(sender)
    sender_email = sender_email.strip().lower()
    own_email = account.get("email_address", "").strip().lower()

    # Never trigger auto-forward or auto-reply loops on messages from self
    if not sender_email or sender_email == own_email:
        return True

    hdr_lower = (raw_headers or "").lower()
    is_automated = (
        "auto-submitted:" in hdr_lower
        or "precedence: bulk" in hdr_lower
        or "precedence: list" in hdr_lower
        or "x-autoreply" in hdr_lower
        or "mailer-daemon" in sender_email
        or "noreply" in sender_email
        or "no-reply" in sender_email
    )

    # 1. Automated Mail Forwarding
    keep_local = True
    if get_setting("fwd_enabled", "0") == "1":
        fwd_target = get_setting("fwd_email", "").strip()
        if fwd_target and "@" in fwd_target and fwd_target.lower() != own_email:
            try:
                smtp = SmtpEngine(account)
                fwd_body = (
                    f"--- [CRITMAIL AUTOMATED RELAY // FORWARDED MESSAGE] ---\n"
                    f"Original Sender: {sender}\n"
                    f"Original Subject: {subject}\n\n"
                    f"{body_plain}"
                )
                smtp.send_message(
                    to_addrs=[fwd_target],
                    subject=f"[FWD] {subject}",
                    body_text=fwd_body
                )
                if get_setting("fwd_keep", "1") == "0":
                    keep_local = False
            except Exception:
                pass

    # 2. Automated Out-of-Office / Vacation Responder
    if get_setting("vac_enabled", "0") == "1" and not is_automated:
        vac_msg = get_setting("vac_msg", "").strip()
        if vac_msg:
            try:
                smtp = SmtpEngine(account)
                smtp.send_message(
                    to_addrs=[sender_email],
                    subject=f"Auto-Reply: Re: {subject}",
                    body_text=vac_msg
                )
            except Exception:
                pass

    return keep_local
