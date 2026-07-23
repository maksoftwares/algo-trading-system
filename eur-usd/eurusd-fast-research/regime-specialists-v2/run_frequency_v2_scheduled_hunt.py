from __future__ import annotations

from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path

import pandas as pd

from src.frequency_v2 import (
    FrequencyCandidate,
    load_capital_m15,
    metrics,
    route_portfolio,
    simulate,
)

ROOT = Path(__file__).resolve().parent
SOURCE = Path(
    "C:/MT5A1M5MomentumBacktest/Tester/Agent-127.0.0.1-3000/"
    "MQL5/Files/EURUSD_M15_CAPITAL_BROKER_201607_202607.csv"
)
EXPECTED_SHA256 = "eacc532a5f0001ea66c80a558bd4cffe7ced5704bf9d9d4770cb2f783269bea0"
WINDOWS = {
    "development": (pd.Timestamp("2016-07-01", tz="UTC"), pd.Timestamp("2022-07-01", tz="UTC")),
    "validation": (pd.Timestamp("2022-07-01", tz="UTC"), pd.Timestamp("2024-07-01", tz="UTC")),
}


def scheduled_candidates() -> list[FrequencyCandidate]:
    rows: list[FrequencyCandidate] = []
    counter = itertools.count(2001)
    regimes = ("trend_up", "trend_down", "chop", "compression", "transition")
    for family, regime, hour, lookback, displacement, stop, target, hold in itertools.product(
        (
            "scheduled_momentum",
            "scheduled_reversal",
            "scheduled_ema_follow",
            "scheduled_ema_fade",
        ),
        regimes,
        (0, 6, 12, 18),
        (4, 16),
        (0.0, 0.25),
        (0.75, 1.25),
        (0.6, 0.9),
        (16, 32),
    ):
        # EMA direction does not depend on the displacement lookback.
        if family.startswith("scheduled_ema") and lookback != 4:
            continue
        rows.append(
            FrequencyCandidate(
                candidate_id=f"EURF2_{next(counter):04d}",
                family=family,
                regime=regime,
                direction="dynamic",
                threshold=float(hour),
                stop_atr=stop,
                target_r=target,
                max_hold_bars=hold,
                lookback=lookback,
                body_min=displacement,
                session="all",
            )
        )
    return rows


