from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "forex" / "fx-regime-specialists-gold-trajectory-v1"
sys.path.insert(0, str(PACKAGE / "src"))

from fx_regime_specialists.campaign import (  # noqa: E402
    aggregate_fx_h1,
    build_state_table,
    load_context_h1,
    load_fx_m5,
    metric_block,
    remove_top_winners,
    route_portfolio,
    serialize,
    sha256_file,
    summarize_specialist,
)
from fx_regime_specialists.seed_decomposition import (  # noqa: E402
    assign_regime_ownership,
    generate_seed_signals,
    simulate_owned_signals,
    verify_seed_lock,
)


SPECIALIST_LABELS = {
    "s1_established_aligned_breakout": "S1 established aligned breakout",
    "s2_transition_aligned_breakout": "S2 transition aligned breakout",
    "s3_compression_release_breakout": "S3 compression-release breakout",
    "s4_neutral_normal_breakout": "S4 neutral-normal breakout",
}


def main() -> int:
    config_path = PACKAGE / "config" / "frozen_seed_decomposition.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_config = json.loads((PACKAGE / "config" / "frozen_campaign.json").read_text(encoding="utf-8"))
    hashes = verify_seed_lock(PACKAGE)
    output = PACKAGE / "outputs" / "seed_decomposition"
    cache = PACKAGE / "outputs" / "cache"
    output.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp(config["data"]["start_utc"])
    end = pd.Timestamp(config["data"]["end_utc"])
    bar_root = Path(config["data"]["fx_bar_root"])
    raw_root = Path(base_config["data"]["dukascopy_raw_root"])
    dxy, _ = load_context_h1(raw_root, "DOLLARIDXUSD", start, end, cache)
    bond, _ = load_context_h1(raw_root, "USTBONDTRUSD", start, end, cache)
    m5 = {symbol: load_fx_m5(bar_root, symbol, start, end) for symbol in ("EURUSD", "GBPUSD", "USDJPY")}
    h1 = {symbol: aggregate_fx_h1(frame) for symbol, frame in m5.items()}
    state = build_state_table(dxy, bond, h1, base_config["classifier"])

    raw_signals = generate_seed_signals(m5["USDJPY"], config["base_seed"])
    owned_signals = assign_regime_ownership(raw_signals, state)
    owned_signals.to_csv(output / "signal_ownership.csv", index=False)
    ownership_counts = owned_signals["ownership"].value_counts().to_dict()
    trades = {}
    summaries = {}
    for specialist in config["specialists"]:
        trades[specialist] = simulate_owned_signals(
            owned_signals, m5["USDJPY"], specialist, config["base_seed"], config["execution"]
        )
        trades[specialist].to_csv(output / f"{specialist}_trades.csv", index=False)
        summaries[specialist] = summarize_specialist(
            trades[specialist], config["windows"], config["admission"]
        )
    admitted = [name for name, summary in summaries.items() if summary["admitted"]]
    portfolio = route_portfolio(trades, admitted, config["router"])
    if not portfolio.empty:
        portfolio.to_csv(output / "routed_portfolio.csv", index=False)
    portfolio_summary = metric_block(portfolio)
    portfolio_status = "NO_PORTFOLIO_FORMED" if not admitted else "ROUTED_RESEARCH_PORTFOLIO"
    result = serialize(
        {
            "campaign_id": config["campaign_id"],
            "status": portfolio_status,
            "research_only": True,
            "preregistration_hashes": hashes,
            "config_sha256": sha256_file(config_path),
            "base_seed_raw_signals": len(raw_signals),
            "ownership_counts": ownership_counts,
            "specialists": summaries,
            "admitted_specialists": admitted,
            "portfolio": {"status": portfolio_status, **portfolio_summary},
            "boundary": {
                "base_seed_parameters_changed": False,
                "regime_classifier_parameters_changed": False,
                "mt5_or_broker_runtime_used": False,
                "all_results_are_development_evidence": True,
            },
        }
    )
    (output / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    verdict = PACKAGE / "FOREX_SESSION_SEED_REGIME_DECOMPOSITION_VERDICT_2026_07_27.md"
    verdict.write_text(render(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


def render(result: dict) -> str:
    lines = [
        "# USDJPY Session-Seed Regime Decomposition Verdict — 2026-07-27",
        "",
        f"Status: `{result['status']}`",
        "",
        "Boundary: offline research only. The base seed and classifier remained frozen; no MT5 or broker runtime was used.",
        "",
        f"Raw frozen-seed signals before ownership: {result['base_seed_raw_signals']}.",
        "",
        "## Ownership Census",
        "",
        "| Owner | Signals |",
        "| --- | ---: |",
    ]
    for owner, count in result["ownership_counts"].items():
        lines.append(f"| `{owner}` | {count} |")
    lines += [
        "",
        "## Standalone Experts",
        "",
        "| Expert | Trades | PF | Net R | Max DD R | Decision |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, summary in result["specialists"].items():
        block = summary["overall"]
        lines.append(
            f"| {SPECIALIST_LABELS[name]} | {block['trades']} | {fmt(block['profit_factor'])} | "
            f"{fmt(block['net_r'])} | {fmt(block['max_drawdown_r'])} | `{summary['status']}` |"
        )
    for name, summary in result["specialists"].items():
        lines += [
            "",
            f"### {SPECIALIST_LABELS[name]}",
            "",
            "| Window | Trades | PF | Net R | Expectancy R |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for window, block in summary["windows"].items():
            lines.append(
                f"| {window} | {block['trades']} | {fmt(block['profit_factor'])} | "
                f"{fmt(block['net_r'])} | {fmt(block['expectancy_r'])} |"
            )
        lines.append(
            f"\nTop-5%-winner removal: {fmt(summary['top_5_percent_winners_removed']['net_r'])}R. "
            f"Additional 0.5-pip stress: {fmt(summary['extra_half_pip_round_trip']['net_r'])}R."
        )
    lines += [
        "",
        "## Router",
        "",
        f"Admitted experts: {', '.join(result['admitted_specialists']) if result['admitted_specialists'] else 'none'}.",
        f"Router status: `{result['portfolio']['status']}`.",
        "",
        "No failed expert is rescued by aggregation. This decomposition is development evidence, not demo evidence.",
    ]
    return "\n".join(lines) + "\n"


def fmt(value) -> str:
    if isinstance(value, str):
        return value
    return f"{float(value):.4f}"


if __name__ == "__main__":
    raise SystemExit(main())
