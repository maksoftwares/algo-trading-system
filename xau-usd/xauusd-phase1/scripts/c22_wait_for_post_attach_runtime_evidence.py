from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for post-attach A3 ML runtime evidence on A1/A2/A3.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.post_attach_monitor import wait_for_post_attach_runtime_evidence  # noqa: PLC0415

    output = wait_for_post_attach_runtime_evidence(
        root,
        report_json=args.report_json,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )
    print(f"A3 ML post-attach runtime monitor status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
