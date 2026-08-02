from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
REPLAY_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/codex-v60-tick-runtime-replay-v1"
sys.path.insert(0, str(REPLAY_ROOT / "src"))

from replay import (  # noqa: E402
    Scenario,
    ScenarioSpec,
    apply_portfolio_protection,
    apply_runtime_risk_mode,
    load_candidates,
    load_json,
    load_quote_cache,
    prepare_quote_cache,
    resolve_input,
    timestamp_ms,
)


CONTRACT_PATH = REPLAY_ROOT / "config/SAFETY_REPAIR_REPLAY_CONTRACT.json"
OVERLAY_PATH = ROOT / "config/v60_drawdown_protection_v1_overlay.json"
OUTPUT_JSON = ROOT / "evidence/V60_DRAWDOWN_PROTECTION_V1_COMPARISON_20260802.json"
OUTPUT_MD = ROOT / "evidence/V60_DRAWDOWN_PROTECTION_V1_COMPARISON_20260802.md"
SCENARIO_ID = "deployed__position_origin_repair_full_runtime"
RECENT_START = "2026-01-01T00:00:00Z"
RECENT_END = "2026-07-01T00:00:00Z"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def scenario(
    contract: Mapping[str, Any],
    config: Mapping[str, Any],
    candidates: list[Any],
    quotes: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    spec = ScenarioSpec(
        scenario_id=SCENARIO_ID,
        starting_equity_usd=float(
            contract["evaluation"]["deployed_activation_equity_usd"]
        ),
        activation_equity_usd=float(
            contract["evaluation"]["deployed_activation_equity_usd"]
        ),
        rebaseline_days=None,
        guardian_enabled=True,
        guardian_exit_attribution="POSITION_ORIGIN",
    )
    replay = Scenario(spec, config, contract, candidates)
    return replay.simulate(quotes), replay.event_rows


def monthly(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in events
        if row["event"] == "POSITION_CLOSED"
        and RECENT_START <= str(row["timestamp_utc"]) < RECENT_END
    ]
    result = []
    for month in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"):
        values = [
            float(row["pnl_usd"])
            for row in rows
            if str(row["timestamp_utc"]).startswith(month)
        ]
        gross_profit = sum(value for value in values if value > 0.0)
        gross_loss = -sum(value for value in values if value < 0.0)
        result.append(
            {
                "month": month,
                "trades": len(values),
                "net_pnl_usd": sum(values),
                "win_rate": (
                    sum(value > 0.0 for value in values) / len(values)
                    if values
                    else 0.0
                ),
                "profit_factor": (
                    gross_profit / gross_loss
                    if gross_loss > 0.0
                    else None
                ),
            }
        )
    return result


def metric_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "trades_closed",
        "net_pnl_usd",
        "profit_factor",
        "win_rate",
        "maximum_lifetime_equity_drawdown_usd",
        "maximum_lifetime_closed_drawdown_usd",
    )
    return {key: float(after[key]) - float(before[key]) for key in keys}


