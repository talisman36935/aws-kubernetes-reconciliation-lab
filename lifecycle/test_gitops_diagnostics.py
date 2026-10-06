"""Diagnostic export keeps only structural failure categories."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gitops_test", ROOT / "scripts/qualify-workload-gitops.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DiagnosticsTests(unittest.TestCase):
    def test_raw_messages_and_credentials_are_not_returned(self):
        message = "secret=private-dummy must specify requests.cpu; forbidden"
        self.assertEqual(MODULE.categories(message), ["forbidden", "quota-missing-compute"])
        self.assertNotIn("private-dummy", str(MODULE.categories(message)))
        self.assertEqual(MODULE.categories("unrelated private-dummy"), [])


if __name__ == "__main__":
    unittest.main()
