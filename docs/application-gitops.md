# Hosted application release and GitOps experiment

## Current source-pin promotion — 2026-10-07

AWS Validate [37690653997](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37690653997)
passed for the source/image lock at `2202e139`. Hosted qualification
[37690806373](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37690806373)
passed baseline, candidate promotion, source/image rollback, and drift repair with
three golden jobs in each phase. The baseline used GCP source `3b1abf3` and its
immutable image; the candidate used source `2202e139` and image
`ghcr.io/talisman36935/report-workshop@sha256:3c08b2754404fdc14dda81ee4e0bc9f9f640a3223ccd89988f19e74250c41816`.
The [source-pinned observation](observations/a9ad22e/workload-gitops.json) records
all phase-local jobs and exact pins. The independent validator passed; source
rollback passed (not merely configuration rollback), migration preceded apps,
the impersonated controller was denied a Namespace create, the scoped API rights
were observed, the local database allow/deny probes returned expected exit codes,
and the cluster was deleted with no errors.

Two earlier attempts remain accurately recorded: [37689635673](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37689635673)
stopped before cluster creation because the candidate diff included a README edit
outside the qualification's allowlist; [37689903807](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37689903807)
ran the cluster and cleaned it up but exposed a mismatch between the baseline
fixture's `candidate` marker and the harness's hard-coded phase label. The harness
now derives and checks the synthetic marker from each exact source revision. These
results qualify hosted kind/Flux application behavior only, not AWS/EKS or cloud
services.

Prior source-pin run: [37522142251](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37522142251)
passed against baseline `bba5671e7d0c741445da0b272563729d754affc0` and candidate
`bed9efd1e2e0d563078f5535b9b5be8e2f88127d`. It promoted GCP source
`3b1abf3b791b4ab95f852c860786ca91d8c0a381` and image
`ghcr.io/talisman36935/report-workshop@sha256:dfba95425f82b619987f307e63e2e2720f9395a5a2c7836ec2d2a25f7d398d23`,
then rolled back to source `32c98ffd9cacb528c2d017f7ea39b54536ca2211` and image
`ghcr.io/talisman36935/report-workshop@sha256:47c7464df5cb1d20ba05eeb391d211309919c477503316d7c8fcf6d4feb43fe5`.
The allowlisted twelve-job result, with exact pins in all four phases, is archived
at [`observations/bed9efd/workload-gitops.json`](observations/bed9efd/workload-gitops.json).
AWS Validate passed at `37521913969`. The experiment also retained prior reports,
proved migration ordering, direct and controller RBAC denial, local network
allow/deny behavior, drift repair and named-cluster cleanup. It provisions no
cloud resources; this is hosted kind/Flux evidence, not AWS/EKS qualification.

The prior configuration-only run [37496120127](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37496120127)
remains archived at [`observations/372f432/workload-gitops.json`](observations/372f432/workload-gitops.json).

The prior qualified pin's run [37482370289](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37482370289)
and sanitized result remain archived at [the 18c7015 observation](observations/18c7015/qualification.md).

[Run 37444041498](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37444041498)
passed all runtime and independent observation gates. The
[qualified record and failure audit](observations/d418d3f/qualification.md) retain
exact source revisions, twelve phase-local jobs, permission/network results and
cleanup. Historical failures and the earlier aliased observation are not rewritten.

This opt-in experiment uses the qualified Report Workshop image with three API,
three worker and three CloudNativePG database instances in a disposable four-node
kind cluster on one GitHub runner. Flux fetches real public immutable Git commits
and applies the `management/workload-test` fixture. Default management roots are
unchanged. It creates no AWS/GCP resources and uses no cloud identity.

The fixture is derived from the locked shared Flux renderer with an explicit
`report-gitops` namespace, kind's `standard` local-path class and synthetic release
markers. CI checks that derivation. The platform owns namespace, quota, database,
identity and RBAC; the impersonated app reconciler owns only migration/app objects.
The dependency graph waits for ready database instances, then migration completion,
then applications. The harness observes actual migration and deployment timestamps.

The local root uses an explicit Deployment CEL health check requiring current
observed generation and all desired replicas updated, ready and available. Flux's
default Deployment status reader recursively reads ReplicaSets/Pods, which the
minimal writer Role intentionally does not allow. The CEL reader uses Deployment
status without adding those permissions; the harness separately checks real ready
replicas and golden reports. Wait/dependencies remain enabled. This is a deliberate
local root health extension; generic cloud roots still need an equivalent reviewed
health contract or scoped read-only health permissions before activation.

An explicit local network overlay preserves default-deny while allowing operator
status access (8000), DB/operator/app PostgreSQL traffic (5432), scoped DNS and DB
access to only this kind cluster's observed API service/endpoint /32 addresses.
Bootstrap supplies those nonsecret addresses through Flux post-build substitution;
the two Git revisions must share the same overlay. This is not a cloud overlay.

The manually dispatched **Qualify application GitOps** workflow requires baseline
and current-main candidate commits with passing Validate runs. The experiment:

1. Reconciles baseline and verifies exact controller source revisions, three ready
   replicas, immutable images, idempotency and golden reports.
2. Promotes to a real candidate Git commit that changes only pod-template release
   annotations and the release ConfigMap; verifies another set of reports and all
   previously acknowledged reports.
3. Returns the source to the baseline SHA and observes configuration rollback,
   rollout readiness and preserved reports. This is **not a binary/schema rollback**.
4. Changes a ConfigMap and API pod-template annotation out of band, then requires
   Flux repair and another successful application smoke check.
5. Checks allowed/denied API permissions and asks the actual impersonating Flux
   controller to create a forbidden Namespace. Ready must be false with a forbidden
   error and the Namespace must remain absent. This tests direct object rights,
   not comprehensive tenant isolation: deployment rights can mount existing
   namespace secrets and assume existing pod service accounts.
6. Requires a permitted synthetic pod to reach the DB service on 5432 and a denied
   pod to fail the same connection after a policy warmup. Probe images are pinned;
   no database credentials are used. This tests one local allow/deny path, not full
   network isolation or provider CNI equivalence.

Only allowlisted observations enter `output/workload-gitops.json`; kubeconfigs,
Secrets, raw command errors, controller messages and logs do not. A cleanup failure
cannot produce pass. The harness refuses an existing named cluster, restores the
prior kubeconfig environment and deletes only its own disposable cluster. Hosted
runner expiry is a fallback, not the cloud janitor/independent cleanup owner.
An independent validator rejects unknown/private fields, missing gates, aliased or
duplicate phase jobs, incorrect rollback revisions and missing allow/deny probes.
Each phase must contain exactly three unique jobs (twelve across the run). This
structural check is not cryptographic provenance or the future signed Labs bundle.

Modern kind has built-in NetworkPolicy support; the original assumption that it
did not enforce policies was incorrect and contributed to the first failed runs.
The local overlay and allow/deny probes must pass before claiming local policy
behavior. This is not an activated EKS profile. Physical-zone HA, CSI deletion, live IAM/SQS/S3,
Config Sync runtime, Cloud Deploy, binary/schema rollback, cloud budgets/TTL and
portfolio ingestion remain separate gates. A render or ordinary CI pass does not
replace this separately qualified runtime experiment.

Impersonation and source pinning follow the operational contracts in the official
[Flux Kustomization documentation](https://fluxcd.io/flux/components/kustomize/kustomizations/)
and [GitRepository documentation](https://fluxcd.io/flux/components/source/gitrepositories/).
Required operator connectivity follows [CNPG 1.30 networking](https://cloudnative-pg.io/docs/1.30/networking/).
