"""Unit tests for password hashing and JWT helpers (no FastAPI, no database).

Run from the backend folder:   python -m unittest tests.test_security -v
"""
import base64
import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt

import config
from utils import security
from utils.exceptions import TokenExpiredError, TokenInvalidError

OTHER_SECRET = "x" * 40


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


class PasswordHashingTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(security, "SCRYPT_N", 2 ** 10)  # fast for tests
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_hash_is_not_the_password_and_verifies(self):
        stored = security.hash_password("s3cret-pass")
        self.assertNotIn("s3cret-pass", stored)
        self.assertTrue(stored.startswith("scrypt$"))
        self.assertTrue(security.verify_password("s3cret-pass", stored))

    def test_wrong_password_fails(self):
        stored = security.hash_password("s3cret-pass")
        self.assertFalse(security.verify_password("s3cret-pasS", stored))
        self.assertFalse(security.verify_password("", stored))

    def test_same_password_gets_different_hashes_because_of_salt(self):
        self.assertNotEqual(security.hash_password("same"), security.hash_password("same"))

    def test_unicode_and_long_passwords(self):
        for password in ("pässwörd-密码-🔑", "a" * 128):
            self.assertTrue(security.verify_password(password, security.hash_password(password)))

    def test_garbage_hash_returns_false_instead_of_raising(self):
        for bad in ("", "plaintext", "scrypt$1$2", "bcrypt$a$b$c$d$e", "scrypt$x$y$z$!!$!!"):
            self.assertFalse(security.verify_password("pw", bad))

    def test_old_hashes_still_verify_after_cost_change(self):
        stored = security.hash_password("pw")
        with mock.patch.object(security, "SCRYPT_N", 2 ** 11):
            self.assertTrue(security.verify_password("pw", stored))


class JwtTests(unittest.TestCase):
    def test_payload_has_expected_claims_and_expiry(self):
        token = security.create_access_token("user-1", "user")
        payload = security.decode_access_token(token)
        self.assertEqual(payload["sub"], "user-1")
        self.assertEqual(payload["role"], "user")
        self.assertEqual(payload["type"], "access")
        self.assertEqual(payload["exp"] - payload["iat"], config.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    def test_token_has_three_parts_and_hs256_header(self):
        token = security.create_access_token("u", "user")
        self.assertEqual(len(token.split(".")), 3)
        self.assertEqual(jwt.get_unverified_header(token)["alg"], "HS256")

    def test_custom_expiry(self):
        token = security.create_access_token("u", "user", expires_delta=timedelta(seconds=90))
        p = security.decode_access_token(token)
        self.assertEqual(p["exp"] - p["iat"], 90)

    def test_expired_token_raises_token_expired(self):
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        token = security.create_access_token("u", "user", now=past)
        with self.assertRaises(TokenExpiredError):
            security.decode_access_token(token)

    def test_token_signed_with_other_secret_is_invalid(self):
        token = jwt.encode({"sub": "u", "type": "access", "iat": datetime.now(timezone.utc),
                            "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                           OTHER_SECRET, algorithm="HS256")
        with self.assertRaises(TokenInvalidError):
            security.decode_access_token(token)

    def test_tampered_payload_is_invalid(self):
        header, payload, signature = security.create_access_token("u", "user").split(".")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        claims["role"] = "admin"
        forged = ".".join([header, _b64(claims), signature])
        with self.assertRaises(TokenInvalidError):
            security.decode_access_token(forged)

    def test_alg_none_token_is_rejected(self):
        token = jwt.encode({"sub": "u", "type": "access", "role": "admin",
                            "iat": datetime.now(timezone.utc),
                            "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                           None, algorithm="none")
        with self.assertRaises(TokenInvalidError):
            security.decode_access_token(token)

    def test_missing_claims_and_wrong_type_are_invalid(self):
        now = datetime.now(timezone.utc)
        no_exp = jwt.encode({"sub": "u", "type": "access", "iat": now}, config.JWT_SECRET, algorithm="HS256")
        wrong_type = jwt.encode({"sub": "u", "type": "refresh", "iat": now, "exp": now + timedelta(minutes=5)},
                                config.JWT_SECRET, algorithm="HS256")
        for token in (no_exp, wrong_type, "not.a.jwt", ""):
            with self.assertRaises(TokenInvalidError, msg=token):
                security.decode_access_token(token)


if __name__ == "__main__":
    unittest.main()
