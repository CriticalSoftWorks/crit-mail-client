"""
The Intelligence Agency (theintelligenceagency.net) — Full-Stack Web Portal, Mobile PWA & Provisioning API Server
Provides:
- Public Enlistment & Callsign Availability API (/api/callsign/check)
- Automated @theintelligenceagency.net Account & CRIT-L5 License Provisioning (/api/enlist)
- CritMail Desktop Client License Verification & Auto-Config API (/api/license/verify)
- Agent HQ Web & Mobile PWA Authentication (/api/auth/login, /api/agent/dashboard)
- Webmail / PWA Outbound & Internal Dispatch Engine via Amazon SES (/api/mail/send)
- Interactive Cryptanalysis & OSINT Mission Verification Engine (/api/missions/solve)
"""
import os
import re
import json
import time
import uuid
import hmac
import hashlib
import secrets
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "agency_portal.db"

DOMAIN = "theintelligenceagency.net"
SES_SMTP_HOST = os.environ.get("SES_SMTP_HOST", "email-smtp.us-east-1.amazonaws.com")
SES_SMTP_PORT = int(os.environ.get("SES_SMTP_PORT", "465"))
SES_SMTP_USER = os.environ.get("SES_SMTP_USER", "")
SES_SMTP_PASS = os.environ.get("SES_SMTP_PASS", "")
STRIPE_CHECKOUT_URL = os.environ.get("STRIPE_CHECKOUT_URL", "")

RESERVED_CALLSIGNS = {
    "admin", "administrator", "root", "postmaster", "webmaster",
    "support", "security", "hq", "director", "abuse", "noreply",
    "no-reply", "bounce", "mail", "imap", "smtp", "pop", "pop3"
}

MISSIONS = [
    {
        "id": "mission-venona-01",
        "code": "OP-VENONA-01",
        "title": "Operation VENONA-9: Intercepted Caesar Shift",
        "category": "CRYPTANALYSIS",
        "difficulty": "RECRUIT // LEVEL 1",
        "xp": 250,
        "briefing": (
            "Station Reykjavik intercepted a shortwave burst from an unlicensed relay beacon. "
            "The payload uses a classic Caesar shift (+7). Decrypt the ciphertext below and submit "
            "the decoded 2-word rendezvous codeword in ALL CAPS."
        ),
        "artifact": "CIPHERTEXT: NVSKLU LHHNSL  (Hint: Shift each letter backward by 7, or test standard shifts: P -> I, Y -> R, etc. Wait: Z -> S, I -> B... Try shifting 'ZPSCLY MVE' back by 7!)",
        "cipher_display": "Z P S C L Y   M V E",
        "hint": "Shift each letter in 'ZPSCLY MVE' backward by 7 positions in the alphabet (Z->S, P->I, S->L, C->V, L->E, Y->R ...).",
        "solution": "SILVER FOX"
    },
    {
        "id": "mission-header-02",
        "code": "OP-SPOOF-02",
        "title": "Operation PHANTOM HEADER: Email Forensics",
        "category": "COUNTER-PHISHING // OPSEC",
        "difficulty": "OPERATIVE // LEVEL 2",
        "xp": 350,
        "briefing": (
            "An email claiming to be from 'Directorate Security <security@theintelligenceagency.net>' "
            "was flagged by CritMail Link Guard. Inspect the raw SMTP headers below and identify the "
            "true originating IPv4 address of the hostile sender."
        ),
        "cipher_display": (
            "Return-Path: <bounce@rogue-relay.example>\n"
            "Received: from mx.theintelligenceagency.net (10.0.4.12)\n"
            "Received: from unknown (HELO mail.theintelligenceagency.net) ([198.51.100.77])\n"
            "Authentication-Results: spf=fail (sender IP is 198.51.100.77) smtp.mailfrom=theintelligenceagency.net;\n"
            "From: Directorate Security <security@theintelligenceagency.net>\n"
            "Subject: URGENT: Reset Vault Credentials"
        ),
        "hint": "Look at the 'Received: from unknown' header and the 'spf=fail (sender IP is ...)' verdict.",
        "solution": "198.51.100.77"
    },
    {
        "id": "mission-numbers-03",
        "code": "OP-UVB76-03",
        "title": "Operation BERYL BEACON: Hexadecimal Dead-Drop",
        "category": "SIGINT // DECODING",
        "difficulty": "CRYPTANALYST // LEVEL 3",
        "xp": 500,
        "briefing": (
            "A numbers station on 4625 kHz transmitted an ASCII hexadecimal byte sequence before going silent. "
            "Convert the hex bytes to ASCII text to reveal the secret project codename."
        ),
        "cipher_display": "41 5A 4F 52 49 41 4E",
        "hint": "41 = 'A', 5A = 'Z', 4F = 'O', 52 = 'R', 49 = 'I', 41 = 'A', 4E = 'N'.",
        "solution": "AZORIAN"
    },
    {
        "id": "mission-osint-04",
        "code": "OP-CREST-04",
        "title": "Operation OXCART: Declassified Archival Recon",
        "category": "HISTORICAL INTEL // FOIA",
        "difficulty": "SENIOR AGENT // LEVEL 4",
        "xp": 600,
        "briefing": (
            "Cross-reference the Declassified FOIA Vault in your Agent HQ Dashboard. "
            "What was the official Mach speed cruising capability of the CIA's Titanium A-12 OXCART reconnaissance aircraft?"
        ),
        "cipher_display": "QUERY: [REDACTED] CRUISING SPEED OF PROJECT OXCART (FORMAT: MACH X.X)",
        "hint": "Open the 'Declassified FOIA Vault' tab and inspect Dossier #002 (Project OXCART / Area 51). Format as MACH 3.2.",
        "solution": "MACH 3.2"
    }
]

