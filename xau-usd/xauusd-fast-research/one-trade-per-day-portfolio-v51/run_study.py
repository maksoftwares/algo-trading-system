from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from research import (  # noqa: E402
    apply_v50_core_policy,
    canonical_hash,
    evaluate_gates,
    fit_and_score,
    overlap_metrics,
    prepare_actions,
    sha256_file,
    standardize_addon,
    standardize_core,
    verify_sources,
    window_metrics,
    select_addon,
)


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
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def verify_v50(v50_path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(v50_path.read_text(encoding="utf-8"))
    if result["decision"] != policy["required_v50_decision"]:
        raise ValueError("V50 decision is not the required risk-gate pass")
    if result["result_sha256"] != policy["required_v50_result_sha256"]:
        raise ValueError("V50 result self-hash is not the frozen value")
    if canonical_hash(result, "result_sha256") != result["result_sha256"]:
        raise ValueError("V50 result self-hash verification failed")
    return {
        "decision": result["decision"],
        "result_sha256": result["result_sha256"],
        "one_year_comparison": result["one_year_comparison"]["V50_SINGLE_POSITION"],
        "exact_stress_drawdown_dollars": result[
            "independent_dukascopy_single_position"
        ]["stress_exact_tick"]["maximum_drawdown_dollars"],
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# XAUUSD One-Trade-Per-Day Portfolio V51 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Research only. V50 Core is unchanged; no prediction, EA, demo/live, or broker action is authorized.",
        "",
        "## Chronological results",
        "",
        "| Window | Lane | Trades | Trades/day | Net USD | PF | Closed DD USD | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for stage in result["stages"]:
        gate_text = (
            "DEVELOPMENT"
            if stage["gate_pass"] is None
            else ("PASS" if stage["gate_pass"] else "FAIL")
        )
        for lane in ("core", "addon", "combined"):
            row = stage[lane]
            pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.3f}"
            lines.append(
                f"| {stage['stage']} | {lane.upper()} | {row['trades']} | "
                f"{row['trades_per_weekday']:.3f} | {row['net_pnl_dollars']:.2f} | "
                f"{pf} | {row['closed_drawdown_dollars']:.2f} | {gate_text if lane == 'combined' else ''} |"
            )
    lines.extend(["", "## Gate failures", ""])
    failures = result["failed_checks"]
    if failures:
        for stage, checks in failures.items():
            lines.append(f"- `{stage}`: {', '.join(checks)}")
    else:
        lines.append("No locked gate failed.")
    lines.extend(
        [
            "",
            "## Risk interpretation",
            "",
            f"Maximum observed combined closed drawdown was USD {result['maximum_combined_closed_drawdown_dollars']:.2f}; "
            f"after the 25% buffer it is USD {result['maximum_buffered_combined_closed_drawdown_dollars']:.2f}.",
            "Whole-account floating equity drawdown remains unproven because every historical Core specialist lacks intratrade marks. Execution therefore remains fail-closed.",
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "one_trade_per_day_portfolio_v51.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("V51 contract must be locked before evaluation")

    source_audit = verify_sources(REPO, config["sources"])
    v50 = verify_v50(
        REPO / config["sources"]["v50_result"]["path"],
        config["v50_core_policy"],
    )
    actions = prepare_actions(
        REPO / config["sources"]["expansion_action_ledger"]["path"],
        config["addon_policy"],
    )
    core_source = pd.read_parquet(
        REPO / config["sources"]["normalized_core_ledger"]["path"]
    )
    core = apply_v50_core_policy(core_source, config["v50_core_policy"])
    account = {
        **config["account_reference"],
        "maximum_addon_risk_usd": config["addon_policy"][
            "maximum_risk_usd_at_0p01_lot"
        ],
    }

    stages: list[dict[str, Any]] = []
    ledgers: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    failed_checks: dict[str, list[str]] = {}
    for stage_name, bounds in config["windows"].items():
        start, end = map(pd.Timestamp, bounds)
        scored, model = fit_and_score(actions, start, config["model"])
        addon_raw = select_addon(scored, start, end, config["addon_policy"])
        addon = standardize_addon(addon_raw)
        core_window = standardize_core(core, start, end)
        combined = pd.concat([core_window, addon], ignore_index=True).sort_values(
            ["entry_time", "trade_id"], kind="mergesort"
        )
        top_removed = (
            int(config["gates"][stage_name]["top_winners_removed"])
            if stage_name in config["gates"]
            else 10
        )
        core_metrics = window_metrics(core_window, start, end, top_removed)
        addon_metrics = window_metrics(addon, start, end, top_removed)
        combined_metrics = window_metrics(combined, start, end, top_removed)
        overlap = overlap_metrics(combined)
        gate_pass: bool | None = None
        checks: dict[str, bool] = {}
        if stage_name in config["gates"]:
            gate_pass, checks = evaluate_gates(
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
            "model": model,
            "core": core_metrics,
            "addon": addon_metrics,
            "combined": combined_metrics,
            "overlap": overlap,
            "gate_pass": gate_pass,
            "checks": checks,
        }
        stages.append(stage)
        for lane, values in (
            ("CORE", core_metrics),
            ("ADDON", addon_metrics),
            ("COMBINED", combined_metrics),
        ):
            metric_rows.append(
                {
                    "stage": stage_name,
                    "lane": lane,
                    "gate_pass": gate_pass if lane == "COMBINED" else "",
                    **values,
                }
            )
        combined.insert(0, "stage", stage_name)
        ledgers.append(combined)

    acceptance = [stage for stage in stages if stage["stage"] != "development"]
    all_pass = bool(acceptance) and all(stage["gate_pass"] for stage in acceptance)
    decision = (
        "V51_ONE_TRADE_PER_DAY_HISTORICAL_GATE_PASS"
        if all_pass
        else "V51_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL"
    )
    maximum_dd = max(stage["combined"]["closed_drawdown_dollars"] for stage in stages)
    buffer = float(config["account_reference"]["capital_safety_buffer_multiple"])
    interpretation = (
        "The fixed add-on raised the unchanged Core above one completed trade per weekday in every later window while passing all stressed expectancy, stability, and closed-drawdown gates. The historical milestone is achieved, but shared-account floating drawdown and prospective evidence are still required before execution."
        if all_pass
        else "The fixed add-on did not satisfy every locked later-period frequency, expectancy, stability, and drawdown gate. V51 is terminal and must not be repaired after opening these outcomes; V50 remains the protected Core."
    )
    result: dict[str, Any] = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "contract_sha256": json.loads(lock_path.read_text(encoding="utf-8"))[
            "contract_sha256"
        ],
        "source_audit": source_audit,
        "v50_core_verification": v50,
        "policy": {
            "model": config["model"],
            "addon": config["addon_policy"],
            "core": config["v50_core_policy"],
        },
        "stages": stages,
        "failed_checks": failed_checks,
        "maximum_combined_closed_drawdown_dollars": maximum_dd,
        "maximum_buffered_combined_closed_drawdown_dollars": maximum_dd * buffer,
        "historical_milestone_achieved": all_pass,
        "interpretation": interpretation,
        "limitations": {
            "claims_pristine_holdout": False,
            "whole_account_floating_drawdown_proven": False,
            "prospective_shared_account_evidence_required": True,
            "execution_authorized": False,
        },
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = canonical_hash(result, "result_sha256")

    output.mkdir(parents=True, exist_ok=True)
    trades_path = output / config["outputs"]["selected_trades"]
    windows_path = output / config["outputs"]["window_metrics"]
    result_path = output / config["outputs"]["result_json"]
    report_path = output / config["outputs"]["result_markdown"]
    pd.concat(ledgers, ignore_index=True).to_parquet(trades_path, index=False)
    pd.DataFrame(metric_rows).to_csv(windows_path, index=False, lineterminator="\n")
    write_json(result_path, result)
    report_path.write_text(render_report(result), encoding="utf-8")
    manifest = {
        "schema_version": config["schema_version"],
        "contract_sha256": result["contract_sha256"],
        "result_sha256": result["result_sha256"],
        "files": {
            path.name: {"bytes": int(path.stat().st_size), "sha256": sha256_file(path)}
            for path in (trades_path, windows_path, result_path, report_path)
        },
    }
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps({"decision": decision, "result_sha256": result["result_sha256"]}))
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
