"""Check the scope and bounded defaults of a rendered EKS intent."""

from datetime import datetime, timedelta, timezone
import unittest

from render_eks import render


def fixture():
    now = datetime.now(timezone.utc)
    intent = {"run_id": "lab-schema-fixture", "account_id": "123456789012",
              "region": "eu-west-2", "expires_at": (now + timedelta(hours=1)).isoformat(),
              "planned_gross_gbp": 5}
    args = {"kubernetes_version": "1.35", "operator_cidr": "192.0.2.10/32",
            "instance_type": "t4g.medium", "control_plane_role": "lab-eks-control",
            "node_role": "lab-eks-node", "identity_name": "lab-capa", "now": now}
    return intent, args


class RenderTests(unittest.TestCase):
    def test_run_scoped_and_bounded(self):
        intent, args = fixture()
        result = render(intent, **args)
        for item in result["items"]:
            self.assertEqual(item["metadata"]["labels"]["portfolio.whitt.uk/run-id"],
                             intent["run_id"])
            self.assertEqual(
                item["metadata"]["annotations"]["portfolio.whitt.uk/planned-gross-gbp"],
                str(intent["planned_gross_gbp"]),
            )
        pool = next(i for i in result["items"] if i["kind"] == "MachinePool")
        self.assertEqual(pool["spec"]["replicas"], 1)
        pools = [i for i in result["items"] if i["kind"] == "AWSManagedMachinePool"]
        self.assertEqual(len(pools), 3)
        self.assertEqual({i["spec"]["availabilityZones"][0] for i in pools},
                         {"eu-west-2a", "eu-west-2b", "eu-west-2c"})
        for item in pools:
            self.assertEqual(item["spec"]["amiType"], "AL2023_ARM_64_STANDARD")
            self.assertEqual(item["spec"]["scaling"], {"minSize": 1, "maxSize": 1})
        control = next(i for i in result["items"] if i["kind"] == "AWSManagedControlPlane")
        self.assertEqual(control["spec"]["endpointAccess"]["publicCIDRs"], ["192.0.2.10/32"])

    def test_rejects_unscoped_inputs(self):
        intent, args = fixture()
        for key, value in (("operator_cidr", "0.0.0.0/0"),
                           ("node_role", "production"),
                           ("identity_name", "default"),
                           ("kubernetes_version", "latest"),
                           ("instance_type", "t4g.small"),
                           ("instance_type", "t3a.small")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                render(intent, **{**args, key: value})

    def test_x86_fallback(self):
        intent, args = fixture()
        result = render(intent, **{**args, "instance_type": "t3a.medium"})
        for item in result["items"]:
            if item["kind"] == "AWSManagedMachinePool":
                self.assertEqual(item["spec"]["amiType"], "AL2023_x86_64_STANDARD")

    def test_arm_large_fallback(self):
        intent, args = fixture()
        result = render(intent, **{**args, "instance_type": "t4g.large"})
        pools = [i for i in result["items"]
                 if i["kind"] == "AWSManagedMachinePool"]
        self.assertEqual(len(pools), 3)
        self.assertEqual({i["spec"]["instanceType"] for i in pools},
                         {"t4g.large"})

    def test_foreign_region_rejected(self):
        intent, args = fixture()
        with self.assertRaises(ValueError):
            render({**intent, "region": "us-east-1"}, **args)


if __name__ == "__main__":
    unittest.main()