FOIA_DOSSIERS = [
    {
        "id": "foia-001",
        "doc_number": "CIA-RDP85T00875R00110013",
        "title": "PROJECT AZORIAN // Sub-Surface Recovery of Soviet Submarine K-129",
        "date": "DECLASSIFIED // 2010 FOIA RELEASE",
        "classification": "TOP SECRET // BYEMAN",
        "summary": (
            "In 1968, Soviet ballistic missile submarine K-129 sank 1,560 miles northwest of Hawaii at a depth of 16,500 feet. "
            "Under the cover story of deep-sea manganese nodule mining with Howard Hughes' ship 'Hughes Glomar Explorer', "
            "the Intelligence Community engineered a 619-foot mechanical claw recovery vessel ('Clementine') to lift the hull "
            "from the ocean floor."
        ),
        "redacted_excerpt": (
            "MEMORANDUM FOR THE RECORD: Cover narrative involving [Summa Corporation deep-ocean mining] successfully "
            "diverted external naval observation during acoustic transponder deployment at [40°06'N 179°57'E]. "
            "Cryptographic material and two nuclear torpedoes were recovered prior to mechanical grapple fracture."
        )
    },
    {
        "id": "foia-002",
        "doc_number": "CIA-CREST-OXCART-1962",
        "title": "PROJECT OXCART // A-12 High-Altitude Titanium Reconnaissance Program",
        "date": "DECLASSIFIED // 2007 CREST ARCHIVE",
        "classification": "TOP SECRET // OXCART",
        "summary": (
            "Developed at Groom Lake (Area 51) prior to the SR-71 Blackbird, the single-seat A-12 OXCART achieved a sustained "
            "cruising speed of MACH 3.2 at 90,000 feet. Because domestic titanium supplies were scarce, the CIA created "
            "front companies to quietly purchase titanium ore directly from the Soviet Union to build the aircraft."
        ),
        "redacted_excerpt": (
            "FLIGHT TEST TELEMETRY: Article 121 sustained [MACH 3.2] at altitude [90,000 FEET] with radar cross-section "
            "reduced via cesium-doped fuel additives and composite edge treatments."
        )
    },
    {
        "id": "foia-003",
        "doc_number": "NSA-VENONA-1943-1980",
        "title": "PROJECT VENONA // Cryptanalysis of One-Time Pad Key Reuse",
        "date": "DECLASSIFIED // 1995 NSA/CIA RELEASE",
        "classification": "TOP SECRET // UMBRA",
        "summary": (
            "One-time pad ciphers are mathematically unbreakable when keys are truly random and used only once. "
            "However, during World War II, Soviet cryptographic supply clerks printed duplicate pages of one-time pad keybooks. "
            "U.S. Army Signal Intelligence Service cryptanalysts led by Gene Grabeel and Meredith Gardner exploited these "
            "'depths' to decrypt over 3,000 top-secret diplomatic cables."
        ),
        "redacted_excerpt": (
            "CRYPTANALYTIC FINDING: Duplicate additive key groups detected across [Trade Mission New York] traffic, "
            "permitting recovery of underlying codebook values and identification of codename [SILVER FOX / ANTENNA]."
        )
    },
    {
        "id": "foia-004",
        "doc_number": "TIA-SEC-2026-OPSEC",
        "title": "MODERN EMAIL OPSEC // Why SPF, DKIM, DMARC & Zero-JS Matter",
        "date": "ACTIVE BRIEFING // 2026 FIELD MANUAL",
        "classification": "OFFICIAL // FIELD AGENT BRIEF",
        "summary": (
            "Modern email clients often embed full Chromium browser engines that execute remote CSS, tracking beacons, "
            "and punycode homograph links. CritMail strips all active scripts, blocks 1x1 tracking pixels by default, "
            "and uses AES-256-GCM with 200,000 PBKDF2-HMAC-SHA256 iterations for end-to-end payload encryption."
        ),
        "redacted_excerpt": (
            "DIRECTIVE 09: All Level-5 Operatives must verify domain authentication via [SPF + 2048-bit RSA DKIM + DMARC] "
            "and engage [Stealth Redaction Mode (Ctrl+Shift+X)] when operating in public visual range."
        )
    }
]