def active_days(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> int:
    mask = (frame["timestamp"] >= start) & (frame["timestamp"] < end)
    return int(frame.loc[mask, "active_date"].nunique())


def main() -> None:
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("Capital.com M15 source checksum mismatch")
    contract = json.loads((ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text())
    frame, _ = load_capital_m15(SOURCE, contract["regime_classifier"])
    output = ROOT / "outputs" / "frequency_v2_scheduled_hunt"
    output.mkdir(parents=True, exist_ok=True)
    universe = scheduled_candidates()
    days = {name: active_days(frame, *window) for name, window in WINDOWS.items()}
    development_rows = []
    development_pass: list[FrequencyCandidate] = []
    for index, candidate in enumerate(universe, 1):
        trades = simulate(frame, candidate, *WINDOWS["development"], maximum_trades_per_day=2)
        row = {**asdict(candidate), **metrics(trades, days["development"])}
        row["stage"] = "development"
        row["parameter_sha256"] = candidate.parameter_sha256
        row["gate_pass"] = bool(
            row["trades"] >= 100
            and row["profit_factor"] >= 1.08
            and row["average_r"] > 0
            and row["top_5pct_removed_profit_factor"] >= 0.92
        )
        development_rows.append(row)
        if row["gate_pass"]:
            development_pass.append(candidate)
        if index % 250 == 0:
            print(f"screened {index}/{len(universe)}; development passes={len(development_pass)}")

    # Freeze no more than five development parameterizations per mechanism,
    # regime, and decision hour before opening validation.
    development_frame = pd.DataFrame(development_rows)
    frozen_ids: list[str] = []
    passed = development_frame[development_frame["gate_pass"]].copy()
    for _, group in passed.groupby(["family", "regime", "threshold"]):
        ordered = group.sort_values(
            ["top_5pct_removed_profit_factor", "profit_factor", "trades"],
            ascending=False,
        )
        frozen_ids.extend(ordered.head(5)["candidate_id"].tolist())
    candidate_map = {candidate.candidate_id: candidate for candidate in universe}
    validation_rows = []
    validation_trades: dict[str, list[dict]] = {}
    validated: list[tuple[FrequencyCandidate, dict]] = []
    for candidate_id in frozen_ids:
        candidate = candidate_map[candidate_id]
        trades = simulate(frame, candidate, *WINDOWS["validation"], maximum_trades_per_day=2)
        row = {**asdict(candidate), **metrics(trades, days["validation"])}
        row["stage"] = "validation"
        row["parameter_sha256"] = candidate.parameter_sha256
        row["gate_pass"] = bool(
            row["trades"] >= 30
            and row["profit_factor"] >= 1.05
            and row["average_r"] > 0
            and row["top_5pct_removed_profit_factor"] >= 0.88
        )
        validation_rows.append(row)
        if row["gate_pass"]:
            validation_trades[candidate_id] = trades
            validated.append((candidate, row))

    # One parameterization per independent regime/decision mechanism/hour.
    validated.sort(
        key=lambda item: (
            min(item[1]["profit_factor"], item[1]["top_5pct_removed_profit_factor"]),
            item[1]["trades"],
        ),
        reverse=True,
    )
    sleeves: list[tuple[FrequencyCandidate, dict]] = []
    seen: set[tuple[str, str, float]] = set()
    for candidate, row in validated:
        key = (candidate.family, candidate.regime, candidate.threshold)
        if key in seen:
            continue
        seen.add(key)
        sleeves.append((candidate, row))

    priority: list[str] = []
    remaining = sleeves.copy()
    selection_path = []
    while remaining and len(priority) < 20:
        best = None
        for candidate, _ in remaining:
            trial_priority = priority + [candidate.candidate_id]
            trial = route_portfolio(validation_trades, trial_priority, maximum_trades_per_day=2)
            result = metrics(trial, days["validation"])
            quality_ok = (
                result["profit_factor"] >= 1.20
                and result["win_rate"] >= 0.50
                and result["average_r"] > 0
            )
            score = (
                int(quality_ok),
                min(result["trades_per_active_day"], 1.0),
                result["profit_factor"],
                result["net_r"],
            )
            if best is None or score > best[0]:
                best = (score, candidate, result)
        if best is None:
            break
        _, selected, result = best
        if result["profit_factor"] < 1.20 or result["average_r"] <= 0:
            break
        priority.append(selected.candidate_id)
        remaining = [item for item in remaining if item[0].candidate_id != selected.candidate_id]
        selection_path.append(
            {"selection_order": len(priority), "candidate_id": selected.candidate_id, **result}
        )
        if result["trades_per_active_day"] >= 1.0 and len({candidate_map[x].regime for x in priority}) >= 3:
            break

    portfolio = route_portfolio(validation_trades, priority, maximum_trades_per_day=2)
    portfolio_metrics = metrics(portfolio, days["validation"])
    selected_specs = [asdict(candidate_map[candidate_id]) for candidate_id in priority]
    distinct_regimes = len({row["regime"] for row in selected_specs})
    gate_pass = bool(
        portfolio_metrics["trades_per_active_day"] >= 1.0
        and portfolio_metrics["profit_factor"] >= 1.30
        and portfolio_metrics["win_rate"] >= 0.52
        and portfolio_metrics["maximum_drawdown_r"] <= 25.0
        and portfolio_metrics["positive_active_month_share"] >= 0.55
        and portfolio_metrics["top_5pct_removed_profit_factor"] >= 1.0
        and distinct_regimes >= 3
    )
    pd.concat(
        [development_frame, pd.DataFrame(validation_rows)], ignore_index=True
    ).to_csv(output / "CANDIDATE_METRICS.csv", index=False)
    pd.DataFrame(selection_path).to_csv(output / "PORTFOLIO_SELECTION_PATH.csv", index=False)
    pd.DataFrame(portfolio).to_csv(output / "VALIDATION_PORTFOLIO_TRADES.csv", index=False)
    verdict = {
        "schema_version": "eurusd_frequency_v2_scheduled_hunt_v1",
        "source_sha256": EXPECTED_SHA256,
        "active_days": days,
        "candidate_count": len(universe),
        "development_pass_count": len(development_pass),
        "validation_opened_count": len(frozen_ids),
        "validation_pass_count": len(validated),
        "selected_priority": priority,
        "selected_specialists": selected_specs,
        "distinct_regimes": distinct_regimes,
        "validation_portfolio_metrics": portfolio_metrics,
        "validation_gate_pass": gate_pass,
        "exam_opened": False,
        "verdict": (
            "FREEZE_PORTFOLIO_AND_OPEN_ADAPTIVE_DEMO_EXAM"
            if gate_pass
            else "SCHEDULED_GENERATION_FAILED_CONTINUE_RESEARCH"
        ),
    }
    (output / "VERDICT.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
