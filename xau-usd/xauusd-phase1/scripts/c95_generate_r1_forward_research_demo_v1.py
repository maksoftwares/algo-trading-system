from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "a3_r1_forward_research_demo_v1.json").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    return phase1 if phase1.exists() else cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the A3 R1 isolated demo forward-research packet.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report", type=Path)
    parser.add_argument("--preset", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.r1_forward_research_demo import generate_r1_forward_research_demo_packet

    report = generate_r1_forward_research_demo_packet(root, report_path=args.report, preset_path=args.preset)
    print(f"A3 R1 forward-research packet: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
