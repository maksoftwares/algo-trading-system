from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from replay import build_result, write_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force-cache",
        action="store_true",
        help="Rebuild the D-drive five-second Dukascopy cache.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "config" / "REPLAY_CONTRACT.json",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=ROOT / "outputs",
    )
    args = parser.parse_args()
    result, events = build_result(
        force_cache=args.force_cache,
        contract_path=args.contract.resolve(),
    )
    write_outputs(result, events, args.output_directory.resolve())
    print(result["decision"])
    for row in result["scenarios"]:
        print(
            row["scenario"]["scenario_id"],
            f"taken={row['trades_accepted']}",
            f"net=${row['net_pnl_usd']:.2f}",
            f"equity_dd=${row['maximum_lifetime_equity_drawdown_usd']:.2f}",
            f"deadlock={row['flat_suspended_deadlock'] or row['floating_peak_deadlock']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
