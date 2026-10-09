"""Export or verify the checked-in OpenAPI contract snapshot."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend" / "src"))

from backend.main import app  # noqa: E402

CONTRACT_PATH = ROOT / "docs" / "api" / "openapi.json"


def main() -> int:
    """Write the current API contract or fail if the snapshot is stale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in OpenAPI snapshot needs updating",
    )
    args = parser.parse_args()
    contract = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"

    if args.check:
        if not CONTRACT_PATH.exists() or CONTRACT_PATH.read_text() != contract:
            print(
                f"{CONTRACT_PATH.relative_to(ROOT)} is stale; "
                "run `uv run python scripts/export_openapi.py` and review it."
            )
            return 1
        print("OpenAPI contract snapshot is up to date.")
        return 0

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(contract)
    print(f"Wrote {CONTRACT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