ACADEMY_COURSES = [
    {
        "id": "acad-101",
        "code": "ACAD-101",
        "division": "DIVISION 01 // NETWORK & COMMS ENGINEERING",
        "title": "Network Protocols, DNS Authentication & Email Security Engineering",
        "credential_title": "Certified SIGINT Communications Specialist (CSCS)",
        "ceu_credits": "3.0 CEU Credits (NIST NICE: Protect & Defend)",
        "xp": 750,
        "summary": (
            "Master the real-world internet protocols that power global email and secure communications: "
            "SMTP, IMAP4, implicit TLS 1.3 (RFC 8314), and the cryptographic DNS authentication triad (SPF, RSA-2048 DKIM, and DMARC)."
        ),
        "modules": [
            {
                "title": "Module 1.1: The Anatomy of Internet Mail (SMTP, IMAP4 & Implicit TLS 1.3)",
                "content": (
                    "Every email crosses multiple network boundaries. Legacy plaintext ports (25, 110, 143) are vulnerable to passive "
                    "wiretapping and STARTTLS downgrade attacks (STRIPTLS). Modern RFC 8314 mandates Implicit TLS from the very first byte: "
                    "Port 465 for SMTP Submission and Port 993 for IMAP4 mailbox synchronization."
                ),
                "code_sample": (
                    "# Verify Implicit TLS 1.3 Handshake on Port 465\n"
                    "openssl s_client -connect email-smtp.us-east-1.amazonaws.com:465 -tls1_3"
                )
            },
            {
                "title": "Module 1.2: Cryptographic DNS Triad (SPF, RSA-2048 DKIM & DMARC)",
                "content": (
                    "1. SPF (Sender Policy Framework): Publishes authorized outbound IPv4/IPv6 ranges in a DNS TXT record (v=spf1).\n"
                    "2. DKIM (DomainKeys Identified Mail): Signs the message headers and body hash with the sender's private RSA-2048 key; "
                    "receiving servers verify the signature via the public key at <selector>._domainkey.<domain>.\n"
                    "3. DMARC (Domain-based Message Authentication, Reporting, and Conformance): Enforces alignment and instructs receivers "
                    "to 'quarantine' or 'reject' unauthenticated messages."
                ),
                "code_sample": (
                    "_dmarc.theintelligenceagency.net. IN TXT \"v=DMARC1; p=quarantine; rua=mailto:postmaster@theintelligenceagency.net\""
                )
            },
            {
                "title": "Module 1.3: SMTP Header Forensics & Detecting Relay Spoofing",
                "content": (
                    "Because the display 'From:' header can be forged by any sender, forensic analysts read 'Received:' headers from TOP to BOTTOM "
                    "(most recent hop at the top) and verify the 'Authentication-Results:' header produced by their own trusted MX server."
                ),
                "code_sample": (
                    "Authentication-Results: mx.google.com;\n"
                    "  dkim=pass header.i=@theintelligenceagency.net header.s=ses;\n"
                    "  spf=pass (google.com: domain of bounce.theintelligenceagency.net designates 54.240.8.1 as permitted sender)"
                )
            }
        ],
        "exam": [
            {
                "q_id": "q1",
                "question": "1. Which DNS authentication standard cryptographically signs outbound email headers and body hashes using an asymmetric public/private keypair?",
                "options": [
                    {"value": "SPF", "label": "SPF (Sender Policy Framework)"},
                    {"value": "DKIM", "label": "DKIM (DomainKeys Identified Mail)"},
                    {"value": "PTR", "label": "Reverse PTR DNS Record"},
                    {"value": "STARTTLS", "label": "Opportunistic STARTTLS"}
                ],
                "answer": "DKIM"
            },
            {
                "q_id": "q2",
                "question": "2. According to RFC 8314, which port is designated for Implicit TLS/SSL outbound SMTP message submission?",
                "options": [
                    {"value": "25", "label": "Port 25 (Plaintext Relay)"},
                    {"value": "110", "label": "Port 110 (POP3)"},
                    {"value": "465", "label": "Port 465 (Implicit TLS Submission)"},
                    {"value": "8080", "label": "Port 8080 (HTTP Proxy)"}
                ],
                "answer": "465"
            },
            {
                "q_id": "q3",
                "question": "3. When inspecting raw email headers for spoofing, which header chain is added hop-by-hop from bottom (earliest) to top (most recent)?",
                "options": [
                    {"value": "RECEIVED", "label": "Received: headers"},
                    {"value": "REPLY-TO", "label": "Reply-To: headers"},
                    {"value": "SUBJECT", "label": "Subject: headers"},
                    {"value": "X-MAILER", "label": "X-Mailer: headers"}
                ],
                "answer": "RECEIVED"
            }
        ]
    },
    {
        "id": "acad-201",
        "code": "ACAD-201",
        "division": "DIVISION 02 // APPLIED CRYPTOGRAPHY & PYTHON",
        "title": "Applied Cryptography, Key Derivation & Python Security Automation",
        "credential_title": "Certified Cryptographic Python Analyst (CCPA)",
        "ceu_credits": "4.0 CEU Credits (NIST NICE: Design & Development)",
        "xp": 1000,
        "summary": (
            "Learn how modern authenticated encryption (AES-256-GCM), password key stretching (PBKDF2-HMAC-SHA256), "
            "constant-time HMAC verification, and Python cryptographic scripting protect classified payloads."
        ),
        "modules": [
            {
                "title": "Module 2.1: Authenticated Encryption with Associated Data (AES-256-GCM)",
                "content": (
                    "Unauthenticated block modes like AES-ECB or raw AES-CBC are vulnerable to pattern leakage and padding oracle attacks. "
                    "AES-256-GCM (Galois/Counter Mode) combines a 256-bit key, a unique 96-bit (12-byte) Nonce/IV, and a 128-bit Authentication Tag "
                    "that guarantees both confidentiality and tamper-proof integrity."
                ),
                "code_sample": (
                    "from cryptography.hazmat.primitives.ciphers.aead import AESGCM\n"
                    "import os\n"
                    "nonce = os.urandom(12)  # 96-bit unique nonce\n"
                    "ciphertext = AESGCM(key_32_bytes).encrypt(nonce, b'TOP SECRET PAYLOAD', None)"
                )
            },
            {
                "title": "Module 2.2: Password Key Stretching (PBKDF2-HMAC-SHA256 & Random Salts)",
                "content": (
                    "Human passphrases do not have 256 bits of uniform entropy. To derive an AES-256 key or store a password hash safely, "
                    "we combine a unique 16-byte cryptographic salt (which defeats precomputed Rainbow Tables) with 150,000+ iterations "
                    "of PBKDF2-HMAC-SHA256 to slow down GPU brute-force attacks."
                ),
                "code_sample": (
                    "import hashlib, secrets\n"
                    "salt = secrets.token_bytes(16)\n"
                    "derived_key = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 200_000)"
                )
            },
            {
                "title": "Module 2.3: Timing Side-Channels & Python's 'secrets' and 'hmac' Modules",
                "content": (
                    "Never use Python's standard 'random' module (Mersenne Twister) for security tokens—its state can be predicted after observing "
                    "624 outputs. Always use 'secrets' (OS CSPRNG) and compare hashes with 'hmac.compare_digest()' to prevent timing attacks."
                ),
                "code_sample": (
                    "import hmac, secrets\n"
                    "token = secrets.token_urlsafe(32)\n"
                    "is_valid = hmac.compare_digest(user_mac, expected_mac)"
                )
            }
        ],
        "exam": [
            {
                "q_id": "q1",
                "question": "1. What critical security property does AES-256-GCM provide in addition to confidentiality via its 128-bit GCM Tag?",
                "options": [
                    {"value": "COMPRESSION", "label": "Lossless payload compression"},
                    {"value": "INTEGRITY", "label": "Authenticated integrity / tamper detection"},
                    {"value": "DNS_ROUTING", "label": "Automatic MX DNS routing"},
                    {"value": "KEY_ESCROW", "label": "Third-party key escrow"}
                ],
                "answer": "INTEGRITY"
            },
            {
                "q_id": "q2",
                "question": "2. Which Python standard library module is backed by the OS CSPRNG and must be used instead of 'random' for security tokens?",
                "options": [
                    {"value": "MATH", "label": "math"},
                    {"value": "SECRETS", "label": "secrets"},
                    {"value": "ITERTOOLS", "label": "itertools"},
                    {"value": "PICKLE", "label": "pickle"}
                ],
                "answer": "SECRETS"
            },
            {
                "q_id": "q3",
                "question": "3. What is the primary role of a unique 16-byte random salt in PBKDF2-HMAC-SHA256?",
                "options": [
                    {"value": "RAINBOW", "label": "Defeats precomputed Rainbow Table lookups and identical hash collisions"},
                    {"value": "SHORTEN", "label": "Shortens the output hash to 8 bits"},
                    {"value": "PLAIN", "label": "Allows the server to recover the plaintext password"},
                    {"value": "COMPRESS", "label": "Compresses large attachments"}
                ],
                "answer": "RAINBOW"
            }
        ]
    },
    {
        "id": "acad-301",
        "code": "ACAD-301",
        "division": "DIVISION 03 // SOC THREAT HUNTING & COUNTER-INTEL",
        "title": "SOC Threat Hunting, Counter-Phishing & OSINT Reconnaissance",
        "credential_title": "Cyber Counter-Intelligence Operator (CCIO)",
        "ceu_credits": "3.5 CEU Credits (NIST NICE: Analyze & Investigate)",
        "xp": 900,
        "summary": (
            "Neutralize tracking beacons, dissect IDN Punycode homograph attacks, analyze malicious payloads without executing scripts, "
            "and execute structured NIST SP 800-61 incident response workflows."
        ),
        "modules": [
            {
                "title": "Module 3.1: Zero-Click Tracking Pixels & Telemetry Neutralization",
                "content": (
                    "Marketing trackers and spear-phishing campaigns embed invisible 1x1 remote images (<img src='https://tracker.example/open?id=992'>). "
                    "When a standard mail client auto-loads remote images, it leaks your public IP address, geolocation, OS/User-Agent, and exact read timestamp. "
                    "CritMail intercepts and strips remote image loads by default."
                ),
                "code_sample": (
                    "# Blocked by CritMail Tracker Shield:\n"
                    "<img src=\"https://telemetry.hostile.example/pixel.gif?uid=target\" width=\"1\" height=\"1\" />"
                )
            },
            {
                "title": "Module 3.2: IDN Homograph Attacks (Punycode 'xn--') & Link Guard",
                "content": (
                    "Attackers register Internationalized Domain Names (IDNs) using Cyrillic or Greek characters that look identical to Latin letters "
                    "(e.g., Cyrillic 'а' U+0430 instead of Latin 'a' U+0061). Under the hood, DNS encodes these domains using the ASCII Punycode prefix 'xn--'."
                ),
                "code_sample": (
                    "Visual Display : https://аpple.com/login (Cyrillic 'а')\n"
                    "Actual DNS Name: https://xn--pple-43d.com/login"
                )
            },
            {
                "title": "Module 3.3: NIST SP 800-61 Incident Response Lifecycle",
                "content": (
                    "Professional Security Operations Centers (SOCs) follow four structured phases under NIST SP 800-61:\n"
                    "1. Preparation -> 2. Detection & Analysis -> 3. Containment, Eradication & Recovery -> 4. Post-Incident Activity."
                ),
                "code_sample": (
                    "Phase 1: Preparation\n"
                    "Phase 2: Detection & Analysis\n"
                    "Phase 3: Containment, Eradication & Recovery\n"
                    "Phase 4: Post-Incident Activity (Lessons Learned)"
                )
            }
        ],
        "exam": [
            {
                "q_id": "q1",
                "question": "1. What ASCII prefix identifies an Internationalized Domain Name (Punycode) often abused in homograph phishing attacks?",
                "options": [
                    {"value": "XN--", "label": "xn--"},
                    {"value": "TLS--", "label": "tls--"},
                    {"value": "UTF8--", "label": "utf8--"},
                    {"value": "DNS--", "label": "dns--"}
                ],
                "answer": "XN--"
            },
            {
                "q_id": "q2",
                "question": "2. How does an embedded 1x1 tracking pixel reveal a recipient's IP address and read time when an HTML email is opened?",
                "options": [
                    {"value": "HTTP_REQ", "label": "The client makes an outbound HTTP/HTTPS GET request to fetch the remote image URL"},
                    {"value": "BLUETOOTH", "label": "It scans local Bluetooth devices"},
                    {"value": "BIOS", "label": "It modifies the system BIOS"},
                    {"value": "ICMP", "label": "It sends an ICMP ping flood"}
                ],
                "answer": "HTTP_REQ"
            },
            {
                "q_id": "q3",
                "question": "3. In the NIST SP 800-61 Incident Response lifecycle, which phase immediately follows 'Detection & Analysis'?",
                "options": [
                    {"value": "CONTAINMENT", "label": "Containment, Eradication & Recovery"},
                    {"value": "MARKETING", "label": "Public Marketing Disclosure"},
                    {"value": "DELETION", "label": "Hard Drive Formatting"},
                    {"value": "PROCUREMENT", "label": "Vendor Procurement"}
                ],
                "answer": "CONTAINMENT"
            }
        ]
    },
    {
        "id": "acad-401",
        "code": "ACAD-401",
        "division": "DIVISION 04 // SECURE INFRASTRUCTURE & SYSTEMS",
        "title": "Linux Hardening, SQL Injection Defense & Zero-Trust API Engineering",
        "credential_title": "Directorate Security & Infrastructure Engineer (DSIE)",
        "ceu_credits": "4.5 CEU Credits (NIST NICE: Operate & Maintain)",
        "xp": 1200,
        "summary": (
            "Build and harden production Linux servers, eliminate SQL Injection via parameterized queries, "
            "lock down SSH keys, and enforce HTTP Strict-Transport-Security (HSTS)."
        ),
        "modules": [
            {
                "title": "Module 4.1: Eliminating SQL Injection (SQLi) with Parameterized Queries",
                "content": (
                    "Formatting user input directly into SQL strings via f-strings or concatenation allows attackers to inject \"' OR 1=1 --\" "
                    "and dump or destroy tables. Parameterized queries (?) separate the SQL command structure from the literal data parameters."
                ),
                "code_sample": (
                    "# VULNERABLE (Never do this):\n"
                    "# cursor.execute(f\"SELECT * FROM agents WHERE callsign = '{user_input}'\")\n\n"
                    "# SECURE (Parameterized Query):\n"
                    "cursor.execute(\"SELECT * FROM agents WHERE callsign = ?\", (user_input,))"
                )
            },
            {
                "title": "Module 4.2: Linux SSH Key Permissions & Least-Privilege Services",
                "content": (
                    "OpenSSH refuses to use private key files (.pem / id_ed25519) if other system users can read them. "
                    "Setting 'chmod 400' (r--------) ensures only the file owner has read access. Production daemons should run under dedicated "
                    "non-root systemd accounts."
                ),
                "code_sample": (
                    "chmod 400 ~/.ssh/id_ed25519\n"
                    "ssh -i ~/.ssh/id_ed25519 operative@184.193.61.45"
                )
            },
            {
                "title": "Module 4.3: Transport Layer Hardening & HSTS",
                "content": (
                    "Even when a server supports HTTPS on Port 443, a user typing a domain name without 'https://' initially makes a plaintext HTTP request. "
                    "The 'Strict-Transport-Security' (HSTS) header instructs browsers to automatically upgrade all future connections to HTTPS."
                ),
                "code_sample": (
                    "Strict-Transport-Security: max-age=63072000; includeSubDomains; preload"
                )
            }
        ],
        "exam": [
            {
                "q_id": "q1",
                "question": "1. What is the primary defense against SQL Injection (SQLi) when executing database queries in Python?",
                "options": [
                    {"value": "PARAMETERIZED", "label": "Parameterized queries (bound placeholders '?')"},
                    {"value": "BASE64", "label": "Base64 encoding the SQL string"},
                    {"value": "UPPERCASE", "label": "Converting all inputs to uppercase"},
                    {"value": "REGEX", "label": "Removing spaces with regex"}
                ],
                "answer": "PARAMETERIZED"
            },
            {
                "q_id": "q2",
                "question": "2. Which Linux octal permission mode restricts an SSH private key file to read-only for its owner and no permissions for group/others?",
                "options": [
                    {"value": "777", "label": "chmod 777 (rwxrwxrwx)"},
                    {"value": "666", "label": "chmod 666 (rw-rw-rw-)"},
                    {"value": "400", "label": "chmod 400 (r--------)"},
                    {"value": "755", "label": "chmod 755 (rwxr-xr-x)"}
                ],
                "answer": "400"
            },
            {
                "q_id": "q3",
                "question": "3. Which HTTP security response header instructs browsers to strictly connect to a domain only over HTTPS?",
                "options": [
                    {"value": "HSTS", "label": "Strict-Transport-Security (HSTS)"},
                    {"value": "ACCEPT", "label": "Accept-Encoding"},
                    {"value": "USER_AGENT", "label": "User-Agent"},
                    {"value": "CACHE", "label": "Cache-Control"}
                ],
                "answer": "HSTS"
            }
        ]
    }
]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def hash_password(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 150000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), stored_hash)


