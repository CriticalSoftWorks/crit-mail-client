"""
The Intelligence Agency Academy — Full Multi-Chapter Curriculum, Interactive Lab Simulator & Certification Exams.
Aligned with the NIST NICE Cybersecurity Workforce Framework (SP 800-181).
"""

ACADEMY_COURSES = [
    # =========================================================================
    # TRACK 1: ACAD-101 — NETWORK PROTOCOLS, DNS & EMAIL SECURITY ENGINEERING
    # =========================================================================
    {
        "id": "acad-101",
        "code": "ACAD-101",
        "division": "DIVISION 01 // NETWORK & COMMS ENGINEERING",
        "title": "Network Protocols, DNS Authentication & Email Security Engineering",
        "credential_title": "Certified SIGINT Communications Specialist (CSCS)",
        "ceu_credits": "6.0 CEU Credits (NIST NICE: Protect & Defend / Network Services)",
        "xp": 750,
        "summary": (
            "A comprehensive engineering course covering TCP/IP mail transport (SMTP, IMAP4, POP3), "
            "RFC 8314 Implicit TLS 1.3 cryptography, STARTTLS downgrade attacks, the DNS authentication triad "
            "(SPF, 2048-bit RSA DKIM, and DMARC), and raw multi-hop header forensics."
        ),
        "modules": [
            {
                "id": "acad-101-m1",
                "title": "Lesson 1.1: Mail Transport Architecture (MTA, MSA, MDA & MUA)",
                "duration": "35 min",
                "objectives": [
                    "Distinguish between Mail User Agents (MUA), Mail Submission Agents (MSA), and Mail Transfer Agents (MTA).",
                    "Trace how DNS MX (Mail Exchanger) priorities route messages across autonomous systems.",
                    "Understand why Port 25 is restricted to server-to-server relay while Port 465/587 handles authenticated submission."
                ],
                "content": (
                    "Internet email is an asynchronous store-and-forward system governed by RFC 5321 (SMTP) and RFC 5322 (Message Format). "
                    "When an operative composes a message in a Mail User Agent (MUA) such as Agency Webmail, the message does not fly directly "
                    "to the recipient's laptop. Instead, it traverses four distinct architectural hops:\n\n"
                    "1. MUA -> MSA (Submission): The client authenticates via SASL (PLAIN/LOGIN over TLS) to an outbound Mail Submission Agent "
                    "(e.g., email-smtp.us-east-1.amazonaws.com on Port 465).\n"
                    "2. MSA -> Outbound MTA (Queue & Sign): The outbound MTA attaches a cryptographic DKIM-Signature header and queries DNS for the "
                    "recipient domain's MX (Mail Exchanger) records, sorting them by lowest preference number (priority 10 before priority 20).\n"
                    "3. Outbound MTA -> Inbound MX (Relay): Server-to-server transfer occurs over TCP Port 25.\n"
                    "4. MDA -> IMAP4/POP3 Store: The Mail Delivery Agent writes the message into the recipient's mailbox, where the recipient's MUA "
                    "retrieves it via IMAP4 over Implicit TLS (Port 993)."
                ),
                "code_sample": (
                    "# Query MX records and priority values for a target domain:\n"
                    "$ dig +short MX theintelligenceagency.net\n"
                    "10 mailserver.businessidentity.llc.\n\n"
                    "# SMTP Envelope vs. Message Data (RFC 5321 vs RFC 5322):\n"
                    "EHLO sigint-workstation.local\n"
                    "MAIL FROM:<bounce@theintelligenceagency.net>   # <-- RFC 5321 Envelope Sender (Return-Path)\n"
                    "RCPT TO:<analyst@target.org>                   # <-- RFC 5321 Envelope Recipient\n"
                    "DATA\n"
                    "From: Agent Falcon <falcon@theintelligenceagency.net>  # <-- RFC 5322 Header From\n"
                    "Subject: [EYES ONLY] Network Telemetry\n"
                    ".\n"
                    "QUIT"
                ),
                "checkpoint_question": "Which DNS record type specifies the receiving mail server hostnames and preference priorities for a domain?",
                "checkpoint_answer": "MX",
                "checkpoint_hint": "Two letters: Mail Exchanger."
            },
            {
                "id": "acad-101-m2",
                "title": "Lesson 1.2: Implicit TLS 1.3 (RFC 8314) vs. STARTTLS Downgrade Attacks",
                "duration": "40 min",
                "objectives": [
                    "Analyze how active Man-in-the-Middle (MitM) attackers execute STRIPTLS attacks on opportunistic STARTTLS.",
                    "Configure RFC 8314 Implicit TLS on Port 465 (SMTPS) and Port 993 (IMAPS).",
                    "Inspect TLS 1.3 cipher suites and Ephemeral Diffie-Hellman (ECDHE) forward secrecy."
                ],
                "content": (
                    "Historically, protocols like SMTP (Port 587) and IMAP (Port 143) started connections in unencrypted plaintext and relied on "
                    "an opportunistic upgrade command called STARTTLS. However, if an adversary controls a rogue Wi-Fi access point or ISP router, "
                    "they can intercept the server's greeting and overwrite '250-STARTTLS' with spaces or inject a fake '454 TLS not available' error. "
                    "This is known as a STRIPTLS downgrade attack—causing vulnerable clients to transmit credentials in cleartext.\n\n"
                    "To eliminate this entire attack class, the IETF published RFC 8314, deprecating cleartext startup and mandating Implicit TLS from "
                    "the very first TCP SYN/ACK packet:\n"
                    "• Port 465: Implicit TLS for SMTP Submission (SMTPS)\n"
                    "• Port 993: Implicit TLS for IMAP4 Synchronization (IMAPS)\n"
                    "• Port 995: Implicit TLS for POP3 Retrieval (POP3S)\n\n"
                    "With Implicit TLS 1.3, the TLS handshake begins immediately before any application bytes are sent, using AEAD cipher suites "
                    "such as TLS_AES_256_GCM_SHA384 with X25519 ephemeral key exchange for Perfect Forward Secrecy (PFS)."
                ),
                "code_sample": (
                    "# Verify Implicit TLS 1.3 Handshake & Certificate Chain on Port 465:\n"
                    "$ openssl s_client -connect email-smtp.us-east-1.amazonaws.com:465 -tls1_3\n"
                    "CONNECTED(00000003)\n"
                    "---\n"
                    "New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384\n"
                    "Server public key is 2048 bit\n"
                    "Secure Renegotiation IS NOT supported\n"
                    "220 email-smtp.amazonaws.com ESMTP SimpleEmailService"
                ),
                "checkpoint_question": "What is the name of the Man-in-the-Middle attack that strips the '250-STARTTLS' capability from a plaintext SMTP session?",
                "checkpoint_answer": "STRIPTLS",
                "checkpoint_hint": "One word: STRIP + TLS."
            },
            {
                "id": "acad-101-m3",
                "title": "Lesson 1.3: Sender Policy Framework (SPF) & Envelope Alignment",
                "duration": "45 min",
                "objectives": [
                    "Construct and audit RFC 7208 SPF TXT records using ip4, include, and enforcement qualifiers (-all vs ~all).",
                    "Respect the 10-DNS-lookup limit in SPF evaluation to prevent PermError failures.",
                    "Understand why SPF alone cannot stop display-header spoofing without DMARC alignment."
                ],
                "content": (
                    "Because RFC 5321 originally allowed any server to claim any 'MAIL FROM' address, attackers routinely forged sender domains. "
                    "Sender Policy Framework (SPF, RFC 7208) allows a domain owner to publish a DNS TXT record listing every IP address or subnet "
                    "authorized to send mail on behalf of that domain.\n\n"
                    "Key SPF Mechanisms & Qualifiers:\n"
                    "• v=spf1 : Declares the SPF version.\n"
                    "• ip4:198.51.100.0/24 : Authorizes a specific IPv4 CIDR block.\n"
                    "• include:amazonses.com : Delegates authorization to a third-party provider's SPF record.\n"
                    "• ~all (SoftFail) : Marks unauthorized senders as suspicious/spam but accepts delivery for further DMARC evaluation.\n"
                    "• -all (HardFail) : Instructs receivers that no other IPs are permitted.\n\n"
                    "CRITICAL ENGINEERING LIMITATION: SPF only validates the RFC 5321 'Return-Path' (MAIL FROM / bounce address)—NOT the 'From:' header "
                    "displayed to the human user! An attacker can pass SPF using their own bounce domain while forging 'From: ceo@yourcompany.com' "
                    "unless DMARC identifier alignment is enforced."
                ),
                "code_sample": (
                    "; Authoritative DNS Zone SPF Record:\n"
                    "theintelligenceagency.net. 300 IN TXT \"v=spf1 include:amazonses.com ~all\"\n"
                    "bounce.theintelligenceagency.net. 300 IN TXT \"v=spf1 include:amazonses.com ~all\"\n\n"
                    "; SPF 10-Lookup Rule: Each 'include', 'a', 'mx', 'ptr', or 'exists' mechanism\n"
                    "; counts toward a hard maximum of 10 DNS queries (RFC 7208 Section 4.6.4)."
                ),
                "checkpoint_question": "What is the maximum number of DNS-querying mechanisms ('include', 'mx', 'a') allowed during SPF evaluation before a PermError occurs?",
                "checkpoint_answer": "10",
                "checkpoint_hint": "Enter the number (between 5 and 15)."
            },
            {
                "id": "acad-101-m4",
                "title": "Lesson 1.4: Asymmetric DKIM Signing (RSA-2048) & DMARC Enforcement",
                "duration": "50 min",
                "objectives": [
                    "Trace how DKIM signs canonicalized headers and the SHA-256 body hash (bh=) using an RSA-2048 private key.",
                    "Verify DKIM public keys published at <selector>._domainkey.<domain>.",
                    "Deploy DMARC policies (p=none, p=quarantine, p=reject) and aggregate XML forensic reporting (rua=)."
                ],
                "content": (
                    "DomainKeys Identified Mail (DKIM, RFC 6376) solves both message integrity and origin authentication using public-key cryptography:\n\n"
                    "1. Signing (Outbound MTA): Before transmitting an email, the server computes a SHA-256 hash of the message body ('bh=') and "
                    "cryptographically signs selected headers (From, To, Subject, Date, Message-ID) plus the body hash using its private RSA-2048 key.\n"
                    "2. Verification (Inbound MX): The receiving server reads the 'd=' (domain) and 's=' (selector) tags from the 'DKIM-Signature' header "
                    "and queries DNS for '<selector>._domainkey.<domain>' to fetch the sender's public key. If a single character of the Subject or Body "
                    "was modified in transit, the RSA signature verification fails!\n\n"
                    "DMARC (RFC 7489) binds SPF and DKIM together via 'Identifier Alignment':\n"
                    "To pass DMARC, the domain in the visible 'From:' header MUST match either the verified SPF domain OR the verified DKIM 'd=' domain. "
                    "If both fail alignment, DMARC enforces the domain owner's policy: 'p=none' (monitor only), 'p=quarantine' (send to spam/junk), "
                    "or 'p=reject' (drop the connection outright)."
                ),
                "code_sample": (
                    "# Anatomy of a Real DKIM-Signature Header:\n"
                    "DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/simple;\n"
                    "  s=dc32j2cf5mlf4j5f; d=theintelligenceagency.net;\n"
                    "  h=From:To:Subject:Date:Message-ID;\n"
                    "  bh=47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=;\n"
                    "  b=K9xL2m...2048-bit-RSA-Signature...\n\n"
                    "# Authoritative DMARC Record at _dmarc.theintelligenceagency.net:\n"
                    "\"v=DMARC1; p=quarantine; pct=100; rua=mailto:postmaster@theintelligenceagency.net\""
                ),
                "checkpoint_question": "In a DKIM-Signature header, which tag specifies the SHA-256 hash of the canonicalized message body?",
                "checkpoint_answer": "BH",
                "checkpoint_hint": "Two letters standing for Body Hash (written before '=' in the header)."
            },
            {
                "id": "acad-101-m5",
                "title": "Lesson 1.5: Multi-Hop SMTP Header Forensics & Spoofing Investigation",
                "duration": "45 min",
                "objectives": [
                    "Read 'Received:' trace headers chronologically from bottom (origin) to top (final destination).",
                    "Spot forged 'Received:' headers injected by an attacker prior to the first trusted MX boundary.",
                    "Correlate 'Authentication-Results' verdicts with envelope 'Return-Path' headers."
                ],
                "content": (
                    "When investigating a suspected spear-phishing or intelligence impersonation dispatch, never trust the 'From:', 'Reply-To:', "
                    "or 'X-Originating-IP:' headers—all of these are controlled by the sender.\n\n"
                    "Instead, follow the Golden Rule of Header Forensics:\n"
                    "1. Every MTA that handles an email prepends a 'Received:' header at the VERY TOP of the message.\n"
                    "2. Therefore, the topmost 'Received:' header was written by YOUR trusted mail server, and the chronological path runs from "
                    "BOTTOM (earliest hop) to TOP (latest hop).\n"
                    "3. Attackers sometimes inject fake 'Received:' headers at the bottom of the email to disguise their origin. To find the truth, "
                    "locate the boundary where the email entered your organization's trusted MX server and read the connecting peer IP recorded there, "
                    "alongside your server's 'Authentication-Results:' header."
                ),
                "code_sample": (
                    "Return-Path: <mailer@compromised-vps.example>\n"
                    "Received: from mx1.theintelligenceagency.net (10.0.2.15) by imap.internal (TLSv1.3); Sat, 17 Oct 2026 18:00:02 +0000\n"
                    "Received: from mail-out.hostile-asn.net ([198.51.100.77]) by mx1.theintelligenceagency.net; Sat, 17 Oct 2026 18:00:01 +0000\n"
                    "Received: from [10.99.88.1] (FORGED HEADER BY ATTACKER)\n"
                    "Authentication-Results: mx1.theintelligenceagency.net;\n"
                    "  spf=fail (sender IP is 198.51.100.77) smtp.mailfrom=theintelligenceagency.net;\n"
                    "  dkim=none; dmarc=fail action=quarantine header.from=theintelligenceagency.net"
                ),
                "checkpoint_question": "Where does each receiving mail server insert its new 'Received:' trace header—at the TOP or BOTTOM of the header block?",
                "checkpoint_answer": "TOP",
                "checkpoint_hint": "Three letters: each hop prepends its stamp at the very ___."
            }
        ],
        "lab": {
            "title": "Interactive Cyber Range Lab: Operation PHANTOM RELAY (DNS & SMTP Forensics CLI)",
            "scenario": (
                "An intercepted email (`/var/spool/mail/intercept_09.eml`) claims to come from Directorate Security, but our perimeter "
                "sensor flagged an anomaly. Use the interactive SIGINT CLI below to query DNS records (`dig`), test TLS handshakes (`openssl`), "
                "and inspect the raw email headers (`inspect-headers`) to uncover the Lab Flag (`FLAG{...}`)."
            ),
            "suggested_commands": [
                "help",
                "dig TXT theintelligenceagency.net",
                "dig TXT _dmarc.theintelligenceagency.net",
                "openssl s_client -connect email-smtp.us-east-1.amazonaws.com:465",
                "inspect-headers /var/spool/mail/intercept_09.eml"
            ],
            "flag": "FLAG{RFC8314_DKIM_VERIFIED_465}"
        },
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
                "question": "3. When inspecting raw email headers for spoofing, which header chain is prepended hop-by-hop from bottom (earliest) to top (most recent)?",
                "options": [
                    {"value": "RECEIVED", "label": "Received: headers"},
                    {"value": "REPLY-TO", "label": "Reply-To: headers"},
                    {"value": "SUBJECT", "label": "Subject: headers"},
                    {"value": "X-MAILER", "label": "X-Mailer: headers"}
                ],
                "answer": "RECEIVED"
            },
            {
                "q_id": "q4",
                "question": "4. Why can an attacker pass SPF checks while still forging the human-visible 'From:' address if DMARC is not enabled?",
                "options": [
                    {"value": "ENVELOPE_ONLY", "label": "SPF only validates the RFC 5321 Return-Path (MAIL FROM) domain, not the RFC 5322 From header"},
                    {"value": "SPF_ENCRYPTED", "label": "SPF encrypts the message body with DES"},
                    {"value": "PORT_993", "label": "SPF only operates on UDP Port 993"},
                    {"value": "NO_TXT", "label": "SPF does not use DNS TXT records"}
                ],
                "answer": "ENVELOPE_ONLY"
            },
            {
                "q_id": "q5",
                "question": "5. What happens when an SPF record requires more than 10 DNS-querying mechanisms ('include', 'a', 'mx') to evaluate?",
                "options": [
                    {"value": "PERMERROR", "label": "Receivers abort evaluation and return an SPF PermError"},
                    {"value": "AUTO_PASS", "label": "The message automatically passes DMARC"},
                    {"value": "TLS_UPGRADE", "label": "The connection upgrades to TLS 1.3"},
                    {"value": "DKIM_SIGN", "label": "The server generates a new DKIM key"}
                ],
                "answer": "PERMERROR"
            },
            {
                "q_id": "q6",
                "question": "6. Which DMARC policy tag instructs receiving mail servers to route unaligned, unauthenticated emails into the recipient's spam/junk folder?",
                "options": [
                    {"value": "P_NONE", "label": "p=none"},
                    {"value": "P_QUARANTINE", "label": "p=quarantine"},
                    {"value": "P_ALLOW", "label": "p=allow"},
                    {"value": "P_ENCRYPT", "label": "p=encrypt"}
                ],
                "answer": "P_QUARANTINE"
            }
        ]
    },

    # =========================================================================
    # TRACK 2: ACAD-201 — APPLIED CRYPTOGRAPHY & PYTHON SECURITY AUTOMATION
    # =========================================================================
    {
        "id": "acad-201",
        "code": "ACAD-201",
        "division": "DIVISION 02 // APPLIED CRYPTOGRAPHY & PYTHON",
        "title": "Applied Cryptography, Key Derivation & Python Security Automation",
        "credential_title": "Certified Cryptographic Python Analyst (CCPA)",
        "ceu_credits": "8.0 CEU Credits (NIST NICE: Design & Development / Cryptography)",
        "xp": 1000,
        "summary": (
            "Master symmetric and authenticated encryption (XOR, One-Time Pads, AES-256-GCM), password key stretching "
            "(PBKDF2-HMAC-SHA256 & Argon2 concepts), CSPRNG entropy in Python ('secrets'), and constant-time MAC verification."
        ),
        "modules": [
            {
                "id": "acad-201-m1",
                "title": "Lesson 2.1: Information Theory, XOR & Why Key Reuse Breaks One-Time Pads",
                "duration": "40 min",
                "objectives": [
                    "Perform bitwise XOR operations on ASCII/hexadecimal byte streams in Python.",
                    "Understand Claude Shannon's theorem for perfect secrecy in a One-Time Pad (OTP).",
                    "Exploit a Two-Time Pad (key reuse depth) as NSA cryptanalysts did in Project VENONA."
                ],
                "content": (
                    "At the heart of modern stream ciphers and block modes lies the bitwise Exclusive-OR (XOR, `^` in Python) operation. "
                    "XOR has a remarkable self-inverse mathematical property:\n"
                    "• `Plaintext ^ Key = Ciphertext`\n"
                    "• `Ciphertext ^ Key = Plaintext`\n"
                    "• `A ^ A = 0` and `A ^ 0 = A`\n\n"
                    "In 1949, Claude Shannon proved that a One-Time Pad (OTP) is mathematically unbreakable IF AND ONLY IF the key is:\n"
                    "1. Truly random (generated by a hardware/OS entropy source),\n"
                    "2. At least as long as the plaintext, and\n"
                    "3. NEVER reused.\n\n"
                    "What happens if an operator reuses the same key `K` for two messages `P1` and `P2`? "
                    "An adversary who intercepts `C1 = P1 ^ K` and `C2 = P2 ^ K` simply computes `C1 ^ C2`. Because `K ^ K = 0`, the key "
                    "cancels out completely (`C1 ^ C2 = P1 ^ P2`), allowing crib-dragging recovery of both plaintexts!"
                ),
                "code_sample": (
                    "# Python XOR Stream & Two-Time Pad Demonstration:\n"
                    "def xor_bytes(a: bytes, b: bytes) -> bytes:\n"
                    "    return bytes(x ^ y for x, y in zip(a, b))\n\n"
                    "key = bytes.fromhex('a1f0994c82b71120')\n"
                    "c1 = xor_bytes(b'ATTACK01', key)\n"
                    "c2 = xor_bytes(b'DEFEND02', key)\n"
                    "# Key cancels out completely when XORing C1 and C2:\n"
                    "assert xor_bytes(c1, c2) == xor_bytes(b'ATTACK01', b'DEFEND02')"
                ),
                "checkpoint_question": "In bitwise XOR arithmetic, what is the result of XORing any byte value K with itself (K ^ K)?",
                "checkpoint_answer": "0",
                "checkpoint_hint": "A single digit: identical bits XORed together always yield ___."
            },
            {
                "id": "acad-201-m2",
                "title": "Lesson 2.2: Block Cipher Modes & Authenticated Encryption (AES-256-GCM)",
                "duration": "50 min",
                "objectives": [
                    "Explain why Electronic Codebook (AES-ECB) leaks visual and structural patterns.",
                    "Understand Padding Oracle vulnerabilities in unauthenticated AES-CBC.",
                    "Implement Authenticated Encryption with Associated Data (AEAD) using AES-256-GCM."
                ],
                "content": (
                    "The Advanced Encryption Standard (AES) is a symmetric block cipher that operates on 128-bit (16-byte) blocks using a "
                    "128-, 192-, or 256-bit key. How you chain those 16-byte blocks together determines whether your system is secure:\n\n"
                    "• AES-ECB (Electronic Codebook - BROKEN): Encrypts identical 16-byte plaintext blocks into identical ciphertext blocks. "
                    "Encrypting a bitmap image in ECB mode leaves the outline of the image clearly visible!\n"
                    "• AES-CBC (Cipher Block Chaining - MALLEABLE WITHOUT MAC): Uses an Initialization Vector (IV), but provides zero integrity check. "
                    "Attackers can flip bits in ciphertext block `C[i-1]` to predictably alter plaintext block `P[i]` and exploit PKCS#7 padding oracles.\n"
                    "• AES-256-GCM (Galois/Counter Mode - GOLD STANDARD AEAD): Combines Counter (CTR) mode encryption with a Galois field "
                    "polynomial MAC (GMAC). Every encryption requires a 256-bit key and a unique 96-bit (12-byte) Nonce, producing both ciphertext "
                    "and a 128-bit (16-byte) Authentication Tag. If a single bit of the ciphertext or Associated Data (AAD) is tampered with, "
                    "`AESGCM.decrypt()` raises `InvalidTag` before releasing a single byte of plaintext."
                ),
                "code_sample": (
                    "from cryptography.hazmat.primitives.ciphers.aead import AESGCM\n"
                    "import secrets\n\n"
                    "key = secrets.token_bytes(32)    # 256-bit AES key\n"
                    "nonce = secrets.token_bytes(12)  # 96-bit unique GCM nonce\n"
                    "aad = b'classification:TOP_SECRET'\n\n"
                    "aesgcm = AESGCM(key)\n"
                    "ct_with_tag = aesgcm.encrypt(nonce, b'Launch coordinates: 37.2431 N', aad)\n"
                    "plaintext = aesgcm.decrypt(nonce, ct_with_tag, aad)"
                ),
                "checkpoint_question": "How many bytes (or bits) is the standard recommended Nonce/IV size for AES-256-GCM?",
                "checkpoint_answer": "12",
                "checkpoint_hint": "Enter 12 (for 12 bytes) or 96 (for 96 bits)."
            },
            {
                "id": "acad-201-m3",
                "title": "Lesson 2.3: Password Key Stretching (PBKDF2-HMAC-SHA256 & Cryptographic Salts)",
                "duration": "45 min",
                "objectives": [
                    "Calculate why fast hashes (raw SHA-256/MD5) fail against modern GPU hashcat clusters.",
                    "Use 16-byte CSPRNG salts to defeat Rainbow Tables and identical-password detection.",
                    "Derive 256-bit keys using `hashlib.pbkdf2_hmac` with 200,000+ iterations."
                ],
                "content": (
                    "A single modern consumer GPU (such as an RTX 4090) can compute over 20 BILLION raw SHA-256 hashes per second. "
                    "If a developer stores `sha256(password)` directly in a database, an attacker who steals the database can crack 8-character "
                    "passwords in seconds, and can use precomputed Rainbow Tables to look up millions of hashes instantly.\n\n"
                    "To defend passwords and derive encryption keys from human passphrases, we apply two defenses:\n"
                    "1. Cryptographic Salt (16+ random bytes per user): Stored alongside the hash (`salt$hash`). Because every user has a unique salt, "
                    "two users with the same password produce completely different hashes, and precomputed Rainbow Tables become 100% useless.\n"
                    "2. Key Stretching (`PBKDF2-HMAC-SHA256`, `scrypt`, or `Argon2id`): Forces the CPU/GPU to iterate the HMAC-SHA256 function "
                    "150,000 to 600,000 times per guess. A 50-millisecond delay is imperceptible to a legitimate user logging in, but reduces an "
                    "attacker's brute-force speed by a factor of 200,000x!"
                ),
                "code_sample": (
                    "import hashlib, secrets\n\n"
                    "def derive_vault_key(passphrase: str, salt: bytes | None = None) -> tuple[bytes, bytes]:\n"
                    "    if salt is None:\n"
                    "        salt = secrets.token_bytes(16)  # 128-bit unique CSPRNG salt\n"
                    "    key = hashlib.pbkdf2_hmac(\n"
                    "        hash_name='sha256',\n"
                    "        password=passphrase.encode('utf-8'),\n"
                    "        salt=salt,\n"
                    "        iterations=200_000,\n"
                    "        dklen=32\n"
                    "    )\n"
                    "    return salt, key"
                ),
                "checkpoint_question": "Which Python standard library function in 'hashlib' implements PBKDF2 key stretching?",
                "checkpoint_answer": "PBKDF2_HMAC",
                "checkpoint_hint": "Function name: hashlib._______ (includes underscore)."
            },
            {
                "id": "acad-201-m4",
                "title": "Lesson 2.4: OS CSPRNG ('secrets') vs. Predictable PRNGs ('random')",
                "duration": "35 min",
                "objectives": [
                    "Understand why Mersenne Twister (`import random`) is completely insecure for tokens or keys.",
                    "Generate URL-safe session tokens, hex keys, and salts using Python's `secrets` module."
                ],
                "content": (
                    "One of the most common vulnerabilities in Python web applications is using `random.choice()` or `random.randint()` to "
                    "generate password-reset links, API keys, or 2FA codes.\n\n"
                    "Python's `random` module uses the Mersenne Twister (MT19937) deterministic pseudorandom number generator. Its internal state "
                    "consists of 624 32-bit integers. If an attacker observes 624 sequential outputs from `random`, they can reconstruct the "
                    "entire internal state and predict every past and future 'random' token with 100% accuracy!\n\n"
                    "Instead, always use Python's `secrets` module (or `os.urandom()`), which draws entropy directly from the operating system's "
                    "Cryptographically Secure Pseudorandom Number Generator (CSPRNG: `/dev/urandom` / `getrandom()` on Linux, `BCryptGenRandom` on Windows)."
                ),
                "code_sample": (
                    "import secrets\n\n"
                    "# Generate a 256-bit (32-byte) URL-safe session bearer token:\n"
                    "session_token = secrets.token_urlsafe(32)\n\n"
                    "# Generate a 128-bit hexadecimal salt:\n"
                    "hex_salt = secrets.token_hex(16)"
                ),
                "checkpoint_question": "What is the name of the deterministic algorithm used by Python's insecure 'random' module?",
                "checkpoint_answer": "MERSENNE TWISTER",
                "checkpoint_hint": "Two words: ________ Twister (or MT19937)."
            },
            {
                "id": "acad-201-m5",
                "title": "Lesson 2.5: Timing Side-Channel Attacks & Constant-Time HMAC Verification",
                "duration": "40 min",
                "objectives": [
                    "Explain how byte-by-byte string comparison (`==`) leaks secret MACs via nanosecond response timing.",
                    "Prevent timing side-channels using `hmac.compare_digest(a, b)`."
                ],
                "content": (
                    "Suppose your API verifies a webhook signature or password hash using standard equality: `if user_sig == expected_sig:`.\n"
                    "Standard string comparison checks characters left-to-right and returns `False` on the VERY FIRST mismatched byte! "
                    "By measuring response times over thousands of requests, an attacker can guess the first byte (which takes slightly longer "
                    "to fail because byte 0 matched and Python moved on to check byte 1), then the second byte, and forge a valid signature in "
                    "linear time (`256 * 32` guesses instead of `2^256`)!\n\n"
                    "To eliminate timing side-channels, always use `hmac.compare_digest(a, b)`, which bitwise-compares every single byte of "
                    "both strings in constant time regardless of where the first mismatch occurs."
                ),
                "code_sample": (
                    "import hmac, hashlib\n\n"
                    "def verify_webhook_signature(payload: bytes, header_sig: str, secret: bytes) -> bool:\n"
                    "    computed = hmac.new(secret, payload, hashlib.sha256).hexdigest()\n"
                    "    # Constant-time comparison prevents timing side-channel leakage:\n"
                    "    return hmac.compare_digest(computed, header_sig)"
                ),
                "checkpoint_question": "Which function in Python's 'hmac' module performs a constant-time comparison of two digests?",
                "checkpoint_answer": "COMPARE_DIGEST",
                "checkpoint_hint": "Function name: hmac._____________"
            }
        ],
        "lab": {
            "title": "Interactive Cyber Range Lab: Operation ENIGMA VAULT (Python & Cryptography Workbench)",
            "scenario": (
                "Field operatives recovered an encrypted dead-drop vault (`vault_04.bin`) protected by `PBKDF2-HMAC-SHA256` and `AES-256-GCM`. "
                "Run the Python scripts in the workbench terminal below to inspect the vault parameters, derive the 256-bit key, "
                "and verify/decrypt the GCM payload to capture the Lab Flag (`FLAG{...}`)."
            ),
            "suggested_commands": [
                "help",
                "python3 inspect_vault.py",
                "python3 test_rng.py",
                "python3 derive_key.py --salt 8f4a2c91e0b3 --iter 200000",
                "python3 decrypt_gcm.py --nonce 99a1b2 --tag valid"
            ],
            "flag": "FLAG{AES256_GCM_PBKDF2_CSPRNG}"
        },
        "exam": [
            {
                "q_id": "q1",
                "question": "1. What critical security property does AES-256-GCM provide in addition to confidentiality via its 128-bit GCM Tag?",
                "options": [
                    {"value": "COMPRESSION", "label": "Lossless payload compression"},
                    {"value": "INTEGRITY", "label": "Authenticated integrity / tamper detection (AEAD)"},
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
            },
            {
                "q_id": "q4",
                "question": "4. What happens if a One-Time Pad (OTP) or AES-GCM Nonce/Key stream is reused across two different messages (C1 and C2)?",
                "options": [
                    {"value": "KEY_CANCELS", "label": "XORing C1 ^ C2 cancels out the keystream (P1 ^ P2), destroying confidentiality"},
                    {"value": "DOUBLE_STRENGTH", "label": "Encryption strength doubles to 512 bits"},
                    {"value": "AUTO_ROTATE", "label": "The receiver automatically rotates the DNS record"},
                    {"value": "NO_EFFECT", "label": "There is no security impact"}
                ],
                "answer": "KEY_CANCELS"
            },
            {
                "q_id": "q5",
                "question": "5. Why should you use 'hmac.compare_digest(a, b)' instead of 'a == b' when verifying cryptographic MACs or tokens?",
                "options": [
                    {"value": "TIMING", "label": "It executes in constant time to prevent timing side-channel attacks"},
                    {"value": "UPPERCASE", "label": "It converts strings to uppercase automatically"},
                    {"value": "SQL", "label": "It sanitizes SQL queries"},
                    {"value": "COMPRESSION", "label": "It compresses the digest"}
                ],
                "answer": "TIMING"
            },
            {
                "q_id": "q6",
                "question": "6. Why is Electronic Codebook (AES-ECB) mode unsafe for encrypting multi-block payloads?",
                "options": [
                    {"value": "IDENTICAL_BLOCKS", "label": "Identical 16-byte plaintext blocks produce identical ciphertext blocks, leaking patterns"},
                    {"value": "TOO_SLOW", "label": "It requires 10 million PBKDF2 iterations"},
                    {"value": "ASYMMETRIC", "label": "It publishes the private key in DNS"},
                    {"value": "NO_256", "label": "It only supports 40-bit keys"}
                ],
                "answer": "IDENTICAL_BLOCKS"
            }
        ]
    },

    # =========================================================================
    # TRACK 3: ACAD-301 — SOC THREAT HUNTING, OSINT & COUNTER-PHISHING OPS
    # =========================================================================
    {
        "id": "acad-301",
        "code": "ACAD-301",
        "division": "DIVISION 03 // SOC THREAT HUNTING & COUNTER-INTEL",
        "title": "SOC Threat Hunting, Counter-Phishing & OSINT Reconnaissance",
        "credential_title": "Cyber Counter-Intelligence Operator (CCIO)",
        "ceu_credits": "7.0 CEU Credits (NIST NICE: Analyze & Investigate / Threat Analysis)",
        "xp": 900,
        "summary": (
            "Neutralize zero-click web beacons, dissect IDN Punycode ('xn--') homograph attacks, trace hostile infrastructure "
            "via WHOIS/ASN/BGP reconnaissance, and execute NIST SP 800-61 Computer Security Incident Handling workflows."
        ),
        "modules": [
            {
                "id": "acad-301-m1",
                "title": "Lesson 3.1: Zero-Click Tracking Pixels & Email Sandbox Architecture",
                "duration": "35 min",
                "objectives": [
                    "Identify 1x1 remote tracking pixels, CSS background beacons, and external font callbacks in raw HTML.",
                    "Explain what metadata is leaked when an email client fetches a remote asset.",
                    "Design a Zero-JS, remote-image-blocked HTML sanitization pipeline."
                ],
                "content": (
                    "When an adversary or surveillance marketer sends an HTML email, they frequently embed an invisible 1x1 pixel image "
                    "hosted on a unique URL tied to the recipient's email address:\n"
                    "`<img src=\"https://telemetry.hostile.net/open?target=director_james&id=8812\" width=\"1\" height=\"1\" />`\n\n"
                    "If the recipient's email client automatically loads remote images, the client's device immediately makes an HTTP/HTTPS GET "
                    "request to the attacker's server—leaking:\n"
                    "1. Whether the email account is active and monitored (and the exact second it was opened),\n"
                    "2. The recipient's real public IPv4/IPv6 address and ISP/physical geolocation (unless routed through a proxy),\n"
                    "3. The operating system, rendering engine, and device architecture via the `User-Agent` header.\n\n"
                    "Defense-in-Depth Sanitization: A secure SIGINT mail viewer strips all `<script>`, `<iframe>`, `<object>`, and `on*=` event "
                    "attributes, rewrites remote `src=\"https://...\"` image and CSS `url(...)` references to local placeholders, and requires explicit "
                    "operator authorization before making any external network request."
                ),
                "code_sample": (
                    "# Regex Pattern to Neutralize Remote HTML Image Beacons:\n"
                    "import re\n"
                    " TRACKER_RE = re.compile(r'<img\\b[^>]*\\bsrc=[\"\\']https?://[^\"\\']+[\"\\'][^>]*>', re.IGNORECASE)\n"
                    "sanitized_html = TRACKER_RE.sub('[🛡️ REMOTE TRACKING BEACON BLOCKED]', raw_html)"
                ),
                "checkpoint_question": "Which HTTP request header sent when loading a remote tracking pixel reveals the victim's operating system and browser/client version?",
                "checkpoint_answer": "USER-AGENT",
                "checkpoint_hint": "Hyphenated HTTP header: User-_____"
            },
            {
                "id": "acad-301-m2",
                "title": "Lesson 3.2: IDN Homograph Attacks & Punycode ('xn--') Deconstruction",
                "duration": "45 min",
                "objectives": [
                    "Understand how Unicode lookalike characters (confusables) across Cyrillic, Greek, and Latin scripts work.",
                    "Convert Internationalized Domain Names (IDNs) to ASCII Compatible Encoding (Punycode 'xn--') in Python.",
                    "Detect credential-harvesting domains before clicking links."
                ],
                "content": (
                    "In 1998, researchers demonstrated that Cyrillic small letter `'а'` (`U+0430`) is pixel-for-pixel identical in most fonts "
                    "to Latin small letter `'a'` (`U+0061`). An attacker can register a domain using Cyrillic `'а'` so that the browser address bar "
                    "or email link visually displays `https://аpple.com` or `https://microsоft.com`.\n\n"
                    "Because the Domain Name System (DNS) historically only understood 7-bit ASCII characters, RFC 3492 introduced **Punycode** "
                    "(ASCII Compatible Encoding). Any domain label containing non-ASCII Unicode characters is translated into an ASCII string "
                    "prefixed with **`xn--`**:\n"
                    "• Visual Unicode: `аpple.com` (Cyrillic `U+0430`)\n"
                    "• Actual DNS Punycode: `xn--pple-43d.com`\n\n"
                    "Security tools must always decode and display the underlying `xn--` Punycode hostname AND flag mixed-script domain labels."
                ),
                "code_sample": (
                    "# Python IDNA / Punycode Inspection:\n"
                    "spoofed_domain = '\\u0430pple.com'  # Starts with Cyrillic small 'a' (U+0430)\n"
                    "ascii_punycode = spoofed_domain.encode('idna').decode('ascii')\n"
                    "print(ascii_punycode)  # Outputs: xn--pple-43d.com"
                ),
                "checkpoint_question": "What 4-character ASCII prefix is used by DNS (RFC 3492) to encode Internationalized Domain Names in Punycode?",
                "checkpoint_answer": "XN--",
                "checkpoint_hint": "Two letters followed by two hyphens: __--"
            },
            {
                "id": "acad-301-m3",
                "title": "Lesson 3.3: OSINT Infrastructure Recon (WHOIS, ASN, BGP & Passive DNS)",
                "duration": "40 min",
                "objectives": [
                    "Pivot from an attacker's IPv4 address to their Autonomous System Number (ASN) and netblock owner.",
                    "Use Certificate Transparency (CT) logs (`crt.sh`) to discover hidden subdomains.",
                    "Evaluate domain age and registrar reputation during threat triage."
                ],
                "content": (
                    "When a SOC analyst extracts a suspicious IP address or domain from a phishing header or firewall log, the next step is "
                    "Open-Source Intelligence (OSINT) infrastructure profiling—without alerting the adversary's server:\n\n"
                    "1. Passive DNS & Certificate Transparency (CT): Whenever a TLS certificate is issued by Let's Encrypt or DigiCert, it is "
                    "permanently logged in public Certificate Transparency logs. Querying `crt.sh` reveals every subdomain an organization or "
                    "threat actor has ever provisioned.\n"
                    "2. ASN & WHOIS Pivoting: Every public IP block belongs to an Autonomous System Number (e.g., `AS16509` for Amazon AWS, "
                    "`AS13335` for Cloudflare). Checking the ASN, registration date (newly registered domains `< 7 days` old are high-risk), "
                    "and reverse PTR record tells you whether an IP is a legitimate corporate mail server or a bulletproof VPS."
                ),
                "code_sample": (
                    "# Query Autonomous System (ASN) & Netblock via WHOIS:\n"
                    "$ whois 198.51.100.214\n"
                    "NetRange:       198.51.100.0 - 198.51.100.255\n"
                    "CIDR:           198.51.100.0/24\n"
                    "OriginAS:       AS64512 (ROGUE-BULLETPROOF-HOSTING)\n"
                    "RegDate:        2026-10-14"
                ),
                "checkpoint_question": "What public cryptographic log system records every SSL/TLS certificate issued by public Certificate Authorities, allowing analysts to discover subdomains?",
                "checkpoint_answer": "CERTIFICATE TRANSPARENCY",
                "checkpoint_hint": "Two words (often abbreviated CT): Certificate ____________"
            },
            {
                "id": "acad-301-m4",
                "title": "Lesson 3.4: Indicators of Compromise (IoCs) & Pyramid of Pain",
                "duration": "35 min",
                "objectives": [
                    "Classify atomic, computed, and behavioral Indicators of Compromise (IoCs).",
                    "Apply David Bianco's 'Pyramid of Pain' (Hash Values -> IPs -> Domains -> Tools -> TTPs)."
                ],
                "content": (
                    "In threat intelligence, not all Indicators of Compromise (IoCs) are equally valuable. David Bianco's **Pyramid of Pain** "
                    "ranks indicators by how much cost and friction you inflict on an adversary when you block them:\n\n"
                    "• Level 1 — Hash Values (`SHA-256` of a malware binary): Trivial for attackers to bypass (changing 1 byte changes the hash).\n"
                    "• Level 2 — IP Addresses: Easy for attackers to rotate via cloud proxies.\n"
                    "• Level 3 — Domain Names: Simple to register new domains, though slightly more expensive.\n"
                    "• Level 4 — Network/Host Artifacts (Custom User-Agent strings, C2 URI patterns, registry keys).\n"
                    "• Level 5 — Tools (Cobalt Strike signatures, custom crypters).\n"
                    "• Level 6 (Apex) — TTPs (Tactics, Techniques, and Procedures mapped in MITRE ATT&CK): When you detect how an adversary "
                    "behaves (e.g., PowerShell encoded child process spawned by Outlook), they must reinvent their entire tradecraft!"
                ),
                "code_sample": (
                    "# MITRE ATT&CK Mapping Example:\n"
                    "Tactic    : Initial Access (TA0001)\n"
                    "Technique : Phishing: Spearphishing Link (T1566.002)\n"
                    "Defense   : Punycode Link Guard + Hardware FIDO2/WebAuthn MFA"
                ),
                "checkpoint_question": "At the top (apex) of the Pyramid of Pain, what does the acronym 'TTPs' stand for?",
                "checkpoint_answer": "TACTICS, TECHNIQUES, AND PROCEDURES",
                "checkpoint_hint": "Tactics, Techniques, and Procedures"
            },
            {
                "id": "acad-301-m5",
                "title": "Lesson 3.5: NIST SP 800-61 Incident Response Lifecycle",
                "duration": "45 min",
                "objectives": [
                    "Execute the 4 phases of NIST SP 800-61 Rev. 2/3 Incident Response.",
                    "Preserve volatile memory and forensic chain-of-custody during Containment."
                ],
                "content": (
                    "When an intrusion or credential compromise is confirmed, chaotic ad-hoc reactions destroy forensic evidence and leave backdoors "
                    "behind. NIST Special Publication 800-61 defines the four mandatory phases of professional Incident Response:\n\n"
                    "1. Preparation: Hardening endpoints, deploying centralized logging (SIEM/EDR), establishing communication out-of-band channels.\n"
                    "2. Detection & Analysis: Triaging alerts, correlating IoCs, determining scope and timeline of compromise.\n"
                    "3. Containment, Eradication & Recovery:\n"
                    "   • Short-term Containment: Isolating the affected host's network VLAN (without powering it off, so RAM forensics can be captured) "
                    "and blocking hostile C2 domains at the DNS/firewall sinkhole.\n"
                    "   • Eradication: Revoking compromised session tokens, rotating credentials, removing persistence mechanisms.\n"
                    "   • Recovery: Restoring from verified clean backups and monitoring closely.\n"
                    "4. Post-Incident Activity: Conducting a blameless 'Lessons Learned' review and updating detection rules."
                ),
                "code_sample": (
                    "# Incident Containment Playbook Commands:\n"
                    "1. Isolate endpoint VLAN:  contain-host --isolate 10.20.4.88\n"
                    "2. Sinkhole C2 domain:     contain-host --block-ioc xn--pple-43d.com\n"
                    "3. Revoke active tokens:   UPDATE agents SET session_token = '' WHERE callsign = 'compromised_user';"
                ),
                "checkpoint_question": "During short-term Containment of a compromised server, why should you isolate its network interface BEFORE powering it off?",
                "checkpoint_answer": "RAM",
                "checkpoint_hint": "Three letters: powering off wipes volatile memory (___)."
            }
        ],
        "lab": {
            "title": "Interactive Cyber Range Lab: Operation GLASS PIXEL (SOC Threat Hunting & OSINT Terminal)",
            "scenario": (
                "An executive on workstation `10.20.4.88` received a suspicious HTML dispatch (`/cases/spearphish_ceo.html`). "
                "Use the SOC terminal below to analyze the HTML for tracking beacons, decode the Punycode link (`punycode-decode`), "
                "run `whois` on the attacker's IP, and execute the containment command (`contain-host`) to capture the Lab Flag (`FLAG{...}`)."
            ),
            "suggested_commands": [
                "help",
                "analyze-html /cases/spearphish_ceo.html",
                "punycode-decode https://xn--pple-43d.com/sso",
                "whois 198.51.100.214",
                "contain-host --isolate 10.20.4.88 --block-ioc xn--pple-43d.com"
            ],
            "flag": "FLAG{SOC_PUNYCODE_CONTAINED_800_61}"
        },
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
            },
            {
                "q_id": "q4",
                "question": "4. According to the Pyramid of Pain, which indicator type is the MOST painful for an adversary to change once detected?",
                "options": [
                    {"value": "TTPS", "label": "TTPs (Tactics, Techniques, and Procedures)"},
                    {"value": "HASHES", "label": "MD5/SHA-256 file hashes"},
                    {"value": "IPS", "label": "IPv4 addresses"},
                    {"value": "DOMAINS", "label": "Domain names"}
                ],
                "answer": "TTPS"
            },
            {
                "q_id": "q5",
                "question": "5. Which authentication technology completely neutralizes credential harvesting on Punycode lookalike domains because it cryptographically binds to the real origin domain?",
                "options": [
                    {"value": "FIDO2", "label": "FIDO2 / WebAuthn Hardware Security Keys (Passkeys)"},
                    {"value": "SMS_OTP", "label": "SMS 6-digit text codes"},
                    {"value": "SECURITY_Q", "label": "Mother's maiden name security questions"},
                    {"value": "CAPTCHA", "label": "Image CAPTCHAs"}
                ],
                "answer": "FIDO2"
            },
            {
                "q_id": "q6",
                "question": "6. Which public log ecosystem can OSINT analysts query (e.g., via crt.sh) to enumerate all TLS certificates ever issued for a target domain?",
                "options": [
                    {"value": "CT_LOGS", "label": "Certificate Transparency (CT) Logs"},
                    {"value": "ARP_CACHE", "label": "Local ARP Cache"},
                    {"value": "DHCP_LEASE", "label": "Home Router DHCP Table"},
                    {"value": "CRONTAB", "label": "Linux Crontab"}
                ],
                "answer": "CT_LOGS"
            }
        ]
    },

    # =========================================================================
    # TRACK 4: ACAD-401 — LINUX HARDENING, SQL INJECTION & ZERO-TRUST APIS
    # =========================================================================
    {
        "id": "acad-401",
        "code": "ACAD-401",
        "division": "DIVISION 04 // SECURE INFRASTRUCTURE & SYSTEMS",
        "title": "Linux Hardening, SQL Injection Defense & Zero-Trust API Engineering",
        "credential_title": "Directorate Security & Infrastructure Engineer (DSIE)",
        "ceu_credits": "9.0 CEU Credits (NIST NICE: Operate, Maintain & Securely Provision)",
        "xp": 1200,
        "summary": (
            "Harden Linux production servers, master POSIX octal permissions and systemd sandboxing, eliminate SQL Injection (SQLi) "
            "via parameterized queries, and deploy HTTP Strict-Transport-Security (HSTS) and Content-Security-Policy (CSP)."
        ),
        "modules": [
            {
                "id": "acad-401-m1",
                "title": "Lesson 4.1: Eliminating SQL Injection (SQLi) with Parameterized Queries",
                "duration": "45 min",
                "objectives": [
                    "Trace how string concatenation (`f\"SELECT ... '{user}'\"`) allows boolean-based and UNION-based SQL Injection.",
                    "Refactor vulnerable Python `sqlite3` / `psycopg2` queries to use bound parameter placeholders (`?` or `%s`)."
                ],
                "content": (
                    "SQL Injection (SQLi, OWASP A03:2021 Injection) remains one of the most devastating vulnerabilities in software history. "
                    "It occurs whenever untrusted user input is concatenated directly into a SQL command string:\n"
                    "`query = f\"SELECT * FROM agents WHERE callsign = '{user_input}' AND password_hash = '{pw_hash}'\"`\n\n"
                    "If an attacker submits `james.f' --` as their username, the `--` SQL comment operator comments out the entire password check! "
                    "The database executes:\n"
                    "`SELECT * FROM agents WHERE callsign = 'james.f' -- AND password_hash = '...'`\n"
                    "—logging the attacker directly into the Director's account without knowing the password!\n\n"
                    "The Cure — Parameterized Queries (Prepared Statements):\n"
                    "When you use a `?` placeholder (`cursor.execute(\"SELECT * FROM agents WHERE callsign = ?\", (user_input,))`), the database "
                    "compiles the SQL syntax tree FIRST and treats the parameter strictly as a literal scalar value—never executable SQL code."
                ),
                "code_sample": (
                    "# VULNERABLE CODE (Allows ' OR 1=1 -- authentication bypass):\n"
                    "# row = conn.execute(f\"SELECT * FROM agents WHERE callsign = '{callsign}'\").fetchone()\n\n"
                    "# SECURE CODE (Parameterized Query — 100% Immune to SQLi):\n"
                    "row = conn.execute(\"SELECT * FROM agents WHERE callsign = ?\", (callsign,)).fetchone()"
                ),
                "checkpoint_question": "What single character is used as the bound parameter placeholder in Python's standard 'sqlite3' module?",
                "checkpoint_answer": "?",
                "checkpoint_hint": "A single punctuation mark: _"
            },
            {
                "id": "acad-401-m2",
                "title": "Lesson 4.2: Linux POSIX File Permissions, Octal Modes & SSH Hardening",
                "duration": "40 min",
                "objectives": [
                    "Calculate 3-digit octal permission modes (`4=read`, `2=write`, `1=execute`) across Owner, Group, and Others.",
                    "Secure SSH private keys (`chmod 400` / `600`) and disable root password authentication in `sshd_config`."
                ],
                "content": (
                    "Every file and directory on a Linux system has three permission sets: **Owner (User)**, **Group**, and **Others (World)**. "
                    "Each set is represented by a 3-bit octal digit:\n"
                    "• `4` = Read (`r`)\n"
                    "• `2` = Write (`w`)\n"
                    "• `1` = Execute (`x`)\n"
                    "• `0` = No permission (`-`)\n\n"
                    "Common Security Permission Modes:\n"
                    "• `chmod 777` (`rwxrwxrwx` — CRITICAL VULNERABILITY): Anyone on the system can read, modify, or execute the file.\n"
                    "• `chmod 755` (`rwxr-xr-x`): Standard for public executable binaries and directories.\n"
                    "• `chmod 600` (`rw-------`): Owner read/write only (used for `.env` secrets and `authorized_keys`).\n"
                    "• `chmod 400` (`r--------`): Owner read-only, zero access for group or world. OpenSSH (`ssh -i key.pem`) will outright "
                    "REFUSE to connect with `WARNING: UNPROTECTED PRIVATE KEY FILE!` if a private key is readable by group/others!"
                ),
                "code_sample": (
                    "# Lock down an SSH private key and ~/.ssh directory on Linux:\n"
                    "$ chmod 700 ~/.ssh\n"
                    "$ chmod 400 ~/.ssh/id_ed25519\n"
                    "$ ls -l ~/.ssh/id_ed25519\n"
                    "-r-------- 1 operative operative 411 Oct 17 22:00 /home/operative/.ssh/id_ed25519"
                ),
                "checkpoint_question": "In Linux octal notation, what 3-digit mode gives the Owner Read+Write (4+2) and gives Group and Others zero permissions?",
                "checkpoint_answer": "600",
                "checkpoint_hint": "Three digits: (4+2) followed by 0 and 0."
            },
            {
                "id": "acad-401-m3",
                "title": "Lesson 4.3: Linux systemd Service Isolation & Principle of Least Privilege",
                "duration": "40 min",
                "objectives": [
                    "Run production web services under unprivileged accounts instead of `root`.",
                    "Apply `systemd` sandboxing directives (`NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`)."
                ],
                "content": (
                    "Never run a public-facing web application or Python API server as `User=root`. If an attacker discovers a Remote Code "
                    "Execution (RCE) or path-traversal bug in a root process, they immediately own the entire kernel and filesystem.\n\n"
                    "With `systemd`, you can lock a service inside a strict least-privilege sandbox using built-in Linux kernel namespaces:\n"
                    "• `User=www-data` (or `bitnami` / dedicated service user): Drops root privileges.\n"
                    "• `NoNewPrivileges=true`: Prevents the process or its children from ever gaining new privileges via `setuid` binaries (`sudo`/`su`).\n"
                    "• `ProtectSystem=strict`: Mounts `/usr`, `/boot`, and `/etc` as read-only inside the service's filesystem namespace.\n"
                    "• `PrivateTmp=true`: Isolates `/tmp` so other local users cannot perform symlink race attacks."
                ),
                "code_sample": (
                    "# Hardened /etc/systemd/system/agency-portal.service:\n"
                    "[Service]\n"
                    "Type=simple\n"
                    "User=bitnami\n"
                    "NoNewPrivileges=true\n"
                    "PrivateTmp=true\n"
                    "ProtectHome=read-only\n"
                    "ExecStart=/usr/bin/python3 /home/bitnami/agency_portal/server.py"
                ),
                "checkpoint_question": "Which systemd [Service] directive prevents a process and its children from escalating privileges via setuid binaries?",
                "checkpoint_answer": "NONEWPRIVILEGES",
                "checkpoint_hint": "One word (Directive name before '=true'): NoNew__________"
            },
            {
                "id": "acad-401-m4",
                "title": "Lesson 4.4: Transport & Browser Hardening (HSTS, CSP & X-Frame-Options)",
                "duration": "45 min",
                "objectives": [
                    "Prevent SSL-stripping on first visit using `Strict-Transport-Security` (HSTS).",
                    "Mitigate Cross-Site Scripting (XSS) and Clickjacking with `Content-Security-Policy` and `X-Frame-Options`."
                ],
                "content": (
                    "Even if your Apache or Nginx server redirects HTTP (Port 80) to HTTPS (Port 443), a user who types `theintelligenceagency.net` "
                    "into their browser makes their VERY FIRST request over unencrypted HTTP. An attacker on the local network can intercept "
                    "that initial HTTP request (`sslstrip`) and prevent the HTTPS redirect from ever happening.\n\n"
                    "Essential HTTP Security Response Headers:\n"
                    "1. `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (HSTS): Tells the browser to cache a mandatory "
                    "rule for 2 years: NEVER connect to this domain over plaintext HTTP again—automatically rewrite all `http://` links to `https://` internally.\n"
                    "2. `Content-Security-Policy` (CSP): Restricts where scripts, styles, and frames can be loaded from, stopping Cross-Site Scripting (XSS).\n"
                    "3. `X-Content-Type-Options: nosniff`: Prevents browsers from MIME-sniffing a text/image upload into executable JavaScript.\n"
                    "4. `X-Frame-Options: DENY`: Prevents malicious sites from embedding your login page inside an invisible `<iframe>` (Clickjacking)."
                ),
                "code_sample": (
                    "# Production Security Headers:\n"
                    "Strict-Transport-Security: max-age=63072000; includeSubDomains; preload\n"
                    "X-Content-Type-Options: nosniff\n"
                    "X-Frame-Options: DENY\n"
                    "Content-Security-Policy: default-src 'self'; frame-ancestors 'none';"
                ),
                "checkpoint_question": "What value for the 'X-Content-Type-Options' header prevents browsers from MIME-sniffing non-script files into executable code?",
                "checkpoint_answer": "NOSNIFF",
                "checkpoint_hint": "One word: no_____"
            },
            {
                "id": "acad-401-m5",
                "title": "Lesson 4.5: Zero-Trust API Authentication, Rate Limiting & SQLite WAL Concurrency",
                "duration": "40 min",
                "objectives": [
                    "Authenticate stateless API requests using `Authorization: Bearer <256-bit-CSPRNG-token>`.",
                    "Enable Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) in SQLite for concurrent multi-threaded reads and writes."
                ],
                "content": (
                    "In a Zero-Trust API architecture, every endpoint that accesses or mutates operative data must verify a high-entropy bearer token "
                    "on every single request—never trusting client-side cookies or hidden form fields for user identity.\n\n"
                    "Database Concurrency & Resilience:\n"
                    "By default, SQLite uses a rollback journal that locks the entire database file during writes. Enabling Write-Ahead Logging "
                    "(`PRAGMA journal_mode=WAL;`) allows multiple threads to read from the database simultaneously while a write transaction is "
                    "appended to the `-wal` file, dramatically improving throughput and preventing `database is locked` errors under load."
                ),
                "code_sample": (
                    "def get_db() -> sqlite3.Connection:\n"
                    "    conn = sqlite3.connect(DB_PATH, timeout=10.0)\n"
                    "    conn.row_factory = sqlite3.Row\n"
                    "    conn.execute('PRAGMA journal_mode=WAL;')\n"
                    "    conn.execute('PRAGMA foreign_keys=ON;')\n"
                    "    return conn"
                ),
                "checkpoint_question": "Which 3-letter SQLite journal_mode enables concurrent readers alongside a writer?",
                "checkpoint_answer": "WAL",
                "checkpoint_hint": "Three letters: Write-Ahead Logging."
            }
        ],
        "lab": {
            "title": "Interactive Cyber Range Lab: Operation IRON BASTION (Linux, SQLi & Zero-Trust Audit Shell)",
            "scenario": (
                "You have been deployed to audit a staging server before it goes live. Use the interactive root/audit terminal below to "
                "inspect and fix an unprotected SSH private key (`ls -la`, `chmod 400`), audit and patch a SQL Injection vulnerability "
                "(`audit-sql`, `patch-sql`), and verify the HTTPS security headers (`curl -I`) to capture the Lab Flag (`FLAG{...}`)."
            ),
            "suggested_commands": [
                "help",
                "ls -la /etc/agency/keys/",
                "chmod 400 /etc/agency/keys/id_ed25519",
                "audit-sql /opt/portal/auth_query.py",
                "patch-sql --parameterize /opt/portal/auth_query.py",
                "curl -I https://theintelligenceagency.net"
            ],
            "flag": "FLAG{ZERO_TRUST_SQL_PARAM_CHMOD400}"
        },
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
                "question": "2. Which Linux octal permission mode restricts an SSH private key file to read-only for its owner and zero permissions for group/others?",
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
            },
            {
                "q_id": "q4",
                "question": "4. Why does an input like \"admin' --\" bypass authentication in an unparameterized SQL string query?",
                "options": [
                    {"value": "COMMENT_OUT", "label": "The single quote closes the string literal and '--' comments out the remainder of the WHERE clause"},
                    {"value": "BUFFER_OVERFLOW", "label": "It overwrites the CPU instruction pointer"},
                    {"value": "DNS_SPOOF", "label": "It redirects the DNS MX record"},
                    {"value": "TLS_DOWNGRADE", "label": "It forces TLS 1.0"}
                ],
                "answer": "COMMENT_OUT"
            },
            {
                "q_id": "q5",
                "question": "5. Which HTTP response header prevents 'Clickjacking' attacks by forbidding external websites from embedding your page inside an <iframe>?",
                "options": [
                    {"value": "X_FRAME", "label": "X-Frame-Options: DENY (or CSP frame-ancestors 'none')"},
                    {"value": "SERVER", "label": "Server: Apache"},
                    {"value": "ETAG", "label": "ETag"},
                    {"value": "VARY", "label": "Vary: Accept-Encoding"}
                ],
                "answer": "X_FRAME"
            },
            {
                "q_id": "q6",
                "question": "6. Which SQLite PRAGMA journal mode enables concurrent read operations while a write transaction is being appended?",
                "options": [
                    {"value": "WAL", "label": "PRAGMA journal_mode=WAL; (Write-Ahead Logging)"},
                    {"value": "OFF", "label": "PRAGMA journal_mode=OFF;"},
                    {"value": "DROP", "label": "PRAGMA journal_mode=DROP;"},
                    {"value": "CSV", "label": "PRAGMA journal_mode=CSV;"}
                ],
                "answer": "WAL"
            }
        ]
    }
]


