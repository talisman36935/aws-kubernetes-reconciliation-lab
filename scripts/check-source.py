"""Validate the shared-source lock before CI checks out its public revision."""

import json
from pathlib import Path
import re

source = json.loads(Path("workload/source.json").read_text())
if source["repository"] != "https://github.com/talisman36935/gcp-platform-delivery-lab.git":
    raise SystemExit("Unexpected shared-source repository")
if source["directory"] != "workload":
    raise SystemExit("Unexpected source directory")
if not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
    raise SystemExit("Shared source must use an immutable Git revision")
if source["image_digest"] is not None and not re.fullmatch(
        r"ghcr\.io/talisman36935/report-workshop@sha256:[0-9a-f]{64}",
        source["image_digest"]):
    raise SystemExit("Shared image must use the immutable published index")
print("revision=" + source["revision"])
