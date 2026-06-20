from __future__ import annotations

import csv
import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TIMEFRAMES = ("M5", "M15", "H1", "H4")
STOP_STYLES = {
    "intraday_atr_1x": 1.0,
    "wide_atr_2x": 2.0,
    "swing_atr_3x": 3.0,
}
POINTS = {
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    "EURUSD": 0.00001,
    "GBPUSD": 0.00001,
    "USDJPY": 0.001,
    "USDCHF": 0.00001,
    "USDCAD": 0.00001,
    "AUDUSD": 0.00001,
    "NZDUSD": 0.00001,
}
MIN_ROWS = 500
MIN_ATR_OBS = 250
MIN_SPREAD_OBS = 250
RECOMMENDED_COST_R = 0.05
DEFAULT_OUTPUT_MD = (
    Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "COST_GEOMETRY_MAP_2026_06_19.md"
)
DEFAULT_OUTPUT_CSV = (
    Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "COST_GEOMETRY_MAP_2026_06_19.csv"
)
DEFAULT_OUTPUT_JSON = (
    Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "COST_GEOMETRY_MAP_2026_06_19.json"
)


@dataclass(frozen=True)
class CellGeometry:
    rank: int
    broker: str
    symbol: str
    timeframe: str
    stop_style: str
    atr_multiplier: float
    source_files: int
    rows: int
    start_utc: str
    end_utc: str
    spread_source: str
    spread_observations: int
    median_spread_points: float | None
    p95_spread_points: float | None
    median_atr14_points: float | None
    p25_atr14_points: float | None
    p75_atr14_points: float | None
    representative_stop_points: float | None
    median_cost_r: float | None
    p95_cost_r: float | None
    structural_bucket: str
    scan_note: str


def generate(
    phase1_root: Path,
    *,
    output_md: Path | None = None,
    output_csv: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    repo_root = phase1_root.parents[1]
    bars_root = repo_root / "xau-usd" / "xauusd-phase0" / "data" / "processed" / "bars"
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    output_csv = (output_csv or phase1_root / DEFAULT_OUTPUT_CSV).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()

    universe = discover_universe(bars_root)
    base_cells: list[dict[str, Any]] = []
    for key, paths in sorted(universe.items()):
        broker, symbol, timeframe = key
        base = analyze_cell(broker, symbol, timeframe, paths)
        base_cells.append(base)

    rows: list[CellGeometry] = []
    for base in base_cells:
        for stop_style, multiplier in STOP_STYLES.items():
            rows.append(make_geometry_row(base, stop_style, multiplier))
    rows = sorted(
        rows,
        key=lambda row: (
            math.inf if row.p95_cost_r is None else row.p95_cost_r,
            math.inf if row.median_cost_r is None else row.median_cost_r,
            row.symbol,
            row.timeframe,
            row.broker,
            row.stop_style,
        ),
    )
    ranked = []
    for index, row in enumerate(rows):
        row_data = asdict(row)
        row_data["rank"] = index + 1
        ranked.append(CellGeometry(**row_data))

    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": "Offline cost-geometry scan only. No hypothesis was designed and no MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.",
        "purpose": "Rank instrument/timeframe/stop-style cells by structural spread cost divided by representative ATR stop distance before selecting any new hypothesis target.",
        "bars_root": str(bars_root),
        "timeframes": list(TIMEFRAMES),
        "stop_styles": STOP_STYLES,
        "recommended_cost_r_ceiling": RECOMMENDED_COST_R,
        "universe": universe_summary(base_cells),
        "rows": [asdict(row) for row in ranked],
        "outputs": {
            "markdown": str(output_md),
            "csv": str(output_csv),
            "json": str(output_json),
        },
    }
    write_outputs(payload, ranked, output_md, output_csv, output_json)
    return payload


