from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase2_demo_repair_common import (
    DEFAULT_POLICY,
    DEFAULT_WEAKNESS_JSON,
    bucket_table,
    duplicate_hidden,
    grouped_summaries,
    load_policy,
    metrics_table,
    read_json,
    read_trades,
    select_trade_source,
    summarize,
    utc_now,
    write_json,
    write_markdown,
)


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_DECISION.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_DECISION.md"


@dataclass(frozen=True)
class RepairDecisionOutput:
    status: str
    json_path: Path
    markdown_path: Path
    bucket_count: int


def generate_repair_decision(
    root: Path,
    policy_path: Path | None = None,
    trades_csv: Path | None = None,
    weakness_json: Path | None = None,
    output_json: Path | None = None,
) -> RepairDecisionOutput:
    root = root.resolve()
    policy_path = (policy_path or root / DEFAULT_POLICY).resolve()
    trades_csv = (trades_csv or select_trade_source(root)).resolve()
    weakness_json = (weakness_json or root / DEFAULT_WEAKNESS_JSON).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else root / DEFAULT_OUTPUT_MD

    policy = load_policy(policy_path)
    rows = read_trades(trades_csv)
    dedup_rows = duplicate_hidden(rows)
    buckets = grouped_summaries(dedup_rows, ["candidate", "symbol", "time_bucket"], policy)
    weakness = read_json(weakness_json)
    payload: dict[str, Any] = {
        "status": "REPAIR_DECISION_READY_NO_RUNTIME_CHANGE",
        "generated_at_utc": utc_now(),
        "policy_path": str(policy_path),
        "policy_id": policy.get("policy_id", "UNKNOWN"),
        "trade_source": str(trades_csv),
        "weakness_shadow_source": str(weakness_json),
        "boundary": (
            "Decision report only. No MT5 charts, EA inputs, presets, orders, positions, "
            "or canonical Phase 2 status are changed."
        ),
        "canonical_phase2_authorized": bool(policy.get("canonical_phase2_authorized")),
        "live_trading_authorized": bool(policy.get("live_trading_authorized")),
        "raw_summary": summarize(rows),
        "duplicate_hidden_summary": summarize(dedup_rows),
        "shadow_combined_keep_summary": weakness.get("weakness_shadow", {}).get("combined_keep_summary", {}),
        "shadow_combined_block_summary": weakness.get("weakness_shadow", {}).get("combined_block_summary", {}),
        "bucket_decisions": buckets,
        "class_counts": class_counts(buckets),
        "policy": policy,
    }
    write_json(output_json, payload)
    write_markdown(output_md, render_markdown(payload))
    return RepairDecisionOutput(str(payload["status"]), output_json, output_md, len(buckets))


def class_counts(buckets: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for bucket in buckets:
        key = str(bucket.get("classification", "UNKNOWN"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def render_markdown(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Decision",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Trade source: `{payload['trade_source']}`",
        f"Weakness shadow source: `{payload['weakness_shadow_source']}`",
        f"Canonical Phase 2 authorized: `{str(payload['canonical_phase2_authorized']).lower()}`",
        f"Live trading authorized: `{str(payload['live_trading_authorized']).lower()}`",
        "",
        "## Summary",
        "",
        metrics_table(
            [
                ("Raw broker view", payload["raw_summary"]),
                ("Duplicate-hidden decision view", payload["duplicate_hidden_summary"]),
            ]
        ),
        "",
        "## Shadow Policy Reference",
        "",
        metrics_table(
            [
                ("Combined shadow would keep", payload["shadow_combined_keep_summary"] or empty_summary()),
                ("Combined shadow would block", payload["shadow_combined_block_summary"] or empty_summary()),
            ]
        ),
        "",
        "## Class Counts",
        "",
        "| Class | Buckets |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in payload["class_counts"].items())
    lines.extend(["", "## Candidate / Symbol / Time Decisions", "", bucket_table(payload["bucket_decisions"]), ""])
    lines.extend(
        [
            "## Operational Decision",
            "",
            "- Prepare controlled demo-only quarantine for suspended weak variants.",
            "- Do not enforce XAUUSD morning/afternoon filtering until a fresh forward week confirms the shadow result.",
            "- Do not treat this report as canonical Phase 2 approval.",
            "- Do not close open positions automatically.",
            "",
        ]
    )
    return lines


def empty_summary() -> dict[str, Any]:
    return {
        "actual_trades": 0,
        "closed_trades": 0,
        "open_trades": 0,
        "wins": 0,
        "losses": 0,
        "closed_win_rate_pct": None,
        "closed_pnl_aed": 0.0,
        "floating_pnl_aed": 0.0,
        "total_pnl_aed": 0.0,
        "profit_factor": None,
        "avg_win_aed": None,
        "avg_loss_aed": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 demo repair decision report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--weakness-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_repair_decision(args.root, args.policy, args.trades_csv, args.weakness_json, args.output_json)
    print(f"Phase 2 demo repair decision: {output.status}")
    print(output.markdown_path)
    print(output.json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
