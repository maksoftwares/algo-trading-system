from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_cme_options_surface import (
    build_daily_risk_reversal,
)
from eurusd_regime_specialists.neutral_cme_span_surface import (
    read_euu_span,
)


def _write_span(path: Path, *, is_settlement: str = "1") -> None:
    options: list[str] = []
    strikes = [
        1.0500,
        1.0600,
        1.0700,
        1.0800,
        1.0900,
        1.1000,
        1.1100,
        1.1200,
        1.1300,
    ]
    for index, strike in enumerate(strikes):
        call = max(1.10 - strike, 0) + 0.003 + index * 0.0001
        put = max(strike - 1.10, 0) + 0.003 - index * 0.00005
        call_delta = max(0.05, 0.85 - index * 0.075)
        put_delta = -(1.0 - call_delta)
        options.extend(
            [
                (
                    "<opt><cId>C{0}</cId><o>C</o><k>{1:.4f}</k>"
                    "<p>{2:.6f}</p><pq>0</pq><d>{3:.6f}</d>"
                    "<v>{4:.6f}</v></opt>"
                ).format(index, strike, call, call_delta, 0.08 + index * 0.001),
                (
                    "<opt><cId>P{0}</cId><o>P</o><k>{1:.4f}</k>"
                    "<p>{2:.6f}</p><pq>0</pq><d>{3:.6f}</d>"
                    "<v>{4:.6f}</v></opt>"
                ).format(index, strike, put, put_delta, 0.075 + index * 0.001),
            ]
        )
    options.append(
        "<opt><cId>CAB</cId><o>C</o><k>1.2000</k>"
        "<p>6.25</p><pq>1</pq><d>0.01</d><v>0.10</v></opt>"
    )
    xml = (
        "<spanFile><fileFormat>4.00</fileFormat>"
        "<created>202501021200</created><pointInTime>"
        "<date>20250102</date><isSetl>{}</isSetl><time>16:00</time>"
        "<run>1</run><clearingOrg><exch><oofPf>"
        "<pfId>22181</pfId><pfCode>EUU</pfCode><series>"
        "<pe>202502</pe><v>0.080000</v><setlDate>20250102</setlDate>"
        "<t>0.082192</t><ldot>20250201</ldot>"
        "<refPriceFlag>N</refPriceFlag><refPrice>1.100000</refPrice>"
        "<undC><exch>CME</exch><pfId>314</pfId><cId>144</cId>"
        "</undC>{}</series></oofPf></exch></clearingOrg>"
        "</pointInTime></spanFile>"
    ).format(is_settlement, "".join(options))
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("synthetic.spn", xml)


def _surface_config() -> dict[str, object]:
    return {
        "surface": {
            "minimum_dte": 20,
            "maximum_dte": 45,
            "target_dte": 30,
            "target_abs_delta": 0.25,
            "maximum_abs_delta_distance": 0.08,
            "minimum_call_put_pairs": 7,
        }
    }


def test_span_parser_normalizes_euu_and_excludes_cabinet_quote(
    tmp_path: Path,
):
    path = tmp_path / "settlement.zip"
    _write_span(path)
    frame, metadata = read_euu_span(path)
    assert len(frame) == 18
    assert metadata["is_settlement"] == "1"
    assert metadata["expiry_count"] == 1
    assert set(frame["span_quote_flag"]) == {"0"}
    assert frame["trade_date_utc"].iloc[0] == pd.Timestamp(
        "2025-01-02T00:00:00Z"
    )
    assert frame["expiry_date_utc"].iloc[0] == pd.Timestamp(
        "2025-02-01T00:00:00Z"
    )
    assert frame["underlying_contract_id"].iloc[0] == "144"


def test_non_settlement_sample_is_rejected_by_default(tmp_path: Path):
    path = tmp_path / "sample.zip"
    _write_span(path, is_settlement="0")
    with pytest.raises(ValueError, match="not a settlement file"):
        read_euu_span(path)
    frame, metadata = read_euu_span(
        path, require_settlement=False
    )
    assert len(frame) == 18
    assert metadata["is_settlement"] == "0"


def test_normalized_span_surface_feeds_frozen_rr_builder(
    tmp_path: Path,
):
    path = tmp_path / "settlement.zip"
    _write_span(path)
    frame, _ = read_euu_span(path)
    result = build_daily_risk_reversal(frame, _surface_config())
    assert len(result) == 1
    assert result.iloc[0]["side"] == "LONG"
    assert result.iloc[0]["call25_abs_delta"] == pytest.approx(
        0.25, abs=0.08
    )
    assert result.iloc[0]["put25_abs_delta"] == pytest.approx(
        0.25, abs=0.08
    )
