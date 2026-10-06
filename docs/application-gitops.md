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

Only allowlisted observations enter `output/workload-gitops.json`; kubeconfigs,
Secrets, raw command errors, controller messages and logs do not. A cleanup failure
cannot produce pass. The harness refuses an existing named cluster, restores the
prior kubeconfig environment and deletes only its own disposable cluster. Hosted
runner expiry is a fallback, not the cloud janitor/independent cleanup owner.

Kind's default kindnet **does not enforce NetworkPolicy**. The fixture keeps the
fail-closed candidate policies but this experiment does not qualify them; it is
not an activated EKS profile. Physical-zone HA, CSI deletion, live IAM/SQS/S3,
Config Sync runtime, Cloud Deploy, binary/schema rollback, cloud budgets/TTL and
portfolio ingestion remain separate gates. Runtime results must be recorded before
claiming this experiment passed.

Impersonation and source pinning follow the operational contracts in the official
[Flux Kustomization documentation](https://fluxcd.io/flux/components/kustomize/kustomizations/)
and [GitRepository documentation](https://fluxcd.io/flux/components/source/gitrepositories/).
