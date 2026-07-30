from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_v57_post_loss_cooldown_impact import (
    apply_post_loss_cooldowns,
    execution_source,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"
LEDGER_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet"
)
OUTPUT_PATH = ROOT / "evidence" / "V60_CANONICAL_DEMO_DEPLOYMENT_PARITY_V1.json"
EXPECTED_BASELINE_ROWS = 2184
EXPECTED_EXECUTABLE_ROWS = 2153
FINAL_WINDOW_START = pd.Timestamp("2025-07-01T00:00:00Z")
FINAL_WINDOW_END = pd.Timestamp("2026-07-01T00:00:00Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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


def source_evidence(
    all_history: pd.DataFrame,
    final_window: pd.DataFrame,
) -> dict[str, Any]:
    all_metrics = metrics(all_history)
    recent_metrics = metrics(final_window)
    enough_history = all_metrics["trade_rows"] >= 30
    historical_pf = all_metrics["profit_factor"]
    recent_pf = recent_metrics["profit_factor"]
    recent_veto = (
        recent_metrics["trade_rows"] >= 10
        and (recent_pf is None or recent_pf < 1.0)
    )
    confirmed = (
        enough_history
        and historical_pf is not None
        and historical_pf >= 1.20
        and not recent_veto
    )
    return {
        "status": "CONFIRMED" if confirmed else "DEMO_PROBATION",
        "all_history": all_metrics,
        "final_twelve_months": recent_metrics,
        "checks": {
            "minimum_30_all_history_trades": enough_history,
            "minimum_1_20_all_history_profit_factor": (
                historical_pf is not None and historical_pf >= 1.20
            ),
            "recent_veto_not_triggered": not recent_veto,
        },
    }


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    source_ids = sorted(str(row["source_id"]) for row in config["sources"])
    cooldowns = {
        str(source["source_id"]): int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        )
        for source in config["sources"]
        if int(source.get("same_direction_post_loss_cooldown_minutes", 0)) > 0
    }
    ledger = pd.read_parquet(LEDGER_PATH)
    candidate_population = ledger.loc[
        ledger["specialist_id"].ne("R5_TRANSITION")
    ].copy()
    candidate_population["execution_source_id"] = candidate_population.apply(
        execution_source,
        axis=1,
    )
    unknown_sources = sorted(
        set(candidate_population["execution_source_id"]) - set(source_ids)
    )
    baseline = candidate_population.loc[
        candidate_population["execution_source_id"].isin(source_ids)
    ].copy()
    audited = apply_post_loss_cooldowns(baseline, cooldowns)
    filtered = audited.loc[audited["post_loss_cooldown_accepted"]].copy()
    window = filtered.loc[
        filtered["entry_time"].ge(FINAL_WINDOW_START)
        & filtered["entry_time"].lt(FINAL_WINDOW_END)
    ].copy()
    per_source = {
        source_id: source_evidence(
            filtered.loc[filtered["execution_source_id"].eq(source_id)],
            window.loc[window["execution_source_id"].eq(source_id)],
        )
        for source_id in source_ids
    }
    probation_sources = sorted(
        source_id
        for source_id, evidence in per_source.items()
        if evidence["status"] == "DEMO_PROBATION"
    )
    checks = {
        "baseline_historical_trade_rows_match": (
            len(baseline) == EXPECTED_BASELINE_ROWS
        ),
        "executable_historical_trade_rows_match": (
            len(filtered) == EXPECTED_EXECUTABLE_ROWS
        ),
        "v57_cooldown_is_exactly_120_minutes": cooldowns
        == {"V57_BREAK_SWING_H4ADX_HIGH": 120},
        "r5_is_excluded": not filtered["specialist_id"].eq("R5_TRANSITION").any(),
        "no_unknown_execution_sources": not unknown_sources,
        "exact_execution_source_set_present": sorted(
            filtered["execution_source_id"].unique().tolist()
        )
        == source_ids,
        "all_history_is_profitable_after_stress": float(
            filtered["fee_stress_pnl_usd"].sum()
        )
        > 0.0,
        "final_twelve_month_window_is_profitable_after_stress": float(
            window["fee_stress_pnl_usd"].sum()
        )
        > 0.0,
    }
    artifact = {
        "schema_version": "xauusd_v60_deployment_parity_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "basis": (
            "Frozen V60 account-routed price ledger filtered to the exact current "
            "executable source population, with the V57 same-direction 120-minute "
            "post-realized-loss cooldown applied path-dependently; R5 is excluded "
            "because it is not executable."
        ),
        "historical_ledger_path": LEDGER_PATH.relative_to(REPO_ROOT).as_posix(),
        "historical_ledger_sha256": sha256_file(LEDGER_PATH),
        "executable_source_ids": source_ids,
        "unknown_execution_source_ids": unknown_sources,
        "excluded_specialist_ids": ["R5_TRANSITION"],
        "post_loss_cooldowns_minutes": cooldowns,
        "baseline_historical_trade_rows": int(len(baseline)),
        "historical_trade_rows": int(len(filtered)),
        "all_history": metrics(filtered),
        "final_twelve_months": {
            "start_inclusive_utc": FINAL_WINDOW_START.isoformat().replace(
                "+00:00", "Z"
            ),
            "end_exclusive_utc": FINAL_WINDOW_END.isoformat().replace(
                "+00:00", "Z"
            ),
            **metrics(window),
        },
        "source_evidence_policy": {
            "minimum_all_history_trades": 30,
            "minimum_all_history_profit_factor": 1.20,
            "recent_veto_minimum_trades": 10,
            "recent_veto_profit_factor_below": 1.0,
            "probation_baseline_demo_allowed": True,
            "probation_ml_topup_allowed": False,
        },
        "per_source": per_source,
        "probation_source_ids": probation_sources,
        "checks": checks,
        "limitations": [
            "This is fixed-0.01-lot historical research evidence, not a profit promise.",
            "The new activation-equity risk controls are runtime safety controls and are not retroactively optimized into this ledger.",
            "R1 historical rows do not carry comparable initial-risk fields, so aggregate risk parity is enforced prospectively by the broker stop geometry and runtime caps.",
        ],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(artifact, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifact, allow_nan=False, indent=2, sort_keys=True))
    return 0 if artifact["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
