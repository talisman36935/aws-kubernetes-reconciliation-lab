"""Validate the allowlisted successful local GitOps observation, not a signature."""

from datetime import datetime
import json
from pathlib import Path
import re
import sys


def validate(record):
    fields = {"verification", "result", "started_at", "finished_at", "baseline_revision",
              "candidate_revision", "application_source", "image", "cloud_provisioned",
              "network_policy_enforced", "simulation", "configuration_rollback_only", "phases",
              "permissions", "controller_denial", "migration_before_apps", "cluster_deleted",
              "errors", "network_probes"}
    if set(record) != fields:
        raise ValueError("observation fields must match the allowlist")
    if record["verification"] != "hosted-kind-flux" or record["result"] != "passed":
        raise ValueError("a complete successful runtime observation is required")
    for key in ("network_policy_enforced", "configuration_rollback_only",
                "migration_before_apps", "cluster_deleted"):
        if record[key] is not True:
            raise ValueError("required qualification/cleanup gate missing")
    if record["cloud_provisioned"] is not False or record["errors"] != []:
        raise ValueError("cloud claim or incomplete runtime must not pass")
    if record["simulation"] != "three labelled workers on one host; local NetworkPolicy allow/deny probes":
        raise ValueError("runtime limitations must be explicit")
    for key in ("baseline_revision", "candidate_revision", "application_source"):
        if not isinstance(record[key], str) or not re.fullmatch(r"[0-9a-f]{40}", record[key]):
            raise ValueError("immutable revisions required")
    if record["baseline_revision"] == record["candidate_revision"]:
        raise ValueError("two distinct config revisions required")
    if not re.fullmatch(r"ghcr\.io/talisman36935/report-workshop@sha256:[0-9a-f]{64}", record["image"]):
        raise ValueError("immutable image required")
    start, finish = (datetime.fromisoformat(record[k]) for k in ("started_at", "finished_at"))
    if start.utcoffset() is None or finish.utcoffset() is None or not 0 < (finish - start).total_seconds() < 1800:
        raise ValueError("bounded timezone-aware runtime required")
    names = ("baseline", "candidate", "rollback", "drift-repaired")
    phases = record["phases"]
    if len(phases) != 4:
        raise ValueError("all four application phases required")
    seen = set()
    for phase, name in zip(phases, names):
        revision = record["candidate_revision" if name == "candidate" else "baseline_revision"]
        if set(phase) != {"phase", "revision", "jobs"} or phase["phase"] != name or phase["revision"] != revision:
            raise ValueError("invalid phase or observed revision")
        if len(phase["jobs"]) != 3:
            raise ValueError("each phase must snapshot exactly three jobs")
        for job in phase["jobs"]:
            if not re.fullmatch(r"[0-9a-f]{32}", job) or job in seen:
                raise ValueError("phase job IDs must be valid and globally unique")
            seen.add(job)
    expected_permissions = {"configmaps": True, "deployments.apps": True, "secrets": False,
        "serviceaccounts": False, "roles.rbac.authorization.k8s.io": False,
        "namespaces": False, "clusterroles": False}
    if record["permissions"] != expected_permissions:
        raise ValueError("delegation boundary changed")
    if record["controller_denial"] != {"ready": False, "reason": "ReconciliationFailed", "forbidden_observed": True}:
        raise ValueError("actual controller denial required")
    expected_probes = {label: {"exit_code": code, "expected": code, "target": "report-db-rw:5432"}
                       for label, code in (("allowed", 0), ("denied", 2))}
    if record["network_probes"] != expected_probes:
        raise ValueError("local network allow/deny probes required")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("supply one observation file")
    validate(json.loads(Path(sys.argv[1]).read_text()))
    print("passed: allowlisted twelve-job GitOps observation and cleanup")