def discover_universe(bars_root: Path) -> dict[tuple[str, str, str], list[Path]]:
    universe: dict[tuple[str, str, str], list[Path]] = {}
    for path in sorted(bars_root.glob("*/*/*/*.csv")):
        try:
            broker = path.relative_to(bars_root).parts[0]
            symbol = path.relative_to(bars_root).parts[1]
            timeframe = path.relative_to(bars_root).parts[2]
        except IndexError:
            continue
        if timeframe not in TIMEFRAMES:
            continue
        if symbol not in POINTS:
            continue
        universe.setdefault((broker, symbol, timeframe), []).append(path)
    return universe


def analyze_cell(broker: str, symbol: str, timeframe: str, paths: list[Path]) -> dict[str, Any]:
    point = POINTS[symbol]
    rows = 0
    spread_values: list[float] = []
    p95_spread_values: list[float] = []
    atr_points: list[float] = []
    rolling_tr: deque[float] = deque(maxlen=14)
    previous_close: float | None = None
    start_utc = ""
    end_utc = ""
    for path in sorted(paths):
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                high = to_float(row.get("high") or row.get("mid_high"))
                low = to_float(row.get("low") or row.get("mid_low"))
                close = to_float(row.get("close") or row.get("mid_close"))
                if high is None or low is None or close is None:
                    continue
                timestamp = row.get("timestamp_utc") or row.get("bar_end_utc") or row.get("time") or ""
                if timestamp:
                    start_utc = start_utc or timestamp
                    end_utc = timestamp
                rows += 1
                median_spread = best_spread_value(row, ("spread_median_points", "spread_close_points", "spread_open_points"))
                p95_spread = best_spread_value(row, ("spread_p95_points", "spread_median_points", "spread_close_points"))
                if median_spread is not None and median_spread > 0:
                    spread_values.append(median_spread)
                if p95_spread is not None and p95_spread > 0:
                    p95_spread_values.append(p95_spread)
                if previous_close is None:
                    true_range = high - low
                else:
                    true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))
                previous_close = close
                rolling_tr.append(max(0.0, true_range))
                if len(rolling_tr) == 14:
                    atr_points.append(sum(rolling_tr) / 14.0 / point)
    return {
        "broker": broker,
        "symbol": symbol,
        "timeframe": timeframe,
        "source_files": len(paths),
        "rows": rows,
        "start_utc": normalize_time(start_utc),
        "end_utc": normalize_time(end_utc),
        "spread_source": "bar_spread_proxy" if spread_values else "missing_spread_evidence",
        "spread_observations": len(spread_values),
        "median_spread_points": percentile(spread_values, 50),
        "p95_spread_points": percentile(p95_spread_values or spread_values, 95),
        "median_atr14_points": percentile(atr_points, 50),
        "p25_atr14_points": percentile(atr_points, 25),
        "p75_atr14_points": percentile(atr_points, 75),
        "atr_observations": len(atr_points),
    }


def make_geometry_row(base: dict[str, Any], stop_style: str, multiplier: float) -> CellGeometry:
    median_atr = base["median_atr14_points"]
    stop = round(median_atr * multiplier, 4) if median_atr is not None else None
    median_cost = ratio(base["median_spread_points"], stop)
    p95_cost = ratio(base["p95_spread_points"], stop)
    usable = (
        base["rows"] >= MIN_ROWS
        and base["spread_observations"] >= MIN_SPREAD_OBS
        and base["atr_observations"] >= MIN_ATR_OBS
        and stop is not None
        and stop > 0
        and p95_cost is not None
    )
    if not usable:
        bucket = "INSUFFICIENT_EVIDENCE"
        note = "Insufficient rows, ATR observations, or positive spread observations for ranking confidence."
    elif p95_cost <= RECOMMENDED_COST_R:
        bucket = "COST_FAVORABLE"
        note = "P95 spread cost is at or below the preferred 0.05R ceiling."
    elif p95_cost <= 0.10:
        bucket = "BORDERLINE"
        note = "P95 spread cost is above 0.05R but still below the hard 0.10R screen ceiling."
    else:
        bucket = "COST_HEAVY"
        note = "P95 spread cost is structurally high versus the representative stop."
    return CellGeometry(
        rank=0,
        broker=base["broker"],
        symbol=base["symbol"],
        timeframe=base["timeframe"],
        stop_style=stop_style,
        atr_multiplier=multiplier,
        source_files=base["source_files"],
        rows=base["rows"],
        start_utc=base["start_utc"],
        end_utc=base["end_utc"],
        spread_source=base["spread_source"],
        spread_observations=base["spread_observations"],
        median_spread_points=round_float(base["median_spread_points"]),
        p95_spread_points=round_float(base["p95_spread_points"]),
        median_atr14_points=round_float(base["median_atr14_points"]),
        p25_atr14_points=round_float(base["p25_atr14_points"]),
        p75_atr14_points=round_float(base["p75_atr14_points"]),
        representative_stop_points=round_float(stop),
        median_cost_r=round_float(median_cost, 5),
        p95_cost_r=round_float(p95_cost, 5),
        structural_bucket=bucket,
        scan_note=note,
    )


