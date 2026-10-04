# EKS rendering and provider compatibility spike

The lab can now render one bounded EKS desired-state set and check it against
checksum-pinned served CRD schemas. This is preparation for the cloud vertical
slice; controller installation, webhook/CEL admission and AWS behavior remain
unqualified.

## Selected source basis

CAPA v2.13.1's go.mod uses CAPI v1.13.4 and Kubernetes libraries v0.35.4. That is
the version pair selected for this schema spike, rather than independently taking
the latest CAPI release. The existing kind v1.35.8 profile is still qualified only
for Flux. A future controller installation must verify the full management stack.

The renderer follows the maintained EKS managed-machine-pool template:

- CAPI Cluster and MachinePool.
- CAPA AWSManagedCluster and AWSManagedControlPlane.
- CAPA AWSManagedMachinePool with one AL2023 x86 node.
- CAPA NodeadmConfig for bootstrap.

The generated namespace is the run ID. All objects carry owner/run labels and
expiry/budget annotations; AWS resources receive declared owner/run/expiry tags.
The controller identity and EKS/node IAM roles must already exist under their
declared bootstrap owner. CAPA owns the generated VPC, with two selected AZs;
network/NAT cost and quota must be evaluated before activation.

The API endpoint enables private access and limits public access to the explicit
operator CIDR. Node count/scaling are fixed to one for the first slice. EKS minor
version and machine size require explicit inputs; syntax validation does not
establish regional support, availability or affordability.

## Credential-free qualification

```sh
python3 -m pip install PyYAML==6.0.2 jsonschema==4.23.0
python3 -m unittest discover -s lifecycle -v
python3 scripts/check-eks-schemas.py
```

The checker downloads only public release artifacts, verifies the hashes in
[pins.json](../management/compatibility/pins.json), and validates six synthetic
custom resources against their served-version schemas. Downloads are cached in
the ignored .cache directory. It makes no AWS or Kubernetes API calls.

The synthetic account, documentation CIDR and machine size in the fixture are
test inputs. They do not select Miles's cloud environment. No GitOps source points
at a generated cloud render, so the ordinary local Flux test cannot provision EKS.

## Render an approved intent

```sh
python3 lifecycle/render_eks.py run-intent.json \
  --kubernetes-version APPROVED_MINOR \
  --operator-cidr APPROVED_CIDR \
  --instance-type APPROVED_TYPE \
  --control-plane-role lab-APPROVED_CONTROL_ROLE \
  --node-role lab-APPROVED_NODE_ROLE \
  --identity-name lab-APPROVED_IDENTITY
```

The command prints a Kubernetes List. Review and retain it with the run inventory;
application to a management cluster is a later lifecycle step. The preflight
requires future expiry within four hours and a positive bounded budget intent.
Those fields do not enforce billing or prove AWS identity.

## What the KROPS review established

At reference commit d54acc2c5ba9d083ee0449f172559c0b4724894b, the AWS guide places
CAPA and ACK in the management plane, includes a management-cluster pivot, and
uses static encrypted controller profiles. Its default layout has three EKS
clusters across two regions and broad controller credential responsibilities.
Its workload paths were documented as empty at that revision.

This lab retains one temporary workload cluster and keeps kind through cleanup.
The shared Report Workshop workload, restricted identity/lifetime design and
independent audit are our remaining integration work. The upstream credential
and multi-cluster defaults are reference findings, not this lab's defaults.

## Qualification still required

Install the selected controllers and their certificate dependency, verify
management Kubernetes support, establish scoped/refreshable controller access,
add ACK S3/SQS compatibility, and qualify the full create/workload/export/delete
cycle. Build the independent inventory/audit/janitor before calling deletion
complete. Server admission, conversion behavior, IAM, AWS quotas and tag/audit
coverage cannot be established by JSON Schema.

References reviewed 2026-10-04:

- [CAPA v2.13.1 template](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/v2.13.1/templates/cluster-template-eks-managedmachinepool.yaml)
- [CAPA dependency versions](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/v2.13.1/go.mod)
- [CAPA managed control-plane API](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/v2.13.1/controlplane/eks/api/v1beta2/awsmanagedcontrolplane_types.go)
- [CAPA machine-pool API](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/v2.13.1/exp/api/v1beta2/awsmanagedmachinepool_types.go)
- [KROPS AWS guide](https://github.com/polarsquad/krops/blob/d54acc2c5ba9d083ee0449f172559c0b4724894b/docs/aws.md)
- [KROPS dependencies](https://github.com/polarsquad/krops/blob/d54acc2c5ba9d083ee0449f172559c0b4724894b/docs/dependencies.md)
