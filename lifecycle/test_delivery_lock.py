"""Verify the renderer cannot bypass the reviewed source/image lock."""

from contextlib import redirect_stderr
import importlib.util
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("delivery", ROOT / "scripts/render-workload-delivery.py")
DELIVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DELIVERY)


class DeliveryLockTests(unittest.TestCase):
    def test_locked_clean_source_and_release_only(self):
        lock = json.loads((ROOT / "workload/source.json").read_text())
        for case in ("clean", "foreign-image", "foreign-source", "dirty"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as scratch:
                release = {"source_revision": lock["revision"], "image": lock["image_digest"]}
                if case == "foreign-image":
                    release["image"] = "ghcr.io/foreign/report@sha256:" + "a" * 64
                path = Path(scratch) / "release.json"
                path.write_text(json.dumps(release))
                responses = [subprocess.CompletedProcess([], 0,
                    stdout=lock["revision"] if case != "foreign-source" else "b" * 40),
                    subprocess.CompletedProcess([], 0, stdout=" M workload/file.go" if case == "dirty" else ""),
                    subprocess.CompletedProcess([], 0)]
                arguments = ["render", "--shared-source", scratch, "--release", str(path),
                             "--storage-class", "standard", "--output", str(Path(scratch) / "profile")]
                with patch("sys.argv", arguments), patch.object(DELIVERY.subprocess, "run", side_effect=responses) as run, redirect_stderr(StringIO()):
                    if case == "clean":
                        DELIVERY.main()
                        self.assertEqual(run.call_count, 3)
                        self.assertIn("--owner", run.call_args.args[0])
                        self.assertIn("flux", run.call_args.args[0])
                    else:
                        with self.assertRaises(SystemExit):
                            DELIVERY.main()
                        self.assertLess(run.call_count, 3)


if __name__ == "__main__":
    unittest.main()
