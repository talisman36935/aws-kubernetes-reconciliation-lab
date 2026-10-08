"""Validate a run intent, without authenticating or provisioning cloud resources."""

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import sys


def validate(intent: dict, now: datetime) -> None:
    """Fail closed on unknown fields, ambiguous scope, or an unbounded lifetime."""
    fields = {
        "run_id",
        "account_id",
        "region",
        "expires_at",
        "planned_gross_gbp",
    }
    if set(intent) != fields:
        raise ValueError("run intent must contain exactly the documented fields")
    if not re.fullmatch(r"lab-[a-z0-9-]{1,40}", str(intent["run_id"])):
        raise ValueError("run_id must have the lab- prefix and bounded safe characters")
    if not re.fullmatch(r"[0-9]{12}", str(intent["account_id"])):
        raise ValueError("account_id must be an explicit 12-digit AWS account")
    if intent["region"] != "eu-west-2":
        raise ValueError("region must be the approved London region eu-west-2")
    expires = datetime.fromisoformat(intent["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None or not now < expires <= now + timedelta(hours=1):
        raise ValueError("expiry must be timezone-aware, in the future, and within 60 minutes")
    estimate = intent["planned_gross_gbp"]
    if (
        isinstance(estimate, bool)
        or not isinstance(estimate, (int, float))
        or not math.isfinite(estimate)
        or estimate <= 0
    ):
        raise ValueError(
            "planned_gross_gbp must be a finite positive estimate, not a spending limit"
        )


if __name__ == "__main__":
    try:
        validate(json.loads(Path(sys.argv[1]).read_text()), datetime.now(timezone.utc))
    except (IndexError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        sys.exit(f"Invalid run intent: {exc}")
    print("Intent valid. NOT spending approval, an identity check, or a cost-enforcement mechanism.")
