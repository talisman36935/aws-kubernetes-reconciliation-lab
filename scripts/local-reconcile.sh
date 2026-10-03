#!/usr/bin/env bash
set -euo pipefail
# Creates and removes only this disposable local cluster. Never uses cloud APIs.
revision="${1:?Supply a pushed, reviewed 40-character Git commit}"
[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid Git revision" >&2; exit 1; }
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="portfolio-reconcile"
if kind get clusters 2>/dev/null | grep -Fxq "$name"; then
  echo "Cluster $name already exists; refusing to replace it" >&2
  exit 1
fi
export KUBECONFIG
KUBECONFIG="$(mktemp)"
cleanup() {
  kind delete cluster --name "$name"
  # The file was exclusively created by this script and may contain credentials.
  rm -f "$KUBECONFIG"
}
trap cleanup EXIT
kind create cluster --name "$name" --config "$root/bootstrap/kind.yaml" \
  --image kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0 --wait 180s
flux install --version=v2.9.6 --components=source-controller,kustomize-controller --timeout=5m
flux create source git portfolio --url=https://github.com/talisman36935/aws-kubernetes-reconciliation-lab \
  --commit="$revision" --interval=1m --timeout=3m
flux create kustomization local-contract --source=GitRepository/portfolio \
  --path=./management/local --prune=true --interval=1m --wait=true --timeout=3m
flux reconcile kustomization local-contract --with-source --timeout=3m
[[ "$(kubectl -n report-lab get configmap reconciliation-contract -o jsonpath='{.data.owner}')" == flux ]]
kubectl -n report-lab patch configmap reconciliation-contract --type=merge -p '{"data":{"owner":"out-of-band"}}'
flux reconcile kustomization local-contract --timeout=3m
[[ "$(kubectl -n report-lab get configmap reconciliation-contract -o jsonpath='{.data.owner}')" == flux ]]
applied="$(kubectl -n flux-system get kustomization local-contract -o jsonpath='{.status.lastAppliedRevision}')"
[[ "$applied" == *"$revision"* ]]
echo "PASS: source revision $revision reconciled and out-of-band drift corrected."
echo "Local kind/Flux evidence only; no EKS, CAPA or ACK claim."
