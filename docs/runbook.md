# Safety and cloud activation gates

## Static run intent

An illustrative intent (update expiry before validation):

```json
{
  "run_id": "lab-example",
  "account_id": "123456789012",
  "region": "eu-west-2",
  "expires_at": "2026-10-03T20:00:00Z",
  "budget_usd": 10
}
```

The account is a fictional format example, not a target. Exactly these five
fields are accepted. Expiry must be timezone-aware, in the future and no more
than four hours away. The $100 ceiling only bounds a declared intent; it does
not authorize expenditure or enforce cloud billing. The validator performs no
AWS API calls and region syntax is not proof of service availability.

## Required before cloud execution

Miles explicitly requested an access reminder before activation. Prompt for the
choices below when local work reaches that boundary; never infer spending approval
from available credentials. Prefer OIDC/federation and do not request pasted access
keys in chat. This reminder does not block independent credential-free work.

1. Choose an approved dedicated AWS account/region, budget and run lifetime.
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
cloud-verified experiments and dormant environments. The original
[evidence contract](plan/portfolio-demos/evidence-and-labs.md) describes the
required provenance and observation timestamps. No website integration is shipped
in this first repository slice.
