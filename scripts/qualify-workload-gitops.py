"""Hosted-only application Flux reconciliation and configuration rollback test."""

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
import uuid

NAME = "portfolio-workload-gitops"
NAMESPACE = "report-gitops"
IDENTITY = "system:serviceaccount:flux-system:report-reconciler"
NODE_IMAGE = ("kindest/node:v1.35.8@sha256:"
              "07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0")
OPERATOR_URL = ("https://github.com/cloudnative-pg/cloudnative-pg/releases/"
                "download/v1.30.1/cnpg-1.30.1.yaml")
OPERATOR_HASH = "37237f145d8138256ea25ae830f87759255665ff08f8d552fdd8224a5ec032fb"
EXPECTED = {"documents": 3, "tokens": 11, "unique_tokens": 6,
            "duplicate_documents": 1,
            "input_sha256": "2522de9d1c28cf3a163c3703dbabb2b63009e5daa6a8d98f2aac85f577307bd5"}
ROOT = Path(__file__).resolve().parents[1]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def run(*args, data=None, timeout=90):
    return subprocess.run(args, input=data, check=True, capture_output=True,
                          text=True, timeout=timeout).stdout.strip()


def kube(*args, **kwargs):
    return run("kubectl", "--context", "kind-" + NAME, *args, **kwargs)


def get(kind, name, namespace=NAMESPACE):
    return json.loads(kube("-n", namespace, "get", kind, name, "-o", "json"))


