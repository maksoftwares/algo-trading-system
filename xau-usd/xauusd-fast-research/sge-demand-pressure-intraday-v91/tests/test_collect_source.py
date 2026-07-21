from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sge_v91_collect", ROOT / "collect_source.py")
assert SPEC is not None and SPEC.loader is not None
COLLECT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COLLECT
SPEC.loader.exec_module(COLLECT)


def test_parse_detail_links_deduplicates_and_orders() -> None:
    html = """
    <a href="/data_DailyReport/10000902">A</a>
    <a href="/data_DailyReport/542671">B</a>
    <a href="/data_DailyReport/10000902">A2</a>
    """
    assert COLLECT.parse_detail_links(html) == ["542671", "10000902"]


def test_parse_historical_table_and_alias_contract() -> None:
    html = """
    <h3>Shanghai Gold Price(May 27, 2022)</h3>
    <p>Date: 2022-05-27</p>
    <table>
      <tr><td>Contract</td><td>Open</td><td>Highest</td><td>Lowest</td>
      <td>Close</td><td>Up/ Down (yuan)</td><td>Up/ Down (%)</td>
      <td>Weighted Average Price</td><td>Volume (Kg)</td><td>Amount (yuan)</td>
      <td>Open Interest (Lot)</td><td>Direction</td><td>Delivery Volume (Lot)</td></tr>
      <tr><td>Au9999</td><td>400</td><td>403</td><td>399</td><td>402.5</td>
      <td>1.6</td><td>0.4%</td><td>402.1</td><td>12,369.72</td>
      <td>4912419070</td><td>-</td><td></td><td></td></tr>
    </table>
    """
    raw = COLLECT.parse_historical_detail(html, "10000902")
    frame = COLLECT._canonical_columns(raw)
    assert frame.loc[0, "date"] == pd.Timestamp("2022-05-27")
    assert frame.loc[0, "contract"] == "Au99.99"
    assert frame.loc[0, "volume_kg"] == 12369.72
    assert frame.loc[0, "change_percent"] == 0.4


def test_maximum_modern_page_defaults_to_one() -> None:
    assert COLLECT.maximum_modern_page("<html></html>") == 1
    html = "gotoPage('/h5_data_DailyReport?x&p=','3')"
    assert COLLECT.maximum_modern_page(html) == 3


def test_known_non_contract_report_ids_are_exactly_registered() -> None:
    assert COLLECT.KNOWN_NON_CONTRACT_REPORT_IDS == {
        "543406",
        "543424",
        "10000802",
    }
    assert COLLECT.KNOWN_MALFORMED_REPORT_IDS == {"543277"}
    assert COLLECT.KNOWN_TITLE_DATE_OVERRIDES == {"542439": "2017-04-18"}
    assert COLLECT.KNOWN_TITLE_MONTH_ALIASES == {"Feburary": "February"}


def test_multiline_historical_header_is_composed_without_duplicates() -> None:
    html = """
    <h3>Shanghai Gold Price(February 16, 2017)</h3>
    <p>Date: 2017-02-16</p>
    <table>
      <tr><td>Contract</td><td>Open</td><td>Highest</td><td>Lowest</td><td>Close</td>
      <td>Up/</td><td>Up/</td><td>Weighted Average</td><td>Volume</td>
      <td>Amount</td><td>Open Interest</td><td>Direction</td><td>Delivery Volume</td></tr>
      <tr><td>Contract</td><td>Open</td><td>Highest</td><td>Lowest</td><td>Close</td>
      <td>Down</td><td>Down</td><td>Price</td><td>(Kg)</td><td>(yuan)</td>
      <td>(Lot)</td><td>Direction</td><td>(Lot)</td></tr>
      <tr><td>Contract</td><td>Open</td><td>Highest</td><td>Lowest</td><td>Close</td>
      <td>(yuan)</td><td>(%)</td><td></td><td></td><td></td><td></td>
      <td>Direction</td><td></td></tr>
      <tr><td>Au9999</td><td>274</td><td>275</td><td>272</td><td>274.9</td>
      <td>1.53</td><td>0.56%</td><td>274.96</td><td>32,061</td>
      <td>8770721945</td><td>-</td><td></td><td></td></tr>
    </table>
    """
    raw = COLLECT.parse_historical_detail(html, "542316")
    assert raw.columns.is_unique
    frame = COLLECT._canonical_columns(raw)
    assert frame.loc[0, "change_yuan"] == 1.53
    assert frame.loc[0, "change_percent"] == 0.56
    assert frame.loc[0, "weighted_average"] == 274.96


