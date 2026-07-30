from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from build_v57_post_loss_cooldown_impact import (
    apply_post_loss_cooldowns,
    metrics,
    sha256_file,
)

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
    / "xau-usd/xauusd-fast-research/causal-canonical-profit-policy-v12"
    / "outputs/PROFIT_POLICY_V12_OUT_OF_TIME_PREDICTIONS.parquet"
)
FINAL_POLICY_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/causal-canonical-profit-policy-v12"
    / "outputs/PROFIT_POLICY_V12_FINAL_RESEARCH_POLICY.json"
)
LEDGER_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/one-trade-per-day-floating-equity-v60"
    / "outputs/ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet"
)
CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"

EXPECTED_SHA256 = {
    CANONICAL_PATH: "fc4771063013cf3633192715d2124c374cf37b44b1be9c1fddde7f67741fbc45",
    PREDICTIONS_PATH: "89e1f0704603e64afb47400a1c1ff6834e46ed861d9ba0fbac2b7a6ea720e4d6",
    FINAL_POLICY_PATH: "e3a9ef530be38ac3ac3d7da443a7aad17baffeaef5d1f958c14de0fe8c3e1c28",
    LEDGER_PATH: "ba9044e0f5ef73292b3b243c39c6b9aa8d7f9921da33633b3354281f378b5bbf",
    CONFIG_PATH: "0e4f6a16e9e0e6fbd5e4798ad68bf126a020bbe4ec437bccf853b5e1b6018629",
}

EXCLUDED_FAMILY = "R5_TRANSITION"
EXPECTED_JOINED_TRADES = 2184
FINAL_END = pd.Timestamp("2026-07-01T00:00:00Z")
WINDOW_MONTHS = (3, 6, 12, 24, 60, 120)
FOLD_YEARS = range(2020, 2026)

SUMMARY_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_COMPARISON.json"
WINDOWS_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_WINDOWS.csv"
FOLDS_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_FOLDS.csv"
MONTHLY_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_LAST_12_MONTHS.csv"
FAMILY_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_LAST_12_MONTHS_BY_FAMILY.csv"
AUDIT_CSV_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_TRADE_AUDIT.csv"
AUDIT_PARQUET_PATH = REPORTS / "V60_ML_V12_PROFIT_POLICY_TRADE_AUDIT.parquet"


def relative_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def verify_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in EXPECTED_SHA256.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256_file(path)
        if digest != expected:
            raise ValueError(
                f"Input hash changed for {relative_path(path)}: "
                f"expected {expected}, observed {digest}"
            )
        observed[relative_path(path)] = digest
    return observed


def load_cooldowns() -> dict[str, int]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        str(source["source_id"]): int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        )
        for source in config["sources"]
        if int(source.get("same_direction_post_loss_cooldown_minutes", 0)) > 0
    }


def load_final_policy() -> dict[str, Any]:
    return json.loads(FINAL_POLICY_PATH.read_text(encoding="utf-8"))