def build() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    base_config = apply_runtime_risk_mode(
        load_json(resolve_input(contract["inputs"]["demo_config"])),
        required_equity_scaling=True,
    )
    candidates, population = load_candidates(contract, base_config)
    cache = prepare_quote_cache(contract, candidates, population)
    quotes = load_quote_cache(cache)

    protected_contract = deepcopy(contract)
    protected_contract["inputs"]["portfolio_protection_overlay"] = str(
        OVERLAY_PATH.relative_to(REPO_ROOT).as_posix()
    )
    protected_config = apply_portfolio_protection(
        protected_contract, deepcopy(base_config)
    )

    before_all, before_events = scenario(contract, base_config, candidates, quotes)
    after_all, after_events = scenario(
        protected_contract, protected_config, candidates, quotes
    )

    start_ms = timestamp_ms(RECENT_START)
    end_ms = timestamp_ms(RECENT_END)
    recent_candidates = [
        row for row in candidates if start_ms <= row.entry_ms < end_ms
    ]
    recent_contract = deepcopy(contract)
    recent_contract["evaluation"]["entry_start_utc"] = RECENT_START
    recent_contract["evaluation"]["entry_end_exclusive_utc"] = RECENT_END
    protected_recent_contract = deepcopy(protected_contract)
    protected_recent_contract["evaluation"]["entry_start_utc"] = RECENT_START
    protected_recent_contract["evaluation"]["entry_end_exclusive_utc"] = RECENT_END
    before_recent, _ = scenario(
        recent_contract, base_config, recent_candidates, quotes
    )
    after_recent, _ = scenario(
        protected_recent_contract,
        protected_config,
        recent_candidates,
        quotes,
    )

    before_monthly = {row["month"]: row for row in monthly(before_events)}
    after_monthly = {row["month"]: row for row in monthly(after_events)}
    months = []
    for month in before_monthly:
        before = before_monthly[month]
        after = after_monthly[month]
        months.append(
            {
                "month": month,
                "before": before,
                "after": after,
                "pnl_delta_usd": after["net_pnl_usd"] - before["net_pnl_usd"],
            }
        )

    accepted = (
        after_recent["net_pnl_usd"] >= before_recent["net_pnl_usd"]
        and after_recent["profit_factor"] >= before_recent["profit_factor"]
        and after_recent["maximum_lifetime_equity_drawdown_usd"]
        <= before_recent["maximum_lifetime_equity_drawdown_usd"] * 0.85
        and after_all["net_pnl_usd"] >= before_all["net_pnl_usd"] * 0.95
        and after_all["maximum_lifetime_equity_drawdown_usd"]
        <= before_all["maximum_lifetime_equity_drawdown_usd"]
        and after_recent["trades_closed"] >= before_recent["trades_closed"] * 0.90
        and after_all["trades_closed"] >= before_all["trades_closed"] * 0.90
    )
    return {
        "schema_version": "xauusd_v60_drawdown_protection_comparison_v1",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "PASS_FOR_PROSPECTIVE_DEMO_OBSERVATION"
            if accepted
            else "REJECT_OR_REVISE_BEFORE_DEMO"
        ),
        "input_sha256": {
            "contract": sha256_file(CONTRACT_PATH),
            "base_config": sha256_file(
                resolve_input(contract["inputs"]["demo_config"])
            ),
            "protection_overlay": sha256_file(OVERLAY_PATH),
            "runtime_source": sha256_file(ROOT / "run_portfolio.py"),
            "replay_source": sha256_file(REPLAY_ROOT / "src/replay.py"),
        },
        "population": population,
        "policy": protected_config["portfolio_protection"],
        "all_history": {
            "before": before_all,
            "after": after_all,
            "delta": metric_delta(before_all, after_all),
        },
        "latest_six_months": {
            "before": before_recent,
            "after": after_recent,
            "delta": metric_delta(before_recent, after_recent),
            "monthly": months,
        },
        "limitations": [
            "The candidate was developed on exposed history and is not independent validation.",
            "Dukascopy intratrade ticks are not Capital.com historical execution ticks.",
            "The result authorizes only prospective demo observation, never live trading.",
        ],
    }


def write(report: Mapping[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    recent = report["latest_six_months"]
    lines = [
        "# V60 Drawdown Protection V1 Comparison",
        "",
        f"Decision: **{report['decision']}**",
        "",
        "| Month | Before P&L | After P&L | Delta | Before trades | After trades | After win rate | After PF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in recent["monthly"]:
        before = row["before"]
        after = row["after"]
        pf = "n/a" if after["profit_factor"] is None else f"{after['profit_factor']:.2f}"
        lines.append(
            f"| {row['month']} | ${before['net_pnl_usd']:.2f} | "
            f"${after['net_pnl_usd']:.2f} | ${row['pnl_delta_usd']:.2f} | "
            f"{before['trades']} | {after['trades']} | "
            f"{after['win_rate']:.2%} | {pf} |"
        )
    for label, section in (
        ("Latest six months", recent),
        ("All history", report["all_history"]),
    ):
        before = section["before"]
        after = section["after"]
        lines.extend(
            [
                "",
                f"## {label}",
                "",
                f"- Net P&L: ${before['net_pnl_usd']:.2f} -> ${after['net_pnl_usd']:.2f}",
                f"- Profit factor: {before['profit_factor']:.3f} -> {after['profit_factor']:.3f}",
                f"- Win rate: {before['win_rate']:.2%} -> {after['win_rate']:.2%}",
                f"- Equity drawdown: ${before['maximum_lifetime_equity_drawdown_usd']:.2f} -> ${after['maximum_lifetime_equity_drawdown_usd']:.2f}",
                f"- Trades: {before['trades_closed']} -> {after['trades_closed']}",
            ]
        )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build()
    write(report)
    print(json.dumps({
        "decision": report["decision"],
        "output": str(OUTPUT_JSON),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
