from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


POLICY_FEATURE_COLUMNS = (
    "execution_source_id",
    "direction",
    "rank",
    "atr_ratio",
    "dist_hi_24h",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_locked_config(path: Path, repo_root: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    for name, item in config["inputs"].items():
        source = resolve(repo_root, str(item["path"]))
        expected = str(item["sha256"])
        if expected == "GENERATE_BEFORE_EXPERIMENT":
            raise ValueError(f"Input hash is not locked: {name}")
        actual = sha256_file(source)
        if actual != expected:
            raise ValueError(f"Input identity changed: {name}: {actual}")
    return config


def policy_mask(frame: pd.DataFrame, rule: Mapping[str, Any]) -> pd.Series:
    missing = set(POLICY_FEATURE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing causal policy features: {sorted(missing)}")
    numeric = frame[["rank", "atr_ratio", "dist_hi_24h"]].apply(
        pd.to_numeric, errors="coerce"
    )
    finite = np.isfinite(numeric).all(axis=1)
    return (
        frame["execution_source_id"].eq(str(rule["source_id"]))
        & frame["direction"].str.upper().eq(str(rule["direction"]).upper())
        & finite
        & numeric["rank"].lt(float(rule["maximum_causal_rank_exclusive"]))
        & numeric["atr_ratio"].ge(float(rule["minimum_atr_ratio_inclusive"]))
        & numeric["dist_hi_24h"].lt(
            float(rule["maximum_distance_to_24h_high_atr_exclusive"])
        )
    )


def closed_metrics(values: Sequence[float]) -> dict[str, Any]:
    pnl = np.asarray(values, dtype=float)
    if not np.isfinite(pnl).all():
        raise ValueError("P/L contains a nonfinite value")
    wins = pnl[pnl > 0.0]
    losses = pnl[pnl < 0.0]
    gross_profit = float(wins.sum())
    gross_loss = -float(losses.sum())
    equity = np.concatenate([[0.0], np.cumsum(pnl)])
    drawdown = np.maximum.accumulate(equity) - equity
    return {
        "trades": int(len(pnl)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "win_rate": float(len(wins) / len(pnl)) if len(pnl) else None,
        "closed_drawdown_usd": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def august_comparison(
    broker_audit: pd.DataFrame,
    causal_features: pd.DataFrame,
    rule: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    features = causal_features.copy()
    if features["candidate_id"].duplicated().any():
        raise ValueError("August causal feature snapshot has duplicate candidates")
    rows = broker_audit.copy()
    rows = rows.loc[
        rows["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & rows["baseline_executed"].astype(str).str.lower().eq("true")
        & rows["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    rows = rows.merge(features, on="candidate_id", how="left", validate="one_to_one")
    if "rank" not in rows.columns and "causal_rank" in rows.columns:
        rows["rank"] = pd.to_numeric(rows["causal_rank"], errors="coerce")
    eligible = policy_mask(rows, rule)
    mature = pd.to_numeric(
        rows["prior_source_executed_count"], errors="coerce"
    ).ge(int(rule["minimum_prior_source_closed_trades"]))
    rows["would_veto"] = eligible & mature
    rows["challenger_pnl_usd"] = np.where(
        rows["would_veto"], 0.0, pd.to_numeric(rows["broker_pnl_usd"])
    )
    rows = rows.sort_values(
        ["broker_exit_time_utc", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    baseline = closed_metrics(pd.to_numeric(rows["broker_pnl_usd"]))
    challenger = closed_metrics(
        pd.to_numeric(rows.loc[~rows["would_veto"], "broker_pnl_usd"])
    )
    veto_values = pd.to_numeric(rows.loc[rows["would_veto"], "broker_pnl_usd"])
    return (
        {
            "evidence_status": "RETROSPECTIVE_EXPOSED_NOT_PROSPECTIVE",
            "baseline_v60": baseline,
            "challenger": challenger,
            "vetoes": int(rows["would_veto"].sum()),
            "vetoed_broker_pnl_usd": float(veto_values.sum()),
            "avoided_broker_pnl_usd": -float(veto_values.sum()),
            "delta_net_pnl_usd": float(
                challenger["net_pnl_usd"] - baseline["net_pnl_usd"]
            ),
            "delta_closed_drawdown_usd": float(
                challenger["closed_drawdown_usd"]
                - baseline["closed_drawdown_usd"]
            ),
        },
        rows,
    )


def crossfeed_comparison(
    priced_runtime: pd.DataFrame,
    veto_trade_ids: set[str],
) -> dict[str, Any]:
    frame = priced_runtime.copy()
    covered = frame["dukascopy_covered"].astype(str).str.lower().eq("true")
    frame = frame.loc[covered].copy()
    frame["trade_id"] = frame["trade_id"].astype(str)
    frame["selected"] = frame["trade_id"].isin(veto_trade_ids)
    missing = veto_trade_ids - set(frame.loc[frame["selected"], "trade_id"])
    if missing:
        raise ValueError(f"Cross-feed evidence lacks selected trades: {sorted(missing)}")
    frame = frame.sort_values(
        ["runtime_exit_time_ms", "trade_id"], kind="stable"
    ).reset_index(drop=True)
    baseline = closed_metrics(
        pd.to_numeric(frame["dukascopy_spread_only_pnl_usd"])
    )
    challenger = closed_metrics(
        pd.to_numeric(
            frame.loc[~frame["selected"], "dukascopy_spread_only_pnl_usd"]
        )
    )
    veto = closed_metrics(
        pd.to_numeric(
            frame.loc[frame["selected"], "dukascopy_spread_only_pnl_usd"]
        )
    )
    annual = []
    years = pd.to_datetime(frame["runtime_entry_time_utc"], utc=True).dt.year
    for year in sorted(years.unique()):
        cohort = frame.loc[years.eq(year)]
        base_net = float(
            pd.to_numeric(cohort["dukascopy_spread_only_pnl_usd"]).sum()
        )
        changed_net = float(
            pd.to_numeric(
                cohort.loc[
                    ~cohort["selected"], "dukascopy_spread_only_pnl_usd"
                ]
            ).sum()
        )
        annual.append(
            {
                "year": int(year),
                "baseline_net_pnl_usd": base_net,
                "challenger_net_pnl_usd": changed_net,
                "delta_net_pnl_usd": changed_net - base_net,
            }
        )
    return {
        "evidence_status": "INDEPENDENT_PRICE_PATH_POST_SELECTED_TIMING",
        "baseline": baseline,
        "challenger": challenger,
        "veto_cohort": veto,
        "covered_vetoes": int(frame["selected"].sum()),
        "delta_net_pnl_usd": float(
            challenger["net_pnl_usd"] - baseline["net_pnl_usd"]
        ),
        "delta_closed_drawdown_usd": float(
            challenger["closed_drawdown_usd"] - baseline["closed_drawdown_usd"]
        ),
        "annual": annual,
        "every_year_nonnegative": all(
            row["delta_net_pnl_usd"] >= 0.0 for row in annual
        ),
    }
