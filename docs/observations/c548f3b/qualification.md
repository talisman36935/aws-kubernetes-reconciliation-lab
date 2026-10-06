# Network fix and application health gate — 2026-10-06

[Run 37440708542](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37440708542)
at `c548f3b15607702d9bd9a83dce1f4b2f8ce9aaee`, baseline `cd0c233`, failed
the runtime step at baseline-reconciliation (CalledProcessError).

The scoped network overlay resolved the prior DB readiness failure: platform
Ready/Healthy True, three DB instances healthy, all PVCs Bound, migration
Ready/Healthy True and Job Complete. Three API and three worker pods were Ready;
all schema init gates completed. App Kustomization was HealthCheckFailed. Cleanup
passed. No smoke/promotion/rollback phase completed: this is not overall success.

The pinned kustomize-controller v1.9.6 depends on fluxcd/cli-utils v1.2.3. Its
[Deployment status reader](https://github.com/fluxcd/cli-utils/blob/v1.2.3/pkg/kstatus/polling/statusreaders/deployment.go)
recursively reads ReplicaSets/Pods, while the writer Role lacks those reads.
This explains a concrete health-contract mismatch, though this failed artifact
does not retain the raw controller error to establish its exact message.
Remediation uses a local-root Deployment CEL reader requiring current observed
generation and all replicas updated/ready/available, without broadening RBAC or
disabling wait. Runtime verification is required before claiming this fixed the run.

The original generic cloud root remains blocked and unchanged; the local root
extension must be explicitly adopted/qualified before cloud activation. No cloud
credentials, resources or spending were involved. All failed records remain history.
