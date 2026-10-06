# Implementation record — 2026-10-03

## ADR 001: preserve the management plane through cleanup

The target architecture is temporary kind management -> Flux -> CAPI/CAPA EKS,
with ACK owning selected application S3/SQS resources. The management plane must
remain available, authorized and reconciling until dependent cloud deletions
complete. EKS management pivot is a later separate profile.

This first slice installs only Flux source-controller and kustomize-controller.
It reconciles a namespace and contract ConfigMap from an immutable Git commit.
The drift test proves the declared local objects return to Git state after an
out-of-band edit. It cannot prove CAPA, ACK or AWS deletion semantics.

## Ownership

| Resource | Initial owner | Future owner |
| --- | --- | --- |
| Local kind cluster and Flux installation | Bounded bootstrap script | Bootstrap remains an explicit exception |
| Local namespace/ConfigMap | Flux Kustomization | Flux |
| AWS account trust/controller identity | Not implemented | Explicit bootstrap, separately recoverable |
| EKS/network/nodes | Not implemented | CAPA under qualified ownership mode |
| Application bucket/queue | Not implemented | ACK S3/SQS |
| App source | GCP repo workload directory | Same pinned release in both clouds |
| Cleanup audit/TTL janitor | Not implemented | Independent external identity and inventory |

## Compatibility record

| Component | Pin | Qualification |
| --- | --- | --- |
| kind | v0.33.0 | Checksum-verified installer; hosted local integration gate |
| Kubernetes node | v1.35.8, digest in local script | Local profile only, not EKS version selection |
| Flux | v2.9.6 | Local Git source/Kustomization/drift test |
| CAPI / CAPA | v1.13.4 / v2.13.1 | Synthetic renders match pinned served CRD schemas; controllers/cloud unqualified |
| ACK S3 / SQS | Not selected | Selected APIs/controller identity still require qualification |

Published release checksums detect download corruption; they are fetched from the
same release origin and do not independently establish publisher authenticity.
Controller image signature verification and provenance remain future hardening.

## Evidence and progress

The hosted Validate workflow runs the local integration only for pushed main
commits; pull requests still receive static lifecycle/shell checks. The pinned
source must exist publicly for Flux to fetch it. Neither job has cloud access.
Success logs contain the source revision and observed drift assertion; this is
test evidence, not the final versioned portfolio evidence bundle.

Next: complete controller/ACK compatibility qualification, credential lifetime
design and externally durable run inventory; implement independent cleanup before
qualifying a bounded AWS create/run/delete cycle. No cloud readiness is claimed.

The SNS lifecycle publisher now emits six allowlisted run events through the
parameterized alert topic. It is a notification adapter only; no scheduler,
cloud-run workflow or independent janitor exists, and delivery is unqualified.
