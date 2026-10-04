"""Render one bounded EKS intent. Performs no cloud or Kubernetes API writes."""

import argparse
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re

from preflight import validate


def render(intent: dict, *, kubernetes_version: str, operator_cidr: str,
           instance_type: str, control_plane_role: str, node_role: str,
           identity_name: str, now: datetime) -> dict:
    validate(intent, now)
    network = ipaddress.ip_network(operator_cidr, strict=True)
    if network.version != 4 or network.prefixlen == 0:
        raise ValueError("operator CIDR must be restricted IPv4")
    if not re.fullmatch(r"1\.[0-9]{2}", kubernetes_version):
        raise ValueError("supply an explicit EKS minor version; availability is a live gate")
    if not re.fullmatch(r"[a-z][a-z0-9]*\.[a-z0-9]+", instance_type):
        raise ValueError("supply an explicitly approved instance type")
    for role in (control_plane_role, node_role):
        if not re.fullmatch(r"lab-[A-Za-z0-9_-]{1,59}", role):
            raise ValueError("IAM role names must use the lab- namespace")
    if not re.fullmatch(r"lab-[a-z0-9-]{1,50}", identity_name):
        raise ValueError("select an explicit lab controller identity")
    name = intent["run_id"]
    labels = {"portfolio.whitt.uk/owner": "portfolio-lab",
              "portfolio.whitt.uk/run-id": name}
    annotations = {"portfolio.whitt.uk/expires-at": intent["expires_at"],
                   "portfolio.whitt.uk/budget-usd": str(intent["budget_usd"])}

    def obj(api, kind, object_name, spec=None):
        metadata = {"name": object_name, "labels": dict(labels),
                    "annotations": dict(annotations)}
        if kind != "Namespace":
            metadata["namespace"] = name
        value = {"apiVersion": api, "kind": kind, "metadata": metadata}
        if spec is not None:
            value["spec"] = spec
        return value

    control = name + "-control-plane"
    pool = name + "-pool"
    tags = {"portfolio-owner": "portfolio-lab", "portfolio-run": name,
            "portfolio-expires-at": intent["expires_at"]}
    items = [
        obj("v1", "Namespace", name),
        obj("cluster.x-k8s.io/v1beta1", "Cluster", name, {
            "clusterNetwork": {"pods": {"cidrBlocks": ["192.168.0.0/16"]}},
            "infrastructureRef": {"apiVersion": "infrastructure.cluster.x-k8s.io/v1beta2",
                                  "kind": "AWSManagedCluster", "name": name},
            "controlPlaneRef": {"apiVersion": "controlplane.cluster.x-k8s.io/v1beta2",
                                "kind": "AWSManagedControlPlane", "name": control},
        }),
        obj("infrastructure.cluster.x-k8s.io/v1beta2", "AWSManagedCluster", name, {}),
        obj("controlplane.cluster.x-k8s.io/v1beta2", "AWSManagedControlPlane", control, {
            "region": intent["region"], "version": kubernetes_version,
            "roleName": control_plane_role, "sshKeyName": "",
            "identityRef": {"kind": "AWSClusterRoleIdentity", "name": identity_name},
            "network": {"vpc": {"cidrBlock": "10.60.0.0/16",
                               "availabilityZoneUsageLimit": 2,
                               "availabilityZoneSelection": "Ordered"}},
            "endpointAccess": {"public": True, "private": True,
                               "publicCIDRs": [str(network)]},
            "additionalTags": dict(tags),
        }),
        obj("cluster.x-k8s.io/v1beta1", "MachinePool", pool, {
            "clusterName": name, "replicas": 1,
            "template": {"spec": {
                "clusterName": name,
                "bootstrap": {"configRef": {
                    "apiVersion": "bootstrap.cluster.x-k8s.io/v1beta2",
                    "kind": "NodeadmConfig", "name": pool}},
                "infrastructureRef": {
                    "apiVersion": "infrastructure.cluster.x-k8s.io/v1beta2",
                    "kind": "AWSManagedMachinePool", "name": pool},
            }},
        }),
        obj("infrastructure.cluster.x-k8s.io/v1beta2", "AWSManagedMachinePool", pool, {
            "amiType": "AL2023_x86_64_STANDARD", "instanceType": instance_type,
            "roleName": node_role, "capacityType": "onDemand",
            "scaling": {"minSize": 1, "maxSize": 1}, "additionalTags": dict(tags),
        }),
        obj("bootstrap.cluster.x-k8s.io/v1beta2", "NodeadmConfig", pool, {}),
    ]
    return {"apiVersion": "v1", "kind": "List", "items": items}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intent", type=Path)
    for flag in ("kubernetes-version", "operator-cidr", "instance-type",
                 "control-plane-role", "node-role", "identity-name"):
        parser.add_argument("--" + flag, required=True)
    args = parser.parse_args()
    result = render(
        json.loads(args.intent.read_text()),
        kubernetes_version=args.kubernetes_version, operator_cidr=args.operator_cidr,
        instance_type=args.instance_type, control_plane_role=args.control_plane_role,
        node_role=args.node_role, identity_name=args.identity_name,
        now=datetime.now(timezone.utc),
    )
    print(json.dumps(result, indent=2, allow_nan=False))
