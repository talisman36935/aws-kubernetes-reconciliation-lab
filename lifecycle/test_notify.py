"""Tests for allowlisted AWS SNS lifecycle notifications."""

import json
import subprocess
import unittest
from unittest.mock import Mock

from notify import EVENTS, message, publish


class LifecycleNotificationTests(unittest.TestCase):
    def test_every_documented_event_is_valid(self):
        for event in EVENTS:
            with self.subTest(event=event):
                item = message("lab-demo-1", event, "2026-10-06T12:00:00Z")
                self.assertEqual(item["event"], event)
                self.assertEqual(item["schema"], "portfolio.lifecycle.v1")

    def test_rejects_unscoped_or_malformed_events(self):
        for run_id, event in [("*", "ready"), ("lab-demo", "shell;bad")]:
            with self.subTest(run_id=run_id, event=event):
                with self.assertRaises(ValueError):
                    message(run_id, event, "2026-10-06T12:00:00Z")

    def test_publisher_uses_argv_and_json_payload_without_shell(self):
        topic = "arn:aws:sns:eu-west-2:123456789012:portfolio-lab-alerts"
        runner = Mock()
        publish(topic, "lab-demo-1", "teardown-failed", runner=runner)
        args, kwargs = runner.call_args
        command = args[0]
        self.assertEqual(command[:4], ["aws", "sns", "publish", "--region"])
        self.assertIn(topic, command)
        self.assertTrue(kwargs["check"])
        self.assertTrue(kwargs["capture_output"])
        self.assertNotIn("shell", kwargs)
        payload = json.loads(command[command.index("--message") + 1])
        self.assertEqual(payload["event"], "teardown-failed")

    def test_rejects_foreign_region_topic(self):
        with self.assertRaises(ValueError):
            publish("arn:aws:sns:us-east-1:123456789012:topic", "lab-demo", "ready")

    def test_delivery_errors_fail_closed_without_raw_provider_output(self):
        topic = "arn:aws:sns:eu-west-2:123456789012:portfolio-lab-alerts"
        runner = Mock(side_effect=subprocess.CalledProcessError(1, ["aws"], stderr="private detail"))
        with self.assertRaisesRegex(RuntimeError, "delivery to SNS failed"):
            publish(topic, "lab-demo-1", "ready", runner=runner)


if __name__ == "__main__":
    unittest.main()
