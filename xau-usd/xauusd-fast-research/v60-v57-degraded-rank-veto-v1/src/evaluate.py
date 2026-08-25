from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "challenger.json"
OUTPUTS = ROOT / "outputs"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(relative: str) -> Path:
    path = Path(relative)
    return path if path.is_absolute() else REPO_ROOT / path


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    for name, item in config["inputs"].items():
        path = resolve(str(item["path"]))
        actual = sha256_file(path)
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed for {name}: {actual}")
    return config


def profit_factor(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    gross_profit = float(array[array > 0.0].sum())
    gross_loss = -float(array[array < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0.0 else float("inf")


def apply_additional_cost(
    candidates: Sequence[Any], additional_cost_usd_per_trade: float
) -> list[Any]:
    additional_cost = float(additional_cost_usd_per_trade)
    if not np.isfinite(additional_cost) or additional_cost < 0.0:
        raise ValueError("Additional per-trade cost must be finite and nonnegative")
    if additional_cost == 0.0:
        return list(candidates)
    return [
        replace(
            candidate,
            pnl_usd=float(candidate.pnl_usd) - additional_cost,
            open_cost_usd=float(candidate.open_cost_usd) + additional_cost,
        )
        for candidate in candidates
    ]


def policy_targets_source(source_id: str, policy: Mapping[str, Any]) -> bool:
    target = str(policy["source_id"])
    return target == "*" or source_id == target


def should_veto(
    *,
    source_id: str,
    rank: float | None,
    prior_outcomes: Sequence[float],
    policy: Mapping[str, Any],
    consecutive_losses: int = 0,
    virtual_profit_factor: float | None = None,
    prior_source_closed_count: int | None = None,
) -> tuple[bool, float | None]:
    if not policy_targets_source(source_id, policy):
        return False, None
    if "minimum_prior_source_closed_trades" in policy:
        minimum_source_history = int(policy["minimum_prior_source_closed_trades"])
        available_source_history = (
            len(prior_outcomes)
            if prior_source_closed_count is None
            else int(prior_source_closed_count)
        )
        if available_source_history < minimum_source_history:
            return False, None
    condition = str(policy.get("state_condition", "ROLLING_PROFIT_FACTOR"))
    if condition == "CONSECUTIVE_LOSSES":
        if rank is None or not np.isfinite(rank):
            return False, None
        return (
            consecutive_losses >= int(policy["minimum_consecutive_losses"])
            and rank < float(policy["maximum_causal_rank_exclusive"]),
            None,
        )
    if condition == "VIRTUAL_ROLLING_PROFIT_FACTOR":
        if rank is None or not np.isfinite(rank):
            return False, virtual_profit_factor
        if virtual_profit_factor is None or not np.isfinite(virtual_profit_factor):
            return False, virtual_profit_factor
        return (
            virtual_profit_factor
            < float(policy["maximum_prior_profit_factor_exclusive"])
            and rank < float(policy["maximum_causal_rank_exclusive"]),
            virtual_profit_factor,
        )
    if condition != "ROLLING_PROFIT_FACTOR":
        raise ValueError(f"Unsupported state condition: {condition}")
    lookback = int(policy["lookback_closed_trades"])
    if len(prior_outcomes) < lookback:
        return False, None
    if rank is None or not np.isfinite(rank):
        return False, profit_factor(prior_outcomes[-lookback:])
    recent_pf = profit_factor(prior_outcomes[-lookback:])
    veto = (
        recent_pf < float(policy["maximum_prior_profit_factor_exclusive"])
        and rank < float(policy["maximum_causal_rank_exclusive"])
    )
    return veto, recent_pf


def load_rank_map(path: Path) -> dict[str, float]:
    frame = pd.read_parquet(path, columns=["trade_id", "rank"])
    if frame["trade_id"].duplicated().any():
        raise ValueError("Causal rank ledger contains duplicate trade IDs")
    return {
        str(row.trade_id): float(row.rank)
        for row in frame.itertuples(index=False)
        if pd.notna(row.rank)
    }


def causal_virtual_profit_factors(
    candidates: Sequence[Any], source_id: str, lookback: int
) -> dict[str, float | None]:
    source = [
        candidate
        for candidate in candidates
        if source_id == "*" or candidate.source_id == source_id
    ]
    exits = sorted(source, key=lambda item: (item.exit_ms, item.trade_id))
    entries = sorted(source, key=lambda item: (item.entry_ms, item.trade_id))
    outcomes: dict[str, list[float]] = defaultdict(list)
    exit_index = 0
    result: dict[str, float | None] = {}
    for candidate in entries:
        while (
            exit_index < len(exits)
            and exits[exit_index].exit_ms <= candidate.entry_ms
        ):
            closed = exits[exit_index]
            outcomes[closed.source_id].append(float(closed.pnl_usd))
            exit_index += 1
        source_outcomes = outcomes[candidate.source_id]
        result[candidate.trade_id] = (
            profit_factor(source_outcomes[-lookback:])
            if len(source_outcomes) >= lookback
            else None
        )
    return result


def challenger_class(replay: ModuleType) -> type:
    class DegradedRankScenario(replay.Scenario):
        def __init__(self, *args: Any, rank_map: Mapping[str, float], policy: Mapping[str, Any], **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.rank_map = rank_map
            self.veto_policy = policy
            self.source_closed: dict[str, deque[float]] = defaultdict(
                lambda: deque(maxlen=int(policy["lookback_closed_trades"]))
            )
            self.source_consecutive_losses: dict[str, int] = defaultdict(int)
            self.source_closed_count: dict[str, int] = defaultdict(int)
            self.virtual_profit_factors = causal_virtual_profit_factors(
                self.candidates,
                str(policy["source_id"]),
                int(policy["lookback_closed_trades"]),
            )
            self.veto_audit: list[dict[str, Any]] = []

        def _close(
            self,
            trade_id: str,
            now_ms: int,
            pnl: float,
            reason: str,
            *,
            counted_by_v60: bool,
        ) -> None:
            source_id = self.positions[trade_id].candidate.source_id
            super()._close(
                trade_id,
                now_ms,
                pnl,
                reason,
                counted_by_v60=counted_by_v60,
            )
            if policy_targets_source(source_id, self.veto_policy):
                self.source_closed[source_id].append(float(pnl))
                self.source_closed_count[source_id] += 1
                self.source_consecutive_losses[source_id] = (
                    self.source_consecutive_losses[source_id] + 1
                    if pnl < 0.0
                    else 0
                )

        def _entry_reason(self, candidate: Any, *args: Any, **kwargs: Any) -> str | None:
            reason = super()._entry_reason(candidate, *args, **kwargs)
            if reason is not None:
                return reason
            rank = self.rank_map.get(candidate.trade_id)
            veto, recent_pf = should_veto(
                source_id=candidate.source_id,
                rank=rank,
                prior_outcomes=list(self.source_closed[candidate.source_id]),
                policy=self.veto_policy,
                consecutive_losses=self.source_consecutive_losses[candidate.source_id],
                prior_source_closed_count=self.source_closed_count[candidate.source_id],
                virtual_profit_factor=self.virtual_profit_factors.get(
                    candidate.trade_id
                ),
            )
            if not veto:
                return None
            self.veto_audit.append(
                {
                    "trade_id": candidate.trade_id,
                    "entry_time_utc": replay.utc_text(candidate.entry_ms),
                    "source_id": candidate.source_id,
                    "causal_rank": rank,
                    "prior_20_profit_factor": recent_pf,
                    "prior_virtual_profit_factor": self.virtual_profit_factors.get(
                        candidate.trade_id
                    ),
                    "prior_consecutive_losses": self.source_consecutive_losses[
                        candidate.source_id
                    ],
                    "candidate_endpoint_pnl_usd": candidate.pnl_usd,
                }
            )
            return "V57_DEGRADED_BOTTOM_DECILE_VETO"

    return DegradedRankScenario


def closed_trade_frame(
    scenario: Any, candidates: Sequence[Any]
) -> pd.DataFrame:
    candidate_map = {candidate.trade_id: candidate for candidate in candidates}
    rows: list[dict[str, Any]] = []
    for row in scenario.event_rows:
        if row["event"] != "POSITION_CLOSED":
            continue
        candidate = candidate_map[str(row["trade_id"])]
        rows.append(
            {
                "trade_id": candidate.trade_id,
                "source_id": candidate.source_id,
                "entry_time_utc": replay_time(candidate.entry_ms),
                "exit_time_utc": str(row["timestamp_utc"]),
                "pnl_usd": float(row["pnl_usd"]),
            }
        )
    return pd.DataFrame(rows)


def replay_time(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).isoformat().replace(
        "+00:00", "Z"
    )


def window_metrics(frame: pd.DataFrame, start: pd.Timestamp) -> dict[str, Any]:
    entry_times = pd.to_datetime(
        frame["entry_time_utc"], utc=True, format="mixed"
    )
    selected = frame[entry_times >= start]
    values = selected["pnl_usd"].to_numpy(dtype=float)
    return {
        "trades": int(len(selected)),
        "net_pnl_usd": float(values.sum()),
        "profit_factor": profit_factor(values),
        "win_rate": float((values > 0.0).mean()) if len(values) else 0.0,
    }


def attach_baseline_runtime_pnl(
    veto_rows: Sequence[Mapping[str, Any]], baseline_trades: pd.DataFrame
) -> list[dict[str, Any]]:
    if baseline_trades["trade_id"].duplicated().any():
        raise ValueError("Baseline runtime trade IDs are not unique")
    runtime_pnl = baseline_trades.set_index("trade_id")["pnl_usd"].to_dict()
    attached: list[dict[str, Any]] = []
    for source in veto_rows:
        row = dict(source)
        trade_id = str(row["trade_id"])
        row["baseline_runtime_executed"] = trade_id in runtime_pnl
        row["baseline_runtime_pnl_usd"] = (
            float(runtime_pnl[trade_id]) if trade_id in runtime_pnl else None
        )
        attached.append(row)
    return attached


def run(
    config_path: Path = CONFIG_PATH,
    *,
    additional_cost_usd_per_trade: float = 0.0,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    config = load_config(config_path)
    replay = load_module(
        "v60_v57_challenger_replay",
        resolve(config["inputs"]["replay_source"]["path"]),
    )
    contract_path = resolve(config["inputs"]["replay_contract"]["path"])
    contract = replay.load_json(contract_path)
    deployed_path = resolve(config["inputs"]["deployed_config"]["path"])
    if resolve(contract["inputs"]["demo_config"]).resolve() != deployed_path.resolve():
        raise ValueError("Replay contract does not reference the deployed config")
    deployed = replay.load_json(deployed_path)
    deployed = replay.apply_portfolio_protection(contract, deployed)
    deployed = replay.apply_runtime_risk_mode(
        deployed,
        bool(
            contract["evaluation"].get(
                "required_equity_fraction_limits_enabled", False
            )
        ),
    )
    candidates, population = replay.load_candidates(contract, deployed)
    candidates = apply_additional_cost(candidates, additional_cost_usd_per_trade)
    cache_meta = replay.prepare_quote_cache(
        contract, candidates, population, force=False
    )
    quotes = replay.load_quote_cache(cache_meta)
    spec = next(
        item
        for item in replay.scenario_specs(contract)
        if item.scenario_id == "deployed__full_runtime"
    )

    baseline_scenario = replay.Scenario(spec, deployed, contract, candidates)
    baseline = baseline_scenario.simulate(quotes)

    rank_map = load_rank_map(
        resolve(config["inputs"]["causal_rank_ledger"]["path"])
    )
    scenario_type = challenger_class(replay)
    challenger_scenario = scenario_type(
        spec,
        deployed,
        contract,
        candidates,
        rank_map=rank_map,
        policy=config["policy"],
    )
    challenger = challenger_scenario.simulate(quotes)

    baseline_trades = closed_trade_frame(baseline_scenario, candidates)
    challenger_trades = closed_trade_frame(challenger_scenario, candidates)
    baseline_trades["entry_year"] = pd.to_datetime(
        baseline_trades["entry_time_utc"], utc=True, format="mixed"
    ).dt.year
    challenger_trades["entry_year"] = pd.to_datetime(
        challenger_trades["entry_time_utc"], utc=True, format="mixed"
    ).dt.year
    veto_audit = attach_baseline_runtime_pnl(
        challenger_scenario.veto_audit, baseline_trades
    )
    years = sorted(
        set(baseline_trades["entry_year"]) | set(challenger_trades["entry_year"])
    )
    annual_rows = []
    for year in years:
        base = baseline_trades.loc[
            baseline_trades["entry_year"] == year, "pnl_usd"
        ]
        changed = challenger_trades.loc[
            challenger_trades["entry_year"] == year, "pnl_usd"
        ]
        annual_rows.append(
            {
                "year": int(year),
                "baseline_trades": int(len(base)),
                "challenger_trades": int(len(changed)),
                "baseline_net_pnl_usd": float(base.sum()),
                "challenger_net_pnl_usd": float(changed.sum()),
                "delta_pnl_usd": float(changed.sum() - base.sum()),
            }
        )
    annual = pd.DataFrame(annual_rows)

    end = pd.Timestamp(contract["evaluation"]["entry_end_exclusive_utc"])
    windows: dict[str, Any] = {}
    for months in (3, 6, 12):
        start = end - pd.DateOffset(months=months)
        windows[f"{months}m"] = {
            "start_utc": start.isoformat(),
            "baseline": window_metrics(baseline_trades, start),
            "challenger": window_metrics(challenger_trades, start),
        }

    identity = config["benchmark_identity"]
    gates_config = config["gates"]
    metric_tolerance = float(gates_config["metric_tolerance_usd"])
    veto_runtime_values = np.asarray(
        [
            row["baseline_runtime_pnl_usd"]
            for row in veto_audit
            if row["baseline_runtime_executed"]
        ],
        dtype=float,
    )
    veto_endpoint_values = np.asarray(
        [row["candidate_endpoint_pnl_usd"] for row in veto_audit],
        dtype=float,
    )
    gates = {
        "baseline_trade_identity": baseline["trades_closed"]
        == int(identity["trades_closed"]),
        "baseline_net_identity": abs(
            baseline["net_pnl_usd"] - float(identity["net_pnl_usd"])
        )
        <= float(identity["net_tolerance_usd"]),
        "net_not_below_baseline": challenger["net_pnl_usd"]
        >= baseline["net_pnl_usd"],
        "profit_factor_not_below_baseline": challenger["profit_factor"]
        >= baseline["profit_factor"],
        "closed_drawdown_not_above_baseline": challenger[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= baseline["maximum_lifetime_closed_drawdown_usd"] + metric_tolerance,
        "equity_drawdown_not_above_baseline": challenger[
            "maximum_lifetime_equity_drawdown_usd"
        ]
        <= baseline["maximum_lifetime_equity_drawdown_usd"] + metric_tolerance,
        "trade_retention": challenger["trades_closed"]
        >= baseline["trades_closed"]
        * float(gates_config["minimum_trade_retention_fraction"]),
        "frequency_retention": challenger["trades_per_weekday"]
        >= baseline["trades_per_weekday"]
        * float(gates_config["minimum_frequency_retention_fraction"]),
        "no_negative_calendar_year_delta": bool(annual["delta_pnl_usd"].ge(0).all()),
        "recent_windows_not_worse": all(
            item["challenger"]["net_pnl_usd"]
            >= item["baseline"]["net_pnl_usd"]
            for item in windows.values()
        ),
        "veto_cohort_large_enough": len(veto_runtime_values)
        >= int(gates_config["minimum_veto_cohort_rows"]),
        "veto_cohort_profit_factor_below_one": len(veto_runtime_values) > 0
        and profit_factor(veto_runtime_values) < 1.0,
    }
    passed = bool(all(gates.values()))
    result = {
        "schema_version": config["schema_version"] + "_result",
        "report_title": config.get("report_title", "V60 V57 Challenger Result"),
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED"
            if passed
            else "KEEP_DEPLOYED_V60"
        ),
        "deployment_authorized": False,
        "evidence_boundary": "RETROSPECTIVE_EXPOSED_OUTCOMES",
        "additional_cost_usd_per_trade": float(additional_cost_usd_per_trade),
        "input_sha256": {
            name: str(item["sha256"]) for name, item in config["inputs"].items()
        },
        "population_audit": population,
        "quote_cache_audit": cache_meta,
        "rank_coverage": {
            "candidate_rows": len(candidates),
            "ranked_candidate_rows": sum(
                candidate.trade_id in rank_map for candidate in candidates
            ),
            "targeted_candidate_rows": sum(
                policy_targets_source(candidate.source_id, config["policy"])
                for candidate in candidates
            ),
            "ranked_targeted_candidate_rows": sum(
                policy_targets_source(candidate.source_id, config["policy"])
                and candidate.trade_id in rank_map
                for candidate in candidates
            ),
        },
        "policy": config["policy"],
        "baseline": baseline,
        "challenger": challenger,
        "delta": {
            "trades": challenger["trades_closed"] - baseline["trades_closed"],
            "net_pnl_usd": challenger["net_pnl_usd"] - baseline["net_pnl_usd"],
            "profit_factor": challenger["profit_factor"] - baseline["profit_factor"],
            "win_rate_percentage_points": 100.0
            * (challenger["win_rate"] - baseline["win_rate"]),
            "closed_drawdown_usd": challenger[
                "maximum_lifetime_closed_drawdown_usd"
            ]
            - baseline["maximum_lifetime_closed_drawdown_usd"],
            "equity_drawdown_usd": challenger[
                "maximum_lifetime_equity_drawdown_usd"
            ]
            - baseline["maximum_lifetime_equity_drawdown_usd"],
        },
        "windows": windows,
        "annual": annual.to_dict(orient="records"),
        "veto_audit": veto_audit,
        "baseline_executed_veto_count": len(veto_runtime_values),
        "veto_baseline_runtime_profit_factor": profit_factor(veto_runtime_values)
        if len(veto_runtime_values)
        else None,
        "veto_endpoint_profit_factor": profit_factor(veto_endpoint_values)
        if len(veto_endpoint_values)
        else None,
        "gates": gates,
        "limitations": [
            "All historical and recent demo outcomes were exposed before nomination.",
            "The historical causal replay cannot authorize demo deployment.",
            "The causal rank ledger has no rank for some candidates; those trades retain baseline behavior.",
            "Capital.com broker-specific future fills and slippage remain unknown.",
        ],
    }
    veto_frame = pd.DataFrame(veto_audit)
    return result, annual, veto_frame


def write_outputs(
    result: Mapping[str, Any],
    annual: pd.DataFrame,
    vetoes: pd.DataFrame,
    output_directory: Path = OUTPUTS,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    annual.to_csv(output_directory / "ANNUAL_COMPARISON.csv", index=False)
    vetoes.to_csv(output_directory / "VETO_AUDIT.csv", index=False)
    base = result["baseline"]
    challenger = result["challenger"]
    delta = result["delta"]
    lines = [
        f"# {result.get('report_title', 'V60 V57 Challenger Result')}",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Retrospective research only. No demo or live deployment is authorized.",
        "",
        "| Metric | Deployed V60 | Challenger | Change |",
        "|---|---:|---:|---:|",
        f"| Trades | {base['trades_closed']} | {challenger['trades_closed']} | {delta['trades']:+d} |",
        f"| Net P/L | ${base['net_pnl_usd']:.2f} | ${challenger['net_pnl_usd']:.2f} | ${delta['net_pnl_usd']:+.2f} |",
        f"| Profit factor | {base['profit_factor']:.4f} | {challenger['profit_factor']:.4f} | {delta['profit_factor']:+.4f} |",
        f"| Win rate | {100*base['win_rate']:.2f}% | {100*challenger['win_rate']:.2f}% | {delta['win_rate_percentage_points']:+.2f} pp |",
        f"| Closed drawdown | ${base['maximum_lifetime_closed_drawdown_usd']:.2f} | ${challenger['maximum_lifetime_closed_drawdown_usd']:.2f} | ${delta['closed_drawdown_usd']:+.2f} |",
        f"| Equity drawdown | ${base['maximum_lifetime_equity_drawdown_usd']:.2f} | ${challenger['maximum_lifetime_equity_drawdown_usd']:.2f} | ${delta['equity_drawdown_usd']:+.2f} |",
        f"| Trades/weekday | {base['trades_per_weekday']:.3f} | {challenger['trades_per_weekday']:.3f} | {challenger['trades_per_weekday']-base['trades_per_weekday']:+.3f} |",
        "",
        f"Veto decisions: `{len(result['veto_audit'])}`; "
        f"baseline-executed cohort: `{result['baseline_executed_veto_count']}`. "
        f"Baseline runtime PF: `{result['veto_baseline_runtime_profit_factor']}`. "
        f"Candidate endpoint PF: `{result['veto_endpoint_profit_factor']}`.",
        "",
        "## Gates",
        "",
    ]
    lines.extend(
        f"- `{name}`: {'PASS' if passed else 'FAIL'}"
        for name, passed in result["gates"].items()
    )
    (output_directory / "RESULT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
