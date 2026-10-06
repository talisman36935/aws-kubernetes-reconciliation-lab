# Hosted application GitOps experiment

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

Modern kind has built-in NetworkPolicy support; the original assumption that it
did not enforce policies was incorrect and contributed to the first failed runs.
The local overlay and allow/deny probes must pass before claiming local policy
behavior. This is not an activated EKS profile. Physical-zone HA, CSI deletion, live IAM/SQS/S3,
Config Sync runtime, Cloud Deploy, binary/schema rollback, cloud budgets/TTL and
portfolio ingestion remain separate gates. Runtime results must be recorded before
claiming this experiment passed.

Impersonation and source pinning follow the operational contracts in the official
[Flux Kustomization documentation](https://fluxcd.io/flux/components/kustomize/kustomizations/)
and [GitRepository documentation](https://fluxcd.io/flux/components/source/gitrepositories/).
Required operator connectivity follows [CNPG 1.30 networking](https://cloudnative-pg.io/docs/1.30/networking/).
