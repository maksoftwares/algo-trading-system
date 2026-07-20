from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from contract import (  # noqa: E402
    CONFIG_PATH,
    load_config,
    resolve_relative,
    sha256_file,
    verify_contract_lock,
)
from evaluation import core_ledger, evaluate_stage, expansion_ledger  # noqa: E402
from router import (  # noqa: E402
    execute_policy,
    policy_definitions,
    score_actions,
)


STAGES = ("development", "validation", "confirmation", "final")


def ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return "Inf" if value > 0 else "-Inf"
    if hasattr(value, "item"):
        return ready(value.item())
    return value


def flatten(policy: dict[str, Any], stages: dict[str, Any]) -> dict[str, Any]:
    row = dict(policy)
    row["all_stage_pass"] = bool(all(value["gate_pass"] for value in stages.values()))
    for stage, value in stages.items():
        row[f"{stage}_pass"] = value["gate_pass"]
        row[f"{stage}_checks"] = json.dumps(value["checks"], sort_keys=True)
        for group in ("expansion", "core", "combined"):
            for key, item in value[group].items():
                row[f"{stage}_{group}_{key}"] = item
    return row


def rank_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(row["all_stage_pass"]),
        min(float(row[f"{stage}_expansion_pf"]) for stage in STAGES),
        min(float(row[f"{stage}_combined_pf"]) for stage in STAGES),
        min(float(row[f"{stage}_expansion_positive_month_share"]) for stage in STAGES),
        -max(abs(float(row[f"{stage}_combined_frequency"]) - 3.5) for stage in STAGES),
        str(row["policy_id"]),
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Macro-Informed Bidirectional Router V36 Result",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Policies evaluated: **{payload['policies']}**",
        f"All-block survivors: **{payload['survivors']}**",
        f"Selected policy: `{payload['selected_policy_id']}`",
        f"Diagnostic best policy: `{payload['diagnostic_best_policy_id']}`",
        "",
    ]
    best = payload.get("best_policy")
    if best:
        lines.extend(
            [
                "| Stage | Pass | Combined trades/day | Expansion PF | Combined PF | Expansion USD | Combined USD |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for stage in STAGES:
            lines.append(
                f"| {stage} | {'PASS' if best[f'{stage}_pass'] else 'FAIL'} | "
                f"{best[f'{stage}_combined_frequency']:.3f} | "
                f"{best[f'{stage}_expansion_pf']:.3f} | "
                f"{best[f'{stage}_combined_pf']:.3f} | "
                f"{best[f'{stage}_expansion_net_usd']:.2f} | "
                f"{best[f'{stage}_combined_net_usd']:.2f} |"
            )
    lines.extend(
        [
            "",
            "All historical blocks are design-contaminated diagnostic evidence.",
            "No result authorizes execution.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    verify_contract_lock()
    output = ROOT / config["outputs"]["directory"]
    evidence_path = output / config["outputs"]["dataset_evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    dataset_path = output / config["outputs"]["merged_actions"]
    if sha256_file(dataset_path) != evidence["dataset_sha256"]:
        raise ValueError("V36 merged dataset hash mismatch")
    actions = pd.read_parquet(dataset_path)
    actions = actions.loc[~actions["regime"].isin(config["excluded_regimes"])].copy()
    if actions["regime"].eq("UNSAFE_SHOCK").any():
        raise ValueError("Unsafe-shock row survived")
    features = list(evidence["model_features"])
    scored = score_actions(actions, features, config)
    diagnostics = scored.attrs.pop("walkforward_diagnostics")
    scored_path = output / config["outputs"]["scored_events"]
    scored.to_parquet(scored_path, index=False)
    policies = policy_definitions(config)
    core_source = pd.read_parquet(resolve_relative(config["sources"]["core_ledger"]))
    core = core_ledger(core_source, float(config["risk_weights"]["core"]))
    executions: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    for policy in policies:
        selected = execute_policy(scored, policy)
        executions[policy["policy_id"]] = selected
        expansion = expansion_ledger(selected, policy["expansion_risk_weight"])
        stages = {
            stage: evaluate_stage(expansion, core, stage, config)[0] for stage in STAGES
        }
        rows.append(flatten(policy, stages))
    ranked = sorted(rows, key=rank_key, reverse=True)
    survivors = [row for row in ranked if row["all_stage_pass"]]
    selected_id = survivors[0]["policy_id"] if survivors else None
    best = ranked[0] if ranked else None
    best_id = best["policy_id"] if best else None
    decision = (
        "MACRO_ROUTER_V36_HISTORICAL_ROBUST_CANDIDATE_PROSPECTIVE_ONLY"
        if survivors
        else "MACRO_ROUTER_V36_NO_ALL_BLOCK_SURVIVOR"
    )
    best_expansion = (
        expansion_ledger(executions[best_id], float(best["expansion_risk_weight"]))
        if best_id is not None
        else scored.iloc[0:0].copy()
    )
    selected_expansion = (
        expansion_ledger(
            executions[selected_id], float(survivors[0]["expansion_risk_weight"])
        )
        if selected_id is not None
        else scored.iloc[0:0].copy()
    )
    portfolio_parts = []
    if selected_id is not None:
        for stage in STAGES:
            _, ledger = evaluate_stage(selected_expansion, core, stage, config)
            portfolio_parts.append(ledger)
    selected_portfolio = (
        pd.concat(portfolio_parts, ignore_index=True)
        if portfolio_parts
        else core.iloc[0:0].copy()
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "policies": len(policies),
        "survivors": len(survivors),
        "source_action_rows": len(actions),
        "scored_events": int(scored["event_id"].nunique()),
        "selected_policy_id": selected_id,
        "diagnostic_best_policy_id": best_id,
        "best_policy": best,
        "top_survivors": survivors[:20],
        "walkforward_diagnostics": diagnostics,
        "feature_change": {
            "base_feature_count": evidence["base_feature_count"],
            "added_feature_count": evidence["added_feature_count"],
            "added_features": evidence["added_features"],
        },
        "authorization": config["authorization"],
    }
    paths = {
        "attempts": output / config["outputs"]["attempts"],
        "survivors": output / config["outputs"]["survivors"],
        "best_expansion": output / config["outputs"]["best_expansion"],
        "selected_expansion": output / config["outputs"]["selected_expansion"],
        "selected_portfolio": output / config["outputs"]["selected_portfolio"],
        "result": output / config["outputs"]["result_json"],
        "markdown": output / config["outputs"]["result_markdown"],
        "manifest": output / config["outputs"]["manifest"],
    }
    pd.DataFrame(rows).to_csv(paths["attempts"], index=False)
    pd.DataFrame(survivors).to_csv(paths["survivors"], index=False)
    best_expansion.to_parquet(paths["best_expansion"], index=False)
    selected_expansion.to_parquet(paths["selected_expansion"], index=False)
    selected_portfolio.to_parquet(paths["selected_portfolio"], index=False)
    paths["result"].write_text(
        json.dumps(ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths["markdown"].write_text(render(payload), encoding="utf-8")
    manifest = {
        "schema_version": config["schema_version"],
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "contract_lock_sha256": sha256_file(
            output / config["outputs"]["contract_lock"]
        ),
        "dataset_sha256": sha256_file(dataset_path),
        "dataset_evidence_sha256": sha256_file(evidence_path),
        "scored_events_sha256": sha256_file(scored_path),
        **{
            f"{name}_sha256": sha256_file(path)
            for name, path in paths.items()
            if name != "manifest"
        },
    }
    paths["manifest"].write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            ready(
                {
                    "decision": decision,
                    "policies": len(policies),
                    "survivors": len(survivors),
                    "selected_policy_id": selected_id,
                    "diagnostic_best_policy_id": best_id,
                    "best_policy": best,
                }
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
