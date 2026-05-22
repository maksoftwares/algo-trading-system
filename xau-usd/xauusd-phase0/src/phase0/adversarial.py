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
ADVERSARIAL_FAILURE_CLASSES = (
    "VALID_LOSS",
    "ROUTER_OPPORTUNITY",
    "LOGIC_GAP",
    "DATA_ISSUE",
    "EXECUTION_AMBIGUITY",
)

ADVERSARIAL_REVIEW_SEED = 920000


@dataclass(frozen=True)
class AdversarialPacketOutput:
    expert: str
    review_path: Path
    losing_trades: int
    selected_trades: int


@dataclass(frozen=True)
class AdversarialScoreOutput:
    expert: str
    score_path: Path
    reviewed_trades: int
    total_trades: int
    logic_gap_failures: int
    logic_gap_failures_pct: float | None
    status: str


def create_adversarial_packets(
    config: ProjectConfig,
    expert: str,
    allow_research_candidate: bool = False,
) -> list[AdversarialPacketOutput]:
    output_dir = config.root / "outputs" / "adversarial_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[AdversarialPacketOutput] = []
    for expert_name in enabled_strategy_names(expert, allow_research_candidate=allow_research_candidate):
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


def score_adversarial_review(
    config: ProjectConfig,
    expert: str,
    allow_research_candidate: bool = False,
) -> list[AdversarialScoreOutput]:
    outputs: list[AdversarialScoreOutput] = []
    for expert_name in enabled_strategy_names(expert, allow_research_candidate=allow_research_candidate):
        outputs.append(_score_one_review(config, expert_name))
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


def _score_one_review(config: ProjectConfig, expert: str) -> AdversarialScoreOutput:
    output_dir = config.root / "outputs" / "adversarial_review"
    review_path = output_dir / f"{expert}_losing_trades_review.csv"
    if not review_path.exists():
        raise ConfigError(f"Adversarial review not found: {review_path}. Run create-adversarial-packets first.")

    table = pd.read_csv(review_path)
    missing = [column for column in ("manual_failure_class", "reviewer", "reviewed_at_utc") if column not in table.columns]
    if missing:
        raise ConfigError(f"Adversarial review {review_path} missing column(s): {', '.join(missing)}.")

    if table.empty:
        reviewed = pd.Series(dtype=bool)
        reviewed_table = table
    else:
        failure_classes = table["manual_failure_class"].fillna("").astype(str).str.strip().str.upper()
        invalid_classes = sorted(
            value
            for value in set(failure_classes)
            if value and value not in ADVERSARIAL_FAILURE_CLASSES
        )
        if invalid_classes:
            raise ConfigError(
                f"Adversarial review {review_path} has unsupported manual_failure_class value(s): "
                f"{', '.join(invalid_classes)}. Allowed: {', '.join(ADVERSARIAL_FAILURE_CLASSES)}."
            )
        reviewed = (
            table[["manual_failure_class", "reviewer", "reviewed_at_utc"]]
            .fillna("")
            .astype(str)
            .apply(lambda row: all(value.strip() for value in row), axis=1)
        )
        reviewed_table = table[reviewed].copy()
        reviewed_table["manual_failure_class"] = (
            reviewed_table["manual_failure_class"].fillna("").astype(str).str.strip().str.upper()
        )

    reviewed_count = int(len(reviewed_table))
    logic_gaps = int((reviewed_table["manual_failure_class"] == "LOGIC_GAP").sum()) if reviewed_count else 0
    logic_gap_pct = None if reviewed_count == 0 else logic_gaps / reviewed_count * 100.0
    threshold = float(config.phase0["gates"]["adversarial_max_logic_gap_loser_pct"])
    if len(table) and reviewed_count < len(table):
        status = "PENDING"
    elif logic_gap_pct is None:
        status = "PASS"
    else:
        status = "PASS" if logic_gap_pct <= threshold else "FAIL"

    score_path = output_dir / f"{expert}_adversarial_score.md"
    score_path.write_text(
        _render_adversarial_score(
            expert=expert,
            review_path=review_path,
            total_trades=len(table),
            reviewed_trades=reviewed_count,
            logic_gap_failures=logic_gaps,
            logic_gap_failures_pct=logic_gap_pct,
            threshold=threshold,
            status=status,
        ),
        encoding="utf-8",
    )
    return AdversarialScoreOutput(
        expert=expert,
        score_path=score_path,
        reviewed_trades=reviewed_count,
        total_trades=len(table),
        logic_gap_failures=logic_gaps,
        logic_gap_failures_pct=logic_gap_pct,
        status=status,
    )


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


def _render_adversarial_score(
    *,
    expert: str,
    review_path: Path,
    total_trades: int,
    reviewed_trades: int,
    logic_gap_failures: int,
    logic_gap_failures_pct: float | None,
    threshold: float,
    status: str,
) -> str:
    pct_text = "n/a" if logic_gap_failures_pct is None else f"{logic_gap_failures_pct:.4g}%"
    return "\n".join(
        [
            f"# Adversarial Review Score: {expert}",
            "",
            f"Review file: {review_path}",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Total sampled losing trades | {total_trades} |",
            f"| Reviewed trades | {reviewed_trades} |",
            f"| Logic-gap failures | {logic_gap_failures} |",
            f"| Logic-gap failure pct | {pct_text} |",
            f"| Threshold | <= {threshold}% |",
            f"| Status | {status} |",
            "",
            "Allowed manual_failure_class values:",
            "",
            "\n".join(f"- {value}" for value in ADVERSARIAL_FAILURE_CLASSES),
            "",
        ]
    )
