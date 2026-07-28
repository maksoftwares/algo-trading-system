from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from download_neutral_dtcc_fx_options import (
    qualified_trade,
    sha256_file,
)


DEFAULT_RAW_ROOT = Path(
    "D:/AlgoTradingData/research/eurusd-neutral-dtcc-fx-options-v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/research/eurusd-neutral-dtcc-skew-v1"
)
DEFAULT_EURUSD_M5 = Path(
    "D:/AlgoTradingData/research/fx-multipair-portfolio-v1/"
    "bars/EURUSD_M5_BIDASK.parquet"
)
MINIMUM_TENOR_DAYS = 14
MAXIMUM_TENOR_DAYS = 60
MINIMUM_ABSOLUTE_LOG_MONEYNESS = 0.001
MAXIMUM_ABSOLUTE_LOG_MONEYNESS = 0.03
MAXIMUM_PAIR_TENOR_DIFFERENCE_DAYS = 7
MAXIMUM_PAIR_MONEYNESS_DIFFERENCE = 0.0025
MINIMUM_PAIRS_PER_SESSION = 3


def parse_strike(value: Any) -> float | None:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    try:
        strike = float(text)
    except ValueError:
        return None
    return strike if strike > 0 else None


def extract_trades(raw_root: Path) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for path in sorted((raw_root / "raw").glob("*.json")):
        stem_parts = path.stem.split("_")
        if len(stem_parts) != 2:
            continue
        report_date = pd.to_datetime(stem_parts[0], format="%Y%m%d")
        option_kind = stem_parts[1]
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload["tradeList"]:
            qualified = qualified_trade(
                row,
                option_kind,
                report_date,
            )
            if qualified is None:
                continue
            if not (
                MINIMUM_TENOR_DAYS
                <= qualified["tenor_days"]
                <= MAXIMUM_TENOR_DAYS
            ):
                continue
            if row.get("strikePriceCurrencyOrCurrencypair") != "EUR/USD":
                continue
            strike = parse_strike(row.get("strikePrice"))
            if strike is None:
                continue
            records.append(
                {
                    "report_date": report_date,
                    "available_time_utc": (
                        report_date + pd.Timedelta(days=1)
                    ).tz_localize("UTC"),
                    "option_kind": option_kind,
                    "dissemination_identifier": qualified[
                        "dissemination_identifier"
                    ],
                    "execution_timestamp": qualified[
                        "execution_timestamp"
                    ],
                    "dissemination_timestamp": qualified[
                        "dissemination_timestamp"
                    ],
                    "expiration_date": qualified["expiration_date"],
                    "tenor_days": qualified["tenor_days"],
                    "eur_notional": qualified["eur_notional"],
                    "usd_premium": qualified["usd_premium"],
                    "strike": strike,
                }
            )
    if not records:
        raise RuntimeError("No qualified DTCC option trades found")
    return (
        pd.DataFrame(records)
        .sort_values(
            [
                "dissemination_timestamp",
                "dissemination_identifier",
            ]
        )
        .drop_duplicates("dissemination_identifier", keep="last")
        .reset_index(drop=True)
    )


