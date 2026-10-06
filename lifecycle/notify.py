"""Emit one allowlisted lab lifecycle event to the run's private SNS topic."""

import argparse
from datetime import datetime, timezone
import json
import re
import subprocess
import sys


EVENTS = {
    "created",
    "ready",
    "expiry-warning",
    "teardown-started",
    "teardown-passed",
    "teardown-failed",
}
TOPIC_ARN = re.compile(r"^arn:aws:sns:eu-west-2:[0-9]{12}:[A-Za-z0-9_-]{1,256}$")


def message(run_id: str, event: str, occurred_at: str) -> dict:
    if not re.fullmatch(r"lab-[a-z0-9-]{1,40}", run_id):
        raise ValueError("run_id must use the bounded lab- identifier format")
    if event not in EVENTS:
        raise ValueError("event is not in the lifecycle allowlist")
    timestamp = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("occurred_at must include a timezone")
    return {
        "schema": "portfolio.lifecycle.v1",
        "run_id": run_id,
        "event": event,
        "occurred_at": timestamp.astimezone(timezone.utc).isoformat(),
    }


def publish(topic_arn: str, run_id: str, event: str, *, runner=subprocess.run) -> None:
    if not TOPIC_ARN.fullmatch(topic_arn):
        raise ValueError("topic ARN must identify an SNS topic in eu-west-2")
    payload = json.dumps(
        message(run_id, event, datetime.now(timezone.utc).isoformat()),
        separators=(",", ":"),
    )
    command = [
        "aws", "sns", "publish", "--region", "eu-west-2",
        "--topic-arn", topic_arn, "--subject", f"Portfolio lab: {event}",
        "--message", payload, "--no-cli-pager", "--output", "json",
    ]
    try:
        runner(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("lifecycle event delivery to SNS failed") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-arn", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--event", choices=sorted(EVENTS), required=True)
    args = parser.parse_args()
    try:
        publish(args.topic_arn, args.run_id, args.event)
    except (ValueError, RuntimeError) as exc:
        print(f"lifecycle notification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
