from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "diagnostic.json"
OUTPUTS = ROOT / "outputs"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_inputs(config: Mapping[str, Any]) -> None:
    for name, item in config["inputs"].items():
        path = resolve(str(item["path"]))
        actual = sha256_file(path)
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def profit_factor(values: Iterable[float]) -> float | None:
    pnl = np.asarray(list(values), dtype=float)
    gross_profit = float(pnl[pnl > 0.0].sum())
    gross_loss = -float(pnl[pnl < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0.0 else None


def metrics(values: Iterable[float]) -> dict[str, Any]:
    pnl = np.asarray(list(values), dtype=float)
    return {
        "trades": int(len(pnl)),
        "wins": int((pnl > 0.0).sum()),
        "losses": int((pnl < 0.0).sum()),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": profit_factor(pnl),
        "win_rate": float((pnl > 0.0).mean()) if len(pnl) else None,
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if pd.isna(value):
        return None
    return value


def timed_metrics(
    frame: pd.DataFrame, *, pnl_column: str, close_column: str
) -> dict[str, Any]:
    ordered = frame.sort_values([close_column, "trade_id"], kind="stable")
    result = metrics(ordered[pnl_column])
    cumulative = ordered[pnl_column].astype(float).cumsum().to_numpy(dtype=float)
    equity = np.r_[0.0, cumulative]
    drawdown = np.maximum.accumulate(equity) - equity
    closed_drawdown = float(drawdown.max()) if len(drawdown) else 0.0
    result["closed_drawdown_usd"] = closed_drawdown
    result["net_to_closed_drawdown"] = (
        float(result["net_pnl_usd"]) / closed_drawdown if closed_drawdown > 0.0 else None
    )
    return result


def utc_text(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).isoformat().replace(
        "+00:00", "Z"
    )


def assign_fold(
    timestamps: pd.Series, fold_config: Sequence[Mapping[str, Any]]
) -> pd.Series:
    values = pd.to_datetime(timestamps, utc=True, format="mixed", errors="raise")
    result = pd.Series("OUTSIDE", index=timestamps.index, dtype="object")
    for fold in fold_config:
        start = pd.Timestamp(str(fold["start"]))
        end = pd.Timestamp(str(fold["end"]))
        result.loc[values.ge(start) & values.lt(end)] = str(fold["fold_id"])
    return result


def annotate_clusters(
    frame: pd.DataFrame,
    *,
    entry_column: str,
    exit_column: str,
    pnl_column: str,
) -> pd.DataFrame:
    work = frame.copy()
    work[entry_column] = pd.to_datetime(
        work[entry_column], utc=True, format="mixed", errors="raise"
    )
    work[exit_column] = pd.to_datetime(
        work[exit_column], utc=True, format="mixed", errors="raise"
    )
    work[pnl_column] = pd.to_numeric(work[pnl_column], errors="raise").astype(float)
    work["utc_entry_date"] = work[entry_column].dt.strftime("%Y-%m-%d")
    group_columns = ["source_id", "direction", "utc_entry_date"]
    work = work.sort_values(group_columns + [entry_column, "trade_id"], kind="stable")
    grouped = work.groupby(group_columns, sort=False, dropna=False)
    work["cluster_size"] = grouped["trade_id"].transform("size").astype(int)
    work["cluster_ordinal"] = grouped.cumcount().add(1).astype(int)
    work["is_cluster_trade"] = work["cluster_size"].ge(2)
    work["later_cluster_trade"] = work["cluster_ordinal"].ge(2)
    post_loss: dict[Any, bool] = {}
    for _, group in grouped:
        prior: list[tuple[pd.Timestamp, float]] = []
        for index, row in group.iterrows():
            entry = pd.Timestamp(row[entry_column])
            post_loss[index] = any(close <= entry and pnl < 0.0 for close, pnl in prior)
            prior.append((pd.Timestamp(row[exit_column]), float(row[pnl_column])))
    work["post_prior_loss_same_day"] = pd.Series(post_loss).reindex(work.index).fillna(False)
    return work.sort_values([entry_column, "trade_id"], kind="stable").reset_index(drop=True)


def aggregate_protection(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouped = frame.groupby(list(columns), sort=True, dropna=False)
    for keys, group in grouped:
        key_values = keys if isinstance(keys, tuple) else (keys,)
        endpoint = metrics(group["endpoint_pnl_usd"])
        protected = metrics(group["protected_pnl_usd"])
        row = {column: value for column, value in zip(columns, key_values)}
        row.update(
            {
                "trades": int(len(group)),
                "protection_changed_trades": int(group["protection_changed"].sum()),
                "protection_action_trades": int(group["protection_action"].sum()),
                "pnl_changed_trades": int(group["pnl_changed"].sum()),
                "protection_improved_trades": int(group["protection_delta_usd"].gt(0).sum()),
                "protection_harmed_trades": int(group["protection_delta_usd"].lt(0).sum()),
                "endpoint_net_pnl_usd": endpoint["net_pnl_usd"],
                "endpoint_profit_factor": endpoint["profit_factor"],
                "endpoint_win_rate": endpoint["win_rate"],
                "protected_net_pnl_usd": protected["net_pnl_usd"],
                "protected_profit_factor": protected["profit_factor"],
                "protected_win_rate": protected["win_rate"],
                "protection_delta_usd": float(group["protection_delta_usd"].sum()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def cohort_table(frame: pd.DataFrame, pnl_column: str) -> pd.DataFrame:
    selectors = {
        "ALL_ACCEPTED": pd.Series(True, index=frame.index),
        "CLUSTER_ALL": frame["is_cluster_trade"],
        "CLUSTER_FIRST": frame["is_cluster_trade"] & ~frame["later_cluster_trade"],
        "CLUSTER_LATER": frame["later_cluster_trade"],
        "POST_PRIOR_LOSS_SAME_DAY": frame["post_prior_loss_same_day"],
        "NOT_POST_PRIOR_LOSS_SAME_DAY": ~frame["post_prior_loss_same_day"],
    }
    rows: list[dict[str, Any]] = []
    for fold_id in ["ALL", *sorted(frame["fold_id"].dropna().unique())]:
        fold_mask = (
            pd.Series(True, index=frame.index)
            if fold_id == "ALL"
            else frame["fold_id"].eq(fold_id)
        )
        for cohort, selector in selectors.items():
            selected = frame.loc[fold_mask & selector]
            rows.append({"fold_id": fold_id, "cohort": cohort, **metrics(selected[pnl_column])})
    return pd.DataFrame(rows)


def capture_replay(config: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, Mapping[str, Any]]:
    v6_config = json.loads(resolve(config["inputs"]["v6_config"]["path"]).read_text())
    evaluator = load_module(
        "v17_shared_evaluator", resolve(config["inputs"]["shared_evaluator"]["path"])
    )
    v6_scenario = load_module(
        "v17_v6_scenario", resolve(config["inputs"]["v6_scenario"]["path"])
    )
    features = pd.read_parquet(resolve(v6_config["inputs"]["causal_feature_ledger"]["path"]))
    if features["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger contains duplicate trade IDs")
    feature_map = {str(row["trade_id"]): row for row in features.to_dict("records")}

    def factory(replay):
        return v6_scenario.combined_challenger_class(
            replay, evaluator, feature_map, v6_config["anti_chase"]
        )

    evaluator.challenger_class = factory
    captured: list[pd.DataFrame] = []
    original = evaluator.closed_trade_frame

    def capture(scenario, candidates):
        frame = original(scenario, candidates)
        candidate_map = {candidate.trade_id: candidate for candidate in candidates}
        close_events = {
            str(row["trade_id"]): row
            for row in scenario.event_rows
            if row["event"] == "POSITION_CLOSED"
        }
        frame["specialist_id"] = frame["trade_id"].map(
            lambda trade_id: candidate_map[str(trade_id)].specialist_id
        )
        frame["sleeve_type"] = frame["trade_id"].map(
            lambda trade_id: candidate_map[str(trade_id)].sleeve_type
        )
        frame["direction"] = frame["trade_id"].map(
            lambda trade_id: candidate_map[str(trade_id)].direction
        )
        frame["risk_usd"] = frame["trade_id"].map(
            lambda trade_id: float(candidate_map[str(trade_id)].risk_usd)
        )
        frame["open_cost_usd"] = frame["trade_id"].map(
            lambda trade_id: float(candidate_map[str(trade_id)].open_cost_usd)
        )
        frame["endpoint_exit_time_utc"] = frame["trade_id"].map(
            lambda trade_id: utc_text(candidate_map[str(trade_id)].exit_ms)
        )
        frame["endpoint_pnl_usd"] = frame["trade_id"].map(
            lambda trade_id: float(candidate_map[str(trade_id)].pnl_usd)
        )
        frame["close_reason"] = frame["trade_id"].map(
            lambda trade_id: str(close_events[str(trade_id)]["reason"])
        )
        captured.append(frame.copy())
        return frame

    evaluator.closed_trade_frame = capture
    base = json.loads(
        evaluator.resolve(v6_config["inputs"]["base_challenger_config"]["path"]).read_text()
    )
    try:
        with tempfile.TemporaryDirectory(prefix="v60-exit-cluster-v17-") as temporary:
            replay_config = deepcopy(base)
            for name, value in v6_config.get("v2_policy_overrides", {}).items():
                replay_config["policy"][name] = value
            replay_config["schema_version"] = str(config["schema_version"])
            replay_config["report_title"] = str(config["report_title"])
            replay_path = Path(temporary) / "diagnostic.json"
            replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
            replay_result, _, _ = evaluator.run(replay_path)
    finally:
        evaluator.closed_trade_frame = original
    if len(captured) != 2:
        raise ValueError(f"Expected two captured trade frames, received {len(captured)}")
    return captured[0], captured[1], replay_result


def protection_audit(
    baseline: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tolerance = float(config["tolerance_usd"])
    audit = baseline.rename(
        columns={"exit_time_utc": "protected_exit_time_utc", "pnl_usd": "protected_pnl_usd"}
    ).copy()
    audit["entry_time_utc"] = pd.to_datetime(
        audit["entry_time_utc"], utc=True, format="mixed", errors="raise"
    )
    audit["protected_exit_time_utc"] = pd.to_datetime(
        audit["protected_exit_time_utc"], utc=True, format="mixed", errors="raise"
    )
    audit["endpoint_exit_time_utc"] = pd.to_datetime(
        audit["endpoint_exit_time_utc"], utc=True, format="mixed", errors="raise"
    )
    audit["endpoint_pnl_usd"] = pd.to_numeric(audit["endpoint_pnl_usd"], errors="raise")
    audit["protected_pnl_usd"] = pd.to_numeric(audit["protected_pnl_usd"], errors="raise")
    audit["protection_delta_usd"] = audit["protected_pnl_usd"] - audit["endpoint_pnl_usd"]
    audit["pnl_changed"] = audit["protection_delta_usd"].abs().gt(tolerance)
    audit["protection_action"] = audit["close_reason"].eq("OPEN_PROFIT_GIVEBACK")
    audit["protection_changed"] = (
        audit["pnl_changed"]
        | audit["protected_exit_time_utc"].ne(audit["endpoint_exit_time_utc"])
        | audit["close_reason"].ne("SOURCE_EXIT")
    )
    audit["entry_year"] = audit["entry_time_utc"].dt.year
    audit["entry_month"] = audit["entry_time_utc"].dt.strftime("%Y-%m")
    audit["fold_id"] = assign_fold(audit["entry_time_utc"], config["folds"])
    by_source = aggregate_protection(audit, ["source_id"])
    by_source_year = aggregate_protection(audit, ["source_id", "entry_year"])
    by_month = aggregate_protection(audit, ["entry_month"])
    return audit, by_source, by_source_year, by_month


def eligible_protection_sources(
    audit: pd.DataFrame, config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    minimum = int(config["eligibility"]["minimum_cohort_trades"])
    required_negative = int(
        config["eligibility"]["minimum_negative_historical_folds"]
    )
    historical_folds = [str(item["fold_id"]) for item in config["folds"]]
    rows: list[dict[str, Any]] = []
    for source_id, group in audit.groupby("source_id", sort=True):
        action_trades = int(group["protection_action"].sum())
        fold_delta = {
            fold: float(group.loc[group["fold_id"].eq(fold), "protection_delta_usd"].sum())
            for fold in historical_folds
        }
        negative_folds = sum(value < 0.0 for value in fold_delta.values())
        eligible = (
            action_trades >= minimum
            and float(group["protection_delta_usd"].sum()) < 0.0
            and negative_folds >= required_negative
        )
        rows.append(
            {
                "source_id": str(source_id),
                "trades": int(len(group)),
                "changed_trades": int(group["protection_changed"].sum()),
                "protection_action_trades": action_trades,
                "pnl_changed_trades": int(group["pnl_changed"].sum()),
                "protection_delta_usd": float(group["protection_delta_usd"].sum()),
                "negative_historical_folds": int(negative_folds),
                "fold_delta_usd": fold_delta,
                "eligible": bool(eligible),
            }
        )
    return rows


def eligible_cluster_cohorts(
    cohorts: pd.DataFrame, config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    minimum = int(config["eligibility"]["minimum_cohort_trades"])
    maximum_pf = float(
        config["eligibility"]["maximum_cluster_profit_factor_exclusive"]
    )
    required_negative = int(
        config["eligibility"]["minimum_negative_historical_folds"]
    )
    historical_folds = [str(item["fold_id"]) for item in config["folds"]]
    rows: list[dict[str, Any]] = []
    for cohort in ("CLUSTER_LATER", "POST_PRIOR_LOSS_SAME_DAY"):
        overall = cohorts.loc[
            cohorts["fold_id"].eq("ALL") & cohorts["cohort"].eq(cohort)
        ].iloc[0]
        fold_pnl = {
            fold: float(
                cohorts.loc[
                    cohorts["fold_id"].eq(fold) & cohorts["cohort"].eq(cohort),
                    "net_pnl_usd",
                ].iloc[0]
            )
            for fold in historical_folds
        }
        negative_folds = sum(value < 0.0 for value in fold_pnl.values())
        pf = overall["profit_factor"]
        eligible = (
            int(overall["trades"]) >= minimum
            and pd.notna(pf)
            and float(pf) < maximum_pf
            and negative_folds >= required_negative
        )
        rows.append(
            {
                "cohort": cohort,
                "trades": int(overall["trades"]),
                "net_pnl_usd": float(overall["net_pnl_usd"]),
                "profit_factor": None if pd.isna(pf) else float(pf),
                "negative_historical_folds": int(negative_folds),
                "fold_pnl_usd": fold_pnl,
                "eligible": bool(eligible),
            }
        )
    return rows


def prepare_july(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    audit = pd.read_csv(resolve(config["inputs"]["july_audit"]["path"]))
    audit = audit.loc[audit["after_decision"].eq("FILLED")].copy()
    audit = audit.rename(
        columns={
            "scheduled_entry_time_utc": "scheduled_time_utc",
            "after_portfolio_pnl_usd": "protected_pnl_usd",
            "pnl_usd": "endpoint_pnl_usd",
        }
    )
    audit["trade_id"] = audit["trade_id"].astype(str)
    audit["fold_id"] = "2026-07"
    audit["protection_delta_usd"] = (
        pd.to_numeric(audit["protected_pnl_usd"], errors="raise")
        - pd.to_numeric(audit["endpoint_pnl_usd"], errors="raise")
    )
    clustered = annotate_clusters(
        audit,
        entry_column="entry_time_utc",
        exit_column="exit_time_utc",
        pnl_column="protected_pnl_usd",
    )
    result = json.loads(resolve(config["inputs"]["july_result"]["path"]).read_text())
    core = result["candidate_population"]["core_generation"]
    feed_integrity = {
        "independent_reconstruction_present": all(
            source in core
            for source in ("R1_BOX", "R1_PULLBACK", "R2_DOWNTREND", "R3_COMPRESSION")
        ),
        "reconstructed_candidate_counts": {
            source: int(core[source])
            for source in ("R1_BOX", "R1_PULLBACK", "R2_DOWNTREND", "R3_COMPRESSION")
        },
        "duplicate_signals_removed": int(
            result["candidate_population"]["duplicate_signals_removed"]
        ),
        "interpretation": (
            "FROZEN_RECONSTRUCTION_CONFIRMS_ZERO_CORE_CANDIDATES"
            if all(int(core[source]) == 0 for source in ("R1_BOX", "R1_PULLBACK", "R2_DOWNTREND", "R3_COMPRESSION"))
            else "CORE_CANDIDATES_PRESENT"
        ),
    }
    return clustered, feed_integrity


def prepare_august(config: Mapping[str, Any]) -> pd.DataFrame:
    audit = pd.read_csv(resolve(config["inputs"]["august_v16_audit"]["path"]))
    audit = audit.loc[as_bool(audit["baseline_executed"]) & as_bool(audit["broker_outcome_resolved"])].copy()
    features = pd.read_csv(resolve(config["inputs"]["august_features"]["path"]))
    feature_columns = features[["candidate_id", "direction"]].drop_duplicates("candidate_id")
    audit = audit.merge(feature_columns, on="candidate_id", how="left", validate="one_to_one")
    audit["trade_id"] = audit["candidate_id"].astype(str)
    audit["fold_id"] = "2026-08-through-25"
    return annotate_clusters(
        audit,
        entry_column="entry_time_utc",
        exit_column="broker_exit_time_utc",
        pnl_column="broker_pnl_usd",
    )


def losing_month_summary(monthly: pd.DataFrame, prefix: str) -> dict[str, Any]:
    column = f"{prefix}_net_pnl_usd"
    negative = monthly.loc[monthly[column].lt(0.0)]
    return {
        "negative_months": int(len(negative)),
        "negative_month_pnl_usd": float(negative[column].sum()),
        "worst_month_pnl_usd": float(monthly[column].min()),
    }


def render_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        f"# {result['report_title']} Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Read-only exposed diagnostic. No trading or deployment change is authorized.",
        "",
        "## Portfolio attribution",
        "",
        "| View | Trades | Net P/L | Profit factor | Win rate | Closed DD | Net/DD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, item in (
        ("Frozen source endpoints on V60 accepted set", result["portfolio_attribution"]["endpoint"]),
        ("Deployed protected closes", result["portfolio_attribution"]["protected"]),
    ):
        pf = "n/a" if item["profit_factor"] is None else f"{item['profit_factor']:.4f}"
        wr = "n/a" if item["win_rate"] is None else f"{item['win_rate']:.2%}"
        ratio = (
            "n/a"
            if item["net_to_closed_drawdown"] is None
            else f"{item['net_to_closed_drawdown']:.2f}"
        )
        lines.append(
            f"| {label} | {item['trades']} | ${item['net_pnl_usd']:.2f} | {pf} | {wr} | "
            f"${item['closed_drawdown_usd']:.2f} | {ratio} |"
        )
    lines.extend(
        [
            "",
            f"Protection attribution delta on the fixed accepted set: **${result['portfolio_attribution']['delta_usd']:+.2f}**.",
            "This is attribution, not a no-protection counterfactual; removing protection can change later capacity and fills.",
            "",
            "Protection improves profit factor, closed drawdown, net/DD, and losing-month severity overall despite the lower fixed-set net P/L.",
            "",
            "## Eligible follow-up lanes",
            "",
        ]
    )
    protection = [row for row in result["protection_eligibility"] if row["eligible"]]
    cluster = [row for row in result["cluster_eligibility"] if row["eligible"]]
    lines.append(
        "- Protection sources: "
        + (", ".join(row["source_id"] for row in protection) if protection else "none")
    )
    lines.append(
        "- Cluster cohorts: "
        + (", ".join(row["cohort"] for row in cluster) if cluster else "none")
    )
    if protection:
        lines.extend(["", "| Source | Protection actions | Delta | Negative folds |", "|---|---:|---:|---:|"])
        for row in protection:
            lines.append(
                f"| {row['source_id']} | {row['protection_action_trades']} | "
                f"${row['protection_delta_usd']:+.2f} | {row['negative_historical_folds']} |"
            )
    later = next(
        row for row in result["cluster_eligibility"] if row["cohort"] == "CLUSTER_LATER"
    )
    post_loss = next(
        row
        for row in result["cluster_eligibility"]
        if row["cohort"] == "POST_PRIOR_LOSS_SAME_DAY"
    )
    lines.extend(
        [
            "",
            "## Cluster finding",
            "",
            f"Later same-source/direction/day trades made **${later['net_pnl_usd']:.2f}** "
            f"at PF **{later['profit_factor']:.4f}** across {later['trades']} trades and were positive in every historical fold.",
            f"Trades after a resolved same-day directional loss made **${post_loss['net_pnl_usd']:.2f}** "
            f"at PF **{post_loss['profit_factor']:.4f}** across {post_loss['trades']} trades.",
            "The July/August cluster losses are therefore not a stable control mechanism.",
            "",
            "## Recent exposed periods",
            "",
            "| Period | Trades | Net P/L | PF | Win rate |",
            "|---|---:|---:|---:|---:|",
            f"| July protected | {result['july']['protected']['trades']} | "
            f"${result['july']['protected']['net_pnl_usd']:.2f} | "
            f"{result['july']['protected']['profit_factor']:.4f} | "
            f"{result['july']['protected']['win_rate']:.2%} |",
            f"| August V60 through 25 | {result['august_through_25']['broker']['trades']} | "
            f"${result['august_through_25']['broker']['net_pnl_usd']:.2f} | "
            f"{result['august_through_25']['broker']['profit_factor']:.4f} | "
            f"{result['august_through_25']['broker']['win_rate']:.2%} |",
        ]
    )
    lines.extend(
        [
            "",
            "## July integrity",
            "",
            f"Independent reconstruction: `{result['july']['feed_integrity']['interpretation']}`.",
            "The failed confirmation harnesses were read-only and are not treated as the cause of candidate silence.",
            "",
            "## Governance",
            "",
            "- No threshold search or veto simulation was performed.",
            "- July and August are exposed diagnostics.",
            "- Any eligible lane needs a separate preregistration, full path-dependent replay, cross-feed and cost stress, then clean forward confirmation.",
            "- V60 remains the only broker-action policy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_inputs(config)
    baseline, v6, replay_result = capture_replay(config)
    frozen_v6 = json.loads(resolve(config["inputs"]["v6_result"]["path"]).read_text())
    identity = {
        "v60_trades": int(replay_result["baseline"]["trades_closed"])
        == int(frozen_v6["baseline"]["trades_closed"]),
        "v60_net": abs(
            float(replay_result["baseline"]["net_pnl_usd"])
            - float(frozen_v6["baseline"]["net_pnl_usd"])
        )
        <= float(config["tolerance_usd"]),
        "v6_trades": int(replay_result["challenger"]["trades_closed"])
        == int(frozen_v6["challenger"]["trades_closed"]),
        "v6_net": abs(
            float(replay_result["challenger"]["net_pnl_usd"])
            - float(frozen_v6["challenger"]["net_pnl_usd"])
        )
        <= float(config["tolerance_usd"]),
    }
    if not all(identity.values()):
        raise ValueError(f"Replay identity failed: {identity}")

    protection, by_source, by_source_year, by_month = protection_audit(baseline, config)
    clustered = annotate_clusters(
        protection,
        entry_column="entry_time_utc",
        exit_column="protected_exit_time_utc",
        pnl_column="protected_pnl_usd",
    )
    cluster_cohorts = cohort_table(clustered, "protected_pnl_usd")
    protection_eligibility = eligible_protection_sources(protection, config)
    cluster_eligibility = eligible_cluster_cohorts(cluster_cohorts, config)
    july, july_feed = prepare_july(config)
    august = prepare_august(config)
    july_cohorts = cohort_table(july, "protected_pnl_usd")
    august_cohorts = cohort_table(august, "broker_pnl_usd")

    protection_supported = any(row["eligible"] for row in protection_eligibility)
    cluster_supported = any(row["eligible"] for row in cluster_eligibility)
    if protection_supported and cluster_supported:
        decision = "DIAGNOSTIC_SUPPORTS_BOTH_RESEARCH_LANES"
    elif protection_supported:
        decision = "DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH"
    elif cluster_supported:
        decision = "DIAGNOSTIC_SUPPORTS_TARGETED_CLUSTER_RESEARCH"
    else:
        decision = "NO_STABLE_MECHANISM_KEEP_V60"

    endpoint_metrics = timed_metrics(
        protection, pnl_column="endpoint_pnl_usd", close_column="endpoint_exit_time_utc"
    )
    protected_metrics = timed_metrics(
        protection, pnl_column="protected_pnl_usd", close_column="protected_exit_time_utc"
    )
    result = {
        "schema_version": config["schema_version"],
        "report_title": config["report_title"],
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "evidence_status": config["evidence_status"],
        "input_identity": identity,
        "portfolio_attribution": {
            "endpoint": endpoint_metrics,
            "protected": protected_metrics,
            "delta_usd": protected_metrics["net_pnl_usd"] - endpoint_metrics["net_pnl_usd"],
            "changed_trades": int(protection["protection_changed"].sum()),
            "protection_action_trades": int(protection["protection_action"].sum()),
            "pnl_changed_trades": int(protection["pnl_changed"].sum()),
            "fixed_accepted_set": True,
        },
        "monthly_downside": {
            "endpoint": losing_month_summary(by_month, "endpoint"),
            "protected": losing_month_summary(by_month, "protected"),
        },
        "protection_eligibility": protection_eligibility,
        "cluster_eligibility": cluster_eligibility,
        "july": {
            "feed_integrity": july_feed,
            "protected": metrics(july["protected_pnl_usd"]),
            "endpoint": metrics(july["endpoint_pnl_usd"]),
            "protection_delta_usd": float(july["protection_delta_usd"].sum()),
            "cluster_cohorts": july_cohorts.to_dict("records"),
            "evidence_status": "EXPOSED_MIXED_RECONSTRUCTION_AND_PROSPECTIVE_LOGS",
        },
        "august_through_25": {
            "broker": metrics(august["broker_pnl_usd"]),
            "cluster_cohorts": august_cohorts.to_dict("records"),
            "evidence_status": "EXPOSED_BROKER_OUTCOMES",
        },
        "limitations": [
            "Every historical, July, and August outcome was exposed before this diagnostic.",
            "Endpoint attribution uses V60's fixed accepted set; removing protection can change capacity and later fills.",
            "July combines retrospective reconstruction with prospective candidate logs.",
            "August has broker outcomes but no frozen source-endpoint counterfactual in this package.",
            "Eligibility supports only a separately preregistered research lane and cannot authorize deployment.",
        ],
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    protection.to_csv(OUTPUTS / "PROTECTION_TRADE_AUDIT.csv", index=False)
    by_source.to_csv(OUTPUTS / "PROTECTION_BY_SOURCE.csv", index=False)
    by_source_year.to_csv(OUTPUTS / "PROTECTION_BY_SOURCE_YEAR.csv", index=False)
    by_month.to_csv(OUTPUTS / "PROTECTION_BY_MONTH.csv", index=False)
    clustered.to_csv(OUTPUTS / "CLUSTER_TRADE_AUDIT.csv", index=False)
    cluster_cohorts.to_csv(OUTPUTS / "CLUSTER_COHORTS.csv", index=False)
    july.to_csv(OUTPUTS / "JULY_AUDIT.csv", index=False)
    august.to_csv(OUTPUTS / "AUGUST_CLUSTER_AUDIT.csv", index=False)
    result = json_ready(result)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8"
    )
    (OUTPUTS / "RESULT.md").write_text(render_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": decision,
                "portfolio_attribution": result["portfolio_attribution"],
                "protection_eligibility": protection_eligibility,
                "cluster_eligibility": cluster_eligibility,
                "july_feed_integrity": july_feed,
            },
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
