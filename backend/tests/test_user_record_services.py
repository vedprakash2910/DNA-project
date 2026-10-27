"""Service-level tests: registration, login verification, record authorization.
Uses a throw-away SQLite file; no FastAPI needed.

Run from the backend folder:   python -m unittest tests.test_user_record_services -v
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from services import record_service, user_service
from utils import security
from utils.database import get_connection
from utils.exceptions import (
    EmailAlreadyRegisteredError, ForbiddenError, InvalidCredentialsError, RecordNotFoundError,
)

REPORT = {"summary": {"total_mutations": 2, "overall_classification": "Low"}, "mutations": []}


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        for patcher in (
            mock.patch.object(config, "DATABASE_PATH", os.path.join(self._dir.name, "t.db")),
            mock.patch.object(security, "SCRYPT_N", 2 ** 10),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self._dir.cleanup)

    def make_admin(self, user):
        with get_connection() as conn:
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user["id"],))
        return {**user, "role": "admin"}


class RegistrationAndLoginTests(ServiceTestCase):
    def test_register_returns_public_user_with_role_user(self):
        user = user_service.register_user("  Alice@Example.COM ", "password-1")
        self.assertEqual(user["email"], "alice@example.com")
        self.assertEqual(user["role"], "user")
        self.assertNotIn("password_hash", user)

    def test_password_is_stored_hashed_not_plain(self):
        user = user_service.register_user("a@example.com", "password-1")
        with get_connection() as conn:
            stored = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],)).fetchone()[0]
        self.assertNotEqual(stored, "password-1")
        self.assertNotIn("password-1", stored)
        self.assertTrue(stored.startswith("scrypt$"))

    def test_duplicate_email_is_rejected_case_insensitively(self):
        user_service.register_user("a@example.com", "password-1")
        with self.assertRaises(EmailAlreadyRegisteredError):
            user_service.register_user("A@EXAMPLE.com", "password-2")

    def test_login_success(self):
        registered = user_service.register_user("a@example.com", "password-1")
        user = user_service.authenticate_user("A@example.com", "password-1")
        self.assertEqual(user["id"], registered["id"])

    def test_wrong_password_and_unknown_email_give_same_error(self):
        user_service.register_user("a@example.com", "password-1")
        with self.assertRaises(InvalidCredentialsError) as wrong_pw:
            user_service.authenticate_user("a@example.com", "nope-nope-1")
        with self.assertRaises(InvalidCredentialsError) as unknown:
            user_service.authenticate_user("who@example.com", "password-1")
        self.assertEqual(wrong_pw.exception.message, unknown.exception.message)

    def test_sql_injection_in_email_is_just_a_wrong_email(self):
        user_service.register_user("a@example.com", "password-1")
        with self.assertRaises(InvalidCredentialsError):
            user_service.authenticate_user("' OR '1'='1", "password-1")

    def test_get_user_by_id(self):
        user = user_service.register_user("a@example.com", "password-1")
        self.assertEqual(user_service.get_user_by_id(user["id"])["email"], "a@example.com")
        self.assertIsNone(user_service.get_user_by_id("missing"))


class RecordAuthorizationTests(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.alice = user_service.register_user("alice@example.com", "password-1")
        self.bob = user_service.register_user("bob@example.com", "password-1")

    def test_owner_can_read_and_delete(self):
        record = record_service.create_record(self.alice["id"], "mine", REPORT)
        got = record_service.get_authorized_record(record["id"], self.alice)
        self.assertEqual(got["title"], "mine")
        self.assertEqual(got["report"], REPORT)
        record_service.delete_record(record["id"], self.alice)
        with self.assertRaises(RecordNotFoundError):
            record_service.get_authorized_record(record["id"], self.alice)

    def test_other_user_is_forbidden(self):
        record = record_service.create_record(self.alice["id"], "mine", REPORT)
        with self.assertRaises(ForbiddenError):
            record_service.get_authorized_record(record["id"], self.bob)
        with self.assertRaises(ForbiddenError):
            record_service.delete_record(record["id"], self.bob)
        # ...and it was not deleted
        self.assertEqual(record_service.get_authorized_record(record["id"], self.alice)["title"], "mine")

    def test_unknown_id_is_404(self):
        with self.assertRaises(RecordNotFoundError):
            record_service.get_authorized_record("nope", self.alice)

    def test_list_only_returns_own_records(self):
        record_service.create_record(self.alice["id"], "a1", REPORT)
        record_service.create_record(self.bob["id"], "b1", REPORT)
        self.assertEqual([r["title"] for r in record_service.list_records(self.alice)], ["a1"])
        self.assertEqual([r["title"] for r in record_service.list_records(self.bob)], ["b1"])

    def test_admin_can_access_and_list_everything(self):
        admin = self.make_admin(user_service.register_user("root@example.com", "password-1"))
        record = record_service.create_record(self.alice["id"], "a1", REPORT)
        self.assertEqual(record_service.get_authorized_record(record["id"], admin)["title"], "a1")
        self.assertEqual(len(record_service.list_records(admin)), 1)
        record_service.delete_record(record["id"], admin)

    def test_deleting_user_removes_their_records(self):
        record_service.create_record(self.alice["id"], "a1", REPORT)
        with get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (self.alice["id"],))
            count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
