"""Check the scope and bounded defaults of a rendered EKS intent."""

from datetime import datetime, timedelta, timezone
import unittest

from render_eks import render


def fixture():
    now = datetime.now(timezone.utc)
    intent = {"run_id": "lab-schema-fixture", "account_id": "123456789012",
              "region": "eu-west-2", "expires_at": (now + timedelta(hours=1)).isoformat(),
              "budget_usd": 10}
    args = {"kubernetes_version": "1.35", "operator_cidr": "192.0.2.10/32",
            "instance_type": "t3.medium", "control_plane_role": "lab-eks-control",
            "node_role": "lab-eks-node", "identity_name": "lab-capa", "now": now}
    return intent, args


class RenderTests(unittest.TestCase):
    def test_run_scoped_and_bounded(self):
        intent, args = fixture()
        result = render(intent, **args)
        for item in result["items"]:
            self.assertEqual(item["metadata"]["labels"]["portfolio.whitt.uk/run-id"],
                             intent["run_id"])
        pool = next(i for i in result["items"] if i["kind"] == "MachinePool")
        self.assertEqual(pool["spec"]["replicas"], 1)
        control = next(i for i in result["items"] if i["kind"] == "AWSManagedControlPlane")
        self.assertEqual(control["spec"]["endpointAccess"]["publicCIDRs"], ["192.0.2.10/32"])

    def test_rejects_unscoped_inputs(self):
        intent, args = fixture()
        for key, value in (("operator_cidr", "0.0.0.0/0"),
                           ("node_role", "production"),
                           ("identity_name", "default"),
                           ("kubernetes_version", "latest")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                render(intent, **{**args, key: value})


if __name__ == "__main__":
    unittest.main()