def attach_causal_spot(
    trades: pd.DataFrame, eurusd_m5_path: Path
) -> pd.DataFrame:
    bars = pd.read_parquet(
        eurusd_m5_path,
        columns=["timestamp_ms", "bid_close", "ask_close"],
    )
    bars["bar_start_utc"] = pd.to_datetime(
        bars["timestamp_ms"], unit="ms", utc=True
    )
    bars["spot_available_time_utc"] = (
        bars["bar_start_utc"] + pd.Timedelta(minutes=5)
    )
    bars["spot_mid"] = (
        bars["bid_close"].astype(float)
        + bars["ask_close"].astype(float)
    ) / 2.0
    joined = pd.merge_asof(
        trades.sort_values("execution_timestamp"),
        bars[
            ["spot_available_time_utc", "spot_mid"]
        ].sort_values("spot_available_time_utc"),
        left_on="execution_timestamp",
        right_on="spot_available_time_utc",
        direction="backward",
        allow_exact_matches=True,
        tolerance=pd.Timedelta(minutes=30),
    )
    joined = joined[joined["spot_mid"].notna()].copy()
    joined["log_moneyness"] = np.log(
        joined["strike"] / joined["spot_mid"]
    )
    joined["absolute_log_moneyness"] = joined[
        "log_moneyness"
    ].abs()
    joined["premium_rate"] = (
        joined["usd_premium"].astype(float)
        / (
            joined["eur_notional"].astype(float)
            * joined["spot_mid"].astype(float)
        )
    )
    is_otm = (
        joined["option_kind"].eq("CALL")
        & joined["log_moneyness"].gt(0)
    ) | (
        joined["option_kind"].eq("PUT")
        & joined["log_moneyness"].lt(0)
    )
    joined = joined[
        is_otm
        & joined["absolute_log_moneyness"].between(
            MINIMUM_ABSOLUTE_LOG_MONEYNESS,
            MAXIMUM_ABSOLUTE_LOG_MONEYNESS,
            inclusive="both",
        )
        & joined["premium_rate"].between(
            0,
            0.20,
            inclusive="neither",
        )
    ].copy()
    return joined.sort_values(
        ["report_date", "option_kind", "dissemination_identifier"]
    ).reset_index(drop=True)


def match_session(frame: pd.DataFrame) -> list[dict[str, Any]]:
    calls = frame[frame["option_kind"].eq("CALL")]
    puts = frame[frame["option_kind"].eq("PUT")]
    candidates: list[tuple[float, str, str, Any, Any]] = []
    for call_index, call in calls.iterrows():
        for put_index, put in puts.iterrows():
            tenor_difference = abs(
                float(call["tenor_days"]) - float(put["tenor_days"])
            )
            moneyness_difference = abs(
                float(call["absolute_log_moneyness"])
                - float(put["absolute_log_moneyness"])
            )
            if (
                tenor_difference
                > MAXIMUM_PAIR_TENOR_DIFFERENCE_DAYS
                or moneyness_difference
                > MAXIMUM_PAIR_MONEYNESS_DIFFERENCE
            ):
                continue
            score = (
                tenor_difference
                / MAXIMUM_PAIR_TENOR_DIFFERENCE_DAYS
                + moneyness_difference
                / MAXIMUM_PAIR_MONEYNESS_DIFFERENCE
            )
            candidates.append(
                (
                    score,
                    str(call["dissemination_identifier"]),
                    str(put["dissemination_identifier"]),
                    call_index,
                    put_index,
                )
            )
    used_calls: set[Any] = set()
    used_puts: set[Any] = set()
    pairs: list[dict[str, Any]] = []
    for score, _, _, call_index, put_index in sorted(candidates):
        if call_index in used_calls or put_index in used_puts:
            continue
        call = calls.loc[call_index]
        put = puts.loc[put_index]
        used_calls.add(call_index)
        used_puts.add(put_index)
        pairs.append(
            {
                "report_date": call["report_date"],
                "available_time_utc": call["available_time_utc"],
                "call_id": call["dissemination_identifier"],
                "put_id": put["dissemination_identifier"],
                "call_execution_timestamp": call[
                    "execution_timestamp"
                ],
                "put_execution_timestamp": put[
                    "execution_timestamp"
                ],
                "call_tenor_days": call["tenor_days"],
                "put_tenor_days": put["tenor_days"],
                "call_absolute_log_moneyness": call[
                    "absolute_log_moneyness"
                ],
                "put_absolute_log_moneyness": put[
                    "absolute_log_moneyness"
                ],
                "call_premium_rate": call["premium_rate"],
                "put_premium_rate": put["premium_rate"],
                "pair_score": score,
                "pair_log_premium_skew": (
                    np.log(float(call["premium_rate"]))
                    - np.log(float(put["premium_rate"]))
                ),
            }
        )
    return pairs


