# AWS Kubernetes Reconciliation Lab

[![Validate](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/workflows/validate.yaml/badge.svg)](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/workflows/validate.yaml)

A Kubernetes reconciliation lab: Git-driven controller reconciliation, observable
failure/recovery, and eventual **audited deletion** of a temporary AWS environment.
Companion: [GCP Platform Delivery Lab](https://github.com/talisman36935/gcp-platform-delivery-lab).

**Status: local reconciliation foundation, not an EKS implementation.**
The EKS rendering spike now checks a bounded desired-state set against pinned
CAPI/CAPA CRD schemas; controller and cloud qualification are still pending.
This first slice proves kind/Flux desired-state reconciliation and drift repair.
CAPI/CAPA, ACK S3/SQS, AWS identity, independent teardown audit and TTL janitor
remain explicit next milestones. No AWS resources are provisioned by current code.

## Run the local reconciliation test

Requirements: Linux amd64/arm64, Docker, curl, tar, sha256sum, network access, and
sufficient local capacity for a disposable Kubernetes cluster. Prefer hosted CI
on a small/shared host. Never point this experiment at an existing cluster.

```sh
git clone https://github.com/talisman36935/aws-kubernetes-reconciliation-lab.git
cd aws-kubernetes-reconciliation-lab
bash scripts/install-local-tools.sh "$PWD/.tools"
export PATH="$PWD/.tools:$PATH"
bash scripts/local-reconcile.sh "$(git rev-parse HEAD)"
```

Use a commit already pushed to the public repository: Flux fetches that exact SHA.
The script creates only `portfolio-reconcile`, refuses to overwrite an existing
cluster with that name, installs pinned Flux controllers, reconciles a ConfigMap,
changes it out-of-band, then asserts Flux repaired it and applied the correct
source revision. An EXIT trap removes that disposable cluster and its kubeconfig.
If the process is forcibly killed, inspect `kind get clusters` and deliberately
remove only `portfolio-reconcile` after confirming it is this test's cluster.

## Run the shared application

The GCP repo's [workload quickstart](https://github.com/talisman36935/gcp-platform-delivery-lab#try-the-application-locally)
is the single source of Report Workshop. [workload/source.json](workload/source.json)
pins a verified source revision instead of maintaining a divergent copy.
To reproduce that exact application version:

```sh
git clone https://github.com/talisman36935/gcp-platform-delivery-lab.git
cd gcp-platform-delivery-lab
git checkout --detach 2c12b6377a76b2e803c75a98c4af51d1af8f38c3
cd workload
docker compose up --build -d
python3 smoke.py
docker compose down
```

There is not yet a published application image or an AWS workload deployment.

The pinned source includes [local metrics and evidence recording](https://github.com/talisman36935/gcp-platform-delivery-lab/blob/2c12b6377a76b2e803c75a98c4af51d1af8f38c3/docs/local-observability.md),
durable API/worker tracing, bounded profiling and compiled regression/recovery.
The replica/SIGKILL recovery experiment passed [hosted validation at de55de7](https://github.com/talisman36935/gcp-platform-delivery-lab/actions/runs/37385769512).
The pinned source additionally includes the dormant three-instance database profile;
see [application replica and database contracts](https://github.com/talisman36935/gcp-platform-delivery-lab/blob/2c12b6377a76b2e803c75a98c4af51d1af8f38c3/docs/application-replicas.md).
AWS CI checks both application and database renders against pinned schemas. These
renders are not connected to the current Flux source and do not deploy workloads.
The AWS Validate workflow tests that exact shared evidence contract, including
rejection of incomplete success records and private error text.

## Validate the lifecycle intent boundary

```sh
python3 -m unittest discover -s lifecycle -v
python3 lifecycle/preflight.py run-intent.json
```

See [runbook](docs/runbook.md) for the intent format and its strict limitations.
The validator rejects broad targets and expired/unbounded intents; it is **not**
AWS identity verification, an operational janitor, spending approval or a hard cap.

## Read the design

- [Ephemeral London HA architecture, instance comparison and cost gates](docs/architecture-cost.md)

- [Architecture, ownership and compatibility](docs/implementation.md)
- [Recorded local verification](docs/verification.md)
- [Safety, lifecycle and next cloud gates](docs/runbook.md)
- [EKS rendering and provider compatibility spike](docs/eks-compatibility.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

The architecture profile describes target capabilities, not completed cloud work.
