from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from audit import canonical_sha256, run_audit, sha256_file  # noqa: E402


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            json_ready(payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def report(result: dict[str, Any], windows: pd.DataFrame) -> str:
    cap = result["frozen_cap_audit"]
    sizing = result["account_sizing"]
    exact = result["dukascopy_frozen_policy"]["stress_exact_tick"]
    lines = [
        "# Historical Core Drawdown Control Audit V43",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "This is a retrospective risk audit, not untouched confirmation and not order authority.",
        "",
        "## Finding",
        "",
        "The USD 889.69 closed drawdown was an R1 uptrend exposure-stacking event. "
        "The already-frozen two-position, one-entry-per-day R1 cap reduces the one-year "
        f"closed drawdown to USD {cap['one_year_capped_closed_drawdown_dollars']:.2f} "
        f"({cap['one_year_drawdown_reduction_fraction']:.1%} lower).",
        "",
        "## Frozen Cap Windows",
        "",
        "| Window | Policy | Trades | Trades/day | Net USD | PF | Closed DD USD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in windows.to_dict("records"):
        pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.3f}"
        lines.append(
            f"| {row['window']} | `{row['policy']}` | {row['trades']} | "
            f"{row['trades_per_weekday']:.3f} | {row['net_pnl_dollars']:.2f} | "
            f"{pf} | {row['closed_drawdown_dollars']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Floating Equity",
            "",
            "The independent ten-year Dukascopy replay of the same frozen cap has exact "
            f"stress floating drawdown of USD {exact['maximum_drawdown_dollars']:.2f}. "
            f"That is {sizing['capped_r1_stress_drawdown_fraction']:.2%} of the current "
            f"USD {sizing['current_equity_dollars']:.2f} account, above the 15% ceiling.",
            "",
            f"R1 alone therefore requires at least USD "
            f"{sizing['buffered_minimum_equity_capped_r1_dollars']:.2f} with the frozen "
            "25% capital buffer. At current equity, the buffered maximum lot is "
            f"{sizing['maximum_lot_at_current_equity_with_buffer']:.4f}; Capital's "
            f"minimum is {sizing['broker_minimum_lot']:.2f}.",
            "",
            "Until the full V42 shared-account forward curve supersedes the legacy "
            "evidence, the whole Core conservatively requires USD "
            f"{sizing['buffered_minimum_equity_legacy_core_dollars']:.2f}.",
            "",
            "## Required Action",
            "",
            "- Keep the R1 cap at two concurrent positions and one entry per UTC day.",
            "- Fail closed on the current account; do not attach a 0.01-lot executor.",
            "- Use a larger adequately funded account or a broker with smaller lot sizing.",
            "- Keep V42 collecting exact shared-account evidence before any demo decision.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config/historical_core_drawdown_control_audit_v43.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    artifacts = run_audit(config, REPO_ROOT)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    result = json_ready(artifacts.result)
    result["result_sha256"] = canonical_sha256(result)
    write_json(output / config["outputs"]["result_json"], result)
    artifacts.windows.to_csv(
        output / config["outputs"]["window_metrics"],
        index=False,
        lineterminator="\n",
    )
    artifacts.cap_decisions.to_csv(
        output / config["outputs"]["cap_decisions"],
        index=False,
        lineterminator="\n",
    )
    artifacts.episode_trades.to_csv(
        output / config["outputs"]["episode_trades"],
        index=False,
        lineterminator="\n",
    )
    (output / config["outputs"]["result_markdown"]).write_text(
        report(result, artifacts.windows),
        encoding="utf-8",
        newline="\n",
    )
    generated = {
        name: output / config["outputs"][name]
        for name in (
            "result_json",
            "result_markdown",
            "window_metrics",
            "cap_decisions",
            "episode_trades",
        )
    }
    write_json(
        output / config["outputs"]["manifest"],
        {
            "schema_version": config["schema_version"],
            "config_sha256": sha256_file(config_path),
            "result_sha256": result["result_sha256"],
            "generated_files": {
                name: {
                    "bytes": int(path.stat().st_size),
                    "sha256": sha256_file(path),
                }
                for name, path in generated.items()
            },
        },
    )
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "one_year_original_closed_dd": result["frozen_cap_audit"][
                    "one_year_original_closed_drawdown_dollars"
                ],
                "one_year_capped_closed_dd": result["frozen_cap_audit"][
                    "one_year_capped_closed_drawdown_dollars"
                ],
                "exact_stress_floating_dd": result["dukascopy_frozen_policy"][
                    "stress_exact_tick"
                ]["maximum_drawdown_dollars"],
                "account_readiness": result["account_sizing"][
                    "account_readiness_decision"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
