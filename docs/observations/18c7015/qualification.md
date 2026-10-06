# AWS application GitOps qualification — 2026-10-06

[Hosted run 37482370289](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37482370289)
passed the hosted `kind`/Flux qualification and its independent evidence-shape
validator. The allowlisted observation is in `workload-gitops.json`.

The run consumed the exact GCP source `f531d2609bbd02c011af6028184eb80d393ee07e`
and immutable image index
`ghcr.io/talisman36935/report-workshop@sha256:0706b71b0771970044a927a3f9ab7c0552ec663c1c96affefdcdcb2d41e61a1e`.
It used the same source/image lock at baseline `ceb9ac01c42627323a24acb253ce5b6ad88606d5`
and candidate `18c7015814ce889d5d0b3cef9bfda92a92550247`.

Four phases each completed three unique jobs: baseline, configuration promotion,
configuration rollback, and drift repair. The runner verified migration-before-app
ordering, exact image pins, golden reports, direct permission boundaries, actual
Flux denial of Namespace creation, and a local NetworkPolicy database allow/deny
pair. The hosted cluster was deleted and the evidence records no errors.

This is an ephemeral single-host Kubernetes qualification, not an AWS account or
EKS/CAPA/ACK deployment. Three labelled workers do not establish physical-zone
separation; the network policy result does not establish a cloud CNI contract.
Binary/schema rollback, London resource provisioning, live IAM/SQS/S3 behavior,
budget guardrails and independent cloud cleanup remain unqualified.
