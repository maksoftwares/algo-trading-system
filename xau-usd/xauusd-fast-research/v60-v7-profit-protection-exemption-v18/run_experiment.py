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
CONFIG = ROOT / "config" / "experiment.json"
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
        actual = sha256_file(resolve(str(item["path"])))
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")


def profit_factor(values: Iterable[float]) -> float | None:
    pnl = np.asarray(list(values), dtype=float)
    gross_profit = float(pnl[pnl > 0.0].sum())
    gross_loss = -float(pnl[pnl < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0.0 else None


def closed_metrics(
    frame: pd.DataFrame,
    *,
    pnl_column: str = "pnl_usd",
    close_column: str = "exit_time_utc",
) -> dict[str, Any]:
    ordered = frame.sort_values([close_column, "trade_id"], kind="stable")
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


def monthly_table(frame: pd.DataFrame, system: str) -> pd.DataFrame:
    work = frame.copy()
    work["entry_time_utc"] = pd.to_datetime(
        work["entry_time_utc"], utc=True, format="mixed", errors="raise"
    )
    work["month"] = work["entry_time_utc"].dt.strftime("%Y-%m")
    rows = []
    for month, group in work.groupby("month", sort=True):
        rows.append({"system": system, "month": month, **closed_metrics(group)})
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


def source_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source_id, group in frame.groupby("source_id", sort=True):
        rows.append({"source_id": source_id, **closed_metrics(group)})
    return pd.DataFrame(rows)


def metric_floor_gates(
    observed: Mapping[str, Any], reference: Mapping[str, Any], prefix: str
) -> dict[str, bool]:
    tolerance = 1e-9
    challenger = observed["challenger"]
    floor = reference["challenger"]
    gates = {
        f"{prefix}_net_not_lower": challenger["net_pnl_usd"] + tolerance
        >= floor["net_pnl_usd"],
        f"{prefix}_profit_factor_not_lower": challenger["profit_factor"] + tolerance
        >= floor["profit_factor"],
        f"{prefix}_closed_drawdown_not_higher": challenger[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= floor["maximum_lifetime_closed_drawdown_usd"] + tolerance,
        f"{prefix}_equity_drawdown_not_higher": challenger[
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


def annual_floor_gates(
    observed: pd.DataFrame,
    reference_rows: Sequence[Mapping[str, Any]],
    prefix: str,
) -> dict[str, bool]:
    reference = {
        int(row["year"]): float(row["challenger_net_pnl_usd"])
        for row in reference_rows
    }
    actual = {
        int(row.year): float(row.challenger_net_pnl_usd)
        for row in observed.itertuples(index=False)
    }
    if set(reference) != set(actual):
        raise ValueError("Annual comparison years changed")
    return {
        f"{prefix}_{year}_not_lower": actual[year] + 1e-9 >= reference[year]
        for year in sorted(reference)
    }


def stress_floor_gates(
    observed: Mapping[str, Any],
    annual: pd.DataFrame,
    reference: Mapping[str, Any],
    prefix: str,
) -> dict[str, bool]:
    tolerance = 1e-9
    challenger = observed["challenger"]
    gates = {
        f"{prefix}_net_not_lower": challenger["net_pnl_usd"] + tolerance
        >= float(reference["challenger_net_pnl_usd"]),
        f"{prefix}_profit_factor_not_lower": challenger["profit_factor"] + tolerance
        >= float(reference["challenger_profit_factor"]),
        f"{prefix}_closed_drawdown_not_higher": challenger[
            "maximum_lifetime_closed_drawdown_usd"
        ]
        <= float(reference["challenger_closed_drawdown_usd"]) + tolerance,
        f"{prefix}_equity_drawdown_not_higher": challenger[
            "maximum_lifetime_equity_drawdown_usd"
        ]
        <= float(reference["challenger_equity_drawdown_usd"]) + tolerance,
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
    gates.update(annual_floor_gates(annual, reference["annual"], f"{prefix}_annual"))
    return {name: bool(value) for name, value in gates.items()}


def render_markdown(result: Mapping[str, Any]) -> str:
    v60 = result["historical"]["baseline"]
    v6 = result["frozen_v6"]["challenger"]
    v18 = result["historical"]["challenger"]
    lines = [
        f"# {result['report_title']} Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Historical exposed research only. No broker or deployment action is authorized.",
        "",
        "| Metric | Deployed V60 | Frozen V6 | V18 | V18 vs V6 |",
        "|---|---:|---:|---:|---:|",
        f"| Trades | {v60['trades_closed']} | {v6['trades_closed']} | {v18['trades_closed']} | {v18['trades_closed'] - v6['trades_closed']:+d} |",
        f"| Net P/L | ${v60['net_pnl_usd']:.2f} | ${v6['net_pnl_usd']:.2f} | ${v18['net_pnl_usd']:.2f} | ${v18['net_pnl_usd'] - v6['net_pnl_usd']:+.2f} |",
        f"| Profit factor | {v60['profit_factor']:.4f} | {v6['profit_factor']:.4f} | {v18['profit_factor']:.4f} | {v18['profit_factor'] - v6['profit_factor']:+.4f} |",
        f"| Closed drawdown | ${v60['maximum_lifetime_closed_drawdown_usd']:.2f} | ${v6['maximum_lifetime_closed_drawdown_usd']:.2f} | ${v18['maximum_lifetime_closed_drawdown_usd']:.2f} | ${v18['maximum_lifetime_closed_drawdown_usd'] - v6['maximum_lifetime_closed_drawdown_usd']:+.2f} |",
        f"| Equity drawdown | ${v60['maximum_lifetime_equity_drawdown_usd']:.2f} | ${v6['maximum_lifetime_equity_drawdown_usd']:.2f} | ${v18['maximum_lifetime_equity_drawdown_usd']:.2f} | ${v18['maximum_lifetime_equity_drawdown_usd'] - v6['maximum_lifetime_equity_drawdown_usd']:+.2f} |",
        "",
        "## Mechanism exercise",
        "",
        f"- V7 exempt trade IDs observed: `{len(v18['v7_profit_protection_exempt_trade_ids'])}`.",
        f"- V7-only five-second cycles: `{v18['v7_profit_protection_exempt_only_cycles']}`.",
        f"- V7/non-V7 overlap cycles: `{v18['v7_profit_protection_exempt_overlap_cycles']}`.",
        "",
        "## Gates",
        "",
    ]
    for name, value in result["gates"].items():
        lines.append(f"- `{name}`: {'PASS' if value else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "- July and August were not used as acceptance evidence.",
            "- August V7 continuation is not evaluable because its frozen unprotected source endpoint is absent.",
            "- A historical pass still requires clean Capital.com forward confirmation.",
            "- V60 remains the only broker-action policy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    validate_inputs(config)
    v6_config = json.loads(resolve(config["inputs"]["v6_config"]["path"]).read_text())
    v6_result = json.loads(resolve(config["inputs"]["v6_result"]["path"]).read_text())
    v17_result = json.loads(resolve(config["inputs"]["v17_result"]["path"]).read_text())
    if v17_result["decision"] != "DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH":
        raise ValueError("V17 does not support the V18 research lane")

    evaluator = load_module(
        "v18_shared_evaluator", resolve(config["inputs"]["shared_evaluator"]["path"])
    )
    v6_scenario = load_module(
        "v18_v6_scenario", resolve(config["inputs"]["v6_scenario"]["path"])
    )
    scenario = load_module(
        "v18_local_scenario", resolve(config["inputs"]["v18_scenario"]["path"])
    )
    features = pd.read_parquet(resolve(v6_config["inputs"]["causal_feature_ledger"]["path"]))
    if features["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger contains duplicate trade IDs")
    feature_map = {str(row["trade_id"]): row for row in features.to_dict("records")}

    def factory(replay):
        return scenario.v7_exempt_challenger_class(
            replay,
            evaluator,
            v6_scenario,
            feature_map,
            v6_config["anti_chase"],
            config["policy"],
        )

    evaluator.challenger_class = factory
    captured: list[pd.DataFrame] = []
    original_closed_trade_frame = evaluator.closed_trade_frame

    def capture(instance, candidates):
        frame = original_closed_trade_frame(instance, candidates)
        captured.append(frame.copy())
        return frame

    evaluator.closed_trade_frame = capture
    base = json.loads(
        resolve(v6_config["inputs"]["base_challenger_config"]["path"]).read_text()
    )
    with tempfile.TemporaryDirectory(prefix="v60-v18-v7-exemption-") as temporary:
        replay_config = deepcopy(base)
        for name, value in v6_config.get("v2_policy_overrides", {}).items():
            replay_config["policy"][name] = value
        replay_config["schema_version"] = config["schema_version"]
        replay_config["report_title"] = config["report_title"]
        replay_config["gates"]["minimum_trade_retention_fraction"] = float(
            config["acceptance"]["minimum_trade_retention_fraction_vs_v60"]
        )
        replay_config["gates"]["minimum_frequency_retention_fraction"] = float(
            config["acceptance"]["minimum_frequency_retention_fraction_vs_v60"]
        )
        replay_path = Path(temporary) / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        historical, annual, vetoes = evaluator.run(replay_path)
        if len(captured) != 2:
            raise ValueError(f"Expected two nominal trade frames, received {len(captured)}")
        baseline_frame, v18_frame = captured
        evaluator.closed_trade_frame = original_closed_trade_frame

        cost_stress: dict[str, Any] = {}
        for cost in config["acceptance"]["additional_cost_stress_usd_per_trade"]:
            stressed, stressed_annual, stressed_vetoes = evaluator.run(
                replay_path, additional_cost_usd_per_trade=float(cost)
            )
            reference = v6_result["cost_stress"][str(cost)]
            prefix = f"v6_cost_{str(cost).replace('.', '_')}"
            gates = stress_floor_gates(stressed, stressed_annual, reference, prefix)
            cost_stress[str(cost)] = {
                "additional_cost_usd_per_trade": float(cost),
                "challenger": stressed["challenger"],
                "windows": stressed["windows"],
                "annual": stressed_annual.to_dict("records"),
                "vetoes": int(len(stressed_vetoes)),
                "gates": gates,
                "all_gates_pass": bool(all(gates.values())),
            }
    evaluator.closed_trade_frame = original_closed_trade_frame

    monthly = monthly_table(v18_frame, "V18")
    monthly_observed = monthly_summary(monthly)
    monthly_reference = config["acceptance"]["v6_monthly_reference"]
    gates = {
        **metric_floor_gates(historical, v6_result, "v6_floor"),
        **annual_floor_gates(annual, v6_result["annual"], "v6_annual"),
        "trade_retention_vs_v60": historical["challenger"]["trades_closed"]
        >= historical["baseline"]["trades_closed"]
        * float(config["acceptance"]["minimum_trade_retention_fraction_vs_v60"]),
        "frequency_retention_vs_v60": historical["challenger"]["trades_per_weekday"]
        >= historical["baseline"]["trades_per_weekday"]
        * float(config["acceptance"]["minimum_frequency_retention_fraction_vs_v60"]),
        "losing_month_burden_not_worse_v6": monthly_observed[
            "negative_month_pnl_usd"
        ]
        + 1e-9
        >= float(monthly_reference["negative_month_pnl_usd"]),
        "worst_month_not_worse_v6": monthly_observed["worst_month_pnl_usd"] + 1e-9
        >= float(monthly_reference["worst_month_pnl_usd"]),
        "mechanism_exercised": (
            len(historical["challenger"]["v7_profit_protection_exempt_trade_ids"]) > 0
            and any(
                abs(float(historical["challenger"][name]) - float(v6_result["challenger"][name]))
                > 1e-9
                for name in (
                    "net_pnl_usd",
                    "profit_factor",
                    "maximum_lifetime_closed_drawdown_usd",
                    "maximum_lifetime_equity_drawdown_usd",
                    "trades_closed",
                )
            )
        ),
        "no_open_positions": int(historical["challenger"]["open_positions_at_end"]) == 0,
        "no_flat_deadlock": not bool(historical["challenger"]["flat_suspended_deadlock"]),
        "no_floating_deadlock": not bool(historical["challenger"]["floating_peak_deadlock"]),
        "all_cost_stress_gates": all(
            item["all_gates_pass"] for item in cost_stress.values()
        ),
    }
    passed = bool(all(gates.values()))
    result = {
        "schema_version": config["schema_version"] + "_result",
        "report_title": config["report_title"],
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "HISTORICAL_CHALLENGER_PASSES_CLEAN_FORWARD_REQUIRED"
            if passed
            else "REJECT_KEEP_V60_AND_FROZEN_V6"
        ),
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "evidence_status": config["evidence_status"],
        "policy": config["policy"],
        "historical": historical,
        "frozen_v6": {
            "challenger": v6_result["challenger"],
            "windows": v6_result["windows"],
            "annual": v6_result["annual"],
            "monthly": monthly_reference,
        },
        "delta_vs_v6": {
            "trades": historical["challenger"]["trades_closed"]
            - v6_result["challenger"]["trades_closed"],
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
        },
        "annual": annual.to_dict("records"),
        "monthly": {"v18": monthly_observed, "v6": monthly_reference},
        "source": source_table(v18_frame).to_dict("records"),
        "cost_stress": cost_stress,
        "august_2026": {
            "status": "NOT_EVALUABLE_WITH_FROZEN_ENDPOINT",
            "reason": "The exposed broker snapshot ends V7 at the actual basket close and does not contain its unprotected source endpoint.",
        },
        "gates": gates,
        "limitations": [
            "All historical outcomes were exposed before V18 nomination.",
            "V17 nominated V7 after inspecting source-level protection attribution.",
            "The historical replay cannot authorize deployment.",
            "No independent Capital.com forward endpoint exists yet for the V7 exemption.",
            "August is not evaluable without imputing V7's unprotected future exit.",
        ],
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUTPUTS / "RESULT.md").write_text(render_markdown(result), encoding="utf-8")
    annual.to_csv(OUTPUTS / "ANNUAL.csv", index=False)
    monthly.to_csv(OUTPUTS / "MONTHLY.csv", index=False)
    source_table(v18_frame).to_csv(OUTPUTS / "SOURCE.csv", index=False)
    v18_frame.to_csv(OUTPUTS / "TRADE_AUDIT.csv", index=False)
    vetoes.to_csv(OUTPUTS / "VETO_AUDIT.csv", index=False)
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "delta_vs_v6": result["delta_vs_v6"],
                "monthly": result["monthly"],
                "mechanism": {
                    "exempt_trade_ids": len(
                        historical["challenger"]["v7_profit_protection_exempt_trade_ids"]
                    ),
                    "exempt_only_cycles": historical["challenger"][
                        "v7_profit_protection_exempt_only_cycles"
                    ],
                    "overlap_cycles": historical["challenger"][
                        "v7_profit_protection_exempt_overlap_cycles"
                    ],
                },
                "failed_gates": [name for name, value in gates.items() if not value],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
