from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

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


def load_evaluator():
    spec = importlib.util.spec_from_file_location("mature_health_sensitivity", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load evaluator: {EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def variants() -> list[tuple[str, dict]]:
    return [
        ("NOMINATED", {}),
        ("MATURITY_40", {"minimum_prior_source_closed_trades": 40}),
        ("MATURITY_60", {"minimum_prior_source_closed_trades": 60}),
        ("LOOKBACK_30", {"lookback_closed_trades": 30}),
        ("HEALTH_080", {"maximum_prior_profit_factor_exclusive": 0.8}),
        ("HEALTH_120", {"maximum_prior_profit_factor_exclusive": 1.2}),
        ("RANK_005", {"maximum_causal_rank_exclusive": 0.05}),
        ("RANK_015", {"maximum_causal_rank_exclusive": 0.15}),
    ]


def main() -> int:
    evaluator = load_evaluator()
    base_config = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    rows = []
    detail = {}
    for name, changes in variants():
        config = json.loads(json.dumps(base_config))
        config["schema_version"] += "_sensitivity_" + name.lower()
        config["report_title"] += f" Sensitivity {name}"
        config["policy"].update(changes)
        with tempfile.TemporaryDirectory(prefix="v60-v2-sensitivity-") as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            result, annual, _ = evaluator.run(path)
        base = result["baseline"]
        challenger = result["challenger"]
        delta = result["delta"]
        robust = bool(
            delta["net_pnl_usd"] > 0.0
            and delta["profit_factor"] >= 0.0
            and delta["closed_drawdown_usd"] <= 1e-6
            and delta["equity_drawdown_usd"] <= 1e-6
            and annual["delta_pnl_usd"].ge(-1e-6).all()
        )
        rows.append(
            {
                "variant": name,
                "vetoes": len(result["veto_audit"]),
                "trades": challenger["trades_closed"],
                "net_pnl_usd": challenger["net_pnl_usd"],
                "delta_net_pnl_usd": delta["net_pnl_usd"],
                "profit_factor": challenger["profit_factor"],
                "closed_drawdown_usd": challenger["maximum_lifetime_closed_drawdown_usd"],
                "equity_drawdown_usd": challenger["maximum_lifetime_equity_drawdown_usd"],
                "minimum_annual_delta_pnl_usd": float(annual["delta_pnl_usd"].min()),
                "all_original_gates_pass": bool(all(result["gates"].values())),
                "core_direction_robust": robust,
            }
        )
        detail[name] = result
        print(json.dumps(rows[-1], sort_keys=True), flush=True)
    frame = pd.DataFrame(rows)
    outputs = ROOT / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    frame.to_csv(outputs / "SENSITIVITY.csv", index=False)
    payload = {
        "schema_version": "v60_mature_source_health_rank_veto_v2_sensitivity",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "nominated_policy_unchanged": True,
        "rows": rows,
        "details": detail,
    }
    (outputs / "SENSITIVITY.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# V60 Mature Source-Health V2 Sensitivity",
        "",
        "Diagnostics only. The nominated policy is unchanged.",
        "",
        "| Variant | Vetoes | Net | Delta | PF | Closed DD | Equity DD | Min annual delta | Original gates | Core robust |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['vetoes']} | ${row['net_pnl_usd']:.2f} | "
            f"${row['delta_net_pnl_usd']:+.2f} | {row['profit_factor']:.4f} | "
            f"${row['closed_drawdown_usd']:.2f} | ${row['equity_drawdown_usd']:.2f} | "
            f"${row['minimum_annual_delta_pnl_usd']:+.2f} | "
            f"{'PASS' if row['all_original_gates_pass'] else 'FAIL'} | "
            f"{'PASS' if row['core_direction_robust'] else 'FAIL'} |"
        )
    (outputs / "SENSITIVITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
