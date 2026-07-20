from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from replication import (  # noqa: E402
    direction_metrics,
    execute_rule,
    marginal_independence,
    metrics,
    month_cluster_bootstrap_lower_bound,
    select_rule,
    sha256_file,
    verify_parquet,
)


def ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Inf" if value > 0 else "-Inf"
    if hasattr(value, "item"):
        return ready(value.item())
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def render(payload: dict[str, Any], table: pd.DataFrame) -> str:
    lines = [
        "# Pullback Swing Replication V7 Result",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        "| Window | Trades | Trades/day | Net USD | PF | DD USD | Top 5 removed | Positive months |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in table.itertuples(index=False):
        lines.append(
            f"| {row.window} | {row.trades} | {row.trades_per_weekday:.3f} | "
            f"{row.net_usd:.2f} | {row.profit_factor:.3f} | "
            f"{row.closed_drawdown_usd:.2f} | {row.top_winners_removed_net_usd:.2f} | "
            f"{row.positive_month_share:.1%} |"
        )
    replication = payload["replication"]
    lines.extend(
        [
            "",
            "## Replication gates",
            "",
            *[f"- {key}: **{'PASS' if value else 'FAIL'}**" for key, value in replication["checks"].items()],
            "",
            f"Month-cluster bootstrap 95% lower mean: **${replication['bootstrap_lower_average_usd']:.3f}/trade**.",
            "",
            "This is historical reverse-time replication only. It does not authorize",
            "model serving, EA consumption, demo trading, live trading, or broker action.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "pullback_swing_replication_v7.json").read_text(
            encoding="utf-8"
        )
    )
    sources = config["sources"]
    action_path = (ROOT / sources["action_ledger"]).resolve()
    core_path = (ROOT / sources["core_ledger"]).resolve()
    actions = verify_parquet(
        action_path, sources["action_sha256"], int(sources["action_expected_rows"])
    )
    core = verify_parquet(
        core_path, sources["core_sha256"], int(sources["core_expected_rows"])
    )
    core["entry_time_utc"] = pd.to_datetime(core["entry_time_utc"], utc=True)
    selected = select_rule(actions, config["rule"])
    trades = execute_rule(selected, config["rule"])
    gate = config["replication_gates"]
    rows: list[dict[str, Any]] = []
    independence: dict[str, Any] = {}
    for window, bounds in config["windows"].items():
        start, end = map(pd.Timestamp, bounds)
        value = metrics(trades, start, end, int(gate["top_winners_removed"]))
        rows.append({"window": window, **value})
        independence[window] = marginal_independence(
            trades,
            core,
            start,
            end,
            int(config["independence"]["core_entry_separation_minutes"]),
        )
    table = pd.DataFrame(rows)
    reverse_start, reverse_end = map(
        pd.Timestamp, config["windows"]["REVERSE_REPLICATION"]
    )
    reverse = next(row for row in rows if row["window"] == "REVERSE_REPLICATION")
    directions = direction_metrics(trades, reverse_start, reverse_end)
    lower = month_cluster_bootstrap_lower_bound(
        trades,
        reverse_start,
        reverse_end,
        int(gate["bootstrap_resamples"]),
        int(gate["bootstrap_seed"]),
        float(gate["bootstrap_lower_quantile"]),
    )
    checks = {
        "minimum_trades": reverse["trades"] >= int(gate["minimum_trades"]),
        "minimum_frequency": reverse["trades_per_weekday"]
        >= float(gate["minimum_frequency"]),
        "minimum_profit_factor": reverse["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "positive_average_usd": reverse["average_usd"] > 0.0,
        "positive_net_usd": reverse["net_usd"] > 0.0,
        "maximum_closed_drawdown": reverse["closed_drawdown_usd"]
        <= float(gate["maximum_closed_drawdown_usd"]),
        "top_winners_removed_positive": reverse["top_winners_removed_net_usd"] > 0.0,
        "minimum_positive_month_share": reverse["positive_month_share"]
        >= float(gate["minimum_positive_month_share"]),
        "long_direction": directions["LONG"]["trades"]
        >= int(gate["minimum_direction_trades"])
        and directions["LONG"]["net_usd"] > 0.0,
        "short_direction": directions["SHORT"]["trades"]
        >= int(gate["minimum_direction_trades"])
        and directions["SHORT"]["net_usd"] > 0.0,
        "bootstrap_lower_average_positive": lower > 0.0,
    }
    passed = bool(all(checks.values()))
    payload = {
        "schema_version": config["schema_version"],
        "decision": (
            "V7_REVERSE_REPLICATION_PASS_REQUIRES_MT5_PARITY_AND_FORWARD_SHADOW"
            if passed
            else "V7_REJECTED"
        ),
        "source": {
            "action_path": action_path.as_posix(),
            "action_sha256": sources["action_sha256"],
            "core_path": core_path.as_posix(),
            "core_sha256": sources["core_sha256"],
        },
        "candidate_rows_before_execution": int(len(selected)),
        "executed_rows": int(len(trades)),
        "rule": config["rule"],
        "replication": {
            "metrics": reverse,
            "directions": directions,
            "bootstrap_lower_average_usd": lower,
            "checks": checks,
            "gate_pass": passed,
        },
        "marginal_independence": independence,
        "authorization": config["authorization"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    trades.to_parquet(output / config["outputs"]["trades"], index=False)
    table.to_csv(output / config["outputs"]["metrics"], index=False)
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render(payload, table), encoding="utf-8"
    )
    artifacts = [
        config["outputs"]["trades"],
        config["outputs"]["metrics"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    manifest = {
        "schema_version": config["schema_version"],
        "files": {
            name: {
                "sha256": sha256_file(output / name),
                "bytes": (output / name).stat().st_size,
            }
            for name in artifacts
        },
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps(ready(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
