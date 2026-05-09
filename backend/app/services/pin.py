"""
PIN service — secure PIN hashing and verification.

Uses bcrypt (cost factor 12). PIN is hashed immediately on receipt.
Never stored raw. Never logged.
"""
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_pin(raw_pin: str) -> str:
    """Return bcrypt hash of the 4-digit PIN."""
    return _ctx.hash(raw_pin)


def verify_pin(raw_pin: str, hashed: str) -> bool:
    """Return True if raw_pin matches the stored bcrypt hash."""
    return _ctx.verify(raw_pin, hashed)
