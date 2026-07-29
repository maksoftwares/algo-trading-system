from __future__ import annotations

from download_neutral_rate_differential import (
    build_audit,
    parse_ecb_csv,
    parse_treasury_xml,
)


def test_treasury_xml_parser_extracts_two_year_rate() -> None:
    payload = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
 xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
 <entry><content><m:properties>
  <d:NEW_DATE m:type="Edm.DateTime">2025-01-02T00:00:00</d:NEW_DATE>
  <d:BC_2YEAR m:type="Edm.Double">4.25</d:BC_2YEAR>
 </m:properties></content></entry>
</feed>"""
    frame = parse_treasury_xml(payload)
    assert len(frame) == 1
    assert frame.iloc[0]["us_treasury_2y_percent"] == 4.25


def test_ecb_csv_parser_binds_exact_series() -> None:
    payload = (
        b"KEY,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
        b"YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y,2025-01-02,2.125,A\n"
        b"YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3Y,2025-01-02,2.250,A\n"
    )
    frame = parse_ecb_csv(payload)
    assert len(frame) == 1
    assert frame.iloc[0]["ecb_euro_area_aaa_2y_percent"] == 2.125


def test_source_audit_contains_no_market_outcome() -> None:
    treasury = parse_treasury_xml(
        b"""<feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
 xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
 <entry><content><m:properties>
 <d:NEW_DATE>2025-01-02</d:NEW_DATE><d:BC_2YEAR>4.25</d:BC_2YEAR>
 </m:properties></content></entry></feed>"""
    )
    ecb = parse_ecb_csv(
        b"KEY,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
        b"YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y,2025-01-02,2.125,A\n"
    )
    audit = build_audit(treasury, ecb)
    assert audit["eurusd_prices_loaded"] is False
    assert audit["pnl_loaded"] is False
    assert audit["status"] == "SOURCE_ACCEPTED_FOR_OUTCOME_BLIND_CENSUS"
