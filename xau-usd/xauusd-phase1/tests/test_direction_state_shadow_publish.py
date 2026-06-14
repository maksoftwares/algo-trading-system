from __future__ import annotations

from pathlib import Path
import csv
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPERTS = ROOT / "mt5" / "Experts"
INCLUDE = ROOT / "mt5" / "Include" / "DirectionStateShadow.mqh"

A2 = EXPERTS / "Phase2ExperimentalDemoExecutor.mq5"
A3_T1 = EXPERTS / "Account3RoundRetestGuardedExecutor.mq5"
A3_T2 = EXPERTS / "Account3RoundRetestStructuredExecutor.mq5"
PUBLISHER = EXPERTS / "DirectionStatePublisher.mq5"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_body(text: str, name: str) -> str:
    marker = f"{name}("
    start = text.index(marker)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[brace : index + 1]
    raise AssertionError(f"could not extract {name}")


def test_direction_state_publisher_is_file_common_and_non_trading():
    text = _text(PUBLISHER)

    assert "CopyRates(InpSymbol, InpTimeframe, 1" in text
    assert "FILE_COMMON" in text
    assert "dirstate_xauusd.csv" in text
    assert "dirstate_xauusd_history.csv" in text
    assert "InpEmaFast = 12" in text
    assert "InpEmaSlow = 34" in text
    assert "InpSlopeBars = 6" in text
    assert "InpEfficiencyRatioBars = 12" in text
    assert "InpEfficiencyRatioFlat = 0.30" in text
    assert "InpEfficiencyRatioStrong = 0.50" in text

    forbidden_terms = [
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "trade.Buy",
        "trade.Sell",
        "PositionOpen",
        "PositionModify",
        "PositionClose",
        "TRADE_ACTION",
        "MqlTradeRequest",
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
        "OrderDelete",
    ]
    for term in forbidden_terms:
        assert term not in text


def test_direction_state_reader_uses_common_file_and_default_fallbacks():
    text = _text(INCLUDE)

    assert "FILE_COMMON" in text
    assert "DirectionStateShadowFieldsForLog" in text
    assert 'direction_text = "0";' in text
    assert 'regime_text = "UNKNOWN";' in text
    assert 'strength_text = "0.000";' in text


def test_consumers_append_direction_state_columns_to_signal_and_order_logs():
    for path in (A2, A3_T1, A3_T2):
        text = _text(path)
        assert "#include <DirectionStateShadow.mqh>" in text
        assert 'input string InpDirectionStateFileName = "dirstate_xauusd.csv";' in text
        assert '"dirstate_direction"' in text
        assert '"dirstate_regime"' in text
        assert '"dirstate_strength"' in text
        assert "DirectionStateShadowFieldsForLog" in text


def test_direction_state_is_not_read_by_any_guard_function():
    guard_cases = (
        (A2, "TradingGuardsPass"),
        (A3_T1, "TradingGuardsPass"),
        (A3_T2, "TradingGuardsPass"),
    )
    for path, function_name in guard_cases:
        body = _function_body(_text(path), function_name)
        assert "DirectionState" not in body
        assert "dirstate_" not in body


def test_direction_state_values_are_never_used_in_conditions():
    for path in (A2, A3_T1, A3_T2):
        for line in _text(path).splitlines():
            if "dirstate_" not in line and "DirectionStateShadowFieldsForLog" not in line:
                continue
            stripped = line.strip()
            assert not stripped.startswith("if(")
            assert not stripped.startswith("if (")
            assert "&&" not in stripped
            assert "||" not in stripped


def test_direction_state_scoreboard_groups_closed_trades_by_regime(tmp_path: Path):
    module = _load_scoreboard_module()
    order_log = tmp_path / "tier1_bestea_order_log_xauusd.csv"
    trades = tmp_path / "trades.csv"
    _write_csv(
        order_log,
        ["magic", "action", "order_ticket", "deal_ticket", "dirstate_direction", "dirstate_regime", "dirstate_strength"],
        [
            {
                "magic": "920101",
                "action": "ORDER_SEND_OK",
                "order_ticket": "111",
                "deal_ticket": "222",
                "dirstate_direction": "1",
                "dirstate_regime": "UP",
                "dirstate_strength": "0.420",
            }
        ],
    )
    _write_csv(
        trades,
        ["magic", "state", "profit_aed", "entry_order", "entry_deal"],
        [{"magic": "920101", "state": "CLOSED", "profit_aed": "12.50", "entry_order": "111", "entry_deal": "222"}],
    )

    payload = module.generate_direction_state_shadow_scoreboard(
        tmp_path,
        order_logs=[order_log],
        trade_history_csv=trades,
        output_json=tmp_path / "scoreboard.json",
    )

    up_row = next(row for row in payload["scoreboard"] if row["magic"] == "920101" and row["regime"] == "UP")
    assert up_row["closed_trades"] == 1
    assert up_row["wins"] == 1
    assert up_row["win_rate_pct"] == 100.0
    assert up_row["pnl_aed"] == 12.5
    assert up_row["evidence_status"] == "READY"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_scoreboard_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_direction_state_shadow_scoreboard.py"
    spec = importlib.util.spec_from_file_location("generate_direction_state_shadow_scoreboard", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_direction_state_shadow_scoreboard"] = module
    spec.loader.exec_module(module)
    return module