def rank_for_xp(xp: int) -> str:
    if xp >= 2500:
        return "DIRECTORATE FELLOW // LEVEL 5"
    if xp >= 1200:
        return "STATION CHIEF // LEVEL 5"
    if xp >= 700:
        return "SENIOR CRYPTANALYST // LEVEL 5"
    if xp >= 250:
        return "FIELD OPERATIVE // LEVEL 5"
    return "SPECIAL AGENT // LEVEL 5"


def generate_license_key() -> str:
    parts = [secrets.token_hex(2).upper() for _ in range(3)]
    return f"CRIT-L5-{parts[0]}-{parts[1]}-{parts[2]}"


def generate_certificate_id(course_code: str, callsign: str) -> tuple[str, str]:
    token = secrets.token_hex(3).upper()
    cert_id = f"TIA-CERT-2026-{course_code.replace('ACAD-', '')}-{token}"
    sig_input = f"{cert_id}:{callsign}:{course_code}:{DOMAIN}".encode("utf-8")
    signature = hashlib.sha256(sig_input).hexdigest()[:32].upper()
    return cert_id, signature


def init_portal_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            callsign TEXT UNIQUE NOT NULL,
            email_address TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            license_key TEXT UNIQUE NOT NULL,
            clearance_level TEXT DEFAULT 'LEVEL-5 OPERATIVE',
            rank TEXT DEFAULT 'SPECIAL AGENT // LEVEL 5',
            xp INTEGER DEFAULT 100,
            plan_tier TEXT DEFAULT 'OPERATIVE_PRO',
            recovery_email TEXT DEFAULT '',
            session_token TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transmissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_callsign TEXT NOT NULL,
            folder TEXT DEFAULT 'inbox',
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            classification TEXT DEFAULT 'INTERNAL AGENCY // EYES ONLY',
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS completed_missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_callsign TEXT NOT NULL,
            mission_id TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            UNIQUE(agent_callsign, mission_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS issued_certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_id TEXT UNIQUE NOT NULL,
            agent_callsign TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            agent_email TEXT NOT NULL,
            course_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            course_title TEXT NOT NULL,
            credential_title TEXT NOT NULL,
            ceu_credits TEXT NOT NULL,
            score_pct INTEGER DEFAULT 100,
            sha256_signature TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            UNIQUE(agent_callsign, course_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS instructor_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            credentials TEXT NOT NULL,
            proposed_topic TEXT NOT NULL,
            background TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Seed Director / Primary Account (james.f@theintelligenceagency.net)
    existing = c.execute("SELECT id FROM agents WHERE callsign = ?", ("james.f",)).fetchone()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not existing:
        c.execute("""
            INSERT INTO agents (
                callsign, email_address, display_name, password_hash,
                license_key, clearance_level, rank, xp, plan_tier, recovery_email, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "james.f",
            f"james.f@{DOMAIN}",
            "Director James F.",
            hash_password("Neriak2356x!"),
            "CRIT-L5-DIRECTOR-0001",
            "DIRECTORATE // LEVEL-5",
            "STATION CHIEF // LEVEL 5",
            1500,
            "FOUNDER_LIFETIME",
            "critmaths@gmail.com",
            now_str
        ))
        _seed_welcome_transmissions(c, "james.f", f"james.f@{DOMAIN}", "CRIT-L5-DIRECTOR-0001")

    # Seed a sample verifiable Founder Certificate for james.f so verification works out of the box
    existing_cert = c.execute("SELECT id FROM issued_certificates WHERE cert_id = ?", ("TIA-CERT-2026-DIRECTOR-0001",)).fetchone()
    if not existing_cert:
        c.execute("""
            INSERT OR IGNORE INTO issued_certificates (
                cert_id, agent_callsign, agent_name, agent_email,
                course_id, course_code, course_title, credential_title,
                ceu_credits, score_pct, sha256_signature, issued_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "TIA-CERT-2026-DIRECTOR-0001",
            "james.f",
            "Director James F.",
            f"james.f@{DOMAIN}",
            "acad-101",
            "ACAD-101",
            "Network Protocols, DNS Authentication & Email Security Engineering",
            "Certified SIGINT Communications Specialist (CSCS)",
            "3.0 CEU Credits (NIST NICE: Protect & Defend)",
            100,
            hashlib.sha256(b"TIA-CERT-2026-DIRECTOR-0001:james.f:ACAD-101").hexdigest()[:32].upper(),
            now_str
        ))

    conn.commit()
    conn.close()


def _seed_welcome_transmissions(cursor, callsign: str, email_addr: str, license_key: str):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cursor.execute("""
        INSERT INTO transmissions (
            agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
        ) VALUES (?, 'inbox', ?, ?, ?, ?, ?, 0, ?)
    """, (
        callsign,
        f"Agency Directorate <hq@{DOMAIN}>",
        email_addr,
        f"[EYES ONLY] Welcome to The Intelligence Agency — Callsign {email_addr}",
        (
            f"OPERATIVE DOSSIER ACTIVATED\n"
            f"==================================================\n"
            f"Assigned Agency Callsign : {email_addr}\n"
            f"CritMail Pro License Key : {license_key}\n"
            f"Clearance Status         : LEVEL-5 OPERATIVE (ACTIVE)\n"
            f"==================================================\n\n"
            f"Welcome to The Intelligence Agency. Your official @{DOMAIN} communications channel "
            f"is now active across both this Agent HQ Web/Mobile Terminal and the CritMail Desktop Client.\n\n"
            f"YOUR FIRST ASSIGNMENT (OP-VENONA-01):\n"
            f"Open the [Cryptanalysis & Recon Ops] tab in your dashboard and decrypt the intercepted "
            f"shortwave transmission 'ZPSCLY MVE' (Caesar shift -7) to earn your first +250 XP commendation.\n\n"
            f"— Directorate of Signals Intelligence (hq@{DOMAIN})"
        ),
        "TOP SECRET // EYES ONLY",
        now_str
    ))
    cursor.execute("""
        INSERT INTO transmissions (
            agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
        ) VALUES (?, 'inbox', ?, ?, ?, ?, ?, 0, ?)
    """, (
        callsign,
        f"Cryptanalysis Division <crypto@{DOMAIN}>",
        email_addr,
        "[MISSION DISPATCH] Operation BERYL BEACON — 4625 kHz Intercept",
        (
            "INTERCEPT LOG // 4625 kHz\n"
            "--------------------------------------------------\n"
            "Captured Hexadecimal Stream: 41 5A 4F 52 49 41 4E\n\n"
            "Decode the ASCII hex bytes above and submit the project codename inside the "
            "[Cryptanalysis & Recon Ops] terminal to unlock +500 XP towards Senior Cryptanalyst rank."
        ),
        "CLASSIFIED // SIGINT OPS",
        now_str
    ))


def normalize_callsign(raw: str) -> str:
    clean = raw.strip().lower()
    if "@" in clean:
        clean = clean.split("@", 1)[0]
    clean = re.sub(r"[^a-z0-9._-]", "", clean).strip("._-")
    return clean


def send_ses_email_if_configured(from_addr: str, to_addr: str, subject: str, body: str) -> tuple[bool, str]:
    """Sends a real email through Amazon SES SMTP if credentials are present in environment or local config."""
    smtp_user = SES_SMTP_USER
    smtp_pass = SES_SMTP_PASS

    # Fallback: check local ~/.critmail/critmail.db if running on the dev machine
    if not smtp_user or not smtp_pass:
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR.parent))
            from critmail.models.database import get_accounts
            for acc in get_accounts():
                if "amazonaws.com" in (acc.get("smtp_host") or ""):
                    smtp_user = acc["smtp_username"]
                    smtp_pass = acc["smtp_password"]
                    break
        except Exception:
            pass

    if not smtp_user or not smtp_pass:
        return False, "Local simulation mode (SES SMTP env vars not set on this host)"

    try:
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL(SES_SMTP_HOST, SES_SMTP_PORT, timeout=12) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True, "Dispatched via Amazon SES (2048-bit DKIM)"
    except Exception as e:
        return False, str(e)


class AgencyPortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, status_code: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _get_authenticated_agent(self):
        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        if not token:
            return None
        conn = get_db()
        row = conn.execute("SELECT * FROM agents WHERE session_token = ?", (token,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/health":
            return self._send_json(200, {
                "status": "OPERATIONAL",
                "domain": DOMAIN,
                "service": "The Intelligence Agency HQ & Callsign Provisioning API",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        if path == "/api/callsign/check":
            raw = (qs.get("callsign", [""])[0] or "").strip()
            callsign = normalize_callsign(raw)
            if len(callsign) < 3:
                return self._send_json(200, {
                    "available": False,
                    "callsign": callsign,
                    "email": f"{callsign}@{DOMAIN}" if callsign else "",
                    "reason": "Callsign must be at least 3 characters (letters, digits, dots, hyphens)."
                })
            if callsign in RESERVED_CALLSIGNS:
                return self._send_json(200, {
                    "available": False,
                    "callsign": callsign,
                    "email": f"{callsign}@{DOMAIN}",
                    "reason": "Reserved Directorate system callsign."
                })
            conn = get_db()
            row = conn.execute("SELECT id FROM agents WHERE callsign = ?", (callsign,)).fetchone()
            conn.close()
            if row:
                return self._send_json(200, {
                    "available": False,
                    "callsign": callsign,
                    "email": f"{callsign}@{DOMAIN}",
                    "reason": "Callsign is already assigned to an active operative."
                })
            return self._send_json(200, {
                "available": True,
                "callsign": callsign,
                "email": f"{callsign}@{DOMAIN}",
                "reason": f"AVAILABLE // {callsign}@{DOMAIN} is ready for immediate assignment."
            })

        if path == "/api/academy/courses":
            courses_out = []
            for c_item in ACADEMY_COURSES:
                c_copy = dict(c_item)
                c_copy["exam"] = [
                    {"q_id": q["q_id"], "question": q["question"], "options": q["options"]}
                    for q in c_item["exam"]
                ]
                courses_out.append(c_copy)
            return self._send_json(200, {"courses": courses_out})

        if path == "/api/certificates/verify":
            cert_id = (qs.get("cert_id", [""])[0] or "").strip().upper()
            if not cert_id:
                return self._send_json(400, {"valid": False, "error": "Please provide a Certificate ID (e.g. TIA-CERT-2026-DIRECTOR-0001)."})
            conn = get_db()
            row = conn.execute("SELECT * FROM issued_certificates WHERE UPPER(cert_id) = ?", (cert_id,)).fetchone()
            conn.close()
            if not row:
                return self._send_json(404, {
                    "valid": False,
                    "cert_id": cert_id,
                    "error": f"Certificate '{cert_id}' was not found in the Directorate Academy Registry."
                })
            cert = dict(row)
            return self._send_json(200, {
                "valid": True,
                "certificate": cert
            })

        if path == "/api/agent/dashboard":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized or expired session token."})
            conn = get_db()
            inbox = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM transmissions WHERE agent_callsign = ? AND folder = 'inbox' ORDER BY id DESC",
                    (agent["callsign"],)
                ).fetchall()
            ]
            sent = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM transmissions WHERE agent_callsign = ? AND folder = 'sent' ORDER BY id DESC",
                    (agent["callsign"],)
                ).fetchall()
            ]
            solved_rows = conn.execute(
                "SELECT mission_id FROM completed_missions WHERE agent_callsign = ?",
                (agent["callsign"],)
            ).fetchall()
            solved_ids = {r["mission_id"] for r in solved_rows}

            cert_rows = conn.execute(
                "SELECT * FROM issued_certificates WHERE agent_callsign = ? ORDER BY id DESC",
                (agent["callsign"],)
            ).fetchall()
            certificates = [dict(r) for r in cert_rows]
            cert_by_course = {c["course_id"]: c for c in certificates}
            conn.close()

            missions_out = []
            for m in MISSIONS:
                m_copy = dict(m)
                m_copy.pop("solution", None)
                m_copy["completed"] = m["id"] in solved_ids
                missions_out.append(m_copy)

            courses_out = []
            for c_item in ACADEMY_COURSES:
                c_copy = dict(c_item)
                c_copy["exam"] = [
                    {"q_id": q["q_id"], "question": q["question"], "options": q["options"]}
                    for q in c_item["exam"]
                ]
                earned = cert_by_course.get(c_item["id"])
                c_copy["completed"] = earned is not None
                c_copy["certificate"] = earned
                courses_out.append(c_copy)

            return self._send_json(200, {
                "agent": {
                    "callsign": agent["callsign"],
                    "email_address": agent["email_address"],
                    "display_name": agent["display_name"],
                    "license_key": agent["license_key"],
                    "clearance_level": agent["clearance_level"],
                    "rank": agent["rank"],
                    "xp": agent["xp"],
                    "plan_tier": agent["plan_tier"],
                    "created_at": agent["created_at"],
                    "imap_host": "mailserver.businessidentity.llc",
                    "imap_port": 993,
                    "smtp_host": SES_SMTP_HOST,
                    "smtp_port": 465
                },
                "inbox": inbox,
                "sent": sent,
                "missions": missions_out,
                "foia_dossiers": FOIA_DOSSIERS,
                "academy_courses": courses_out,
                "certificates": certificates
            })

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        if path == "/api/enlist":
            callsign = normalize_callsign(body.get("callsign", ""))
            display_name = (body.get("display_name") or f"Agent {callsign.capitalize()}").strip()
            password = body.get("password") or body.get("passphrase") or ""
            plan_tier = body.get("plan_tier") or body.get("division") or "OPERATIVE_PRO"
            recovery_email = (body.get("recovery_email") or "").strip()

            if len(callsign) < 3 or callsign in RESERVED_CALLSIGNS:
                return self._send_json(400, {"error": "Invalid or reserved callsign. Choose at least 3 characters."})
            if len(password) < 6:
                return self._send_json(400, {"error": "Passphrase must be at least 6 characters."})

            conn = get_db()
            existing = conn.execute("SELECT id FROM agents WHERE callsign = ?", (callsign,)).fetchone()
            if existing:
                conn.close()
                return self._send_json(409, {"error": f"{callsign}@{DOMAIN} is already claimed by another agent."})

            email_addr = f"{callsign}@{DOMAIN}"
            license_key = generate_license_key()
            session_token = secrets.token_urlsafe(32)
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            c = conn.cursor()
            c.execute("""
                INSERT INTO agents (
                    callsign, email_address, display_name, password_hash,
                    license_key, clearance_level, rank, xp, plan_tier,
                    recovery_email, session_token, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                callsign, email_addr, display_name, hash_password(password),
                license_key, "LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5",
                150, plan_tier, recovery_email, session_token, now_str
            ))
            _seed_welcome_transmissions(c, callsign, email_addr, license_key)
            conn.commit()
            conn.close()

            # Optional: If recovery_email provided, send welcome dossier via Amazon SES
            if recovery_email and "@" in recovery_email:
                send_ses_email_if_configured(
                    from_addr=f"The Intelligence Agency <hq@{DOMAIN}>",
                    to_addr=recovery_email,
                    subject=f"[TOP SECRET] Operative Enlistment Confirmed: {email_addr}",
                    body=(
                        f"Welcome to The Intelligence Agency, {display_name}!\n\n"
                        f"Assigned Agency Email : {email_addr}\n"
                        f"CritMail License Key  : {license_key}\n"
                        f"Clearance Status      : LEVEL-5 OPERATIVE\n\n"
                        f"Log into the Agent HQ Dashboard at https://{DOMAIN} or activate your key inside CritMail."
                    )
                )

            return self._send_json(200, {
                "ok": True,
                "token": session_token,
                "stripe_checkout_url": STRIPE_CHECKOUT_URL,
                "agent": {
                    "callsign": callsign,
                    "email": email_addr,
                    "email_address": email_addr,
                    "display_name": display_name,
                    "license_key": license_key,
                    "clearance_level": "LEVEL-5 OPERATIVE",
                    "clearance_title": "SPECIAL AGENT // LEVEL 5",
                    "rank": "SPECIAL AGENT // LEVEL 5",
                    "xp": 150,
                    "plan_tier": plan_tier
                }
            })

        if path == "/api/auth/login":
            raw_user = (body.get("callsign") or body.get("email") or "").strip()
            callsign = normalize_callsign(raw_user)
            password = body.get("password") or body.get("passphrase") or ""

            conn = get_db()
            row = conn.execute(
                "SELECT * FROM agents WHERE callsign = ? OR license_key = ?",
                (callsign, raw_user.upper())
            ).fetchone()
            if not row or not verify_password(password, row["password_hash"]):
                conn.close()
                return self._send_json(401, {"error": "Invalid Agency Callsign or Passphrase."})

            session_token = secrets.token_urlsafe(32)
            conn.execute("UPDATE agents SET session_token = ? WHERE id = ?", (session_token, row["id"]))
            conn.commit()
            agent = dict(row)
            conn.close()

            return self._send_json(200, {
                "ok": True,
                "token": session_token,
                "agent": {
                    "callsign": agent["callsign"],
                    "email": agent["email_address"],
                    "email_address": agent["email_address"],
                    "display_name": agent["display_name"],
                    "license_key": agent["license_key"],
                    "clearance_level": agent["clearance_level"],
                    "clearance_title": agent["rank"],
                    "rank": agent["rank"],
                    "xp": agent["xp"]
                }
            })

        if path == "/api/license/verify":
            license_key = (body.get("license_key") or "").strip().upper()
            callsign = normalize_callsign(body.get("callsign") or "")
            conn = get_db()
            if license_key:
                row = conn.execute("SELECT * FROM agents WHERE license_key = ?", (license_key,)).fetchone()
            else:
                row = conn.execute("SELECT * FROM agents WHERE callsign = ?", (callsign,)).fetchone()
            conn.close()

            if not row:
                return self._send_json(404, {
                    "valid": False,
                    "error": "License key not found in Agency Directorate registry."
                })
            agent = dict(row)
            return self._send_json(200, {
                "valid": True,
                "callsign": agent["callsign"],
                "email": agent["email_address"],
                "email_address": agent["email_address"],
                "display_name": agent["display_name"],
                "license_key": agent["license_key"],
                "clearance_level": agent["clearance_level"],
                "clearance_title": agent["rank"],
                "rank": agent["rank"],
                "xp": agent["xp"],
                "imap_host": "mailserver.businessidentity.llc",
                "imap_port": 993,
                "smtp_host": SES_SMTP_HOST,
                "smtp_port": 465
            })

        if path == "/api/mail/send":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})
            recipient = (body.get("recipient") or "").strip()
            subject = (body.get("subject") or "(No Subject)").strip()
            msg_body = (body.get("body") or "").strip()
            if not recipient or "@" not in recipient:
                return self._send_json(400, {"error": "Valid recipient email address required."})

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            sender_formatted = f"{agent['display_name']} <{agent['email_address']}>"

            conn = get_db()
            c = conn.cursor()
            # Save in sender's Sent folder
            c.execute("""
                INSERT INTO transmissions (
                    agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                ) VALUES (?, 'sent', ?, ?, ?, ?, 'OUTBOUND DISPATCH // TLS 1.3', 1, ?)
            """, (agent["callsign"], sender_formatted, recipient, subject, msg_body, now_str))

            # If recipient is an internal @theintelligenceagency.net agent, also deliver to their portal inbox immediately!
            if recipient.lower().endswith(f"@{DOMAIN}"):
                target_callsign = normalize_callsign(recipient)
                c.execute("""
                    INSERT INTO transmissions (
                        agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                    ) VALUES (?, 'inbox', ?, ?, ?, ?, 'INTERNAL AGENCY // EYES ONLY', 0, ?)
                """, (target_callsign, sender_formatted, recipient, subject, msg_body, now_str))

            conn.commit()
            conn.close()

            # Also dispatch via Amazon SES so external recipients (and IMAP inbox) receive it
            ses_ok, ses_info = send_ses_email_if_configured(
                from_addr=sender_formatted,
                to_addr=recipient,
                subject=subject,
                body=msg_body
            )
            return self._send_json(200, {
                "ok": True,
                "ses_dispatched": ses_ok,
                "detail": ses_info
            })

        if path == "/api/missions/solve":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})
            mission_id = (body.get("mission_id") or body.get("code") or "").strip()
            answer = " ".join((body.get("answer") or "").strip().upper().split())

            target_mission = next(
                (m for m in MISSIONS if m["id"].lower() == mission_id.lower() or m["code"].lower() == mission_id.lower()),
                None
            )
            if not target_mission:
                return self._send_json(404, {"error": "Mission not found."})
            mission_id = target_mission["id"]

            if answer != target_mission["solution"]:
                return self._send_json(200, {
                    "correct": False,
                    "message": "DECRYPTION MISMATCH // Solution rejected. Check the hint and try again."
                })

            conn = get_db()
            c = conn.cursor()
            already = c.execute(
                "SELECT id FROM completed_missions WHERE agent_callsign = ? AND mission_id = ?",
                (agent["callsign"], mission_id)
            ).fetchone()
            if already:
                conn.close()
                return self._send_json(200, {
                    "correct": True,
                    "already_completed": True,
                    "xp": agent["xp"],
                    "rank": agent["rank"],
                    "message": "Mission already solved and logged in your dossier."
                })

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            c.execute(
                "INSERT INTO completed_missions (agent_callsign, mission_id, completed_at) VALUES (?, ?, ?)",
                (agent["callsign"], mission_id, now_str)
            )
            new_xp = int(agent["xp"]) + int(target_mission["xp"])
            new_rank = rank_for_xp(new_xp)
            c.execute(
                "UPDATE agents SET xp = ?, rank = ? WHERE callsign = ?",
                (new_xp, new_rank, agent["callsign"])
            )
            c.execute("""
                INSERT INTO transmissions (
                    agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                ) VALUES (?, 'inbox', ?, ?, ?, ?, 'COMMENDATION // DIRECTORATE', 0, ?)
            """, (
                agent["callsign"],
                f"Directorate Commendations <hq@{DOMAIN}>",
                agent["email_address"],
                f"[COMMENDATION] {target_mission['code']} Solved (+{target_mission['xp']} XP)",
                (
                    f"Operative {agent['display_name']} ({agent['email_address']}),\n\n"
                    f"Your cryptanalytic solution for {target_mission['title']} has been verified.\n"
                    f"XP Awarded   : +{target_mission['xp']} XP (Total: {new_xp} XP)\n"
                    f"Current Rank : {new_rank}\n\n"
                    f"— Directorate of Signals Intelligence"
                ),
                now_str
            ))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "correct": True,
                "xp": new_xp,
                "rank": new_rank,
                "xp_gained": target_mission["xp"],
                "message": f"VERIFIED! +{target_mission['xp']} XP awarded. Rank: {new_rank}"
            })

        if path == "/api/academy/exam":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})
            course_id = (body.get("course_id") or body.get("code") or "").strip()
            answers = body.get("answers") or {}

            course = next(
                (c for c in ACADEMY_COURSES if c["id"].lower() == course_id.lower() or c["code"].lower() == course_id.lower()),
                None
            )
            if not course:
                return self._send_json(404, {"error": "Academy course not found."})

            total_q = len(course["exam"])
            correct_q = 0
            for q in course["exam"]:
                submitted = str(answers.get(q["q_id"], "")).strip().upper()
                if submitted == q["answer"].upper():
                    correct_q += 1

            score_pct = int(round((correct_q / total_q) * 100)) if total_q else 100
            if correct_q < total_q:
                return self._send_json(200, {
                    "passed": False,
                    "score_pct": score_pct,
                    "correct_count": correct_q,
                    "total_count": total_q,
                    "message": f"EXAM SCORE: {correct_q}/{total_q} ({score_pct}%). 100% required for Directorate Certification. Review the course modules and try again!"
                })

            conn = get_db()
            c = conn.cursor()
            existing_cert = c.execute(
                "SELECT * FROM issued_certificates WHERE agent_callsign = ? AND course_id = ?",
                (agent["callsign"], course["id"])
            ).fetchone()
            if existing_cert:
                cert_dict = dict(existing_cert)
                conn.close()
                return self._send_json(200, {
                    "passed": True,
                    "already_certified": True,
                    "score_pct": 100,
                    "xp": agent["xp"],
                    "rank": agent["rank"],
                    "certificate": cert_dict,
                    "message": f"Already certified! Certificate ID: {cert_dict['cert_id']}"
                })

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            cert_id, sig = generate_certificate_id(course["code"], agent["callsign"])
            c.execute("""
                INSERT INTO issued_certificates (
                    cert_id, agent_callsign, agent_name, agent_email,
                    course_id, course_code, course_title, credential_title,
                    ceu_credits, score_pct, sha256_signature, issued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cert_id,
                agent["callsign"],
                agent["display_name"],
                agent["email_address"],
                course["id"],
                course["code"],
                course["title"],
                course["credential_title"],
                course["ceu_credits"],
                100,
                sig,
                now_str
            ))

            new_xp = int(agent["xp"]) + int(course["xp"])
            new_rank = rank_for_xp(new_xp)
            c.execute(
                "UPDATE agents SET xp = ?, rank = ? WHERE callsign = ?",
                (new_xp, new_rank, agent["callsign"])
            )
            c.execute("""
                INSERT INTO transmissions (
                    agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                ) VALUES (?, 'inbox', ?, ?, ?, ?, 'ACADEMY DIPLOMA // VERIFIED CREDENTIAL', 0, ?)
            """, (
                agent["callsign"],
                f"Directorate Training Academy <academy@{DOMAIN}>",
                agent["email_address"],
                f"[CERTIFICATION ISSUED] {course['credential_title']} — {cert_id}",
                (
                    f"OFFICIAL DIRECTORATE CREDENTIAL ISSUED\n"
                    f"==================================================\n"
                    f"Certificate ID    : {cert_id}\n"
                    f"Operative         : {agent['display_name']} ({agent['email_address']})\n"
                    f"Credential Earned : {course['credential_title']}\n"
                    f"Course Completed  : {course['code']} — {course['title']}\n"
                    f"Continuing Ed     : {course['ceu_credits']}\n"
                    f"SHA-256 Signature : {sig}\n"
                    f"Public Verify URL : https://{DOMAIN}/?verify={cert_id}\n"
                    f"==================================================\n\n"
                    f"Congratulations! You have earned +{course['xp']} XP (New Rank: {new_rank})."
                ),
                now_str
            ))
            conn.commit()
            cert_row = c.execute("SELECT * FROM issued_certificates WHERE cert_id = ?", (cert_id,)).fetchone()
            conn.close()

            return self._send_json(200, {
                "passed": True,
                "score_pct": 100,
                "xp": new_xp,
                "rank": new_rank,
                "xp_gained": course["xp"],
                "certificate": dict(cert_row),
                "message": f"🎓 CERTIFICATION EARNED! Credential '{course['credential_title']}' ({cert_id}) issued (+{course['xp']} XP)!"
            })

        if path == "/api/academy/instructor-apply":
            full_name = (body.get("full_name") or "").strip()
            email = (body.get("email") or "").strip()
            credentials = (body.get("credentials") or "").strip()
            proposed_topic = (body.get("proposed_topic") or "").strip()
            background = (body.get("background") or "").strip()

            if not full_name or not email or "@" not in email or not credentials:
                return self._send_json(400, {"error": "Please provide your name, email address, and professional credentials."})

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO instructor_applications (
                    full_name, email, credentials, proposed_topic, background, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, email, credentials, proposed_topic, background, now_str))

            # Deliver directly into Director james.f's HQ Inbox
            c.execute("""
                INSERT INTO transmissions (
                    agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                ) VALUES ('james.f', 'inbox', ?, ?, ?, ?, 'ADVISORY BOARD // INSTRUCTOR APPLICATION', 0, ?)
            """, (
                f"{full_name} <{email}>",
                f"james.f@{DOMAIN}",
                f"[ACADEMY INSTRUCTOR APPLICATION] {full_name} ({credentials})",
                (
                    f"NEW MISSION-FIRST ACADEMY INSTRUCTOR / ADVISORY APPLICATION\n"
                    f"============================================================\n"
                    f"Applicant Name : {full_name}\n"
                    f"Contact Email  : {email}\n"
                    f"Credentials    : {credentials}\n"
                    f"Proposed Track : {proposed_topic}\n"
                    f"Submitted At   : {now_str}\n"
                    f"------------------------------------------------------------\n"
                    f"Background & Mission Statement:\n{background}\n"
                ),
                now_str
            ))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "ok": True,
                "message": "Application logged with the Directorate Advisory Board! Director James F. will review your credentials."
            })

        return self._send_json(404, {"error": "Unknown API endpoint."})


def run_server(host: str = "0.0.0.0", port: int = 8080):
    init_portal_db()
    server = ThreadingHTTPServer((host, port), AgencyPortalHandler)
    print(f"[THE INTELLIGENCE AGENCY] Portal & API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port_num = int(os.environ.get("PORT", "8080"))
    run_server(port=port_num)
