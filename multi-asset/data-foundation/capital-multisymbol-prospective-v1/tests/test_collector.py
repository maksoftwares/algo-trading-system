from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capital_multisymbol_collector", ROOT / "src" / "collector.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def config(tmp_path: Path) -> dict:
    payload = json.loads(
        (ROOT / "config" / "capital_multisymbol_prospective_v1.json").read_text(
            encoding="utf-8"
        )
    )
    payload["storage"]["root"] = str(tmp_path / "data")
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"test")
    payload["account"]["terminal_exe"] = str(terminal)
    return payload


class FakeMt5:
    COPY_TICKS_ALL = 7

    def __init__(self, ticks: np.ndarray, login: int = 1033030):
        self.ticks = ticks
        self.login = login
        self.selected: set[str] = set()

    def initialize(self, **_kwargs):
        return True

    def shutdown(self):
        return None

    def last_error(self):
        return (1, "Success")

    def account_info(self):
        return SimpleNamespace(login=self.login, server="Capital.ComMena-Demo")

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def symbol_select(self, symbol, selected):
        if selected:
            self.selected.add(symbol)
        return True

    def symbol_info(self, symbol):
        return SimpleNamespace(
            select=symbol in self.selected,
            visible=symbol in self.selected,
            trade_mode=4,
            ticks_bookdepth=0,
        )

    def symbol_info_tick(self, _symbol):
        return SimpleNamespace(time_msc=int(self.ticks["time_msc"][-1]))

    def copy_ticks_range(self, _symbol, _start, _end, _mode):
        return self.ticks


@pytest.fixture
def ticks():
    dtype = [
        ("time", "<i8"),
        ("bid", "<f8"),
        ("ask", "<f8"),
        ("last", "<f8"),
        ("volume", "<u8"),
        ("time_msc", "<i8"),
        ("flags", "<u4"),
        ("volume_real", "<f8"),
    ]
    return np.array(
        [
            (0, 4000.0, 4000.3, 0.0, 0, 1785110400100, 6, 0.0),
            (0, 4000.1, 4000.4, 0.0, 0, 1785110400200, 6, 0.0),
        ],
        dtype=dtype,
    )


def test_locked_config_has_no_authority():
    payload = json.loads(
        (ROOT / "config" / "capital_multisymbol_prospective_v1.json").read_text(
            encoding="utf-8"
        )
    )
    MODULE.validate_config(payload)
    assert payload["account"]["expected_login"] == 1033030
    assert all(value is False for value in payload["authority"].values())


def test_preboundary_pass_writes_no_tick_rows(tmp_path, ticks):
    payload = config(tmp_path)
    fake = FakeMt5(ticks)
    result = MODULE.collect_once(
        payload, fake, now=datetime(2026, 7, 26, 12, tzinfo=UTC)
    )
    assert result["decision"] == "WAIT_BOUNDARY"
    assert not list(Path(payload["storage"]["root"]).rglob("*.csv"))


def test_boundary_rows_are_partitioned_and_resume_is_idempotent(tmp_path, ticks):
    payload = config(tmp_path)
    fake = FakeMt5(ticks)
    now = datetime(2026, 7, 27, 0, 1, tzinfo=UTC)
    first = MODULE.collect_once(payload, fake, now=now)
    second = MODULE.collect_once(payload, fake, now=now)
    assert first["symbols"]["XAUUSD"]["rows_written_this_pass"] == 2
    assert second["symbols"]["XAUUSD"]["rows_written_this_pass"] == 0
    paths = list(Path(payload["storage"]["root"]).rglob("*.csv"))
    assert len(paths) == len(payload["symbols"])
    assert sum(1 for _ in paths[0].open(encoding="ascii")) == 3


def test_wrong_account_fails_closed(tmp_path, ticks):
    payload = config(tmp_path)
    with pytest.raises(MODULE.CollectorError, match="locked login"):
        MODULE.collect_once(
            payload,
            FakeMt5(ticks, login=999999),
            now=datetime(2026, 7, 27, 0, 1, tzinfo=UTC),
        )


def test_source_contains_no_order_api():
    source = (ROOT / "src" / "collector.py").read_text(encoding="utf-8").lower()
    assert "order_send" not in source
    assert "trade_action_" not in source
    assert "position_close" not in source
