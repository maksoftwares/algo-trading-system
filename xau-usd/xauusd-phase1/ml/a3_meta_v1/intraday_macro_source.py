from __future__ import annotations

import csv
import hashlib
import importlib
import json
import shutil
import sys
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


DEFAULT_CONTRACT = Path("config/ml/a3_ml_intraday_macro_source_v1.json")
FOUNDATION_LANE = Path("multi-asset/data-foundation/dukascopy-ticks-v1")
EXPECTED_SYMBOLS = ("DOLLARIDXUSD", "USTBONDTRUSD")
EXPECTED_SOURCE_CODES = ("DOLLAR.IDX-USD", "USTBOND.TR-USD")
EXPECTED_PRICE_BASES = ("Bid", "Ask", "Mid")
VALID_ACQUISITION_STATUSES = {"DOWNLOADED_VALID", "RESUMED_VALID"}


class IntradayMacroSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourcePaths:
    storage_root: Path
    research_root: Path
    run_one: Path
    run_two: Path
    final_bars: Path
    manifest: Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json_bytes(value))


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["symbol", "month", "status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_contract(phase1_root: Path, contract_path: Path | None) -> tuple[Path, dict[str, Any]]:
    path = contract_path or phase1_root / DEFAULT_CONTRACT
    if not path.is_absolute():
        path = phase1_root / path
    contract = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(contract)
    return path, contract


def contract_months(contract: dict[str, Any]) -> list[str]:
    start = pd.Timestamp(contract["window"]["start_utc"])
    end = pd.Timestamp(contract["window"]["end_exclusive_utc"])
    if start.tzinfo is None or end.tzinfo is None:
        raise IntradayMacroSourceError("source window must be timezone aware")
    if start.day != 1 or start.hour or start.minute or start.second:
        raise IntradayMacroSourceError("source start must be a UTC month boundary")
    if end.day != 1 or end.hour or end.minute or end.second:
        raise IntradayMacroSourceError("source end must be a UTC month boundary")
    return [value.strftime("%Y-%m") for value in pd.date_range(start, end, freq="MS", inclusive="left")]


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_intraday_macro_source_v1":
        raise IntradayMacroSourceError("unexpected source contract schema")
    source = contract.get("source", {})
    if source.get("origin") != "https://jetta.dukascopy.com/v1":
        raise IntradayMacroSourceError("official Jetta origin changed")
    instruments = contract.get("instruments", [])
    symbols = tuple(item.get("symbol") for item in instruments)
    codes = tuple(item.get("source_code") for item in instruments)
    if symbols != EXPECTED_SYMBOLS or codes != EXPECTED_SOURCE_CODES:
        raise IntradayMacroSourceError("intraday macro instrument lock changed")
    if any(item.get("price_scale") != 3 or item.get("pip_size") != 0.01 for item in instruments):
        raise IntradayMacroSourceError("instrument price geometry changed")
    months = contract_months(contract)
    expected = int(contract["window"]["expected_months_per_instrument"])
    if len(months) != expected or expected != 90:
        raise IntradayMacroSourceError("expected source chronology changed")
    acquisition = contract.get("acquisition", {})
    if acquisition.get("maximum_concurrency") != 4:
        raise IntradayMacroSourceError("source concurrency lock changed")
    if acquisition.get("retry_count_after_initial_attempt") != 1:
        raise IntradayMacroSourceError("source retry lock changed")
    normalization = contract.get("normalization", {})
    if normalization.get("timeframe_minutes") != 5:
        raise IntradayMacroSourceError("normalization timeframe changed")
    if tuple(normalization.get("price_bases", [])) != EXPECTED_PRICE_BASES:
        raise IntradayMacroSourceError("normalization price bases changed")
    controls = contract.get("research_controls", {})
    if controls.get("source_only") is not True:
        raise IntradayMacroSourceError("source-only control missing")
    if any(
        controls.get(key) is not False
        for key in (
            "gold_outcome_join_authorized",
            "strategy_threshold_search_authorized",
            "model_training_authorized",
        )
    ):
        raise IntradayMacroSourceError("source stage authorizes outcome research")
    authorization = contract.get("authorization", {})
    if any(
        authorization.get(key) is not False
        for key in (
            "python_demo_predictions_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
        )
    ):
        raise IntradayMacroSourceError("source stage authorizes execution")


def _repo_root(phase1_root: Path) -> Path:
    root = phase1_root.resolve().parents[1]
    lane = root / FOUNDATION_LANE
    if not lane.is_dir():
        raise IntradayMacroSourceError(f"Dukascopy foundation lane missing: {lane}")
    return root


def _load_foundation(phase1_root: Path):
    lane = _repo_root(phase1_root) / FOUNDATION_LANE
    source_root = lane / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return importlib.import_module("dukascopy_tick_foundation.foundation")


def install_locked_instruments(foundation: Any, contract: dict[str, Any]) -> None:
    foundation.INSTRUMENTS = {
        item["symbol"]: {
            "source_code": item["source_code"],
            "pip_size": item["pip_size"],
            "price_scale": item["price_scale"],
        }
        for item in contract["instruments"]
    }
    foundation.TIMEFRAMES_MINUTES = {"M5": 5}
    foundation.PRICE_BASES = EXPECTED_PRICE_BASES


def _paths(contract: dict[str, Any]) -> SourcePaths:
    source = contract["source"]
    storage_root = Path(source["external_storage_root"]).resolve()
    research_root = storage_root / source["research_relative_root"]
    return SourcePaths(
        storage_root=storage_root,
        research_root=research_root,
        run_one=research_root / "run-one",
        run_two=research_root / "run-two",
        final_bars=storage_root / contract["outputs"]["bars_relative_path"],
        manifest=storage_root / contract["outputs"]["manifest_relative_path"],
    )


def verify_metadata(contract: dict[str, Any], paths: SourcePaths) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in contract["instruments"]:
        path = paths.storage_root / item["metadata_path"]
        if not path.is_file():
            raise IntradayMacroSourceError(f"instrument metadata missing: {path}")
        digest = _sha256_file(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if digest != item["metadata_sha256"]:
            raise IntradayMacroSourceError(f"instrument metadata hash changed: {item['symbol']}")
        if payload.get("name") != item["source_name"] or payload.get("code") != item["source_code"]:
            raise IntradayMacroSourceError(f"instrument metadata identity changed: {item['symbol']}")
        if payload.get("priceScale") != item["price_scale"] or payload.get("pipValue") != item["pip_size"]:
            raise IntradayMacroSourceError(f"instrument metadata geometry changed: {item['symbol']}")
        rows.append(
            {
                "symbol": item["symbol"],
                "source_name": payload["name"],
                "source_code": payload["code"],
                "metadata_sha256": digest,
                "metadata_bytes": path.stat().st_size,
            }
        )
    return rows


def _selected_months(contract: dict[str, Any], requested: Iterable[str] | None) -> list[str]:
    locked = contract_months(contract)
    if requested is None:
        return locked
    selected = list(dict.fromkeys(requested))
    invalid = sorted(set(selected) - set(locked))
    if invalid:
        raise IntradayMacroSourceError(f"months outside locked window: {invalid}")
    return selected


def acquire_sources(
    foundation: Any,
    contract: dict[str, Any],
    paths: SourcePaths,
    months: Iterable[str],
    concurrency: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        import httpx
    except ImportError:
        client = None
    else:
        client = httpx.Client(
            limits=httpx.Limits(
                max_connections=concurrency, max_keepalive_connections=concurrency
            ),
            headers={"User-Agent": "A3_INTRADAY_MACRO_SOURCE_V1/1.0", "Accept": "application/json"},
            follow_redirects=False,
        )

    def fetcher(url: str, timeout_seconds: int) -> tuple[bytes, dict[str, str], int]:
        if client is None:
            return foundation.http_fetch(url, timeout_seconds)
        foundation.validate_official_url(url)
        try:
            response = client.get(url, timeout=timeout_seconds)
        except httpx.HTTPError as exc:
            raise urllib.error.URLError(str(exc)) from exc
        return (
            response.content,
            {key.lower(): value for key, value in response.headers.items()},
            response.status_code,
        )

    try:
        for item in contract["instruments"]:
            symbol = item["symbol"]
            for month_key in months:
                year, month = (int(value) for value in month_key.split("-"))
                print(f"acquire {symbol} {month_key}", flush=True)
                hourly = foundation.acquire_month(
                    paths.storage_root,
                    symbol,
                    year,
                    month,
                    concurrency=concurrency,
                    fetcher=fetcher,
                )
                foundation.write_month_acquisition_manifest(
                    paths.storage_root, symbol, year, month, hourly
                )
                failed = sum(
                    row.get("status") not in VALID_ACQUISITION_STATUSES
                    for row in hourly
                )
                if failed == 0:
                    foundation.validate_month_acquisition_manifest(
                        paths.storage_root, symbol, year, month
                    )
                    frozen = foundation.freeze_raw_month(
                        paths.storage_root, symbol, year, month
                    )
                    complete = bool(frozen["complete"])
                else:
                    complete = False
                rows.append(
                    {
                        "symbol": symbol,
                        "month": month_key,
                        "expected_hours": len(hourly),
                        "valid_hours": len(hourly) - failed,
                        "failed_hours": failed,
                        "tick_count": sum(
                            int(row.get("tick_count", 0)) for row in hourly
                        ),
                        "raw_bytes": sum(int(row.get("bytes", 0)) for row in hourly),
                        "status": "COMPLETE" if complete else "INCOMPLETE",
                    }
                )
    finally:
        if client is not None:
            client.close()
    return rows


def inventory_raw_sources(
    foundation: Any, contract: dict[str, Any], paths: SourcePaths
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in contract["instruments"]:
        symbol = item["symbol"]
        for month_key in contract_months(contract):
            year, month = (int(value) for value in month_key.split("-"))
            manifest_path = (
                paths.storage_root
                / "raw"
                / symbol
                / f"year={year:04d}"
                / f"month={month:02d}"
                / "_ACQUISITION_MANIFEST.json"
            )
            if not manifest_path.is_file():
                rows.append(
                    {
                        "symbol": symbol,
                        "month": month_key,
                        "expected_hours": len(foundation.hours_in_month(year, month)),
                        "valid_hours": 0,
                        "failed_hours": len(foundation.hours_in_month(year, month)),
                        "tick_count": 0,
                        "raw_bytes": 0,
                        "status": "MISSING",
                    }
                )
                continue
            try:
                foundation.validate_month_acquisition_manifest(
                    paths.storage_root, symbol, year, month
                )
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                hourly = manifest["rows"]
                valid = sum(
                    row.get("status") in VALID_ACQUISITION_STATUSES for row in hourly
                )
                rows.append(
                    {
                        "symbol": symbol,
                        "month": month_key,
                        "expected_hours": len(hourly),
                        "valid_hours": valid,
                        "failed_hours": len(hourly) - valid,
                        "tick_count": sum(
                            int(row.get("tick_count", 0)) for row in hourly
                        ),
                        "raw_bytes": sum(int(row.get("bytes", 0)) for row in hourly),
                        "status": "COMPLETE",
                    }
                )
            except Exception as exc:  # Report corrupt or incomplete cached source without masking it.
                rows.append(
                    {
                        "symbol": symbol,
                        "month": month_key,
                        "expected_hours": len(foundation.hours_in_month(year, month)),
                        "valid_hours": 0,
                        "failed_hours": len(foundation.hours_in_month(year, month)),
                        "tick_count": 0,
                        "raw_bytes": 0,
                        "status": f"INVALID:{type(exc).__name__}",
                    }
                )
    return rows


def normalize_sources(
    foundation: Any,
    contract: dict[str, Any],
    paths: SourcePaths,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for run_name, run_root in (("run-one", paths.run_one), ("run-two", paths.run_two)):
        for item in contract["instruments"]:
            symbol = item["symbol"]
            for month_key in contract_months(contract):
                year, month = (int(value) for value in month_key.split("-"))
                print(f"normalize {run_name} {symbol} {month_key}", flush=True)
                result = foundation.normalize_month(
                    paths.storage_root, run_root, symbol, year, month
                )
                results.append(
                    {
                        "run": run_name,
                        **result["partition"],
                        **{
                            f"integrity_{key}": value
                            for key, value in result["integrity"].items()
                            if key not in {"symbol", "month", "tick_count"}
                        },
                    }
                )
    comparison = foundation.compare_run_hashes(paths.run_one, paths.run_two)
    return results, comparison


def _read_basis_month(run_root: Path, symbol: str, basis: str, month_key: str) -> pd.DataFrame:
    year, month = month_key.split("-")
    path = (
        run_root
        / "bars"
        / symbol
        / basis.lower()
        / "M5"
        / f"year={year}"
        / f"month={month}"
        / "bars.parquet"
    )
    frame = pd.read_parquet(
        path,
        columns=["timestamp_ms", "open", "high", "low", "close", "volume", "tick_count"],
    )
    prefix = f"{symbol.lower()}_{basis.lower()}_"
    return frame.rename(
        columns={column: f"{prefix}{column}" for column in frame.columns if column != "timestamp_ms"}
    )


def build_combined_m5(
    run_root: Path, contract: dict[str, Any], output_path: Path
) -> dict[str, Any]:
    symbol_frames: list[pd.DataFrame] = []
    for item in contract["instruments"]:
        symbol = item["symbol"]
        month_frames: list[pd.DataFrame] = []
        for month_key in contract_months(contract):
            bases = [
                _read_basis_month(run_root, symbol, basis, month_key)
                for basis in EXPECTED_PRICE_BASES
            ]
            merged = bases[0]
            for basis_frame in bases[1:]:
                merged = merged.merge(
                    basis_frame, on="timestamp_ms", how="inner", validate="one_to_one"
                )
            month_frames.append(merged)
        symbol_frame = pd.concat(month_frames, ignore_index=True)
        if symbol_frame["timestamp_ms"].duplicated().any():
            raise IntradayMacroSourceError(f"duplicate M5 bars for {symbol}")
        symbol_frames.append(symbol_frame)
    combined = symbol_frames[0].merge(
        symbol_frames[1], on="timestamp_ms", how="outer", validate="one_to_one"
    )
    combined = combined.sort_values("timestamp_ms", kind="mergesort").reset_index(drop=True)
    combined.insert(
        0, "timestamp_utc", pd.to_datetime(combined["timestamp_ms"], unit="ms", utc=True)
    )
    for symbol in EXPECTED_SYMBOLS:
        combined[f"{symbol.lower()}_available"] = combined[
            f"{symbol.lower()}_mid_close"
        ].notna()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(
        output_path,
        engine="pyarrow",
        compression="zstd",
        index=False,
        row_group_size=100_000,
    )
    return {
        "path": str(output_path),
        "rows": len(combined),
        "first_timestamp_utc": combined.iloc[0]["timestamp_utc"].isoformat()
        if len(combined)
        else "",
        "last_timestamp_utc": combined.iloc[-1]["timestamp_utc"].isoformat()
        if len(combined)
        else "",
        "sha256": _sha256_file(output_path),
        "bytes": output_path.stat().st_size,
    }


def active_day_coverage(
    source_frame: pd.DataFrame, xau_frame: pd.DataFrame
) -> list[dict[str, Any]]:
    xau_days = set(
        pd.to_datetime(xau_frame["timestamp_ms"], unit="ms", utc=True)
        .dt.floor("D")
        .unique()
    )
    rows: list[dict[str, Any]] = []
    for symbol in EXPECTED_SYMBOLS:
        available = source_frame[f"{symbol.lower()}_available"].fillna(False)
        source_days = set(source_frame.loc[available, "timestamp_utc"].dt.floor("D").unique())
        overlap = source_days & xau_days
        rows.append(
            {
                "symbol": symbol,
                "xau_active_days": len(xau_days),
                "source_active_days": len(source_days),
                "overlap_active_days": len(overlap),
                "active_source_day_share_vs_xau": len(overlap) / len(xau_days)
                if xau_days
                else 0.0,
            }
        )
    return rows


def classify_source(
    *, metadata_valid: bool, complete: bool, integrity_valid: bool, coverage_valid: bool, deterministic: bool
) -> str:
    if not metadata_valid or not integrity_valid or not coverage_valid or not deterministic:
        return "INTRADAY_MACRO_SOURCE_INVALID"
    if not complete:
        return "INTRADAY_MACRO_SOURCE_PARTIAL_NOT_READY"
    return "INTRADAY_MACRO_SOURCE_VALID"


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# A3 ML Intraday Macro Source V1 Report",
        "",
        f"Classification: `{report['classification']}`",
        "",
        "This is a source-quality result only. It does not authorize a strategy, model, EA, or broker action.",
        "",
        "## Coverage",
        "",
        "| Instrument | Complete months | Active-day share vs XAU | Ticks |",
        "|---|---:|---:|---:|",
    ]
    coverage_by_symbol = {row["symbol"]: row for row in report["active_day_coverage"]}
    for symbol in EXPECTED_SYMBOLS:
        months = sum(
            row["symbol"] == symbol and row["status"] == "COMPLETE"
            for row in report["monthly_coverage"]
        )
        ticks = sum(
            row["tick_count"]
            for row in report["monthly_coverage"]
            if row["symbol"] == symbol
        )
        share = coverage_by_symbol.get(symbol, {}).get("active_source_day_share_vs_xau", 0.0)
        lines.append(f"| {symbol} | {months} | {share:.4%} | {ticks:,} |")
    lines.extend(
        [
            "",
            "## Determinism",
            "",
            f"- Monthly normalized outputs identical: `{report['determinism']['identical']}`",
            f"- Combined M5 outputs identical: `{report['combined_m5']['deterministic']}`",
            "",
            "## Decision",
            "",
            report["decision"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii", newline="\n")


def run_intraday_macro_source(
    phase1_root: Path,
    contract_path: Path | None = None,
    *,
    months: Iterable[str] | None = None,
    skip_acquisition: bool = False,
    source_only: bool = False,
    concurrency: int | None = None,
) -> str:
    contract_path, contract = _read_contract(phase1_root, contract_path)
    paths = _paths(contract)
    paths.storage_root.mkdir(parents=True, exist_ok=True)
    metadata = verify_metadata(contract, paths)
    foundation = _load_foundation(phase1_root)
    install_locked_instruments(foundation, contract)
    selected = _selected_months(contract, months)
    locked_concurrency = int(contract["acquisition"]["maximum_concurrency"])
    concurrency = locked_concurrency if concurrency is None else concurrency
    if not 1 <= concurrency <= locked_concurrency:
        raise IntradayMacroSourceError("concurrency exceeds the locked maximum")
    if not skip_acquisition:
        acquire_sources(foundation, contract, paths, selected, concurrency)
    coverage = inventory_raw_sources(foundation, contract, paths)
    outputs = contract["outputs"]
    coverage_path = phase1_root / outputs["coverage_csv"]
    _write_csv(coverage_path, coverage)
    complete = all(row["status"] == "COMPLETE" for row in coverage)
    if source_only or not complete:
        classification = "INTRADAY_MACRO_SOURCE_PARTIAL_NOT_READY"
        report = {
            "schema_version": contract["schema_version"],
            "classification": classification,
            "contract_path": str(contract_path),
            "contract_sha256": _sha256_file(contract_path),
            "metadata": metadata,
            "monthly_coverage": coverage,
            "complete": complete,
            "decision": "Resume source acquisition. Outcome research remains locked.",
        }
        _write_json(phase1_root / outputs["report_json"], report)
        return classification

    normalized, comparison = normalize_sources(foundation, contract, paths)
    combined_one_path = paths.run_one / "combined" / "m5_bidask_features_v1.parquet"
    combined_two_path = paths.run_two / "combined" / "m5_bidask_features_v1.parquet"
    combined_one = build_combined_m5(paths.run_one, contract, combined_one_path)
    combined_two = build_combined_m5(paths.run_two, contract, combined_two_path)
    combined_deterministic = combined_one["sha256"] == combined_two["sha256"]
    paths.final_bars.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(combined_one_path, paths.final_bars)
    final_bars = {
        **combined_one,
        "path": str(paths.final_bars),
        "sha256": _sha256_file(paths.final_bars),
    }
    reference = contract["xau_active_day_reference"]
    xau_path = paths.storage_root / reference["feature_path"]
    if _sha256_file(xau_path) != reference["feature_sha256"]:
        raise IntradayMacroSourceError("XAU active-day reference hash changed")
    xau_frame = pd.read_parquet(xau_path, columns=["timestamp_ms"])
    if len(xau_frame) != int(reference["feature_rows"]):
        raise IntradayMacroSourceError("XAU active-day reference row count changed")
    source_frame = pd.read_parquet(
        paths.final_bars,
        columns=[
            "timestamp_utc",
            "DOLLARIDXUSD_available".lower(),
            "USTBONDTRUSD_available".lower(),
        ],
    )
    active_coverage = active_day_coverage(source_frame, xau_frame)
    gates = contract["quality_gates"]
    minimum_share = float(gates["minimum_active_source_day_share_vs_xau"])
    coverage_valid = all(
        row["active_source_day_share_vs_xau"] >= minimum_share
        for row in active_coverage
    )
    negative_spreads = sum(
        int(row.get("integrity_negative_spread_count", 0)) for row in normalized
    )
    conflict_count = sum(
        int(row.get("integrity_conflicting_same_timestamp_count", 0))
        for row in normalized
        if row["run"] == "run-one"
    )
    tick_count = sum(
        int(row.get("tick_count", 0))
        for row in normalized
        if row["run"] == "run-one"
    )
    conflict_share = conflict_count / tick_count if tick_count else 0.0
    integrity_valid = (
        negative_spreads <= int(gates["maximum_negative_spread_count"])
        and conflict_share <= float(gates["maximum_conflicting_same_timestamp_share"])
    )
    deterministic = bool(comparison["identical"] and combined_deterministic)
    classification = classify_source(
        metadata_valid=True,
        complete=complete,
        integrity_valid=integrity_valid,
        coverage_valid=coverage_valid,
        deterministic=deterministic,
    )
    decision = (
        "Source gates pass. A separate preregistration may define a causal gold event census; no strategy is authorized."
        if classification == "INTRADAY_MACRO_SOURCE_VALID"
        else "Source gates failed. Do not join these inputs to gold outcomes."
    )
    manifest = {
        "schema_version": contract["schema_version"],
        "contract_sha256": _sha256_file(contract_path),
        "metadata": metadata,
        "bars": final_bars,
        "monthly_normalization_inventory_sha256": comparison["run_one_inventory_sha256"],
    }
    _write_json(paths.manifest, manifest)
    report = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "contract_path": str(contract_path),
        "contract_sha256": _sha256_file(contract_path),
        "metadata": metadata,
        "monthly_coverage": coverage,
        "active_day_coverage": active_coverage,
        "integrity": {
            "negative_spread_count": negative_spreads,
            "conflicting_same_timestamp_count": conflict_count,
            "conflicting_same_timestamp_share": conflict_share,
        },
        "determinism": comparison,
        "combined_m5": {
            "run_one": combined_one,
            "run_two": combined_two,
            "deterministic": combined_deterministic,
            "final": final_bars,
        },
        "manifest_path": str(paths.manifest),
        "manifest_sha256": _sha256_file(paths.manifest),
        "decision": decision,
        "authorization": contract["authorization"],
    }
    _write_json(phase1_root / outputs["report_json"], report)
    _write_markdown(phase1_root / outputs["report_markdown"], report)
    return classification