def test_legacy_variety_header_is_normalized() -> None:
    html = """
    <h3>Shanghai Gold Price (July 1, 2016)</h3>
    <p>Date: 2016-07-01</p>
    <table>
      <tr><td>Variety</td><td>Open</td><td>High</td><td>Low</td><td>Close</td>
      <td>Up/Down(yuan)</td><td>Weighted Average Price</td><td>Volume(Kg)</td>
      <td>Amount(yuan)</td><td>Open Interest</td><td>Direction</td>
      <td>Delivery Volume</td></tr>
      <tr><td>Au9999</td><td>282.95</td><td>286.37</td><td>281.90</td>
      <td>285.89</td><td>4.39</td><td>285.27</td><td>21,480.50</td>
      <td>5995059656.40</td><td>-</td><td></td><td></td></tr>
    </table>
    """
    raw = COLLECT.parse_historical_detail(html, "539185")
    frame = COLLECT._canonical_columns(raw)
    assert frame.loc[0, "contract"] == "Au99.99"
    assert frame.loc[0, "high"] == 286.37
    assert frame.loc[0, "volume_kg"] == 21480.5


def test_bare_second_up_down_column_is_percent_when_yuan_is_present() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2017-04-14"],
            "Contract": ["Au9999"],
            "Close": [286.5],
            "Up/ Down (yuan)": [1.2],
            "Up/ Down": ["0.42%"],
            "Volume (Kg)": [1000],
            "source_article_id": ["542595"],
            "source_type": ["historical_detail"],
        }
    )
    normalized = COLLECT._canonical_columns(frame)
    assert normalized.loc[0, "change_yuan"] == 1.2
    assert normalized.loc[0, "change_percent"] == 0.42


def test_headerless_standard_contract_table_uses_registered_position_order() -> None:
    html = """
    <h3>Shanghai Gold Price(July 18, 2022)</h3>
    <p>Date: 2022-07-18</p>
    <table>
      <tr><td>Au9999</td><td>404</td><td>406</td><td>400.7</td><td>403</td>
      <td>0.31</td><td>0.08%</td><td>402.66</td><td>10,183.06</td>
      <td>4021039000</td><td>-</td><td></td><td></td></tr>
    </table>
    """
    raw = COLLECT.parse_historical_detail(html, "10000868")
    normalized = COLLECT._canonical_columns(raw)
    assert normalized.loc[0, "contract"] == "Au99.99"
    assert normalized.loc[0, "close"] == 403
    assert normalized.loc[0, "change_percent"] == 0.08


def test_historical_title_date_overrides_incorrect_metadata_date() -> None:
    html = """
    <h3>Shanghai Gold Price (July 25, 2016)</h3>
    <p>Date: 2016-09-19</p>
    <table>
      <tr><td>Variety</td><td>Open</td><td>High</td><td>Low</td><td>Close</td>
      <td>Up/Down(yuan)</td><td>Weighted Average Price</td><td>Volume(Kg)</td>
      <td>Amount(yuan)</td><td>Open Interest</td><td>Direction</td>
      <td>Delivery Volume</td></tr>
      <tr><td>Au9999</td><td>282</td><td>286</td><td>281</td><td>285</td>
      <td>4</td><td>284</td><td>1000</td><td>284000000</td><td>-</td>
      <td></td><td></td></tr>
    </table>
    """
    raw = COLLECT.parse_historical_detail(html, "539600")
    assert raw.loc[0, "Date"] == "2016-07-25"


def test_non_contract_footer_is_removed_and_direction_is_canonical() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2023-05-25", "2023-05-25"],
            "Contract": ["Au(T+D)", "*Please note that volume is two-way."],
            "Close": [448.1, None],
            "Volume (Kg)": [42000, None],
            "Direction": ["Short to Long", ""],
            "source_article_id": ["10001468", "10001468"],
            "source_type": ["historical_detail", "historical_detail"],
        }
    )
    normalized = COLLECT._canonical_columns(frame)
    assert normalized["contract"].tolist() == ["Au(T+D)"]
    assert normalized["direction"].tolist() == ["short_to_long"]
