from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
REPORTS = ROOT / "reports"

CANONICAL_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1"
    / "outputs/step_3/STEP_3_CANONICAL_DATASET.parquet"
)
PREDICTIONS_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research"
    / "causal-canonical-expected-r-availability-v11"
    / "outputs/AVAILABILITY_V11_OUT_OF_TIME_PREDICTIONS.parquet"
)
LEDGER_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet"
)

EXPECTED_SHA256 = {
    CANONICAL_PATH: "fc4771063013cf3633192715d2124c374cf37b44b1be9c1fddde7f67741fbc45",
    PREDICTIONS_PATH: "060dcd0e4e03e025dd4d4ce4426f6c1f32ac7e304549692d9d9909b7e6c78202",
    LEDGER_PATH: "ba9044e0f5ef73292b3b243c39c6b9aa8d7f9921da33633b3354281f378b5bbf",
}

START = pd.Timestamp("2025-07-01T00:00:00Z")
END = pd.Timestamp("2026-07-01T00:00:00Z")
OUT_OF_TIME_FOLD = "F2025"
EXCLUDED_FAMILY = "R5_TRANSITION"
EXPECTED_RAW_TRADES = 363
EXPECTED_MONTHS = 12

SUMMARY_PATH = REPORTS / "V60_ML_V11_LAST_12_MONTHS_COMPARISON.json"
MONTHLY_PATH = REPORTS / "V60_ML_V11_LAST_12_MONTHS_COMPARISON.csv"
AUDIT_PATH = REPORTS / "V60_ML_V11_LAST_12_MONTHS_TRADE_AUDIT.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    cumulative = values.astype(float).cumsum()
    return float((cumulative.cummax() - cumulative).max())


def realized_exit_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    realized = (
        frame.groupby("exit_time", sort=True)["fee_stress_pnl_usd"].sum().cumsum()
    )
    return float((realized.cummax() - realized).max())


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame["fee_stress_pnl_usd"].astype(float)
    gross_profit = float(values.clip(lower=0.0).sum())
    gross_loss = float(-values.clip(upper=0.0).sum())
    return {
        "trades": int(len(frame)),
        "net_pnl_usd": float(values.sum()),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": -gross_loss,
        "win_rate": float(values.gt(0.0).mean()) if len(values) else None,
        "profit_factor": (
            float(gross_profit / gross_loss) if gross_loss > 0.0 else None
        ),
        "average_pnl_usd": float(values.mean()) if len(values) else None,
        "closed_trade_drawdown_usd": drawdown(values),
        "realized_exit_drawdown_usd": realized_exit_drawdown(frame),
    }


def verify_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in EXPECTED_SHA256.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256_file(path)
        if digest != expected:
            raise ValueError(f"Input hash changed: {path}")
        observed[path.relative_to(REPO_ROOT).as_posix()] = digest
    return observed