def build_daily_skew(
    trades: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    pair_records: list[dict[str, Any]] = []
    for _, session in trades.groupby("report_date", sort=True):
        pair_records.extend(match_session(session))
    pairs = pd.DataFrame(pair_records)
    if pairs.empty:
        raise RuntimeError("No matched DTCC skew pairs found")
    daily = (
        pairs.groupby("report_date", as_index=False)
        .agg(
            available_time_utc=("available_time_utc", "first"),
            matched_pairs=("pair_log_premium_skew", "size"),
            daily_log_premium_skew=(
                "pair_log_premium_skew",
                "median",
            ),
            median_pair_score=("pair_score", "median"),
        )
        .sort_values("report_date")
    )
    daily["source_eligible"] = daily["matched_pairs"].ge(
        MINIMUM_PAIRS_PER_SESSION
    )
    return daily, pairs


def build(
    raw_root: Path,
    output_root: Path,
    eurusd_m5_path: Path,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    extracted = extract_trades(raw_root)
    surface_trades = attach_causal_spot(extracted, eurusd_m5_path)
    daily, pairs = build_daily_skew(surface_trades)

    trades_path = output_root / "QUALIFIED_OTM_TRADES.parquet"
    pairs_path = output_root / "MATCHED_PAIRS.parquet"
    daily_path = output_root / "DTCC_EURUSD_DAILY_SKEW.parquet"
    surface_trades.to_parquet(trades_path, index=False)
    pairs.to_parquet(pairs_path, index=False)
    daily.to_parquet(daily_path, index=False)

    parent_manifest = raw_root / "MANIFEST.json"
    eligible = daily[daily["source_eligible"]]
    manifest = {
        "campaign": "eurusd-neutral-dtcc-skew-v1",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "DTCC CFTC public EUR/USD OTC vanilla options",
        "source_dashboard": "https://pddata.dtcc.com/ppd/search",
        "parent_manifest": {
            "path": str(parent_manifest),
            "sha256": sha256_file(parent_manifest),
        },
        "eurusd_m5_source": {
            "path": str(eurusd_m5_path),
            "sha256": sha256_file(eurusd_m5_path),
            "spot_rule": (
                "Mid-close of latest M5 bar completed before option "
                "execution, maximum age 30 minutes"
            ),
        },
        "surface_contract": {
            "minimum_tenor_days": MINIMUM_TENOR_DAYS,
            "maximum_tenor_days": MAXIMUM_TENOR_DAYS,
            "minimum_absolute_log_moneyness": (
                MINIMUM_ABSOLUTE_LOG_MONEYNESS
            ),
            "maximum_absolute_log_moneyness": (
                MAXIMUM_ABSOLUTE_LOG_MONEYNESS
            ),
            "otm_only": True,
            "maximum_pair_tenor_difference_days": (
                MAXIMUM_PAIR_TENOR_DIFFERENCE_DAYS
            ),
            "maximum_pair_moneyness_difference": (
                MAXIMUM_PAIR_MONEYNESS_DIFFERENCE
            ),
            "minimum_pairs_per_session": (
                MINIMUM_PAIRS_PER_SESSION
            ),
            "pairing": (
                "Deterministic greedy minimum normalized tenor-plus-"
                "absolute-moneyness distance without reuse"
            ),
            "pair_skew": (
                "log(call USD premium per spot-adjusted EUR notional) "
                "minus log(matched put premium rate)"
            ),
            "daily_skew": "median pair skew",
        },
        "credentials_used": False,
        "cost_usd": 0.0,
        "qualified_otm_trades": len(surface_trades),
        "qualified_otm_calls": int(
            surface_trades["option_kind"].eq("CALL").sum()
        ),
        "qualified_otm_puts": int(
            surface_trades["option_kind"].eq("PUT").sum()
        ),
        "matched_pairs": len(pairs),
        "daily_sessions": len(daily),
        "eligible_daily_sessions": len(eligible),
        "first_eligible_date": (
            eligible["report_date"].min().date().isoformat()
        ),
        "last_eligible_date": (
            eligible["report_date"].max().date().isoformat()
        ),
        "artifacts": {
            "qualified_trades": {
                "path": str(trades_path),
                "sha256": sha256_file(trades_path),
            },
            "matched_pairs": {
                "path": str(pairs_path),
                "sha256": sha256_file(pairs_path),
            },
            "daily_skew": {
                "path": str(daily_path),
                "sha256": sha256_file(daily_path),
            },
        },
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["manifest_sha256"] = sha256_file(manifest_path)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    parser.add_argument(
        "--eurusd-m5-path", type=Path, default=DEFAULT_EURUSD_M5
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build(
        args.raw_root,
        args.output_root,
        args.eurusd_m5_path,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
