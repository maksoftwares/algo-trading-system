from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "run_crossfeed_veto_audit.py"


def load_script():
    spec = importlib.util.spec_from_file_location("crossfeed_veto_audit_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Tick:
    def __init__(self, timestamp_ms: int, bid: float, ask: float, source: str, row: int):
        self.timestamp_ms = timestamp_ms
        self.bid = bid
        self.ask = ask
        self.source_file_id = source
        self.source_row_index = row


class Decoder:
    @staticmethod
    def decode_payload(raw: bytes, symbol: str, source_file_id: str):
        assert symbol == "XAUUSD"
        payload = json.loads(raw)
        return [
            Tick(row[0], row[1], row[2], source_file_id, index)
            for index, row in enumerate(payload["ticks"])
        ]


def hour_file(root: Path, timestamp_ms: int) -> Path:
    stamp = datetime.fromtimestamp(timestamp_ms / 1000.0, UTC)
    path = (
        root
        / f"year={stamp.year:04d}"
        / f"month={stamp.month:02d}"
        / f"{stamp:%Y%m%d%H}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_quote_store_selects_first_quote_at_or_after(tmp_path: Path):
    module = load_script()
    base = int(datetime(2026, 8, 25, 12, tzinfo=UTC).timestamp() * 1000)
    path = hour_file(tmp_path, base)
    path.write_text(
        json.dumps(
            {"ticks": [[base - 1, 100.0, 100.1], [base + 7, 100.2, 100.3]]}
        ),
        encoding="utf-8",
    )
    store = module.DukascopyQuoteStore(tmp_path, Decoder())
    quote = store.at_or_after(base, maximum_lag_ms=10)
    assert quote is not None
    assert quote["timestamp_ms"] == base + 7
    assert quote["lag_ms"] == 7
    assert quote["bid"] == 100.2


def test_quote_store_rejects_quote_beyond_lag_limit(tmp_path: Path):
    module = load_script()
    base = int(datetime(2026, 8, 25, 12, tzinfo=UTC).timestamp() * 1000)
    path = hour_file(tmp_path, base)
    path.write_text(
        json.dumps({"ticks": [[base + 11, 100.0, 100.1]]}), encoding="utf-8"
    )
    store = module.DukascopyQuoteStore(tmp_path, Decoder())
    assert store.at_or_after(base, maximum_lag_ms=10) is None


def test_profit_factor_and_closed_drawdown():
    module = load_script()
    import pandas as pd

    frame = pd.DataFrame(
        {
            "trade_id": ["a", "b", "c"],
            "runtime_exit_time_ms": [1, 2, 3],
            "pnl": [10.0, -4.0, -8.0],
        }
    )
    assert module.profit_factor(frame["pnl"]) == 10.0 / 12.0
    assert module.closed_drawdown(frame, "pnl") == 12.0


def test_timestamp_ms_is_independent_of_pandas_storage_resolution():
    module = load_script()
    assert module.timestamp_ms("2021-01-04T16:20:00Z") == 1_609_777_200_000


def test_committed_crossfeed_result_preserves_locked_invariants():
    payload = json.loads((ROOT / "CROSSFEED_VETO_AUDIT.json").read_text())
    assert payload["coverage"]["runtime_trades"] == 1_390
    assert payload["coverage"]["covered_trades"] == 1_366
    assert payload["coverage"]["covered_veto_trades"] == 12
    assert payload["diagnostics"]["crossfeed_mechanism_support"] is True
    assert all(payload["diagnostics"]["checks"].values())
    assert payload["diagnostics"]["deployment_authorized"] is False
    assert payload["method"]["causal_strategy_replay"] is False
    assert payload["dukascopy_veto_cohort"]["net_pnl_usd"] < 0.0
    assert payload["dukascopy_same_timing_v2"]["net_pnl_usd"] > payload[
        "dukascopy_same_timing_baseline"
    ]["net_pnl_usd"]

    manifest = (ROOT / "CROSSFEED_SOURCE_MANIFEST.csv").read_text().splitlines()
    assert len(manifest) == 2_112
    assert manifest[1].startswith("year=2021/")
    assert ":/" not in manifest[1]
