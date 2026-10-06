# Safety and cloud activation gates

## Ephemeral HA cloud execution policy

Follow the [ephemeral HA architecture and cost policy](architecture-cost.md)
before activation. London multi-zone HA, 4 GiB minimum-first Graviton nodes,
layered provider-specific alerts, a £5 gross per-run planning ceiling, £10 total
for the first GCP+AWS attempts, 60-minute maximum lifetime and immediate audited
cleanup are the approved starting policy. These are not provider-guaranteed
monetary caps; preflight cost coverage and alert delivery must pass before apply.
Existing topology/intent validators do not yet enforce the complete policy.

## Static run intent

An illustrative intent (update expiry before validation):

```json
{
  "run_id": "lab-example",
  "account_id": "123456789012",
  "region": "eu-west-2",
  "expires_at": "2026-10-06T20:00:00Z",
  "budget_gbp": 5
}
```

The account is a synthetic validator example; the £5 per-run budget and 60-minute
maximum now reflect the approved policy. Exactly these five fields are accepted.
Expiry must be timezone-aware, in the future and no more than 60 minutes away.
The validator performs no AWS API calls and does not enforce cloud billing.

## Required before cloud execution

Cloud execution requires an explicit access and spending review. Prompt for the
choices below when local work reaches that boundary; never infer spending approval
from available credentials. Prefer OIDC/federation and do not request pasted access
keys in chat. This reminder does not block independent credential-free work.

1. Choose the dedicated AWS account and confirm its billing currency; set the
   £5 gross-cost target and 60-minute run expiry. Configure actual-cost
   alerts at 25/50/75/90/100%, forecast alerts at 75/100% when available, and
   verify the SNS email subscription before provisioning. Use the parameterized
   [budget template](../lifecycle/budget-alerts.json); its email input is private,
   its amount is limited to £5, and notifications exclude trial credits. It is an
   account-wide monthly warning, not a per-run cap; do not use it without checking
   the account's other spend and billing-month boundary.
2. Verify caller identity and controller credential lifetime/refresh. A CI OIDC
   exchange alone does not give long-lived kind controllers a refresh path.
3. Qualify controller/CRD/API versions and least-privilege bootstrap IAM.
4. Implement external run inventory, ownership tags and explicit retained
   resources; keep these recoverable after loss of the management cluster.
5. Implement an independently operated janitor and scoped provider-side audit.
6. Record readiness conditions and assert a full create/workload/delete slice.

There is deliberately no cloud apply workflow or partially functional automatic
cleanup script. Current kind cleanup is **not an AWS cleanup implementation**.

## Future deletion order

Stop workload producers -> export evidence -> suspend/remove desired state ->
delete consumers and run-scoped data -> observe ACK deletion -> delete EKS through
CAPA -> independently audit AWS -> remove management last. Failed cleanup stays
failed/incomplete. Do not strip finalizers automatically or run account-wide
deletion commands. Audit EKS, compute, load balancers, NAT, disks, IPs, network
interfaces, buckets, queues and retained logs/images with declared coverage.

## Portfolio integration

The portfolio will consume sanitized immutable historical bundles, not live
credentials or public cluster-control endpoints. It must distinguish local tests,
cloud-verified experiments and dormant environments. Evidence must record source/image provenance, observation timestamps,
experiment results and independently verified cleanup. No website integration is shipped
in this first repository slice.
