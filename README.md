# AWS Kubernetes Reconciliation Lab

[![Validate](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/workflows/validate.yaml/badge.svg)](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/workflows/validate.yaml)

A KROPS-inspired portfolio lab: Git-driven controller reconciliation, observable
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
git checkout --detach 487679ffcd7125f1f1fd7878d5d84401bc7d6819
cd workload
docker compose up --build -d
python3 smoke.py
docker compose down
```

There is not yet a published application image or an AWS workload deployment.

The pinned source includes [local metrics and evidence recording](https://github.com/talisman36935/gcp-platform-delivery-lab/blob/487679ffcd7125f1f1fd7878d5d84401bc7d6819/docs/local-observability.md),
durable API/worker tracing, bounded profiling and compiled regression/recovery.
It passed [hosted validation](https://github.com/talisman36935/gcp-platform-delivery-lab/actions/runs/37164832226).
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

- [Ephemeral London HA architecture, instance comparison and cost gates](docs/plan/portfolio-demos/minimal-infrastructure.md)

- [Architecture, ownership and compatibility](docs/implementation.md)
- [Recorded local verification](docs/verification.md)
- [Safety, lifecycle and next cloud gates](docs/runbook.md)
- [EKS rendering and provider compatibility spike](docs/eks-compatibility.md)
- [Full strategy](docs/plan/portfolio-demo-strategy-2026-10-02.md)
- [Platform design](docs/plan/portfolio-demos/platforms.md)
- [Evidence and portfolio Labs contract](docs/plan/portfolio-demos/evidence-and-labs.md)
- [Milestones](docs/plan/portfolio-demos/delivery-plan.md)
- [Annotated reference catalogue](docs/plan/portfolio-demos/references.md)
- [KROPS attribution](THIRD_PARTY_NOTICES.md)

The planning documents describe intended capabilities, not completed cloud work.