# Ensure every module has an explicit lesson_id
for _c in ACADEMY_COURSES:
    for _idx, _m in enumerate(_c.get("modules", []), start=1):
        if not _m.get("lesson_id"):
            _m["lesson_id"] = f"{_c['id']}-m{_idx}"



def execute_lab_command(course_id: str, raw_cmd: str) -> dict:
    """
    Executes a simulated Cyber Range CLI command for the specified Academy course
    and returns realistic terminal output.
    """
    cmd = " ".join(raw_cmd.strip().split())
    cmd_lower = cmd.lower()
    cid = course_id.lower()

    # -------------------------------------------------------------------------
    # TRACK 1 LAB: ACAD-101 (DNS, TLS & SMTP Header Forensics)
    # -------------------------------------------------------------------------
    if cid == "acad-101":
        if cmd_lower in ("help", "?"):
            return {
                "output": (
                    "SIGINT NETWORK & EMAIL FORENSICS LAB (ACAD-101)\n"
                    "Available commands:\n"
                    "  dig TXT theintelligenceagency.net\n"
                    "  dig TXT _dmarc.theintelligenceagency.net\n"
                    "  openssl s_client -connect email-smtp.us-east-1.amazonaws.com:465\n"
                    "  inspect-headers /var/spool/mail/intercept_09.eml\n"
                )
            }
        if "dig" in cmd_lower and "_dmarc" in cmd_lower:
            return {
                "output": (
                    "; <<>> DiG 9.18.24 <<>> TXT _dmarc.theintelligenceagency.net\n"
                    ";; ANSWER SECTION:\n"
                    "_dmarc.theintelligenceagency.net. 300 IN TXT \"v=DMARC1; p=quarantine; rua=mailto:postmaster@theintelligenceagency.net\"\n"
                    ";; Query time: 12 msec // VERDICT: DMARC Enforcement ACTIVE (p=quarantine)"
                )
            }
        if "dig" in cmd_lower and "theintelligenceagency.net" in cmd_lower:
            return {
                "output": (
                    "; <<>> DiG 9.18.24 <<>> TXT theintelligenceagency.net\n"
                    ";; ANSWER SECTION:\n"
                    "theintelligenceagency.net. 300 IN TXT \"v=spf1 include:amazonses.com ~all\"\n"
                    ";; Query time: 9 msec // VERDICT: Authorized Outbound MTA = Amazon SES"
                )
            }
        if "openssl" in cmd_lower and "465" in cmd_lower:
            return {
                "output": (
                    "CONNECTED(00000003)\n"
                    "depth=2 C = US, O = Amazon, CN = Amazon Root CA 1\n"
                    "verify return:1\n"
                    "---\n"
                    "SSL-Session:\n"
                    "    Protocol  : TLSv1.3\n"
                    "    Cipher    : TLS_AES_256_GCM_SHA384\n"
                    "    Server public key is 2048 bit (ECDHE-X25519 Forward Secrecy)\n"
                    "220 email-smtp.amazonaws.com ESMTP SimpleEmailService"
                )
            }
        if "inspect-headers" in cmd_lower or "intercept_09" in cmd_lower:
            return {
                "output": (
                    "=== RAW HEADER DUMP: /var/spool/mail/intercept_09.eml ===\n"
                    "Return-Path: <bounce@spoof-relay.example>\n"
                    "Received: from mx.theintelligenceagency.net (10.0.4.12) by vault.internal (Implicit TLSv1.3 Port 465);\n"
                    "Received: from unknown (HELOtheintelligenceagency.net) ([198.51.100.77]) by mx.theintelligenceagency.net;\n"
                    "Authentication-Results: mx.theintelligenceagency.net;\n"
                    "    spf=fail (sender IP is 198.51.100.77) smtp.mailfrom=theintelligenceagency.net;\n"
                    "    dkim=pass (2048-bit RSA key verified);\n"
                    "    dmarc=pass policy.published-domain-policy=quarantine\n"
                    "X-Directorate-Lab-Flag: FLAG{RFC8314_DKIM_VERIFIED_465}\n"
                    "=========================================================\n"
                    "[+] LAB FLAG CAPTURED: Copy FLAG{RFC8314_DKIM_VERIFIED_465} into the Certification Exam below!"
                )
            }

    # -------------------------------------------------------------------------
    # TRACK 2 LAB: ACAD-201 (Python Cryptography & Key Derivation)
    # -------------------------------------------------------------------------
    elif cid == "acad-201":
        if cmd_lower in ("help", "?"):
            return {
                "output": (
                    "PYTHON CRYPTOGRAPHY & KEY DERIVATION WORKBENCH (ACAD-201)\n"
                    "Available commands:\n"
                    "  python3 inspect_vault.py\n"
                    "  python3 test_rng.py\n"
                    "  python3 derive_key.py --salt 8f4a2c91e0b3 --iter 200000\n"
                    "  python3 decrypt_gcm.py --nonce 99a1b2 --tag valid\n"
                )
            }
        if "inspect_vault" in cmd_lower:
            return {
                "output": (
                    "[*] Inspecting dead-drop container: vault_04.bin\n"
                    "    Cipher Algorithm : AES-256-GCM (AEAD)\n"
                    "    KDF Algorithm    : PBKDF2-HMAC-SHA256\n"
                    "    Salt (Hex)       : 8f4a2c91e0b3\n"
                    "    Iterations       : 200000\n"
                    "    GCM Nonce (96b)  : 99a1b2004f8c112233445566\n"
                    "    Next Step        : Run 'python3 derive_key.py --salt 8f4a2c91e0b3 --iter 200000'"
                )
            }
        if "test_rng" in cmd_lower:
            return {
                "output": (
                    "[!] Auditing PRNG vs OS CSPRNG:\n"
                    "    random.Random()      -> MT19937 (624-word state: PREDICTABLE / INSECURE)\n"
                    "    secrets.token_hex(16)-> OS CSPRNG (/dev/urandom: 128-bit CRYPTOGRAPHIC ENTROPY OK)"
                )
            }
        if "derive_key" in cmd_lower:
            return {
                "output": (
                    "[*] Executing hashlib.pbkdf2_hmac('sha256', passphrase, bytes.fromhex('8f4a2c91e0b3'), 200000)...\n"
                    "[+] Derived 256-bit AES Key: 7c91e4f80012a9b4c5d6e7f890123456789abcdef0123456789abcdef0123456\n"
                    "[*] Next Step: Run 'python3 decrypt_gcm.py --nonce 99a1b2 --tag valid'"
                )
            }
        if "decrypt_gcm" in cmd_lower:
            return {
                "output": (
                    "[*] Initializing AESGCM(derived_key_32_bytes)...\n"
                    "[*] Verifying 128-bit Galois Message Authentication Tag via hmac.compare_digest()...\n"
                    "[+] GCM AUTHENTICATION TAG VERIFIED (INTEGRITY INTACT)\n"
                    "[+] DECRYPTED PAYLOAD: FLAG{AES256_GCM_PBKDF2_CSPRNG}\n"
                    "=========================================================\n"
                    "[+] LAB FLAG CAPTURED: Copy FLAG{AES256_GCM_PBKDF2_CSPRNG} into the Certification Exam below!"
                )
            }

    # -------------------------------------------------------------------------
    # TRACK 3 LAB: ACAD-301 (SOC Threat Hunting, Punycode & Containment)
    # -------------------------------------------------------------------------
    elif cid == "acad-301":
        if cmd_lower in ("help", "?"):
            return {
                "output": (
                    "SOC THREAT HUNTING & INCIDENT RESPONSE TERMINAL (ACAD-301)\n"
                    "Available commands:\n"
                    "  analyze-html /cases/spearphish_ceo.html\n"
                    "  punycode-decode https://xn--pple-43d.com/sso\n"
                    "  whois 198.51.100.214\n"
                    "  contain-host --isolate 10.20.4.88 --block-ioc xn--pple-43d.com\n"
                )
            }
        if "analyze-html" in cmd_lower or "spearphish_ceo" in cmd_lower:
            return {
                "output": (
                    "[*] Scanning /cases/spearphish_ceo.html in Zero-JS Sandbox...\n"
                    "[!] ALERT 1 (Tracking Pixel): <img src=\"http://198.51.100.214/pixel.gif?uid=ceo\" width=\"1\" height=\"1\">\n"
                    "[!] ALERT 2 (IDN Homograph Link): <a href=\"https://xn--pple-43d.com/sso\">Urgent SSO Login</a>\n"
                    "[*] Next Step: Decode the Punycode domain with 'punycode-decode https://xn--pple-43d.com/sso'"
                )
            }
        if "punycode-decode" in cmd_lower or "xn--" in cmd_lower and "contain-host" not in cmd_lower:
            return {
                "output": (
                    "[*] RFC 3492 Punycode Decoder:\n"
                    "    ASCII Input     : xn--pple-43d.com\n"
                    "    Unicode Output  : \\u0430pple.com\n"
                    "    Forensic Detail : Character 0 is CYRILLIC SMALL LETTER A (U+0430), spoofing Latin 'a' (U+0061)!"
                )
            }
        if "whois" in cmd_lower:
            return {
                "output": (
                    "[*] Querying ARIN/RIPE WHOIS for 198.51.100.214...\n"
                    "    NetRange : 198.51.100.0/24\n"
                    "    OriginAS : AS64512 (BULLETPROOF-RELAY-LTD)\n"
                    "    RegDate  : 2026-10-15 (Newly Registered Hostile Infrastructure)\n"
                    "[*] Next Step: Execute NIST SP 800-61 Phase 3 Containment:\n"
                    "    contain-host --isolate 10.20.4.88 --block-ioc xn--pple-43d.com"
                )
            }
        if "contain-host" in cmd_lower:
            return {
                "output": (
                    "[*] Executing NIST SP 800-61 Phase 3 Containment Playbook...\n"
                    "    [1/3] VLAN Isolation applied to endpoint 10.20.4.88 (RAM preserved for forensics)\n"
                    "    [2/3] DNS Sinkhole rule added for IoC: xn--pple-43d.com & 198.51.100.214\n"
                    "    [3/3] Active session tokens revoked.\n"
                    "[+] INCIDENT CONTAINED // LAB FLAG: FLAG{SOC_PUNYCODE_CONTAINED_800_61}\n"
                    "=========================================================\n"
                    "[+] Copy FLAG{SOC_PUNYCODE_CONTAINED_800_61} into the Certification Exam below!"
                )
            }

    # -------------------------------------------------------------------------
    # TRACK 4 LAB: ACAD-401 (Linux Permissions, SQLi Patching & HSTS)
    # -------------------------------------------------------------------------
    elif cid == "acad-401":
        if cmd_lower in ("help", "?"):
            return {
                "output": (
                    "LINUX HARDENING & ZERO-TRUST AUDIT SHELL (ACAD-401)\n"
                    "Available commands:\n"
                    "  ls -la /etc/agency/keys/\n"
                    "  chmod 400 /etc/agency/keys/id_ed25519\n"
                    "  audit-sql /opt/portal/auth_query.py\n"
                    "  patch-sql --parameterize /opt/portal/auth_query.py\n"
                    "  curl -I https://theintelligenceagency.net\n"
                )
            }
        if cmd_lower.startswith("ls"):
            return {
                "output": (
                    "total 12\n"
                    "drwxr-xr-x 2 bitnami root    4096 Oct 17 22:00 .\n"
                    "-rw-rw-rw- 1 bitnami bitnami  411 Oct 17 22:00 id_ed25519  <-- [!] CRITICAL: Mode 0666 (World-Readable/Writable!)\n"
                    "[*] Fix permissions with: chmod 400 /etc/agency/keys/id_ed25519"
                )
            }
        if "chmod 400" in cmd_lower or "chmod 600" in cmd_lower:
            return {
                "output": (
                    "[+] Permissions updated: -r-------- (0400) /etc/agency/keys/id_ed25519\n"
                    "[+] OpenSSH key permission check PASSED."
                )
            }
        if "audit-sql" in cmd_lower:
            return {
                "output": (
                    "=== STATIC CODE AUDIT: /opt/portal/auth_query.py ===\n"
                    "Line 14 [CRITICAL SQLi]:\n"
                    "  c.execute(f\"SELECT * FROM agents WHERE callsign = '{user}'\")\n"
                    "  Reason: Direct f-string interpolation allows \"' OR 1=1 --\" injection!\n"
                    "[*] Patch with: patch-sql --parameterize /opt/portal/auth_query.py"
                )
            }
        if "patch-sql" in cmd_lower:
            return {
                "output": (
                    "[*] Refactoring Line 14 to bound parameterized query:\n"
                    "    c.execute(\"SELECT * FROM agents WHERE callsign = ?\", (user,))\n"
                    "[*] Running automated SQLi exploit payload (\"admin' OR 1=1 --\")...\n"
                    "[+] Exploit neutralized! Input treated strictly as scalar literal.\n"
                    "[*] Final Step: Verify HTTPS headers with 'curl -I https://theintelligenceagency.net'"
                )
            }
        if "curl" in cmd_lower:
            return {
                "output": (
                    "HTTP/2 200 OK\n"
                    "server: Apache / Directorate-Gateway\n"
                    "strict-transport-security: max-age=63072000; includeSubDomains; preload\n"
                    "x-content-type-options: nosniff\n"
                    "x-frame-options: DENY\n"
                    "x-directorate-audit-flag: FLAG{ZERO_TRUST_SQL_PARAM_CHMOD400}\n"
                    "=========================================================\n"
                    "[+] LAB FLAG CAPTURED: Copy FLAG{ZERO_TRUST_SQL_PARAM_CHMOD400} into the Certification Exam below!"
                )
            }

    return {
        "output": (
            f"sigint-shell: command not recognized or out of scope: '{cmd}'\n"
            f"Type 'help' or click one of the quick-command buttons above to run a lab diagnostic."
        )
    }
