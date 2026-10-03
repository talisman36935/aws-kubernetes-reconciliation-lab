# Verification record

## Initial foundation — 2026-10-03

Source: `02711fca85f1a1f82b493d580a83c1d1d944e129`.
[Hosted run 37145049038](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37145049038)
passed lifecycle negative tests, shell syntax/ShellCheck, and the real local
kind/Flux integration:

1. Flux fetched the exact public source revision.
2. The Kustomization became ready and ConfigMap owner equaled `flux`.
3. An out-of-band patch changed owner to `out-of-band`.
4. Reconciliation restored owner to `flux` and reported the expected revision.
5. Cleanup removed `portfolio-reconcile-control-plane`.

The run emitted:

```text
PASS: source revision 02711fca85f1a1f82b493d580a83c1d1d944e129 reconciled and out-of-band drift corrected.
Local kind/Flux evidence only; no EKS, CAPA or ACK claim.
Deleted nodes: ["portfolio-reconcile-control-plane"]
```

This authored record retains the result beyond CI log retention. It is not the
future signed/versioned portfolio evidence bundle or an AWS cleanup audit.
