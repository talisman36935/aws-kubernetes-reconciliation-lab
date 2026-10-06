# First application GitOps attempt — 2026-10-06

Qualify application GitOps [37437874482](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37437874482)
at candidate `68ae455d4de9ef46e82ffa1329858063771f5caf`, baseline
`ddb35e0c424c9f6b2002fb31afd7a62afd4754dc`, failed step
Reconcile, promote, roll back, repair drift and deny escalation.

The baseline-reconciliation stage returned CalledProcessError. Platform
Ready/Healthy were Unknown/Progressing; migration and app dependencies remained
unready. No application phase completed. The exact database/platform cause is
not established by this run's diagnostics. The adjacent observation confirms
cluster deletion. No cloud resources were provisioned.

Remediation adds bounded, allowlisted pod/container/PVC/database/event-category
diagnostics before cleanup. Do not claim app GitOps qualification or silently
reinterpret this failure as successful apply. Follow-up runs are separate evidence.
