"""Direct unit tests for the password hashing layer.

This is the exact spot that regressed: an incompatible bcrypt version made
``hash_password`` raise at runtime, 500-ing every register/login. These tests
fail fast and unambiguously if the bcrypt/passlib backend is broken again.
"""

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_hash_handles_long_password():
    # bcrypt has a 72-byte limit; the backend must not blow up on long input.
    long_password = "a" * 200
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed) is True


def test_access_token_roundtrip():
    token = create_access_token("builder@example.com")
    assert decode_token(token) == "builder@example.com"


def test_decode_invalid_token_returns_none():
    assert decode_token("not-a-real-token") is None
