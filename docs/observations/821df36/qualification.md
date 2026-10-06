# Runtime pass, observation alias defect — 2026-10-06

[Run 37442671990](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37442671990)
passed runtime checks at candidate `821df36881e03ae80545ff9dcbc298b0da052c80`,
baseline `e338078`: migration ordering, exact source revisions, three ready
API/worker replicas, golden reports through promotion/config rollback/drift repair,
direct permission checks, real controller denial, allowed/denied network probes
and cluster deletion. Network and Deployment health fixes are runtime-confirmed.

Independent artifact inspection found a Python aliasing bug: the first phase's
jobs field points to the cumulative list, so later additions changed it from three
IDs to nine. There are twelve distinct actual jobs, but this is **not a qualified
phase-local observation**. Preserve this original artifact; do not silently rewrite
its counts or infer nine baseline jobs. Runtime checks passed, evidence validation
did not meet the intended shape. No CI failure is being hidden or relabelled.

Remediation snapshots each phase list and adds an independent allowlist/four-phase/
twelve-unique-job/gate validator plus alias regression tests before artifact
qualification. A fresh reviewed run must produce valid evidence. No cloud access,
resources or spending were involved. Configuration rollback did not change binaries
or reverse schema migrations; policy probes cover one local DB path only.
