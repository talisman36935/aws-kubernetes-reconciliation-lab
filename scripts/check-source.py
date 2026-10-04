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
print("revision=" + source["revision"])
