from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


LANE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = LANE_ROOT.parents[2]
SRC = LANE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest import run_portfolio  # noqa: E402
from data_adapter import load_bundle, sha256_file  # noqa: E402
from metrics import gate_audit, monthly_results, profit_factor, rolling_results, standalone_family_gate, summary  # noqa: E402
from regime import attach_regime, classify_regimes  # noqa: E402
from strategies import FAMILY_IDS, generate_signals  # noqa: E402


BRANCH = "codex/xau-multiregime-fast-discovery-v1"
BASE_COMMIT = "50bf9b5dbcc563a20254e9041e41ec0762c86f6e"


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if pd.isna(value):
        return None
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def portable(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _segment_rows(trades: pd.DataFrame, config: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    rows = []
    for name, boundaries in config["segments"].items():
        start, end = pd.Timestamp(boundaries[0]), pd.Timestamp(boundaries[1])
        group = trades.loc[(trades["entry_time"] >= start) & (trades["entry_time"] < end)] if len(trades) else trades
        rows.append({
            "scope": scope, "segment": name, "start": start, "end_exclusive": end,
            "trades": int(len(group)), "net_r": float(group["net_r"].sum()) if len(group) else 0.0,
            "profit_factor": profit_factor(group["net_r"]) if len(group) else None,
            "expectancy_r": float(group["net_r"].mean()) if len(group) else 0.0,
            "stress_net_r": float(group["stress_net_r"].sum()) if len(group) else 0.0,
            "stress_profit_factor": profit_factor(group["stress_net_r"]) if len(group) else None,
        })
    return rows


def _group_results(trades: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in trades.groupby(columns, sort=True) if len(trades) else []:
        keys = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(columns, keys, strict=True))
        row.update({
            "trades": int(len(group)), "wins": int((group["net_r"] > 0).sum()), "losses": int((group["net_r"] < 0).sum()),
            "net_r": float(group["net_r"].sum()), "profit_factor": profit_factor(group["net_r"]),
            "expectancy_r": float(group["net_r"].mean()), "stress_net_r": float(group["stress_net_r"].sum()),
            "stress_profit_factor": profit_factor(group["stress_net_r"]), "stress_expectancy_r": float(group["stress_net_r"].mean()),
        })
        rows.append(row)
    result_columns = [
        *columns, "trades", "wins", "losses", "net_r", "profit_factor", "expectancy_r",
        "stress_net_r", "stress_profit_factor", "stress_expectancy_r",
    ]
    return pd.DataFrame(rows, columns=result_columns)


def _abandonment(gates: dict[str, Any], portfolio: dict[str, Any], segment_rows: pd.DataFrame, coverage: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    if not coverage["segment_d_complete"]:
        return "MULTIREGIME_V1_DATA_INCOMPLETE_NO_ADVANCEMENT", ["SEGMENT_D_UNAVAILABLE_OR_INCOMPLETE"]
    if portfolio["average_trades_per_year"] < 120:
        reasons.append("PORTFOLIO_FREQUENCY_BELOW_120_PER_YEAR")
    if not gates["at_least_one_family_passes"]:
        reasons.append("NO_FAMILY_PASSES_STANDALONE_GATES")
    if (portfolio["profit_factor"] or 0) < 1.20:
        reasons.append("BASELINE_PORTFOLIO_PF_BELOW_1P20")
    if portfolio["expectancy_r"] < 0.05:
        reasons.append("BASELINE_PORTFOLIO_EXPECTANCY_BELOW_0P05R")
    if (portfolio["stress_profit_factor"] or 0) <= 1.00:
        reasons.append("STRESS_PORTFOLIO_PF_AT_OR_BELOW_1P00")
    segment_d = segment_rows.loc[(segment_rows["scope"] == "PORTFOLIO") & (segment_rows["segment"] == "D")].iloc[0]
    if int(segment_d["trades"]) == 0 or segment_d["net_r"] < 0 or pd.isna(segment_d["profit_factor"]) or segment_d["profit_factor"] < 1.05:
        reasons.append("SEGMENT_D_NEGATIVE_OR_PF_BELOW_1P05")
    if portfolio["floating_drawdown_r"] > 20:
        reasons.append("BASELINE_FLOATING_DRAWDOWN_ABOVE_20R")
    if portfolio["stress_floating_drawdown_r"] > 25:
        reasons.append("STRESS_FLOATING_DRAWDOWN_ABOVE_25R")
    if not gates["contract_granularity_adequate"]:
        reasons.append("XAUUSD_1000_ACCOUNT_CONTRACT_GRANULARITY_INADEQUATE")
    return ("MULTIREGIME_V1_ABANDONED_NO_RESCUE" if reasons else "MULTIREGIME_V1_PROMISING_CONFIRMATION_REQUIRED"), reasons


def _report(payload: dict[str, Any], family: pd.DataFrame, segments: pd.DataFrame) -> str:
    p = payload["portfolio_summary"]
    lines = [
        "# XAUUSD Multi-Regime Fast Discovery V1", "",
        f"- Branch: `{BRANCH}`", f"- Base commit: `{BASE_COMMIT}`",
        f"- Exact period: `{payload['coverage']['requested_start']}` to `{payload['coverage']['requested_end_exclusive']}` (exclusive).",
        f"- Data status: `{payload['coverage']['status']}`.", f"- Decision: `{payload['decision']}`.",
        f"- Families admitted to combined portfolio: `{', '.join(payload['portfolio_admitted_families']) or 'NONE'}`.",
        "- Engineering/deployment authorization: `NOT_AUTHORIZED`.", "",
        "## Portfolio", "",
        "| Trades | Trades/year | Median/month | PF | Exp R | Net R | Stress PF | Stress exp R | Stress net R | Floating DD R |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {p['trades']} | {p['average_trades_per_year']:.2f} | {p['median_trades_per_calendar_month']:.1f} | {p['profit_factor'] or 0:.3f} | {p['expectancy_r']:.3f} | {p['net_r']:.3f} | {p['stress_profit_factor'] or 0:.3f} | {p['stress_expectancy_r']:.3f} | {p['stress_net_r']:.3f} | {p['floating_drawdown_r']:.3f} |",
        "", "## Standalone families", "",
        "| Family | Trades | PF | Exp R | Net R | Stress PF | Stress exp R | DD R | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in family.iterrows():
        lines.append(f"| {row['strategy_id']} | {int(row['trades'])} | {row['profit_factor'] or 0:.3f} | {row['expectancy_r']:.3f} | {row['net_r']:.3f} | {row['stress_profit_factor'] or 0:.3f} | {row['stress_expectancy_r']:.3f} | {row['floating_drawdown_r']:.3f} | {row['standalone_gate_passed']} |")
    lines.extend(["", "## Segments", "", "| Scope | Segment | Trades | PF | Exp R | Net R | Stress net R |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    for _, row in segments.iterrows():
        pf_text = f"{row['profit_factor']:.3f}" if pd.notna(row["profit_factor"]) else "N/A"
        lines.append(f"| {row['scope']} | {row['segment']} | {int(row['trades'])} | {pf_text} | {row['expectancy_r']:.3f} | {row['net_r']:.3f} | {row['stress_net_r']:.3f} |")
    lines.extend([
        "", "## $1,000 account and 100x leverage", "",
        f"- Risk budget per trade: `${payload['account_audit']['risk_budget_usd']:.2f}` (0.50%).",
        f"- Contract-granularity rejects: `{payload['gate_audit']['contract_granularity_rejects']}` / `{payload['gate_audit']['valid_opportunities']}` (`{payload['gate_audit']['contract_granularity_reject_pct']:.2f}%`).",
        "- Leverage is used only for margin estimation and does not scale R returns.",
        "- Position risk uses captured native XAUUSD OrderCalcProfit parity; margin uses the broker-captured OrderCalcMargin result on the 100x account.", "",
        "## Cost and data notes", "",
        "- Baseline execution uses actual per-bar Bid/Ask spread. Stress uses the development-period P95 spread plus 0.05R slippage.",
        "- Funding uses the broker-observed interest-current swap snapshot frozen before scoring; historical swap-rate changes were not available and are not fabricated.",
        "- M5 sequencing is stop-first on ambiguous bars, stop gaps fill at the worse open, and target gaps fill at the frozen target.",
        "- Segment D is the same-broker Capital.com MT5 tail and is scored without parameter changes.", "",
        "## Abandonment reasons", "",
    ])
    lines.extend([f"- `{reason}`" for reason in payload["abandonment_reasons"]] or ["- None."])
    lines.extend(["", "There is no rescue variant for this direction."])
    return "\n".join(lines) + "\n"


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config_hash = sha256_file(config_path)
    output_dir = REPO_ROOT / config["output_dir"]; output_dir.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(REPO_ROOT, config)
    runtime_config = copy.deepcopy(config)
    runtime_config["account"]["order_calc_margin_rate"] = float(bundle.contract["order_calc_margin_rate"])
    router = classify_regimes(bundle.bars["H4"], config["router"])
    attached = {timeframe: attach_regime(bundle.bars[timeframe], router.bars) for timeframe in ("M5", "M15", "H1")}
    candidates = generate_signals(attached["M15"], attached["H1"], runtime_config)
    standalone_results = {family: run_portfolio(attached["M15"], attached["M5"], candidates.loc[candidates["strategy_id"] == family], runtime_config) for family in FAMILY_IDS}
    start, end = pd.Timestamp(config["requested_start"]), pd.Timestamp(config["requested_end_exclusive"])
    family_summaries = {family: summary(result.trades, start, end) for family, result in standalone_results.items()}
    admitted_families = [family for family, values in family_summaries.items() if standalone_family_gate(values)["passed"]]
    admitted_candidates = candidates.loc[candidates["strategy_id"].isin(admitted_families)]
    combined = run_portfolio(attached["M15"], attached["M5"], admitted_candidates, runtime_config)
    portfolio_summary = summary(combined.trades, start, end)
    monthly = monthly_results(combined.trades, start, end); rolling = rolling_results(combined.trades, start, end)
    segment_rows = _segment_rows(combined.trades, config, "PORTFOLIO")
    for family, result in standalone_results.items():
        segment_rows.extend(_segment_rows(result.trades, config, family))
    segments = pd.DataFrame(segment_rows)
    standalone_signals = pd.concat([result.signals for result in standalone_results.values()], ignore_index=True).sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    standalone_trades = pd.concat([result.trades.assign(evaluation_scope="STANDALONE") for result in standalone_results.values()], ignore_index=True).sort_values(["entry_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    combined_signal_output = combined.signals.reindex(columns=standalone_signals.columns)
    combined_trade_output = combined.trades.reindex(columns=[column for column in standalone_trades.columns if column != "evaluation_scope"])
    gates = gate_audit(family_summaries, portfolio_summary, rolling, combined.trades, standalone_signals, bundle.coverage["segment_d_complete"])
    family_rows = []
    for family, values in family_summaries.items():
        row = {"strategy_id": family, **values, "standalone_gate_passed": gates["family_gates"][family]["passed"]}
        family_rows.append(row)
    family_frame = pd.DataFrame(family_rows)
    decision, abandonment = _abandonment(gates, portfolio_summary, segments, bundle.coverage)
    account_audit = {
        "equity_usd": float(config["account"]["equity_usd"]), "risk_fraction": float(config["account"]["risk_fraction"]),
        "risk_budget_usd": float(config["account"]["equity_usd"]) * float(config["account"]["risk_fraction"]),
        "leverage": int(config["account"]["leverage"]), "native_contract_evidence": "A1_XAU_R6_ORDERCALCPROFIT_PARITY_V1",
        "volume_min": float(config["account"]["volume_min"]), "contract_size_oz": float(config["account"]["contract_size_oz"]),
        "order_calc_margin_rate": float(bundle.contract["order_calc_margin_rate"]),
    }
    payload = {
        "schema_version": "xauusd_multiregime_fast_discovery_result_v1", "branch": BRANCH, "base_commit": BASE_COMMIT,
        "config_sha256_frozen_before_scoring": config_hash, "coverage": bundle.coverage,
        "source_manifest": bundle.source_manifest, "captured_mt5_contract": bundle.contract,
        "funding_model": "FROZEN_ACTUAL_BROKER_INTEREST_CURRENT_SNAPSHOT_NOT_HISTORICAL_SERIES",
        "portfolio_summary": portfolio_summary, "family_summaries": family_summaries,
        "portfolio_admitted_families": admitted_families,
        "gate_audit": gates, "account_audit": account_audit, "decision": decision, "abandonment_reasons": abandonment,
        "parameter_revision_count_after_first_complete_run": 0, "deployment_authorized": False,
    }
    paths = {
        "result_json": output_dir / "MULTIREGIME_FAST_DISCOVERY_RESULT.json",
        "result_md": output_dir / "MULTIREGIME_FAST_DISCOVERY_RESULT.md",
        "regime_census": output_dir / "MULTIREGIME_REGIME_CENSUS.csv",
        "family_results": output_dir / "MULTIREGIME_FAMILY_RESULTS.csv",
        "segment_results": output_dir / "MULTIREGIME_SEGMENT_RESULTS.csv",
        "monthly_results": output_dir / "MULTIREGIME_MONTHLY_RESULTS.csv",
        "rolling_results": output_dir / "MULTIREGIME_ROLLING_RESULTS.csv",
        "direction_results": output_dir / "MULTIREGIME_DIRECTION_RESULTS.csv",
        "signal_ledger": output_dir / "MULTIREGIME_SIGNAL_LEDGER.csv",
        "trade_ledger": output_dir / "MULTIREGIME_TRADE_LEDGER.csv",
        "standalone_signal_ledger": output_dir / "MULTIREGIME_STANDALONE_SIGNAL_LEDGER.csv",
        "standalone_trade_ledger": output_dir / "MULTIREGIME_STANDALONE_TRADE_LEDGER.csv",
        "gate_audit": output_dir / "MULTIREGIME_GATE_AUDIT.json",
        "manifest": output_dir / "MULTIREGIME_MANIFEST.json",
    }
    write_json(paths["result_json"], payload); paths["result_md"].write_text(_report(payload, family_frame, segments), encoding="utf-8")
    router.census.to_csv(paths["regime_census"], index=False, lineterminator="\n")
    family_frame.to_csv(paths["family_results"], index=False, lineterminator="\n"); segments.to_csv(paths["segment_results"], index=False, lineterminator="\n")
    monthly.to_csv(paths["monthly_results"], index=False, lineterminator="\n"); rolling.to_csv(paths["rolling_results"], index=False, lineterminator="\n")
    _group_results(combined.trades, ["strategy_id", "direction"]).to_csv(paths["direction_results"], index=False, lineterminator="\n")
    combined_signal_output.to_csv(paths["signal_ledger"], index=False, lineterminator="\n"); combined_trade_output.to_csv(paths["trade_ledger"], index=False, lineterminator="\n")
    standalone_signals.to_csv(paths["standalone_signal_ledger"], index=False, lineterminator="\n"); standalone_trades.to_csv(paths["standalone_trade_ledger"], index=False, lineterminator="\n")
    write_json(paths["gate_audit"], gates)
    output_hashes = {name: sha256_file(path) for name, path in paths.items() if name != "manifest"}
    manifest = {
        "schema_version": "xauusd_multiregime_manifest_v1", "branch": BRANCH, "base_commit": BASE_COMMIT,
        "config": {"path": portable(config_path), "sha256": config_hash}, "inputs": bundle.source_manifest,
        "outputs": {name: {"path": portable(paths[name]), "sha256": digest} for name, digest in output_hashes.items()},
        "replay_command": f"python {portable(Path(__file__).resolve())} --config {portable(config_path)}", "decision": decision,
    }
    write_json(paths["manifest"], manifest)
    return {
        "decision": decision, "abandonment_reasons": abandonment, "portfolio_summary": portfolio_summary,
        "family_summaries": family_summaries, "outputs": {name: portable(path) for name, path in paths.items()},
        "sha256": {**output_hashes, "manifest": sha256_file(paths["manifest"])},
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", required=True, type=Path); args = parser.parse_args()
    path = args.config if args.config.is_absolute() else REPO_ROOT / args.config
    print(json.dumps(clean(run(path)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
