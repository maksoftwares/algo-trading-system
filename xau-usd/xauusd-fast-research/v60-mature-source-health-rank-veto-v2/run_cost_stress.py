from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
BASE_CONFIG = ROOT / "config" / "challenger.json"
EVALUATOR = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-v57-degraded-rank-veto-v1"
    / "src"
    / "evaluate.py"
)
OUTPUTS = ROOT / "outputs"
COST_LEVELS_USD = (0.0, 0.10, 0.20, 0.25, 0.50, 1.00)
COMPARATIVE_GATE_NAMES = (
    "net_not_below_baseline",
    "profit_factor_not_below_baseline",
    "closed_drawdown_not_above_baseline",
    "equity_drawdown_not_above_baseline",
    "trade_retention",
    "frequency_retention",
    "no_negative_calendar_year_delta",
    "recent_windows_not_worse",
    "veto_cohort_large_enough",
    "veto_cohort_profit_factor_below_one",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def comparative_gates_pass(gates: dict[str, bool]) -> bool:
    return all(bool(gates[name]) for name in COMPARATIVE_GATE_NAMES)


def candidate_cost_summary(config: dict) -> dict[str, float | int]:
    replay_item = config["inputs"]["replay_source"]
    replay = load_module("v60_v2_cost_stress_replay", REPO_ROOT / replay_item["path"])
    contract = replay.load_json(REPO_ROOT / config["inputs"]["replay_contract"]["path"])
    deployed = replay.load_json(REPO_ROOT / config["inputs"]["deployed_config"]["path"])
    deployed = replay.apply_portfolio_protection(contract, deployed)
    deployed = replay.apply_runtime_risk_mode(
        deployed,
        bool(
            contract["evaluation"].get(
                "required_equity_fraction_limits_enabled", False
            )
        ),
    )
    candidates, _ = replay.load_candidates(contract, deployed)
    values = np.asarray([candidate.open_cost_usd for candidate in candidates], dtype=float)
    return {
        "candidate_rows": int(len(values)),
        "mean_existing_open_cost_usd": float(values.mean()),
        "median_existing_open_cost_usd": float(np.median(values)),
    }


def main() -> int:
    evaluator = load_module("v60_v2_cost_stress_evaluator", EVALUATOR)
    config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    config["inputs"]["shared_evaluator"]["sha256"] = sha256_file(EVALUATOR)
    cost_summary = candidate_cost_summary(config)
    rows: list[dict] = []
    details: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="v60-v2-cost-stress-") as temporary:
        config_path = Path(temporary) / "challenger.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        for additional_cost in COST_LEVELS_USD:
            result, annual, _ = evaluator.run(
                config_path,
                additional_cost_usd_per_trade=additional_cost,
            )
            base = result["baseline"]
            challenger = result["challenger"]
            delta = result["delta"]
            row = {
                "additional_cost_usd_per_trade": additional_cost,
                "additional_cost_vs_mean_existing_open_cost": (
                    additional_cost / cost_summary["mean_existing_open_cost_usd"]
                ),
                "baseline_trades": base["trades_closed"],
                "challenger_trades": challenger["trades_closed"],
                "baseline_net_pnl_usd": base["net_pnl_usd"],
                "challenger_net_pnl_usd": challenger["net_pnl_usd"],
                "delta_net_pnl_usd": delta["net_pnl_usd"],
                "baseline_profit_factor": base["profit_factor"],
                "challenger_profit_factor": challenger["profit_factor"],
                "baseline_closed_drawdown_usd": base[
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "challenger_closed_drawdown_usd": challenger[
                    "maximum_lifetime_closed_drawdown_usd"
                ],
                "baseline_equity_drawdown_usd": base[
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "challenger_equity_drawdown_usd": challenger[
                    "maximum_lifetime_equity_drawdown_usd"
                ],
                "veto_decisions": len(result["veto_audit"]),
                "baseline_executed_vetoes": result[
                    "baseline_executed_veto_count"
                ],
                "veto_baseline_runtime_profit_factor": result[
                    "veto_baseline_runtime_profit_factor"
                ],
                "minimum_annual_delta_pnl_usd": float(
                    annual["delta_pnl_usd"].min()
                ),
                "comparative_gates_pass": comparative_gates_pass(result["gates"]),
            }
            rows.append(row)
            details[f"additional_cost_{additional_cost:.2f}"] = result
            print(json.dumps(row, sort_keys=True), flush=True)

    frame = pd.DataFrame(rows)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUTS / "COST_STRESS.csv", index=False)
    payload = {
        "schema_version": "v60_mature_source_health_rank_veto_v2_cost_stress",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "authorization": {
            "runtime_changes": False,
            "demo_deployment": False,
            "live_deployment": False,
        },
        "method": (
            "Each candidate receives the same additional dollar cost. Normal source-exit "
            "PnL is reduced once; open-position cost is increased once so all path-dependent "
            "equity, guardian, and profit-protection decisions are replayed under stress."
        ),
        "benchmark_identity_note": (
            "Frozen unstressed identity gates are intentionally excluded from stressed-run "
            "comparative pass/fail because stressed V60 is no longer the frozen dollar identity."
        ),
        "candidate_cost_summary": cost_summary,
        "comparative_gate_names": list(COMPARATIVE_GATE_NAMES),
        "rows": rows,
        "details": details,
    }
    (OUTPUTS / "COST_STRESS.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# V60 Mature Source-Health V2 Cost Stress",
        "",
        "Diagnostic only. The nominated V2 policy is unchanged and deployment remains unauthorized.",
        "",
        (
            f"The exact replay population has {cost_summary['candidate_rows']} candidates. "
            f"Existing modeled open cost averages ${cost_summary['mean_existing_open_cost_usd']:.3f} "
            f"and has a ${cost_summary['median_existing_open_cost_usd']:.3f} median."
        ),
        "",
        "| Added cost/trade | vs existing mean | V60 net | V2 net | Delta | V60 PF | V2 PF | V60 closed DD | V2 closed DD | V60 equity DD | V2 equity DD | Vetoes (common path) | Min annual delta | Comparative gates |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| ${row['additional_cost_usd_per_trade']:.2f} | "
            f"{100*row['additional_cost_vs_mean_existing_open_cost']:.0f}% | "
            f"${row['baseline_net_pnl_usd']:.2f} | ${row['challenger_net_pnl_usd']:.2f} | "
            f"${row['delta_net_pnl_usd']:+.2f} | {row['baseline_profit_factor']:.4f} | "
            f"{row['challenger_profit_factor']:.4f} | "
            f"${row['baseline_closed_drawdown_usd']:.2f} | "
            f"${row['challenger_closed_drawdown_usd']:.2f} | "
            f"${row['baseline_equity_drawdown_usd']:.2f} | "
            f"${row['challenger_equity_drawdown_usd']:.2f} | "
            f"{row['veto_decisions']} ({row['baseline_executed_vetoes']}) | "
            f"${row['minimum_annual_delta_pnl_usd']:+.2f} | "
            f"{'PASS' if row['comparative_gates_pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "The added cost is charged to both V60 and V2. Because the replay is rerun from ticks, "
            "the surcharge can change health state, veto decisions, drawdown controls, and exit paths.",
        ]
    )
    (OUTPUTS / "COST_STRESS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
