from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .research import PACKAGE_ROOT, sha256_file


FAMILY = "N12_NEUTRAL_CME_EURUSD_25D_RISK_REVERSAL"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_cme_options_surface"
REQUIRED_COLUMNS = (
    "Trade Date",
    "Exchange Code",
    "Asset Class",
    "Product Code",
    "Product Type",
    "Put/Call",
    "Strike Price",
    "Contract Year",
    "Contract Month",
    "Settlement",
    "Open Interest",
    "Total Volume",
    "Delta",
    "Implied Volatility",
    "Last Trade Date",
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_cme_options_surface.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_CME_OPTIONS_SURFACE_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_historical_surface_outcome_pass") is not True:
        raise RuntimeError("CME options-surface contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "CME options-surface preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def read_euu_eod(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            "Licensed CME DataMine EUR/USD options history is missing: "
            f"{path}"
        )
    return prepare_euu_eod(pd.read_csv(path, compression="infer", dtype=str))


def prepare_euu_eod(raw: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(
            "CME EUU EOD input is missing required columns: "
            + ", ".join(missing)
        )
    frame = raw.loc[:, REQUIRED_COLUMNS].copy()
    frame = frame[
        frame["Exchange Code"].eq("XCME")
        & frame["Asset Class"].str.upper().eq("FX")
        & frame["Product Code"].eq("EUU")
        & frame["Product Type"].eq("OPT")
        & frame["Put/Call"].isin(("C", "P"))
    ].copy()
    frame["trade_date_utc"] = pd.to_datetime(
        frame["Trade Date"], format="%Y%m%d", utc=True, errors="coerce"
    )
    frame["expiry_date_utc"] = pd.to_datetime(
        frame["Last Trade Date"], format="%Y%m%d", utc=True, errors="coerce"
    )
    frame["strike"] = (
        pd.to_numeric(frame["Strike Price"], errors="coerce") / 10_000.0
    )
    frame["settlement"] = pd.to_numeric(
        frame["Settlement"], errors="coerce"
    )
    frame["open_interest"] = pd.to_numeric(
        frame["Open Interest"], errors="coerce"
    ).fillna(0.0)
    frame["total_volume"] = pd.to_numeric(
        frame["Total Volume"], errors="coerce"
    ).fillna(0.0)
    frame["reported_delta"] = pd.to_numeric(
        frame["Delta"], errors="coerce"
    )
    frame["reported_iv"] = pd.to_numeric(
        frame["Implied Volatility"], errors="coerce"
    )
    percent_iv = frame["reported_iv"] > 3.0
    frame.loc[percent_iv, "reported_iv"] /= 100.0
    frame = frame.dropna(
        subset=[
            "trade_date_utc",
            "expiry_date_utc",
            "strike",
            "settlement",
        ]
    )
    frame = frame[
        (frame["strike"] > 0)
        & (frame["settlement"] >= 0)
        & (frame["expiry_date_utc"] > frame["trade_date_utc"])
    ].copy()
    frame["dte"] = (
        frame["expiry_date_utc"] - frame["trade_date_utc"]
    ).dt.total_seconds() / 86_400.0
    frame = (
        frame.sort_values(
            [
                "trade_date_utc",
                "expiry_date_utc",
                "strike",
                "Put/Call",
            ]
        )
        .drop_duplicates(
            [
                "trade_date_utc",
                "expiry_date_utc",
                "strike",
                "Put/Call",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )
    return frame


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def black76_price(
    forward: float,
    strike: float,
    years: float,
    volatility: float,
    discount: float,
    put_call: str,
) -> float:
    if (
        forward <= 0
        or strike <= 0
        or years <= 0
        or volatility <= 0
        or discount <= 0
    ):
        return float("nan")
    root_t = math.sqrt(years)
    d1 = (
        math.log(forward / strike)
        + 0.5 * volatility * volatility * years
    ) / (volatility * root_t)
    d2 = d1 - volatility * root_t
    if put_call == "C":
        return discount * (
            forward * _normal_cdf(d1)
            - strike * _normal_cdf(d2)
        )
    if put_call == "P":
        return discount * (
            strike * _normal_cdf(-d2)
            - forward * _normal_cdf(-d1)
        )
    raise ValueError(f"Unsupported put/call value: {put_call!r}")


def black76_abs_delta(
    forward: float,
    strike: float,
    years: float,
    volatility: float,
    put_call: str,
) -> float:
    root_t = math.sqrt(years)
    d1 = (
        math.log(forward / strike)
        + 0.5 * volatility * volatility * years
    ) / (volatility * root_t)
    call_delta = _normal_cdf(d1)
    if put_call == "C":
        return call_delta
    if put_call == "P":
        return 1.0 - call_delta
    raise ValueError(f"Unsupported put/call value: {put_call!r}")


def implied_volatility(
    price: float,
    forward: float,
    strike: float,
    years: float,
    discount: float,
    put_call: str,
) -> float:
    intrinsic = discount * (
        max(forward - strike, 0.0)
        if put_call == "C"
        else max(strike - forward, 0.0)
    )
    if price < intrinsic - 1e-8 or price <= 0:
        return float("nan")
    low = 1e-4
    high = 5.0
    high_price = black76_price(
        forward, strike, years, high, discount, put_call
    )
    if not math.isfinite(high_price) or high_price < price:
        return float("nan")
    for _ in range(80):
        mid = (low + high) / 2.0
        mid_price = black76_price(
            forward, strike, years, mid, discount, put_call
        )
        if mid_price < price:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def infer_forward_discount(expiry: pd.DataFrame) -> tuple[float, float]:
    calls = expiry[expiry["Put/Call"].eq("C")][
        ["strike", "settlement"]
    ].rename(columns={"settlement": "call"})
    puts = expiry[expiry["Put/Call"].eq("P")][
        ["strike", "settlement"]
    ].rename(columns={"settlement": "put"})
    pairs = calls.merge(puts, on="strike", how="inner")
    if len(pairs) < 3:
        raise ValueError("At least three call/put strike pairs are required")
    x = pairs["strike"].to_numpy(dtype=float)
    y = (pairs["call"] - pairs["put"]).to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    discount = -float(slope)
    if not 0.50 <= discount <= 1.50:
        raise ValueError(
            f"Put-call parity implied invalid discount {discount:.6f}"
        )
    forward = float(intercept / discount)
    if not math.isfinite(forward) or forward <= 0:
        raise ValueError("Put-call parity implied invalid forward")
    return forward, discount


def conservative_availability_utc(
    trade_date_utc: pd.Timestamp,
) -> pd.Timestamp:
    next_weekday = trade_date_utc + pd.offsets.BDay(1)
    local_final = pd.Timestamp(next_weekday.date()).tz_localize(
        "America/Chicago"
    ) + pd.Timedelta(hours=10)
    final_utc = local_final.tz_convert("UTC")
    return final_utc.ceil("D")


def _option_iv_and_delta(
    row: pd.Series,
    forward: float,
    discount: float,
    years: float,
) -> tuple[float, float]:
    iv = float(row["reported_iv"])
    if not math.isfinite(iv) or iv <= 0:
        iv = implied_volatility(
            float(row["settlement"]),
            forward,
            float(row["strike"]),
            years,
            discount,
            str(row["Put/Call"]),
        )
    if not math.isfinite(iv) or iv <= 0:
        return float("nan"), float("nan")
    delta = float(row["reported_delta"])
    if not math.isfinite(delta) or not 0 < abs(delta) < 1:
        delta = black76_abs_delta(
            forward,
            float(row["strike"]),
            years,
            iv,
            str(row["Put/Call"]),
        )
    return iv, abs(delta)


def _nearest_delta_row(
    frame: pd.DataFrame,
    put_call: str,
    target: float,
    maximum_distance: float,
) -> pd.Series | None:
    side = frame[
        frame["Put/Call"].eq(put_call)
        & frame["surface_iv"].notna()
        & frame["surface_abs_delta"].notna()
    ].copy()
    if side.empty:
        return None
    side["delta_distance"] = (
        side["surface_abs_delta"] - target
    ).abs()
    side = side.sort_values(
        ["delta_distance", "strike"],
        ascending=[True, put_call == "C"],
    )
    best = side.iloc[0]
    if float(best["delta_distance"]) > maximum_distance:
        return None
    return best


def build_daily_risk_reversal(
    prepared: pd.DataFrame,
    cfg: dict[str, Any] | None = None,
) -> pd.DataFrame:
    config = load_config() if cfg is None else cfg
    surface = config["surface"]
    minimum_dte = float(surface["minimum_dte"])
    maximum_dte = float(surface["maximum_dte"])
    target_dte = float(surface["target_dte"])
    target_delta = float(surface["target_abs_delta"])
    maximum_delta_distance = float(
        surface["maximum_abs_delta_distance"]
    )
    minimum_pairs = int(surface["minimum_call_put_pairs"])
    rows: list[dict[str, Any]] = []
    keys = ["trade_date_utc", "expiry_date_utc"]
    for (trade_date, expiry_date), expiry in prepared.groupby(
        keys, sort=True
    ):
        dte = float(expiry["dte"].iloc[0])
        if not minimum_dte <= dte <= maximum_dte:
            continue
        calls = expiry[expiry["Put/Call"].eq("C")]["strike"]
        puts = expiry[expiry["Put/Call"].eq("P")]["strike"]
        pair_count = int(len(set(calls) & set(puts)))
        if pair_count < minimum_pairs:
            continue
        try:
            forward, discount = infer_forward_discount(expiry)
        except ValueError:
            continue
        years = dte / 365.0
        enriched = expiry.copy()
        values = enriched.apply(
            _option_iv_and_delta,
            axis=1,
            args=(forward, discount, years),
            result_type="expand",
        )
        enriched["surface_iv"] = values[0]
        enriched["surface_abs_delta"] = values[1]
        call25 = _nearest_delta_row(
            enriched,
            "C",
            target_delta,
            maximum_delta_distance,
        )
        put25 = _nearest_delta_row(
            enriched,
            "P",
            target_delta,
            maximum_delta_distance,
        )
        if call25 is None or put25 is None:
            continue
        rr25 = 100.0 * (
            float(call25["surface_iv"])
            - float(put25["surface_iv"])
        )
        rows.append(
            {
                "trade_date_utc": trade_date,
                "expiry_date_utc": expiry_date,
                "dte": dte,
                "dte_distance": abs(dte - target_dte),
                "forward": forward,
                "discount": discount,
                "call_put_pairs": pair_count,
                "call25_strike": float(call25["strike"]),
                "put25_strike": float(put25["strike"]),
                "call25_abs_delta": float(
                    call25["surface_abs_delta"]
                ),
                "put25_abs_delta": float(
                    put25["surface_abs_delta"]
                ),
                "call25_iv": float(call25["surface_iv"]),
                "put25_iv": float(put25["surface_iv"]),
                "rr25_vol_points": rr25,
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "trade_date_utc",
                "expiry_date_utc",
                "availability_utc",
                "rr25_vol_points",
                "side",
            ]
        )
    result = pd.DataFrame(rows).sort_values(
        ["trade_date_utc", "dte_distance", "expiry_date_utc"]
    )
    result = result.drop_duplicates(
        "trade_date_utc", keep="first"
    ).drop(columns="dte_distance")
    result["availability_utc"] = result["trade_date_utc"].map(
        conservative_availability_utc
    )
    result["side"] = np.select(
        [
            result["rr25_vol_points"] > 0,
            result["rr25_vol_points"] < 0,
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    result["family"] = FAMILY
    return result.reset_index(drop=True)
