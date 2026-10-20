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
import base64
import urllib.request
import urllib.parse
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

STRIPE_SECRET_KEY = os.environ.get(
    "STRIPE_SECRET_KEY",
    "sk_test_51UGLSwLDCe49tIs9CIWbMj7Qzigcc6w1DzOjFukxP3mK2a2hwBb45mNHeSkcNIKAEMHDTkr4SfwJdVinsDFT6pFl00CcqVc8wD"
).strip()
STRIPE_PUBLISHABLE_KEY = os.environ.get(
    "STRIPE_PUBLISHABLE_KEY",
    "pk_test_51UGLSwLDCe49tIs9jDMx9fxVaFfG4tuCdpDCZQoJOjv5QIImNdO2ARuU9Mg3RdNpFOtlEzdrWIhcH2RVjM6dZ7b500KPo765Hf"
).strip()

STRIPE_PRICE_IDS = {
    "OPERATIVE_MONTHLY": "price_1USJHvLDCe49tIs9cXw4GDyO",
    "OPERATIVE_ANNUAL": "price_1USJHwLDCe49tIs9h2ne71oO",
    "STATION_CHIEF_LIFETIME": "price_1USJHwLDCe49tIs9pXxIeNXz",
}
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

try:
    from web_portal.academy_curriculum import ACADEMY_COURSES, execute_lab_command
except ImportError:
    from academy_curriculum import ACADEMY_COURSES, execute_lab_command


def _sanitize_course_for_client(course: dict, completed_lesson_ids: set = None, earned_cert: dict = None, agent_tier: str = "OPERATIVE_PRO") -> dict:
    completed_lesson_ids = completed_lesson_ids or set()
    c_copy = dict(course)
    modules_out = []
    free_count = int(course.get("free_preview_count") or 2)
    is_cadet = agent_tier == "CADET_FREE"

    for idx, m in enumerate(course.get("modules", []), start=1):
        lesson_id = m.get("lesson_id") or f"{course['id']}-m{idx}"
        is_locked = is_cadet and (idx > free_count)
        m_copy = {
            "lesson_id": lesson_id,
            "title": m.get("title", ""),
            "duration": m.get("duration", "20 min"),
            "objectives": m.get("objectives", []),
            "content": m.get("content", ""),
            "code_sample": m.get("code_sample", ""),
            "checkpoint_q": m.get("checkpoint_q", ""),
            "checkpoint_hint": m.get("checkpoint_hint", ""),
            "completed": (lesson_id in completed_lesson_ids) or (earned_cert is not None),
            "is_locked": is_locked
        }
        modules_out.append(m_copy)

    c_copy["modules"] = modules_out
    c_copy["free_preview_count"] = free_count
    c_copy["exam_locked"] = is_cadet
    total_lessons = len(modules_out)
    done_lessons = sum(1 for m in modules_out if m["completed"])
    c_copy["total_lessons"] = total_lessons
    c_copy["completed_lessons"] = done_lessons
    c_copy["progress_pct"] = int(round((done_lessons / total_lessons) * 100)) if total_lessons else 0

    lab = course.get("lab")
    if lab:
        c_copy["lab"] = {
            "lab_id": lab.get("lab_id", ""),
            "title": lab.get("title", ""),
            "scenario": lab.get("scenario", ""),
            "suggested_commands": lab.get("suggested_commands", []),
            "flag_hint": lab.get("flag_hint", "")
        }

    c_copy["exam"] = [
        {"q_id": q["q_id"], "question": q["question"], "options": q["options"]}
        for q in course.get("exam", [])
    ]
    c_copy["completed"] = earned_cert is not None
    c_copy["certificate"] = earned_cert
    return c_copy



def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def get_all_courses(include_unpublished: bool = False) -> list[dict]:
    try:
        conn = get_db()
        query = (
            "SELECT * FROM courses ORDER BY rowid ASC"
            if include_unpublished
            else "SELECT * FROM courses WHERE is_published = 1 ORDER BY rowid ASC"
        )
        rows = conn.execute(query).fetchall()
        courses = []
        for r in rows:
            c_dict = {
                "id": r["id"],
                "code": r["code"],
                "division": r["division"],
                "title": r["title"],
                "credential_title": r["credential_title"],
                "ceu_credits": r["ceu_credits"],
                "xp": int(r["xp"]),
                "estimated_duration": r["estimated_duration"] or "3.0 Hours",
                "summary": r["summary"],
                "modules": json.loads(r["modules_json"]) if r["modules_json"] else [],
                "lab": json.loads(r["lab_json"]) if r["lab_json"] else {},
                "exam": json.loads(r["exam_json"]) if r["exam_json"] else [],
                "is_published": int(r["is_published"]),
                "free_preview_count": int(r["free_preview_count"]) if "free_preview_count" in r.keys() and r["free_preview_count"] is not None else 2,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            }
            courses.append(c_dict)
        conn.close()
        if courses:
            return courses
    except Exception as e:
        print(f"[COURSES DB ERROR] {e}")
    return list(ACADEMY_COURSES)


def get_course_by_id(course_id: str) -> dict | None:
    cid = (course_id or "").strip().lower()
    courses = get_all_courses(include_unpublished=True)
    return next(
        (c for c in courses if c["id"].lower() == cid or c["code"].lower() == cid),
        None
    )


def run_course_lab_command(course_id: str, raw_cmd: str) -> dict:
    course = get_course_by_id(course_id)
    cmd_clean = " ".join(raw_cmd.strip().split())
    if course and course.get("lab"):
        custom_map = (course["lab"] or {}).get("custom_commands", {})
        for k, v in custom_map.items():
            if k.strip().lower() == cmd_clean.lower():
                return {"ok": True, "command": raw_cmd, "output": v}
    try:
        return execute_lab_command(course_id, raw_cmd)
    except Exception:
        return {
            "ok": True,
            "command": raw_cmd,
            "output": f"operative@sigint-lab:~$ {cmd_clean}\n[EXEC] Command completed in simulated range environment. Type 'help' for options."
        }


