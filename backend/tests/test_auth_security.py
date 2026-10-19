import pytest

from app.features.auth.security import (
    MAX_PASSWORD_BYTES,
    MIN_PASSWORD_LENGTH,
    PasswordPolicyError,
    create_one_time_token,
    hash_one_time_token,
    hash_password,
    normalize_email,
    validate_new_password,
    verify_password,
)


def test_email_normalization_trims_and_casefolds() -> None:
    assert normalize_email("  Study.Group@EXAMPLE.COM ") == "study.group@example.com"


@pytest.mark.parametrize(
    "email",
    ["", "not-an-email", "missing-at.example.com", "user@"],
)
def test_email_normalization_rejects_invalid_addresses(email: str) -> None:
    with pytest.raises(ValueError, match="valid email"):
        normalize_email(email)


def test_new_password_accepts_boundary_and_preserves_spaces() -> None:
    password = "  " + "a" * (MIN_PASSWORD_LENGTH - 2) + "  "

    validate_new_password(password)
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash)
    assert not verify_password(password.strip(), password_hash)


def test_new_password_rejects_too_short_and_oversized_values() -> None:
    with pytest.raises(PasswordPolicyError, match="at least"):
        validate_new_password("too short")

    with pytest.raises(PasswordPolicyError, match="too long"):
        validate_new_password("a" * (MAX_PASSWORD_BYTES + 1))


def test_password_verification_fails_closed_for_wrong_or_malformed_hash() -> None:
    password_hash = hash_password("an acceptable long passphrase")

    assert not verify_password("a different long passphrase", password_hash)
    assert not verify_password("an acceptable long passphrase", "not-an-argon-hash")


def test_one_time_token_returns_raw_value_and_stores_only_its_sha256_hash() -> None:
    raw_token, stored_hash = create_one_time_token()

    assert len(raw_token) >= 40
    assert len(stored_hash) == 64
    assert stored_hash == hash_one_time_token(raw_token)
    assert raw_token not in stored_hash


def test_hash_one_time_token_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        hash_one_time_token("")
