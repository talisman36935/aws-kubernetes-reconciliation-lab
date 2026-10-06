"""Validate the allowlisted successful local GitOps observation, not a signature."""

from datetime import datetime
import json
from pathlib import Path
import re
import sys


def validate(record):
    legacy_fields = {"verification", "result", "started_at", "finished_at", "baseline_revision",
              "candidate_revision", "application_source", "image", "cloud_provisioned",
              "network_policy_enforced", "simulation", "configuration_rollback_only", "phases",
              "permissions", "controller_denial", "migration_before_apps", "cluster_deleted",
              "errors", "network_probes"}
    release_fields = legacy_fields | {"baseline_application_source", "baseline_image",
                                      "application_source_rollback"}
    upgraded = set(record) == release_fields
    if set(record) not in (legacy_fields, release_fields):
        raise ValueError("observation fields must match the allowlist")
    if record["verification"] != "hosted-kind-flux" or record["result"] != "passed":
        raise ValueError("a complete successful runtime observation is required")
    for key in ("network_policy_enforced", "migration_before_apps", "cluster_deleted"):
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
    source_changed = False
    if upgraded:
        if not re.fullmatch(r"[0-9a-f]{40}", record["baseline_application_source"]):
            raise ValueError("immutable baseline application source required")
        if not re.fullmatch(r"ghcr\.io/talisman36935/report-workshop@sha256:[0-9a-f]{64}",
                            record["baseline_image"]):
            raise ValueError("immutable baseline image required")
        source_changed = (record["baseline_application_source"], record["baseline_image"]) != (
            record["application_source"], record["image"])
        if record["configuration_rollback_only"] is not (not source_changed):
            raise ValueError("rollback classification does not match immutable release inputs")
        if record["application_source_rollback"] is not source_changed:
            raise ValueError("source/image rollback evidence does not match immutable release inputs")
    elif record["configuration_rollback_only"] is not True:
        raise ValueError("legacy configuration-only observation must retain its original contract")
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
        phase_fields = {"phase", "revision", "jobs"}
        if upgraded:
            phase_fields |= {"application_source", "image"}
        if set(phase) != phase_fields or phase["phase"] != name or phase["revision"] != revision:
            raise ValueError("invalid phase or observed revision")
        if upgraded:
            baseline_phase = name != "candidate"
            expected_source = (record["baseline_application_source"] if baseline_phase
                               else record["application_source"])
            expected_image = record["baseline_image"] if baseline_phase else record["image"]
            if phase["application_source"] != expected_source or phase["image"] != expected_image:
                raise ValueError("phase source/image does not match expected promotion or rollback")
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
