"""
Authentication module for Smart Factory Floor Monitor.
Passwords are stored as SHA-256 hashes with a random salt.
Two default accounts are seeded on first run:
  admin    / admin123
  operator / operator123
"""

import hashlib
import os
from database import find_user, create_user
from config import ROLE_ADMIN, ROLE_OPERATOR


def _hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, _ = stored_hash.split(":", 1)
    return _hash_password(password, salt) == stored_hash


def login(username: str, password: str):
    """
    Returns {"username": ..., "role": ...} on success, None on failure.
    """
    user = find_user(username)
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None


def seed_default_users():
    """
    Creates default accounts if they do not already exist.
    Called once at application startup.
    """
    create_user("admin",    _hash_password("admin123"),    ROLE_ADMIN)
    create_user("operator", _hash_password("operator123"), ROLE_OPERATOR)
    print("[Auth] Default accounts ready  →  admin / admin123  |  operator / operator123")
