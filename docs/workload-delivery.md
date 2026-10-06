# Shared adapter and Flux delivery boundary

The shared source owns the Pub/Sub/GCS and SQS/S3 adapters and delivery renderer.
AWS consumes its immutable source and image in `workload/source.json`; it does not
maintain a second application implementation. The delivery entry point requires
a clean checkout of exactly that commit and a release record matching both pins.

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
health, read-only schema init gates and namespace-scoped application impersonation.
Platform owns database, workload identity, quota and default-deny policy. App rights
exclude Secrets, ServiceAccounts, RBAC and cluster resources. Existing Flux roots
remain contract-only. Provider/CNI/API/peer/metadata/telemetry policies and workload
IAM require explicit qualification; the rendered candidate is intentionally blocked,
not an operational EKS profile. Live app GitOps/rollback/negative-RBAC evidence is
still pending, distinct from the passing local contract drift/cleanup test.

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
