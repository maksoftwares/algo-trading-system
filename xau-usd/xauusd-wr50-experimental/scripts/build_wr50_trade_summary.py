from __future__ import annotations

import argparse
import csv
from pathlib import Path

from build_wr50_daily_report import compute_metrics, load_trade_rows


def write_trade_summary(root: Path, ledger_paths: list[Path] | None = None) -> Path:
    rows = load_trade_rows(root, ledger_paths)
    metrics = compute_metrics(rows)
    out = root / "outputs" / "reports" / "WR50_TRADE_SUMMARY_DETAIL.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ea_id",
        "magic",
        "trades",
        "open_trades",
        "win_rate",
        "profit_factor",
        "net_r",
        "pnl",
        "avg_win_r",
        "avg_loss_r",
        "cost_r",
        "commission",
        "swap",
        "entry_spread_median",
        "entry_spread_p95",
        "max_consecutive_losses",
        "largest_trade_contribution",
        "top5_trade_contribution",
        "status",
        "notes",
    ]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in metrics:
            writer.writerow({field: getattr(item, field) for field in fields})
    return out


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    root = default_root()
    parser = argparse.ArgumentParser(description="Build WR50 CSV trade summary.")
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--ledger", type=Path, action="append")
    args = parser.parse_args(argv)
    out = write_trade_summary(args.root, args.ledger)
    print(f"WR50 trade summary: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

