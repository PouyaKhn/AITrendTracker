"""Admin authentication helpers.

Credentials are never stored in plaintext. The admin password is kept as a salted
PBKDF2-SHA256 hash in the ``ADMIN_PASSWORD_HASH`` environment variable, and login
verification uses a constant-time comparison to avoid timing side-channels.

Generate a hash for a new password:

    python auth.py

then set the printed value as ``ADMIN_PASSWORD_HASH`` (and ``ADMIN_USERNAME``).
"""

import hashlib
import hmac
import os
import secrets

# Encoded format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
_ALGORITHM = "pbkdf2_sha256"
_DEFAULT_ITERATIONS = 240_000
_SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = _DEFAULT_ITERATIONS,
                  salt: bytes | None = None) -> str:
    """Return an encoded PBKDF2-SHA256 hash for ``password``."""
    if salt is None:
        salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALGORITHM}${iterations}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time check of ``password`` against an encoded PBKDF2 hash."""
    try:
        algorithm, iterations_s, salt_hex, hash_hex = encoded.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (AttributeError, ValueError):
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected)


def admin_credentials_configured() -> bool:
    """True when both the admin username and password hash are set."""
    return bool(os.getenv("ADMIN_USERNAME", "").strip()
                and os.getenv("ADMIN_PASSWORD_HASH", "").strip())


def verify_admin_credentials(username: str, password: str) -> bool:
    """Verify a submitted username/password against the configured admin credentials.

    Both checks always run (no short-circuit) so the response time does not reveal
    whether the username alone was correct.
    """
    expected_user = os.getenv("ADMIN_USERNAME", "").strip()
    expected_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    if not expected_user or not expected_hash:
        return False
    user_ok = hmac.compare_digest(
        (username or "").encode("utf-8"), expected_user.encode("utf-8")
    )
    password_ok = verify_password(password or "", expected_hash)
    return user_ok and password_ok


if __name__ == "__main__":
    import getpass

    pw = getpass.getpass("Admin password: ")
    if pw != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    print("\nSet this in your environment / .env:\n")
    print(f"ADMIN_PASSWORD_HASH='{hash_password(pw)}'")
