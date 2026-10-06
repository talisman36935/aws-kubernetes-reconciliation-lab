"""Independent evidence gates reject aliasing and incomplete/private records."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "observation", ROOT / "scripts/validate-workload-observation.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ObservationTests(unittest.TestCase):
    def test_rejects_original_aliased_observation(self):
        record = json.loads((ROOT / "docs/observations/821df36/workload-gitops.json").read_text())
        with self.assertRaises(ValueError):
            MODULE.validate(record)

    def test_complete_shape_and_negative_gates(self):
        original = json.loads((ROOT / "docs/observations/821df36/workload-gitops.json").read_text())
        # In-memory schema fixture only; the retained runtime artifact is untouched.
        valid = deepcopy(original)
        valid["phases"][0]["jobs"] = valid["phases"][0]["jobs"][:3]
        MODULE.validate(valid)
        for case in ("cleanup", "cloud", "private-field", "denial", "duplicate", "probe", "rollback"):
            with self.subTest(case=case):
                bad = deepcopy(valid)
                if case == "cleanup":
                    bad["cluster_deleted"] = False
                elif case == "cloud":
                    bad["cloud_provisioned"] = True
                elif case == "private-field":
                    bad["raw_log"] = "synthetic-private-text"
                elif case == "denial":
                    bad["controller_denial"]["forbidden_observed"] = False
                elif case == "duplicate":
                    bad["phases"][1]["jobs"][0] = bad["phases"][0]["jobs"][0]
                elif case == "probe":
                    bad["network_probes"]["denied"]["exit_code"] = 0
                elif case == "rollback":
                    bad["phases"][2]["revision"] = bad["candidate_revision"]
                with self.assertRaises(ValueError):
                    MODULE.validate(bad)


if __name__ == "__main__":
    unittest.main()