def load_joined_trades() -> tuple[pd.DataFrame, dict[str, bool]]:
    canonical = pd.read_parquet(CANONICAL_PATH)
    predictions = pd.read_parquet(PREDICTIONS_PATH)
    ledger = pd.read_parquet(LEDGER_PATH)

    canonical = canonical.loc[
        canonical["historical_portfolio_accepted"].astype(bool)
        & canonical["decision_time"].ge(START)
        & canonical["decision_time"].lt(END)
        & canonical["family_id"].ne(EXCLUDED_FAMILY)
    ].copy()
    predictions = predictions.loc[
        predictions["fold_id"].eq(OUT_OF_TIME_FOLD),
        [
            "candidate_id",
            "model_score",
            "threshold",
            "selected",
            "model_available",
            "availability_action",
        ],
    ].copy()
    canonical = canonical.merge(
        predictions, on="candidate_id", how="left", validate="one_to_one"
    )

    pass_mask = canonical["xau_feature_status"].eq("PASS")
    abstain_mask = canonical["xau_feature_status"].ne("PASS")
    checks = {
        "raw_trade_count_matches": len(canonical) == EXPECTED_RAW_TRADES,
        "pass_rows_have_frozen_predictions": bool(
            canonical.loc[pass_mask, "model_score"].notna().all()
        ),
        "nonpass_rows_have_no_prediction": bool(
            canonical.loc[abstain_mask, "model_score"].isna().all()
        ),
        "predicted_rows_use_available_model": bool(
            canonical.loc[pass_mask, "model_available"].astype(bool).all()
        ),
        "predicted_rows_use_frozen_v11_action": bool(
            canonical.loc[pass_mask, "availability_action"]
            .eq("APPLY_FROZEN_V10_SELECTION")
            .all()
        ),
    }
    canonical["ml_retained"] = canonical["selected"].fillna(True).astype(bool)
    canonical["ml_action"] = np.where(
        pass_mask,
        np.where(canonical["ml_retained"], "RETAIN", "VETO"),
        "MODEL_ABSTAIN_RETAIN_ALL",
    )
    canonical["join_minute"] = canonical["decision_time"].dt.floor("min")

    ledger = ledger.loc[
        ledger["specialist_id"].ne(EXCLUDED_FAMILY)
        & ledger["entry_time"].ge(START)
        & ledger["entry_time"].lt(END)
    ].copy()
    ledger["family_id"] = ledger["specialist_id"].fillna(ledger["sleeve_id"])
    ledger["join_minute"] = ledger["signal_time"].dt.floor("min")
    checks["ledger_trade_count_matches"] = len(ledger) == EXPECTED_RAW_TRADES
    checks["canonical_join_keys_unique"] = not canonical.duplicated(
        ["family_id", "join_minute"]
    ).any()
    checks["ledger_join_keys_unique"] = not ledger.duplicated(
        ["family_id", "join_minute"]
    ).any()

    joined = canonical.merge(
        ledger,
        on=["family_id", "join_minute"],
        how="outer",
        validate="one_to_one",
        indicator=True,
        suffixes=("_canonical", "_ledger"),
    )
    checks["exact_one_to_one_trade_join"] = bool(joined["_merge"].eq("both").all())
    checks["joined_trade_count_matches"] = len(joined) == EXPECTED_RAW_TRADES
    if not all(checks.values()):
        failures = sorted(key for key, value in checks.items() if not value)
        raise ValueError(f"Historical ML comparison failed closed: {failures}")

    joined = joined.sort_values(
        ["entry_time_ledger", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    joined["month"] = joined["entry_time_ledger"].dt.strftime("%Y-%m")
    joined["ml_pnl_usd"] = np.where(
        joined["ml_retained"], joined["fee_stress_pnl_usd"], 0.0
    )
    return joined, checks


def monthly_comparison(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for month, raw in trades.groupby("month", sort=True):
        retained = raw.loc[raw["ml_retained"]]
        raw_metrics = metrics(raw)
        ml_metrics = metrics(retained)
        rows.append(
            {
                "month": month,
                "raw_trades": raw_metrics["trades"],
                "raw_pnl_usd": raw_metrics["net_pnl_usd"],
                "raw_win_rate_pct": float(raw_metrics["win_rate"]) * 100.0,
                "raw_profit_factor": raw_metrics["profit_factor"],
                "ml_retained_trades": ml_metrics["trades"],
                "ml_vetoed_trades": int(len(raw) - len(retained)),
                "ml_abstained_retained_trades": int(
                    retained["ml_action"].eq("MODEL_ABSTAIN_RETAIN_ALL").sum()
                ),
                "ml_pnl_usd": ml_metrics["net_pnl_usd"],
                "ml_win_rate_pct": float(ml_metrics["win_rate"]) * 100.0,
                "ml_profit_factor": ml_metrics["profit_factor"],
                "ml_minus_raw_pnl_usd": float(
                    ml_metrics["net_pnl_usd"] - raw_metrics["net_pnl_usd"]
                ),
                "ml_trade_retention_pct": 100.0 * len(retained) / len(raw),
            }
        )
    result = pd.DataFrame(rows)
    if len(result) != EXPECTED_MONTHS:
        raise ValueError(f"Expected {EXPECTED_MONTHS} monthly rows")
    return result


def audit_frame(trades: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "trade_id",
        "candidate_id",
        "month",
        "family_id",
        "decision_time",
        "entry_time_ledger",
        "exit_time",
        "direction_ledger",
        "xau_feature_status",
        "model_score",
        "threshold",
        "ml_action",
        "ml_retained",
        "fee_stress_pnl_usd",
        "ml_pnl_usd",
    ]
    return trades[columns].rename(
        columns={
            "decision_time": "decision_time_utc",
            "entry_time_ledger": "entry_time_utc",
            "exit_time": "exit_time_utc",
            "direction_ledger": "direction",
            "fee_stress_pnl_usd": "raw_pnl_usd",
        }
    )


def main() -> int:
    input_hashes = verify_inputs()
    trades, checks = load_joined_trades()
    monthly = monthly_comparison(trades)
    raw = metrics(trades)
    retained_trades = trades.loc[trades["ml_retained"]].copy()
    vetoed_trades = trades.loc[~trades["ml_retained"]].copy()
    retained = metrics(retained_trades)
    vetoed = metrics(vetoed_trades)

    checks.update(
        {
            "all_months_present": len(monthly) == EXPECTED_MONTHS,
            "raw_pnl_reconciles": bool(
                np.isclose(
                    float(monthly["raw_pnl_usd"].sum()),
                    float(raw["net_pnl_usd"]),
                    rtol=0.0,
                    atol=1e-9,
                )
            ),
            "ml_pnl_reconciles": bool(
                np.isclose(
                    float(monthly["ml_pnl_usd"].sum()),
                    float(retained["net_pnl_usd"]),
                    rtol=0.0,
                    atol=1e-9,
                )
            ),
            "raw_equals_retained_plus_vetoed": bool(
                np.isclose(
                    float(raw["net_pnl_usd"]),
                    float(retained["net_pnl_usd"])
                    + float(vetoed["net_pnl_usd"]),
                    rtol=0.0,
                    atol=1e-9,
                )
            ),
        }
    )
    if not all(checks.values()):
        raise ValueError("Final historical ML reconciliation failed")

    summary = {
        "schema_version": "xauusd_v60_ml_v11_last_12_months_comparison_v1",
        "status": "PASS",
        "period": {
            "start_inclusive_utc": START.isoformat().replace("+00:00", "Z"),
            "end_exclusive_utc": END.isoformat().replace("+00:00", "Z"),
            "entry_month_basis": True,
        },
        "methodology": {
            "model_policy": "FROZEN_EXPECTED_R_V10_WITH_V11_AVAILABILITY",
            "prediction_fold": OUT_OF_TIME_FOLD,
            "population": "EXACT_HISTORICALLY_ROUTED_V60_TRADES_WITHOUT_R5",
            "overlay_position": "POST_FROZEN_V60_ROUTING",
            "missing_feature_action": "MODEL_ABSTAIN_RETAIN_ALL",
            "pnl_basis": "FEE_STRESSED_FIXED_0P01_LOT_USD",
            "runtime_or_demo_authorized": False,
        },
        "input_sha256": input_hashes,
        "counts": {
            "raw_trades": int(len(trades)),
            "model_scored_trades": int(trades["model_score"].notna().sum()),
            "model_abstained_retained_trades": int(
                trades["ml_action"].eq("MODEL_ABSTAIN_RETAIN_ALL").sum()
            ),
            "ml_retained_trades": int(trades["ml_retained"].sum()),
            "ml_vetoed_trades": int((~trades["ml_retained"]).sum()),
        },
        "raw": raw,
        "ml_v11_overlay": retained,
        "vetoed": vetoed,
        "delta": {
            "ml_minus_raw_pnl_usd": float(
                retained["net_pnl_usd"] - raw["net_pnl_usd"]
            ),
            "win_rate_percentage_points": 100.0
            * (float(retained["win_rate"]) - float(raw["win_rate"])),
            "profit_factor": float(retained["profit_factor"])
            - float(raw["profit_factor"]),
            "closed_trade_drawdown_usd": float(
                retained["closed_trade_drawdown_usd"]
                - raw["closed_trade_drawdown_usd"]
            ),
            "trade_retention": len(retained_trades) / len(trades),
        },
        "profitable_months": {
            "raw": int(monthly["raw_pnl_usd"].gt(0.0).sum()),
            "ml_v11_overlay": int(monthly["ml_pnl_usd"].gt(0.0).sum()),
        },
        "checks": checks,
        "limitations": [
            "This is a historical research calculation, not a profit promise.",
            "Historical outcomes were exposed during model development; prospective confirmation remains mandatory.",
            "The overlay vetoes exact already-routed V60 trades. It does not re-admit candidates that historical routing rejected after an ML veto frees capacity.",
            "ML remains unauthorized for MT5 shadowing, demo filtering, live trading, sizing, or broker action.",
        ],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(MONTHLY_PATH, index=False)
    audit_frame(trades).to_csv(AUDIT_PATH, index=False)
    SUMMARY_PATH.write_text(
        json.dumps(summary, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
