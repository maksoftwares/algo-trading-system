from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.audit import (
    build_price_ledger,
    canonical_sha256,
    directory_manifest,
    envelope_drawdown,
    floating_curve,
    load_m5_bars,
    sha256_file,
    verify_repo_sources,
    window_drawdowns,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "one_trade_per_day_floating_equity_v60.json"


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return json_ready(value.item())
    return value


def _verify_contract(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    output = ROOT / config["outputs"]["directory"]
    path = output / config["outputs"]["contract_lock"]
    if not path.is_file():
        raise FileNotFoundError("Lock the V60 contract before evaluation")
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract["config_sha256"] != sha256_file(CONFIG_PATH):
        raise ValueError("V60 config changed after contract lock")
    repo_hashes = verify_repo_sources(REPO_ROOT, config["repo_sources"])
    if repo_hashes != contract["repo_source_hashes"]:
        raise ValueError("V60 repo source set changed after lock")
    market = config["market_data"]
    if sha256_file(Path(market["modern_m5"]["path"])) != contract["modern_m5_sha256"]:
        raise ValueError("Modern M5 source changed after lock")
    if directory_manifest(market["legacy_bid_m5"]) != contract["legacy_bid_manifest"]:
        raise ValueError("Legacy bid M5 source changed after lock")
    if directory_manifest(market["legacy_ask_m5"]) != contract["legacy_ask_manifest"]:
        raise ValueError("Legacy ask M5 source changed after lock")
    implementations = {
        "audit": sha256_file(ROOT / "src" / "audit.py"),
        "runner": sha256_file(ROOT / "run_evaluation.py"),
    }
    if implementations != contract["implementation_hashes"]:
        raise ValueError("V60 implementation changed after lock")
    return contract, repo_hashes


def _load_repo_frames(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    sources = config["repo_sources"]

    def read(key: str) -> pd.DataFrame:
        return pd.read_parquet(REPO_ROOT / sources[key]["path"])

    frames = {
        key: read(key)
        for key in (
            "regime_rawtick",
            "chop_rawtick",
            "transition_rawtick",
            "v7_rawtick",
            "expansion_rawtick",
            "v25_rawtick",
        )
    }
    return read("v59_trades"), read("v59_core"), frames


def _episode_rows(label: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"scenario": label, **result}


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    contract, repo_hashes = _verify_contract(config)
    with (REPO_ROOT / config["repo_sources"]["v59_result"]["path"]).open(encoding="utf-8") as handle:
        v59_result = json.load(handle)
    if not bool(v59_result["gate"]["passed"]):
        raise ValueError("V59 inherited gates are not passed")

    trades, core, source_frames = _load_repo_frames(config)
    ledger, price_audit = build_price_ledger(
        trades,
        core,
        source_frames,
        config["price_reconstruction"],
        float(config["floating_equity"]["r1_additional_fee_stress_usd_per_trade"]),
    )
    bars, market_audit = load_m5_bars(config["market_data"])
    first_entry = ledger["entry_time"].min().floor("5min")
    last_exit = ledger["exit_time"].max().ceil("5min")
    bars = bars.loc[
        bars["timestamp_utc"].ge(first_entry - pd.Timedelta(minutes=5))
        & bars["timestamp_utc"].le(last_exit)
    ].reset_index(drop=True)
    base_curve = floating_curve(
        bars,
        ledger,
        "pnl_usd",
        "open_cost_usd",
        int(config["floating_equity"]["bar_minutes"]),
    )
    stress_curve = floating_curve(
        bars,
        ledger,
        "fee_stress_pnl_usd",
        "fee_stress_open_cost_usd",
        int(config["floating_equity"]["bar_minutes"]),
    )
    base_drawdown = envelope_drawdown(base_curve)
    stress_drawdown = envelope_drawdown(stress_curve)
    windows = window_drawdowns(base_curve, stress_curve, config["windows"])

    tolerance = float(config["price_reconstruction"]["absolute_tolerance"])
    base_endpoint = float(ledger["pnl_usd"].sum())
    stress_endpoint = float(ledger["fee_stress_pnl_usd"].sum())
    base_reconciled = abs(base_endpoint - float(trades["pnl_usd"].sum())) <= tolerance
    expected_stress = base_endpoint - float(
        ledger["is_r1"].sum()
        * config["floating_equity"]["r1_additional_fee_stress_usd_per_trade"]
    )
    stress_reconciled = abs(stress_endpoint - expected_stress) <= tolerance
    raw_limit = float(config["floating_equity"]["maximum_raw_drawdown_usd"])
    buffered_limit = float(config["floating_equity"]["maximum_allowed_drawdown_usd"])
    buffer_multiplier = float(config["floating_equity"]["capital_buffer_multiplier"])
    required = windows.loc[windows["window"].isin(config["required_windows"])]
    checks = {
        "v59_inherited_gates": bool(v59_result["gate"]["passed"]),
        "all_trades_price_reconstructed": int(len(ledger)) == int(len(trades)),
        "base_endpoint_reconciled": bool(base_reconciled),
        "fee_stress_endpoint_reconciled": bool(stress_reconciled),
        "full_history_base_raw_drawdown": base_drawdown["maximum_drawdown_usd"] <= raw_limit,
        "full_history_fee_stress_raw_drawdown": stress_drawdown["maximum_drawdown_usd"] <= raw_limit,
        "full_history_base_buffered_drawdown": base_drawdown["maximum_drawdown_usd"] * buffer_multiplier <= buffered_limit,
        "full_history_fee_stress_buffered_drawdown": stress_drawdown["maximum_drawdown_usd"] * buffer_multiplier <= buffered_limit,
        "required_windows_base_raw_drawdown": bool((required["base_floating_drawdown_usd"] <= raw_limit).all()),
        "required_windows_fee_stress_raw_drawdown": bool((required["fee_stress_floating_drawdown_usd"] <= raw_limit).all()),
    }
    passed = bool(all(checks.values()))
    decision = (
        "V60_WHOLE_ACCOUNT_FLOATING_EQUITY_GATE_PASS"
        if passed
        else "V60_WHOLE_ACCOUNT_FLOATING_EQUITY_GATE_FAIL_TERMINAL"
    )
    result = {
        "schema_version": "xauusd_one_trade_per_day_floating_equity_v60_result",
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "repo_source_hashes": repo_hashes,
        "price_reconstruction_audit": price_audit,
        "market_data_audit": market_audit,
        "evaluated_bar_count": int(len(bars)),
        "base_endpoint_pnl_usd": base_endpoint,
        "fee_stress_endpoint_pnl_usd": stress_endpoint,
        "base_floating": base_drawdown,
        "fee_stress_floating": stress_drawdown,
        "maximum_open_positions": int(base_curve["open_positions"].max()),
        "maximum_open_addons": int(base_curve["open_addons"].max()),
        "maximum_known_initial_risk_usd": float(base_curve["known_initial_risk_usd"].max()),
        "maximum_addon_initial_risk_usd": float(base_curve["addon_initial_risk_usd"].max()),
        "capital_gate": {
            "starting_equity_usd": config["floating_equity"]["starting_equity_usd"],
            "maximum_allowed_drawdown_usd": buffered_limit,
            "capital_buffer_multiplier": buffer_multiplier,
            "maximum_raw_drawdown_usd": raw_limit,
        },
        "checks": checks,
        "passed": passed,
        "limitations": {
            "m5_envelope_not_exact_tick_curve": True,
            "boundary_bars_intentionally_conservative": True,
            "native_r1_fee_evidence_complete": False,
            "mt5_portfolio_parity_required": True,
            "prospective_shadow_required": True,
        },
        "research_controls": config["research_controls"],
    }
    result = json_ready(result)
    result["result_sha256"] = canonical_sha256(result)

    output = ROOT / config["outputs"]["directory"]
    ledger.to_parquet(output / config["outputs"]["price_ledger"], index=False)
    windows.to_csv(output / config["outputs"]["windows"], index=False, lineterminator="\n")
    episodes = pd.DataFrame(
        [_episode_rows("LOCKED_PNL", base_drawdown), _episode_rows("R1_FEE_STRESS", stress_drawdown)]
    )
    episodes.to_csv(output / config["outputs"]["episodes"], index=False, lineterminator="\n")
    (output / config["outputs"]["result_json"]).write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# One-Trade-Per-Day Floating Equity V60 Result",
        "",
        f"Decision: `{decision}`",
        "",
        f"Reconstructed trades: **{len(ledger)} / {len(trades)}**",
        f"Maximum concurrent positions: **{int(base_curve['open_positions'].max())}**",
        f"Maximum concurrent add-ons: **{int(base_curve['open_addons'].max())}**",
        "",
        "| Scenario | Raw floating DD | Buffered DD | Peak UTC | Trough UTC |",
        "|---|---:|---:|---|---|",
        f"| Locked P&L | {base_drawdown['maximum_drawdown_usd']:.2f} | {base_drawdown['maximum_drawdown_usd'] * buffer_multiplier:.2f} | {base_drawdown['peak_time_utc']} | {base_drawdown['trough_time_utc']} |",
        f"| R1 +$0.30 fee stress | {stress_drawdown['maximum_drawdown_usd']:.2f} | {stress_drawdown['maximum_drawdown_usd'] * buffer_multiplier:.2f} | {stress_drawdown['peak_time_utc']} | {stress_drawdown['trough_time_utc']} |",
        "",
        f"Locked raw-DD limit: **${raw_limit:.2f}**; buffered hard limit: **${buffered_limit:.2f}**.",
        "",
        "| Window | Base floating DD | Fee-stress floating DD |",
        "|---|---:|---:|",
    ]
    for row in windows.itertuples(index=False):
        lines.append(
            f"| {row.window} | {row.base_floating_drawdown_usd:.2f} | {row.fee_stress_floating_drawdown_usd:.2f} |"
        )
    failed = [name for name, ok in checks.items() if not ok]
    lines.extend(
        [
            "",
            f"Failed checks: `{failed}`",
            "",
            "Historical research only. MT5 portfolio parity and sealed prospective shadow evidence remain required.",
        ]
    )
    (output / config["outputs"]["result_markdown"]).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    artifacts = {}
    for key in ("contract_lock", "price_ledger", "windows", "episodes", "result_json", "result_markdown"):
        path = output / config["outputs"][key]
        artifacts[key] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    manifest = {
        "schema_version": "xauusd_one_trade_per_day_floating_equity_v60_manifest",
        "artifacts": artifacts,
    }
    (output / config["outputs"]["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(decision)
    print(result["result_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
