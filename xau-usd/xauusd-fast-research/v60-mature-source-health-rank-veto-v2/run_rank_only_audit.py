from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


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


def load_evaluator():
    spec = importlib.util.spec_from_file_location("v60_v2_rank_only_audit", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load evaluator: {EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    evaluator = load_evaluator()
    config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    config["schema_version"] += "_posthoc_rank_only_audit"
    config["report_title"] = "V60 Mature Bottom-Decile Rank-Only Post-Hoc Audit"
    config["policy"].update(
        {
            "state_condition": "CONSECUTIVE_LOSSES",
            "minimum_consecutive_losses": 0,
        }
    )
    with tempfile.TemporaryDirectory(prefix="v60-rank-only-audit-") as temporary:
        path = Path(temporary) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        result, annual, vetoes = evaluator.run(path)

    payload = {
        "schema_version": "v60_mature_bottom_decile_rank_only_posthoc_audit_v1",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "post_hoc_after_exposed_broker_outcomes": True,
        "deployment_authorized": False,
        "decision": result["decision"],
        "policy": result["policy"],
        "baseline": result["baseline"],
        "challenger": result["challenger"],
        "delta": result["delta"],
        "windows": result["windows"],
        "annual": result["annual"],
        "veto_count": len(result["veto_audit"]),
        "baseline_executed_veto_count": result["baseline_executed_veto_count"],
        "veto_baseline_runtime_profit_factor": result[
            "veto_baseline_runtime_profit_factor"
        ],
        "gates": result["gates"],
        "limitations": [
            "This rule was tested after the July-August 2026 broker outcomes were exposed.",
            "A historical pass cannot authorize deployment.",
            "The audit uses a pre-existing rank threshold and maturity threshold without tuning.",
        ],
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "RANK_ONLY_AUDIT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    annual.to_csv(OUTPUTS / "RANK_ONLY_AUDIT_ANNUAL.csv", index=False)
    vetoes.to_csv(OUTPUTS / "RANK_ONLY_AUDIT_VETOES.csv", index=False)
    base = result["baseline"]
    challenger = result["challenger"]
    delta = result["delta"]
    failed = [name for name, passed in result["gates"].items() if not passed]
    lines = [
        "# Mature Bottom-Decile Rank-Only Post-Hoc Audit",
        "",
        "This diagnostic was prompted by exposed broker outcomes. Deployment is unauthorized.",
        "",
        "| Metric | V60 | Rank-only | Change |",
        "|---|---:|---:|---:|",
        f"| Trades | {base['trades_closed']} | {challenger['trades_closed']} | {delta['trades']:+d} |",
        f"| Net P/L | ${base['net_pnl_usd']:.2f} | ${challenger['net_pnl_usd']:.2f} | ${delta['net_pnl_usd']:+.2f} |",
        f"| Profit factor | {base['profit_factor']:.4f} | {challenger['profit_factor']:.4f} | {delta['profit_factor']:+.4f} |",
        f"| Win rate | {100*base['win_rate']:.2f}% | {100*challenger['win_rate']:.2f}% | {delta['win_rate_percentage_points']:+.2f} pp |",
        f"| Closed DD | ${base['maximum_lifetime_closed_drawdown_usd']:.2f} | ${challenger['maximum_lifetime_closed_drawdown_usd']:.2f} | ${delta['closed_drawdown_usd']:+.2f} |",
        f"| Equity DD | ${base['maximum_lifetime_equity_drawdown_usd']:.2f} | ${challenger['maximum_lifetime_equity_drawdown_usd']:.2f} | ${delta['equity_drawdown_usd']:+.2f} |",
        "",
        f"Vetoes: {len(result['veto_audit'])}; common-path baseline executions: {result['baseline_executed_veto_count']}.",
        f"Failed gates: {', '.join(failed) if failed else 'none'}.",
    ]
    (OUTPUTS / "RANK_ONLY_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": result["decision"], "delta": delta, "failed": failed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
