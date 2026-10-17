"""
CritMail Security - Hardware/OS-Backed Credential Encryption
Uses Windows DPAPI (Data Protection API) with AES-256-GCM fallback.
Passwords are NEVER saved in plain text.
"""
import base64
import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
from critmail.config import KEYSTORE_PATH

# Windows DPAPI structures
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte))
    ]

def _win32_encrypt(plaintext: str) -> str:
    """Encrypts plaintext using Windows DPAPI (CryptProtectData)."""
    data = plaintext.encode('utf-8')
    data_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.POINTER(ctypes.c_byte)))
    data_out = DATA_BLOB()
    
    # CryptProtectData(pDataIn, szDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
    crypt32 = ctypes.windll.crypt32
    # CRYPTPROTECT_UI_FORBIDDEN = 0x1
    success = crypt32.CryptProtectData(
        ctypes.byref(data_in),
        "CritMail Secret",
        None,
        None,
        None,
        0x1,
        ctypes.byref(data_out)
    )
    if not success:
        raise RuntimeError("CryptProtectData failed with error code: " + str(ctypes.GetLastError()))
    
    buf = (ctypes.c_byte * data_out.cbData)()
    ctypes.memmove(buf, data_out.pbData, data_out.cbData)
    # Free memory allocated by CryptProtectData
    ctypes.windll.kernel32.LocalFree(data_out.pbData)
    
    raw_bytes = bytes(buf)
    return "dpapi:" + base64.b64encode(raw_bytes).decode('ascii')

def _win32_decrypt(ciphertext: str) -> str:
    """Decrypts ciphertext using Windows DPAPI (CryptUnprotectData)."""
    raw_bytes = base64.b64decode(ciphertext[6:])
    data_in = DATA_BLOB(len(raw_bytes), ctypes.cast(ctypes.create_string_buffer(raw_bytes, len(raw_bytes)), ctypes.POINTER(ctypes.c_byte)))
    data_out = DATA_BLOB()
    
    crypt32 = ctypes.windll.crypt32
    success = crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        None,
        None,
        None,
        None,
        0x1,
        ctypes.byref(data_out)
    )
    if not success:
        raise RuntimeError("CryptUnprotectData failed with error code: " + str(ctypes.GetLastError()))
    
    buf = (ctypes.c_byte * data_out.cbData)()
    ctypes.memmove(buf, data_out.pbData, data_out.cbData)
    ctypes.windll.kernel32.LocalFree(data_out.pbData)
    
    return bytes(buf).decode('utf-8')

def _fallback_encrypt(plaintext: str) -> str:
    """AES-256-GCM fallback encryption using cryptography library."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not KEYSTORE_PATH.exists():
        key = AESGCM.generate_key(bit_length=256)
        KEYSTORE_PATH.write_bytes(key)
    else:
        key = KEYSTORE_PATH.read_bytes()
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), b"critmail-auth")
    return "aesgcm:" + base64.b64encode(nonce + ct).decode('ascii')

def _fallback_decrypt(ciphertext: str) -> str:
    """AES-256-GCM fallback decryption."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not KEYSTORE_PATH.exists():
        raise FileNotFoundError("Keystore not found")
    key = KEYSTORE_PATH.read_bytes()
    raw = base64.b64decode(ciphertext[7:])
    nonce = raw[:12]
    ct = raw[12:]
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, b"critmail-auth")
    return pt.decode('utf-8')

def encrypt_secret(plaintext: str) -> str:
    """Safely encrypt secret credential using best available OS encryption."""
    if not plaintext:
        return ""
    if sys.platform == "win32":
        try:
            return _win32_encrypt(plaintext)
        except Exception:
            return _fallback_encrypt(plaintext)
    return _fallback_encrypt(plaintext)

def decrypt_secret(ciphertext: str) -> str:
    """Safely decrypt secret credential."""
    if not ciphertext:
        return ""
    if ciphertext.startswith("dpapi:"):
        return _win32_decrypt(ciphertext)
    elif ciphertext.startswith("aesgcm:"):
        return _fallback_decrypt(ciphertext)
    # Backward compatibility / raw fallback
    return ciphertext


CIPHER_BEGIN = "-----BEGIN TIA CLASSIFIED CIPHER [AES-256-GCM]-----"
CIPHER_END = "-----END TIA CLASSIFIED CIPHER-----"


def has_classified_cipher(text: str) -> bool:
    """Checks if a message body contains an armored TIA Classified Cipher block."""
    return bool(text and CIPHER_BEGIN in text and CIPHER_END in text)


def encrypt_classified_message(plaintext: str, passphrase: str) -> str:
    """
    Encrypts message body into an ASCII-armored AES-256-GCM block derived via PBKDF2-HMAC-SHA256.
    """
    import hashlib
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 120000, dklen=32)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), b"TIA-CLASSIFIED-V1")
    payload = base64.b64encode(salt + nonce + ct).decode("ascii")
    wrapped = "\n".join(payload[i:i + 64] for i in range(0, len(payload), 64))
    return (
        f"[CLASSIFIED TRANSMISSION // EYES ONLY — AES-256-GCM ENCRYPTED]\n"
        f"{CIPHER_BEGIN}\n"
        f"{wrapped}\n"
        f"{CIPHER_END}\n"
        f"[DECRYPT IN CRITMAIL USING AUTHORIZED AGENT PASSPHRASE]"
    )


def decrypt_classified_message(armored_text: str, passphrase: str) -> str:
    """
    Extracts and decrypts an ASCII-armored TIA Classified Cipher block using the passphrase.
    """
    import hashlib
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if CIPHER_BEGIN not in armored_text or CIPHER_END not in armored_text:
        raise ValueError("No valid TIA Classified Cipher block found in message.")

    inner = armored_text.split(CIPHER_BEGIN, 1)[1].split(CIPHER_END, 1)[0]
    b64_clean = "".join(inner.split())
    raw = base64.b64decode(b64_clean)
    if len(raw) < 29:
        raise ValueError("Corrupted cipher payload.")

    salt = raw[:16]
    nonce = raw[16:28]
    ct = raw[28:]
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 120000, dklen=32)
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, b"TIA-CLASSIFIED-V1")
    return pt.decode("utf-8")
