from __future__ import annotations

from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PHASE1_ROOT))

from pullback import (  # noqa: E402
    PullbackSettings,
    dependency_sha256,
    evaluate_decisions,
    prepare_bars,
    rates_to_frame,
    sha256_file,
    utc_text,
    yearly_ranges,
)
from ml.a3_meta_v1.mt5_readonly import (  # noqa: E402
    MT5ConnectionSpec,
    ReadOnlyMT5Client,
)


UTC = timezone.utc


def load_config() -> dict[str, Any]:
    return json.loads(
        (ROOT / "config" / "capital_r1_pullback_forward_v29.json").read_text(
            encoding="utf-8"
        )
    )


def resolve_artifact(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def read_mt5_log(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        rows: list[list[str]] = []
        for line_number, row in enumerate(reader, start=2):
            if len(row) < len(header):
                raise ValueError(f"short MT5 log row at {path}:{line_number}")
            if any(value for value in row[len(header) :]):
                raise ValueError(
                    f"nonempty trailing MT5 log cell at {path}:{line_number}"
                )
            rows.append(row[: len(header)])
    return pd.DataFrame(rows, columns=header, dtype=str)


def fetch_timeframe(
    client: ReadOnlyMT5Client,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    timeframe_value = client.timeframe_value(timeframe)
    for lower, upper in yearly_ranges(start, end):
        rates = client.copy_rates_range(symbol, timeframe_value, lower, upper)
        if rates is None or len(rates) == 0:
            raise RuntimeError(
                f"MT5 returned no {timeframe} rates for {utc_text(lower)} to {utc_text(upper)}: "
                f"{client.last_error()}"
            )
        chunks.append(rates_to_frame(rates))
    result = (
        pd.concat(chunks, ignore_index=True)
        .drop_duplicates("time", keep="last")
        .sort_values("time")
        .reset_index(drop=True)
    )
    start_stamp = pd.Timestamp(start)
    end_stamp = pd.Timestamp(end)
    result = result.loc[
        result["time"].ge(start_stamp) & result["time"].lt(end_stamp)
    ].reset_index(drop=True)
    if result.empty:
        raise RuntimeError(f"MT5 returned no bounded {timeframe} history")
    return result


def fetch_historical_bars(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    source = config["source"]
    start = datetime.fromisoformat(
        source["history_start_inclusive_utc"].replace("Z", "+00:00")
    )
    end = datetime.fromisoformat(
        source["parity_end_exclusive_utc"].replace("Z", "+00:00")
    )
    client = ReadOnlyMT5Client.from_installed_package()
    if not client.initialize(MT5ConnectionSpec(source["terminal_exe"], True)):
        raise RuntimeError(f"MT5 initialize failed: {client.last_error()}")
    try:
        account = client.account_info()
        if account is None:
            raise RuntimeError(f"MT5 account unavailable: {client.last_error()}")
        if int(account.login) != int(source["historical_account_login"]):
            raise RuntimeError(f"Historical MT5 account changed: {account.login}")
        if str(account.server) != str(source["account_server"]):
            raise RuntimeError(f"Historical MT5 server changed: {account.server}")
        return {
            timeframe.lower(): fetch_timeframe(
                client, source["symbol"], timeframe, start, end
            )
            for timeframe in ("M15", "H1", "H4", "D1")
        }
    finally:
        client.shutdown()


def exact_list_equal(left: pd.Series, right: pd.Series) -> bool:
    return left.reset_index(drop=True).equals(right.reset_index(drop=True))


def metric_parity(
    observed: pd.Series, expected: pd.Series, decimals: int
) -> tuple[bool, float]:
    left = pd.to_numeric(observed, errors="raise").to_numpy(dtype=float)
    right = pd.to_numeric(expected, errors="raise").to_numpy(dtype=float)
    if len(left) != len(right):
        return False, float("inf")
    maximum = float(np.max(np.abs(left - right))) if len(left) else 0.0
    recorded_half_unit = 0.5 * (10.0 ** (-decimals))
    return bool(maximum <= recorded_half_unit + 1e-9), maximum


def build_report() -> dict[str, Any]:
    config = load_config()
    settings = PullbackSettings.from_mapping(config["settings"])
    artifacts = {
        name: resolve_artifact(path) for name, path in config["artifacts"].items()
    }
    for path in artifacts.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    signals = read_mt5_log(artifacts["signals"])
    orders = read_mt5_log(artifacts["orders"])
    required_signals = {
        "timestamp_broker",
        "stage",
        "direction",
        "reason",
        "spread_points",
        "break_distance_atr",
        "estimated_cost_r",
    }
    required_orders = {
        "timestamp_broker",
        "action",
        "direction",
        "reason",
        "stop_points",
        "estimated_cost_r",
    }
    if not required_signals <= set(signals.columns):
        raise ValueError("historical signal log schema changed")
    if not required_orders <= set(orders.columns):
        raise ValueError("historical order log schema changed")

    decisions = pd.DataFrame(
        {
            "decision_time_utc": pd.to_datetime(
                signals["timestamp_broker"], format="%Y.%m.%d %H:%M:%S", utc=True
            ),
            "spread_points": pd.to_numeric(
                signals["spread_points"], errors="raise"
            ).astype(float),
        }
    )
    if decisions["decision_time_utc"].duplicated().any():
        raise ValueError("historical signal decisions are duplicated")
    expected_raw = signals["stage"].eq("WOULD_SIGNAL")
    expected_orders = orders.copy()
    expected_orders["decision_time_utc"] = pd.to_datetime(
        expected_orders["timestamp_broker"], format="%Y.%m.%d %H:%M:%S", utc=True
    )
    if expected_orders["decision_time_utc"].duplicated().any():
        raise ValueError("historical order decisions are duplicated")
    expected_order_times = pd.DatetimeIndex(expected_orders["decision_time_utc"])
    expected_raw_times = pd.DatetimeIndex(
        decisions.loc[expected_raw, "decision_time_utc"]
    )
    if not expected_order_times.equals(expected_raw_times):
        raise ValueError("historical raw-signal and order timestamps differ")

    bars = fetch_historical_bars(config)
    prepared = prepare_bars(bars["m15"], bars["h1"], bars["h4"], bars["d1"], settings)
    observed = evaluate_decisions(prepared, decisions, settings)
    observed_raw = observed.loc[observed["raw_signal"]].reset_index(drop=True)
    expected_raw_rows = signals.loc[expected_raw].reset_index(drop=True)

    raw_time_equal = pd.DatetimeIndex(observed_raw["decision_time_utc"]).equals(
        expected_raw_times
    )
    stage_equal = bool(
        np.array_equal(
            observed["raw_signal"].to_numpy(dtype=bool),
            expected_raw.to_numpy(dtype=bool),
        )
    )
    signal_direction_equal = exact_list_equal(
        observed_raw["direction"], expected_raw_rows["direction"]
    )
    signal_reason_equal = exact_list_equal(
        observed_raw["signal_reason"], expected_raw_rows["reason"]
    )
    break_equal, break_max_abs = metric_parity(
        observed_raw["break_distance_atr"],
        expected_raw_rows["break_distance_atr"],
        4,
    )

    order_action_equal = exact_list_equal(
        observed_raw["guard_action"], expected_orders["action"]
    )
    order_direction_equal = exact_list_equal(
        observed_raw["direction"], expected_orders["direction"]
    )
    order_reason_equal = exact_list_equal(
        observed_raw["guard_reason"], expected_orders["reason"]
    )
    stop_equal, stop_max_abs = metric_parity(
        observed_raw["stop_points"], expected_orders["stop_points"], 2
    )
    cost_equal, cost_max_abs = metric_parity(
        observed_raw["estimated_cost_r"], expected_orders["estimated_cost_r"], 4
    )

    parity = {
        "decision_rows_expected": int(len(signals)),
        "decision_rows_observed": int(len(observed)),
        "raw_signal_rows_expected": int(expected_raw.sum()),
        "raw_signal_rows_observed": int(observed["raw_signal"].sum()),
        "order_rows_expected": int(len(expected_orders)),
        "pass_rows_expected": int(expected_orders["action"].eq("ORDER_SEND_OK").sum()),
        "pass_rows_observed": int(
            observed_raw["guard_action"].eq("ORDER_SEND_OK").sum()
        ),
        "decision_stage_exact": stage_equal,
        "raw_signal_times_exact": raw_time_equal,
        "signal_direction_exact": signal_direction_equal,
        "signal_reason_exact": signal_reason_equal,
        "break_distance_atr_within_4dp_log_precision": break_equal,
        "break_distance_atr_max_abs_error": break_max_abs,
        "order_action_exact": order_action_equal,
        "order_direction_exact": order_direction_equal,
        "order_reason_exact": order_reason_equal,
        "stop_points_within_2dp_log_precision": stop_equal,
        "stop_points_max_abs_error": stop_max_abs,
        "estimated_cost_r_within_4dp_log_precision": cost_equal,
        "estimated_cost_r_max_abs_error": cost_max_abs,
        "expected_guard_reason_counts": {
            str(key): int(value)
            for key, value in expected_orders["reason"]
            .value_counts()
            .sort_index()
            .items()
        },
        "observed_guard_reason_counts": {
            str(key): int(value)
            for key, value in observed_raw["guard_reason"]
            .value_counts()
            .sort_index()
            .items()
        },
    }
    booleans = [
        stage_equal,
        raw_time_equal,
        signal_direction_equal,
        signal_reason_equal,
        break_equal,
        order_action_equal,
        order_direction_equal,
        order_reason_equal,
        stop_equal,
        cost_equal,
    ]
    parity["pass"] = bool(
        len(signals) == len(observed)
        and int(expected_raw.sum()) == int(observed["raw_signal"].sum())
        and int(expected_orders["action"].eq("ORDER_SEND_OK").sum())
        == int(observed_raw["guard_action"].eq("ORDER_SEND_OK").sum())
        and all(booleans)
    )
    report = {
        "schema_version": "xauusd_capital_r1_pullback_v29_historical_parity",
        "created_at_utc": utc_text(datetime.now(UTC)),
        "source_interval": {
            "start_inclusive_utc": config["source"]["parity_start_inclusive_utc"],
            "end_exclusive_utc": config["source"]["parity_end_exclusive_utc"],
        },
        "source_artifacts": {
            name: {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for name, path in artifacts.items()
        },
        "history": {
            timeframe: {
                "rows": int(len(frame)),
                "first_bar_utc": utc_text(frame.iloc[0]["time"]),
                "last_bar_utc": utc_text(frame.iloc[-1]["time"]),
                "canonical_ohlc_sha256": __import__("hashlib")
                .sha256(frame.to_csv(index=False, lineterminator="\n").encode("ascii"))
                .hexdigest(),
            }
            for timeframe, frame in bars.items()
        },
        "rule_dependency_sha256": dependency_sha256(
            REPO_ROOT, config["contract_scope"]
        ),
        "parity": parity,
        "authority": config["authority"],
    }
    if not parity["pass"]:
        observed_reasons = observed_raw["guard_reason"].reset_index(drop=True)
        expected_reasons = expected_orders["reason"].reset_index(drop=True)
        mismatch_indices = np.flatnonzero(
            ~observed_reasons.eq(expected_reasons).to_numpy(dtype=bool)
        )
        report["first_guard_mismatches"] = [
            {
                "decision_time_utc": utc_text(
                    observed_raw.iloc[int(index)]["decision_time_utc"]
                ),
                "observed_reason": str(observed_reasons.iloc[int(index)]),
                "expected_reason": str(expected_reasons.iloc[int(index)]),
            }
            for index in mismatch_indices[:20]
        ]
    return report


def main() -> int:
    report = build_report()
    output = ROOT / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "CAPITAL_R1_PULLBACK_V29_HISTORICAL_PARITY.json"
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["parity"], sort_keys=True))
    return 0 if report["parity"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
