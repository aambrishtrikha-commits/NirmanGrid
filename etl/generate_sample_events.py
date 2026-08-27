"""Generate 60 Delhi SAMPLE events. Every row stamped source=SAMPLE."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from nirmangrid.sample_events import write_sample_files  # noqa: E402


def main() -> int:
    result = write_sample_files()
    print(f"Wrote {result['count']} SAMPLE events")
    print(result["json"])
    print(result["csv"])
    if result["count"] != 60:
        print("Expected 60 events.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
