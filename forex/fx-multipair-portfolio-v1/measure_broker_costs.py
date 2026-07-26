"""Read the demo account's real FX spread and swap rates. Strictly read-only.

Why this exists: every cost conclusion in FINDINGS.md rests on an *assumed*
spread, because no FX broker spread has ever been measured in this repository.
This measures the real thing, and in particular the **swap** rates, which decide
whether the carry premium (REJECTIONS.md R6) is capturable on this account.

Safety contract. This module calls only ``initialize``, ``account_info``,
``symbol_info``, ``symbol_info_tick`` and ``symbols_get`` -- the same read-only
surface the existing ``capital-multisymbol-prospective-v1`` collector uses. It
sends no order, modifies no symbol, changes no setting, and writes nothing
outside this package's ``outputs/``. It asserts the account is a demo before
reporting and refuses to continue on a real account.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

FX_WANTED = (
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "EURGBP", "EURJPY", "GBPJPY", "EURAUD", "AUDJPY", "USDMXN", "USDZAR",
    "USDTRY", "USDSEK", "USDNOK", "USDPLN", "USDHUF", "USDCNH",
)
SWAP_MODE = {
    0: "DISABLED", 1: "POINTS", 2: "SYMBOL_CURRENCY", 3: "MARGIN_CURRENCY",
    4: "DEPOSIT_CURRENCY", 5: "INTEREST_CURRENT", 6: "INTEREST_OPEN",
    7: "REOPEN_CURRENT", 8: "REOPEN_BID",
}
TRADE_MODE = {0: "DISABLED", 1: "LONGONLY", 2: "SHORTONLY", 3: "CLOSEONLY", 4: "FULL"}


def main() -> int:
    if not mt5.initialize():
        print(f"initialize failed: {mt5.last_error()}")
        print("The terminal must be running and logged in. Nothing was changed.")
        return 1
    try:
        account = mt5.account_info()
        if account is None:
            print(f"account_info failed: {mt5.last_error()}")
            return 1
        is_demo = account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        print(f"account {account.login} @ {account.server}  currency={account.currency}")
        print(f"trade_mode={'DEMO' if is_demo else account.trade_mode} (read-only query)")
        if not is_demo:
            print("REFUSING: not a demo account. No data reported.")
            return 2

        available = {symbol.name for symbol in mt5.symbols_get()}
        rows = []
        print(
            f"\n{'symbol':10s} {'spread_pts':>10} {'spread_pips':>11} {'swapL':>9} {'swapS':>9} "
            f"{'swap_mode':>16} {'3d':>3} {'digits':>6} {'minlot':>7} {'trade':>9}"
        )
        print("-" * 106)
        for symbol in FX_WANTED:
            if symbol not in available:
                continue
            if not mt5.symbol_select(symbol, True):
                # symbol_select only toggles Market Watch visibility; needed to read quotes.
                continue
            info = mt5.symbol_info(symbol)
            tick = mt5.symbol_info_tick(symbol)
            if info is None:
                continue
            point = info.point
            live_spread = (tick.ask - tick.bid) / point if tick and tick.ask and tick.bid else None
            # pip = 10 points on a 5/3-digit FX quote
            pip_points = 10.0 if info.digits in (3, 5) else 1.0
            row = {
                "symbol": symbol,
                "spread_points_current": info.spread,
                "spread_points_live": None if live_spread is None else round(live_spread, 1),
                "spread_pips": round(info.spread / pip_points, 2),
                "spread_float": bool(info.spread_float),
                "swap_long": info.swap_long,
                "swap_short": info.swap_short,
                "swap_mode": SWAP_MODE.get(info.swap_mode, str(info.swap_mode)),
                "swap_rollover3days": info.swap_rollover3days,
                "digits": info.digits,
                "point": point,
                "volume_min": info.volume_min,
                "volume_step": info.volume_step,
                "trade_contract_size": info.trade_contract_size,
                "trade_mode": TRADE_MODE.get(info.trade_mode, str(info.trade_mode)),
                "currency_profit": info.currency_profit,
            }
            rows.append(row)
            print(
                f"{symbol:10s} {info.spread:>10} {row['spread_pips']:>11.2f} "
                f"{info.swap_long:>9.3f} {info.swap_short:>9.3f} {row['swap_mode']:>16} "
                f"{info.swap_rollover3days:>3} {info.digits:>6} {info.volume_min:>7} "
                f"{row['trade_mode']:>9}"
            )

        report = {
            "schema_version": "fx_broker_cost_measurement_v1",
            "access": "READ_ONLY_SYMBOL_INFO_NO_ORDERS_NO_MODIFICATIONS",
            "account": {
                "login": account.login,
                "server": account.server,
                "currency": account.currency,
                "is_demo": is_demo,
            },
            "symbols": rows,
            "symbols_available_count": len(available),
            "fx_symbols_found": [row["symbol"] for row in rows],
            "fx_symbols_missing": [s for s in FX_WANTED if s not in available],
        }
        out = ROOT / "outputs" / "BROKER_COSTS.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nsymbols on server: {len(available)}")
        print(f"missing from wanted list: {report['fx_symbols_missing']}")
        print(f"wrote {out}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
