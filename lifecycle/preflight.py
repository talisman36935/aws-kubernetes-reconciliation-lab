"""Validate a run intent, without authenticating or provisioning cloud resources."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys


def validate(intent: dict, now: datetime) -> None:
    """Fail closed on unknown fields, ambiguous scope, or an unbounded lifetime."""
    fields = {"run_id", "account_id", "region", "expires_at", "budget_gbp"}
    if set(intent) != fields:
        raise ValueError("run intent must contain exactly the documented fields")
    if not re.fullmatch(r"lab-[a-z0-9-]{1,40}", str(intent["run_id"])):
        raise ValueError("run_id must have the lab- prefix and bounded safe characters")
    if not re.fullmatch(r"[0-9]{12}", str(intent["account_id"])):
        raise ValueError("account_id must be an explicit 12-digit AWS account")
    if not re.fullmatch(r"(us|eu|ap|ca|sa|af|me|il|mx)-[a-z]+-[0-9]", str(intent["region"])):
        raise ValueError("region must be an explicit commercial AWS region")
    expires = datetime.fromisoformat(intent["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None or not now < expires <= now + timedelta(hours=1):
        raise ValueError("expiry must be timezone-aware, in the future, and within 60 minutes")
    budget = intent["budget_gbp"]
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not 0 < budget <= 5:
        raise ValueError("budget_gbp must be positive and no greater than the approved £5 ceiling")


if __name__ == "__main__":
    try:
        validate(json.loads(Path(sys.argv[1]).read_text()), datetime.now(timezone.utc))
    except (IndexError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        sys.exit(f"Invalid run intent: {exc}")
    print("Intent valid. NOT spending approval, an identity check, or a cost-enforcement mechanism.")
