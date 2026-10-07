# Shared application source promotion — `a9ad22e`

AWS [Validate run 37689716429](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37689716429)
and [hosted GitOps run 37690806373](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37690806373)
passed for GCP source `2202e13962914f71e56b146ff7632282b9d04492` and immutable
image `ghcr.io/talisman36935/report-workshop@sha256:3c08b2754404fdc14dda81ee4e0bc9f9f640a3223ccd89988f19e74250c41816`.
The [allowlisted observation](workload-gitops.json) records exact Git and image
pins for baseline, promotion, source/image rollback and drift-repair phases, with
three unique golden jobs in each phase.

Migration completed before application rollout. The actual Flux reconciler had
ConfigMap/Deployment write permission but was denied Secrets, ServiceAccounts,
RBAC and Namespace writes; a real forbidden Namespace reconciliation remained
unready and created no Namespace. The local DB allow/deny probes returned their
expected results. The independent artifact validator passed and the disposable
kind cluster was deleted with no reported errors.

This was a hosted kind/Flux experiment with three labelled workers on one machine.
It provisions no AWS resources and establishes no EKS, cloud IAM, cloud network,
storage, physical-zone, cloud-cost or cloud-cleanup qualification. Source rollback
was exercised in this local harness; it is not a claim that additive database
migrations are automatically reversible.
