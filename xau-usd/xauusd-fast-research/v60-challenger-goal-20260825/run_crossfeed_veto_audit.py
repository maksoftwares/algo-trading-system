from __future__ import annotations

from bisect import bisect_left
from collections import OrderedDict
from datetime import UTC, datetime
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
REPLAY_CONTRACT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-tick-runtime-replay-v1"
    / "config"
    / "DRAWDOWN_PROTECTION_V1_REPLAY_CONTRACT.json"
)
REPLAY_SOURCE = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-tick-runtime-replay-v1"
    / "src"
    / "replay.py"
)
FOUNDATION_SOURCE = (
    REPO_ROOT
    / "multi-asset"
    / "data-foundation"
    / "dukascopy-ticks-v1"
    / "src"
    / "dukascopy_tick_foundation"
    / "foundation.py"
)
EVENTS = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-tick-runtime-replay-v1"
    / "outputs"
    / "current-deployed-benchmark-20260825"
    / "EVENTS.csv"
)
VETO_AUDIT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-mature-source-health-rank-veto-v2"
    / "outputs"
    / "VETO_AUDIT.csv"
)
COHORT_AUDIT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-mature-source-health-rank-veto-v2"
    / "outputs"
    / "COHORT_AUDIT.csv"
)
RAW_ROOT = Path(
    "D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/raw/XAUUSD"
)
OUTPUT_CSV = ROOT / "CROSSFEED_VETO_AUDIT.csv"
OUTPUT_JSON = ROOT / "CROSSFEED_VETO_AUDIT.json"
OUTPUT_MD = ROOT / "CROSSFEED_VETO_AUDIT.md"
SOURCE_MANIFEST = ROOT / "CROSSFEED_SOURCE_MANIFEST.csv"
MAX_QUOTE_LAG_MS = 5_000
EXPECTED_BASELINE_TRADES = 1_390
EXPECTED_BASELINE_NET_USD = 3_603.565
BASELINE_NET_TOLERANCE_USD = 0.01


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return sha256_bytes(payload)


