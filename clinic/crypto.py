import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class CryptoConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class EncryptedPayload:
    version: str
    nonce_b64: str
    ciphertext_b64: str

    def serialize(self) -> str:
        return f"enc:{self.version}:{self.nonce_b64}:{self.ciphertext_b64}"


_PREFIX = "enc:v1:"


def _get_master_key() -> bytes:
    key_b64 = getattr(settings, "AES_MASTER_KEY_B64", "") or os.environ.get("AES_MASTER_KEY_B64", "")
    if not key_b64:
        raise CryptoConfigurationError(
            "AES_MASTER_KEY_B64 is not configured. Set it in .env (base64-encoded 32-byte key)."
        )

    try:
        key = base64.b64decode(key_b64)
    except Exception as exc:  # noqa: BLE001
        raise CryptoConfigurationError("AES_MASTER_KEY_B64 is not valid base64") from exc

    if len(key) not in (16, 24, 32):
        raise CryptoConfigurationError("AES_MASTER_KEY_B64 must decode to 16/24/32 bytes")

    return key


def encrypt_str(plaintext: str, *, aad: bytes = b"ua-clinic") -> str:
    if plaintext is None:
        return None  # type: ignore[return-value]
    if not isinstance(plaintext, str):
        raise TypeError("encrypt_str expects a str")
    if plaintext.startswith(_PREFIX):
        return plaintext

    key = _get_master_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)

    payload = EncryptedPayload(
        version="v1",
        nonce_b64=base64.b64encode(nonce).decode("ascii"),
        ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
    )
    return payload.serialize()


def decrypt_str(value: str, *, aad: bytes = b"ua-clinic") -> str:
    if value is None:
        return None  # type: ignore[return-value]
    if not isinstance(value, str):
        raise TypeError("decrypt_str expects a str")

    if not value.startswith(_PREFIX):
        # Assume plaintext (e.g., legacy/unencrypted data)
        return value

    # enc:v1:<nonce_b64>:<ciphertext_b64>
    parts = value.split(":", 3)
    if len(parts) != 4:
        raise ValueError("Invalid encrypted payload format")

    _enc, version, nonce_b64, ciphertext_b64 = parts
    if version != "v1":
        raise ValueError(f"Unsupported encryption version: {version}")

    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    key = _get_master_key()
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    return plaintext.decode("utf-8")
