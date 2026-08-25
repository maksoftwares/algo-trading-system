from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime
import hashlib
import heapq
import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT = ROOT / "outputs" / "RESULT.json"
EVENTS = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-tick-runtime-replay-v1"
    / "outputs"
    / "current-deployed-benchmark-20260825"
    / "EVENTS.csv"
)
RANKS = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-portable-mature-topup-v2"
    / "outputs"
    / "PRIMARY_DECISIONS.parquet"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profit_factor(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    gross_profit = float(array[array > 0.0].sum())
    gross_loss = -float(array[array < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0.0 else float("inf")


def load_baseline_trades() -> pd.DataFrame:
    events = pd.read_csv(EVENTS)
    events = events.loc[events["scenario_id"].eq("deployed__full_runtime")]
    entries = events.loc[
        events["event"].eq("ORDER_FILLED"),
        ["trade_id", "source_id", "timestamp_utc"],
    ].rename(columns={"timestamp_utc": "entry_time_utc"})
    exits = events.loc[
        events["event"].eq("POSITION_CLOSED"),
        ["trade_id", "timestamp_utc", "pnl_usd"],
    ].rename(columns={"timestamp_utc": "exit_time_utc"})
    ranks = pd.read_parquet(RANKS, columns=["trade_id", "rank"])
    frame = entries.merge(exits, on="trade_id", validate="one_to_one").merge(
        ranks, on="trade_id", how="left", validate="one_to_one"
    )
    frame["entry_time_utc"] = pd.to_datetime(
        frame["entry_time_utc"], utc=True, format="mixed"
    )
    frame["exit_time_utc"] = pd.to_datetime(
        frame["exit_time_utc"], utc=True, format="mixed"
    )
    return frame.sort_values(["entry_time_utc", "trade_id"]).reset_index(drop=True)


def reconstruct_eligible(frame: pd.DataFrame, policy: dict) -> pd.DataFrame:
    lookback = int(policy["lookback_closed_trades"])
    minimum_history = int(policy["minimum_prior_source_closed_trades"])
    history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=lookback))
    closed_count: dict[str, int] = defaultdict(int)
    pending: list[tuple[int, str, str, float]] = []
    rows = []
    for trade in frame.itertuples(index=False):
        entry_ns = int(trade.entry_time_utc.value)
        while pending and pending[0][0] <= entry_ns:
            _, _, source_id, pnl = heapq.heappop(pending)
            history[source_id].append(pnl)
            closed_count[source_id] += 1
        source_history = history[trade.source_id]
        prior_pf = (
            profit_factor(source_history) if len(source_history) == lookback else None
        )
        eligible = bool(
            closed_count[trade.source_id] >= minimum_history
            and prior_pf is not None
            and prior_pf < float(policy["maximum_prior_profit_factor_exclusive"])
            and pd.notna(trade.rank)
        )
        selected = bool(
            eligible
            and float(trade.rank) < float(policy["maximum_causal_rank_exclusive"])
        )
        if eligible:
            rows.append(
                {
                    "trade_id": str(trade.trade_id),
                    "source_id": str(trade.source_id),
                    "entry_time_utc": trade.entry_time_utc,
                    "entry_year": int(trade.entry_time_utc.year),
                    "entry_date": trade.entry_time_utc.date().isoformat(),
                    "causal_rank": float(trade.rank),
                    "prior_profit_factor": float(prior_pf),
                    "baseline_runtime_pnl_usd": float(trade.pnl_usd),
                    "selected_by_v2": selected,
                }
            )
        if not selected:
            heapq.heappush(
                pending,
                (
                    int(trade.exit_time_utc.value),
                    str(trade.trade_id),
                    str(trade.source_id),
                    float(trade.pnl_usd),
                ),
            )
    return pd.DataFrame(rows)


def stratified_permutation_p_value(
    frame: pd.DataFrame,
    group_columns: list[str],
    *,
    iterations: int = 100_000,
    seed: int = 20260825,
) -> float:
    observed = float(
        frame.loc[frame["selected_by_v2"], "baseline_runtime_pnl_usd"].sum()
    )
    rng = np.random.default_rng(seed)
    groups = []
    group_key: str | list[str] = group_columns[0] if len(group_columns) == 1 else group_columns
    for _, group in frame.groupby(group_key, sort=True):
        selected_count = int(group["selected_by_v2"].sum())
        if selected_count:
            groups.append(
                (
                    group["baseline_runtime_pnl_usd"].to_numpy(dtype=float),
                    selected_count,
                )
            )
    simulated = np.zeros(iterations, dtype=float)
    for values, selected_count in groups:
        for index in range(iterations):
            simulated[index] += float(
                rng.choice(values, size=selected_count, replace=False).sum()
            )
    return float((np.count_nonzero(simulated <= observed) + 1) / (iterations + 1))


def main() -> int:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    frame = reconstruct_eligible(load_baseline_trades(), result["policy"])
    selected = frame.loc[frame["selected_by_v2"]].copy()
    expected_ids = {
        str(row["trade_id"])
        for row in result["veto_audit"]
        if bool(row["baseline_runtime_executed"])
    }
    if set(selected["trade_id"]) != expected_ids:
        raise ValueError("Cohort reconstruction differs from the exact runtime replay")
    other = frame.loc[~frame["selected_by_v2"]]
    selected_wins = int(selected["baseline_runtime_pnl_usd"].gt(0.0).sum())
    selected_losses = int(selected["baseline_runtime_pnl_usd"].lt(0.0).sum())
    other_wins = int(other["baseline_runtime_pnl_usd"].gt(0.0).sum())
    other_losses = int(other["baseline_runtime_pnl_usd"].lt(0.0).sum())
    fisher_p = float(
        fisher_exact(
            [[selected_wins, selected_losses], [other_wins, other_losses]],
            alternative="less",
        ).pvalue
    )
    payload = {
        "schema_version": "v60_mature_source_health_rank_veto_v2_cohort_audit",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "input_sha256": {
            "v2_result": sha256_file(RESULT),
            "baseline_events": sha256_file(EVENTS),
            "causal_ranks": sha256_file(RANKS),
        },
        "eligible_cohort": {
            "trades": int(len(frame)),
            "wins": int(frame["baseline_runtime_pnl_usd"].gt(0.0).sum()),
            "net_pnl_usd": float(frame["baseline_runtime_pnl_usd"].sum()),
        },
        "selected_cohort": {
            "trades": int(len(selected)),
            "wins": selected_wins,
            "losses": selected_losses,
            "net_pnl_usd": float(selected["baseline_runtime_pnl_usd"].sum()),
            "profit_factor": profit_factor(selected["baseline_runtime_pnl_usd"]),
            "distinct_entry_dates": int(selected["entry_date"].nunique()),
            "source_counts": selected.groupby("source_id").size().astype(int).to_dict(),
            "year_counts": selected.groupby("entry_year").size().astype(int).to_dict(),
        },
        "other_degraded_ranked_cohort": {
            "trades": int(len(other)),
            "wins": other_wins,
            "losses": other_losses,
            "net_pnl_usd": float(other["baseline_runtime_pnl_usd"].sum()),
            "profit_factor": profit_factor(other["baseline_runtime_pnl_usd"]),
        },
        "diagnostics": {
            "fisher_exact_one_sided_p": fisher_p,
            "source_stratified_permutation_p": stratified_permutation_p_value(
                frame, ["source_id"]
            ),
            "year_stratified_permutation_p": stratified_permutation_p_value(
                frame, ["entry_year"], seed=20260826
            ),
            "source_year_stratified_permutation_p": stratified_permutation_p_value(
                frame, ["source_id", "entry_year"], seed=20260827
            ),
            "iterations_per_permutation": 100_000,
            "post_selection_inference": True,
            "deployment_authorized": False,
        },
        "limitations": [
            "The policy was nominated after historical outcomes were exposed.",
            "P-values are descriptive post-selection diagnostics, not untouched proof.",
            "Only new forward broker outcomes can satisfy deployment authorization.",
        ],
    }
    outputs = ROOT / "outputs"
    frame.assign(
        entry_time_utc=frame["entry_time_utc"].astype(str)
    ).to_csv(outputs / "COHORT_AUDIT.csv", index=False)
    (outputs / "COHORT_AUDIT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    diagnostics = payload["diagnostics"]
    selected_summary = payload["selected_cohort"]
    other_summary = payload["other_degraded_ranked_cohort"]
    lines = [
        "# V60 Mature Source-Health V2 Cohort Audit",
        "",
        "Post-selection diagnostics only. Deployment remains unauthorized.",
        "",
        "| Cohort | Trades | Wins | Losses | Net P/L | PF |",
        "|---|---:|---:|---:|---:|---:|",
        f"| V2 selected | {selected_summary['trades']} | {selected_summary['wins']} | "
        f"{selected_summary['losses']} | ${selected_summary['net_pnl_usd']:.2f} | "
        f"{selected_summary['profit_factor']:.4f} |",
        f"| Other degraded ranked trades | {other_summary['trades']} | "
        f"{other_summary['wins']} | {other_summary['losses']} | "
        f"${other_summary['net_pnl_usd']:.2f} | {other_summary['profit_factor']:.4f} |",
        "",
        f"- Fisher exact one-sided p: `{diagnostics['fisher_exact_one_sided_p']:.6f}`.",
        f"- Source-stratified permutation p: `{diagnostics['source_stratified_permutation_p']:.6f}`.",
        f"- Year-stratified permutation p: `{diagnostics['year_stratified_permutation_p']:.6f}`.",
        f"- Source-year-stratified permutation p: `{diagnostics['source_year_stratified_permutation_p']:.6f}`.",
        f"- Distinct selected entry dates: `{selected_summary['distinct_entry_dates']}`.",
        "",
        "These tests strengthen the historical mechanism but do not remove the need for new forward evidence.",
    ]
    (outputs / "COHORT_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload["diagnostics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
