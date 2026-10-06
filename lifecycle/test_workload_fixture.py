"""Static guardrails for the opt-in hosted workload experiment."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "management/workload-test"


class WorkloadFixtureTests(unittest.TestCase):
    def test_disjoint_ownership_pins_and_migration_order(self):
        lock = json.loads((ROOT / "workload/source.json").read_text())
        identities = set()
        for group in ("platform", "migrations", "apps"):
            objects = json.loads((FIXTURE / group / "resources.json").read_text())["items"]
            for obj in objects:
                identity = (obj["apiVersion"], obj["kind"],
                            obj["metadata"].get("namespace"), obj["metadata"]["name"])
                self.assertNotIn(identity, identities)
                identities.add(identity)
                self.assertNotEqual(obj["kind"], "Secret")
                if obj["kind"] in {"Deployment", "Job"}:
                    pod = obj["spec"]["template"]["spec"]
                    for container in pod["containers"] + pod.get("initContainers", []):
                        self.assertEqual(container["image"], lock["image_digest"])
                    if obj["kind"] == "Deployment":
                        self.assertEqual(pod["initContainers"][0]["args"], ["schema-check"])
        graph = json.loads((FIXTURE / "root/resources.json").read_text())["items"]
        for index, group in enumerate(("platform", "migrations", "apps")):
            spec = graph[index]["spec"]
            self.assertEqual(spec["path"], "./management/workload-test/" + group)
            self.assertTrue(spec["wait"])
            if index:
                self.assertEqual(spec["serviceAccountName"], "report-reconciler")
                self.assertEqual(spec["dependsOn"], [{"name": graph[index - 1]["metadata"]["name"]}])
        denied = json.loads((FIXTURE / "denied/resources.json").read_text())["items"]
        self.assertEqual(denied, [{"apiVersion": "v1", "kind": "Namespace",
                                   "metadata": {"name": "report-forbidden"}}])
        overlay = json.loads((FIXTURE / "local-network/resources.json").read_text())["items"]
        for policy in overlay:
            self.assertEqual(policy["kind"], "NetworkPolicy")
            self.assertEqual(policy["metadata"]["namespace"], "report-gitops")
            self.assertNotIn("0.0.0.0/0", json.dumps(policy))
        self.assertEqual(len(overlay), 3)


if __name__ == "__main__":
    unittest.main()
