"""Render from the exact shared source/image lock without cluster operations."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-source", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--storage-class", required=True)
    parser.add_argument("--backend", choices=["local", "aws"], default="local")
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    lock = json.loads((root / "workload/source.json").read_text())
    release = json.loads(args.release.read_text())
    if release["source_revision"] != lock["revision"] or release["image"] != lock["image_digest"]:
        parser.error("release must match both immutable lock inputs")
    actual = subprocess.run(["git", "-C", str(args.shared_source), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(args.shared_source), "status", "--porcelain"],
                           check=True, capture_output=True, text=True).stdout.strip()
    if actual != lock["revision"] or dirty:
        parser.error("supply a clean checkout of the exact locked shared source")
    command = [sys.executable, str(args.shared_source / "workload/deploy/render_delivery.py"),
               "--owner", "flux", "--release", str(args.release.resolve()),
               "--storage-class", args.storage_class, "--backend", args.backend,
               "--output", str(args.output.resolve())]
    if args.settings:
        command += ["--settings", str(args.settings.resolve())]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
