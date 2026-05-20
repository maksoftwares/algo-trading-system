from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig
from phase0.strategies.registry import enabled_strategy_names


ADVERSARIAL_COLUMNS = (
    "trade_id",
    "expert",
    "cell_id",
    "symbol",
    "broker",
    "cost_model",
    "entry_time_utc",
    "exit_time_utc",
    "direction",
    "entry_price",
    "stop_loss",
    "take_profit",
    "exit_price",
    "net_pnl",
    "r_multiple",
    "setup_reason_code",
    "chart_context_start_utc",
    "chart_context_end_utc",
    "manual_failure_class",
    "manual_notes",
    "reviewer",
    "reviewed_at_utc",
)

ADVERSARIAL_REVIEW_SEED = 920000


@dataclass(frozen=True)
class AdversarialPacketOutput:
    expert: str
    review_path: Path
    losing_trades: int
    selected_trades: int


def create_adversarial_packets(config: ProjectConfig, expert: str) -> list[AdversarialPacketOutput]:
    output_dir = config.root / "outputs" / "adversarial_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[AdversarialPacketOutput] = []
    for expert_name in enabled_strategy_names(expert):
        losing = _load_losing_matrix_trades(config, expert_name)
        selected = _select_review_sample(losing)
        path = output_dir / f"{expert_name}_losing_trades_review.csv"
        pd.DataFrame(selected, columns=ADVERSARIAL_COLUMNS).to_csv(path, index=False)
        outputs.append(
            AdversarialPacketOutput(
                expert=expert_name,
                review_path=path,
                losing_trades=len(losing),
                selected_trades=len(selected),
            )
        )
    return outputs


def _load_losing_matrix_trades(config: ProjectConfig, expert: str) -> list[dict[str, object]]:
    directory = config.root / "outputs" / "matrix_results" / expert
    if not directory.exists():
        raise ConfigError(f"Matrix results directory not found: {directory}. Run run-matrix first.")

    rows: list[dict[str, object]] = []
    trade_files = sorted(directory.glob("cell_*_trades.csv"))
    for trades_path in trade_files:
        summary_path = trades_path.with_name(trades_path.name.replace("_trades.csv", ".csv"))
        if not summary_path.exists():
            raise ConfigError(f"Missing matrix summary for trades file: {summary_path}.")
        trades = pd.read_csv(trades_path)
        if trades.empty:
            continue
        summary = pd.read_csv(summary_path).iloc[0].to_dict()
        for trade_index, trade in trades.iterrows():
            net_pnl = float(trade.get("net_pnl_usd", 0.0))
            if net_pnl >= 0:
                continue
            rows.append(_review_row(expert, int(trade_index) + 1, summary, trade))
    return rows


def _review_row(
    expert: str,
    trade_index: int,
    summary: dict[str, object],
    trade: pd.Series,
) -> dict[str, object]:
    cell_id = int(summary.get("cell_id", 0))
    entry_time = pd.Timestamp(trade["entry_time_utc"])
    exit_time = pd.Timestamp(trade["exit_time_utc"])
    context_start = entry_time - pd.Timedelta(hours=4)
    context_end = exit_time + pd.Timedelta(hours=1)
    reason = trade.get("metadata_entry_reason", trade.get("exit_reason", ""))
    return {
        "trade_id": f"{expert}-cell{cell_id}-{trade_index}",
        "expert": expert,
        "cell_id": cell_id,
        "symbol": trade.get("symbol", summary.get("symbol", "XAUUSD")),
        "broker": summary.get("broker", ""),
        "cost_model": summary.get("cost_model", ""),
        "entry_time_utc": entry_time.isoformat(),
        "exit_time_utc": exit_time.isoformat(),
        "direction": trade.get("direction", ""),
        "entry_price": trade.get("entry_price", ""),
        "stop_loss": trade.get("stop_loss", ""),
        "take_profit": trade.get("take_profit", ""),
        "exit_price": trade.get("exit_price", ""),
        "net_pnl": trade.get("net_pnl_usd", ""),
        "r_multiple": trade.get("r_multiple", ""),
        "setup_reason_code": reason,
        "chart_context_start_utc": context_start.isoformat(),
        "chart_context_end_utc": context_end.isoformat(),
        "manual_failure_class": "",
        "manual_notes": "",
        "reviewer": "",
        "reviewed_at_utc": "",
    }


def _select_review_sample(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) <= 100:
        return rows

    df = pd.DataFrame(rows)
    df["net_pnl_numeric"] = pd.to_numeric(df["net_pnl"], errors="coerce").fillna(0.0)
    top_losses = df.sort_values("net_pnl_numeric", ascending=True).head(20)
    sampled = df.sample(n=100, random_state=ADVERSARIAL_REVIEW_SEED)
    selected = (
        pd.concat([top_losses, sampled], ignore_index=True)
        .drop_duplicates(subset=["trade_id"])
        .drop(columns=["net_pnl_numeric"])
        .sort_values(["cell_id", "entry_time_utc", "trade_id"])
    )
    return selected.to_dict("records")
