from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


REQUIRED_PROPOSAL_COLUMNS = ("trade_id", "entry_time_utc", "source_id", "proposal_rule")


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
        actual = sha256_file(source)
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")
    return config


def normalize_proposals(rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows))
    missing = set(REQUIRED_PROPOSAL_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Proposal metadata missing: {sorted(missing)}")
    frame = frame.loc[:, REQUIRED_PROPOSAL_COLUMNS].copy()
    if frame[list(REQUIRED_PROPOSAL_COLUMNS)].isna().any().any():
        raise ValueError("Proposal metadata contains null values")
    frame["trade_id"] = frame["trade_id"].astype(str)
    frame["source_id"] = frame["source_id"].astype(str)
    frame["proposal_rule"] = frame["proposal_rule"].astype(str)
    frame["entry_time_utc"] = pd.to_datetime(frame["entry_time_utc"], utc=True)
    if frame["entry_time_utc"].isna().any():
        raise ValueError("Proposal entry time is invalid")

    identity_counts = frame.groupby("trade_id", sort=False).agg(
        entry_times=("entry_time_utc", "nunique"),
        source_ids=("source_id", "nunique"),
    )
    inconsistent = identity_counts.loc[
        identity_counts["entry_times"].gt(1) | identity_counts["source_ids"].gt(1)
    ]
    if not inconsistent.empty:
        raise ValueError(f"Conflicting proposal identity: {sorted(inconsistent.index)}")

    deduplicated = (
        frame.groupby(["trade_id", "entry_time_utc", "source_id"], as_index=False)
        .agg(proposal_rule=("proposal_rule", lambda value: "+".join(sorted(set(value)))))
        .sort_values(["entry_time_utc", "trade_id"], kind="stable")
        .reset_index(drop=True)
    )
    return deduplicated


def apply_source_day_budget(
    proposals: pd.DataFrame, maximum_vetoes: int
) -> pd.DataFrame:
    if maximum_vetoes < 1:
        raise ValueError("Maximum source/day vetoes must be positive")
    rows = normalize_proposals(proposals.to_dict("records"))
    rows["utc_day"] = rows["entry_time_utc"].dt.strftime("%Y-%m-%d")
    rows["source_day_sequence"] = rows.groupby(
        ["source_id", "utc_day"], sort=False
    ).cumcount() + 1
    rows["selected_veto"] = rows["source_day_sequence"].le(maximum_vetoes)
    rows["budget_action"] = rows["selected_veto"].map(
        {True: "VETO", False: "RETAIN_SOURCE_DAY_BUDGET"}
    )
    return rows


def closed_metrics(values: pd.Series) -> dict[str, Any]:
    pnl = pd.to_numeric(values, errors="raise").astype(float)
    wins = pnl.loc[pnl.gt(0.0)]
    losses = pnl.loc[pnl.lt(0.0)]
    gross_profit = float(wins.sum())
    gross_loss = -float(losses.sum())
    equity = pd.Series([0.0, *pnl.cumsum().tolist()], dtype=float)
    drawdown = equity.cummax() - equity
    return {
        "trades": int(len(pnl)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "win_rate": float(len(wins) / len(pnl)) if len(pnl) else None,
        "closed_drawdown_usd": float(drawdown.max()),
    }


def august_comparison(
    broker_audit: pd.DataFrame,
    antichase_audit: pd.DataFrame,
    maximum_vetoes: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    broker = broker_audit.copy()
    broker = broker.loc[
        broker["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & broker["baseline_executed"].astype(str).str.lower().eq("true")
        & broker["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    anti = antichase_audit[["candidate_id", "would_veto"]].copy()
    anti["antichase_proposal"] = anti["would_veto"].astype(str).str.lower().eq("true")
    anti = anti.drop(columns="would_veto")
    broker = broker.merge(anti, on="candidate_id", how="left", validate="one_to_one")
    broker["v2_proposal"] = broker["would_veto"].astype(str).str.lower().eq("true")
    broker["antichase_proposal"] = broker["antichase_proposal"].fillna(False)

    proposal_rows: list[dict[str, Any]] = []
    for row in broker.to_dict("records"):
        rules = []
        if row["v2_proposal"]:
            rules.append("V2_SOURCE_HEALTH")
        if row["antichase_proposal"]:
            rules.append("V57_VOLATILITY_ANTICHASE")
        for rule in rules:
            proposal_rows.append(
                {
                    "trade_id": row["candidate_id"],
                    "entry_time_utc": row["entry_time_utc"],
                    "source_id": row["source_id"],
                    "proposal_rule": rule,
                }
            )
    if proposal_rows:
        budget = apply_source_day_budget(pd.DataFrame(proposal_rows), maximum_vetoes)
        selected = set(budget.loc[budget["selected_veto"], "trade_id"])
    else:
        budget = pd.DataFrame()
        selected = set()
    broker["combined_veto"] = broker["candidate_id"].astype(str).isin(selected)
    broker = broker.sort_values(["broker_exit_time_utc", "candidate_id"], kind="stable")
    baseline = closed_metrics(broker["broker_pnl_usd"])
    challenger = closed_metrics(broker.loc[~broker["combined_veto"], "broker_pnl_usd"])
    veto = closed_metrics(broker.loc[broker["combined_veto"], "broker_pnl_usd"])
    return (
        {
            "baseline_v60": baseline,
            "challenger": challenger,
            "veto_cohort": veto,
            "delta_net_pnl_usd": challenger["net_pnl_usd"] - baseline["net_pnl_usd"],
            "delta_closed_drawdown_usd": challenger["closed_drawdown_usd"]
            - baseline["closed_drawdown_usd"],
            "raw_proposals": int(len(budget)),
            "selected_vetoes": int(len(selected)),
        },
        broker,
    )
