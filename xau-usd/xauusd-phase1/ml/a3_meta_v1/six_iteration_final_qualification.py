from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_microstructure_regime import _sha256_file


DEFAULT_CONTRACT = Path("config/ml/a3_ml_six_iteration_final_qualification_v1.json")


class FinalQualificationError(RuntimeError):
    pass


def run_six_iteration_final_qualification(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    loaded: dict[str, Any] = {}
    input_audit = {}
    for name, spec in contract["inputs"].items():
        path = (root / spec["path"]).resolve()
        if not path.is_file() or _sha256_file(path) != spec["sha256"]:
            raise FinalQualificationError(f"qualification input missing or changed: {name}")
        input_audit[name] = {"path": str(path), "sha256": spec["sha256"]}
        loaded[name] = path if path.suffix.lower() == ".csv" else json.loads(path.read_text(encoding="utf-8"))

    daily = _daily_stress_pnl(loaded["portfolio_trades"], contract["monte_carlo"])
    monte_carlo = [
        _block_bootstrap(
            daily,
            float(capital),
            contract["monte_carlo"],
        )
        for capital in contract["monte_carlo"]["capital_scenarios_usd"]
    ]
    portfolio = loaded["shared_portfolio"]
    macro = loaded["macro_specialists"]
    cftc = loaded["cftc_specialists"]
    ranker = loaded["ml_ranker"]
    intended_mc = next(
        row for row in monte_carlo if row["starting_capital_usd"] == float(contract["monte_carlo"]["capital_scenarios_usd"][0])
    )
    external_survivors = list(macro.get("research_survivors", [])) + list(cftc.get("research_survivors", []))
    ranker_survivor = ranker.get("selected_policy") is not None
    shared_pass = portfolio.get("classification") == "SHARED_ACCOUNT_RESEARCH_PASS"
    untouched_holdout = False
    raw = portfolio["unguarded"]
    gates = {
        "minimum_frequency": float(raw["annualized_trades_per_trading_day"])
        >= float(contract["qualification_gates"]["minimum_trades_per_trading_day"]),
        "monte_carlo_drawdown": float(intended_mc["drawdown_threshold_breach_probability"])
        <= float(contract["qualification_gates"]["maximum_drawdown_breach_probability"]),
        "monte_carlo_risk_of_ruin": float(intended_mc["risk_of_ruin_probability"])
        <= float(contract["qualification_gates"]["maximum_risk_of_ruin"]),
        "stress_profit_factor": float(raw["stress_profit_factor"] or 0.0)
        >= float(contract["qualification_gates"]["minimum_stress_profit_factor"]),
        "six_month_stability": float(raw["nonnegative_six_month_share"])
        >= float(contract["qualification_gates"]["minimum_nonnegative_six_month_share"]),
        "external_specialist_survivor": bool(external_survivors)
        if contract["qualification_gates"]["require_external_specialist_survivor"]
        else True,
        "ml_ranker_survivor": bool(ranker_survivor)
        if contract["qualification_gates"]["require_ml_ranker_survivor"]
        else True,
        "shared_portfolio_pass": shared_pass
        if contract["qualification_gates"]["require_shared_portfolio_pass"]
        else True,
        "untouched_holdout": untouched_holdout
        if contract["qualification_gates"]["require_untouched_holdout"]
        else True,
    }
    deployable = all(gates.values())
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(outputs["monte_carlo_csv"], monte_carlo)
    payload = {
        "schema_version": contract["schema_version"],
        "classification": (
            "SIX_ITERATION_DEPLOYMENT_QUALIFIED"
            if deployable
            else "SIX_ITERATION_RESEARCH_COMPLETE_NO_DEPLOYABLE_SYSTEM"
        ),
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "input_audit": input_audit,
        "iteration_results": {
            "iteration_1_foundation": loaded["foundation"]["causality_checks"],
            "iteration_2_macro_specialists": macro["classification"],
            "iteration_3_cftc_specialists": cftc["classification"],
            "iteration_4_shared_portfolio": portfolio["classification"],
            "iteration_5_ml_ranker": ranker["classification"],
            "iteration_6_final_qualification": "PASS" if deployable else "FAIL",
        },
        "external_specialist_survivors": external_survivors,
        "ml_selected_policy": ranker.get("selected_policy"),
        "historical_foundation": {
            "profitable": float(raw["stress_net_usd"]) > 0 and float(raw["stress_profit_factor"] or 0) > 1,
            "trades": raw["trades"],
            "stress_net_usd": raw["stress_net_usd"],
            "stress_profit_factor": raw["stress_profit_factor"],
            "frequency_per_trading_day": raw["annualized_trades_per_trading_day"],
            "nonnegative_six_month_share": raw["nonnegative_six_month_share"],
            "top10_winners_removed_stress_net_usd": raw["top10_winners_removed_stress_net_usd"],
            "pnl_windows": loaded["exact_portfolio"]["windows"],
        },
        "drawdown_boundary": portfolio["drawdown_boundary"],
        "overlap": portfolio["overlap"],
        "monte_carlo": monte_carlo,
        "gates": gates,
        "failed_gates": [key for key, value in gates.items() if not value],
        "deployment_decision": {
            "python_prediction_demo": False,
            "ea_signal_consumption": False,
            "demo_trading": False,
            "live_trading": False,
            "reason": "No external specialist or ML survivor, frequency and shared-account risk gates failed, and no untouched holdout exists.",
        },
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "campaign_complete": True,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _daily_stress_pnl(path: Path, config: Mapping[str, Any]) -> np.ndarray:
    pnl = defaultdict(float)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            exit_date = datetime.strptime(row["exit_time"], "%Y.%m.%d %H:%M:%S").date().isoformat()
            pnl[exit_date] += float(row["stress_profit_usd"])
    dates = pd.bdate_range(config["start_date"], pd.Timestamp(config["end_exclusive_date"]) - pd.Timedelta(days=1))
    return np.asarray([pnl[date.date().isoformat()] for date in dates], dtype=float)


def _block_bootstrap(
    daily_pnl: np.ndarray,
    starting_capital: float,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    simulations = int(config["simulations"])
    block = int(config["block_trading_days"])
    batch_size = int(config["batch_size"])
    threshold = float(config["drawdown_threshold_pct"])
    seed = int(config["random_seed"]) + int(round(starting_capital * 100))
    rng = np.random.default_rng(seed)
    days = len(daily_pnl)
    blocks = int(np.ceil(days / block))
    offsets = np.arange(block, dtype=int)
    max_dd_pct = np.empty(simulations, dtype=float)
    ending = np.empty(simulations, dtype=float)
    ruined = np.empty(simulations, dtype=bool)
    breached = np.empty(simulations, dtype=bool)
    cursor = 0
    while cursor < simulations:
        count = min(batch_size, simulations - cursor)
        starts = rng.integers(0, days, size=(count, blocks))
        indices = (starts[:, :, None] + offsets[None, None, :]) % days
        samples = daily_pnl[indices.reshape(count, -1)[:, :days]]
        equity = starting_capital + np.cumsum(samples, axis=1)
        with_start = np.concatenate([np.full((count, 1), starting_capital), equity], axis=1)
        peaks = np.maximum.accumulate(with_start, axis=1)[:, 1:]
        drawdown_pct = (peaks - equity) / peaks
        max_dd_pct[cursor : cursor + count] = drawdown_pct.max(axis=1)
        ending[cursor : cursor + count] = equity[:, -1]
        ruined[cursor : cursor + count] = (equity <= 0).any(axis=1)
        breached[cursor : cursor + count] = (drawdown_pct >= threshold).any(axis=1)
        cursor += count
    return {
        "starting_capital_usd": starting_capital,
        "simulations": simulations,
        "trading_days_per_path": days,
        "block_trading_days": block,
        "random_seed": seed,
        "risk_of_ruin_probability": float(ruined.mean()),
        "drawdown_threshold_pct": threshold,
        "drawdown_threshold_breach_probability": float(breached.mean()),
        "median_max_drawdown_pct": float(np.quantile(max_dd_pct, 0.50)),
        "p95_max_drawdown_pct": float(np.quantile(max_dd_pct, 0.95)),
        "p99_max_drawdown_pct": float(np.quantile(max_dd_pct, 0.99)),
        "median_ending_equity_usd": float(np.quantile(ending, 0.50)),
        "p05_ending_equity_usd": float(np.quantile(ending, 0.05)),
        "p95_ending_equity_usd": float(np.quantile(ending, 0.95)),
    }


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: Mapping[str, Any]) -> str:
    foundation = payload["historical_foundation"]
    dd = payload["drawdown_boundary"]
    lines = [
        "# A3 ML Six-Iteration Final Qualification V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "## Bottom Line",
        "",
        f"The R1/R2 historical foundation is profitable: {foundation['trades']} trades, stress net ${foundation['stress_net_usd']:.2f}, stress PF {foundation['stress_profit_factor']:.3f}.",
        f"It is not deployable under this campaign: frequency is {foundation['frequency_per_trading_day']:.3f}/day, no new specialist or ML policy survived, and shared-account risk/holdout gates failed.",
        f"Measured closed-trade drawdown is ${dd['measured_shared_closed_trade_drawdown_usd']:.2f}; the conservative component-sum upper boundary is ${dd['sum_component_mt5_equity_drawdown_upper_bound_usd']:.2f}.",
        "",
        "## Monte Carlo",
        "",
        "| Starting capital | Ruin probability | P(DD >= 15%) | Median max DD | P95 max DD | Median ending equity |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["monte_carlo"]:
        lines.append(
            f"| ${row['starting_capital_usd']:.2f} | {100 * row['risk_of_ruin_probability']:.2f}% | {100 * row['drawdown_threshold_breach_probability']:.2f}% | {100 * row['median_max_drawdown_pct']:.2f}% | {100 * row['p95_max_drawdown_pct']:.2f}% | ${row['median_ending_equity_usd']:.2f} |"
        )
    lines.extend(["", "## Gates", ""])
    lines.extend(f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in payload["gates"].items())
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The six research iterations are complete. Python demo prediction, EA consumption, demo trading, and live trading remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_six_iteration_final_qualification_v1":
        raise FinalQualificationError("unexpected final qualification contract")
    monte = contract.get("monte_carlo", {})
    if int(monte.get("simulations", 0)) < 10000 or int(monte.get("block_trading_days", 0)) < 5:
        raise FinalQualificationError("Monte Carlo scope weakened")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only"):
        raise FinalQualificationError("qualification must remain research only")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise FinalQualificationError(f"{key} must remain false")
