"""Independent replication of the Codex EURUSD H4 confirmation portfolio.

Codex's own pipeline reproduces its published result exactly (1,288 trades,
matching block counts and win rates), so this is not a reproducibility check.
It is a *data and execution* check: take Codex's exact trade decisions — entry
time, side, stop and target — and re-resolve every outcome on this lane's
independent Dukascopy M5 bid/ask bars using this lane's engine conventions.

What that isolates:

1. **Feed agreement.** Does Codex's entry price exist in independent data at the
   stated timestamp?
2. **Execution realism.** A SHORT is closed by *buying*, so its stop and target
   must be resolved on the **ask** path. Resolving a short on the bid (or on the
   mid) makes stops trigger later and targets trigger sooner — a systematic
   optimistic bias that no amount of cost stress would reveal, because it is a
   path error rather than a cost error.

Trade decisions are taken as given and never re-derived, so any difference is
attributable to data or fill resolution, not to a different strategy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, load_m5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
LEDGER = Path(
    r"C:\Users\ZHAOZH~1\AppData\Local\Temp\claude"
    r"\C--Users-ZHAO-ZHU-INFORMATION-Downloads-algo-trading-system"
    r"\a4c0f7b6-6efa-492a-ad2e-e53ef7b80853\scratchpad\codex-verify"
    r"\forex\eurusd-regime-specialists-v1\outputs\h4_confirmation_ensemble\TRADES.csv"
)
SYMBOL = "EURUSD"
PIP = 0.0001
SPREAD_PIPS = 0.70  # Codex's assumption; independently measured as 0.70 in this lane
MAX_HOLD_BARS = 288 * 5


def resolve(
    bars: pd.DataFrame, entry_index: int, side: int, stop: float, target: float, path: str
) -> tuple[str, float, int]:
    """Resolve one trade forward. ``path`` selects which series tests the levels."""
    last = min(entry_index + MAX_HOLD_BARS, len(bars) - 1)
    window = slice(entry_index, last + 1)
    if path == "correct":
        # short closes by buying -> ask path; long closes by selling -> bid path
        high = (bars["ask_high"] if side < 0 else bars["bid_high"]).to_numpy()[window]
        low = (bars["ask_low"] if side < 0 else bars["bid_low"]).to_numpy()[window]
    elif path == "mid":
        high = ((bars["ask_high"] + bars["bid_high"]) / 2).to_numpy()[window]
        low = ((bars["ask_low"] + bars["bid_low"]) / 2).to_numpy()[window]
    else:  # "optimistic": resolve a short on the bid path
        high = (bars["bid_high"] if side < 0 else bars["ask_high"]).to_numpy()[window]
        low = (bars["bid_low"] if side < 0 else bars["ask_low"]).to_numpy()[window]

    if side < 0:
        hit_stop, hit_target = high >= stop, low <= target
    else:
        hit_stop, hit_target = low <= stop, high >= target

    stop_at = int(np.argmax(hit_stop)) if hit_stop.any() else -1
    target_at = int(np.argmax(hit_target)) if hit_target.any() else -1
    if stop_at < 0 and target_at < 0:
        close = (bars["ask_close"] if side < 0 else bars["bid_close"]).to_numpy()[last]
        return "TIMEOUT", float(close), last
    if stop_at < 0:
        return "TARGET", target, entry_index + target_at
    if target_at < 0:
        return "STOP", stop, entry_index + stop_at
    if stop_at <= target_at:  # ambiguous bar resolves to the stop
        return "STOP", stop, entry_index + stop_at
    return "TARGET", target, entry_index + target_at


def main() -> int:
    if not LEDGER.is_file():
        print(f"ledger not found: {LEDGER}")
        return 1
    ledger = pd.read_csv(LEDGER)
    ledger["entry_time_utc"] = pd.to_datetime(ledger["entry_time_utc"], utc=True)
    print(f"Codex ledger: {len(ledger)} trades, {ledger['side'].value_counts().to_dict()}")

    bars = load_m5(CACHE, SYMBOL)
    stamps = bars["timestamp_ms"].to_numpy(np.int64)
    # pandas 3 parses to datetime64[us]; normalise explicitly rather than
    # assuming a resolution, which silently produced seconds on the first pass.
    entry_ms = (
        ledger["entry_time_utc"].dt.tz_convert(None).astype("datetime64[ns]").astype("int64")
        // 1_000_000
    ).to_numpy()
    index = np.searchsorted(stamps, entry_ms, side="left")
    found = (index < len(bars)) & (stamps[np.clip(index, 0, len(bars) - 1)] == entry_ms)
    print(f"entry timestamps matched in independent M5 data: {found.sum()}/{len(ledger)}")

    work = ledger.loc[found].copy().reset_index(drop=True)
    idx = index[found]
    side = np.where(work["side"].to_numpy() == "SHORT", -1, 1)

    # --- 1. feed agreement on the entry price ---
    my_bid = bars["bid_open"].to_numpy()[idx]
    my_ask = bars["ask_open"].to_numpy()[idx]
    their_entry = work["entry"].to_numpy()
    # a short sells the bid; a long buys the ask
    my_fill = np.where(side < 0, my_bid, my_ask)
    diff_pips = (their_entry - my_fill) / PIP
    print(
        f"\nentry price vs independent feed (pips): median {np.median(diff_pips):+.3f}  "
        f"p05 {np.quantile(diff_pips, 0.05):+.2f}  p95 {np.quantile(diff_pips, 0.95):+.2f}  "
        f"|>1 pip| {(np.abs(diff_pips) > 1).mean() * 100:.1f}%"
    )

    # --- 2. re-resolve outcomes under three path conventions ---
    results = {}
    for path in ("correct", "mid", "optimistic"):
        reasons, nets = [], []
        for row in range(len(work)):
            reason, exit_price, _ = resolve(
                bars, int(idx[row]), int(side[row]),
                float(work.loc[row, "stop"]), float(work.loc[row, "target"]), path,
            )
            gross = (their_entry[row] - exit_price) if side[row] < 0 else (exit_price - their_entry[row])
            nets.append(gross / PIP - SPREAD_PIPS)
            reasons.append(reason)
        nets = np.asarray(nets)
        stop_r = work["stop_pips"].to_numpy()
        r = nets / stop_r
        wins, losses = r[r > 0], r[r <= 0]
        results[path] = {
            "trades": int(r.size),
            "win_rate_pct": round(100.0 * wins.size / r.size, 2),
            "net_r": round(float(r.sum()), 2),
            "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.size else None,
            "target_share_pct": round(100.0 * float(np.mean(np.array(reasons) == "TARGET")), 2),
            "stop_share_pct": round(100.0 * float(np.mean(np.array(reasons) == "STOP")), 2),
            "agree_with_codex_pct": round(
                100.0 * float(np.mean(np.array(reasons) == work["exit_reason"].to_numpy())), 2
            ),
        }

    print("\n=== outcomes re-resolved on independent data ===")
    print(f"{'path convention':16s} {'trades':>7} {'WR%':>7} {'PF':>8} {'net R':>9} {'TARGET%':>8} {'agree%':>7}")
    print("-" * 68)
    codex_pf = None
    for path, value in results.items():
        print(
            f"{path:16s} {value['trades']:>7} {value['win_rate_pct']:>7.2f} "
            f"{value['profit_factor']:>8.4f} {value['net_r']:>9.2f} "
            f"{value['target_share_pct']:>8.2f} {value['agree_with_codex_pct']:>7.2f}"
        )
    # Codex's own numbers on the same subset
    their_r = work["r"].to_numpy()
    tw, tl = their_r[their_r > 0], their_r[their_r <= 0]
    codex_pf = float(tw.sum() / -tl.sum())
    print(
        f"{'CODEX reported':16s} {len(work):>7} "
        f"{100.0 * tw.size / their_r.size:>7.2f} {codex_pf:>8.4f} {their_r.sum():>9.2f}"
        f"{'':>8} {'100.00':>7}"
    )

    out = ROOT / "outputs" / "CODEX_REPLICATION.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_codex_replication_v1",
                "purpose": "re-resolve Codex trade decisions on independent Dukascopy data",
                "ledger_trades": int(len(ledger)),
                "matched_trades": int(found.sum()),
                "entry_price_diff_pips_median": float(np.median(diff_pips)),
                "codex_reported_pf_on_matched": round(codex_pf, 4),
                "independent": results,
            },
            indent=2, sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