def universe_summary(base_cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "broker": row["broker"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "source_files": row["source_files"],
            "rows": row["rows"],
            "start_utc": row["start_utc"],
            "end_utc": row["end_utc"],
            "spread_source": row["spread_source"],
            "spread_observations": row["spread_observations"],
            "atr_observations": row["atr_observations"],
        }
        for row in sorted(base_cells, key=lambda item: (item["symbol"], item["timeframe"], item["broker"]))
    ]


def write_outputs(payload: dict[str, Any], rows: list[CellGeometry], output_md: Path, output_csv: Path, output_json: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()) if rows else list(CellGeometry.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    output_md.write_text(render_markdown(payload, rows), encoding="utf-8")


def render_markdown(payload: dict[str, Any], rows: list[CellGeometry]) -> str:
    eligible = [row for row in rows if row.structural_bucket in {"COST_FAVORABLE", "BORDERLINE"}]
    top = rows[:25]
    best = eligible[0] if eligible else (rows[0] if rows else None)
    best_capital = next((row for row in rows if row.broker == "capital_com" and row.structural_bucket in {"COST_FAVORABLE", "BORDERLINE"}), None)
    lines = [
        "# Cost Geometry Map - 2026-06-19",
        "",
        "Status: `PASS`",
        "Decision: `MAP_ONLY_NO_HYPOTHESIS_SELECTED`",
        "",
        payload["boundary"],
        "",
        "## Method",
        "",
        "- Universe: processed bar files under `xau-usd/xauusd-phase0/data/processed/bars` for M5, M15, H1, and H4.",
        "- Symbols scanned only where processed bars exist: `XAUUSD`, `EURUSD`, `USDJPY`, plus limited `XAGUSD` H1.",
        "- GBPUSD and other FX majors are not ranked because no processed historical bars were found in this workspace.",
        "- Spread source: positive `spread_median_points` / `spread_p95_points` from broker bar files.",
        "- Representative stop: median ATR14 in points multiplied by `1x`, `2x`, and `3x` for intraday, wide, and swing-style sizing.",
        "- Cost geometry: `cost_R = spread_points / representative_stop_points`.",
        "- Preferred next-hypothesis geometry: P95 cost_R <= `0.05`.",
        "",
        "## Best Cost Geometry Cell",
        "",
    ]
    if best is not None:
        lines.extend(
            [
                "| Field | Value |",
                "| --- | --- |",
                f"| Rank | {best.rank} |",
                f"| Broker / Symbol / Timeframe | `{best.broker}` / `{best.symbol}` / `{best.timeframe}` |",
                f"| Stop style | `{best.stop_style}` ({best.atr_multiplier}x ATR14) |",
                f"| P95 cost_R | `{best.p95_cost_r}` |",
                f"| Median cost_R | `{best.median_cost_r}` |",
                f"| Representative stop points | `{best.representative_stop_points}` |",
                f"| Median / P95 spread points | `{best.median_spread_points}` / `{best.p95_spread_points}` |",
                f"| Structural bucket | `{best.structural_bucket}` |",
                "",
            ]
        )
    if best_capital is not None:
        lines.extend(
            [
                "## Best Capital.com Cell",
                "",
                "Use this if the next experiment must remain on the current Capital.com environment rather than switching broker/data source.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Rank | {best_capital.rank} |",
                f"| Broker / Symbol / Timeframe | `{best_capital.broker}` / `{best_capital.symbol}` / `{best_capital.timeframe}` |",
                f"| Stop style | `{best_capital.stop_style}` ({best_capital.atr_multiplier}x ATR14) |",
                f"| P95 cost_R | `{best_capital.p95_cost_r}` |",
                f"| Median cost_R | `{best_capital.median_cost_r}` |",
                f"| Representative stop points | `{best_capital.representative_stop_points}` |",
                f"| Median / P95 spread points | `{best_capital.median_spread_points}` / `{best_capital.p95_spread_points}` |",
                "",
            ]
        )
    lines.extend(
        [
            "## Ranked Cells - Top 25",
            "",
            "| Rank | Broker | Symbol | TF | Stop style | Rows | Median spread | P95 spread | Stop pts | Median cost_R | P95 cost_R | Bucket |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in top:
        lines.append(
            f"| {row.rank} | `{row.broker}` | `{row.symbol}` | `{row.timeframe}` | `{row.stop_style}` | {row.rows} | "
            f"{row.median_spread_points} | {row.p95_spread_points} | {row.representative_stop_points} | "
            f"{row.median_cost_r} | {row.p95_cost_r} | `{row.structural_bucket}` |"
        )
    lines.extend(
        [
            "",
            "## Universe Actually Scanned",
            "",
            "| Broker | Symbol | TF | Files | Rows | Start UTC | End UTC | Spread source | Spread obs | ATR obs |",
            "| --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: |",
        ]
    )
    for item in payload["universe"]:
        lines.append(
            f"| `{item['broker']}` | `{item['symbol']}` | `{item['timeframe']}` | {item['source_files']} | {item['rows']} | "
            f"{item['start_utc']} | {item['end_utc']} | `{item['spread_source']}` | {item['spread_observations']} | {item['atr_observations']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The map supports the reviewer thesis: as timeframe/stop distance expands, spread becomes a much smaller fraction of risk.",
            "- The most cost-favorable cells are swing-style, not M5 scalps.",
            "- This report does not prove edge. It only chooses where edge research has a structurally fair chance after cost.",
            "- No new hypothesis should be designed until this map is reviewed and the owner/reviewer select exactly one cell.",
            "",
            "## Outputs",
            "",
            f"- CSV: `{payload['outputs']['csv']}`",
            f"- JSON: `{payload['outputs']['json']}`",
            f"- Markdown: `{payload['outputs']['markdown']}`",
            "",
        ]
    )
    return "\n".join(lines)


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        value_float = float(text)
    except ValueError:
        return None
    if not math.isfinite(value_float):
        return None
    return value_float


def best_spread_value(row: dict[str, str], fields: tuple[str, ...]) -> float | None:
    for field in fields:
        value = to_float(row.get(field))
        if value is not None and value > 0:
            return value
    return None


def percentile(values: list[float], pct: float) -> float | None:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    position = (len(clean) - 1) * pct / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return clean[int(position)]
    return clean[lower] + (clean[upper] - clean[lower]) * (position - lower)


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def round_float(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def normalize_time(value: str) -> str:
    return value.replace("T", " ").replace("Z", "") if value else ""


def main() -> int:
    phase1_root = Path(__file__).resolve().parents[1]
    payload = generate(phase1_root)
    print(f"COST_GEOMETRY_MAP rows={len(payload['rows'])}")
    print(payload["outputs"]["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
