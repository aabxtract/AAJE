import base64
import json
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.config import settings


TAG_LENGTH = 16


class FlowCryptoError(ValueError):
    pass


def _private_key_bytes() -> bytes:
    if settings.meta_flow_private_key:
        return settings.meta_flow_private_key.replace("\\n", "\n").encode("utf-8")
    if settings.meta_flow_private_key_path:
        return Path(settings.meta_flow_private_key_path).read_bytes()
    raise FlowCryptoError("Meta Flow private key is not configured")


def _private_key_password() -> bytes | None:
    if not settings.meta_flow_private_key_passphrase:
        return None
    return settings.meta_flow_private_key_passphrase.encode("utf-8")


def decrypt_flow_request(body: dict) -> tuple[dict, bytes, bytes]:
    try:
        encrypted_aes_key = base64.b64decode(body["encrypted_aes_key"])
        encrypted_flow_data = base64.b64decode(body["encrypted_flow_data"])
        initial_vector = base64.b64decode(body["initial_vector"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FlowCryptoError("Invalid encrypted Flow request body") from exc

    try:
        private_key = serialization.load_pem_private_key(
            _private_key_bytes(),
            password=_private_key_password(),
        )
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise FlowCryptoError("Could not decrypt Flow AES key") from exc

    encrypted_body = encrypted_flow_data[:-TAG_LENGTH]
    auth_tag = encrypted_flow_data[-TAG_LENGTH:]
    try:
        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(initial_vector, auth_tag),
        ).decryptor()
        decrypted = decryptor.update(encrypted_body) + decryptor.finalize()
        return json.loads(decrypted.decode("utf-8")), aes_key, initial_vector
    except (InvalidTag, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FlowCryptoError("Could not decrypt Flow data") from exc


def encrypt_flow_response(response: dict, aes_key: bytes, initial_vector: bytes) -> str:
    flipped_iv = bytes(byte ^ 0xFF for byte in initial_vector)
    encryptor = Cipher(
        algorithms.AES(aes_key),
        modes.GCM(flipped_iv),
    ).encryptor()
    payload = json.dumps(response, separators=(",", ":")).encode("utf-8")
    encrypted = encryptor.update(payload) + encryptor.finalize() + encryptor.tag
    return base64.b64encode(encrypted).decode("utf-8")
