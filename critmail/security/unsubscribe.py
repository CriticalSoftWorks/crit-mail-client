"""
CritMail Security - One-Click Auto-Unsubscribe Engine
Parses RFC 2369 / RFC 8058 List-Unsubscribe headers and body unsubscribe links.
Allows safe automated unsubscription via mailto: email or verified HTTPS endpoints.
"""
import re
import json
from urllib.parse import urlparse

# Detection patterns for RFC 2369 headers
RE_UNSUB_HEADER_ITEM = re.compile(r"<([^>]+)>")

# Detection patterns for body unsubscribe links
RE_BODY_UNSUB_LINK = re.compile(
    r"""<a\b[^>]*?\bhref\s*=\s*["']([^"']*(?:unsubscribe|opt-?out|preferences|manage-sub)[^"']*)["'][^>]*>(.*?)</a>""",
    re.IGNORECASE
)

def extract_unsubscribe_info(raw_headers: str, body_html: str = "", body_plain: str = "") -> dict:
    """
    Extracts structured unsubscribe data from RFC headers and HTML/text bodies.
    Returns:
        {
            "has_unsubscribe": bool,
            "mailto": str or None,
            "url": str or None,
            "one_click_post": bool,
            "source": "header" or "body" or None
        }
    """
    mailto_target = None
    url_target = None
    one_click_post = False
    source = None

    # 1. Parse Headers for List-Unsubscribe & List-Unsubscribe-Post (with RFC 5322 line unfolding)
    if raw_headers:
        unfolded_lines = []
        for line in raw_headers.splitlines():
            if line.startswith((" ", "\t")) and unfolded_lines:
                unfolded_lines[-1] += " " + line.strip()
            else:
                unfolded_lines.append(line)

        for line in unfolded_lines:
            lower_line = line.lower()
            if lower_line.startswith("list-unsubscribe:"):
                header_val = line.split(":", 1)[1]
                matches = RE_UNSUB_HEADER_ITEM.findall(header_val)
                for item in matches:
                    item = item.strip()
                    if item.lower().startswith("mailto:") and not mailto_target:
                        mailto_target = item
                    elif item.lower().startswith("http") and not url_target:
                        url_target = item
                if matches:
                    source = "header"

            if lower_line.startswith("list-unsubscribe-post:"):
                val = line.split(":", 1)[1].strip()
                if "list-unsubscribe=one-click" in val.lower():
                    one_click_post = True

    # 2. Fallback: Parse HTML body if headers didn't have a direct unsubscribe link
    if not url_target and not mailto_target and body_html:
        match = RE_BODY_UNSUB_LINK.search(body_html)
        if match:
            url_cand = match.group(1).strip()
            if url_cand.startswith("http"):
                url_target = url_cand
                source = "body"

    has_unsub = bool(mailto_target or url_target)
    return {
        "has_unsubscribe": has_unsub,
        "mailto": mailto_target,
        "url": url_target,
        "one_click_post": one_click_post,
        "source": source
    }

def perform_one_click_post_unsubscribe(url: str) -> tuple[bool, str]:
    """Executes RFC 8058 One-Click POST unsubscribe request over HTTPS."""
    import urllib.request
    import ssl
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            return False, "RFC 8058 One-Click POST requires an HTTPS endpoint."
        data = b"List-Unsubscribe=One-Click"
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "CritMail-Security-Core/1.0"
            },
            method="POST"
        )
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                return True, f"RFC 8058 One-Click Unsubscribe POST succeeded (HTTP {code})."
            return False, f"Server returned HTTP {code}."
    except Exception as e:
        return False, str(e)

def format_unsubscribe_json(unsub_info: dict) -> str:
    """Serializes unsubscribe info into JSON for database storage."""
    if not unsub_info.get("has_unsubscribe"):
        return ""
    return json.dumps(unsub_info)

def parse_unsubscribe_json(json_str: str) -> dict:
    if not json_str:
        return {"has_unsubscribe": False, "mailto": None, "url": None, "one_click_post": False}
    try:
        return json.loads(json_str)
    except Exception:
        return {"has_unsubscribe": False, "mailto": None, "url": None, "one_click_post": False}
