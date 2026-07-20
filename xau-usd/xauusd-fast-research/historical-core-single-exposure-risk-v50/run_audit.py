from __future__ import annotations

import json
from pathlib import Path

from src.audit import run_audit


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "historical_core_single_exposure_risk_v50.json"


def render_markdown(result: dict, windows) -> str:
    lines = [
        "# Historical Core Single-Exposure Risk Control V50",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "This is retrospective risk governance, not untouched alpha evidence and not order authority.",
        "",
        "## Historical Comparison",
        "",
        "| Window | Policy | Trades | Trades/day | Net USD | PF | Closed DD USD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in windows.itertuples(index=False):
        pf = "n/a" if row.profit_factor is None else f"{row.profit_factor:.3f}"
        lines.append(
            f"| {row.window} | `{row.policy}` | {row.trades} | "
            f"{row.trades_per_weekday:.3f} | {row.net_pnl_dollars:.2f} | "
            f"{pf} | {row.closed_drawdown_dollars:.2f} |"
        )
    sizing = result["account_sizing"]
    exact = result["independent_dukascopy_single_position"]["stress_exact_tick"]
    lines.extend(
        [
            "",
            "## Exact Floating Drawdown",
            "",
            f"The ten-year one-position R1 replay has exact stress floating drawdown of USD {exact['maximum_drawdown_dollars']:.2f}.",
            f"That is {sizing['unbuffered_drawdown_fraction']:.2%} of USD {sizing['current_equity_dollars']:.2f}, or {sizing['buffered_drawdown_fraction']:.2%} after the frozen 25% capital buffer.",
            f"The buffered minimum equity is USD {sizing['buffered_minimum_equity_dollars']:.2f}; the reference account has USD {sizing['capital_reserve_above_buffered_minimum_dollars']:.2f} above that minimum.",
            "",
            "## Locked Control",
            "",
            "- Maximum one open R1 box position.",
            "- Maximum one new R1 box entry per UTC day.",
            "- Reject a second R1 box entry while the first remains open.",
            "- Keep the 15% account ceiling and 25% capital buffer.",
            "- Keep execution fail-closed until whole-account forward evidence passes.",
            "",
            "The R1 lane now fits its risk gate. Whole-Core floating drawdown remains unproven because the historical ledger lacks intratrade marks for every specialist.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    artifacts = run_audit(config, REPO_ROOT)
    outputs = ROOT / config["outputs"]["directory"]
    outputs.mkdir(parents=True, exist_ok=True)
    result_path = outputs / config["outputs"]["result_json"]
    result_path.write_text(
        json.dumps(artifacts.result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    artifacts.windows.to_csv(outputs / config["outputs"]["window_metrics"], index=False)
    artifacts.decisions.to_csv(outputs / config["outputs"]["decisions"], index=False)
    (outputs / config["outputs"]["result_markdown"]).write_text(
        render_markdown(artifacts.result, artifacts.windows), encoding="utf-8"
    )
    manifest = {
        "schema_version": config["schema_version"],
        "result_sha256": artifacts.result["result_sha256"],
        "decision": artifacts.result["decision"],
        "source_audit": artifacts.result["source_audit"],
        "external_source_audit": artifacts.result["external_source_audit"],
    }
    (outputs / config["outputs"]["manifest"]).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(artifacts.result["decision"])
    print(f"result_sha256={artifacts.result['result_sha256']}")


if __name__ == "__main__":
    main()
