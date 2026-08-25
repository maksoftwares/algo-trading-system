from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
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

from src.scenario import ProtectionState, managed_challenger_class, update_protection


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


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for name, item in config["inputs"].items():
        actual = sha256_file(resolve(item["path"]))
        if actual != item["sha256"]:
            raise ValueError(f"Input identity changed: {name}: {actual}")
    return config


def feature_map(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    return {str(row["trade_id"]): row for row in frame.to_dict("records")}


def comparative_gates(gates: Mapping[str, Any]) -> dict[str, bool]:
    return {
        name: bool(value)
        for name, value in gates.items()
        if name not in {"baseline_net_identity", "baseline_trade_identity"}
    }


def pnl_series_metrics(values: pd.Series) -> dict[str, Any]:
    pnl = pd.to_numeric(values, errors="raise").astype(float)
    wins = pnl.loc[pnl.gt(0.0)]
    losses = pnl.loc[pnl.lt(0.0)]
    gross_profit = float(wins.sum())
    gross_loss = -float(losses.sum())
    equity = pd.Series([0.0, *pnl.cumsum().tolist()])
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


def floor_gates(
    observed: Mapping[str, Any], reference: Mapping[str, Any], prefix: str
) -> dict[str, bool]:
    tolerance = 1e-9
    challenger = observed["challenger"]
    floor = reference["challenger"]
    gates = {
        f"{prefix}_full_net_not_lower": challenger["net_pnl_usd"] + tolerance
        >= floor["net_pnl_usd"],
        f"{prefix}_full_profit_factor_not_lower": challenger["profit_factor"]
        + tolerance
        >= floor["profit_factor"],
        f"{prefix}_full_closed_drawdown_not_higher": challenger[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= floor["maximum_lifetime_closed_drawdown_usd"] + tolerance,
        f"{prefix}_full_equity_drawdown_not_higher": challenger[
            "maximum_lifetime_equity_drawdown_usd"
        ]
        <= floor["maximum_lifetime_equity_drawdown_usd"] + tolerance,
    }
    for window_id in ("3m", "6m", "12m"):
        current = observed["windows"][window_id]["challenger"]
        prior = reference["windows"][window_id]["challenger"]
        gates[f"{prefix}_{window_id}_net_not_lower"] = (
            current["net_pnl_usd"] + tolerance >= prior["net_pnl_usd"]
        )
        gates[f"{prefix}_{window_id}_profit_factor_not_lower"] = (
            current["profit_factor"] + tolerance >= prior["profit_factor"]
        )
    return {name: bool(value) for name, value in gates.items()}


def stress_floor_gates(
    observed: Mapping[str, Any], reference: Mapping[str, Any]
) -> dict[str, bool]:
    tolerance = 1e-9
    return {
        "net_not_below_v12": observed["challenger_net_pnl_usd"] + tolerance
        >= reference["challenger_net_pnl_usd"],
        "profit_factor_not_below_v12": observed["challenger_profit_factor"]
        + tolerance
        >= reference["challenger_profit_factor"],
        "closed_drawdown_not_above_v12": observed["challenger_closed_drawdown_usd"]
        <= reference["challenger_closed_drawdown_usd"] + tolerance,
        "equity_drawdown_not_above_v12": observed["challenger_equity_drawdown_usd"]
        <= reference["challenger_equity_drawdown_usd"] + tolerance,
    }


def closed_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    ordered = frame.sort_values(["close_ms", "candidate_id"], kind="stable")
    pnl = pd.to_numeric(ordered["pnl_usd"], errors="raise").astype(float)
    gross_profit = float(pnl.clip(lower=0.0).sum())
    gross_loss = -float(pnl.clip(upper=0.0).sum())
    equity = pd.Series([0.0, *pnl.cumsum().tolist()])
    drawdown = equity.cummax() - equity
    return {
        "trades": int(len(pnl)),
        "wins": int(pnl.gt(0.0).sum()),
        "losses": int(pnl.lt(0.0).sum()),
        "net_pnl_usd": float(pnl.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "win_rate": float(pnl.gt(0.0).mean()) if len(pnl) else None,
        "closed_drawdown_usd": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def august_vetoes(
    trades: pd.DataFrame,
    anti_audit: pd.DataFrame,
    anti_rule: Mapping[str, Any],
    v12_scenario,
) -> pd.DataFrame:
    features = anti_audit.copy()
    if features["candidate_id"].duplicated().any():
        raise ValueError("August anti-chase features contain duplicate candidates")
    proposal: dict[str, bool] = {}
    for row in features.to_dict("records"):
        proposal[str(row["candidate_id"])] = v12_scenario.anti_chase_veto(
            row,
            int(float(row["prior_source_executed_count"])),
            anti_rule,
        )
    result = trades.copy()
    result["v6_antichase_proposal"] = (
        result["candidate_id"].astype(str).map(proposal).fillna(False).astype(bool)
    )
    result["combined_veto"] = result["v2_baseline_path_proposal"].astype(bool) | result[
        "v6_antichase_proposal"
    ]
    return result


def apply_august_management(
    trades: pd.DataFrame,
    quotes: pd.DataFrame,
    policy: Mapping[str, Any],
) -> pd.DataFrame:
    quote_ms = quotes["cycle_ms"].to_numpy(dtype=np.int64)
    bid = quotes["bid"].to_numpy(dtype=float)
    ask = quotes["ask"].to_numpy(dtype=float)
    records: list[dict[str, Any]] = []
    for row in trades.to_dict("records"):
        start = int(row["broker_entry_ms"])
        end = int(row["broker_exit_ms"])
        left = int(np.searchsorted(quote_ms, start, side="left"))
        right = int(np.searchsorted(quote_ms, end, side="right"))
        state = ProtectionState()
        managed = False
        pnl = float(row["broker_pnl_usd"])
        close_ms = end
        peak = 0.0
        multiplier = float(row["volume_lots"]) / 0.01
        direction = str(row["direction"]).upper()
        for index in range(left, right):
            side = bid[index] if direction == "LONG" else ask[index]
            sign = 1.0 if direction == "LONG" else -1.0
            open_pnl = (
                sign * (float(side) - float(row["entry_price"])) * multiplier
                - float(row["entry_cost_usd"])
            )
            action = update_protection(
                state, policy, float(row["initial_risk_usd"]), open_pnl
            )
            peak = state.peak_pnl_usd
            if action == "CLOSE":
                managed = True
                pnl = float(open_pnl)
                close_ms = int(quote_ms[index])
                break
        output = dict(row)
        output.update(
            {
                "pnl_usd": pnl,
                "close_ms": close_ms,
                "managed_close": managed,
                "armed": state.armed,
                "peak_open_pnl_usd": peak,
                "original_broker_pnl_usd": float(row["broker_pnl_usd"]),
            }
        )
        records.append(output)
    return pd.DataFrame(records)


def main() -> int:
    config = load_config()
    inputs = config["inputs"]
    v12_config = json.loads(resolve(inputs["v12_config"]["path"]).read_text())
    frozen_v12 = json.loads(resolve(inputs["frozen_v12_result"]["path"]).read_text())
    frozen_v6 = json.loads(resolve(inputs["frozen_v6_result"]["path"]).read_text())
    v12_scenario = load_module(
        "v13_v12_scenario", resolve(inputs["v12_scenario"]["path"])
    )
    evaluator = load_module(
        "v13_shared_evaluator",
        resolve(v12_config["inputs"]["shared_evaluator"]["path"]),
    )
    anti_module = load_module(
        "v13_crossfeed",
        resolve(v12_config["inputs"]["antichase_experiment_source"]["path"]),
    )
    features = pd.read_parquet(
        resolve(v12_config["inputs"]["causal_feature_ledger"]["path"])
    )
    features_by_trade = feature_map(features)
    base = json.loads(
        resolve(v12_config["inputs"]["base_challenger_config"]["path"]).read_text()
    )
    original_factory = evaluator.challenger_class

    def configure_scenario(incremental_cost_stress_usd: float) -> None:
        evaluator.challenger_class = lambda replay: managed_challenger_class(
            replay,
            evaluator,
            v12_scenario,
            features_by_trade,
            v12_config["anti_chase"],
            config["individual_profit_lock"],
            source_health_cost_offset_usd=float(incremental_cost_stress_usd),
        )

    with tempfile.TemporaryDirectory(prefix="v60-v13-profit-lock-") as temporary:
        replay_config = deepcopy(base)
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = "V60 Canonical Health Profit Lock V13"
        replay_config["gates"]["minimum_trade_retention_fraction"] = float(
            config["acceptance"]["minimum_trade_retention_fraction"]
        )
        replay_config["gates"]["minimum_frequency_retention_fraction"] = float(
            config["acceptance"]["minimum_frequency_retention_fraction"]
        )
        replay_path = Path(temporary) / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        configure_scenario(0.0)
        historical, annual, vetoes = evaluator.run(replay_path)
        cost_stress: dict[str, Any] = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            configure_scenario(float(cost))
            stressed, stressed_annual, stressed_vetoes = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(cost)
            )
            comparative = comparative_gates(stressed["gates"])
            item = {
                "additional_cost_usd_per_trade": float(cost),
                "baseline_net_pnl_usd": stressed["baseline"]["net_pnl_usd"],
                "challenger_net_pnl_usd": stressed["challenger"]["net_pnl_usd"],
                "baseline_profit_factor": stressed["baseline"]["profit_factor"],
                "challenger_profit_factor": stressed["challenger"]["profit_factor"],
                "baseline_closed_drawdown_usd": stressed["baseline"][
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "challenger_closed_drawdown_usd": stressed["challenger"][
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "baseline_equity_drawdown_usd": stressed["baseline"][
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "challenger_equity_drawdown_usd": stressed["challenger"][
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "individual_profit_protection_arms": stressed["challenger"][
                    "individual_profit_protection_arms"
                ],
                "individual_profit_protection_closes": stressed["challenger"][
                    "individual_profit_protection_closes"
                ],
                "executed_vetoes": int(stressed["baseline_executed_veto_count"]),
                "veto_trade_ids": sorted(
                    stressed_vetoes.loc[
                        stressed_vetoes["baseline_runtime_executed"]
                        .astype(str)
                        .str.lower()
                        .eq("true"),
                        "trade_id",
                    ].astype(str)
                ),
                "annual": stressed_annual.to_dict("records"),
                "windows": stressed["windows"],
                "comparative_gates": comparative,
                "all_comparative_gates_pass": bool(all(comparative.values())),
            }
            reference = frozen_v12["cost_stress"][str(cost)]
            item["v12_floor_gates"] = stress_floor_gates(item, reference)
            item["all_v12_floor_gates_pass"] = bool(
                all(item["v12_floor_gates"].values())
            )
            cost_stress[str(cost)] = item
    evaluator.challenger_class = original_factory

    august_trades = pd.read_parquet(resolve(inputs["august_trade_snapshot"]["path"]))
    august_quotes = pd.read_parquet(resolve(inputs["august_quote_snapshot"]["path"]))
    anti_audit = pd.read_csv(resolve(inputs["antichase_august_audit"]["path"]))
    august_trades = august_vetoes(
        august_trades, anti_audit, v12_config["anti_chase"], v12_scenario
    )
    baseline_august = august_trades.assign(
        pnl_usd=august_trades["broker_pnl_usd"],
        close_ms=august_trades["broker_exit_ms"],
    )
    retained_august = august_trades.loc[~august_trades["combined_veto"]].copy()
    managed_august = apply_august_management(
        retained_august, august_quotes, config["individual_profit_lock"]
    )
    same_retained_entry_set = (
        len(managed_august) == len(retained_august)
        and set(managed_august["candidate_id"].astype(str))
        == set(retained_august["candidate_id"].astype(str))
    )
    august = {
        "baseline_v60": closed_metrics(baseline_august),
        "frozen_v12_entry_policy": closed_metrics(
            retained_august.assign(
                pnl_usd=retained_august["broker_pnl_usd"],
                close_ms=retained_august["broker_exit_ms"],
            )
        ),
        "challenger": closed_metrics(managed_august),
        "managed_closes": int(managed_august["managed_close"].sum()),
        "armed_trades": int(managed_august["armed"].sum()),
        "same_retained_entry_set": bool(same_retained_entry_set),
    }
    august["delta_vs_v60_net_pnl_usd"] = (
        august["challenger"]["net_pnl_usd"] - august["baseline_v60"]["net_pnl_usd"]
    )
    august["delta_vs_v12_net_pnl_usd"] = (
        august["challenger"]["net_pnl_usd"]
        - august["frozen_v12_entry_policy"]["net_pnl_usd"]
    )
    tolerance = 1e-9
    august_gates = {
        "positive_net_pnl": august["challenger"]["net_pnl_usd"] > 0.0,
        "net_not_below_frozen_v6": august["challenger"]["net_pnl_usd"]
        + tolerance
        >= float(config["acceptance"]["august_minimum_net_pnl_usd"]),
        "profit_factor_not_below_frozen_v6": august["challenger"]["profit_factor"]
        + tolerance
        >= float(config["acceptance"]["august_minimum_profit_factor"]),
        "closed_drawdown_not_above_frozen_v6": august["challenger"][
            "closed_drawdown_usd"
        ]
        <= float(config["acceptance"]["august_maximum_closed_drawdown_usd"])
        + tolerance,
        "same_retained_entry_set": bool(august["same_retained_entry_set"]),
    }

    executed = vetoes.loc[
        vetoes["baseline_runtime_executed"].astype(str).str.lower().eq("true")
    ].copy()
    executed_ids = set(executed["trade_id"].astype(str))
    crossfeed = anti_module.crossfeed_comparison(
        pd.read_csv(
            resolve(v12_config["inputs"]["crossfeed_priced_runtime"]["path"]),
            low_memory=False,
        ),
        executed_ids,
    )
    anti_component_rows = executed.loc[
        executed["proposal_rule"].astype(str).str.contains(
            "V57_WEAK_FOLLOWTHROUGH_ANTICHASE", regex=False
        )
    ]
    v2_component_rows = executed.loc[
        executed["proposal_rule"].astype(str).str.contains(
            "V2_SOURCE_HEALTH", regex=False
        )
    ]
    anti_component = pnl_series_metrics(
        anti_component_rows["baseline_runtime_pnl_usd"]
    )
    v2_component = pnl_series_metrics(
        v2_component_rows["baseline_runtime_pnl_usd"]
    )
    anti_component["avoided_pnl_usd"] = -anti_component["net_pnl_usd"]
    v2_component["avoided_pnl_usd"] = -v2_component["net_pnl_usd"]
    component_gates = {
        "anti_minimum_rows": anti_component["trades"] >= 1,
        "anti_positive_avoided_pnl": anti_component["avoided_pnl_usd"] > 0.0,
        "anti_profit_factor_below_0_8": anti_component["profit_factor"] is not None
        and anti_component["profit_factor"] < 0.8,
        "v2_minimum_rows": v2_component["trades"] >= 10,
        "v2_positive_avoided_pnl": v2_component["avoided_pnl_usd"] > 0.0,
        "v2_profit_factor_below_0_8": v2_component["profit_factor"] is not None
        and v2_component["profit_factor"] < 0.8,
    }
    v12_floors = floor_gates(historical, frozen_v12, "v12")
    v6_floors = floor_gates(historical, frozen_v6, "v6")
    retention = historical["challenger"]["trades_closed"] / historical["baseline"][
        "trades_closed"
    ]
    management_support = {
        "minimum_historical_arms": historical["challenger"][
            "individual_profit_protection_arms"
        ]
        >= int(config["acceptance"]["minimum_historical_protection_arms"]),
        "minimum_historical_closes": historical["challenger"][
            "individual_profit_protection_closes"
        ]
        >= int(config["acceptance"]["minimum_historical_protection_closes"]),
        "no_deadlock": not bool(
            historical["challenger"]["flat_suspended_deadlock"]
            or historical["challenger"]["floating_peak_deadlock"]
            or historical["challenger"]["open_positions_at_end"]
        ),
    }
    gates = {
        "nominal_v60_comparative_gates": bool(all(historical["gates"].values())),
        "nominal_v12_floors": bool(all(v12_floors.values())),
        "nominal_v6_floors": bool(all(v6_floors.values())),
        "locked_trade_retention": retention
        >= float(config["acceptance"]["minimum_trade_retention_fraction"]),
        "veto_component_support": bool(all(component_gates.values())),
        "management_support": bool(all(management_support.values())),
        "cost_stress_v60_comparative_gates": bool(
            all(item["all_comparative_gates_pass"] for item in cost_stress.values())
        ),
        "cost_stress_v12_floors": bool(
            all(item["all_v12_floor_gates_pass"] for item in cost_stress.values())
        ),
        "august_hard_objective": bool(all(august_gates.values())),
        "crossfeed_delta_not_below_v12": crossfeed["delta_net_pnl_usd"]
        >= frozen_v12["dukascopy_crossfeed"]["delta_net_pnl_usd"],
        "crossfeed_every_year_nonnegative": bool(crossfeed["every_year_nonnegative"]),
        "clean_forward_evidence": False,
    }
    retrospective_pass = all(
        value for name, value in gates.items() if name != "clean_forward_evidence"
    )
    result = historical
    result.update(
        {
            "schema_version": config["schema_version"] + "_result",
            "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "decision": (
                "HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED"
                if retrospective_pass
                else "KEEP_DEPLOYED_V60"
            ),
            "deployment_authorized": False,
            "broker_action_authorized": False,
            "evidence_status": config["evidence_status"],
            "individual_profit_lock": config["individual_profit_lock"],
            "trade_retention": retention,
            "v12_floor_gates": v12_floors,
            "v6_floor_gates": v6_floors,
            "management_support_gates": management_support,
            "veto_component_gates": component_gates,
            "antichase_component": anti_component,
            "v2_component": v2_component,
            "august_2026_through_25": august,
            "august_gates": august_gates,
            "dukascopy_crossfeed": crossfeed,
            "cost_stress": cost_stress,
            "combined_gates": gates,
            "limitations": [
                "All historical and August outcomes were exposed before this composition.",
                "P05 was not selected by its original development-selection rule.",
                "The historical replay uses Dukascopy five-second executable quote states aligned to Capital entries.",
                "August uses frozen Capital.com five-second quote paths and the exposed V12 baseline-path veto set.",
                "Only clean prospective evidence can authorize a runtime change.",
            ],
        }
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False, lineterminator="\n")
    vetoes.to_csv(OUTPUTS / "HISTORICAL_VETOES.csv", index=False, lineterminator="\n")
    managed_august.to_csv(
        OUTPUTS / "AUGUST_2026_TRADE_AUDIT.csv", index=False, lineterminator="\n"
    )
    lines = [
        "# V60 Canonical Health Profit Lock V13 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        (
            f"Historical: {historical['challenger']['trades_closed']} trades, "
            f"${historical['challenger']['net_pnl_usd']:.2f} net, PF "
            f"{historical['challenger']['profit_factor']:.3f}, closed DD "
            f"${historical['challenger']['maximum_lifetime_closed_drawdown_usd']:.2f}, "
            f"equity DD ${historical['challenger']['maximum_lifetime_equity_drawdown_usd']:.2f}."
        ),
        (
            f"August through 25: ${august['challenger']['net_pnl_usd']:.2f} net, "
            f"PF {august['challenger']['profit_factor']:.3f}, closed DD "
            f"${august['challenger']['closed_drawdown_usd']:.2f}; "
            f"{august['managed_closes']} managed closes."
        ),
        (
            f"Historical protection: {historical['challenger']['individual_profit_protection_arms']} "
            f"arms and {historical['challenger']['individual_profit_protection_closes']} closes."
        ),
        "",
        "Exposed retrospective result only. Deployment remains prohibited.",
        "",
    ]
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "historical_net_pnl_usd": historical["challenger"]["net_pnl_usd"],
                "historical_closed_drawdown_usd": historical["challenger"][
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "august_net_pnl_usd": august["challenger"]["net_pnl_usd"],
                "gates": gates,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
