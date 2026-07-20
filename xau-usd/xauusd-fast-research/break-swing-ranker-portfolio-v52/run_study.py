from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V51_SRC = REPO / "xau-usd/xauusd-fast-research/one-trade-per-day-portfolio-v51/src"
sys.path.insert(0, str(V51_SRC))
sys.path.insert(0, str(ROOT / "src"))

import research as base  # noqa: E402
from ranker import prepare_candidates, quarterly_scores, select_ranked, standardize  # noqa: E402


def ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return ready(value.item())
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(ready(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def verify_v50(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result["decision"] != policy["required_v50_decision"]:
        raise ValueError("Frozen V50 decision mismatch")
    if result["result_sha256"] != policy["required_v50_result_sha256"]:
        raise ValueError("Frozen V50 result hash mismatch")
    if base.canonical_hash(result, "result_sha256") != result["result_sha256"]:
        raise ValueError("V50 self-hash mismatch")
    return {
        "decision": result["decision"],
        "result_sha256": result["result_sha256"],
    }


def render(result: dict[str, Any]) -> str:
    lines = [
        "# XAUUSD Break-Swing Ranker Portfolio V52 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Research only. V50 Core is unchanged and execution remains unauthorized.",
        "",
        "| Window | Lane | Trades | Trades/day | Net USD | PF | Closed DD USD | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for stage in result["stages"]:
        for lane in ("core", "addon", "combined"):
            row = stage[lane]
            pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.3f}"
            gate = (
                ""
                if lane != "combined"
                else (
                    "DEVELOPMENT"
                    if stage["gate_pass"] is None
                    else ("PASS" if stage["gate_pass"] else "FAIL")
                )
            )
            lines.append(
                f"| {stage['stage']} | {lane.upper()} | {row['trades']} | "
                f"{row['trades_per_weekday']:.3f} | {row['net_pnl_dollars']:.2f} | "
                f"{pf} | {row['closed_drawdown_dollars']:.2f} | {gate} |"
            )
    lines.extend(["", "## Failures", ""])
    if result["failed_checks"]:
        for stage, failures in result["failed_checks"].items():
            lines.append(f"- `{stage}`: {', '.join(failures)}")
    else:
        lines.append("No locked gate failed.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
            "Whole-account floating drawdown remains unproven. No Python serving, EA, demo/live, or broker authority is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config/break_swing_ranker_portfolio_v52.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("V52 contract must be locked before evaluation")
    source_audit = base.verify_sources(REPO, config["sources"])
    v50 = verify_v50(
        REPO / config["sources"]["v50_result"]["path"], config["v50_core_policy"]
    )
    actions = prepare_candidates(
        REPO / config["sources"]["expansion_action_ledger"]["path"],
        config["addon_policy"],
    )
    core_source = pd.read_parquet(
        REPO / config["sources"]["normalized_core_ledger"]["path"]
    )
    core = base.apply_v50_core_policy(core_source, config["v50_core_policy"])
    account = {
        **config["account_reference"],
        "maximum_addon_risk_usd": config["addon_policy"][
            "maximum_risk_usd_at_0p01_lot"
        ],
    }
    stages: list[dict[str, Any]] = []
    ledgers: list[pd.DataFrame] = []
    rows: list[dict[str, Any]] = []
    failed_checks: dict[str, list[str]] = {}
    for stage_name, bounds in config["windows"].items():
        start, end = map(pd.Timestamp, bounds)
        scored, diagnostics = quarterly_scores(
            actions, start, end, config["model"], config["addon_policy"]
        )
        addon = standardize(select_ranked(scored, config["addon_policy"]))
        core_window = base.standardize_core(core, start, end)
        combined = pd.concat([core_window, addon], ignore_index=True).sort_values(
            ["entry_time", "trade_id"], kind="mergesort"
        )
        removed = (
            int(config["gates"][stage_name]["top_winners_removed"])
            if stage_name in config["gates"]
            else 10
        )
        core_metrics = base.window_metrics(core_window, start, end, removed)
        addon_metrics = base.window_metrics(addon, start, end, removed)
        combined_metrics = base.window_metrics(combined, start, end, removed)
        gate_pass: bool | None = None
        checks: dict[str, bool] = {}
        if stage_name in config["gates"]:
            gate_pass, checks = base.evaluate_gates(
                addon_metrics,
                combined_metrics,
                config["gates"][stage_name],
                account,
            )
            if not gate_pass:
                failed_checks[stage_name] = [
                    name for name, passed in checks.items() if not passed
                ]
        stage = {
            "stage": stage_name,
            "start_utc": start.isoformat(),
            "end_exclusive_utc": end.isoformat(),
            "quarterly_models": diagnostics,
            "core": core_metrics,
            "addon": addon_metrics,
            "combined": combined_metrics,
            "overlap": base.overlap_metrics(combined),
            "gate_pass": gate_pass,
            "checks": checks,
        }
        stages.append(stage)
        for lane, metrics in (
            ("CORE", core_metrics),
            ("ADDON", addon_metrics),
            ("COMBINED", combined_metrics),
        ):
            rows.append({"stage": stage_name, "lane": lane, **metrics})
        combined.insert(0, "stage", stage_name)
        ledgers.append(combined)
    acceptance = [stage for stage in stages if stage["stage"] != "development"]
    passed = bool(acceptance) and all(stage["gate_pass"] for stage in acceptance)
    decision = (
        "V52_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if passed
        else "V52_BREAK_SWING_RANKER_GATE_FAIL_TERMINAL"
    )
    interpretation = (
        "The fixed-action quarterly ranker lifted the unchanged Core above one completed trade per weekday in every later window while passing all marginal expectancy, stability, and buffered closed-drawdown gates. The historical frequency milestone is achieved; prospective shared-account evidence is still required."
        if passed
        else "The fixed-action quarterly ranker failed at least one locked later-period frequency, marginal expectancy, stability, or drawdown gate. V52 is terminal and V50 remains the protected Core."
    )
    result: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "contract_sha256": json.loads(lock_path.read_text(encoding="utf-8"))[
            "contract_sha256"
        ],
        "source_audit": source_audit,
        "v50_core_verification": v50,
        "stages": stages,
        "failed_checks": failed_checks,
        "historical_milestone_achieved": passed,
        "interpretation": interpretation,
        "limitations": {
            "claims_pristine_holdout": False,
            "whole_account_floating_drawdown_proven": False,
            "execution_authorized": False,
        },
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = base.canonical_hash(result, "result_sha256")
    output.mkdir(parents=True, exist_ok=True)
    trades_path = output / config["outputs"]["selected_trades"]
    windows_path = output / config["outputs"]["window_metrics"]
    result_path = output / config["outputs"]["result_json"]
    report_path = output / config["outputs"]["result_markdown"]
    pd.concat(ledgers, ignore_index=True).to_parquet(trades_path, index=False)
    pd.DataFrame(rows).to_csv(windows_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    report_path.write_text(render(result), encoding="utf-8")
    manifest = {
        "schema_version": config["schema_version"],
        "contract_sha256": result["contract_sha256"],
        "result_sha256": result["result_sha256"],
        "files": {
            path.name: {
                "bytes": int(path.stat().st_size),
                "sha256": base.sha256_file(path),
            }
            for path in (trades_path, windows_path, result_path, report_path)
        },
    }
    manifest["manifest_sha256"] = base.canonical_hash(manifest, "manifest_sha256")
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps({"decision": decision, "result_sha256": result["result_sha256"]}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
