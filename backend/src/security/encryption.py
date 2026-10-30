import base64
import os
import logging
import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from src.config import settings

logger = logging.getLogger("crm.security.encryption")

# Argon2id Hasher configured with secure AppSec parameters
# Memory: 64 MiB (65536 KiB), Time: 3 iterations, Parallelism: 4 lanes
_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID
)


def hash_pin_argon2(secret: str) -> str:
    """Hash PIN or password using strict Argon2id algorithm."""
    if not secret:
        raise ValueError("El secreto a cifrar no puede estar vacio.")
    return _hasher.hash(secret)


def verify_pin_argon2(hash_str: str, secret: str) -> bool:
    """Verify PIN or password against stored Argon2id hash."""
    if not hash_str or not secret:
        return False
    try:
        return _hasher.verify(hash_str, secret)
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception as e:
        logger.warning(f"Error al verificar hash Argon2id: {e}")
        return False


def _derive_encryption_key() -> bytes:
    """Derive 256-bit symmetric encryption key from APP_SECRET_KEY using HKDF-SHA256."""
    raw_secret = settings.APP_SECRET_KEY.encode("utf-8")
    salt = b"crm_local_salt_v6_tijuana"
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"crm_tokens_encryption_at_rest"
    )
    return hkdf.derive(raw_secret)


def encrypt_token(plaintext: str) -> str:
    """Encrypt secret token at rest using AES-256-GCM authenticated cipher."""
    if not plaintext:
        return ""
    key = _derive_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Combine nonce (12 bytes) + ciphertext/tag and encode as base64
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt_token(ciphertext_b64: str) -> str:
    """Decrypt secret token encrypted at rest with AES-256-GCM."""
    if not ciphertext_b64:
        return ""
    try:
        raw_combined = base64.b64decode(ciphertext_b64.encode("ascii"))
        if len(raw_combined) < 28:
            # Fallback for plain unencrypted token if stored before encryption
            return ciphertext_b64
        nonce = raw_combined[:12]
        ciphertext = raw_combined[12:]
        key = _derive_encryption_key()
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception:
        # Graceful fallback if token was unencrypted legacy string
        return ciphertext_b64
