from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_v57_post_loss_cooldown_impact import apply_post_loss_cooldowns


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
    baseline = ledger.loc[ledger["specialist_id"].ne("R5_TRANSITION")].copy()
    audited = apply_post_loss_cooldowns(baseline, cooldowns)
    filtered = audited.loc[audited["post_loss_cooldown_accepted"]].copy()
    window = filtered.loc[
        filtered["entry_time"].ge(FINAL_WINDOW_START)
        & filtered["entry_time"].lt(FINAL_WINDOW_END)
    ].copy()
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
