import hashlib
import secrets

from email_validator import EmailNotValidError, validate_email
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

MIN_PASSWORD_LENGTH = 15
MAX_PASSWORD_BYTES = 1024

_password_hasher = PasswordHash.recommended()


class PasswordPolicyError(ValueError):
    """Raised when a new password falls outside the supported password policy."""


def normalize_email(email: str) -> str:
    try:
        normalized = validate_email(email.strip(), check_deliverability=False).normalized
    except EmailNotValidError:
        raise ValueError("Enter a valid email address") from None
    return normalized.casefold()


def validate_new_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters"
        )
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise PasswordPolicyError("Password is too long")


def hash_password(password: str) -> str:
    validate_new_password(password)
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password, password_hash)
    except (PwdlibError, ValueError):
        return False


def create_one_time_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hash_one_time_token(token)


def hash_one_time_token(token: str) -> str:
    if not token:
        raise ValueError("Token cannot be empty")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
