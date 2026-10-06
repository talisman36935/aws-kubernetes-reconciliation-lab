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
- Three CAPA AWSManagedMachinePools with one AL2023 node each; ARM for
  t4g.medium (first candidate) or t4g.large (measured fallback), x86 for
  t3a.medium/t3a.large only when ARM is unavailable or incompatible.
- CAPA NodeadmConfig for bootstrap.

The generated namespace is the run ID. All objects carry owner/run labels and
expiry/budget annotations; AWS resources receive declared owner/run/expiry tags.
The controller identity and EKS/node IAM roles must already exist under their
declared bootstrap owner. CAPA owns the generated VPC, with three selected AZs;
network/NAT cost and quota must be evaluated before activation.

The API endpoint enables private access and limits public access to the explicit
operator CIDR. Each of three zone-specific groups has fixed min/max/desired size one. EKS minor
version and machine size require explicit inputs; syntax validation does not
establish regional support, availability or affordability.

## Credential-free qualification

```sh
python3 -m pip install PyYAML==6.0.2 jsonschema==4.23.0
python3 -m unittest discover -s lifecycle -v
python3 scripts/check-eks-schemas.py
```

The checker downloads only public release artifacts, verifies the hashes in
[pins.json](../management/compatibility/pins.json), and validates twelve synthetic
custom resources against their served-version schemas. Downloads are cached in
the ignored .cache directory. It makes no AWS or Kubernetes API calls.

The synthetic account, documentation CIDR and machine size in the fixture are
test inputs. They do not authorize a cloud run. No GitOps source points
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
requires future expiry within 60 minutes and a positive budget intent no greater
than £5. Those fields do not enforce billing or prove AWS identity.

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
