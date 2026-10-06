# Verification record

## Hosted application GitOps — 2026-10-06

[37444041498](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37444041498)
passed actual application baseline/promotion/configuration rollback/drift repair,
source/replica/image/golden report assertions, migration ordering, direct RBAC and
controller denial, local policy probes, independent observation validation and
cluster cleanup. See the [twelve-job record and full audit](observations/d418d3f/qualification.md).
Three simulated-zone workers share one host. No cloud resources were provisioned;
binary/schema rollback, Config Sync and EKS/cloud lifecycle remain unqualified.

## Initial foundation — 2026-10-03

Source: `02711fca85f1a1f82b493d580a83c1d1d944e129`.
[Hosted run 37145049038](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37145049038)
passed lifecycle negative tests, shell syntax/ShellCheck, and the real local
kind/Flux integration:

1. Flux fetched the exact public source revision.
2. The Kustomization became ready and ConfigMap owner equaled `flux`.
3. An out-of-band patch changed owner to `out-of-band`.
4. Reconciliation restored owner to `flux` and reported the expected revision.
5. Cleanup removed `portfolio-reconcile-control-plane`.

The run emitted:

```text
PASS: source revision 02711fca85f1a1f82b493d580a83c1d1d944e129 reconciled and out-of-band drift corrected.
Local kind/Flux evidence only; no EKS, CAPA or ACK claim.
Deleted nodes: ["portfolio-reconcile-control-plane"]
```

This authored record retains the result beyond CI log retention. It is not the
future signed/versioned portfolio evidence bundle or an AWS cleanup audit.
