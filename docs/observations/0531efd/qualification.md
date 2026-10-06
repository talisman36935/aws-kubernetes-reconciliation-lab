# Diagnostic application GitOps attempt — 2026-10-06

[Run 37439207586](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37439207586)
at `0531efdc33e490261803e71b2daad5bc0033504b`, baseline `ddb35e0`, failed
Reconcile, promote, roll back, repair drift and deny escalation: baseline DB wait
timed out. Initdb completed, storage was Bound and one primary was Running/Ready;
CNPG reported Instance Status Extraction Error: HTTP communication issue, one
ready instance and no replicas. Requests/limits existed; no quota or scheduling
failure category was captured. Cluster deletion passed. No app phase completed.

The test's assumption that modern kind did not enforce NetworkPolicy was wrong.
Its default-deny candidate lacks operator status ingress and DB peer/API/DNS
allowances, consistent with the observed status communication failure. Remediation
adds a scoped local overlay and observed API /32 substitutions, retains deny and
requires explicit allowed/denied TCP probes. A subsequent pass is required to
confirm the causal fix. No broad Internet allowance or cloud profile activation.

The old observation's network_policy_enforced=false is an unverified initial
declaration, not measured proof of absent enforcement. Preserve this failed record,
but use later probe evidence for the network claim. The
[kind release history](https://github.com/kubernetes-sigs/kind/releases/tag/v0.24.0)
records built-in policy support; [CNPG networking](https://cloudnative-pg.io/docs/1.30/networking/)
documents operator/instance connectivity. No cloud credentials/resources involved.
