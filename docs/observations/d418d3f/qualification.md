# Qualified application GitOps observation — 2026-10-06

[Qualify application GitOps 37444041498](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37444041498)
passed runtime and independent evidence validation at candidate
`d418d3ffbf37d3021cf9fb784415af307db2da9e`, baseline
`e338078bf53da0195033299c8a1dccd03f31d638`.
Both inputs had passing Validate runs (37443765302 / 37442289689).
Application source/image remained the qualified `0e0a613` / `sha256:505f63c...`.

The adjacent original observation has exactly three unique jobs per phase and
twelve globally unique jobs. Migration completed before app Deployment creation;
Flux reported each expected immutable source revision and each phase had three
ready API/worker replicas and the pinned image. All new reports matched the golden
output; each later phase reread all previously acknowledged reports. Promotion,
return to baseline, ConfigMap/pod-template drift repair and source readiness passed.

The impersonated reconciler could create ConfigMaps/Deployments but could not
create Secrets, ServiceAccounts, Roles, Namespaces or ClusterRoles. An actual
Flux attempt to create a forbidden Namespace returned Ready=False,
ReconciliationFailed/forbidden, and the Namespace remained absent. The permitted
DB reachability probe returned 0; the default-denied probe returned no-response 2.
Migration/app wait gates remained enabled; RBAC was not widened. Cluster deletion
passed. No credentials, raw logs or controller error messages enter this record.

## Audit trail

| Attempt | Outcome | Remediation / verification |
| --- | --- | --- |
| 37437874482 at `68ae455` | Platform progressing; app dependencies blocked; exact cause not captured; cleanup passed | Diagnostics `0531efd`, Validate 37439045667; retained [record](../68ae455/qualification.md) |
| 37439207586 at `0531efd` | One ready DB primary, HTTP status communication error; cleanup passed | Scoped local network overlay `cd0c233`, Validate 37440285762; DB/migration/replicas confirmed healthy in next run; [record](../0531efd/qualification.md) |
| 37440708542 at `c548f3b` | Actual app pods ready but Flux app HealthCheckFailed; cleanup passed | Explicit Deployment CEL `e338078`, Validate 37442289689; later runtime passes confirm fix; [record](../c548f3b/qualification.md) |
| 37442671990 at `821df36` | All runtime gates passed, but baseline phase list aliased later jobs | Snapshot/independent validator `d418d3f`, Validate 37443765302; current fresh record passes; [unaltered observation/caveat](../821df36/qualification.md) |
| 37444041498 at `d418d3f` | Runtime, correct twelve-job observation, permission/network gates and cleanup passed | Current qualified observation |

Three labelled workers share one hosted machine and local-path storage. Policy
probes establish one local DB allow/deny path, not full isolation or a cloud CNI
claim. Rollback changes configuration only, not binaries or schemas. This is not
Config Sync/EKS/GCP/IAM/SQS/S3/physical-zone HA qualification, a cloud teardown audit
or a signed durable Labs bundle. Default roots and generic cloud profiles remain
inactive/blocked. Live cloud, provider overlays, independent cleanup/TTL/cost
protection, full telemetry and portfolio ingestion remain outstanding.
