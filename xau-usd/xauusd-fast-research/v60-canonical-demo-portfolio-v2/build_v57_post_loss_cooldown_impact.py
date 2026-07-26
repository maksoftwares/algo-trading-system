from __future__ import annotations

import hashlib
import heapq
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"
LEDGER_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet"
)
REPORTS = ROOT / "reports"
JSON_PATH = REPORTS / "V60_V57_POST_LOSS_COOLDOWN_IMPACT.json"
MONTHLY_PATH = REPORTS / "V60_V57_POST_LOSS_COOLDOWN_LAST_12_MONTHS.csv"
AUDIT_PATH = REPORTS / "V60_V57_POST_LOSS_COOLDOWN_TRADE_AUDIT.csv"
FINAL_WINDOW_START = pd.Timestamp("2025-07-01T00:00:00Z")
FINAL_WINDOW_END = pd.Timestamp("2026-07-01T00:00:00Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def execution_source(row: pd.Series) -> str:
    specialist = row.get("specialist_id")
    if specialist is not None and not pd.isna(specialist):
        return str(specialist)
    return str(row["sleeve_id"])


def apply_post_loss_cooldowns(
    frame: pd.DataFrame, cooldown_minutes: Mapping[str, int]
) -> pd.DataFrame:
    result = frame.copy()
    result["post_loss_cooldown_accepted"] = False
    result["post_loss_cooldown_reason"] = ""
    result["execution_source_id"] = result.apply(execution_source, axis=1)

    open_trades: list[tuple[int, int, Any]] = []
    last_loss: dict[tuple[str, str], pd.Timestamp] = {}
    sequence = 0
    ordered = result.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    )
    for index, row in ordered.iterrows():
        entry = pd.Timestamp(row["entry_time"])
        entry_ns = int(entry.value)
        while open_trades and open_trades[0][0] <= entry_ns:
            _, _, completed_index = heapq.heappop(open_trades)
            completed = result.loc[completed_index]
            completed_source = str(completed["execution_source_id"])
            if (
                int(cooldown_minutes.get(completed_source, 0)) > 0
                and float(completed["fee_stress_pnl_usd"]) < 0.0
            ):
                key = (completed_source, str(completed["direction"]).upper())
                closed_at = pd.Timestamp(completed["exit_time"])
                if key not in last_loss or closed_at > last_loss[key]:
                    last_loss[key] = closed_at

        source = str(row["execution_source_id"])
        direction = str(row["direction"]).upper()
        minutes = int(cooldown_minutes.get(source, 0))
        previous_loss = last_loss.get((source, direction))
        if (
            minutes > 0
            and previous_loss is not None
            and entry < previous_loss + pd.Timedelta(minutes=minutes)
        ):
            result.at[index, "post_loss_cooldown_reason"] = (
                "SAME_DIRECTION_POST_LOSS_COOLDOWN"
            )
            continue

        result.at[index, "post_loss_cooldown_accepted"] = True
        result.at[index, "post_loss_cooldown_reason"] = "ROUTED"
        heapq.heappush(
            open_trades,
            (int(pd.Timestamp(row["exit_time"]).value), sequence, index),
        )
        sequence += 1
    return result


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame["fee_stress_pnl_usd"].to_numpy(dtype=float)
    gross_profit = float(np.clip(values, 0.0, None).sum())
    gross_loss = float(np.clip(-values, 0.0, None).sum())
    cumulative = pd.Series(values).cumsum()
    drawdown = cumulative.cummax() - cumulative
    return {
        "trade_rows": int(len(frame)),
        "net_pnl_usd": float(values.sum()),
        "win_rate": float((values > 0.0).mean()) if len(values) else None,
        "profit_factor": (
            float(gross_profit / gross_loss) if gross_loss > 0.0 else None
        ),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": -gross_loss,
        "closed_trade_drawdown_usd": (
            float(drawdown.max()) if len(drawdown) else 0.0
        ),
    }


