# AWS application GitOps qualification — 2026-10-06

[Hosted run 37496120127](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37496120127)
passed the `kind`/Flux application experiment and its independent observation
validator. The allowlisted record is archived in
[`workload-gitops.json`](workload-gitops.json).

The run used GCP source `32c98ffd9cacb528c2d017f7ea39b54536ca2211` and public
image index
`ghcr.io/talisman36935/report-workshop@sha256:47c7464df5cb1d20ba05eeb391d211309919c477503316d7c8fcf6d4feb43fe5`.
The source/image baseline is AWS commit
`bba5671e7d0c741445da0b272563729d754affc0`; candidate
`372f4325c8c308554443942649721eb68e70eddd` changes only the synthetic app release
markers. Both revisions passed AWS Validate (`37495547945`, `37495581270`).

Four phases completed three unique golden-report jobs each: baseline, app-config
promotion, configuration rollback, and drift repair. Migration-before-app ordering,
the exact image pin, twelve unique jobs, and cluster deletion were verified. The
delegated Flux controller was observed forbidden from creating a Namespace; its
API permissions allow ConfigMaps and Deployments but deny Secrets, ServiceAccounts,
Roles, Namespaces and ClusterRoles. The local DB network overlay passed the allowed
and denied PostgreSQL probes.

The fixture carries distinct `report-api`, `report-worker` and `report-migrate`
service accounts with token automount disabled; exact renderer parity and these
account assignments are checked by AWS Validate. This proves the local manifest
and GitOps contract only, not live cloud identity or IAM behavior.

This is ephemeral Kubernetes on one hosted runner with three labelled simulated
workers, not AWS account or EKS/CAPA/ACK qualification. It provisions no cloud
resources. Physical-zone separation, cloud CNI/CSI, SQS/S3 and IAM behavior,
London budget enforcement, independent cloud cleanup, and binary/schema rollback
remain unqualified.
