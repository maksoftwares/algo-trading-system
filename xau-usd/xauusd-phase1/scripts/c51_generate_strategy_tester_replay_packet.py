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
    parser = argparse.ArgumentParser(description="Generate the A3 ML Strategy Tester replay packet.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--packet-dir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.strategy_tester_replay_packet import generate_strategy_tester_replay_packet  # noqa: PLC0415

    output = generate_strategy_tester_replay_packet(
        root,
        report_json=args.report_json,
        registry_path=args.registry,
        packet_dir=args.packet_dir,
    )
    print(f"A3 ML Strategy Tester replay packet status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
