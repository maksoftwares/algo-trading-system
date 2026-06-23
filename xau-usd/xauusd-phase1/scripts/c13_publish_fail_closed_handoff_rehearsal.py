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
    parser = argparse.ArgumentParser(description="Publish fail-closed A3 ML EA handoff rehearsal files.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--publish", action="store_true", help="Copy ABSTAIN-only rehearsal files into configured MT5 MQL5/Files roots.")
    parser.add_argument("--terminal-file-name", default="A3_ML_EA_HANDOFF.csv")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.fail_closed_handoff_rehearsal import publish_fail_closed_handoff_rehearsal  # noqa: PLC0415

    output = publish_fail_closed_handoff_rehearsal(
        root,
        report_json=args.report_json,
        publish=args.publish,
        terminal_file_name=args.terminal_file_name,
    )
    print(f"A3 ML fail-closed handoff rehearsal status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