def timestamp_ms(value: Any) -> int:
    return int(pd.Timestamp(value).value // 1_000_000)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DukascopyQuoteStore:
    def __init__(
        self,
        raw_root: Path,
        decoder: Any,
        *,
        maximum_cached_hours: int = 4,
    ) -> None:
        self.raw_root = raw_root
        self.decoder = decoder
        self.maximum_cached_hours = maximum_cached_hours
        self._cache: OrderedDict[str, tuple[list[int], list[Any]]] = OrderedDict()
        self.source_hashes: dict[str, str] = {}
        self.missing_files: set[str] = set()

    def hour_path(self, timestamp_ms: int) -> Path:
        stamp = datetime.fromtimestamp(timestamp_ms / 1000.0, UTC)
        return (
            self.raw_root
            / f"year={stamp.year:04d}"
            / f"month={stamp.month:02d}"
            / f"{stamp:%Y%m%d%H}.json"
        )

    def load_hour(self, timestamp_ms: int) -> tuple[list[int], list[Any]]:
        path = self.hour_path(timestamp_ms)
        key = path.relative_to(self.raw_root).as_posix()
        if key in self._cache:
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
        if not path.is_file():
            self.missing_files.add(key)
            value = ([], [])
        else:
            raw = path.read_bytes()
            self.source_hashes[key] = sha256_bytes(raw)
            ticks = self.decoder.decode_payload(raw, "XAUUSD", key)
            timestamps = [int(tick.timestamp_ms) for tick in ticks]
            if timestamps != sorted(timestamps):
                raise ValueError(f"Nonmonotonic decoded tick hour: {path}")
            value = (timestamps, ticks)
        self._cache[key] = value
        while len(self._cache) > self.maximum_cached_hours:
            self._cache.popitem(last=False)
        return value

    def at_or_after(
        self, timestamp_ms: int, *, maximum_lag_ms: int = MAX_QUOTE_LAG_MS
    ) -> dict[str, Any] | None:
        hour_ms = timestamp_ms - timestamp_ms % 3_600_000
        for candidate_hour_ms in (hour_ms, hour_ms + 3_600_000):
            timestamps, ticks = self.load_hour(candidate_hour_ms)
            index = bisect_left(timestamps, timestamp_ms)
            if index >= len(timestamps):
                continue
            tick = ticks[index]
            lag_ms = int(tick.timestamp_ms) - timestamp_ms
            if lag_ms > maximum_lag_ms:
                return None
            return {
                "timestamp_ms": int(tick.timestamp_ms),
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "lag_ms": lag_ms,
                "source_file": str(tick.source_file_id),
                "source_row_index": int(tick.source_row_index),
            }
        return None


def load_exact_runtime_population() -> pd.DataFrame:
    replay = load_module("v60_crossfeed_replay", REPLAY_SOURCE)
    contract = replay.load_json(REPLAY_CONTRACT)
    config = replay.apply_runtime_risk_mode(
        replay.apply_portfolio_protection(
            contract,
            replay.load_json(replay.resolve_input(contract["inputs"]["demo_config"])),
        ),
        bool(
            contract["evaluation"].get(
                "required_equity_fraction_limits_enabled", False
            )
        ),
    )
    candidates, _ = replay.load_candidates(contract, config)
    candidate_rows = pd.DataFrame(
        {
            "trade_id": candidate.trade_id,
            "candidate_source_id": candidate.source_id,
            "direction": candidate.direction,
            "candidate_entry_time_ms": candidate.entry_ms,
            "candidate_exit_time_ms": candidate.exit_ms,
        }
        for candidate in candidates
    )

    events = pd.read_csv(EVENTS, low_memory=False)
    events = events.loc[events["scenario_id"].eq("deployed__full_runtime")]
    entries = events.loc[
        events["event"].eq("ORDER_FILLED"),
        ["trade_id", "source_id", "timestamp_utc"],
    ].rename(
        columns={
            "source_id": "runtime_source_id",
            "timestamp_utc": "runtime_entry_time_utc",
        }
    )
    exits = events.loc[
        events["event"].eq("POSITION_CLOSED"),
        ["trade_id", "timestamp_utc", "pnl_usd"],
    ].rename(
        columns={
            "timestamp_utc": "runtime_exit_time_utc",
            "pnl_usd": "capital_runtime_pnl_usd",
        }
    )
    frame = entries.merge(exits, on="trade_id", validate="one_to_one").merge(
        candidate_rows, on="trade_id", validate="one_to_one"
    )
    frame["runtime_entry_time_utc"] = pd.to_datetime(
        frame["runtime_entry_time_utc"], utc=True, format="mixed"
    )
    frame["runtime_exit_time_utc"] = pd.to_datetime(
        frame["runtime_exit_time_utc"], utc=True, format="mixed"
    )
    # Pandas 3 may store parsed timestamps at microsecond resolution, so the
    # Series integer representation is not a stable unit. Timestamp.value is ns.
    frame["runtime_entry_time_ms"] = frame["runtime_entry_time_utc"].map(
        timestamp_ms
    )
    frame["runtime_exit_time_ms"] = frame["runtime_exit_time_utc"].map(
        timestamp_ms
    )
    frame["capital_runtime_pnl_usd"] = pd.to_numeric(
        frame["capital_runtime_pnl_usd"], errors="raise"
    )
    if len(frame) != EXPECTED_BASELINE_TRADES:
        raise ValueError(
            f"Expected {EXPECTED_BASELINE_TRADES} runtime trades, found {len(frame)}"
        )
    observed_net = float(frame["capital_runtime_pnl_usd"].sum())
    if abs(observed_net - EXPECTED_BASELINE_NET_USD) > BASELINE_NET_TOLERANCE_USD:
        raise ValueError(
            f"Baseline net changed: expected {EXPECTED_BASELINE_NET_USD}, "
            f"found {observed_net}"
        )
    if not frame["runtime_source_id"].eq(frame["candidate_source_id"]).all():
        raise ValueError("Runtime and candidate source identities differ")
    if frame["runtime_exit_time_ms"].le(frame["runtime_entry_time_ms"]).any():
        raise ValueError("Runtime population contains a nonpositive holding period")
    return frame.sort_values(
        ["runtime_entry_time_ms", "trade_id"]
    ).reset_index(drop=True)


def attach_policy_membership(frame: pd.DataFrame) -> pd.DataFrame:
    veto = pd.read_csv(VETO_AUDIT)
    veto = veto.loc[veto["baseline_runtime_executed"].astype(str).eq("True")]
    veto_ids = set(veto["trade_id"].astype(str))
    cohort = pd.read_csv(COHORT_AUDIT)
    eligible_ids = set(cohort["trade_id"].astype(str))
    selected_ids = set(
        cohort.loc[cohort["selected_by_v2"].astype(str).eq("True"), "trade_id"].astype(
            str
        )
    )
    if selected_ids != veto_ids or len(veto_ids) != 12:
        raise ValueError("V2 veto identities differ between locked audit artifacts")
    if not veto_ids.issubset(set(frame["trade_id"])):
        raise ValueError("A locked veto is missing from the runtime population")
    result = frame.copy()
    result["v2_veto"] = result["trade_id"].isin(veto_ids)
    result["degraded_ranked_eligible"] = result["trade_id"].isin(eligible_ids)
    return result


def price_on_dukascopy(
    frame: pd.DataFrame, quote_store: DukascopyQuoteStore
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in frame.itertuples(index=False):
        entry = quote_store.at_or_after(int(trade.runtime_entry_time_ms))
        exit_quote = quote_store.at_or_after(int(trade.runtime_exit_time_ms))
        row = trade._asdict()
        row["dukascopy_entry_covered"] = entry is not None
        row["dukascopy_exit_covered"] = exit_quote is not None
        row["dukascopy_covered"] = entry is not None and exit_quote is not None
        row.update(
            {
                "dukascopy_entry_time_utc": None,
                "dukascopy_entry_lag_ms": None,
                "dukascopy_entry_bid": None,
                "dukascopy_entry_ask": None,
                "dukascopy_entry_source_file": None,
                "dukascopy_entry_source_row_index": None,
                "dukascopy_exit_time_utc": None,
                "dukascopy_exit_lag_ms": None,
                "dukascopy_exit_bid": None,
                "dukascopy_exit_ask": None,
                "dukascopy_exit_source_file": None,
                "dukascopy_exit_source_row_index": None,
                "dukascopy_spread_only_pnl_usd": None,
            }
        )
        if entry is not None:
            row.update(
                {
                    "dukascopy_entry_time_utc": datetime.fromtimestamp(
                        entry["timestamp_ms"] / 1000.0, UTC
                    ).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    "dukascopy_entry_lag_ms": entry["lag_ms"],
                    "dukascopy_entry_bid": entry["bid"],
                    "dukascopy_entry_ask": entry["ask"],
                    "dukascopy_entry_source_file": entry["source_file"],
                    "dukascopy_entry_source_row_index": entry["source_row_index"],
                }
            )
        if exit_quote is not None:
            row.update(
                {
                    "dukascopy_exit_time_utc": datetime.fromtimestamp(
                        exit_quote["timestamp_ms"] / 1000.0, UTC
                    ).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    "dukascopy_exit_lag_ms": exit_quote["lag_ms"],
                    "dukascopy_exit_bid": exit_quote["bid"],
                    "dukascopy_exit_ask": exit_quote["ask"],
                    "dukascopy_exit_source_file": exit_quote["source_file"],
                    "dukascopy_exit_source_row_index": exit_quote[
                        "source_row_index"
                    ],
                }
            )
        if entry is not None and exit_quote is not None:
            if trade.direction == "LONG":
                pnl = float(exit_quote["bid"] - entry["ask"])
            elif trade.direction == "SHORT":
                pnl = float(entry["bid"] - exit_quote["ask"])
            else:
                raise ValueError(f"Unknown direction: {trade.direction}")
            row["dukascopy_spread_only_pnl_usd"] = pnl
        rows.append(row)
    result = pd.DataFrame(rows)
    result["entry_year"] = pd.to_datetime(
        result["runtime_entry_time_utc"], utc=True
    ).dt.year
    return result


def profit_factor(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    gross_profit = float(array[array > 0.0].sum())
    gross_loss = -float(array[array < 0.0].sum())
    return gross_profit / gross_loss if gross_loss > 0 else math.inf


def closed_drawdown(frame: pd.DataFrame, pnl_column: str) -> float:
    ordered = frame.sort_values(["runtime_exit_time_ms", "trade_id"])
    equity = np.asarray(ordered[pnl_column].cumsum(), dtype=float)
    equity = np.concatenate(([0.0], equity))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def metrics(frame: pd.DataFrame, pnl_column: str) -> dict[str, Any]:
    values = pd.to_numeric(frame[pnl_column], errors="raise")
    return {
        "trades": int(len(frame)),
        "wins": int(values.gt(0.0).sum()),
        "losses": int(values.lt(0.0).sum()),
        "win_rate_percent": float(values.gt(0.0).mean() * 100.0) if len(frame) else None,
        "net_pnl_usd": float(values.sum()),
        "profit_factor": profit_factor(values),
        "closed_drawdown_usd": closed_drawdown(frame, pnl_column),
    }


def annual_comparison(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for year, group in frame.groupby("entry_year", sort=True):
        retained = group.loc[~group["v2_veto"]]
        baseline = metrics(group, "dukascopy_spread_only_pnl_usd")
        challenger = metrics(retained, "dukascopy_spread_only_pnl_usd")
        rows.append(
            {
                "year": int(year),
                "baseline_trades": baseline["trades"],
                "challenger_trades": challenger["trades"],
                "baseline_net_pnl_usd": baseline["net_pnl_usd"],
                "challenger_net_pnl_usd": challenger["net_pnl_usd"],
                "delta_net_pnl_usd": challenger["net_pnl_usd"]
                - baseline["net_pnl_usd"],
            }
        )
    return rows


def quote_lag_sensitivity(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for maximum_lag_ms in (250, 500, 1_000, 2_000, 5_000):
        common = frame.loc[
            frame["dukascopy_covered"]
            & frame["dukascopy_entry_lag_ms"].le(maximum_lag_ms)
            & frame["dukascopy_exit_lag_ms"].le(maximum_lag_ms)
        ].copy()
        veto = common.loc[common["v2_veto"]]
        retained = common.loc[~common["v2_veto"]]
        baseline_metrics = metrics(common, "dukascopy_spread_only_pnl_usd")
        challenger_metrics = metrics(retained, "dukascopy_spread_only_pnl_usd")
        veto_metrics = metrics(veto, "dukascopy_spread_only_pnl_usd")
        rows.append(
            {
                "maximum_lag_ms": maximum_lag_ms,
                "covered_trades": int(len(common)),
                "covered_vetoes": int(len(veto)),
                "veto_net_pnl_usd": veto_metrics["net_pnl_usd"],
                "veto_profit_factor": veto_metrics["profit_factor"],
                "challenger_delta_net_pnl_usd": challenger_metrics["net_pnl_usd"]
                - baseline_metrics["net_pnl_usd"],
                "challenger_delta_profit_factor": challenger_metrics[
                    "profit_factor"
                ]
                - baseline_metrics["profit_factor"],
                "challenger_delta_closed_drawdown_usd": challenger_metrics[
                    "closed_drawdown_usd"
                ]
                - baseline_metrics["closed_drawdown_usd"],
            }
        )
    return rows


def write_source_manifest(store: DukascopyQuoteStore) -> str:
    rows = [
        {"source_file": path, "sha256": digest}
        for path, digest in sorted(store.source_hashes.items())
    ]
    with SOURCE_MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["source_file", "sha256"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return canonical_sha256(rows)


def markdown(payload: dict[str, Any]) -> str:
    base = payload["dukascopy_same_timing_baseline"]
    challenger = payload["dukascopy_same_timing_v2"]
    veto = payload["dukascopy_veto_cohort"]
    lines = [
        "# V60/V2 Dukascopy Cross-Feed Veto Audit",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This transplants the exact V60 runtime entry and exit timestamps onto "
        "independent Dukascopy bid/ask ticks. It tests price-path portability; it "
        "does not replay the strategy on Dukascopy and cannot authorize deployment.",
        "",
        f"Common quote coverage: {payload['coverage']['covered_trades']:,}/"
        f"{payload['coverage']['runtime_trades']:,} trades "
        f"({payload['coverage']['coverage_fraction']:.2%}); veto coverage "
        f"{payload['coverage']['covered_veto_trades']}/"
        f"{payload['coverage']['veto_trades']}.",
        "",
        "| Metric | V60 same timing | V2 same timing | Change |",
        "|---|---:|---:|---:|",
        f"| Trades | {base['trades']:,} | {challenger['trades']:,} | {challenger['trades'] - base['trades']:+,} |",
        f"| Net spread-only P/L | ${base['net_pnl_usd']:.2f} | ${challenger['net_pnl_usd']:.2f} | ${challenger['net_pnl_usd'] - base['net_pnl_usd']:+.2f} |",
        f"| Profit factor | {base['profit_factor']:.4f} | {challenger['profit_factor']:.4f} | {challenger['profit_factor'] - base['profit_factor']:+.4f} |",
        f"| Win rate | {base['win_rate_percent']:.2f}% | {challenger['win_rate_percent']:.2f}% | {challenger['win_rate_percent'] - base['win_rate_percent']:+.2f} pp |",
        f"| Closed drawdown | ${base['closed_drawdown_usd']:.2f} | ${challenger['closed_drawdown_usd']:.2f} | ${challenger['closed_drawdown_usd'] - base['closed_drawdown_usd']:+.2f} |",
        "",
        "## Rejected cohort",
        "",
        f"The 12 V2 vetoes produce ${veto['net_pnl_usd']:.2f} at PF "
        f"{veto['profit_factor']:.4f} on Dukascopy using the same timestamps. "
        f"Capital/Dukascopy outcome-sign agreement is "
        f"{payload['diagnostics']['veto_outcome_sign_agreement_percent']:.2f}%.",
        "",
        "| Year | V60 P/L | V2 P/L | Change |",
        "|---:|---:|---:|---:|",
    ]
    for row in payload["annual_comparison"]:
        lines.append(
            f"| {row['year']} | ${row['baseline_net_pnl_usd']:.2f} | "
            f"${row['challenger_net_pnl_usd']:.2f} | ${row['delta_net_pnl_usd']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "## Quote-lag sensitivity",
            "",
            "| Maximum lag | Covered trades | Covered vetoes | Veto P/L | Veto PF | V2 P/L change |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["quote_lag_sensitivity"]:
        lines.append(
            f"| {row['maximum_lag_ms']} ms | {row['covered_trades']:,} | "
            f"{row['covered_vetoes']} | ${row['veto_net_pnl_usd']:.2f} | "
            f"{row['veto_profit_factor']:.4f} | "
            f"${row['challenger_delta_net_pnl_usd']:+.2f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Cross-feed mechanism support: **{str(payload['diagnostics']['crossfeed_mechanism_support']).upper()}**.",
            "The audit uses the Capital-derived holding intervals, so it remains "
            "historically exposed and post-selected. Dukascopy spread is included, "
            "but commission, swap, and broker-specific stop triggering are not. "
            "The locked clean prospective broker test remains the deployment gate.",
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    decoder = load_module("v60_crossfeed_foundation", FOUNDATION_SOURCE)
    frame = attach_policy_membership(load_exact_runtime_population())
    store = DukascopyQuoteStore(RAW_ROOT, decoder)
    priced = price_on_dukascopy(frame, store)
    coverage = float(priced["dukascopy_covered"].mean())
    veto_coverage = float(
        priced.loc[priced["v2_veto"], "dukascopy_covered"].mean()
    )
    manifest_hash = write_source_manifest(store)
    common = priced.loc[priced["dukascopy_covered"]].copy()
    baseline = metrics(common, "dukascopy_spread_only_pnl_usd")
    retained = common.loc[~common["v2_veto"]].copy()
    challenger = metrics(retained, "dukascopy_spread_only_pnl_usd")
    veto = common.loc[common["v2_veto"]].copy()
    veto_metrics = metrics(veto, "dukascopy_spread_only_pnl_usd")
    eligible_other = common.loc[
        common["degraded_ranked_eligible"] & ~common["v2_veto"]
    ].copy()
    annual = annual_comparison(common)
    lag_sensitivity = quote_lag_sensitivity(priced)
    sign_agreement = float(
        np.mean(
            np.sign(veto["capital_runtime_pnl_usd"].to_numpy(dtype=float))
            == np.sign(
                veto["dukascopy_spread_only_pnl_usd"].to_numpy(dtype=float)
            )
        )
        * 100.0
    )
    all_sign_agreement = float(
        np.mean(
            np.sign(common["capital_runtime_pnl_usd"].to_numpy(dtype=float))
            == np.sign(
                common["dukascopy_spread_only_pnl_usd"].to_numpy(dtype=float)
            )
        )
        * 100.0
    )
    correlation = float(
        np.corrcoef(
            common["capital_runtime_pnl_usd"].to_numpy(dtype=float),
            common["dukascopy_spread_only_pnl_usd"].to_numpy(dtype=float),
        )[0, 1]
    )
    selected_wins = int(
        veto["dukascopy_spread_only_pnl_usd"].gt(0.0).sum()
    )
    selected_losses = int(
        veto["dukascopy_spread_only_pnl_usd"].lt(0.0).sum()
    )
    other_wins = int(
        eligible_other["dukascopy_spread_only_pnl_usd"].gt(0.0).sum()
    )
    other_losses = int(
        eligible_other["dukascopy_spread_only_pnl_usd"].lt(0.0).sum()
    )
    fisher_p = float(
        fisher_exact(
            [[selected_wins, selected_losses], [other_wins, other_losses]],
            alternative="less",
        ).pvalue
    )
    checks = {
        "minimum_98_percent_quote_coverage": coverage >= 0.98,
        "complete_veto_quote_coverage": veto_coverage == 1.0,
        "veto_cohort_net_negative": veto_metrics["net_pnl_usd"] < 0.0,
        "veto_cohort_profit_factor_below_0_8": veto_metrics["profit_factor"] < 0.8,
        "challenger_net_not_below_baseline": challenger["net_pnl_usd"]
        >= baseline["net_pnl_usd"],
        "challenger_profit_factor_not_below_baseline": challenger["profit_factor"]
        >= baseline["profit_factor"],
        "challenger_closed_drawdown_not_above_baseline": challenger[
            "closed_drawdown_usd"
        ]
        <= baseline["closed_drawdown_usd"],
        "every_calendar_year_net_delta_nonnegative": all(
            row["delta_net_pnl_usd"] >= 0.0 for row in annual
        ),
    }
    payload = {
        "schema_version": "v60_v2_dukascopy_crossfeed_veto_audit_v1",
        "generated_at_utc": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "method": {
            "description": "Exact Capital V60 runtime intervals repriced on the first Dukascopy quote at or after each entry and exit timestamp",
            "xau_position_ounces": 1.0,
            "equivalent_lot_size": 0.01,
            "maximum_quote_lag_ms": MAX_QUOTE_LAG_MS,
            "included_cost": "Dukascopy bid/ask spread",
            "excluded_costs": ["commission", "swap", "broker-specific stop triggering"],
            "causal_strategy_replay": False,
            "untouched_out_of_sample": False,
            "deployment_authorized": False,
        },
        "input_sha256": {
            "replay_contract": sha256_file(REPLAY_CONTRACT),
            "replay_source": sha256_file(REPLAY_SOURCE),
            "foundation_decoder": sha256_file(FOUNDATION_SOURCE),
            "runtime_events": sha256_file(EVENTS),
            "veto_audit": sha256_file(VETO_AUDIT),
            "cohort_audit": sha256_file(COHORT_AUDIT),
            "dukascopy_source_manifest": manifest_hash,
        },
        "coverage": {
            "runtime_trades": int(len(priced)),
            "covered_trades": int(priced["dukascopy_covered"].sum()),
            "coverage_fraction": coverage,
            "veto_trades": int(priced["v2_veto"].sum()),
            "covered_veto_trades": int(
                priced.loc[priced["v2_veto"], "dukascopy_covered"].sum()
            ),
            "source_files_hashed": len(store.source_hashes),
            "missing_source_files": sorted(store.missing_files),
            "uncovered_trade_ids": priced.loc[
                ~priced["dukascopy_covered"], "trade_id"
            ].astype(str).tolist(),
            "maximum_observed_entry_lag_ms": int(
                priced["dukascopy_entry_lag_ms"].max()
            ),
            "maximum_observed_exit_lag_ms": int(
                priced["dukascopy_exit_lag_ms"].max()
            ),
        },
        "capital_runtime_baseline": metrics(priced, "capital_runtime_pnl_usd"),
        "capital_common_coverage_baseline": metrics(
            common, "capital_runtime_pnl_usd"
        ),
        "dukascopy_same_timing_baseline": baseline,
        "dukascopy_same_timing_v2": challenger,
        "dukascopy_veto_cohort": veto_metrics,
        "dukascopy_other_degraded_ranked_cohort": metrics(
            eligible_other, "dukascopy_spread_only_pnl_usd"
        ),
        "annual_comparison": annual,
        "quote_lag_sensitivity": lag_sensitivity,
        "diagnostics": {
            "capital_dukascopy_all_trade_pnl_correlation": correlation,
            "all_trade_outcome_sign_agreement_percent": all_sign_agreement,
            "veto_outcome_sign_agreement_percent": sign_agreement,
            "eligible_cohort_fisher_exact_one_sided_p": fisher_p,
            "checks": checks,
            "crossfeed_mechanism_support": all(checks.values()),
            "post_selection_diagnostic": True,
            "deployment_authorized": False,
        },
        "limitations": [
            "Entry and exit timestamps were produced by the Capital replay and are therefore historically exposed.",
            "This does not test whether Dukascopy prices would independently trigger the same entries or exits.",
            "The policy was selected after observing historical Capital outcomes.",
            "Dukascopy spread is included, but commission, swap, and broker-specific execution are not.",
            "Only the preregistered clean prospective broker test can authorize review for deployment.",
        ],
    }

    output = priced.copy()
    output["runtime_entry_time_utc"] = output["runtime_entry_time_utc"].map(
        lambda value: value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    output["runtime_exit_time_utc"] = output["runtime_exit_time_utc"].map(
        lambda value: value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    output.to_csv(OUTPUT_CSV, index=False, lineterminator="\n")
    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    OUTPUT_MD.write_text(markdown(payload), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
