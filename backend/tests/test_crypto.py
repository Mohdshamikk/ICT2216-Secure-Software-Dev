import hashlib

from app.utils.crypto import (
    BCRYPT_WORK_FACTOR,
    generate_secure_token,
    generate_totp_secret,
    get_totp_provisioning_uri,
    hash_password,
    validate_password_complexity,
    verify_password,
)


def test_hash_password_and_verify_password():
    password = "Ocean!Lantern92-Maple"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith(f"$2b${BCRYPT_WORK_FACTOR}$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!123", hashed) is False


def test_password_policy_rejects_short_password():
    valid, reason = validate_password_complexity("Short1!")

    assert valid is False
    assert "12 characters" in reason


def test_password_policy_rejects_weak_common_password():
    valid, reason = validate_password_complexity("Password123!")

    assert valid is False
    assert reason != ""


def test_password_policy_accepts_strong_password():
    valid, reason = validate_password_complexity("Ocean!Lantern92-Maple")

    assert valid is True
    assert reason == ""


def test_password_policy_rejects_bcrypt_truncation_risk():
    valid, reason = validate_password_complexity("A" * 73)

    assert valid is False
    assert "72 bytes" in reason


def test_secure_token_returns_raw_token_and_sha256_hash():
    raw_token, token_hash = generate_secure_token()

    assert raw_token != token_hash
    assert len(raw_token) > 32
    assert token_hash == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def test_totp_secret_and_provisioning_uri():
    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri("test@example.com", secret)

    assert len(secret) >= 32
    assert uri.startswith("otpauth://totp/")
    assert "issuer=FinTrack" in uri