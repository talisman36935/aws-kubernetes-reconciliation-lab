"""Static contract tests for AWS budget alert configuration."""

import json
from pathlib import Path
import unittest


TEMPLATE = Path(__file__).with_name("budget-alerts.json")


class BudgetAlertTests(unittest.TestCase):
    def test_gross_cost_thresholds_are_configurable_alerts_not_a_cap(self):
        template = json.loads(TEMPLATE.read_text())
        params = template["Parameters"]
        self.assertTrue(params["AlertEmail"]["NoEcho"])
        self.assertNotIn("MaxValue", params["BudgetAmount"])
        self.assertIn("not a spending cap", params["BudgetAmount"]["Description"])
        self.assertEqual(params["BudgetCurrency"]["AllowedValues"], ["GBP"])
        budget = template["Resources"]["RunCostBudget"]["Properties"]
        self.assertFalse(budget["Budget"]["CostTypes"]["IncludeCredit"])
        self.assertEqual(budget["ResourceTags"][0]["Key"], "portfolio-owner")
        self.assertEqual(budget["Budget"]["TimeUnit"], "MONTHLY")
        notifications = budget["NotificationsWithSubscribers"]
        actual = [n for n in notifications
                  if n["Notification"]["NotificationType"] == "ACTUAL"]
        forecast = [n for n in notifications
                    if n["Notification"]["NotificationType"] == "FORECASTED"]
        self.assertEqual([n["Notification"]["Threshold"] for n in actual],
                         [25, 50, 75, 90, 100])
        self.assertEqual([n["Notification"]["Threshold"] for n in forecast],
                         [75, 100])
        for notification in notifications:
            self.assertEqual(notification["Subscribers"], [{
                "SubscriptionType": "SNS", "Address": {"Ref": "BudgetAlertsTopic"}}])
        subscription = template["Resources"]["BudgetAlertsTopic"]["Properties"]["Subscription"][0]
        self.assertEqual(subscription, {
            "Endpoint": {"Ref": "AlertEmail"}, "Protocol": "email"})


if __name__ == "__main__":
    unittest.main()