def load_joined_trades() -> tuple[pd.DataFrame, dict[str, bool]]:
    canonical = pd.read_parquet(CANONICAL_PATH)
    predictions = pd.read_parquet(PREDICTIONS_PATH)
    ledger = pd.read_parquet(LEDGER_PATH)

    canonical = canonical.loc[
        canonical["historical_portfolio_accepted"].astype(bool)
        & canonical["family_id"].ne(EXCLUDED_FAMILY),
        [
            "candidate_id",
            "family_id",
            "decision_time",
            "xau_feature_status",
            "crossasset_feature_status",
            "comex_feature_status",
        ],
    ].copy()
    canonical["join_minute"] = canonical["decision_time"].dt.floor("min")

    ledger = ledger.loc[ledger["specialist_id"].ne(EXCLUDED_FAMILY)].copy()
    ledger["family_id"] = ledger["specialist_id"].fillna(ledger["sleeve_id"])
    ledger["join_minute"] = ledger["signal_time"].dt.floor("min")

    checks = {
        "canonical_accepted_non_r5_count": len(canonical) == EXPECTED_JOINED_TRADES,
        "ledger_non_r5_count": len(ledger) == EXPECTED_JOINED_TRADES,
        "canonical_join_keys_unique": not canonical.duplicated(
            ["family_id", "join_minute"]
        ).any(),
        "ledger_join_keys_unique": not ledger.duplicated(
            ["family_id", "join_minute"]
        ).any(),
        "canonical_candidate_ids_unique": not canonical["candidate_id"]
        .duplicated()
        .any(),
        "prediction_candidate_ids_unique": not predictions["candidate_id"]
        .duplicated()
        .any(),
    }

    joined = ledger.merge(
        canonical,
        on=["family_id", "join_minute"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    checks["exact_one_to_one_portfolio_join"] = bool(joined["_merge"].eq("both").all())
    checks["joined_count"] = len(joined) == EXPECTED_JOINED_TRADES
    joined = joined.drop(columns="_merge")

    prediction_columns = [
        "candidate_id",
        "fold_id",
        "model_score",
        "threshold",
        "v12_threshold",
        "v12_quantile",
        "v12_action",
        "selected",
    ]
    joined = joined.merge(
        predictions[prediction_columns],
        on="candidate_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    joined["v12_prediction_available"] = joined["_merge"].eq("both")
    joined = joined.drop(columns="_merge")
    joined["v12_retained"] = joined["selected"].fillna(True).astype(bool)
    joined["v12_action"] = joined["v12_action"].fillna("MODEL_ABSTAIN_RETAIN_ALL")

    checks.update(
        {
            "predicted_rows_have_selection": bool(
                joined.loc[joined["v12_prediction_available"], "selected"].notna().all()
            ),
            "missing_predictions_retain_all": bool(
                joined.loc[~joined["v12_prediction_available"], "v12_retained"].all()
            ),
            "missing_predictions_abstain": bool(
                joined.loc[~joined["v12_prediction_available"], "v12_action"]
                .eq("MODEL_ABSTAIN_RETAIN_ALL")
                .all()
            ),
        }
    )
    failures = sorted(key for key, passed in checks.items() if not passed)
    if failures:
        raise ValueError(f"Exact V12 portfolio join failed closed: {failures}")

    joined = joined.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    return joined, checks


def metric_delta(
    raw_metrics: dict[str, Any], ml_metrics: dict[str, Any]
) -> dict[str, Any]:
    return {
        "trade_rows": ml_metrics["trade_rows"] - raw_metrics["trade_rows"],
        "net_pnl_usd": (ml_metrics["net_pnl_usd"] - raw_metrics["net_pnl_usd"]),
        "win_rate_percentage_points": 100.0
        * (ml_metrics["win_rate"] - raw_metrics["win_rate"]),
        "profit_factor": (ml_metrics["profit_factor"] - raw_metrics["profit_factor"]),
        "closed_trade_drawdown_usd": (
            ml_metrics["closed_trade_drawdown_usd"]
            - raw_metrics["closed_trade_drawdown_usd"]
        ),
    }


def replay_comparison(
    frame: pd.DataFrame, cooldowns: dict[str, int]
) -> tuple[dict[str, Any], pd.DataFrame]:
    raw_audit = apply_post_loss_cooldowns(frame, cooldowns).rename(
        columns={
            "post_loss_cooldown_accepted": "raw_cooldown_accepted",
            "post_loss_cooldown_reason": "raw_cooldown_reason",
        }
    )
    ml_input = frame.loc[frame["v12_retained"]].copy()
    ml_audit = apply_post_loss_cooldowns(ml_input, cooldowns).rename(
        columns={
            "post_loss_cooldown_accepted": "ml_cooldown_accepted",
            "post_loss_cooldown_reason": "ml_cooldown_reason",
        }
    )
    ml_decisions = ml_audit[["trade_id", "ml_cooldown_accepted", "ml_cooldown_reason"]]
    audit = raw_audit.merge(
        ml_decisions, on="trade_id", how="left", validate="one_to_one"
    )
    veto_mask = ~audit["v12_retained"]
    audit["ml_cooldown_accepted"] = (
        audit["ml_cooldown_accepted"].fillna(False).astype(bool)
    )
    audit.loc[veto_mask, "ml_cooldown_reason"] = "V12_VETO"

    raw_accepted = audit.loc[audit["raw_cooldown_accepted"]]
    ml_accepted = audit.loc[audit["ml_cooldown_accepted"]]
    raw_metrics = metrics(raw_accepted)
    ml_metrics = metrics(ml_accepted)
    comparison = {
        "raw": raw_metrics,
        "ml_v12": ml_metrics,
        "delta_ml_minus_raw": metric_delta(raw_metrics, ml_metrics),
        "v12_vetoed_before_cooldown": int(veto_mask.sum()),
        "model_abstained_retained_before_cooldown": int(
            audit["v12_action"].eq("MODEL_ABSTAIN_RETAIN_ALL").sum()
        ),
    }
    return comparison, audit


def row_from_comparison(
    label: str,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    raw = result["raw"]
    ml = result["ml_v12"]
    delta = result["delta_ml_minus_raw"]
    return {
        "period": label,
        "start_inclusive_utc": start.isoformat() if start is not None else None,
        "end_exclusive_utc": end.isoformat() if end is not None else None,
        "raw_trades": raw["trade_rows"],
        "raw_net_pnl_usd": raw["net_pnl_usd"],
        "raw_win_rate_pct": raw["win_rate"] * 100.0,
        "raw_profit_factor": raw["profit_factor"],
        "raw_closed_trade_drawdown_usd": raw["closed_trade_drawdown_usd"],
        "ml_trades": ml["trade_rows"],
        "ml_net_pnl_usd": ml["net_pnl_usd"],
        "ml_win_rate_pct": ml["win_rate"] * 100.0,
        "ml_profit_factor": ml["profit_factor"],
        "ml_closed_trade_drawdown_usd": ml["closed_trade_drawdown_usd"],
        "delta_trades": delta["trade_rows"],
        "delta_net_pnl_usd": delta["net_pnl_usd"],
        "delta_win_rate_percentage_points": delta["win_rate_percentage_points"],
        "delta_profit_factor": delta["profit_factor"],
        "delta_closed_trade_drawdown_usd": delta["closed_trade_drawdown_usd"],
        "v12_vetoed_before_cooldown": result["v12_vetoed_before_cooldown"],
        "model_abstained_retained_before_cooldown": result[
            "model_abstained_retained_before_cooldown"
        ],
    }


def window_rows(
    trades: pd.DataFrame, cooldowns: dict[str, int]
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    audits: dict[str, pd.DataFrame] = {}
    for months in WINDOW_MONTHS:
        start = FINAL_END - pd.DateOffset(months=months)
        frame = trades.loc[
            trades["entry_time"].ge(start) & trades["entry_time"].lt(FINAL_END)
        ].copy()
        label = f"{months // 12}Y" if months >= 12 else f"{months}M"
        result, audit = replay_comparison(frame, cooldowns)
        rows.append(row_from_comparison(label, start, FINAL_END, result))
        audits[label] = audit

    result, audit = replay_comparison(trades, cooldowns)
    rows.append(row_from_comparison("ALL", None, None, result))
    audits["ALL"] = audit
    return pd.DataFrame(rows), audits


def fold_rows(trades: pd.DataFrame, cooldowns: dict[str, int]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for year in FOLD_YEARS:
        start = pd.Timestamp(f"{year}-07-01T00:00:00Z")
        end = pd.Timestamp(f"{year + 1}-07-01T00:00:00Z")
        frame = trades.loc[
            trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
        ].copy()
        result, _ = replay_comparison(frame, cooldowns)
        rows.append(row_from_comparison(f"F{year}", start, end, result))
    return pd.DataFrame(rows)


def grouped_rows(
    audit: pd.DataFrame, group_column: str, labels: Iterable[str]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for label in labels:
        group = audit.loc[audit[group_column].eq(label)]
        raw = metrics(group.loc[group["raw_cooldown_accepted"]])
        ml = metrics(group.loc[group["ml_cooldown_accepted"]])
        delta = metric_delta(raw, ml)
        rows.append(
            {
                group_column: label,
                "raw_trades": raw["trade_rows"],
                "raw_net_pnl_usd": raw["net_pnl_usd"],
                "raw_win_rate_pct": (
                    raw["win_rate"] * 100.0 if raw["win_rate"] is not None else None
                ),
                "raw_profit_factor": raw["profit_factor"],
                "raw_closed_trade_drawdown_usd": raw["closed_trade_drawdown_usd"],
                "ml_trades": ml["trade_rows"],
                "ml_net_pnl_usd": ml["net_pnl_usd"],
                "ml_win_rate_pct": (
                    ml["win_rate"] * 100.0 if ml["win_rate"] is not None else None
                ),
                "ml_profit_factor": ml["profit_factor"],
                "ml_closed_trade_drawdown_usd": ml["closed_trade_drawdown_usd"],
                "delta_trades": delta["trade_rows"],
                "delta_net_pnl_usd": delta["net_pnl_usd"],
                "delta_profit_factor": delta["profit_factor"],
                "delta_closed_trade_drawdown_usd": delta["closed_trade_drawdown_usd"],
            }
        )
    return pd.DataFrame(rows)


def build_outputs() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    input_hashes = verify_inputs()
    trades, data_checks = load_joined_trades()
    cooldowns = load_cooldowns()
    final_policy = load_final_policy()

    windows, audits = window_rows(trades, cooldowns)
    folds = fold_rows(trades, cooldowns)
    final_audit = audits["1Y"].copy()
    final_audit["month"] = final_audit["entry_time"].dt.strftime("%Y-%m")
    months = pd.period_range("2025-07", "2026-06", freq="M").astype(str)
    monthly = grouped_rows(final_audit, "month", months)
    families = sorted(final_audit["family_id"].unique())
    family = grouped_rows(final_audit, "family_id", families)

    window_index = windows.set_index("period")
    diagnostics = {
        "six_month_net_pnl_improved": bool(
            window_index.at["6M", "delta_net_pnl_usd"] > 0.0
        ),
        "twelve_month_net_pnl_improved": bool(
            window_index.at["1Y", "delta_net_pnl_usd"] > 0.0
        ),
        "twelve_month_profit_factor_improved": bool(
            window_index.at["1Y", "delta_profit_factor"] > 0.0
        ),
        "twelve_month_drawdown_not_worse": bool(
            window_index.at["1Y", "delta_closed_trade_drawdown_usd"] <= 0.0
        ),
        "all_history_net_pnl_improved": bool(
            window_index.at["ALL", "delta_net_pnl_usd"] > 0.0
        ),
        "all_history_profit_factor_improved": bool(
            window_index.at["ALL", "delta_profit_factor"] > 0.0
        ),
        "latest_three_month_net_pnl_improved": bool(
            window_index.at["3M", "delta_net_pnl_usd"] > 0.0
        ),
        "all_history_drawdown_not_worse": bool(
            window_index.at["ALL", "delta_closed_trade_drawdown_usd"] <= 0.0
        ),
        "final_policy_actively_filters": bool(
            float(final_policy["chosen_quantile"]) > 0.0
            and final_policy["selection_reason"]
            != "RETAIN_ALL_INSUFFICIENT_CALIBRATION_USD_IMPROVEMENT"
        ),
        "prospective_confirmation_available": False,
    }
    report = {
        "schema_version": "xauusd_v60_ml_v12_profit_policy_comparison_v1",
        "status": "POST_OUTCOME_DIAGNOSTIC_POSITIVE_NOT_DEPLOYABLE",
        "deployment_eligible": False,
        "input_sha256": input_hashes,
        "data_checks": data_checks,
        "methodology": {
            "population": "EXACT_HISTORICALLY_ROUTED_V60_TRADES_WITHOUT_R5",
            "join": "ONE_TO_ONE_BY_FAMILY_AND_SIGNAL_MINUTE",
            "model_policy": "V12_OUT_OF_TIME_PROFIT_POLICY_DECISIONS",
            "missing_prediction_action": "MODEL_ABSTAIN_RETAIN_ALL",
            "cooldown_replay": (
                "RAW_AND_ML_PATHS_REPLAYED_INDEPENDENTLY_WITH_CURRENT_"
                "V57_SAME_DIRECTION_POST_LOSS_COOLDOWN"
            ),
            "pnl_basis": "FEE_STRESSED_FIXED_0P01_LOT_USD",
            "period_end_exclusive_utc": FINAL_END.isoformat(),
            "excluded_family": EXCLUDED_FAMILY,
        },
        "counts": {
            "exact_joined_trades": len(trades),
            "v12_prediction_rows": int(trades["v12_prediction_available"].sum()),
            "model_abstain_retain_rows": int(
                (~trades["v12_prediction_available"]).sum()
            ),
        },
        "final_research_policy": final_policy,
        "diagnostic_checks": diagnostics,
        "authorization": {
            "offline_research_authorized": True,
            "python_serving_authorized": False,
            "ml_shadow_authorized": False,
            "ea_consumption_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
            "runtime_change_authorized": False,
        },
        "artifact_paths": {
            "windows_csv": relative_path(WINDOWS_PATH),
            "folds_csv": relative_path(FOLDS_PATH),
            "last_twelve_months_csv": relative_path(MONTHLY_PATH),
            "last_twelve_months_by_family_csv": relative_path(FAMILY_PATH),
            "trade_audit_csv": relative_path(AUDIT_CSV_PATH),
            "trade_audit_parquet": relative_path(AUDIT_PARQUET_PATH),
        },
        "limitations": [
            "Historical outcomes were exposed before this portfolio diagnostic; the apparent lift is not fresh proof.",
            "The V12 final forward policy retains all because calibration did not prove enough USD improvement.",
            "The overlay can veto already-routed V60 trades but cannot re-admit candidates rejected by the historical router.",
            "The latest three-month result is worse with V12, and all-history closed-trade drawdown is slightly worse.",
            "Prospective disjoint calibration and confirmation evidence is not yet available.",
            "Fixed-0.01-lot fee-stress history is not a profit promise.",
        ],
    }
    audit_columns = [
        "trade_id",
        "candidate_id",
        "family_id",
        "fold_id",
        "signal_time",
        "decision_time",
        "entry_time",
        "exit_time",
        "direction",
        "fee_stress_pnl_usd",
        "xau_feature_status",
        "crossasset_feature_status",
        "comex_feature_status",
        "v12_prediction_available",
        "model_score",
        "threshold",
        "v12_threshold",
        "v12_quantile",
        "v12_action",
        "v12_retained",
        "raw_cooldown_accepted",
        "raw_cooldown_reason",
        "ml_cooldown_accepted",
        "ml_cooldown_reason",
    ]
    return report, windows, folds, monthly, family, audits["ALL"][audit_columns]


def main() -> int:
    report, windows, folds, monthly, family, audit = build_outputs()
    REPORTS.mkdir(parents=True, exist_ok=True)
    windows.to_csv(WINDOWS_PATH, index=False)
    folds.to_csv(FOLDS_PATH, index=False)
    monthly.to_csv(MONTHLY_PATH, index=False)
    family.to_csv(FAMILY_PATH, index=False)
    audit.to_csv(AUDIT_CSV_PATH, index=False)
    audit.to_parquet(AUDIT_PARQUET_PATH, index=False)
    SUMMARY_PATH.write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
