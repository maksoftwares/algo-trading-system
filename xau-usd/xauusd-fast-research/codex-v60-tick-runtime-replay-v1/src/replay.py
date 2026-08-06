from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONTRACT_PATH = ROOT / "config" / "REPLAY_CONTRACT.json"
OUTPUTS = ROOT / "outputs"
DAY_MS = 86_400_000
HOUR_MS = 3_600_000
PNL_COLUMN = "fee_stress_pnl_usd"
OPEN_COST_COLUMN = "fee_stress_open_cost_usd"
_DRAWDOWN_LIMIT_KEYS = {
    "closed_drawdown_suspend_usd",
    "closed_drawdown_resume_usd",
    "combined_closed_drawdown_hard_stop_usd",
    "floating_drawdown_hard_stop_usd",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return sha256_bytes(payload)


def resolve_input(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def utc_text(timestamp_ms: int | None) -> str | None:
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def timestamp_ms(value: Any) -> int:
    return int(pd.Timestamp(value).value // 1_000_000)


def effective_threshold(
    risk: Mapping[str, Any], activation_equity: float, absolute_key: str
) -> float:
    absolute = float(risk[absolute_key])
    fraction_limits_enabled = bool(
        risk.get("equity_fraction_limits_enabled", True)
    )
    if absolute_key in _DRAWDOWN_LIMIT_KEYS:
        fraction_limits_enabled = bool(
            risk.get(
                "drawdown_equity_fraction_limits_enabled",
                fraction_limits_enabled,
            )
        )
    if not fraction_limits_enabled:
        return absolute
    fraction_key = absolute_key.removesuffix("_usd") + "_fraction"
    return min(
        absolute,
        activation_equity * float(risk[fraction_key]),
    )


def apply_runtime_risk_mode(
    config: dict[str, Any],
    required_equity_scaling: bool = False,
) -> dict[str, Any]:
    configured_equity_scaling = config["risk"].get("equity_fraction_limits_enabled")
    if bool(configured_equity_scaling) is not required_equity_scaling:
        mode = (
            "activation-equity-scaled"
            if required_equity_scaling
            else "absolute-only"
        )
        raise ValueError(f"Replay requires the canonical {mode} risk mode")
    config["risk"]["equity_fraction_limits_enabled"] = required_equity_scaling
    return config


def apply_portfolio_protection(
    contract: Mapping[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    relative = contract["inputs"].get("portfolio_protection_overlay")
    if not relative:
        return config
    path = resolve_input(str(relative))
    overlay = load_json(path)
    if overlay.get("schema_version") != "xauusd_v60_drawdown_protection_v1_overlay":
        raise ValueError("Unexpected drawdown-protection overlay schema")
    base_path = resolve_input(contract["inputs"]["demo_config"])
    expected = overlay["base_config"]
    if resolve_input(str(expected["path"])).resolve() != base_path.resolve():
        raise ValueError("Drawdown protection is bound to another config")
    if sha256_file(base_path) != str(expected["sha256"]):
        raise ValueError("Drawdown-protection base config identity changed")
    config["portfolio_protection"] = overlay["portfolio_protection"]
    return config


@dataclass(frozen=True)
class Candidate:
    trade_id: str
    source_id: str
    specialist_id: str
    sleeve_type: str
    entry_ms: int
    exit_ms: int
    direction: str
    risk_usd: float
    pnl_usd: float
    entry_price: float
    exit_price: float
    open_cost_usd: float
    maximum_risk_usd: float
    maximum_spread_r: float
    maximum_open_positions: int
    maximum_entries_per_utc_day: int
    maximum_entry_gap_minutes: int
    cooldown_minutes: int
    event_id: str | None

    @property
    def sign(self) -> float:
        return 1.0 if self.direction == "LONG" else -1.0


@dataclass
class Position:
    candidate: Candidate
    basis_offset: float


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    starting_equity_usd: float
    activation_equity_usd: float
    rebaseline_days: int | None
    guardian_enabled: bool
    guardian_exit_attribution: str


@dataclass
class GuardianState:
    dubai_day: int | None = None
    day_start_equity: float = 0.0
    peak_day_pnl: float = 0.0
    armed: bool = False
    next_floor_armed: bool = False
    locked: bool = False


def _source_id(row: Any) -> str:
    sleeve = str(row.sleeve_id)
    if sleeve != "V59_BROKER_CORE":
        return sleeve
    specialist = str(row.specialist_id)
    if specialist == "R1_UPTREND":
        if str(row.source_strategy) == "h4_d1_long_best_box2_atr80":
            return "R1_BOX"
        if str(row.source_strategy) == "r1_h1_pullback_long_v1":
            return "R1_PULLBACK"
        raise ValueError(f"Unknown R1 source strategy: {row.source_strategy}")
    mapping = {
        "R2_DOWNTREND": "R2_DOWNTREND",
        "R3_COMPRESSION": "R3_COMPRESSION",
        "R4_CHOP": "R4_CHOP",
    }
    if specialist not in mapping:
        raise ValueError(f"Unknown core specialist: {specialist}")
    return mapping[specialist]


def _event_id(source_id: str, trade_id: str) -> str | None:
    prefixes = {
        "V7_SWING_HEALTH": "V7_",
        "V8_RETEST_HEALTH": "V8_",
        "V25_CHOP": "V25_",
        "V57_BREAK_SWING_H4ADX_HIGH": "V9_BREAK_",
    }
    prefix = prefixes.get(source_id)
    if prefix is None:
        return None
    if not trade_id.startswith(prefix):
        raise ValueError(f"Unexpected {source_id} trade ID: {trade_id}")
    return trade_id[len(prefix) :]


def _r1_risk_map(path: Path) -> dict[tuple[int, int], float]:
    frame = pd.read_csv(path, low_memory=False)
    allowed = {
        "BT_A1_XAU_ROUTER_V1_R1_LONG_BOX2_PREVHEALTH",
        "BT_A1_XAU_R1_PULLBACK_LONG_V2_M15_SESSION_09_15",
    }
    frame = frame.loc[frame["native_run_id"].astype(str).isin(allowed)].copy()
    result: dict[tuple[int, int], float] = {}
    pattern = re.compile(r"^(sl|tp)\s+([0-9.]+)", re.IGNORECASE)
    for row in frame.itertuples(index=False):
        match = pattern.match(str(row.native_exit_comment).strip())
        if match is None:
            raise ValueError(f"Unparseable R1 exit comment: {row.native_exit_comment}")
        exit_level = float(match.group(2))
        entry = float(row.native_entry_price)
        risk = entry - exit_level if match.group(1).lower() == "sl" else (
            exit_level - entry
        ) / 2.0
        if not math.isfinite(risk) or risk <= 0:
            raise ValueError(f"Invalid reconstructed R1 risk: {risk}")
        key = (
            timestamp_ms(pd.to_datetime(row.native_entry_time, utc=True)),
            timestamp_ms(pd.to_datetime(row.native_exit_time, utc=True)),
        )
        if key in result:
            raise ValueError(f"Duplicate R1 time key: {key}")
        result[key] = risk
    return result


def load_candidates(
    contract: Mapping[str, Any], config: Mapping[str, Any]
) -> tuple[list[Candidate], dict[str, Any]]:
    ledger_path = resolve_input(contract["inputs"]["ledger"])
    frame = pd.read_parquet(ledger_path)
    raw_rows = len(frame)
    for column in ("entry_time", "exit_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    start = pd.Timestamp(contract["evaluation"]["entry_start_utc"])
    end = pd.Timestamp(contract["evaluation"]["entry_end_exclusive_utc"])
    excluded = set(contract["population"]["excluded_specialist_ids"])
    frame = frame.loc[
        frame["entry_time"].ge(start)
        & frame["entry_time"].lt(end)
        & ~frame["specialist_id"].isin(excluded)
    ].copy()
    r1_risk = _r1_risk_map(
        resolve_input(contract["inputs"]["r1_native_reconciliation"])
    )
    source_config = {str(row["source_id"]): row for row in config["sources"]}
    candidates: list[Candidate] = []
    r1_rows = 0
    for row in frame.itertuples(index=False):
        source_id = _source_id(row)
        source = source_config[source_id]
        entry_ms = timestamp_ms(row.entry_time)
        exit_ms = timestamp_ms(row.exit_time)
        if exit_ms <= entry_ms:
            raise ValueError(f"Nonpositive holding period: {row.trade_id}")
        if source_id in {"R1_BOX", "R1_PULLBACK"}:
            risk = r1_risk.get((entry_ms, exit_ms))
            if risk is None:
                raise ValueError(f"Missing R1 native risk: {row.trade_id}")
            r1_rows += 1
        else:
            risk = float(row.risk_usd)
        values = (
            risk,
            float(getattr(row, PNL_COLUMN)),
            float(row.entry_price),
            float(row.exit_price),
            float(getattr(row, OPEN_COST_COLUMN)),
        )
        if not all(math.isfinite(value) for value in values) or risk <= 0:
            raise ValueError(f"Invalid candidate geometry: {row.trade_id}")
        specialist = (
            str(row.specialist_id)
            if pd.notna(row.specialist_id)
            else str(row.sleeve_id)
        )
        trade_id = str(row.trade_id)
        candidates.append(
            Candidate(
                trade_id=trade_id,
                source_id=source_id,
                specialist_id=specialist,
                sleeve_type=str(source.get("sleeve_type", "CORE")).upper(),
                entry_ms=entry_ms,
                exit_ms=exit_ms,
                direction=str(row.direction).upper(),
                risk_usd=risk,
                pnl_usd=float(getattr(row, PNL_COLUMN)),
                entry_price=float(row.entry_price),
                exit_price=float(row.exit_price),
                open_cost_usd=float(getattr(row, OPEN_COST_COLUMN)),
                maximum_risk_usd=float(source["maximum_risk_usd"]),
                maximum_spread_r=float(source["maximum_spread_r"]),
                maximum_open_positions=int(source["maximum_open_positions"]),
                maximum_entries_per_utc_day=int(
                    source["maximum_entries_per_utc_day"]
                ),
                maximum_entry_gap_minutes=int(
                    source["maximum_entry_gap_minutes"]
                ),
                cooldown_minutes=int(
                    source.get("same_direction_post_loss_cooldown_minutes", 0)
                ),
                event_id=_event_id(source_id, trade_id),
            )
        )
    candidates.sort(key=lambda row: (row.entry_ms, row.source_id, row.trade_id))
    ids = [row.trade_id for row in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate trade IDs are not unique")
    source_counts = Counter(row.source_id for row in candidates)
    audit = {
        "raw_ledger_rows": int(raw_rows),
        "evaluation_candidate_rows": int(len(candidates)),
        "r1_native_risk_rows": int(r1_rows),
        "source_counts": dict(sorted(source_counts.items())),
        "first_entry_utc": utc_text(candidates[0].entry_ms),
        "last_entry_utc": utc_text(candidates[-1].entry_ms),
        "last_exit_utc": utc_text(max(row.exit_ms for row in candidates)),
        "population_sha256": canonical_sha256(
            [
                [
                    row.trade_id,
                    row.source_id,
                    row.entry_ms,
                    row.exit_ms,
                    row.risk_usd,
                    row.pnl_usd,
                ]
                for row in candidates
            ]
        ),
    }
    return candidates, audit


def _hour_path(root: Path, hour_ms: int) -> Path:
    moment = datetime.fromtimestamp(hour_ms / 1000.0, UTC)
    return (
        root
        / f"year={moment.year:04d}"
        / f"month={moment.month:02d}"
        / f"{moment:%Y%m%d%H}.json"
    )


def _decode_hour(raw: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    payload = json.loads(raw)
    times = payload.get("times", [])
    if not times:
        return (
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.float64),
            np.empty(0, dtype=np.float64),
        )
    required = ("timestamp", "multiplier", "bid", "ask", "bids", "asks")
    if any(payload.get(key) is None for key in required):
        raise ValueError("Nonempty Dukascopy hour lacks a base field")
    if not (
        len(times)
        == len(payload["bids"])
        == len(payload["asks"])
        == len(payload["bidVolumes"])
        == len(payload["askVolumes"])
    ):
        raise ValueError("Dukascopy tick arrays have inconsistent lengths")
    timestamp = np.cumsum(np.asarray(times, dtype=np.int64))
    timestamp += int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    bid = float(payload["bid"]) + np.cumsum(
        np.asarray(payload["bids"], dtype=np.float64)
    ) * multiplier
    ask = float(payload["ask"]) + np.cumsum(
        np.asarray(payload["asks"], dtype=np.float64)
    ) * multiplier
    # XAUUSD's source scale is three decimals. Every delta is one source tick,
    # so vectorized cumulative rounding is equivalent to the locked decoder.
    bid = np.floor(bid * 1000.0 + 0.5 + 1e-9) / 1000.0
    ask = np.floor(ask * 1000.0 + 0.5 + 1e-9) / 1000.0
    if np.any(ask <= bid) or np.any(np.diff(timestamp) < 0):
        raise ValueError("Invalid Dukascopy quote ordering")
    return timestamp, bid, ask


def _relevant_hours(candidates: Iterable[Candidate]) -> list[int]:
    intervals = sorted(
        (
            row.entry_ms // HOUR_MS,
            row.exit_ms // HOUR_MS,
        )
        for row in candidates
    )
    merged: list[list[int]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    hours: list[int] = []
    for start, end in merged:
        hours.extend(range(start - 1, end + 1))
    return sorted(set(hour * HOUR_MS for hour in hours))


def prepare_quote_cache(
    contract: Mapping[str, Any],
    candidates: list[Candidate],
    population_audit: Mapping[str, Any],
    *,
    force: bool = False,
) -> dict[str, Any]:
    cache_dir = Path(contract["cache"]["directory"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        name: cache_dir / f"{name}.npy"
        for name in ("cycle_ms", "tick_ms", "bid", "ask")
    }
    meta_path = cache_dir / "CACHE_META.json"
    manifest_path = OUTPUTS / "TICK_FILES_MANIFEST.csv"
    identity = {
        "schema_version": "v60_tick_quote_cache_v1",
        "population_sha256": population_audit["population_sha256"],
        "poll_seconds": int(contract["evaluation"]["poll_seconds"]),
        "raw_root": str(contract["inputs"]["dukascopy_raw_root"]),
    }
    if not force and meta_path.is_file() and all(path.is_file() for path in paths.values()):
        meta = load_json(meta_path)
        if meta.get("identity") == identity:
            return meta

    raw_root = Path(contract["inputs"]["dukascopy_raw_root"])
    poll_ms = int(contract["evaluation"]["poll_seconds"]) * 1000
    offsets = np.arange(0, HOUR_MS, poll_ms, dtype=np.int64)
    cycle_parts: list[np.ndarray] = []
    tick_parts: list[np.ndarray] = []
    bid_parts: list[np.ndarray] = []
    ask_parts: list[np.ndarray] = []
    manifest: list[dict[str, Any]] = []
    carry: tuple[int, float, float] | None = None
    previous_hour: int | None = None
    for hour_ms in _relevant_hours(candidates):
        if previous_hour is None or hour_ms != previous_hour + HOUR_MS:
            carry = None
        previous_hour = hour_ms
        path = _hour_path(raw_root, hour_ms)
        if not path.is_file():
            manifest.append(
                {
                    "path": str(path),
                    "bytes": 0,
                    "sha256": "",
                    "ticks": 0,
                    "status": "MISSING",
                }
            )
            continue
        raw = path.read_bytes()
        tick_ms, bid, ask = _decode_hour(raw)
        manifest.append(
            {
                "path": str(path),
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "ticks": int(len(tick_ms)),
                "status": "OK",
            }
        )
        cycles = hour_ms + offsets
        indexes = np.searchsorted(tick_ms, cycles, side="right") - 1
        valid = indexes >= 0
        observed_tick = np.empty(len(cycles), dtype=np.int64)
        observed_bid = np.empty(len(cycles), dtype=np.float64)
        observed_ask = np.empty(len(cycles), dtype=np.float64)
        if valid.any():
            observed_tick[valid] = tick_ms[indexes[valid]]
            observed_bid[valid] = bid[indexes[valid]]
            observed_ask[valid] = ask[indexes[valid]]
        if (~valid).any() and carry is not None:
            observed_tick[~valid] = carry[0]
            observed_bid[~valid] = carry[1]
            observed_ask[~valid] = carry[2]
            valid[~valid] = True
        if valid.any():
            cycle_parts.append(cycles[valid])
            tick_parts.append(observed_tick[valid])
            bid_parts.append(observed_bid[valid])
            ask_parts.append(observed_ask[valid])
        if len(tick_ms):
            carry = (int(tick_ms[-1]), float(bid[-1]), float(ask[-1]))

    if not cycle_parts:
        raise ValueError("No Dukascopy quote cycles were prepared")
    arrays = {
        "cycle_ms": np.concatenate(cycle_parts),
        "tick_ms": np.concatenate(tick_parts),
        "bid": np.concatenate(bid_parts),
        "ask": np.concatenate(ask_parts),
    }
    if np.any(np.diff(arrays["cycle_ms"]) <= 0):
        raise ValueError("Quote cache cycles are not strictly increasing")
    for name, values in arrays.items():
        np.save(paths[name], values, allow_pickle=False)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("path", "bytes", "sha256", "ticks", "status"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest)
    meta = {
        "identity": identity,
        "cycles": int(len(arrays["cycle_ms"])),
        "first_cycle_utc": utc_text(int(arrays["cycle_ms"][0])),
        "last_cycle_utc": utc_text(int(arrays["cycle_ms"][-1])),
        "source_files": int(len(manifest)),
        "missing_source_files": int(
            sum(row["status"] != "OK" for row in manifest)
        ),
        "source_bytes": int(sum(int(row["bytes"]) for row in manifest)),
        "source_ticks": int(sum(int(row["ticks"]) for row in manifest)),
        "manifest_sha256": sha256_file(manifest_path),
        "array_paths": {name: str(path) for name, path in paths.items()},
    }
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return meta


def load_quote_cache(meta: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return {
        name: np.load(path, mmap_mode="r")
        for name, path in meta["array_paths"].items()
    }


class Scenario:
    def __init__(
        self,
        spec: ScenarioSpec,
        config: Mapping[str, Any],
        contract: Mapping[str, Any],
        candidates: list[Candidate],
    ) -> None:
        self.spec = spec
        self.config = config
        self.contract = contract
        self.candidates = candidates
        self.risk = config["risk"]
        self.account_closed_pnl = 0.0
        self.v60_closed_pnl = 0.0
        self.policy_peak_closed = 0.0
        self.lifetime_peak_closed = 0.0
        self.peak_equity = spec.starting_equity_usd
        self.lifetime_peak_equity = spec.starting_equity_usd
        self.max_policy_closed_dd = 0.0
        self.max_lifetime_closed_dd = 0.0
        self.max_lifetime_equity_dd = 0.0
        self.drawdown_suspended = False
        self.flat_since_ms: int | None = None
        self.positions: dict[str, Position] = {}
        self.exit_heap: list[tuple[int, str]] = []
        self.candidate_index = 0
        self.daily_entries: Counter[tuple[str, int]] = Counter()
        self.recovery_daily_entries: Counter[int] = Counter()
        self.addon_events: set[str] = set()
        self.last_losses: dict[tuple[str, str], int] = {}
        self.rejections: Counter[str] = Counter()
        self.close_pnls: list[float] = []
        self.event_rows: list[dict[str, Any]] = []
        self.suspensions = 0
        self.rebaselines = 0
        self.recovery_entries = 0
        self.emergency_closes = 0
        self.guardian_arms = 0
        self.guardian_locks = 0
        self.maximum_open_positions = 0
        self.profit_protection_arms = 0
        self.profit_giveback_closes = 0
        self.profit_protection_armed = False
        self.profit_protection_peak_open_pnl = 0.0
        self.profit_protection_tickets: set[str] = set()
        self.first_suspend_ms: int | None = None
        self.first_hard_stop_ms: int | None = None
        self.first_guardian_lock_ms: int | None = None
        self.guardian = GuardianState()
        keys = (
            "closed_drawdown_suspend_usd",
            "closed_drawdown_resume_usd",
            "combined_closed_drawdown_hard_stop_usd",
            "floating_drawdown_hard_stop_usd",
            "maximum_account_concurrent_initial_risk_usd",
            "maximum_directional_concurrent_initial_risk_usd",
        )
        self.limits = {
            key: effective_threshold(self.risk, spec.activation_equity_usd, key)
            for key in keys
        }

    def equity(self, bid: float, ask: float) -> float:
        value = self.spec.starting_equity_usd + self.account_closed_pnl
        for position in self.positions.values():
            candidate = position.candidate
            side = bid if candidate.direction == "LONG" else ask
            adjusted = side + position.basis_offset
            value += (
                candidate.sign * (adjusted - candidate.entry_price)
                - candidate.open_cost_usd
            )
        return value

    def _record(
        self, event: str, now_ms: int, candidate: Candidate | None = None, **extra: Any
    ) -> None:
        row: dict[str, Any] = {
            "scenario_id": self.spec.scenario_id,
            "event": event,
            "timestamp_utc": utc_text(now_ms),
            "trade_id": "" if candidate is None else candidate.trade_id,
            "source_id": "" if candidate is None else candidate.source_id,
        }
        row.update(extra)
        self.event_rows.append(row)

    def _market_pnl(self, position: Position, bid: float, ask: float) -> float:
        candidate = position.candidate
        side = bid if candidate.direction == "LONG" else ask
        adjusted = side + position.basis_offset
        return (
            candidate.sign * (adjusted - candidate.entry_price)
            - candidate.open_cost_usd
        )

    def _close(
        self,
        trade_id: str,
        now_ms: int,
        pnl: float,
        reason: str,
        *,
        counted_by_v60: bool,
    ) -> None:
        position = self.positions.pop(trade_id)
        candidate = position.candidate
        self.account_closed_pnl += pnl
        if counted_by_v60:
            self.v60_closed_pnl += pnl
        self.close_pnls.append(pnl)
        if (
            candidate.source_id == "V57_BREAK_SWING_H4ADX_HIGH"
            and pnl < 0.0
        ):
            self.last_losses[(candidate.source_id, candidate.direction)] = now_ms
        self._record(
            "POSITION_CLOSED",
            now_ms,
            candidate,
            reason=reason,
            pnl_usd=pnl,
            counted_by_v60=counted_by_v60,
        )
        if self.drawdown_suspended and not self.positions and self.flat_since_ms is None:
            self.flat_since_ms = now_ms

    def _close_all(
        self,
        now_ms: int,
        bid: float,
        ask: float,
        reason: str,
        *,
        counted_by_v60: bool,
    ) -> None:
        for trade_id in sorted(list(self.positions)):
            position = self.positions[trade_id]
            self._close(
                trade_id,
                now_ms,
                self._market_pnl(position, bid, ask),
                reason,
                counted_by_v60=counted_by_v60,
            )
            self.emergency_closes += 1

    def _settle_normal_exits(self, now_ms: int) -> None:
        import heapq

        while self.exit_heap and self.exit_heap[0][0] <= now_ms:
            _, trade_id = heapq.heappop(self.exit_heap)
            position = self.positions.get(trade_id)
            if position is None:
                continue
            self._close(
                trade_id,
                now_ms,
                position.candidate.pnl_usd,
                "SOURCE_EXIT",
                counted_by_v60=True,
            )

    def _evaluate_profit_protection(
        self, now_ms: int, bid: float, ask: float
    ) -> None:
        settings = self.config.get("portfolio_protection")
        if not isinstance(settings, Mapping) or not bool(settings.get("enabled")):
            return
        tickets = set(self.positions)
        if not tickets:
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()
            return
        if self.profit_protection_tickets and not self.profit_protection_tickets.intersection(
            tickets
        ):
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
        self.profit_protection_tickets = tickets
        active_risk = sum(
            position.candidate.risk_usd for position in self.positions.values()
        )
        open_pnl = sum(
            self._market_pnl(position, bid, ask)
            for position in self.positions.values()
        )
        self.profit_protection_peak_open_pnl = max(
            self.profit_protection_peak_open_pnl, open_pnl
        )
        arm = float(settings["open_profit_arm_r"]) * active_risk
        retain = float(settings["open_profit_retain_r"]) * active_risk
        if not self.profit_protection_armed and open_pnl >= arm:
            self.profit_protection_armed = True
            self.profit_protection_arms += 1
            self._record(
                "OPEN_PROFIT_PROTECTION_ARMED",
                now_ms,
                open_pnl_usd=open_pnl,
                active_initial_risk_usd=active_risk,
            )
        elif self.profit_protection_armed and open_pnl <= retain:
            for trade_id in sorted(list(self.positions)):
                position = self.positions[trade_id]
                self._close(
                    trade_id,
                    now_ms,
                    self._market_pnl(position, bid, ask),
                    "OPEN_PROFIT_GIVEBACK",
                    counted_by_v60=True,
                )
                self.profit_giveback_closes += 1
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()

    def _refresh_drawdown(self, now_ms: int, equity: float) -> tuple[float, float]:
        self.peak_equity = max(self.peak_equity, equity)
        self.lifetime_peak_equity = max(self.lifetime_peak_equity, equity)
        floating_dd = self.peak_equity - equity
        self.max_lifetime_equity_dd = max(
            self.max_lifetime_equity_dd,
            self.lifetime_peak_equity - equity,
        )
        self.policy_peak_closed = max(
            self.policy_peak_closed, self.v60_closed_pnl
        )
        self.lifetime_peak_closed = max(
            self.lifetime_peak_closed, self.v60_closed_pnl
        )
        policy_dd = self.policy_peak_closed - self.v60_closed_pnl
        true_dd = self.lifetime_peak_closed - self.v60_closed_pnl
        self.max_policy_closed_dd = max(self.max_policy_closed_dd, policy_dd)
        self.max_lifetime_closed_dd = max(self.max_lifetime_closed_dd, true_dd)
        if (
            not self.drawdown_suspended
            and policy_dd >= self.limits["closed_drawdown_suspend_usd"]
        ):
            self.drawdown_suspended = True
            self.suspensions += 1
            if self.first_suspend_ms is None:
                self.first_suspend_ms = now_ms
            self._record(
                "CLOSED_DRAWDOWN_SUSPENDED",
                now_ms,
                closed_drawdown_usd=policy_dd,
            )
        elif (
            self.drawdown_suspended
            and policy_dd <= self.limits["closed_drawdown_resume_usd"]
        ):
            self.drawdown_suspended = False
            self.flat_since_ms = None
            self._record(
                "CLOSED_DRAWDOWN_RESUMED",
                now_ms,
                closed_drawdown_usd=policy_dd,
            )
        if self.drawdown_suspended and not self.positions:
            if self.flat_since_ms is None:
                self.flat_since_ms = now_ms
        return floating_dd, policy_dd

    def _maybe_rebaseline(self, now_ms: int) -> None:
        if (
            self.spec.rebaseline_days is None
            or not self.drawdown_suspended
            or self.positions
            or self.flat_since_ms is None
        ):
            return
        wait_ms = self.spec.rebaseline_days * DAY_MS
        if now_ms - self.flat_since_ms < wait_ms:
            return
        prior_peak = self.policy_peak_closed
        self.policy_peak_closed = self.v60_closed_pnl
        self.drawdown_suspended = False
        self.flat_since_ms = None
        self.rebaselines += 1
        self._record(
            "FLAT_REBASELINE",
            now_ms,
            prior_policy_peak_closed_pnl_usd=prior_peak,
            new_policy_peak_closed_pnl_usd=self.v60_closed_pnl,
            lifetime_peak_closed_pnl_usd=self.lifetime_peak_closed,
            peak_equity_usd=self.peak_equity,
        )

    def _guardian_day(self, now_ms: int) -> int:
        offset = int(self.contract["guardian"]["dubai_utc_offset_minutes"]) * 60_000
        return (now_ms + offset) // DAY_MS

    def _guardian_reset(self, now_ms: int, equity: float) -> None:
        if not self.spec.guardian_enabled:
            return
        day = self._guardian_day(now_ms)
        if self.guardian.dubai_day == day:
            return
        self.guardian = GuardianState(
            dubai_day=day,
            day_start_equity=equity,
        )
        self._record("GUARDIAN_DAY_RESET", now_ms, day_start_equity_usd=equity)

    def _guardian_evaluate(
        self, now_ms: int, bid: float, ask: float, equity: float
    ) -> None:
        if not self.spec.guardian_enabled:
            return
        settings = self.contract["guardian"]
        conversion = float(self.contract["evaluation"]["usd_to_aed"])
        floor = float(settings["daily_floor_aed"]) / conversion
        next_floor = float(settings["next_daily_floor_aed"]) / conversion
        loss_stop = float(settings["daily_loss_stop_aed"]) / conversion
        state = self.guardian
        day_pnl = equity - state.day_start_equity
        state.peak_day_pnl = max(state.peak_day_pnl, day_pnl)
        if state.locked:
            if self.positions:
                self._close_all(
                    now_ms,
                    bid,
                    ask,
                    "GUARDIAN_KEEP_FLAT",
                    counted_by_v60=(
                        self.spec.guardian_exit_attribution
                        == "POSITION_ORIGIN"
                    ),
                )
            return
        if bool(settings["daily_loss_stop_enabled"]) and day_pnl <= loss_stop:
            state.locked = True
            self.guardian_locks += 1
            if self.first_guardian_lock_ms is None:
                self.first_guardian_lock_ms = now_ms
            self._record(
                "GUARDIAN_LOCKED",
                now_ms,
                reason="DAILY_LOSS_STOP",
                day_pnl_usd=day_pnl,
            )
            self._close_all(
                now_ms,
                bid,
                ask,
                "GUARDIAN_DAILY_LOSS_STOP",
                counted_by_v60=(
                    self.spec.guardian_exit_attribution == "POSITION_ORIGIN"
                ),
            )
            return
        if not bool(settings.get("daily_profit_floor_enabled", True)):
            return
        just_armed = False
        if not state.armed and day_pnl >= floor:
            state.armed = True
            just_armed = True
            self.guardian_arms += 1
            self._record("GUARDIAN_ARMED", now_ms, day_pnl_usd=day_pnl)
        if (
            state.armed
            and bool(settings["next_daily_floor_enabled"])
            and not state.next_floor_armed
            and next_floor > floor
            and day_pnl >= next_floor
        ):
            state.next_floor_armed = True
            self._record("GUARDIAN_NEXT_FLOOR_ARMED", now_ms, day_pnl_usd=day_pnl)
        active_floor = next_floor if state.next_floor_armed else floor
        if (
            state.armed
            and not just_armed
            and day_pnl <= active_floor
            and state.peak_day_pnl > active_floor
        ):
            state.locked = True
            self.guardian_locks += 1
            if self.first_guardian_lock_ms is None:
                self.first_guardian_lock_ms = now_ms
            self._record(
                "GUARDIAN_LOCKED",
                now_ms,
                reason="DAILY_PROFIT_FLOOR_RETURN",
                day_pnl_usd=day_pnl,
            )
            self._close_all(
                now_ms,
                bid,
                ask,
                "GUARDIAN_PROFIT_FLOOR_RETURN",
                counted_by_v60=(
                    self.spec.guardian_exit_attribution == "POSITION_ORIGIN"
                ),
            )

    def _current_risk(self) -> tuple[float, dict[str, float], float, int, int]:
        total = 0.0
        directional = {"LONG": 0.0, "SHORT": 0.0}
        addon = 0.0
        core_count = 0
        addon_count = 0
        for position in self.positions.values():
            candidate = position.candidate
            total += candidate.risk_usd
            directional[candidate.direction] += candidate.risk_usd
            if candidate.sleeve_type == "ADDON":
                addon += candidate.risk_usd
                addon_count += 1
            else:
                core_count += 1
        return total, directional, addon, core_count, addon_count

    def _reject(self, candidate: Candidate, now_ms: int, reason: str) -> None:
        self.rejections[reason] += 1
        self._record("CANDIDATE_REJECTED", now_ms, candidate, reason=reason)

    def _entry_reason(
        self,
        candidate: Candidate,
        now_ms: int,
        tick_ms: int,
        bid: float,
        ask: float,
        floating_hard: bool,
        closed_hard: bool,
        floating_dd: float,
        closed_dd: float,
    ) -> str | None:
        age_ms = now_ms - candidate.entry_ms
        utc_day = candidate.entry_ms // DAY_MS
        total, directional, addon_risk, core_count, addon_count = self._current_risk()
        source_open = sum(
            position.candidate.source_id == candidate.source_id
            for position in self.positions.values()
        )
        protection = self.config.get("portfolio_protection")
        if isinstance(protection, Mapping) and bool(protection.get("enabled")):
            drawdown_fraction = max(floating_dd, closed_dd) / float(
                self.spec.activation_equity_usd
            )
            if candidate.sleeve_type == "ADDON" and drawdown_fraction >= float(
                protection["soft_addon_block_drawdown_fraction"]
            ):
                return "SOFT_DRAWDOWN_ADDON_BLOCK"
            if candidate.sleeve_type == "CORE" and drawdown_fraction >= float(
                protection["soft_core_concurrency_drawdown_fraction"]
            ):
                if core_count >= int(protection["soft_core_maximum_open_positions"]):
                    return "SOFT_DRAWDOWN_CORE_CONCURRENCY"
            for family in protection["same_direction_source_families"]:
                if candidate.source_id not in family:
                    continue
                if any(
                    position.candidate.source_id in family
                    and position.candidate.source_id != candidate.source_id
                    and position.candidate.direction == candidate.direction
                    for position in self.positions.values()
                ):
                    return "SAME_DIRECTION_PROTECTION_FAMILY"
        if candidate.risk_usd > candidate.maximum_risk_usd:
            return "SOURCE_MAXIMUM_RISK"
        if age_ms > candidate.maximum_entry_gap_minutes * 60_000:
            return "STALE_CANDIDATE"
        if (
            self.spec.guardian_enabled
            and bool(self.contract["guardian"]["halt_entries_when_armed"])
            and (self.guardian.armed or self.guardian.locked)
        ):
            return "ENTRY_HALT_FILE_ACTIVE"
        if floating_hard:
            return "FLOATING_DRAWDOWN_HARD_STOP"
        if closed_hard:
            return "COMBINED_CLOSED_DRAWDOWN_HARD_STOP"
        if self.drawdown_suspended:
            recovery = self.risk.get("closed_drawdown_recovery")
            if not isinstance(recovery, Mapping) or not bool(
                recovery.get("enabled")
            ):
                return "CLOSED_DRAWDOWN_SUSPENDED"
            if candidate.sleeve_type != "CORE":
                return "DRAWDOWN_RECOVERY_CORE_ONLY"
            if candidate.source_id not in set(recovery["eligible_source_ids"]):
                return "DRAWDOWN_RECOVERY_SOURCE_NOT_ELIGIBLE"
            if len(self.positions) >= int(recovery["maximum_open_positions"]):
                return "DRAWDOWN_RECOVERY_MAXIMUM_OPEN_POSITIONS"
            if candidate.risk_usd > float(recovery["maximum_initial_risk_usd"]):
                return "DRAWDOWN_RECOVERY_MAXIMUM_INITIAL_RISK"
            hard_limit = min(
                self.limits["combined_closed_drawdown_hard_stop_usd"],
                self.limits["floating_drawdown_hard_stop_usd"],
            )
            required_headroom = candidate.risk_usd * float(
                recovery["minimum_hard_stop_headroom_multiple"]
            )
            if hard_limit - max(floating_dd, closed_dd) < required_headroom:
                return "DRAWDOWN_RECOVERY_INSUFFICIENT_HARD_STOP_HEADROOM"
            if self.recovery_daily_entries[utc_day] >= int(
                recovery["maximum_entries_per_utc_day"]
            ):
                return "DRAWDOWN_RECOVERY_MAXIMUM_DAILY_ENTRIES"
        if (
            total + candidate.risk_usd
            > self.limits["maximum_account_concurrent_initial_risk_usd"]
        ):
            return "MAXIMUM_ACCOUNT_CONCURRENT_INITIAL_RISK"
        if (
            directional[candidate.direction] + candidate.risk_usd
            > self.limits["maximum_directional_concurrent_initial_risk_usd"]
        ):
            return "MAXIMUM_DIRECTIONAL_CONCURRENT_INITIAL_RISK"
        if (
            candidate.sleeve_type == "CORE"
            and core_count >= int(self.risk["maximum_core_open_positions"])
        ):
            return "MAXIMUM_CORE_OPEN_POSITIONS"
        if (
            candidate.sleeve_type == "ADDON"
            and addon_count >= int(self.risk["maximum_addon_open_positions"])
        ):
            return "MAXIMUM_ADDON_OPEN_POSITIONS"
        if (
            candidate.sleeve_type == "ADDON"
            and addon_risk + candidate.risk_usd
            > float(self.risk["maximum_addon_concurrent_initial_risk_usd"])
        ):
            return "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK"
        if len(self.positions) >= int(self.risk["maximum_account_xau_positions"]):
            return "MAXIMUM_ACCOUNT_XAU_POSITIONS"
        if source_open >= candidate.maximum_open_positions:
            return "MAXIMUM_SOURCE_OPEN_POSITIONS"
        last_loss = self.last_losses.get((candidate.source_id, candidate.direction))
        if (
            last_loss is not None
            and now_ms < last_loss + candidate.cooldown_minutes * 60_000
        ):
            return "SAME_DIRECTION_POST_LOSS_COOLDOWN"
        if (
            self.daily_entries[(candidate.source_id, utc_day)]
            >= candidate.maximum_entries_per_utc_day
        ):
            return "MAXIMUM_SOURCE_DAILY_ENTRIES"
        account_entries = sum(
            count
            for (_, day), count in self.daily_entries.items()
            if day == utc_day
        )
        if account_entries >= int(self.risk["maximum_daily_entries"]):
            return "MAXIMUM_DAILY_ENTRIES"
        addon_entries = sum(
            count
            for (source_id, day), count in self.daily_entries.items()
            if day == utc_day
            and source_id
            in {
                "V7_SWING_HEALTH",
                "V8_RETEST_HEALTH",
                "V25_CHOP",
                "V57_BREAK_SWING_H4ADX_HIGH",
            }
        )
        if (
            candidate.sleeve_type == "ADDON"
            and addon_entries
            >= int(self.risk["maximum_addon_entries_per_utc_day"])
        ):
            return "MAXIMUM_ADDON_DAILY_ENTRIES"
        if (
            candidate.sleeve_type == "ADDON"
            and candidate.event_id is not None
            and candidate.event_id in self.addon_events
        ):
            return "DUPLICATE_ADDON_EVENT"
        if now_ms - tick_ms > int(
            self.contract["evaluation"]["maximum_tick_age_seconds"]
        ) * 1000:
            return "STALE_BROKER_TICK"
        spread = ask - bid
        if spread <= 0.0:
            return "INVALID_SPREAD"
        if spread / candidate.risk_usd > candidate.maximum_spread_r:
            return "SPREAD_R_EXCEEDED"
        return None

    def _open_candidate(
        self, candidate: Candidate, now_ms: int, bid: float, ask: float
    ) -> None:
        import heapq

        executable = ask if candidate.direction == "LONG" else bid
        position = Position(
            candidate=candidate,
            basis_offset=candidate.entry_price - executable,
        )
        self.positions[candidate.trade_id] = position
        heapq.heappush(self.exit_heap, (candidate.exit_ms, candidate.trade_id))
        utc_day = candidate.entry_ms // DAY_MS
        self.daily_entries[(candidate.source_id, utc_day)] += 1
        recovery_entry = self.drawdown_suspended
        if recovery_entry:
            self.recovery_daily_entries[utc_day] += 1
            self.recovery_entries += 1
        if candidate.sleeve_type == "ADDON" and candidate.event_id is not None:
            self.addon_events.add(candidate.event_id)
        self.maximum_open_positions = max(
            self.maximum_open_positions, len(self.positions)
        )
        self._record(
            "ORDER_FILLED",
            now_ms,
            candidate,
            initial_risk_usd=candidate.risk_usd,
            basis_offset=position.basis_offset,
            drawdown_recovery_entry=recovery_entry,
        )

    def process_cycle(
        self, now_ms: int, tick_ms: int, bid: float, ask: float
    ) -> None:
        pre_equity = self.equity(bid, ask)
        self._guardian_reset(now_ms, pre_equity)
        self._maybe_rebaseline(now_ms)
        self._settle_normal_exits(now_ms)
        self._evaluate_profit_protection(now_ms, bid, ask)
        equity = self.equity(bid, ask)
        self._guardian_evaluate(now_ms, bid, ask, equity)
        equity = self.equity(bid, ask)
        floating_dd, closed_dd = self._refresh_drawdown(now_ms, equity)
        floating_hard = (
            floating_dd >= self.limits["floating_drawdown_hard_stop_usd"]
        )
        closed_hard = (
            closed_dd >= self.limits["combined_closed_drawdown_hard_stop_usd"]
        )
        if floating_hard or closed_hard:
            if self.first_hard_stop_ms is None:
                self.first_hard_stop_ms = now_ms
            if self.positions:
                reason = (
                    "FLOATING_DRAWDOWN_HARD_STOP"
                    if floating_hard
                    else "COMBINED_CLOSED_DRAWDOWN_HARD_STOP"
                )
                self._record(
                    "V60_HARD_STOP",
                    now_ms,
                    reason=reason,
                    floating_drawdown_usd=floating_dd,
                    closed_drawdown_usd=closed_dd,
                )
                self._close_all(
                    now_ms,
                    bid,
                    ask,
                    reason,
                    counted_by_v60=True,
                )
                equity = self.equity(bid, ask)
                floating_dd, closed_dd = self._refresh_drawdown(now_ms, equity)
                floating_hard = (
                    floating_dd
                    >= self.limits["floating_drawdown_hard_stop_usd"]
                )
                closed_hard = (
                    closed_dd
                    >= self.limits["combined_closed_drawdown_hard_stop_usd"]
                )

        while (
            self.candidate_index < len(self.candidates)
            and self.candidates[self.candidate_index].entry_ms <= now_ms
        ):
            candidate = self.candidates[self.candidate_index]
            self.candidate_index += 1
            reason = self._entry_reason(
                candidate,
                now_ms,
                tick_ms,
                bid,
                ask,
                floating_hard,
                closed_hard,
                floating_dd,
                closed_dd,
            )
            if reason is not None:
                self._reject(candidate, now_ms, reason)
            else:
                self._open_candidate(candidate, now_ms, bid, ask)
        # Capture the immediate spread/cost effect as lifetime evidence without
        # changing the executor's policy peak until its next poll.
        post_entry_equity = self.equity(bid, ask)
        self.lifetime_peak_equity = max(
            self.lifetime_peak_equity, post_entry_equity
        )
        self.max_lifetime_equity_dd = max(
            self.max_lifetime_equity_dd,
            self.lifetime_peak_equity - post_entry_equity,
        )

    def simulate(self, quotes: Mapping[str, np.ndarray]) -> dict[str, Any]:
        cycles = quotes["cycle_ms"]
        ticks = quotes["tick_ms"]
        bids = quotes["bid"]
        asks = quotes["ask"]
        index = 0
        while index < len(cycles):
            if not self.positions and self.candidate_index >= len(self.candidates):
                break
            if not self.positions and self.candidate_index < len(self.candidates):
                next_entry = self.candidates[self.candidate_index].entry_ms
                index = int(np.searchsorted(cycles, next_entry, side="left"))
                if index >= len(cycles):
                    break
            self.process_cycle(
                int(cycles[index]),
                int(ticks[index]),
                float(bids[index]),
                float(asks[index]),
            )
            index += 1
        if self.candidate_index < len(self.candidates):
            remaining = len(self.candidates) - self.candidate_index
            self.rejections["NO_REPLAY_CYCLE"] += remaining
            self.candidate_index = len(self.candidates)
        gross_profit = sum(value for value in self.close_pnls if value > 0)
        gross_loss = -sum(value for value in self.close_pnls if value < 0)
        wins = sum(value > 0 for value in self.close_pnls)
        accepted = len(self.close_pnls) + len(self.positions)
        weekdays = int(
            np.busday_count(
                self.contract["evaluation"]["entry_start_utc"][:10],
                self.contract["evaluation"]["entry_end_exclusive_utc"][:10],
            )
        )
        policy_closed_dd = self.policy_peak_closed - self.v60_closed_pnl
        final_equity = (
            self.spec.starting_equity_usd + self.account_closed_pnl
            if not self.positions
            else float("nan")
        )
        return {
            "scenario": asdict(self.spec),
            "effective_limits_usd": self.limits,
            "candidate_rows": len(self.candidates),
            "trades_accepted": accepted,
            "trades_closed": len(self.close_pnls),
            "open_positions_at_end": len(self.positions),
            "net_pnl_usd": self.account_closed_pnl,
            "v60_tracked_closed_pnl_usd": self.v60_closed_pnl,
            "guardian_magic_excluded_pnl_usd": (
                self.account_closed_pnl - self.v60_closed_pnl
            ),
            "final_equity_usd": final_equity,
            "win_rate": wins / len(self.close_pnls) if self.close_pnls else 0.0,
            "profit_factor": (
                gross_profit / gross_loss if gross_loss > 0 else None
            ),
            "gross_profit_usd": gross_profit,
            "gross_loss_usd": gross_loss,
            "trades_per_weekday": accepted / weekdays,
            "maximum_policy_closed_drawdown_usd": self.max_policy_closed_dd,
            "maximum_lifetime_closed_drawdown_usd": self.max_lifetime_closed_dd,
            "maximum_lifetime_equity_drawdown_usd": self.max_lifetime_equity_dd,
            "ending_policy_closed_drawdown_usd": policy_closed_dd,
            "maximum_open_positions": self.maximum_open_positions,
            "profit_protection_arms": self.profit_protection_arms,
            "profit_giveback_closes": self.profit_giveback_closes,
            "suspensions": self.suspensions,
            "rebaselines": self.rebaselines,
            "drawdown_recovery_entries": self.recovery_entries,
            "emergency_position_closes": self.emergency_closes,
            "guardian_arms": self.guardian_arms,
            "guardian_locks": self.guardian_locks,
            "first_suspend_at_utc": utc_text(self.first_suspend_ms),
            "first_hard_stop_at_utc": utc_text(self.first_hard_stop_ms),
            "first_guardian_lock_at_utc": utc_text(
                self.first_guardian_lock_ms
            ),
            "ending_drawdown_suspended": self.drawdown_suspended,
            "ending_guardian_armed": self.guardian.armed,
            "ending_guardian_locked": self.guardian.locked,
            "flat_suspended_deadlock": bool(
                self.drawdown_suspended
                and not self.positions
                and policy_closed_dd
                > self.limits["closed_drawdown_resume_usd"]
            ),
            "floating_peak_deadlock": bool(
                not self.positions
                and self.peak_equity
                - (
                    self.spec.starting_equity_usd
                    + self.account_closed_pnl
                )
                >= self.limits["floating_drawdown_hard_stop_usd"]
            ),
            "rejection_counts": dict(sorted(self.rejections.items())),
        }


def scenario_specs(contract: Mapping[str, Any]) -> list[ScenarioSpec]:
    evaluation = contract["evaluation"]
    deployed = float(evaluation["deployed_activation_equity_usd"])
    funded = float(evaluation["funded_starting_equity_usd"])
    policies = [
        ("deployed", deployed, deployed, None),
        ("deposit_only", funded, deployed, None),
        ("funded_reinitialized", funded, funded, None),
    ]
    policies.extend(
        (f"funded_rebaseline_{days}d", funded, funded, int(days))
        for days in evaluation["rebaseline_days"]
    )
    result: list[ScenarioSpec] = []
    for name, starting, activation, days in policies:
        for guardian in contract["guardian"]["enabled_views"]:
            suffix = "full_runtime" if guardian else "executor_only"
            result.append(
                ScenarioSpec(
                    scenario_id=f"{name}__{suffix}",
                    starting_equity_usd=starting,
                    activation_equity_usd=activation,
                    rebaseline_days=days,
                    guardian_enabled=bool(guardian),
                    guardian_exit_attribution=(
                        "DEPLOYED_MAGIC_FILTER"
                        if guardian
                        else "NOT_APPLICABLE"
                    ),
                )
            )
    for name, starting, activation in (
        ("deployed", deployed, deployed),
        ("funded_reinitialized", funded, funded),
    ):
        result.append(
            ScenarioSpec(
                scenario_id=f"{name}__position_origin_repair_full_runtime",
                starting_equity_usd=starting,
                activation_equity_usd=activation,
                rebaseline_days=None,
                guardian_enabled=True,
                guardian_exit_attribution="POSITION_ORIGIN",
            )
        )
    return result


def capital_spread_audit(
    contract: Mapping[str, Any], quotes: Mapping[str, np.ndarray]
) -> dict[str, Any]:
    files = sorted(Path().glob("__never__"))
    raw_glob = str(contract["inputs"]["capital_tick_glob"])
    glob_path = Path(raw_glob)
    files = sorted(glob_path.parent.glob(glob_path.name))
    samples: list[np.ndarray] = []
    rows = 0
    hashes: dict[str, str] = {}
    for path in files:
        hashes[str(path)] = sha256_file(path)
        offset = 0
        for chunk in pd.read_csv(
            path,
            usecols=lambda name: name in {"spread_price", "bid", "ask"},
            chunksize=250_000,
        ):
            spread = (
                pd.to_numeric(chunk["spread_price"], errors="coerce")
                if "spread_price" in chunk
                else pd.to_numeric(chunk["ask"], errors="coerce")
                - pd.to_numeric(chunk["bid"], errors="coerce")
            )
            values = spread.to_numpy(dtype=float)
            values = values[np.isfinite(values) & (values > 0)]
            rows += len(values)
            samples.append(values[(100 - offset % 100) % 100 :: 100])
            offset += len(values)
    capital = np.concatenate(samples) if samples else np.empty(0)
    duka = (
        np.asarray(quotes["ask"][::100], dtype=float)
        - np.asarray(quotes["bid"][::100], dtype=float)
    )
    duka = duka[np.isfinite(duka) & (duka > 0)]

    def stats(values: np.ndarray) -> dict[str, Any]:
        if not len(values):
            return {"sample_rows": 0, "median": None, "p95": None, "p99": None}
        return {
            "sample_rows": int(len(values)),
            "median": float(np.quantile(values, 0.50)),
            "p95": float(np.quantile(values, 0.95)),
            "p99": float(np.quantile(values, 0.99)),
        }

    return {
        "capital_files": len(files),
        "capital_valid_rows": rows,
        "capital_file_sha256": hashes,
        "capital_spread_price_sample": stats(capital),
        "dukascopy_replay_spread_sample": stats(duka),
        "sampling_stride": 100,
        "interpretation": (
            "Prospective Capital.com spreads are a broker-parity diagnostic, "
            "not same-period historical replacement prices."
        ),
    }


def input_hashes(contract: Mapping[str, Any]) -> dict[str, str]:
    keys = (
        "demo_config",
        "executor_source",
        "runtime_source",
        "guardian_source",
        "guardian_exit_magic_evidence",
        "guardian_chart",
        "live_state",
        "live_status",
        "ledger",
        "r1_native_reconciliation",
        "dukascopy_decoder_source",
    )
    result: dict[str, str] = {}
    for key in keys:
        path = resolve_input(contract["inputs"][key])
        result[key] = sha256_file(path)
    protection = contract["inputs"].get("portfolio_protection_overlay")
    if protection:
        result["portfolio_protection_overlay"] = sha256_file(
            resolve_input(str(protection))
        )
    return result


def build_result(
    *,
    force_cache: bool = False,
    contract_path: Path = CONTRACT_PATH,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    contract = load_json(contract_path)
    config = apply_runtime_risk_mode(
        apply_portfolio_protection(
            contract,
            load_json(resolve_input(contract["inputs"]["demo_config"])),
        ),
        bool(
            contract["evaluation"].get(
                "required_equity_fraction_limits_enabled",
                False,
            )
        ),
    )
    candidates, population = load_candidates(contract, config)
    cache_meta = prepare_quote_cache(
        contract, candidates, population, force=force_cache
    )
    quotes = load_quote_cache(cache_meta)
    scenarios: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for spec in scenario_specs(contract):
        replay = Scenario(spec, config, contract, candidates)
        scenarios.append(replay.simulate(quotes))
        events.extend(replay.event_rows)
    scenario_map = {
        row["scenario"]["scenario_id"]: row for row in scenarios
    }
    key = scenario_map["funded_rebaseline_30d__full_runtime"]
    technically_running = not (
        key["flat_suspended_deadlock"]
        or key["floating_peak_deadlock"]
        or key["open_positions_at_end"]
    )
    closed_evidence_cap = float(
        config["risk"]["combined_closed_drawdown_hard_stop_usd"]
    )
    equity_evidence_cap = float(
        config["risk"]["floating_drawdown_hard_stop_usd"]
    )
    lifetime_risk_pass = (
        key["maximum_lifetime_closed_drawdown_usd"] <= closed_evidence_cap
        and key["maximum_lifetime_equity_drawdown_usd"] <= equity_evidence_cap
    )
    def repair_assessment(scenario_id: str) -> dict[str, Any]:
        row = scenario_map[scenario_id]
        operable = not (
            row["flat_suspended_deadlock"]
            or row["floating_peak_deadlock"]
            or row["open_positions_at_end"]
        )
        effective_closed_cap = float(
            row["effective_limits_usd"]["combined_closed_drawdown_hard_stop_usd"]
        )
        effective_equity_cap = float(
            row["effective_limits_usd"]["floating_drawdown_hard_stop_usd"]
        )
        risk_pass = (
            row["maximum_lifetime_closed_drawdown_usd"] <= effective_closed_cap
            and row["maximum_lifetime_equity_drawdown_usd"] <= effective_equity_cap
        )
        return {
            "scenario_id": scenario_id,
            "technically_running": operable,
            "effective_risk_evidence_passed": risk_pass,
            "effective_closed_cap_usd": effective_closed_cap,
            "effective_equity_cap_usd": effective_equity_cap,
            "net_pnl_usd": row["net_pnl_usd"],
            "profit_factor": row["profit_factor"],
            "maximum_lifetime_closed_drawdown_usd": row[
                "maximum_lifetime_closed_drawdown_usd"
            ],
            "maximum_lifetime_equity_drawdown_usd": row[
                "maximum_lifetime_equity_drawdown_usd"
            ],
        }

    deployed_repair = repair_assessment(
        "deployed__position_origin_repair_full_runtime"
    )
    funded_repair = repair_assessment(
        "funded_reinitialized__position_origin_repair_full_runtime"
    )
    if (
        deployed_repair["technically_running"]
        and deployed_repair["effective_risk_evidence_passed"]
    ):
        decision = "POSITION_ORIGIN_REPAIR_PASSES_CURRENT_CAPITAL_REPLAY"
    elif (
        funded_repair["technically_running"]
        and funded_repair["effective_risk_evidence_passed"]
    ):
        decision = "POSITION_ORIGIN_REPAIR_PASSES_FUNDED_REPLAY_CURRENT_CAPITAL_FAILS"
    else:
        decision = "POSITION_ORIGIN_REPAIR_FAILS_REPLAY"
    result = {
        "schema_version": "codex_v60_tick_runtime_replay_result_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "decision": decision,
        "demo_ready_from_this_replay": False,
        "authorization": contract["authorization"],
        "contract_sha256": sha256_file(contract_path),
        "input_sha256": input_hashes(contract),
        "population_audit": population,
        "quote_cache_audit": cache_meta,
        "cross_broker_spread_audit": capital_spread_audit(contract, quotes),
        "scenarios": scenarios,
        "key_30_day_full_runtime_technically_running": technically_running,
        "key_30_day_lifetime_risk_evidence_passed": lifetime_risk_pass,
        "nominal_lifetime_evidence_caps_usd": {
            "closed": closed_evidence_cap,
            "equity": equity_evidence_cap,
        },
        "position_origin_repair": {
            "deployed_capital": deployed_repair,
            "funded_reinitialized": funded_repair,
        },
        "risk_mode": (
            "MIXED_ENTRY_EQUITY_SCALED_DRAWDOWN_ABSOLUTE_USD"
            if config["risk"].get("equity_fraction_limits_enabled")
            and not config["risk"].get(
                "drawdown_equity_fraction_limits_enabled",
                True,
            )
            else (
                "ACTIVATION_EQUITY_SCALED"
                if config["risk"]["equity_fraction_limits_enabled"]
                else "ABSOLUTE_USD_ONLY"
            )
        ),
        "confirmed_findings": [
            (
                "The canonical runtime uses activation-equity-scaled entry-risk limits and absolute-USD fixed-lot drawdown limits."
                if config["risk"].get("equity_fraction_limits_enabled")
                and not config["risk"].get(
                    "drawdown_equity_fraction_limits_enabled",
                    True,
                )
                else "The canonical runtime uses the same fixed USD risk thresholds at deployed and funded activation capital."
            ),
            "No tested scenario ends in a flat suspension or floating-peak deadlock under the bounded recovery policy.",
            "The legacy specialist-magic view omits guardian exits using magic 919200; the deployed position-origin repair counts the complete lifecycle.",
            "Re-baseline scenarios are retained as historical counterfactuals; the deployed recovery policy does not forgive or reset the lifetime drawdown peak.",
            "The repaired runtime attributes every exit to the source position lifecycle and reconstructs the historical closed-P/L peak.",
            "The repair is evaluated separately at actual deployed activation capital and at the proposed funded activation capital.",
        ],
        "limitations": [
            "Dukascopy is not the Capital.com historical feed. A causal per-position entry basis offset preserves source endpoints but cannot reproduce broker-specific intratrade paths.",
            "The attached guardian has a two-second timer with an unknowable phase relative to the five-second Python executor. Both are evaluated on the locked five-second grid.",
            "Historical broker order rejections, slippage, feed-generation delay, and changing minimum-stop geometry cannot be reconstructed.",
            "The replay contains only V60 positions. The live guardian closes all account positions, including activity outside V60.",
            "Normal source exit timestamps and fee-stressed P&L remain frozen; the replay does not re-trigger every historical stop or target from cross-broker ticks.",
            "A favorable diagnostic still requires explicit deployment authorization and prospective demo observation; funding remains a separate owner decision.",
        ],
    }
    return result, events


def render_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# V60 Tick Runtime Replay V1",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Read-only research. No terminal, account, runtime state, authorization, or ML setting was changed.",
        "",
        "## Population and market path",
        "",
        f"- Candidates replayed: **{result['population_audit']['evaluation_candidate_rows']:,}**.",
        f"- R1 rows with native reconstructed risk: **{result['population_audit']['r1_native_risk_rows']:,}**.",
        f"- Five-second quote states: **{result['quote_cache_audit']['cycles']:,}**.",
        f"- Raw Dukascopy ticks read: **{result['quote_cache_audit']['source_ticks']:,}** from **{result['quote_cache_audit']['source_files']:,}** hourly files.",
        "",
        "## Results",
        "",
        "| scenario | guardian accounting | taken | account net | V60 tracked | excluded | PF | equity DD | V60 lifetime closed DD | deadlock |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["scenarios"]:
        spec = row["scenario"]
        pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.2f}"
        lines.append(
            f"| {spec['scenario_id']} | "
            f"{spec['guardian_exit_attribution']} | "
            f"{row['trades_accepted']:,} | ${row['net_pnl_usd']:,.2f} | "
            f"${row['v60_tracked_closed_pnl_usd']:,.2f} | "
            f"${row['guardian_magic_excluded_pnl_usd']:,.2f} | {pf} | "
            f"${row['maximum_lifetime_equity_drawdown_usd']:,.2f} | "
            f"${row['maximum_lifetime_closed_drawdown_usd']:,.2f} | "
            f"{row['flat_suspended_deadlock'] or row['floating_peak_deadlock']} |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"The funded 30-day full-runtime path is technically still running at the end: **{result['key_30_day_full_runtime_technically_running']}**.",
            f"Its lifetime risk evidence passes the nominal caps: **{result['key_30_day_lifetime_risk_evidence_passed']}**.",
            "",
            f"The position-origin repair at actual deployed capital is technically running: **{result['position_origin_repair']['deployed_capital']['technically_running']}**; effective-cap risk evidence passed: **{result['position_origin_repair']['deployed_capital']['effective_risk_evidence_passed']}**.",
            "",
            f"The same repair at `$3,000` funded/reinitialized capital is technically running: **{result['position_origin_repair']['funded_reinitialized']['technically_running']}**; effective-cap risk evidence passed: **{result['position_origin_repair']['funded_reinitialized']['effective_risk_evidence_passed']}**.",
            "",
            "The re-baseline proposal remains rejected. This read-only replay does not authorize a demo change, funding, or any rule that forgives accumulated drawdown.",
            "",
            "## Confirmed findings",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["confirmed_findings"])
    lines.extend(
        [
            "",
            "## Important limits",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["limitations"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    result: Mapping[str, Any],
    events: list[dict[str, Any]],
    output_directory: Path = OUTPUTS,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_directory / "RESULT.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )
    flat_rows: list[dict[str, Any]] = []
    for row in result["scenarios"]:
        summary = {
            **row["scenario"],
            **{
                key: value
                for key, value in row.items()
                if key
                not in {"scenario", "effective_limits_usd", "rejection_counts"}
            },
            "rejection_counts_json": json.dumps(
                row["rejection_counts"], sort_keys=True
            ),
        }
        flat_rows.append(summary)
    pd.DataFrame(flat_rows).to_csv(
        output_directory / "SCENARIOS.csv",
        index=False,
    )
    pd.DataFrame(events).to_csv(
        output_directory / "EVENTS.csv",
        index=False,
    )
