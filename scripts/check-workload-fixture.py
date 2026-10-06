"""Check local-only GitOps fixture derivation against the pinned shared renderer."""

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "management/workload-test"
DEPLOYMENT_HEALTH_EXPRESSION = (
    "has(status.observedGeneration) && has(status.updatedReplicas) "
    "&& has(status.readyReplicas) && has(status.availableReplicas) "
    "&& status.observedGeneration == metadata.generation "
    "&& status.updatedReplicas == spec.replicas "
    "&& status.readyReplicas == spec.replicas "
    "&& status.availableReplicas == spec.replicas"
)


def verify_root_health(root_items):
    report_apps = [item for item in root_items
                   if item.get("kind") == "Kustomization"
                   and item.get("metadata", {}).get("name") == "report-apps"]
    expected = [{"apiVersion": "apps/v1", "kind": "Deployment",
                 "current": DEPLOYMENT_HEALTH_EXPRESSION}]
    if (len(report_apps) != 1
            or report_apps[0].get("spec", {}).get("healthCheckExprs") != expected):
        raise ValueError("report-apps Deployment health check differs from shared renderer contract")


def verify(shared_source: Path):
    lock = json.loads((ROOT / "workload/source.json").read_text())
    revision = subprocess.run(["git", "-C", str(shared_source), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
    if revision != lock["revision"]:
        raise ValueError("fixture check requires the exact shared source")
    sys.path.insert(0, str(shared_source / "workload/deploy"))
    spec = importlib.util.spec_from_file_location(
        "delivery_fixture", shared_source / "workload/deploy/render_delivery.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    release = {"source_revision": lock["revision"], "image": lock["image_digest"],
               "capabilities": ["schema-check", "cloud-queue-object-v1"]}
    expected = module.render(release=release, owner="flux", namespace="report-gitops",
                             storage_class="standard")
    root_items = json.loads((FIXTURE / "root/resources.json").read_text())["items"]
    verify_root_health(root_items)
    for group in ("platform", "migrations", "apps"):
        actual = json.loads((FIXTURE / group / "resources.json").read_text())["items"]
        if group == "apps":
            config = actual.pop()
            if (config["kind"] != "ConfigMap" or config["metadata"]["name"] != "delivery-release"
                    or config["data"] not in ({"release": "baseline"}, {"release": "candidate"})):
                raise ValueError("invalid synthetic release marker")
            for obj in actual:
                if obj["kind"] == "Deployment":
                    annotations = obj["spec"]["template"]["metadata"].pop("annotations")
                    if annotations != {"portfolio.whitt.uk/config-release": config["data"]["release"]}:
                        raise ValueError("deployment marker and release disagree")
        if actual != expected[group]:
            raise ValueError("fixture drifted from the locked shared renderer: " + group)
    print("fixture matches locked renderer plus explicit local test markers")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-source", type=Path, required=True)
    verify(parser.parse_args().shared_source)
