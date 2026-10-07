"""Diagnostic export keeps only structural failure categories."""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gitops_test", ROOT / "scripts/qualify-workload-gitops.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DiagnosticsTests(unittest.TestCase):
    def test_release_marker_is_read_from_the_exact_revision(self):
        source = {"items": [
            {"kind": "Deployment", "spec": {"template": {"metadata": {
                "annotations": {"portfolio.whitt.uk/config-release": "candidate"}}}}},
            {"kind": "ConfigMap", "metadata": {"name": "delivery-release"},
             "data": {"release": "candidate"}},
        ]}
        with patch.object(MODULE, "run", return_value=json.dumps(source)) as run:
            self.assertEqual(MODULE.release_marker("a" * 40), "candidate")
        run.assert_called_once_with(
            "git", "show", "a" * 40 + ":management/workload-test/apps/resources.json")

    def test_release_marker_rejects_inconsistent_source_fixture(self):
        source = {"items": [
            {"kind": "Deployment", "spec": {"template": {"metadata": {
                "annotations": {"portfolio.whitt.uk/config-release": "baseline"}}}}},
            {"kind": "ConfigMap", "metadata": {"name": "delivery-release"},
             "data": {"release": "candidate"}},
        ]}
        with patch.object(MODULE, "run", return_value=json.dumps(source)):
            with self.assertRaisesRegex(ValueError, "inconsistent synthetic release markers"):
                MODULE.release_marker("b" * 40)

    def test_phase_records_are_independent_snapshots(self):
        jobs = ["a" * 32]
        phase = MODULE.phase_record("baseline", "b" * 40, jobs, "d" * 40,
                                    "ghcr.io/talisman36935/report-workshop@sha256:" + "e" * 64)
        jobs += ["c" * 32]
        self.assertEqual(phase["jobs"], ["a" * 32])

    def test_raw_messages_and_credentials_are_not_returned(self):
        message = "secret=private-dummy must specify requests.cpu; forbidden"
        self.assertEqual(MODULE.categories(message), ["forbidden", "quota-missing-compute"])
        self.assertNotIn("private-dummy", str(MODULE.categories(message)))
        self.assertEqual(MODULE.categories("unrelated private-dummy"), [])


if __name__ == "__main__":
    unittest.main()