def wait(check, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            value = check()
            if value:
                return value
        except (OSError, URLError, subprocess.CalledProcessError):
            pass
        time.sleep(2)
    raise TimeoutError("bounded condition not observed")


def reconcile(revision):
    kube("-n", "flux-system", "patch", "gitrepository", "portfolio",
         "--type=merge", "-p", json.dumps({"spec": {"ref": {"commit": revision}}}))
    run("flux", "reconcile", "source", "git", "portfolio", "--timeout=3m", timeout=200)
    for group in ("platform", "migrations", "apps"):
        run("flux", "reconcile", "kustomization", "report-" + group,
            "--timeout=6m", timeout=380)
        value = get("kustomizations.kustomize.toolkit.fluxcd.io",
                    "report-" + group, "flux-system")
        if not value["status"]["lastAppliedRevision"].endswith(revision):
            raise ValueError("controller applied a different source revision")
        if not any(c["type"] == "Ready" and c["status"] == "True"
                   and c.get("observedGeneration") == value["metadata"]["generation"]
                   for c in value["status"].get("conditions", [])):
            raise ValueError("controller generation is not ready")


def request(path, payload=None, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Idempotency-Key"] = key
    with urlopen(Request("http://127.0.0.1:18080" + path,
                         data=None if payload is None else json.dumps(payload).encode(),
                         headers=headers), timeout=5) as response:
        return json.load(response)


def stop_forward(process):
    if process:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def smoke(release, image, old_jobs):
    for role in ("api", "worker"):
        deployment = get("deployment", "report-" + role)
        if deployment["status"].get("readyReplicas") != 3:
            raise ValueError("three ready replicas not observed")
        if deployment["spec"]["template"]["metadata"]["annotations"].get(
                "portfolio.whitt.uk/config-release") != release:
            raise ValueError("desired pod configuration not observed")
        if deployment["spec"]["template"]["spec"]["containers"][0]["image"] != image:
            raise ValueError("qualified image changed")
    if get("configmap", "delivery-release")["data"]["release"] != release:
        raise ValueError("desired release ConfigMap not observed")
    process = subprocess.Popen([
        "kubectl", "--context", "kind-" + NAME, "-n", NAMESPACE,
        "port-forward", "service/report-api", "18080:8080"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait(lambda: request("/readyz"), 30)
        for job in old_jobs:
            if request("/v1/jobs/" + job + "/report") != EXPECTED:
                raise ValueError("accepted report changed across reconciliation")
        jobs = []
        for _ in range(3):
            key = "gitops-" + uuid.uuid4().hex
            payload = {"fixture": "tiny-v1", "algorithm": "tokens-v1"}
            job = request("/v1/jobs", payload, key)["id"]
            if request("/v1/jobs", payload, key)["id"] != job:
                raise ValueError("idempotency changed")
            wait(lambda: request("/v1/jobs/" + job)["state"] == "succeeded")
            if request("/v1/jobs/" + job + "/report") != EXPECTED:
                raise ValueError("golden report changed")
            jobs.append(job)
        return jobs
    finally:
        stop_forward(process)


def denied_condition():
    obj = get("kustomizations.kustomize.toolkit.fluxcd.io", "report-denied", "flux-system")
    for condition in obj.get("status", {}).get("conditions", []):
        if (condition["type"] == "Ready" and condition["status"] == "False"
                and condition.get("observedGeneration") == obj["metadata"]["generation"]
                and "forbidden" in condition.get("message", "").lower()):
            return {"ready": False, "reason": condition["reason"],
                    "forbidden_observed": True}
    return None


def permissions():
    result = {}
    for resource, allowed in (("configmaps", True), ("deployments.apps", True),
                              ("secrets", False), ("serviceaccounts", False),
                              ("roles.rbac.authorization.k8s.io", False),
                              ("namespaces", False), ("clusterroles", False)):
        command = ["kubectl", "--context", "kind-" + NAME, "auth", "can-i",
                   "create", resource, "--as=" + IDENTITY, "-n", NAMESPACE]
        check = subprocess.run(command, capture_output=True, text=True, timeout=30)
        expected = "yes" if allowed else "no"
        if check.stdout.strip() != expected or check.returncode != (0 if allowed else 1):
            raise ValueError("unexpected delegated permission")
        result[resource] = allowed
    return result


def network_probes():
    """Require allowed TCP success and default-denied TCP failure after warmup."""
    address = str(ipaddress.IPv4Address(get("service", "report-db-rw")["spec"]["clusterIP"]))
    result = {}
    for label, expected in (("allowed", 0), ("denied", 1)):
        name = "report-network-" + label
        kube("apply", "-f", "-", data=json.dumps({
            "apiVersion": "v1", "kind": "Pod", "metadata": {"name": name,
                "namespace": NAMESPACE, "labels": {"portfolio.whitt.uk/network-probe": label}},
            "spec": {"restartPolicy": "Never", "activeDeadlineSeconds": 60,
                "automountServiceAccountToken": False,
                "securityContext": {"runAsNonRoot": True, "runAsUser": 65532,
                                    "seccompProfile": {"type": "RuntimeDefault"}},
                "containers": [{"name": "probe",
                    "image": "postgres:18-alpine@sha256:77f585114c32fbca283dc835b0596f4e52b51b4c6662d7810b2f4084f60a1873",
                    "command": ["sh", "-c", 'sleep 5; nc -z -w 2 "$TARGET" 5432'],
                    "env": [{"name": "TARGET", "value": address}],
                    "resources": {"requests": {"cpu": "10m", "memory": "16Mi"},
                                  "limits": {"cpu": "100m", "memory": "64Mi"}},
                    "securityContext": {"allowPrivilegeEscalation": False,
                        "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}}}]}}))
        def finished():
            pod = get("pod", name)
            states = pod.get("status", {}).get("containerStatuses", [])
            if states and "terminated" in states[0].get("state", {}):
                return states[0]["state"]["terminated"]
            return None
        state = wait(finished, 120)
        if state["exitCode"] != expected:
            raise ValueError("network allow/deny probe did not match policy")
        result[label] = {"exit_code": state["exitCode"], "expected": expected,
                         "target": "report-db-rw:5432"}
        kube("-n", NAMESPACE, "delete", "pod", name, "--wait=true", "--timeout=30s")
    return result


def categories(message):
    """Classify structural failures without exporting the original message."""
    text = message.lower()
    patterns = {"quota-missing-compute": "must specify",
                "quota-exceeded": "exceeded quota", "pod-security": "violates podsecurity",
                "unbound-storage": "unbound immediate persistentvolumeclaims",
                "insufficient-cpu": "insufficient cpu", "insufficient-memory": "insufficient memory",
                "forbidden": "forbidden", "image-pull": "pull image",
                "cel-evaluation": "evaluate", "health-timeout": "health check failed"}
    return sorted(name for name, pattern in patterns.items() if pattern in text)


def diagnostics():
    """Only structural status fields, never logs, env, Secrets or raw messages."""
    result = {}
    for kind in ("pods", "persistentvolumeclaims", "jobs", "events"):
        try:
            objects = json.loads(kube("-n", NAMESPACE, "get", kind, "-o", "json"))["items"]
            rows = []
            for obj in objects[:50]:
                status = obj.get("status", {})
                row = {"name": obj["metadata"]["name"]}
                if kind == "events":
                    row = {"reason": obj.get("reason"),
                           "object_kind": obj.get("involvedObject", {}).get("kind"),
                           "categories": categories(obj.get("message", ""))}
                else:
                    row["phase"] = status.get("phase")
                    row["conditions"] = [{"type": c["type"], "status": c["status"],
                                          "reason": c.get("reason"),
                                          "categories": categories(c.get("message", ""))}
                                         for c in status.get("conditions", [])]
                if kind == "pods":
                    row["node"] = obj["spec"].get("nodeName")
                    row["containers"] = [{"name": c["name"], "resources": c.get("resources", {})}
                                         for c in obj["spec"].get("initContainers", [])
                                         + obj["spec"].get("containers", [])]
                    row["container_states"] = [{"name": c["name"],
                        "waiting_reason": c.get("state", {}).get("waiting", {}).get("reason"),
                        "terminated_reason": c.get("state", {}).get("terminated", {}).get("reason")}
                        for c in status.get("initContainerStatuses", []) + status.get("containerStatuses", [])]
                rows.append(row)
            result[kind] = rows
        except Exception:
            result[kind] = {"unavailable": True}
    try:
        status = get("clusters.postgresql.cnpg.io", "report-db").get("status", {})
        result["database"] = {"instances": status.get("instances"),
                              "ready_instances": status.get("readyInstances"),
                              "phase": status.get("phase"),
                              "conditions": [{"type": c["type"], "status": c["status"],
                                  "reason": c.get("reason"), "categories": categories(c.get("message", ""))}
                                  for c in status.get("conditions", [])]}
    except Exception:
        result["database"] = {"unavailable": True}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    if os.getenv("GITHUB_ACTIONS") != "true":
        parser.error("heavy qualification is hosted-CI only")
    if (not all(re.fullmatch(r"[0-9a-f]{40}", r) for r in (args.baseline, args.candidate))
            or args.baseline == args.candidate):
        parser.error("supply two distinct reviewed immutable Git revisions")
    if run("git", "rev-parse", "HEAD") != args.candidate:
        parser.error("candidate must match the executing checkout")
    run("git", "merge-base", "--is-ancestor", args.baseline, args.candidate)
    if json.loads(run("git", "show", args.baseline + ":workload/source.json")) != json.loads(
            (ROOT / "workload/source.json").read_text()):
        parser.error("configuration rollback requires identical application source/image locks")
    for group in ("platform", "migrations", "root", "denied"):
        for filename in ("resources.json", "kustomization.yaml"):
            path = "management/workload-test/" + group + "/" + filename
            if run("git", "show", args.baseline + ":" + path) != (ROOT / path).read_text().strip():
                parser.error("only application configuration may differ between revisions")
    path = "management/workload-test/local-network/resources.json"
    if run("git", "show", args.baseline + ":" + path) != (ROOT / path).read_text().strip():
        parser.error("local network overlay must be unchanged between revisions")
    if NAME in run("kind", "get", "clusters").splitlines():
        parser.error("refusing to overwrite an existing cluster")
    output = ROOT / "output/workload-gitops.json"
    if output.exists():
        parser.error("refusing to overwrite observations")
    lock = json.loads((ROOT / "workload/source.json").read_text())
    record = {"verification": "hosted-kind-flux", "result": "failed",
              "started_at": stamp(), "baseline_revision": args.baseline,
              "candidate_revision": args.candidate, "application_source": lock["revision"],
              "image": lock["image_digest"], "cloud_provisioned": False,
              "network_policy_enforced": False,
              "simulation": "three labelled workers on one host; local NetworkPolicy allow/deny probes",
              "configuration_rollback_only": True, "phases": [], "permissions": {},
              "controller_denial": None, "migration_before_apps": False,
              "cluster_deleted": False, "errors": []}
    created = False
    stage = "create-cluster"
    original = os.environ.get("KUBECONFIG")
    with tempfile.TemporaryDirectory(prefix="portfolio-gitops-") as scratch:
        os.environ["KUBECONFIG"] = str(Path(scratch) / "kubeconfig")
        try:
            # Mark ownership before create so partial-create errors still clean up.
            created = True
            run("kind", "create", "cluster", "--name", NAME, "--config",
                str(ROOT / "bootstrap/workload-kind.yaml"), "--image", NODE_IMAGE,
                "--wait", "180s", timeout=240)
            stage = "install-controllers"
            run("flux", "install", "--version=v2.9.6",
                "--components=source-controller,kustomize-controller", "--timeout=5m", timeout=330)
            with urlopen(OPERATOR_URL, timeout=60) as response:
                operator = response.read(2 * 1024 * 1024 + 1)
            if hashlib.sha256(operator).hexdigest() != OPERATOR_HASH:
                raise ValueError("operator checksum mismatch")
            kube("apply", "--server-side", "-f", "-", data=operator.decode())
            kube("-n", "cnpg-system", "rollout", "status", "deployment/cnpg-controller-manager",
                 "--timeout=180s", timeout=200)
            stage = "baseline-reconciliation"
            run("flux", "create", "source", "git", "portfolio",
                "--url=https://github.com/talisman36935/aws-kubernetes-reconciliation-lab",
                "--commit=" + args.baseline, "--interval=1m", "--timeout=3m", timeout=200)
            endpoints = json.loads(kube("-n", "default", "get", "endpoints", "kubernetes", "-o", "json"))
            endpoint = str(ipaddress.IPv4Address(endpoints["subsets"][0]["addresses"][0]["ip"]))
            service = str(ipaddress.IPv4Address(get("service", "kubernetes", "default")["spec"]["clusterIP"]))
            graph = json.loads((ROOT / "management/workload-test/root/resources.json").read_text())
            graph["items"][0]["spec"]["postBuild"] = {"substitute": {
                "KIND_API_ENDPOINT": endpoint, "KIND_API_SERVICE": service}}
            kube("apply", "-f", "-", data=json.dumps(graph))
            # Observe platform-created DB early so failures retain structural
            # admission/storage diagnostics instead of only a Flux wait timeout.
            wait(lambda: get("clusters.postgresql.cnpg.io", "report-db").get(
                "status", {}).get("readyInstances") == 3, 240)
            reconcile(args.baseline)
            job = get("job", "report-migrate-" + lock["revision"][:12])
            completion = datetime.fromisoformat(job["status"]["completionTime"].replace("Z", "+00:00"))
            for role in ("api", "worker"):
                created_at = get("deployment", "report-" + role)["metadata"]["creationTimestamp"]
                if datetime.fromisoformat(created_at.replace("Z", "+00:00")) < completion:
                    raise ValueError("application deployed before migration completion")
            record["migration_before_apps"] = True
            jobs = smoke("baseline", lock["image_digest"], [])
            record["phases"].append({"phase": "baseline", "revision": args.baseline, "jobs": jobs})
            stage = "candidate-reconciliation"
            reconcile(args.candidate)
            new = smoke("candidate", lock["image_digest"], jobs)
            record["phases"].append({"phase": "candidate", "revision": args.candidate, "jobs": new})
            jobs += new
            stage = "rollback-reconciliation"
            reconcile(args.baseline)
            new = smoke("baseline", lock["image_digest"], jobs)
            record["phases"].append({"phase": "rollback", "revision": args.baseline, "jobs": new})
            jobs += new
            stage = "drift-repair"
            kube("-n", NAMESPACE, "patch", "configmap", "delivery-release", "--type=merge",
                 "-p", json.dumps({"data": {"release": "out-of-band"}}))
            kube("-n", NAMESPACE, "patch", "deployment", "report-api", "--type=merge", "-p",
                 json.dumps({"spec": {"template": {"metadata": {"annotations": {
                     "portfolio.whitt.uk/config-release": "out-of-band"}}}}}))
            reconcile(args.baseline)
            new = smoke("baseline", lock["image_digest"], jobs)
            record["phases"].append({"phase": "drift-repaired", "revision": args.baseline, "jobs": new})
            stage = "delegated-denial"
            record["permissions"] = permissions()
            kube("apply", "-f", "-", data=json.dumps({
                "apiVersion": "kustomize.toolkit.fluxcd.io/v1", "kind": "Kustomization",
                "metadata": {"name": "report-denied", "namespace": "flux-system"},
                "spec": {"interval": "1m", "timeout": "1m", "prune": True,
                         "sourceRef": {"kind": "GitRepository", "name": "portfolio"},
                         "path": "./management/workload-test/denied",
                         "serviceAccountName": "report-reconciler"}}))
            record["controller_denial"] = wait(denied_condition, 120)
            if "report-forbidden" in kube("get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}").split():
                raise ValueError("forbidden namespace was created")
            stage = "network-policy-probes"
            record["network_probes"] = network_probes()
            record["network_policy_enforced"] = True
            record["result"] = "passed"
        except Exception as error:
            record["errors"].append({"stage": stage, "category": type(error).__name__})
            # No raw command stderr, controller messages, logs or Secrets in artifacts.
            print("qualification failed at", stage, "category", type(error).__name__, flush=True)
            if created and stage not in {"create-cluster", "install-controllers"}:
                for group in ("platform", "migrations", "apps"):
                    try:
                        obj = get("kustomizations.kustomize.toolkit.fluxcd.io", "report-" + group, "flux-system")
                        print(group, [(c["type"], c["status"], c.get("reason"))
                                      for c in obj.get("status", {}).get("conditions", [])])
                    except Exception:
                        pass
                record["diagnostics"] = diagnostics()
                print(json.dumps(record["diagnostics"], sort_keys=True), flush=True)
        finally:
            if created:
                try:
                    run("kind", "delete", "cluster", "--name", NAME, timeout=120)
                    record["cluster_deleted"] = NAME not in run("kind", "get", "clusters").splitlines()
                except Exception as error:
                    record["errors"].append({"stage": "cleanup", "category": type(error).__name__})
            if not record["cluster_deleted"]:
                record["result"] = "failed"
            record["finished_at"] = stamp()
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps(record, indent=2) + "\n")
            if original is None:
                os.environ.pop("KUBECONFIG", None)
            else:
                os.environ["KUBECONFIG"] = original
    print("hosted application GitOps:", record["result"])
    return 0 if record["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
