from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.window_performance import build_window_report, write_window_report  # noqa: E402


def main() -> int:
    report = build_window_report()
    json_path, md_path = write_window_report(report)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
