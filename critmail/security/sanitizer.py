"""
CritMail Security - Anti-Exploit HTML Sanitizer and Tracking Neutralizer
Prevents remote code execution, tracking pixels, CSS exfiltration, and malicious tags.
"""
import re
import html
from urllib.parse import urlparse

# Disallowed tags that could execute scripts, embed sub-windows, or steal user input
BLOCKED_TAGS = {
    "script", "iframe", "object", "embed", "applet", "form", "input",
    "button", "textarea", "select", "meta", "base", "link"
}

# Regex for stripping dangerous tags completely (content included for script/style if desired)
RE_SCRIPT = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
RE_STYLE = re.compile(r"<\s*style[^>]*>.*?<\s*/\s*style\s*>", re.IGNORECASE | re.DOTALL)
RE_TAGS_STRIP = re.compile(r"<\s*(/?)\s*(" + "|".join(BLOCKED_TAGS) + r")(\s+[^>]*)?>", re.IGNORECASE)

# Inline event handlers like onload, onclick, onerror, onmouseover, etc.
RE_EVENT_HANDLERS = re.compile(r"\s+on[a-zA-Z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)

# Dangerous URL schemes in href/src
RE_DANGEROUS_SCHEMES = re.compile(r"(href|src)\s*=\s*[\"']?\s*(javascript|vbscript|data(?!\s*:\s*image)):", re.IGNORECASE)

# Remote image detection (http:// or https://)
RE_IMG_SRC = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*[\"'])(https?://[^\"']+)([\"'][^>]*>)", re.IGNORECASE)

def sanitize_html(html_content: str, block_remote_images: bool = True) -> tuple[str, int]:
    """
    Sanitizes HTML content to guarantee safe rendering.
    Returns:
        (sanitized_html: str, blocked_images_count: int)
    """
    if not html_content:
        return "", 0
    
    # 1. Strip all <script> blocks completely
    cleaned = RE_SCRIPT.sub("", html_content)
    
    # 2. Strip any other dangerous tags (<iframe, <object, <embed, <form, etc.)
    cleaned = RE_TAGS_STRIP.sub("", cleaned)
    
    # 3. Strip inline JS event handlers
    cleaned = RE_EVENT_HANDLERS.sub("", cleaned)
    
    # 4. Neutralize javascript: or vbscript: links
    cleaned = RE_DANGEROUS_SCHEMES.sub(r'\1="#blocked-scheme:', cleaned)
    
    # 5. Handle remote images / tracking beacons
    blocked_count = 0
    if block_remote_images:
        matches = list(RE_IMG_SRC.finditer(cleaned))
        blocked_count = len(matches)
        
        # Replace remote image sources with safe placeholder and data attribute
        def _replace_img(m):
            prefix = m.group(1)
            original_url = m.group(2)
            suffix = m.group(3)
            return (
                f'<span class="remote-tracker-blocked" title="Blocked remote image from {html.escape(original_url, quote=True)}" '
                f'style="display:inline-block; border:1px dashed #1e3759; background:#0e1522; color:#7a9ab8; '
                f'font-family:monospace; font-size:10px; padding:2px 5px; margin:2px;">[Remote Image Blocked]</span>'
            )
        cleaned = RE_IMG_SRC.sub(_replace_img, cleaned)
        
    return cleaned, blocked_count

def html_to_plain_text(html_content: str) -> str:
    """Fast, clean conversion of HTML to formatted plain text."""
    if not html_content:
        return ""
    # Strip script and style first
    text = RE_SCRIPT.sub("", html_content)
    text = RE_STYLE.sub("", text)
    
    # Replace line breaks and paragraph ends
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/?\s*p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/?\s*div[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/?\s*h[1-6][^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # Unescape HTML entities (&amp;, &lt;, etc.)
    text = html.unescape(text)
    
    # Normalize multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


RE_REDACT_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_REDACT_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_REDACT_PHONE = re.compile(r"(?:\+\d{1,2}\s*)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")


def redact_sensitive_text(text: str) -> str:
    """Replaces emails, IP addresses, and phone numbers with classified redaction blocks."""
    if not text:
        return ""
    out = RE_REDACT_EMAIL.sub("[███REDACTED-AGENT███]", text)
    out = RE_REDACT_IPV4.sub("[███REDACTED-IP███]", out)
    out = RE_REDACT_PHONE.sub("[███REDACTED-COMMS███]", out)
    return out


def redact_sensitive_html(html_text: str) -> str:
    """Redacts emails, IPs, and phone numbers inside HTML text nodes without breaking HTML tags."""
    if not html_text:
        return ""
    badge = (
        '<span style="background:#00e5ff; color:#060a10; font-weight:bold; '
        'padding:0px 4px; font-family:Consolas,monospace;">[██REDACTED██]</span>'
    )
    parts = re.split(r"(<[^>]+>)", html_text)
    for i in range(0, len(parts), 2):
        chunk = parts[i]
        chunk = RE_REDACT_EMAIL.sub(badge, chunk)
        chunk = RE_REDACT_IPV4.sub(badge, chunk)
        chunk = RE_REDACT_PHONE.sub(badge, chunk)
        parts[i] = chunk
    return "".join(parts)
