from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ORDER_LOGS = [
    Path("C:/MT5PortableTier1BestEA/MQL5/Files/tier1_bestea_order_log_xauusd.csv"),
    Path("C:/MT5PortableRepairLane/MQL5/Files/a3_rdguard_v1_order_log.csv"),
    Path("C:/MT5PortableRepairLane/MQL5/Files/a3_rdstruct_v1_order_log.csv"),
]

EA_BY_MAGIC = {
    "920101": "A2_breakout_retest_920101",
    "933000": "A3_rdguard_v1_933000",
    "933100": "A3_rdstruct_v1_933100",
}

REGIMES = ["STRONG_UP", "UP", "FLAT", "DOWN", "STRONG_DOWN", "UNKNOWN"]


@dataclass(frozen=True)
class ScoreRow:
    ea: str
    magic: str
    regime: str
    order_log_entries: int
    broker_trade_rows: int
    closed_trades: int
    wins: int
    losses: int
    win_rate_pct: float | None
    pnl_aed: float | None
    profit_factor: float | str | None
    evidence_status: str


def generate_direction_state_shadow_scoreboard(
    root: Path,
    order_logs: list[Path] | None = None,
    trade_history_csv: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output_json = output_json or reports / "DIRECTION_STATE_SHADOW_SCOREBOARD_2026_06_14.json"
    order_logs = order_logs or DEFAULT_ORDER_LOGS

    order_rows = _read_order_rows(order_logs)
    trades = _read_csv(trade_history_csv) if trade_history_csv else []
    order_state_by_ticket = _direction_state_by_ticket(order_rows)
    enriched_trades = [_enrich_trade(row, order_state_by_ticket) for row in trades]
    rows = _score_rows(order_rows, enriched_trades)

    payload = {
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "order_logs": [str(path) for path in order_logs],
        "trade_history_csv": str(trade_history_csv or ""),
        "scoreboard": [row.__dict__ for row in rows],
        "notes": [
            "DirectionState is shadow-only. Scoreboard grouping does not imply a trading rule.",
            "Win rate and PnL populate when broker-history rows can be matched to order-log tickets carrying dirstate fields.",
        ],
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(output_json.with_suffix(".csv"), rows)
    output_json.with_suffix(".md").write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _read_order_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        for row in _read_csv(path):
            enriched = dict(row)
            enriched["source_order_log"] = str(path)
            rows.append(enriched)
    return rows


def _read_csv(path: Path | None) -> list[dict[str, str]]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _direction_state_by_ticket(order_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for row in order_rows:
        regime = row.get("dirstate_regime") or "UNKNOWN"
        state = {
            "dirstate_direction": row.get("dirstate_direction") or "0",
            "dirstate_regime": regime,
            "dirstate_strength": row.get("dirstate_strength") or "0.000",
            "magic": row.get("magic") or "",
        }
        for key in ("order_ticket", "deal_ticket"):
            value = str(row.get(key) or "").strip()
            if value and value != "0":
                mapping[value] = state
    return mapping


def _enrich_trade(row: dict[str, str], state_by_ticket: dict[str, dict[str, str]]) -> dict[str, str]:
    enriched = dict(row)
    state = None
    for key in ("entry_order", "entry_deal", "order_ticket", "deal_ticket", "position_ticket"):
        value = str(enriched.get(key) or "").strip()
        if value in state_by_ticket:
            state = state_by_ticket[value]
            break
    if state:
        enriched.update(state)
    else:
        enriched.setdefault("dirstate_direction", "0")
        enriched.setdefault("dirstate_regime", "UNKNOWN")
        enriched.setdefault("dirstate_strength", "0.000")
    return enriched


def _score_rows(order_rows: list[dict[str, str]], trades: list[dict[str, str]]) -> list[ScoreRow]:
    output: list[ScoreRow] = []
    for magic, ea in EA_BY_MAGIC.items():
        order_subset = [row for row in order_rows if str(row.get("magic") or "") == magic]
        trade_subset = [row for row in trades if str(row.get("magic") or "") == magic]
        for regime in REGIMES:
            regime_orders = [row for row in order_subset if (row.get("dirstate_regime") or "UNKNOWN") == regime]
            regime_trades = [row for row in trade_subset if (row.get("dirstate_regime") or "UNKNOWN") == regime]
            closed = [row for row in regime_trades if (row.get("state") or "").upper() == "CLOSED"]
            profits = [_to_float(row.get("profit_aed") or row.get("profit") or row.get("pnl")) for row in closed]
            profits = [value for value in profits if value is not None]
            wins = [value for value in profits if value > 0.0]
            losses = [value for value in profits if value < 0.0]
            gross_win = sum(wins)
            gross_loss = sum(losses)
            output.append(
                ScoreRow(
                    ea=ea,
                    magic=magic,
                    regime=regime,
                    order_log_entries=len(regime_orders),
                    broker_trade_rows=len(regime_trades),
                    closed_trades=len(profits),
                    wins=len(wins),
                    losses=len(losses),
                    win_rate_pct=round(len(wins) / len(profits) * 100.0, 2) if profits else None,
                    pnl_aed=round(sum(profits), 2) if profits else None,
                    profit_factor=_profit_factor(gross_win, gross_loss),
                    evidence_status="READY" if profits else "PENDING_MATCHED_CLOSED_TRADES",
                )
            )
    return output


def _profit_factor(gross_win: float, gross_loss: float) -> float | str | None:
    if gross_loss < 0.0:
        return round(gross_win / abs(gross_loss), 2)
    if gross_win > 0.0:
        return "inf"
    return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _write_csv(path: Path, rows: list[ScoreRow]) -> None:
    fields = list(ScoreRow.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(row.__dict__ for row in rows)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# DirectionState Shadow Scoreboard",
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
        "| EA | Magic | Regime | Order log rows | Broker trade rows | Closed | Wins | Losses | Win rate | PnL AED | PF | Status |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["scoreboard"]:
        lines.append(
            "| {ea} | {magic} | {regime} | {order_log_entries} | {broker_trade_rows} | {closed_trades} | {wins} | {losses} | {wr} | {pnl} | {pf} | {status} |".format(
                ea=row["ea"],
                magic=row["magic"],
                regime=row["regime"],
                order_log_entries=row["order_log_entries"],
                broker_trade_rows=row["broker_trade_rows"],
                closed_trades=row["closed_trades"],
                wins=row["wins"],
                losses=row["losses"],
                wr=_fmt(row["win_rate_pct"]),
                pnl=_fmt(row["pnl_aed"]),
                pf=_fmt(row["profit_factor"]),
                status=row["evidence_status"],
            )
        )
    lines.extend(["", "Notes:", *[f"- {note}" for note in payload["notes"]], ""])
    return "\n".join(lines)


def _fmt(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--order-log", action="append", type=Path, default=[])
    parser.add_argument("--trade-history-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    order_logs = args.order_log if args.order_log else None
    payload = generate_direction_state_shadow_scoreboard(
        args.root,
        order_logs=order_logs,
        trade_history_csv=args.trade_history_csv,
        output_json=args.output_json,
    )
    print(f"status={payload['status']}")
    print(f"rows={len(payload['scoreboard'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
