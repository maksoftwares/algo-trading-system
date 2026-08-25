from __future__ import annotations

import ast
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import heapq
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUTS = ROOT / "outputs"
sys.path.insert(0, str(ROOT))

from src.scenario import PROPOSAL_RULE, monthly_overlay_class, should_veto_monthly


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
        actual = sha256_file(resolve(str(item["path"])))
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_inputs(config)
    return config


def profit_factor(values: pd.Series | np.ndarray) -> float | None:
    pnl = np.asarray(values, dtype=float)
    gross_profit = float(pnl[pnl > 0.0].sum())
    gross_loss = -float(pnl[pnl < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0.0 else None


def closed_metrics(
    frame: pd.DataFrame,
    *,
    pnl_column: str = "pnl_usd",
    close_column: str = "exit_time_utc",
    id_column: str = "trade_id",
) -> dict[str, Any]:
    ordered = frame.sort_values([close_column, id_column], kind="stable")
    pnl = pd.to_numeric(ordered[pnl_column], errors="raise").astype(float)
    equity = np.r_[0.0, pnl.cumsum().to_numpy(dtype=float)]
    drawdown = np.maximum.accumulate(equity) - equity
    return {
        "trades": int(len(pnl)),
        "wins": int(pnl.gt(0.0).sum()),
        "losses": int(pnl.lt(0.0).sum()),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": profit_factor(pnl),
        "win_rate": float(pnl.gt(0.0).mean()) if len(pnl) else None,
        "closed_drawdown_usd": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def monthly_table(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    work = frame.copy()
    work["entry_time_utc"] = pd.to_datetime(
        work["entry_time_utc"], utc=True, format="mixed", errors="raise"
    )
    work["month"] = work["entry_time_utc"].dt.strftime("%Y-%m")
    rows: list[dict[str, Any]] = []
    for month, group in work.groupby("month", sort=True):
        metrics = closed_metrics(group)
        rows.append({"system": label, "month": month, **metrics})
    return pd.DataFrame(rows)


def monthly_summary(table: pd.DataFrame) -> dict[str, Any]:
    negative = table.loc[table["net_pnl_usd"].lt(0.0)]
    return {
        "months": int(len(table)),
        "positive_months": int(table["net_pnl_usd"].gt(0.0).sum()),
        "negative_months": int(len(negative)),
        "negative_month_pnl_usd": float(negative["net_pnl_usd"].sum()),
        "worst_month_pnl_usd": float(table["net_pnl_usd"].min()),
    }


def metric_floor_gates(
    observed: Mapping[str, Any], reference: Mapping[str, Any], prefix: str
) -> dict[str, bool]:
    tolerance = 1e-9
    current = observed["challenger"]
    prior = reference["challenger"]
    gates = {
        f"{prefix}_net_not_lower": current["net_pnl_usd"] + tolerance
        >= prior["net_pnl_usd"],
        f"{prefix}_profit_factor_not_lower": current["profit_factor"] + tolerance
        >= prior["profit_factor"],
        f"{prefix}_closed_drawdown_not_higher": current[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= prior["maximum_lifetime_closed_drawdown_usd"] + tolerance,
        f"{prefix}_equity_drawdown_not_higher": current[
            "maximum_lifetime_equity_drawdown_usd"
        ]
        <= prior["maximum_lifetime_equity_drawdown_usd"] + tolerance,
    }
    for window_id in ("3m", "6m", "12m"):
        current_window = observed["windows"][window_id]["challenger"]
        prior_window = reference["windows"][window_id]["challenger"]
        gates[f"{prefix}_{window_id}_net_not_lower"] = (
            current_window["net_pnl_usd"] + tolerance
            >= prior_window["net_pnl_usd"]
        )
        gates[f"{prefix}_{window_id}_profit_factor_not_lower"] = (
            current_window["profit_factor"] + tolerance
            >= prior_window["profit_factor"]
        )
    return {name: bool(value) for name, value in gates.items()}


def annual_floor_gates(
    observed: pd.DataFrame, reference_rows: list[Mapping[str, Any]], prefix: str
) -> dict[str, bool]:
    reference = {
        int(row["year"]): float(row["challenger_net_pnl_usd"])
        for row in reference_rows
    }
    actual = {
        int(row.year): float(row.challenger_net_pnl_usd)
        for row in observed.itertuples(index=False)
    }
    if set(actual) != set(reference):
        raise ValueError("Annual comparison years changed")
    return {
        f"{prefix}_{year}_pnl_not_lower": actual[year] + 1e-9 >= reference[year]
        for year in sorted(reference)
    }


def apply_overlay_sequence(
    frame: pd.DataFrame,
    policy: Mapping[str, Any],
    *,
    id_column: str,
    entry_column: str,
    exit_column: str,
    pnl_column: str,
    rank_column: str,
    base_veto_column: str,
    canonical_pnl_column: str | None = None,
) -> pd.DataFrame:
    work = frame.copy()
    work[entry_column] = pd.to_datetime(
        work[entry_column], utc=True, format="mixed", errors="raise"
    )
    work[exit_column] = pd.to_datetime(
        work[exit_column], utc=True, format="mixed", errors="raise"
    )
    work[pnl_column] = pd.to_numeric(work[pnl_column], errors="raise").astype(float)
    work[rank_column] = pd.to_numeric(work[rank_column], errors="coerce")
    work[base_veto_column] = work[base_veto_column].astype(bool)
    canonical = canonical_pnl_column or pnl_column
    work[canonical] = pd.to_numeric(work[canonical], errors="raise").astype(float)

    month_count: dict[str, int] = {}
    month_pnl: dict[str, float] = {}
    pending: list[tuple[int, int, str, float]] = []
    sequence = 0
    records: list[dict[str, Any]] = []
    for row in work.sort_values([entry_column, id_column], kind="stable").to_dict(
        "records"
    ):
        entry = pd.Timestamp(row[entry_column])
        while pending and pending[0][0] <= entry.value:
            _, _, month, pnl = heapq.heappop(pending)
            month_count[month] = month_count.get(month, 0) + 1
            month_pnl[month] = month_pnl.get(month, 0.0) + pnl
        month = entry.strftime("%Y-%m")
        before_count = month_count.get(month, 0)
        before_pnl = month_pnl.get(month, 0.0)
        rank = None if pd.isna(row[rank_column]) else float(row[rank_column])
        monthly_veto = False
        if not bool(row[base_veto_column]):
            monthly_veto = should_veto_monthly(
                closed_trades=before_count,
                closed_pnl_usd=before_pnl,
                causal_rank=rank,
                policy=policy,
            )
        retained = not bool(row[base_veto_column]) and not monthly_veto
        output = dict(row)
        output.update(
            {
                "prior_month_closed_trades": before_count,
                "prior_month_closed_pnl_usd": before_pnl,
                "monthly_quality_veto": monthly_veto,
                "v14_retained": retained,
            }
        )
        records.append(output)
        if retained:
            sequence += 1
            close = pd.Timestamp(row[exit_column])
            heapq.heappush(
                pending,
                (close.value, sequence, close.strftime("%Y-%m"), float(row[canonical])),
            )
    return pd.DataFrame(records)


def august_audit(
    v6_config: Mapping[str, Any],
    v6_result: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    broker = pd.read_csv(resolve(v6_config["inputs"]["exposed_broker_audit"]["path"]))
    broker = broker.loc[
        broker["entry_time_utc"].astype(str).str.startswith("2026-08-")
        & broker["baseline_executed"].astype(str).str.lower().eq("true")
        & broker["broker_outcome_resolved"].astype(str).str.lower().eq("true")
    ].copy()
    anti = pd.read_csv(resolve(v6_config["inputs"]["antichase_august_audit"]["path"]))
    anti_base = anti["would_veto"].astype(str).str.lower().eq("true")
    ret_4h = pd.to_numeric(anti["ret_4h"], errors="coerce")
    ret_24h = pd.to_numeric(anti["ret_24h"], errors="coerce")
    ratio = ret_4h / ret_24h.replace(0.0, np.nan)
    followthrough = ret_24h.gt(
        float(v6_config["anti_chase"]["minimum_ret_24h_exclusive"])
    ) & ratio.lt(
        float(v6_config["anti_chase"]["maximum_ret_4h_to_ret_24h_exclusive"])
    )
    anti_map = pd.DataFrame(
        {
            "candidate_id": anti["candidate_id"].astype(str),
            "v6_antichase_veto": anti_base & followthrough,
        }
    )
    if anti_map["candidate_id"].duplicated().any():
        raise ValueError("August anti-chase audit contains duplicate candidates")
    broker = broker.merge(anti_map, on="candidate_id", how="left", validate="one_to_one")
    broker["v6_antichase_veto"] = broker["v6_antichase_veto"].fillna(False)
    broker["v2_veto"] = broker["would_veto"].astype(str).str.lower().eq("true")
    broker["v6_veto"] = broker["v2_veto"] | broker["v6_antichase_veto"]
    broker["causal_rank_numeric"] = pd.to_numeric(broker["causal_rank"], errors="coerce")
    volumes = broker["broker_execution"].map(
        lambda value: float(ast.literal_eval(str(value))["volume_lots"])
    )
    broker["canonical_pnl_usd"] = pd.to_numeric(
        broker["broker_pnl_usd"], errors="raise"
    ) * (float(policy["canonical_lot_size"]) / volumes)
    audit = apply_overlay_sequence(
        broker,
        policy,
        id_column="candidate_id",
        entry_column="entry_time_utc",
        exit_column="broker_exit_time_utc",
        pnl_column="broker_pnl_usd",
        rank_column="causal_rank_numeric",
        base_veto_column="v6_veto",
        canonical_pnl_column="canonical_pnl_usd",
    )
    v60 = closed_metrics(
        audit,
        pnl_column="broker_pnl_usd",
        close_column="broker_exit_time_utc",
        id_column="candidate_id",
    )
    v6 = closed_metrics(
        audit.loc[~audit["v6_veto"]],
        pnl_column="broker_pnl_usd",
        close_column="broker_exit_time_utc",
        id_column="candidate_id",
    )
    v14 = closed_metrics(
        audit.loc[audit["v14_retained"]],
        pnl_column="broker_pnl_usd",
        close_column="broker_exit_time_utc",
        id_column="candidate_id",
    )
    frozen = v6_result["august_2026_through_25"]["challenger"]
    identity = {
        "trades": v6["trades"] == int(frozen["trades"]),
        "net": abs(v6["net_pnl_usd"] - float(frozen["net_pnl_usd"])) <= 1e-9,
    }
    gates = {
        "v6_identity": all(identity.values()),
        "positive_net": v14["net_pnl_usd"] > 0.0,
        "net_not_below_v6": v14["net_pnl_usd"] + 1e-9 >= v6["net_pnl_usd"],
        "profit_factor_not_below_v6": v14["profit_factor"] + 1e-9
        >= v6["profit_factor"],
        "closed_drawdown_not_above_v6": v14["closed_drawdown_usd"]
        <= v6["closed_drawdown_usd"] + 1e-9,
    }
    return {
        "v60": v60,
        "v6": v6,
        "v14": v14,
        "monthly_overlay_vetoes": int(audit["monthly_quality_veto"].sum()),
        "identity": identity,
        "gates": gates,
    }, audit


def crossfeed_audit(
    v6_config: Mapping[str, Any],
    v6_result: Mapping[str, Any],
    features: pd.DataFrame,
    policy: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    priced = pd.read_csv(resolve(v6_config["inputs"]["crossfeed_priced_runtime"]["path"]))
    priced = priced.loc[
        priced["dukascopy_covered"].astype(str).str.lower().eq("true")
    ].copy()
    veto_ids = {
        str(row["trade_id"])
        for row in v6_result["veto_audit"]
        if bool(row["baseline_runtime_executed"])
    }
    rank_map = {
        str(row.trade_id): float(row.rank)
        for row in features[["trade_id", "rank"]].itertuples(index=False)
        if pd.notna(row.rank)
    }
    priced["v6_veto"] = priced["trade_id"].astype(str).isin(veto_ids)
    priced["causal_rank"] = priced["trade_id"].astype(str).map(rank_map)
    audit = apply_overlay_sequence(
        priced,
        policy,
        id_column="trade_id",
        entry_column="runtime_entry_time_utc",
        exit_column="runtime_exit_time_utc",
        pnl_column="dukascopy_spread_only_pnl_usd",
        rank_column="causal_rank",
        base_veto_column="v6_veto",
    )
    v60 = closed_metrics(
        audit,
        pnl_column="dukascopy_spread_only_pnl_usd",
        close_column="runtime_exit_time_utc",
    )
    v6_frame = audit.loc[~audit["v6_veto"]]
    v14_frame = audit.loc[audit["v14_retained"]]
    v6 = closed_metrics(
        v6_frame,
        pnl_column="dukascopy_spread_only_pnl_usd",
        close_column="runtime_exit_time_utc",
    )
    v14 = closed_metrics(
        v14_frame,
        pnl_column="dukascopy_spread_only_pnl_usd",
        close_column="runtime_exit_time_utc",
    )
    frozen = v6_result["dukascopy_crossfeed"]["challenger"]
    identity = {
        "trades": v6["trades"] == int(frozen["trades"]),
        "net": abs(v6["net_pnl_usd"] - float(frozen["net_pnl_usd"])) <= 1e-9,
    }
    v6_year = (
        v6_frame.assign(
            year=pd.to_datetime(
                v6_frame["runtime_entry_time_utc"], utc=True, format="mixed"
            ).dt.year
        )
        .groupby("year")["dukascopy_spread_only_pnl_usd"]
        .sum()
    )
    v14_year = (
        v14_frame.assign(
            year=pd.to_datetime(
                v14_frame["runtime_entry_time_utc"], utc=True, format="mixed"
            ).dt.year
        )
        .groupby("year")["dukascopy_spread_only_pnl_usd"]
        .sum()
    )
    annual = [
        {
            "year": int(year),
            "v6_net_pnl_usd": float(v6_year.loc[year]),
            "v14_net_pnl_usd": float(v14_year.loc[year]),
            "delta_net_pnl_usd": float(v14_year.loc[year] - v6_year.loc[year]),
        }
        for year in sorted(set(v6_year.index) | set(v14_year.index))
    ]
    gates = {
        "v6_identity": all(identity.values()),
        "net_not_below_v6": v14["net_pnl_usd"] + 1e-9 >= v6["net_pnl_usd"],
        "profit_factor_not_below_v6": v14["profit_factor"] + 1e-9
        >= v6["profit_factor"],
        "closed_drawdown_not_above_v6": v14["closed_drawdown_usd"]
        <= v6["closed_drawdown_usd"] + 1e-9,
        "every_year_not_below_v6": all(row["delta_net_pnl_usd"] >= -1e-9 for row in annual),
    }
    return {
        "evidence_status": "INDEPENDENT_PRICE_PATH_POST_SELECTED_TIMING",
        "v60": v60,
        "v6": v6,
        "v14": v14,
        "monthly_overlay_vetoes": int(audit["monthly_quality_veto"].sum()),
        "annual": annual,
        "identity": identity,
        "gates": gates,
    }, audit


def stress_gates(
    observed: Mapping[str, Any], reference: Mapping[str, Any], annual: pd.DataFrame
) -> dict[str, bool]:
    current = observed["challenger"]
    tolerance = 1e-9
    gates = {
        "net_not_below_v6": current["net_pnl_usd"] + tolerance
        >= float(reference["challenger_net_pnl_usd"]),
        "profit_factor_not_below_v6": current["profit_factor"] + tolerance
        >= float(reference["challenger_profit_factor"]),
        "closed_drawdown_not_above_v6": current[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= float(reference["challenger_closed_drawdown_usd"]) + tolerance,
        "equity_drawdown_not_above_v6": current[
            "maximum_lifetime_equity_drawdown_usd"
        ]
        <= float(reference["challenger_equity_drawdown_usd"]) + tolerance,
    }
    reference_years = {
        int(row["year"]): float(row["challenger_net_pnl_usd"])
        for row in reference["annual"]
    }
    actual_years = {
        int(row.year): float(row.challenger_net_pnl_usd)
        for row in annual.itertuples(index=False)
    }
    gates["every_year_not_below_v6"] = set(reference_years) == set(actual_years) and all(
        actual_years[year] + tolerance >= reference_years[year]
        for year in reference_years
    )
    return {name: bool(value) for name, value in gates.items()}


def render_markdown(result: Mapping[str, Any]) -> str:
    v60 = result["historical"]["baseline"]
    v14 = result["historical"]["challenger"]
    v6 = result["frozen_v6"]["challenger"]
    monthly = result["monthly"]
    lines = [
        f"# {result['report_title']} Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Research only. No deployment or broker action is authorized.",
        "",
        "| Metric | V60 | V6 | V14 |",
        "|---|---:|---:|---:|",
        f"| Trades | {v60['trades_closed']} | {v6['trades_closed']} | {v14['trades_closed']} |",
        f"| Net P/L | ${v60['net_pnl_usd']:.2f} | ${v6['net_pnl_usd']:.2f} | ${v14['net_pnl_usd']:.2f} |",
        f"| Profit factor | {v60['profit_factor']:.4f} | {v6['profit_factor']:.4f} | {v14['profit_factor']:.4f} |",
        f"| Closed drawdown | ${v60['maximum_lifetime_closed_drawdown_usd']:.2f} | ${v6['maximum_lifetime_closed_drawdown_usd']:.2f} | ${v14['maximum_lifetime_closed_drawdown_usd']:.2f} |",
        f"| Equity drawdown | ${v60['maximum_lifetime_equity_drawdown_usd']:.2f} | ${v6['maximum_lifetime_equity_drawdown_usd']:.2f} | ${v14['maximum_lifetime_equity_drawdown_usd']:.2f} |",
        f"| Losing months | {monthly['v60']['negative_months']} | {result['frozen_v6_monthly_reference']['negative_months']} | {monthly['v14']['negative_months']} |",
        f"| Losing-month P/L | ${monthly['v60']['negative_month_pnl_usd']:.2f} | ${result['frozen_v6_monthly_reference']['negative_month_pnl_usd']:.2f} | ${monthly['v14']['negative_month_pnl_usd']:.2f} |",
        f"| Worst month | ${monthly['v60']['worst_month_pnl_usd']:.2f} | ${result['frozen_v6_monthly_reference']['worst_month_pnl_usd']:.2f} | ${monthly['v14']['worst_month_pnl_usd']:.2f} |",
        "",
        f"Monthly-quality vetoes: `{result['monthly_overlay_vetoes']}`.",
        "",
        "## Gates",
        "",
    ]
    for name, value in result["gates"].items():
        lines.append(f"- `{name}`: {'PASS' if value else 'FAIL'}")
    lines.extend(["", "Clean forward evidence remains mandatory.", ""])
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    report_title = str(
        config.get("report_title", "V60 Monthly Quality Risk Overlay V14")
    )
    v6_config = json.loads(resolve(config["inputs"]["v6_config"]["path"]).read_text())
    validate_inputs(v6_config)
    v6_result = json.loads(resolve(config["inputs"]["v6_result"]["path"]).read_text())
    v6_scenario = load_module(
        "v14_v6_scenario", resolve(config["inputs"]["v6_scenario"]["path"])
    )
    evaluator = load_module(
        "v14_shared_evaluator", resolve(v6_config["inputs"]["shared_evaluator"]["path"])
    )
    features = pd.read_parquet(resolve(v6_config["inputs"]["causal_feature_ledger"]["path"]))
    if features["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger contains duplicate trade IDs")
    feature_map = {str(row["trade_id"]): row for row in features.to_dict("records")}
    policy = config["monthly_quality_policy"]

    def factory(replay):
        base_type = v6_scenario.combined_challenger_class(
            replay,
            evaluator,
            feature_map,
            v6_config["anti_chase"],
        )
        return monthly_overlay_class(replay, base_type, policy)

    evaluator.challenger_class = factory
    captured: list[pd.DataFrame] = []
    original_closed_trade_frame = evaluator.closed_trade_frame

    def capture(scenario, candidates):
        frame = original_closed_trade_frame(scenario, candidates)
        captured.append(frame.copy())
        return frame

    evaluator.closed_trade_frame = capture
    base = json.loads(
        resolve(v6_config["inputs"]["base_challenger_config"]["path"]).read_text()
    )
    with tempfile.TemporaryDirectory(prefix="v60-monthly-overlay-v14-") as temporary:
        replay_config = deepcopy(base)
        for name, value in v6_config.get("v2_policy_overrides", {}).items():
            replay_config["policy"][name] = value
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = report_title
        replay_config["gates"]["minimum_trade_retention_fraction"] = float(
            config["acceptance"]["minimum_trade_retention_fraction"]
        )
        replay_config["gates"]["minimum_frequency_retention_fraction"] = float(
            config["acceptance"]["minimum_frequency_retention_fraction"]
        )
        replay_config["gates"]["minimum_veto_cohort_rows"] = int(
            v6_config["acceptance"]["minimum_executed_vetoes"]
        )
        replay_path = Path(temporary) / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)
        baseline_frame, v14_frame = captured[-2:]
        cost_stress: dict[str, Any] = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            stressed, stressed_annual, _ = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(cost)
            )
            reference = v6_result["cost_stress"][str(cost)]
            gates = stress_gates(stressed, reference, stressed_annual)
            cost_stress[str(cost)] = {
                "additional_cost_usd_per_trade": float(cost),
                "challenger": stressed["challenger"],
                "annual": stressed_annual.to_dict("records"),
                "gates": gates,
                "all_gates_pass": bool(all(gates.values())),
            }
    evaluator.closed_trade_frame = original_closed_trade_frame

    v60_monthly = monthly_table(baseline_frame, "V60")
    v14_monthly = monthly_table(v14_frame, "V14")
    monthly = pd.concat([v60_monthly, v14_monthly], ignore_index=True)
    v60_monthly_summary = monthly_summary(v60_monthly)
    v14_monthly_summary = monthly_summary(v14_monthly)
    frozen_monthly = config["frozen_v6_monthly_reference"]

    gates = {
        **{name: bool(value) for name, value in historical["gates"].items()},
        **metric_floor_gates(historical, v6_result, "v6_floor"),
        **annual_floor_gates(annual, v6_result["annual"], "v6_annual_floor"),
        "negative_month_count_not_above_v6": v14_monthly_summary["negative_months"]
        <= int(frozen_monthly["negative_months"]),
        "negative_month_pnl_better_than_v6": v14_monthly_summary[
            "negative_month_pnl_usd"
        ]
        > float(frozen_monthly["negative_month_pnl_usd"]),
        "worst_month_not_below_v6": v14_monthly_summary["worst_month_pnl_usd"]
        + 1e-9
        >= float(frozen_monthly["worst_month_pnl_usd"]),
    }
    monthly_overlay_vetoes = int(
        vetoes.get("proposal_rule", pd.Series(dtype=str)).astype(str).eq(PROPOSAL_RULE).sum()
    )
    gates["monthly_overlay_vetoes_present"] = monthly_overlay_vetoes >= int(
        config["acceptance"]["minimum_monthly_overlay_vetoes"]
    )
    gates["no_open_positions"] = int(historical["challenger"]["open_positions_at_end"]) == 0
    gates["no_flat_deadlock"] = not bool(historical["challenger"]["flat_suspended_deadlock"])
    gates["no_floating_deadlock"] = not bool(
        historical["challenger"]["floating_peak_deadlock"]
    )

    august, august_rows = august_audit(v6_config, v6_result, policy)
    crossfeed, crossfeed_rows = crossfeed_audit(v6_config, v6_result, features, policy)
    gates["august_all_gates"] = bool(all(august["gates"].values()))
    gates["crossfeed_all_gates"] = bool(all(crossfeed["gates"].values()))
    gates["all_cost_stress_gates"] = bool(
        all(item["all_gates_pass"] for item in cost_stress.values())
    )

    passed = bool(all(gates.values()))
    result = {
        "schema_version": config["schema_version"],
        "report_title": report_title,
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "RESEARCH_CHALLENGER_PASSES_FORWARD_CONFIRMATION_REQUIRED"
            if passed
            else "REJECT_KEEP_DEPLOYED_V60"
        ),
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "evidence_status": config["evidence_status"],
        "policy": policy,
        "historical": historical,
        "frozen_v6": {
            "challenger": v6_result["challenger"],
            "windows": v6_result["windows"],
            "annual": v6_result["annual"],
        },
        "delta_vs_v6": {
            "net_pnl_usd": historical["challenger"]["net_pnl_usd"]
            - v6_result["challenger"]["net_pnl_usd"],
            "profit_factor": historical["challenger"]["profit_factor"]
            - v6_result["challenger"]["profit_factor"],
            "closed_drawdown_usd": historical["challenger"][
                "maximum_lifetime_closed_drawdown_usd"
            ]
            - v6_result["challenger"]["maximum_lifetime_closed_drawdown_usd"],
            "equity_drawdown_usd": historical["challenger"][
                "maximum_lifetime_equity_drawdown_usd"
            ]
            - v6_result["challenger"]["maximum_lifetime_equity_drawdown_usd"],
            "trades": historical["challenger"]["trades_closed"]
            - v6_result["challenger"]["trades_closed"],
        },
        "annual": annual.to_dict("records"),
        "monthly": {"v60": v60_monthly_summary, "v14": v14_monthly_summary},
        "frozen_v6_monthly_reference": frozen_monthly,
        "monthly_overlay_vetoes": monthly_overlay_vetoes,
        "cost_stress": cost_stress,
        "august_2026_through_25": august,
        "dukascopy_crossfeed": crossfeed,
        "gates": gates,
        "limitations": [
            "All historical and August outcomes were exposed before evaluation.",
            "The fixed rule was nominated after a bounded endpoint screen.",
            "Calendar-month boundaries are operational conventions, not market regimes.",
            "Clean prospective evidence is mandatory before deployment.",
        ],
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUTPUTS / "RESULT.md").write_text(render_markdown(result), encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False)
    monthly.to_csv(OUTPUTS / "MONTHLY.csv", index=False)
    vetoes.to_csv(OUTPUTS / "VETO_AUDIT.csv", index=False)
    august_rows.to_csv(OUTPUTS / "AUGUST_2026_AUDIT.csv", index=False)
    crossfeed_rows.to_csv(OUTPUTS / "CROSSFEED_AUDIT.csv", index=False)
    print(json.dumps({
        "decision": result["decision"],
        "delta_vs_v6": result["delta_vs_v6"],
        "monthly": result["monthly"],
        "monthly_overlay_vetoes": monthly_overlay_vetoes,
        "failed_gates": [name for name, value in gates.items() if not value],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
