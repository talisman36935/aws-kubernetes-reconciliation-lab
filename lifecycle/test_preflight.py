"""Negative tests for the static lifecycle intent boundary."""

from datetime import datetime, timezone
import unittest

from preflight import validate


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
        self.intent = {
            "run_id": "lab-fixture",
            "account_id": "123456789012",
            "region": "eu-west-2",
            "expires_at": "2026-10-03T14:00:00Z",
            "budget_usd": 10,
        }

    def test_valid(self):
        validate(self.intent, self.now)

    def test_rejects_unsafe_intents(self):
        for field, value in [
            ("run_id", "*"), ("account_id", "*"), ("region", "all"),
            ("expires_at", "2026-10-03T11:00:00Z"),
            ("expires_at", "2026-10-04T12:00:00Z"),
            ("expires_at", "2026-10-03T14:00:00"),
            ("budget_usd", 0), ("budget_usd", True),
            ("budget_usd", float("nan")), ("budget_usd", 101),
        ]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    validate({**self.intent, field: value}, self.now)

    def test_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            validate({**self.intent, "credentials": "forbidden"}, self.now)


if __name__ == "__main__":
    unittest.main()