def generate_course_template_from_material(topic: str, raw_material: str = "", division: str = "", code: str = "") -> dict:
    clean_topic = topic.strip() or "Advanced Cybersecurity & Cyber Defense"
    clean_code = code.strip().upper() if code.strip() else f"ACAD-{secrets.randbelow(400) + 500}"
    course_id = clean_code.lower()
    clean_div = division.strip() if division.strip() else "DIVISION 05 // ADVANCED APPLIED SECURITY"

    snippets = [line.strip() for line in raw_material.split("\n") if len(line.strip()) > 30]
    s1 = snippets[0] if len(snippets) > 0 else f"Comprehensive architectural foundations of {clean_topic}."
    s2 = snippets[1] if len(snippets) > 1 else f"Offensive threat modeling, vulnerability discovery and exploit mechanics in {clean_topic}."
    s3 = snippets[2] if len(snippets) > 2 else f"Defensive engineering, cryptographic mitigation, and real-time incident triage for {clean_topic}."
    s4 = snippets[3] if len(snippets) > 3 else f"Zero-trust integration, automated logging, and policy enforcement under NIST guidelines."
    s5 = snippets[4] if len(snippets) > 4 else f"Operational case studies, live threat hunting, and intelligence synthesis."

    modules = [
        {
            "lesson_id": f"{course_id}-m1",
            "title": f"Lesson 1.1: Core Architecture & Theoretical Foundations",
            "duration": "30 min",
            "objectives": [
                f"Deconstruct the protocol/system architecture of {clean_topic}.",
                "Analyze trust boundaries, cryptographic invariants, and threat models.",
                "Identify common misconfigurations and attack surfaces."
            ],
            "content": f"{s1}\n\nWhen architecting systems for {clean_topic}, practitioners must strictly establish zero-trust assumptions. Communication channels must enforce authenticated transport encryption, principle of least privilege, and non-repudiation.",
            "code_sample": f"# Operational Verification Script for {clean_topic}\nimport sys, os\nprint('[INFO] Verifying security posture and cryptographic bounds...')\n# Check security state\nassert os.path.exists('/etc/security'), 'Configuration missing'",
            "checkpoint_q": f"What core security property ensures that transmitted data in {clean_topic} cannot be read by unauthorized intermediaries?",
            "checkpoint_answer": "Confidentiality",
            "checkpoint_hint": "One of the primary CIA triad pillars (Confidentiality, Integrity, Availability)."
        },
        {
            "lesson_id": f"{course_id}-m2",
            "title": f"Lesson 1.2: Threat Vectors, Vulnerability Discovery & Exploitation",
            "duration": "35 min",
            "objectives": [
                f"Examine active adversary tactics targeting {clean_topic}.",
                "Simulate downgrade, injection, or timing side-channel attacks.",
                "Document vulnerability findings using standard CVSS scoring."
            ],
            "content": f"{s2}\n\nAdversaries exploit parsing differentials, improper input sanitization, and weak entropy sources. In this lesson, we dissect real-world CVE disclosures and inspect malicious payloads.",
            "code_sample": "# Vulnerability Triage Snippet\ndef audit_payload(raw_input: bytes) -> bool:\n    # Detect dangerous format strings or unsanitized metachars\n    dangerous = [b'../', b';', b'|', b'--']\n    return not any(pattern in raw_input for pattern in dangerous)",
            "checkpoint_q": "Which standard scoring system provides a numerical representation of vulnerability severity (from 0.0 to 10.0)?",
            "checkpoint_answer": "CVSS",
            "checkpoint_hint": "Four letters: Common Vulnerability Scoring System."
        },
        {
            "lesson_id": f"{course_id}-m3",
            "title": f"Lesson 1.3: Cryptographic Mitigations & Defensive Hardening",
            "duration": "40 min",
            "objectives": [
                "Implement robust authenticated encryption and key derivation.",
                "Enforce strict input parameterization to eliminate injection attacks.",
                "Configure hardened security response headers and policy enforcement."
            ],
            "content": f"{s3}\n\nRemediation requires structural defense-in-depth: moving from vulnerable string interpolation to bound placeholders, replacing weak pseudorandom number generators with OS-backed CSPRNGs, and deploying constant-time comparisons.",
            "code_sample": "import hmac, hashlib\n# Constant-time MAC comparison prevents timing leakage\ndef verify_auth_token(user_token: str, expected_token: str) -> bool:\n    return hmac.compare_digest(user_token.encode(), expected_token.encode())",
            "checkpoint_q": "Which Python function performs timing-attack resistant comparison between two cryptographic secrets?",
            "checkpoint_answer": "compare_digest",
            "checkpoint_hint": "Part of the 'hmac' module: hmac.compare_digest()."
        },
        {
            "lesson_id": f"{course_id}-m4",
            "title": f"Lesson 1.4: Zero-Trust Logging, Telemetry & Incident Response",
            "duration": "30 min",
            "objectives": [
                "Deploy structured audit logging without exposing sensitive PII.",
                "Construct NIST SP 800-61 incident response containment playbooks.",
                "Integrate SIEM alerting rules for anomalous telemetry."
            ],
            "content": f"{s4}\n\nAuditing and telemetry must be tamper-proof. Write-ahead logging, remote syslog replication over mutual TLS, and automated anomaly containment prevent adversaries from clearing system tracks.",
            "code_sample": "# SIEM Alert Rule Structure (JSON-Lines Telemetry)\n{\"timestamp\": \"2026-10-19T10:00:00Z\", \"event\": \"AUTH_ANOMALY\", \"severity\": \"HIGH\", \"action\": \"CONTAIN_SESSION\"}",
            "checkpoint_q": "In NIST SP 800-61, which phase immediately follows 'Detection & Analysis' during an active breach?",
            "checkpoint_answer": "Containment",
            "checkpoint_hint": "Stopping the attacker from spreading: Containment, Eradication & Recovery."
        },
        {
            "lesson_id": f"{course_id}-m5",
            "title": f"Lesson 1.5: Field Intelligence Synthesis & Threat Hunting Capstone",
            "duration": "45 min",
            "objectives": [
                "Synthesize intelligence observables into actionable defense signatures.",
                "Execute live threat-hunting queries across network and host endpoints.",
                "Prepare technical briefings aligned with executive and regulatory standards."
            ],
            "content": f"{s5}\n\nTrue cyber mastery requires synthesizing technical diagnostics into strategic decision-making. Operatives must be capable of isolating hostile actors, auditing configurations, and certifying system integrity.",
            "code_sample": "# Threat Hunting Query (Simulated)\nSELECT parent_process, process_name, command_line FROM host_telemetry\nWHERE command_line LIKE '%FLAG{%' OR is_elevated = 1;",
            "checkpoint_q": "What term describes structured technical evidence (such as hashes, domain names, or IP addresses) of an intrusion?",
            "checkpoint_answer": "IOC",
            "checkpoint_hint": "Three letters: Indicator of Compromise (IOC)."
        }
    ]

    flag_val = f"FLAG{{TIA_{clean_code.replace('-', '_')}_{secrets.token_hex(4).upper()}}}"
    lab = {
        "lab_id": f"lab-{course_id}",
        "title": f"Interactive Cyber Range Lab: Operation {clean_topic.upper()[:24]}",
        "scenario": f"A compromised terminal node has exhibited unauthorized activity related to {clean_topic}. As the lead SIGINT cyber operative, execute live forensic and diagnostic commands in the simulated range environment to neutralize the threat and capture the verification flag.",
        "flag": flag_val,
        "flag_hint": "Run diagnostic commands like 'audit', 'scan', and 'extract-flag' in the terminal below.",
        "suggested_commands": ["help", "status", "scan-host", "audit-policy", "extract-flag"],
        "custom_commands": {
            "help": "SIGINT DIAGNOSTIC TOOLKIT // AVAILABLE COMMANDS:\n  status        - Inspect current system and defensive posture\n  scan-host     - Run deep network & process vulnerability audit\n  audit-policy  - Verify zero-trust policy enforcement\n  extract-flag  - Recover verified operative CTF course flag\n  clear         - Reset terminal display",
            "status": f"=== SYSTEM INTEGRITY REPORT // {clean_code} ===\nTarget Environment : {clean_topic}\nDefensive Posture  : MONITORED // LEVEL-5 CLEARANCE ACTIVE\nVulnerability Scan : 1 Anomalous Process Detected on Port 8443\nStatus Code        : DEFCON-3",
            "scan-host": "=== HOST RECONNAISSANCE SCAN ===\n[+] Checking open listening sockets...\n    TCP 127.0.0.1:443   (TLS 1.3 / Authenticated)\n    TCP 127.0.0.1:8443  (UNAUTHORIZED DAEMON / PID 4192)\n[!] Found anomalous payload in /tmp/intercept.bin\n[+] Run 'audit-policy' to verify remediation controls.",
            "audit-policy": "=== ZERO-TRUST POLICY AUDIT ===\n[+] Cryptographic Assertions: PASS (256-bit Keying Verified)\n[+] File Permissions       : PASS (0400 Read-Only)\n[+] Transport Security     : PASS (TLS 1.3 Strict Enforced)\n[+] Sandboxing             : ISOLATED\nRemediation successful! You may now run 'extract-flag'.",
            "extract-flag": f"=== PRACTICAL LAB FLAG RECOVERED ===\nVerification Authority : The Intelligence Agency Directorate\nTrack Assessment       : {clean_code} — {clean_topic}\nPractical Lab Flag     :\n--------------------------------------------------\n  {flag_val}\n--------------------------------------------------\nCopy the flag above or inspect the exam section below."
        }
    }

    exam = [
        {
            "q_id": "q1",
            "question": f"1. What is the primary objective of establishing zero-trust architecture in {clean_topic}?",
            "options": [
                {"value": "VERIFY", "label": "Never trust, always verify every access request regardless of perimeter"},
                {"value": "DEFAULT_ALLOW", "label": "Grant default administrator access to all users"},
                {"value": "DISABLE_AUTH", "label": "Disable multi-factor authentication"},
                {"value": "PLAINTEXT", "label": "Transmit operational telemetry in plaintext"}
            ],
            "answer": "VERIFY"
        },
        {
            "q_id": "q2",
            "question": "2. Which defense prevents timing side-channel attacks during cryptographic hash verification in Python?",
            "options": [
                {"value": "COMPARE_DIGEST", "label": "Using hmac.compare_digest() for constant-time comparison"},
                {"value": "DOUBLE_EQUAL", "label": "Standard string equality '=='"},
                {"value": "UPPERCASE", "label": "Converting both strings to uppercase"},
                {"value": "LEN", "label": "Comparing string lengths only"}
            ],
            "answer": "COMPARE_DIGEST"
        },
        {
            "q_id": "q3",
            "question": "3. What is the primary role of bound parameter placeholders ('?') in SQL queries?",
            "options": [
                {"value": "PREVENT_SQLI", "label": "Separates SQL command structure from user data to eliminate SQL Injection"},
                {"value": "FASTER_NET", "label": "Compresses network packets across routers"},
                {"value": "ENCRYPT_DISK", "label": "Encrypts the entire physical disk drive"},
                {"value": "AUTO_BACKUP", "label": "Automatically schedules weekly backups"}
            ],
            "answer": "PREVENT_SQLI"
        },
        {
            "q_id": "q4",
            "question": "4. According to NIST SP 800-61, what is the critical initial phase of the incident response lifecycle?",
            "options": [
                {"value": "PREPARATION", "label": "Preparation (Policies, tools, training & telemetry)"},
                {"value": "PANIC", "label": "Immediate server power disconnection"},
                {"value": "MARKETING", "label": "Social media disclosure"},
                {"value": "DELETION", "label": "Deleting database logs"}
            ],
            "answer": "PREPARATION"
        },
        {
            "q_id": "q5",
            "question": "5. Which octal permission mode provides optimal security for sensitive private keys on Linux?",
            "options": [
                {"value": "400", "label": "chmod 400 (Read-only for owner, no access for others)"},
                {"value": "777", "label": "chmod 777 (Full read/write/execute for everyone)"},
                {"value": "666", "label": "chmod 666 (Read/write for all)"},
                {"value": "755", "label": "chmod 755 (Executable by all)"}
            ],
            "answer": "400"
        },
        {
            "q_id": "q6",
            "question": "6. What technical artifact represents verifiable evidence of an intrusion (e.g. SHA-256 hash or malicious C2 domain)?",
            "options": [
                {"value": "IOC", "label": "Indicator of Compromise (IOC)"},
                {"value": "CSS", "label": "Cascading Style Sheet"},
                {"value": "RAM", "label": "Random Access Memory"},
                {"value": "HTML", "label": "HyperText Markup Language"}
            ],
            "answer": "IOC"
        }
    ]

    return {
        "id": course_id,
        "code": clean_code,
        "division": clean_div,
        "title": clean_topic,
        "credential_title": f"Certified {clean_topic.split()[0]} Specialist ({clean_code.replace('ACAD-', '')})",
        "ceu_credits": "4.0 CEU Credits (NIST NICE: Protect & Defend / Analyze)",
        "xp": 1000,
        "estimated_duration": "3.5 Hours (5 Lessons + Cyber Range Lab)",
        "summary": f"A rigorous, hands-on training track in {clean_topic}. Master foundational architecture, offensive threat vectors, cryptographic defense, and zero-trust engineering.",
        "modules": modules,
        "lab": lab,
        "exam": exam,
        "is_published": 1
    }


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
        CREATE TABLE IF NOT EXISTS completed_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_callsign TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            UNIQUE(agent_callsign, lesson_id)
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            division TEXT NOT NULL,
            title TEXT NOT NULL,
            credential_title TEXT NOT NULL,
            ceu_credits TEXT NOT NULL,
            xp INTEGER NOT NULL,
            estimated_duration TEXT DEFAULT '3.0 Hours',
            summary TEXT NOT NULL,
            modules_json TEXT NOT NULL,
            lab_json TEXT NOT NULL,
            exam_json TEXT NOT NULL,
            is_published INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    course_cols = [row[1] for row in c.execute("PRAGMA table_info(courses)").fetchall()]
    if "free_preview_count" not in course_cols:
        c.execute("ALTER TABLE courses ADD COLUMN free_preview_count INTEGER DEFAULT 2")

    agent_cols = [row[1] for row in c.execute("PRAGMA table_info(agents)").fetchall()]
    if "stripe_customer_id" not in agent_cols:
        c.execute("ALTER TABLE agents ADD COLUMN stripe_customer_id TEXT DEFAULT ''")
    if "stripe_subscription_id" not in agent_cols:
        c.execute("ALTER TABLE agents ADD COLUMN stripe_subscription_id TEXT DEFAULT ''")
    if "subscription_status" not in agent_cols:
        c.execute("ALTER TABLE agents ADD COLUMN subscription_status TEXT DEFAULT 'active'")

    # Seed core courses if courses table is empty
    c_count = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if c_count == 0:
        for c_item in ACADEMY_COURSES:
            c.execute("""
                INSERT OR REPLACE INTO courses (
                    id, code, division, title, credential_title, ceu_credits, xp,
                    estimated_duration, summary, modules_json, lab_json, exam_json,
                    is_published, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                c_item["id"],
                c_item["code"],
                c_item.get("division", ""),
                c_item["title"],
                c_item.get("credential_title", ""),
                c_item.get("ceu_credits", ""),
                int(c_item.get("xp", 500)),
                c_item.get("estimated_duration", "2.5 Hours"),
                c_item.get("summary", ""),
                json.dumps(c_item.get("modules", [])),
                json.dumps(c_item.get("lab", {})),
                json.dumps(c_item.get("exam", [])),
                now_str,
                now_str
            ))

    # Seed Director / Primary Account (james.f@theintelligenceagency.net)
    existing = c.execute("SELECT id FROM agents WHERE callsign = ?", ("james.f",)).fetchone()

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
            courses_out = [_sanitize_course_for_client(c_item) for c_item in get_all_courses()]
            return self._send_json(200, {"courses": courses_out})

        if path == "/api/admin/courses":
            agent = self._get_authenticated_agent()
            if not agent or (agent["callsign"] != "james.f" and "DIRECTOR" not in agent.get("clearance_level", "").upper()):
                return self._send_json(403, {"error": "Restricted to Agency Directorate."})
            return self._send_json(200, {"courses": get_all_courses(include_unpublished=True)})

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

            lesson_rows = conn.execute(
                "SELECT lesson_id FROM completed_lessons WHERE agent_callsign = ?",
                (agent["callsign"],)
            ).fetchall()
            completed_lesson_ids = {r["lesson_id"] for r in lesson_rows}

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

            is_director = agent["callsign"] == "james.f" or "DIRECTOR" in agent.get("clearance_level", "").upper()
            agent_tier = "DIRECTOR" if is_director else agent.get("plan_tier", "OPERATIVE_PRO")

            all_courses = get_all_courses()
            courses_out = [
                _sanitize_course_for_client(
                    c_item,
                    completed_lesson_ids=completed_lesson_ids,
                    earned_cert=cert_by_course.get(c_item["id"]),
                    agent_tier=agent_tier
                )
                for c_item in all_courses
            ]

            return self._send_json(200, {
                "agent": {
                    "callsign": agent["callsign"],
                    "email_address": agent["email_address"],
                    "display_name": agent["display_name"],
                    "license_key": agent["license_key"],
                    "clearance_level": agent["clearance_level"],
                    "rank": agent["rank"],
                    "xp": agent["xp"],
                    "is_director": is_director,
                    "plan_tier": agent["plan_tier"],
                    "stripe_customer_id": agent.get("stripe_customer_id") or "",
                    "subscription_status": agent.get("subscription_status") or "active",
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

        if path == "/api/academy/lab-exec":
            course_id = (body.get("course_id") or body.get("code") or "").strip()
            command = (body.get("command") or "").strip()
            res = run_course_lab_command(course_id, command)
            return self._send_json(200, {
                "ok": res.get("ok", True),
                "command": command,
                "output": res.get("output", "")
            })

        if path == "/api/academy/lesson-checkpoint":
            course_id = (body.get("course_id") or body.get("code") or "").strip()
            lesson_id = (body.get("lesson_id") or "").strip()
            raw_answer = (body.get("answer") or "").strip()

            course = get_course_by_id(course_id)
            if not course:
                return self._send_json(404, {"error": "Academy course not found."})

            target_mod = None
            target_idx = 1
            for idx, m in enumerate(course.get("modules", []), start=1):
                mid = m.get("lesson_id") or f"{course['id']}-m{idx}"
                if mid.lower() == lesson_id.lower():
                    target_mod = dict(m)
                    target_mod["lesson_id"] = mid
                    target_idx = idx
                    break

            if not target_mod:
                return self._send_json(404, {"error": "Lesson module not found."})

            agent = self._get_authenticated_agent()
            free_preview_count = int(course.get("free_preview_count") or 2)
            is_cadet = (not agent) or (agent.get("plan_tier") == "CADET_FREE")
            is_exempt = agent and (agent["callsign"] == "james.f" or "DIRECTOR" in agent.get("clearance_level", "").upper())

            if is_cadet and not is_exempt and target_idx > free_preview_count:
                return self._send_json(200, {
                    "correct": False,
                    "requires_upgrade": True,
                    "lesson_id": target_mod["lesson_id"],
                    "message": (
                        f"🔒 LEVEL-5 OPERATIVE CLEARANCE REQUIRED // You have mastered the foundational chapters! "
                        f"Chapter {target_idx} and specialized practical exercises require Level-5 Operative ($4.99/mo) "
                        f"or Station Chief Lifetime ($69) clearance."
                    )
                })

            expected = (target_mod.get("checkpoint_answer") or target_mod.get("checkpoint_a") or "").strip()
            norm_sub = re.sub(r"[^a-zA-Z0-9._+-]", "", raw_answer).upper()
            norm_exp = re.sub(r"[^a-zA-Z0-9._+-]", "", expected).upper()

            if not norm_sub or (norm_sub != norm_exp and expected.upper() not in raw_answer.upper()):
                return self._send_json(200, {
                    "correct": False,
                    "lesson_id": target_mod["lesson_id"],
                    "message": f"CHECKPOINT MISMATCH // Review the lesson material. Hint: {target_mod.get('checkpoint_hint', '')}"
                })

            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(200, {
                    "correct": True,
                    "lesson_id": target_mod["lesson_id"],
                    "xp_gained": 0,
                    "message": "CHECKPOINT VERIFIED! (Sign in to Agent HQ to record permanent lesson progress & +50 XP)."
                })

            conn = get_db()
            c = conn.cursor()
            already = c.execute(
                "SELECT id FROM completed_lessons WHERE agent_callsign = ? AND lesson_id = ?",
                (agent["callsign"], target_mod["lesson_id"])
            ).fetchone()

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            xp_gained = 0
            new_xp = int(agent["xp"])
            new_rank = agent["rank"]

            if not already:
                c.execute(
                    "INSERT INTO completed_lessons (agent_callsign, lesson_id, completed_at) VALUES (?, ?, ?)",
                    (agent["callsign"], target_mod["lesson_id"], now_str)
                )
                xp_gained = 50
                new_xp += xp_gained
                new_rank = rank_for_xp(new_xp)
                c.execute(
                    "UPDATE agents SET xp = ?, rank = ? WHERE callsign = ?",
                    (new_xp, new_rank, agent["callsign"])
                )
                conn.commit()

            lesson_rows = c.execute(
                "SELECT lesson_id FROM completed_lessons WHERE agent_callsign = ?",
                (agent["callsign"],)
            ).fetchall()
            done_set = {r["lesson_id"] for r in lesson_rows}
            conn.close()

            course_lesson_ids = [m.get("lesson_id") or f"{course['id']}-m{idx}" for idx, m in enumerate(course.get("modules", []), start=1)]
            completed_count = sum(1 for lid in course_lesson_ids if lid in done_set)
            total_count = len(course_lesson_ids)
            progress_pct = int(round((completed_count / total_count) * 100)) if total_count else 100

            return self._send_json(200, {
                "correct": True,
                "lesson_id": target_mod["lesson_id"],
                "already_completed": already is not None,
                "xp_gained": xp_gained,
                "xp": new_xp,
                "rank": new_rank,
                "completed_lessons": completed_count,
                "total_lessons": total_count,
                "progress_pct": progress_pct,
                "message": (
                    f"LESSON CHECKPOINT VERIFIED! +{xp_gained} XP awarded ({completed_count}/{total_count} lessons complete)."
                    if xp_gained > 0 else
                    f"Lesson checkpoint already verified ({completed_count}/{total_count} lessons complete)."
                )
            })

        if path == "/api/academy/exam":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})
            course_id = (body.get("course_id") or body.get("code") or "").strip()
            answers = body.get("answers") or {}
            submitted_flag = (body.get("lab_flag") or "").strip().upper()

            course = get_course_by_id(course_id)
            if not course:
                return self._send_json(404, {"error": "Academy course not found."})

            is_cadet = agent.get("plan_tier") == "CADET_FREE"
            is_exempt = agent["callsign"] == "james.f" or "DIRECTOR" in agent.get("clearance_level", "").upper()
            if is_cadet and not is_exempt:
                return self._send_json(200, {
                    "passed": False,
                    "requires_upgrade": True,
                    "message": (
                        "🔒 CERTIFICATION RESTRICTED // The official certification exam, CEU credits, "
                        "and SHA-256 signed TIA-CERT diploma require Level-5 Operative ($4.99/mo) or Station Chief Lifetime ($69) clearance."
                    )
                })


            expected_flag = ((course.get("lab") or {}).get("flag") or "").strip().upper()
            lab_flag_valid = (not expected_flag) or (submitted_flag == expected_flag)

            total_q = len(course["exam"])
            correct_q = 0
            for q in course["exam"]:
                submitted = str(answers.get(q["q_id"], "")).strip().upper()
                if submitted == q["answer"].upper():
                    correct_q += 1

            score_pct = int(round((correct_q / total_q) * 100)) if total_q else 100
            if not lab_flag_valid:
                return self._send_json(200, {
                    "passed": False,
                    "lab_flag_valid": False,
                    "score_pct": score_pct,
                    "correct_count": correct_q,
                    "total_count": total_q,
                    "message": (
                        f"PRACTICAL LAB FLAG REQUIRED // Written score: {correct_q}/{total_q} ({score_pct}%), "
                        f"but the Cyber Range Practical Lab Flag (FLAG{{...}}) was missing or invalid. "
                        f"Run the commands in the Interactive Lab Terminal above to capture the course flag!"
                    )
                })

            if correct_q < total_q:
                return self._send_json(200, {
                    "passed": False,
                    "lab_flag_valid": True,
                    "score_pct": score_pct,
                    "correct_count": correct_q,
                    "total_count": total_q,
                    "message": f"EXAM SCORE: {correct_q}/{total_q} ({score_pct}%) | Practical Lab Flag: VERIFIED. 100% ({total_q}/{total_q}) required on the written exam for Directorate Certification!"
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

            # Also mark all lessons in this course as completed
            for m in course.get("modules", []):
                if m.get("lesson_id"):
                    c.execute(
                        "INSERT OR IGNORE INTO completed_lessons (agent_callsign, lesson_id, completed_at) VALUES (?, ?, ?)",
                        (agent["callsign"], m["lesson_id"], now_str)
                    )

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

        # ---------------------------------------------------------------------
        # BILLING & STRIPE CHECKOUT API ENDPOINTS
        # ---------------------------------------------------------------------
        if path == "/api/billing/create-checkout-session":
            agent = self._get_authenticated_agent()
            plan_tier = (body.get("plan_tier") or "OPERATIVE_MONTHLY").upper().strip()
            callsign = (agent["callsign"] if agent else (body.get("callsign") or "operative")).strip()

            stripe_key = STRIPE_SECRET_KEY

            TIER_PRICES = {
                "CADET_FREE": {"amount": 0, "currency": "usd", "name": "Cadet Recruit Access", "mode": "free"},
                "OPERATIVE_MONTHLY": {"amount": 499, "currency": "usd", "name": "Level-5 Operative Clearance (Monthly)", "mode": "subscription"},
                "OPERATIVE_ANNUAL": {"amount": 3999, "currency": "usd", "name": "Level-5 Operative Clearance (Annual Pass - Save 33%)", "mode": "subscription"},
                "STATION_CHIEF_LIFETIME": {"amount": 6900, "currency": "usd", "name": "Station Chief Clearance (Lifetime Founder)", "mode": "payment"},
            }
            tier_meta = TIER_PRICES.get(plan_tier, TIER_PRICES["OPERATIVE_MONTHLY"])

            if stripe_key and tier_meta["mode"] != "free":
                try:
                    host = self.headers.get("Host") or DOMAIN
                    protocol = "http" if ("localhost" in host or "127.0.0.1" in host) else "https"
                    origin = f"{protocol}://{host}"

                    stripe_url = "https://api.stripe.com/v1/checkout/sessions"
                    params = {
                        "mode": tier_meta["mode"],
                        "success_url": f"{origin}/?payment=success&tier={plan_tier}&session_id={{CHECKOUT_SESSION_ID}}",
                        "cancel_url": f"{origin}/?payment=cancelled",
                        "client_reference_id": callsign,
                        "metadata[callsign]": callsign,
                        "metadata[plan_tier]": plan_tier,
                        "line_items[0][price]": STRIPE_PRICE_IDS.get(plan_tier, ""),
                        "line_items[0][quantity]": "1",
                        "allow_promotion_codes": "true"
                    }
                    if agent and agent.get("email_address"):
                        params["customer_email"] = agent["email_address"]
                    elif agent and agent.get("stripe_customer_id"):
                        params["customer"] = agent["stripe_customer_id"]

                    post_data = urllib.parse.urlencode(params).encode("utf-8")
                    req = urllib.request.Request(stripe_url, data=post_data, method="POST")
                    auth_header = base64.b64encode(f"{stripe_key}:".encode("utf-8")).decode("utf-8")
                    req.add_header("Authorization", f"Basic {auth_header}")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")

                    with urllib.request.urlopen(req, timeout=12) as stripe_resp:
                        stripe_data = json.loads(stripe_resp.read().decode("utf-8"))
                        return self._send_json(200, {
                            "ok": True,
                            "checkout_url": stripe_data.get("url"),
                            "session_id": stripe_data.get("id"),
                            "simulated": False
                        })
                except Exception as ex:
                    print(f"[STRIPE API ERROR] {ex}")

            # Local Simulation / Sandbox Fallback
            return self._send_json(200, {
                "ok": True,
                "simulated": True,
                "plan_tier": plan_tier,
                "tier_name": tier_meta["name"],
                "amount": tier_meta["amount"],
                "message": f"Sandbox Billing Mode Active. Instant clearance activation available for {tier_meta['name']}."
            })

        if path == "/api/billing/verify-checkout-session":
            session_id = (body.get("session_id") or "").strip()
            if not session_id:
                return self._send_json(400, {"error": "Missing session_id."})

            stripe_key = STRIPE_SECRET_KEY
            if not stripe_key:
                return self._send_json(500, {"error": "Stripe key not configured."})

            try:
                req = urllib.request.Request(f"https://api.stripe.com/v1/checkout/sessions/{session_id}", method="GET")
                auth_header = base64.b64encode(f"{stripe_key}:".encode("utf-8")).decode("utf-8")
                req.add_header("Authorization", f"Basic {auth_header}")
                with urllib.request.urlopen(req, timeout=12) as stripe_resp:
                    sess = json.loads(stripe_resp.read().decode("utf-8"))

                if sess.get("payment_status") != "paid" and sess.get("status") != "complete":
                    return self._send_json(400, {"error": "Payment session not completed."})

                meta = sess.get("metadata") or {}
                callsign = meta.get("callsign") or sess.get("client_reference_id") or ""
                plan_tier = (meta.get("plan_tier") or "OPERATIVE_MONTHLY").upper().strip()
                customer_id = sess.get("customer") or ""
                sub_id = sess.get("subscription") or ""

                agent = self._get_authenticated_agent()
                if not callsign and agent:
                    callsign = agent["callsign"]

                if not callsign:
                    return self._send_json(400, {"error": "Unable to resolve agent callsign for session."})

                clearance_map = {
                    "CADET_FREE": ("CADET RECRUIT", "CADET // LEVEL 1"),
                    "OPERATIVE_MONTHLY": ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"),
                    "OPERATIVE_ANNUAL": ("LEVEL-5 OPERATIVE (ANNUAL)", "SENIOR OPERATIVE // LEVEL 5"),
                    "STATION_CHIEF_LIFETIME": ("STATION CHIEF (LIFETIME)", "STATION CHIEF // LEVEL 5")
                }
                clearance_level, rank = clearance_map.get(plan_tier, ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"))

                conn = get_db()
                conn.execute("""
                    UPDATE agents 
                    SET plan_tier = ?, clearance_level = ?, rank = ?, 
                        stripe_customer_id = CASE WHEN ? != '' THEN ? ELSE stripe_customer_id END,
                        stripe_subscription_id = CASE WHEN ? != '' THEN ? ELSE stripe_subscription_id END,
                        subscription_status = 'active'
                    WHERE callsign = ?
                """, (plan_tier, clearance_level, rank, customer_id, customer_id, sub_id, sub_id, callsign))

                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                conn.execute("""
                    INSERT INTO transmissions (
                        agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                    ) VALUES (?, 'inbox', 'directorate@theintelligenceagency.net', ?, ?, ?, 'CLEARANCE UPGRADE // STRIPE VERIFIED', 0, ?)
                """, (
                    callsign,
                    f"{callsign}@theintelligenceagency.net",
                    f"[DIRECTORATE] Verified Clearance Escalation to {clearance_level}",
                    (
                        f"OFFICIAL STRIPE CLEARANCE VERIFIED\n"
                        f"===================================\n"
                        f"Callsign        : {callsign}\n"
                        f"Verified Plan   : {plan_tier}\n"
                        f"Clearance Level : {clearance_level}\n"
                        f"Rank            : {rank}\n"
                        f"Stripe Session  : {session_id}\n"
                        f"Status          : ACTIVE // ALL MODULES & CERTIFICATIONS UNLOCKED\n\n"
                        f"Your clearance and webmail privileges have been officially updated."
                    ),
                    now_str
                ))
                conn.commit()
                conn.close()

                return self._send_json(200, {
                    "ok": True,
                    "plan_tier": plan_tier,
                    "clearance_level": clearance_level,
                    "rank": rank,
                    "message": f"Payment verified! Clearance escalated to {clearance_level} ({plan_tier})."
                })
            except Exception as ex:
                print(f"[VERIFY SESSION ERROR] {ex}")
                return self._send_json(500, {"error": f"Failed to verify Stripe session: {ex}"})

        if path == "/api/billing/customer-portal":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})

            stripe_key = STRIPE_SECRET_KEY
            if not stripe_key:
                return self._send_json(500, {"error": "Stripe key not configured."})

            host = self.headers.get("Host") or DOMAIN
            protocol = "http" if ("localhost" in host or "127.0.0.1" in host) else "https"
            return_url = f"{protocol}://{host}/"

            customer_id = (agent.get("stripe_customer_id") or "").strip()
            if not customer_id:
                try:
                    q = urllib.parse.urlencode({"email": agent["email_address"], "limit": 1})
                    req = urllib.request.Request(f"https://api.stripe.com/v1/customers?{q}", method="GET")
                    auth_header = base64.b64encode(f"{stripe_key}:".encode("utf-8")).decode("utf-8")
                    req.add_header("Authorization", f"Basic {auth_header}")
                    with urllib.request.urlopen(req, timeout=10) as r:
                        cust_data = json.loads(r.read().decode("utf-8"))
                        if cust_data.get("data"):
                            customer_id = cust_data["data"][0]["id"]
                            conn = get_db()
                            conn.execute("UPDATE agents SET stripe_customer_id = ? WHERE callsign = ?", (customer_id, agent["callsign"]))
                            conn.commit()
                            conn.close()
                except Exception as ex:
                    print(f"[CUSTOMER SEARCH ERROR] {ex}")

            if not customer_id:
                return self._send_json(400, {
                    "error": "No Stripe customer account linked to this callsign yet. Upgrade your clearance first to manage subscriptions."
                })

            try:
                portal_url = "https://api.stripe.com/v1/billing_portal/sessions"
                params = urllib.parse.urlencode({
                    "customer": customer_id,
                    "return_url": return_url
                }).encode("utf-8")
                req = urllib.request.Request(portal_url, data=params, method="POST")
                auth_header = base64.b64encode(f"{stripe_key}:".encode("utf-8")).decode("utf-8")
                req.add_header("Authorization", f"Basic {auth_header}")
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                with urllib.request.urlopen(req, timeout=12) as r:
                    portal_data = json.loads(r.read().decode("utf-8"))
                    return self._send_json(200, {
                        "ok": True,
                        "portal_url": portal_data.get("url")
                    })
            except Exception as ex:
                print(f"[PORTAL ERROR] {ex}")
                return self._send_json(500, {"error": f"Failed to create billing portal: {ex}"})

        if path == "/api/billing/webhook":
            event_type = body.get("type", "")
            data_obj = (body.get("data") or {}).get("object") or {}
            print(f"[STRIPE WEBHOOK] Received event: {event_type}")

            conn = get_db()
            if event_type == "checkout.session.completed":
                meta = data_obj.get("metadata") or {}
                callsign = meta.get("callsign") or data_obj.get("client_reference_id")
                plan_tier = (meta.get("plan_tier") or "OPERATIVE_MONTHLY").upper().strip()
                customer_id = data_obj.get("customer") or ""
                sub_id = data_obj.get("subscription") or ""

                if callsign:
                    clearance_map = {
                        "CADET_FREE": ("CADET RECRUIT", "CADET // LEVEL 1"),
                        "OPERATIVE_MONTHLY": ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"),
                        "OPERATIVE_ANNUAL": ("LEVEL-5 OPERATIVE (ANNUAL)", "SENIOR OPERATIVE // LEVEL 5"),
                        "STATION_CHIEF_LIFETIME": ("STATION CHIEF (LIFETIME)", "STATION CHIEF // LEVEL 5")
                    }
                    clearance_level, rank = clearance_map.get(plan_tier, ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"))
                    conn.execute("""
                        UPDATE agents 
                        SET plan_tier = ?, clearance_level = ?, rank = ?, 
                            stripe_customer_id = CASE WHEN ? != '' THEN ? ELSE stripe_customer_id END,
                            stripe_subscription_id = CASE WHEN ? != '' THEN ? ELSE stripe_subscription_id END,
                            subscription_status = 'active'
                        WHERE callsign = ?
                    """, (plan_tier, clearance_level, rank, customer_id, customer_id, sub_id, sub_id, callsign))
                    conn.commit()

            elif event_type == "customer.subscription.deleted":
                sub_id = data_obj.get("id")
                if sub_id:
                    conn.execute("""
                        UPDATE agents
                        SET plan_tier = 'CADET_FREE', clearance_level = 'CADET RECRUIT', rank = 'CADET // LEVEL 1', subscription_status = 'canceled'
                        WHERE stripe_subscription_id = ?
                    """, (sub_id,))
                    conn.commit()

            elif event_type == "invoice.payment_failed":
                sub_id = data_obj.get("subscription")
                if sub_id:
                    conn.execute("UPDATE agents SET subscription_status = 'past_due' WHERE stripe_subscription_id = ?", (sub_id,))
                    conn.commit()

            conn.close()
            return self._send_json(200, {"received": True})

        if path == "/api/billing/simulate-upgrade":
            agent = self._get_authenticated_agent()
            if not agent:
                return self._send_json(401, {"error": "Unauthorized."})

            new_tier = (body.get("plan_tier") or "OPERATIVE_MONTHLY").upper().strip()
            clearance_map = {
                "CADET_FREE": ("CADET RECRUIT", "CADET // LEVEL 1"),
                "OPERATIVE_MONTHLY": ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"),
                "OPERATIVE_ANNUAL": ("LEVEL-5 OPERATIVE (ANNUAL)", "SENIOR OPERATIVE // LEVEL 5"),
                "STATION_CHIEF_LIFETIME": ("STATION CHIEF (LIFETIME)", "STATION CHIEF // LEVEL 5")
            }
            clearance_level, rank = clearance_map.get(new_tier, ("LEVEL-5 OPERATIVE", "SPECIAL AGENT // LEVEL 5"))

            conn = get_db()
            conn.execute("""
                UPDATE agents 
                SET plan_tier = ?, clearance_level = ?, rank = ?, subscription_status = 'active'
                WHERE callsign = ?
            """, (new_tier, clearance_level, rank, agent["callsign"]))

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            conn.execute("""
                INSERT INTO transmissions (
                    agent_callsign, folder, sender, recipient, subject, body, classification, is_read, created_at
                ) VALUES (?, 'inbox', 'directorate@theintelligenceagency.net', ?, ?, ?, 'CLEARANCE UPGRADE // OFFICIAL', 0, ?)
            """, (
                agent["callsign"],
                agent["email_address"],
                f"[DIRECTORATE] Clearance Escalated to {clearance_level}",
                (
                    f"OPERATIVE CLEARANCE UPGRADE CONFIRMED\n"
                    f"=====================================\n"
                    f"Callsign        : {agent['callsign']}\n"
                    f"New Plan Tier   : {new_tier}\n"
                    f"Clearance Level : {clearance_level}\n"
                    f"Rank            : {rank}\n"
                    f"Status          : ACTIVE // ALL MODULES & CERTIFICATIONS UNLOCKED\n\n"
                    f"Welcome to full operational status."
                ),
                now_str
            ))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "ok": True,
                "plan_tier": new_tier,
                "clearance_level": clearance_level,
                "rank": rank,
                "message": f"Clearance escalated to {clearance_level} ({new_tier})!"
            })

        # ---------------------------------------------------------------------
        # DIRECTOR COURSE STUDIO API ENDPOINTS
        # ---------------------------------------------------------------------
        if path == "/api/admin/courses/save":
            agent = self._get_authenticated_agent()
            if not agent or (agent["callsign"] != "james.f" and "DIRECTOR" not in agent.get("clearance_level", "").upper()):
                return self._send_json(403, {"error": "Restricted to Agency Directorate."})

            course_data = body.get("course") or body
            cid = re.sub(r"[^a-z0-9_-]", "", str(course_data.get("id") or course_data.get("code") or "").lower().strip())
            code = (course_data.get("code") or cid.upper()).strip()
            title = (course_data.get("title") or "Untitled Track").strip()
            division = (course_data.get("division") or "DIVISION 05 // ADVANCED APPLIED SECURITY").strip()
            cred_title = (course_data.get("credential_title") or f"Certified {title} Specialist").strip()
            ceu = (course_data.get("ceu_credits") or "4.0 CEU Credits (NIST NICE)").strip()
            xp = int(course_data.get("xp") or 1000)
            duration = (course_data.get("estimated_duration") or "3.0 Hours").strip()
            summary = (course_data.get("summary") or "").strip()
            modules = course_data.get("modules") or []
            lab = course_data.get("lab") or {}
            exam = course_data.get("exam") or []
            is_pub = 1 if course_data.get("is_published", True) else 0

            if not cid or not code:
                return self._send_json(400, {"error": "Course ID and Code are required."})

            for idx, m in enumerate(modules, start=1):
                if not m.get("lesson_id"):
                    m["lesson_id"] = f"{cid}-m{idx}"

            free_preview = int(course_data.get("free_preview_count") or 2)

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            conn = get_db()
            conn.execute("""
                INSERT OR REPLACE INTO courses (
                    id, code, division, title, credential_title, ceu_credits, xp,
                    estimated_duration, summary, modules_json, lab_json, exam_json,
                    free_preview_count, is_published, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM courses WHERE id = ?), ?), ?)
            """, (
                cid, code, division, title, cred_title, ceu, xp, duration, summary,
                json.dumps(modules), json.dumps(lab), json.dumps(exam),
                free_preview, is_pub, cid, now_str, now_str
            ))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "ok": True,
                "course_id": cid,
                "message": f"Course [{code}] successfully saved & published to Live Academy!"
            })

        if path == "/api/admin/courses/delete":
            agent = self._get_authenticated_agent()
            if not agent or (agent["callsign"] != "james.f" and "DIRECTOR" not in agent.get("clearance_level", "").upper()):
                return self._send_json(403, {"error": "Restricted to Agency Directorate."})

            cid = (body.get("course_id") or body.get("id") or "").strip().lower()
            if not cid:
                return self._send_json(400, {"error": "Course ID required."})

            conn = get_db()
            conn.execute("DELETE FROM courses WHERE id = ?", (cid,))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "ok": True,
                "message": f"Course '{cid}' deleted from database."
            })

        if path == "/api/admin/courses/ai-ingest":
            agent = self._get_authenticated_agent()
            if not agent or (agent["callsign"] != "james.f" and "DIRECTOR" not in agent.get("clearance_level", "").upper()):
                return self._send_json(403, {"error": "Restricted to Agency Directorate."})

            topic = (body.get("topic") or "").strip()
            raw_material = (body.get("raw_material") or "").strip()
            code = (body.get("code") or "").strip()
            division = (body.get("division") or "").strip()

            if not topic and not raw_material:
                return self._send_json(400, {"error": "Please provide a Course Topic or paste raw material."})

            draft = generate_course_template_from_material(topic=topic or "Advanced Cyber Operations", raw_material=raw_material, division=division, code=code)
            return self._send_json(200, {
                "ok": True,
                "course": draft,
                "draft_course": draft
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
