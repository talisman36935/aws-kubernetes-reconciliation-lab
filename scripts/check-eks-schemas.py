"""Validate a synthetic EKS render against checksum-pinned provider CRD schemas."""

import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen

from jsonschema import Draft4Validator
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lifecycle"))
from render_eks import render
from test_render_eks import fixture

pins = json.loads(Path("management/compatibility/pins.json").read_text())
cache = Path(".cache/compatibility")
cache.mkdir(parents=True, exist_ok=True)
schemas = {}
for name in ("capi", "capa"):
    pin = pins[name]
    artifact = cache / (name + ".yaml")
    if not artifact.exists():
        with urlopen(pin["url"], timeout=30) as response:
            data = response.read()
        artifact.write_bytes(data)
    data = artifact.read_bytes()
    if hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise SystemExit("Provider artifact checksum differs from the compatibility pin")
    for document in yaml.safe_load_all(data):
        if document and document.get("kind") == "CustomResourceDefinition":
            spec = document["spec"]
            for version in spec["versions"]:
                if version["served"]:
                    schemas[(spec["group"] + "/" + version["name"], spec["names"]["kind"])] = version["schema"]["openAPIV3Schema"]
intent, args = fixture()
objects = render(intent, **args)["items"]
checked = 0
for obj in objects:
    if obj["kind"] == "Namespace":
        continue
    key = (obj["apiVersion"], obj["kind"])
    if key not in schemas:
        raise SystemExit("Rendered kind/version absent from pinned served CRDs: " + str(key))
    Draft4Validator(schemas[key]).validate(obj)
    checked += 1
print(f"Validated {checked} synthetic custom resources against pinned served CRDs.")
print("Schema result only; no controller installation or AWS API calls.")
