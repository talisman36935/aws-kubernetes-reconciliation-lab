#!/usr/bin/env bash
set -euo pipefail
# Install only in the caller-supplied directory; never pipe a remote script to sh.
destination="${1:?Usage: install-local-tools.sh /absolute/tool/directory}"
[[ "$destination" == /* ]] || { echo "An absolute tool directory is required" >&2; exit 1; }
case "$(uname -m)" in
  x86_64) arch=amd64 ;;
  aarch64|arm64) arch=arm64 ;;
  *) echo "Unsupported architecture" >&2; exit 1 ;;
esac
[[ "$(uname -s)" == Linux ]] || { echo "Linux only for this bootstrap" >&2; exit 1; }
mkdir -p "$destination"
scratch="$(mktemp -d)"
# Keep downloaded archives on failure for inspection; no recursive deletion.
cd "$scratch"
curl --fail --silent --show-error --location -o kind "https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-$arch"
curl --fail --silent --show-error --location -o kind.sha256 "https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-$arch.sha256sum"
expected="$(awk '{print $1}' kind.sha256)"
echo "$expected  kind" | sha256sum --check --status
curl --fail --silent --show-error --location -o kubectl "https://dl.k8s.io/release/v1.35.8/bin/linux/$arch/kubectl"
curl --fail --silent --show-error --location -o kubectl.sha256 "https://dl.k8s.io/release/v1.35.8/bin/linux/$arch/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check --status
archive="flux_2.9.6_linux_$arch.tar.gz"
curl --fail --silent --show-error --location -O "https://github.com/fluxcd/flux2/releases/download/v2.9.6/$archive"
curl --fail --silent --show-error --location -o flux-checksums.txt "https://github.com/fluxcd/flux2/releases/download/v2.9.6/flux_2.9.6_checksums.txt"
awk -v file="$archive" '$2 == file {print}' flux-checksums.txt > selected-checksum.txt
[[ -s selected-checksum.txt ]]
sha256sum --check --status selected-checksum.txt
tar -xzf "$archive" flux
install -m 0755 kind kubectl flux "$destination/"
echo "Installed pinned tools in $destination; download cache: $scratch"
