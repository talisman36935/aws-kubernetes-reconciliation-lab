# References and attribution

The architecture is inspired by [Polarsquad KROPS](https://github.com/polarsquad/krops/tree/d54acc2c5ba9d083ee0449f172559c0b4724894b),
reference commit `d54acc2c5ba9d083ee0449f172559c0b4724894b`, Apache-2.0.
KROPS composes existing controllers; this repository does not install a separate
"KROPS controller". Current lab scripts/manifests are independently authored.
No KROPS source has been copied into this initial slice.

The EKS renderer adapts the resource structure of the Kubernetes Cluster API
Provider AWS v2.13.1 managed-machine-pool example:
https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/v2.13.1/templates/cluster-template-eks-managedmachinepool.yaml
CAPA is Apache-2.0, Copyright The Kubernetes Authors. The renderer adds this lab's
explicit identity, endpoint restriction, lifecycle scope and bounded node policy.
The upstream license is retained at licenses/CAPA-APACHE-2.0.txt.

Flux and kind are downloaded as separately distributed tools. Their upstream
licenses and release notices remain authoritative. The broader
[reference catalogue](docs/plan/portfolio-demos/references.md) records inspiration,
review depth, limitations and reuse requirements for portfolio and platform examples.