def comparison(before: pd.DataFrame, after: pd.DataFrame) -> dict[str, Any]:
    before_metrics = metrics(before)
    after_metrics = metrics(after)
    return {
        "before": before_metrics,
        "after": after_metrics,
        "effect": {
            "trades": after_metrics["trade_rows"] - before_metrics["trade_rows"],
            "net_pnl_usd": (
                after_metrics["net_pnl_usd"] - before_metrics["net_pnl_usd"]
            ),
            "win_rate_percentage_points": 100.0
            * (after_metrics["win_rate"] - before_metrics["win_rate"]),
            "profit_factor": (
                after_metrics["profit_factor"] - before_metrics["profit_factor"]
            ),
            "closed_trade_drawdown_usd": (
                after_metrics["closed_trade_drawdown_usd"]
                - before_metrics["closed_trade_drawdown_usd"]
            ),
        },
    }


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cooldowns = {
        str(source["source_id"]): int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        )
        for source in config["sources"]
        if int(source.get("same_direction_post_loss_cooldown_minutes", 0)) > 0
    }
    ledger = pd.read_parquet(LEDGER_PATH)
    baseline = ledger.loc[ledger["specialist_id"].ne("R5_TRANSITION")].copy()
    audited = apply_post_loss_cooldowns(baseline, cooldowns)
    accepted = audited.loc[audited["post_loss_cooldown_accepted"]].copy()

    before_window = baseline.loc[
        baseline["entry_time"].ge(FINAL_WINDOW_START)
        & baseline["entry_time"].lt(FINAL_WINDOW_END)
    ].copy()
    after_window = accepted.loc[
        accepted["entry_time"].ge(FINAL_WINDOW_START)
        & accepted["entry_time"].lt(FINAL_WINDOW_END)
    ].copy()
    report = {
        "schema_version": "xauusd_v60_v57_post_loss_cooldown_impact_v1",
        "policy": {
            "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
            "same_direction_post_loss_cooldown_minutes": 120,
            "trigger": "PRIOR_ACCEPTED_TRADE_REALIZED_FEE_STRESS_NET_PNL_NEGATIVE",
            "opposite_direction_remains_eligible": True,
            "other_sources_remain_unchanged": True,
        },
        "historical_ledger_path": LEDGER_PATH.relative_to(REPO_ROOT).as_posix(),
        "historical_ledger_sha256": sha256_file(LEDGER_PATH),
        "all_history": comparison(baseline, accepted),
        "final_twelve_months": {
            "start_inclusive_utc": FINAL_WINDOW_START.isoformat().replace(
                "+00:00", "Z"
            ),
            "end_exclusive_utc": FINAL_WINDOW_END.isoformat().replace(
                "+00:00", "Z"
            ),
            **comparison(before_window, after_window),
        },
        "limitations": [
            "Fixed-0.01-lot historical fee-stress evidence is not a profit promise.",
            "The cooldown is evaluated path-dependently using only prior accepted and completed trades.",
            "The calculation is deterministic and has no ML participation.",
        ],
    }

    monthly_before = (
        before_window.assign(month=before_window["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month", as_index=False)["fee_stress_pnl_usd"]
        .agg(before_trades="count", before_net_pnl_usd="sum")
    )
    monthly_after = (
        after_window.assign(month=after_window["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month", as_index=False)["fee_stress_pnl_usd"]
        .agg(after_trades="count", after_net_pnl_usd="sum")
    )
    monthly = monthly_before.merge(monthly_after, on="month", how="outer").fillna(0)
    monthly["trade_effect"] = monthly["after_trades"] - monthly["before_trades"]
    monthly["net_pnl_effect_usd"] = (
        monthly["after_net_pnl_usd"] - monthly["before_net_pnl_usd"]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monthly.to_csv(MONTHLY_PATH, index=False)
    audited.to_csv(AUDIT_PATH, index=False)
    print(json.dumps(report, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
