# Immutable workload release promotion and rollback — 2026-10-06

[Validate 37521913969](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37521913969)
and hosted qualification
[37522142251](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37522142251)
passed. The experiment started at AWS commit
`bba5671e7d0c741445da0b272563729d754affc0` and exercised candidate
`bed9efd1e2e0d563078f5535b9b5be8e2f88127d`.

Baseline GCP source/image were `32c98ffd9cacb528c2d017f7ea39b54536ca2211` /
`sha256:47c7464df5cb1d20ba05eeb391d211309919c477503316d7c8fcf6d4feb43fe5`.
Candidate source/image were `3b1abf3b791b4ab95f852c860786ca91d8c0a381` /
`sha256:dfba95425f82b619987f307e63e2e2720f9395a5a2c7836ec2d2a25f7d398d23`.
The four phases record the exact immutable source and image: baseline, candidate,
rollback to the old source/image, and drift repair to that baseline. Each phase
completed three unique synthetic jobs; previously accepted reports were reread.

Migration ordering, three ready API/worker replicas, idempotency and golden
reports passed. Delegated writes to ConfigMaps/Deployments succeeded while direct
and Flux-controller attempts to create Secrets, service accounts, RBAC or
cluster-scoped resources were denied. Local network probes allowed PostgreSQL
from the permitted workload and denied the disallowed probe. The named kind
cluster was deleted; no cloud resources were provisioned.

The previous
[configuration-only preflight rejection](../9fa2e75/qualification.md) and
[baseline-marker mismatch](../aa66120/qualification.md) remain recorded.
This qualification is local kind/Flux evidence only, not AWS/EKS, cloud identity,
or cloud cleanup qualification.
