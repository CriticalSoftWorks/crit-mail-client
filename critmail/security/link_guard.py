"""
CritMail Security - Anti-Phishing Link Guard
Inspects URLs for spoofing, homographs, punycode attacks, and suspicious IP addresses.
"""
import re
from urllib.parse import urlparse

# Detection patterns for phishing techniques
RE_IP_HOST = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
RE_HEX_OCT_IP = re.compile(r"^(0x[0-9a-fA-F]+|[0-9]{8,})$")

def inspect_url_security(url: str) -> dict:
    """
    Evaluates safety of a link before launching.
    Returns analysis dict with warnings and risk score.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Strip port if present for domain inspection
    host = netloc.split(":")[0] if ":" in netloc else netloc
    
    warnings = []
    risk_level = "LOW"  # LOW, MEDIUM, HIGH
    
    if scheme not in ("http", "https"):
        warnings.append(f"Uncommon protocol '{scheme}' (could be dangerous)")
        risk_level = "HIGH"
    elif scheme == "http":
        warnings.append("Connection is unencrypted HTTP (no TLS)")
        if risk_level != "HIGH":
            risk_level = "MEDIUM"
            
    # Punycode / IDN homograph attack check
    if host.startswith("xn--") or ".xn--" in host:
        warnings.append("Punycode domain detected (potential homograph/character spoofing attack)")
        risk_level = "HIGH"
        
    # Non-ASCII characters in host
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        warnings.append("Non-ASCII unicode characters in domain name (homoglyph risk)")
        risk_level = "HIGH"
        
    # Raw numeric IP address instead of domain
    if RE_IP_HOST.match(host) or RE_HEX_OCT_IP.match(host):
        warnings.append("Direct IP address used instead of domain name")
        risk_level = "HIGH"
        
    # Userinfo in URL (e.g., http://google.com@attacker.com)
    if "@" in parsed.netloc:
        warnings.append("Credential or sub-authority symbol '@' in URL (classic phishing lure)")
        risk_level = "HIGH"
        
    return {
        "url": url,
        "scheme": scheme,
        "host": host,
        "path": parsed.path or "/",
        "risk_level": risk_level,
        "warnings": warnings,
        "is_safe": risk_level == "LOW"
    }
