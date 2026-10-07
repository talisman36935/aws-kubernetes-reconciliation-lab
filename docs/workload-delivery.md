# Shared adapter and Flux delivery boundary

The shared source owns the Pub/Sub/GCS and SQS/S3 adapters and delivery renderer.
AWS consumes its immutable source and image in `workload/source.json`; it does not
maintain a second application implementation. The delivery entry point requires
a clean checkout of exactly that commit and a release record matching both pins.
The current source pin is GCP source `2202e13962914f71e56b146ff7632282b9d04492` and
image index `ghcr.io/talisman36935/report-workshop@sha256:3c08b2754404fdc14dda81ee4e0bc9f9f640a3223ccd89988f19e74250c41816`.
That exact source passed GCP Validate (`37687488181`) and publish/native-ARM/
hosted-kind HA qualification (`37687979581`). Anonymous verification checked
AMD64/ARM64 runtime content. The source-scoped records are in the
[GCP qualification observation](https://github.com/talisman36935/gcp-platform-delivery-lab/tree/main/docs/observations/2202e13).
The HA experiment used three simulated workers on one hosted machine; no cloud was
provisioned and no cloud-zone failure or signature verification was established.
The previous source lock's AWS fixture validation passed at
[37521913969](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37521913969).
Its hosted promotion/rollback experiment passed at
[37522142251](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37522142251);
its exact per-phase source/image and gate results are in
[`observations/bed9efd/workload-gitops.json`](observations/bed9efd/workload-gitops.json).
These are historical consumer qualifications for the prior source/image pair. The
current lock's hosted source/image promotion, rollback, drift, RBAC, network and
cleanup qualification passed at
[37690806373](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37690806373);
its allowlisted observation is archived at
[`observations/a9ad22e/workload-gitops.json`](observations/a9ad22e/workload-gitops.json).
The prior AWS record before that is archived at
[`observations/372f432/workload-gitops.json`](observations/372f432/workload-gitops.json).
Prior AWS delivery runs remain historical evidence. None of these runs is live AWS
or EKS/CAPA/ACK qualification.

The local `management/workload-test` platform/migration/app resources are derived
from the locked shared renderer. When advancing the lock, check out that exact
clean shared commit and run `scripts/check-workload-fixture.py --shared-source
PATH --write`; this regenerates only those shared-derived groups and retains the
explicit candidate test marker. The root health contract and local network/denial
overlays remain separately owned and unchanged. The same command without `--write`
is the parity check used by Validate.

```sh
python3 scripts/render-workload-delivery.py \
  --shared-source PINNED_SHARED_CHECKOUT --release image-release.json \
  --storage-class QUALIFIED_CSI_CLASS --output profiles/delivery
```

`--backend aws --settings NONSECRET_RESOURCE_HANDOFF.json` selects existing London
SQS/S3 resources and the scoped IAM role. The queue URL and role account must match.
No keys, session tokens or signed URLs belong in the handoff. This command never
creates cloud resources, changes a Git root or applies Kubernetes objects.

The generated root graph uses `platform -> migrations -> apps`, ready-instance DB
health, a Deployment health gate requiring observed generation plus updated,
ready and available replica counts to match desired replicas, read-only schema
init gates and namespace-scoped application impersonation. The opt-in local AWS
fixture checker enforces exact CEL parity with the shared renderer and rejects
missing or weakened health checks.
The shared source now assigns separate `report-api`, `report-worker` and
`report-migrate` Kubernetes service accounts, with token automount disabled for
each; provider workload identity is worker-only in cloud profiles. The AWS local
fixture carries the account separation but no cloud annotations, projected cloud
tokens, or cloud credentials. This is manifest-level separation, not live IAM
qualification.
Platform owns database, workload identity, quota and default-deny policy. App rights
exclude Secrets, ServiceAccounts, RBAC and cluster resources. Existing Flux roots
remain contract-only. Provider/CNI/API/peer/metadata/telemetry policies and workload
IAM require explicit qualification; the rendered candidate is intentionally blocked,
not an operational EKS profile. The [separate hosted application experiment](application-gitops.md)
now qualifies local delivery/configuration rollback/negative-RBAC and one policy
path with explicit local networking and Deployment health extensions. This does
not qualify the generic blocked cloud tree or activate current Flux roots.

Queue delivery is at least once. DB publication/processing tokens fence state;
workers create attempt/hash-specific S3 objects, atomically select a reference and
JSONB report, then delete the message receipt. Terminal redelivery does not recompute.
Object-before-commit can leave an orphan; an independent sweep/export/cleanup owner
is still required. HTTP currently reads the committed JSONB report, not S3.

Do not switch backends against an existing backlog or purge a live queue. DLQ,
redrive permissions, cloud ownership/IAM, bucket region/version deletion and TTL
remain activation gates. SDK/protocol-double tests are not live AWS qualification.
Only migrate/rollback between capability-compatible releases; additive database
migrations are not automatically reversed on a Git rollback.
