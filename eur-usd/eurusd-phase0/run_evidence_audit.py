from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.evidence_audit import run_audit, write_outputs  # noqa: E402


def main() -> int:
    report = run_audit()
    json_path, md_path = write_outputs(report)
    print(report["status"])
    print(json_path)
    print(md_path)
    return 0 if report["status"] == "WORKING_RESEARCH_STRATEGY_FORWARD_NOT_AUTHORIZED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
