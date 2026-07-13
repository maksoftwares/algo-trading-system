from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import run_a1_r2_continuation_short_v1_exact as continuation_v1
import run_a1_r2_continuation_short_v2_repair_exact as continuation_v2
import run_a1_r2_continuation_short_v4_volatility_gate_exact as continuation_v4
import run_a1_r2_pullback_rejection_short_v1_exact as pullback_v1
import run_a1_r2_pullback_rejection_short_v2_repair_exact as pullback_v2
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
PREREG = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_R2_MODE27_PREHISTORY_OVERLAP_CONTROLS_PREREG_2026_07_10.md"
)
EA_SOURCE = mt5.EA_SOURCE
FROM_DATE = "2016.01.01"
TO_DATE = "2021.12.31"
WINDOW_ID = "prehistory_201601_202112"
OUTPUT_PREFIX = "A1_XAU_R2_CONTROL_PREHISTORY_201601_202112"
TAG = "A1_XAU_R2_CONTROL_PREHISTORY_201601_202112"
TESTER_DEPOSIT = "1000"
TESTER_CURRENCY = "USD"
HISTORICAL_RUN_AUTHORIZED = False
RUNNER_COMPLETE = True


@dataclass(frozen=True)
class ControlSpec:
    control_id: str
    source_module: ModuleType
    source_runner: Path
    variant_name: str
    input_sha256: str
    source_priority: int
    normalizer: Callable[..., list[dict[str, Any]]]
    normalizer_name: str

    @property
    def normalized_path(self) -> Path:
        return REPORTS_DIR / f"{OUTPUT_PREFIX}_{self.control_id}_NORMALIZED_TRADES.csv"


CONTROL_SPECS = (
    ControlSpec(
        control_id="r2_pullback_rejection_v1_h1",
        source_module=pullback_v1,
        source_runner=Path(pullback_v1.__file__).resolve(),
        variant_name="r2_pullback_short_h1_confirm",
        input_sha256="9c84ccab846a723465a2ed23b2f31f2c94364ea18eff66610d98d3aadfff6466",
        source_priority=84,
        normalizer=pullback_v1.r2_rows,
        normalizer_name="run_a1_r2_pullback_rejection_short_v1_exact.r2_rows",
    ),
    ControlSpec(
        control_id="r2_pullback_rejection_v2_body58",
        source_module=pullback_v2,
        source_runner=Path(pullback_v2.__file__).resolve(),
        variant_name="r2_h1_m5_body58",
        input_sha256="c7b68ed3187cf6c1303b556c9e81b2ec74add0c94dd7e920f50d2dc95c05468a",
        source_priority=91,
        normalizer=pullback_v1.r2_rows,
        normalizer_name="run_a1_r2_pullback_rejection_short_v1_exact.r2_rows",
    ),
    ControlSpec(
        control_id="r2_continuation_v1_body45",
        source_module=continuation_v1,
        source_runner=Path(continuation_v1.__file__).resolve(),
        variant_name="r2_impulse_retest_body45",
        input_sha256="bab0cd951b34fed2d5bb8ff93a53c7bbf37833223b965d1f0a22efcf3df179af",
        source_priority=98,
        normalizer=continuation_v1.continuation_rows,
        normalizer_name="run_a1_r2_continuation_short_v1_exact.continuation_rows",
    ),
    ControlSpec(
        control_id="r2_continuation_v2_break15_30",
        source_module=continuation_v2,
        source_runner=Path(continuation_v2.__file__).resolve(),
        variant_name="r2_impulse_break15_30_cap20",
        input_sha256="b1c2290ecd60e597c34f0f47150e238c00989b491c1b0ee49235e6dc518697e9",
        source_priority=102,
        normalizer=continuation_v1.continuation_rows,
        normalizer_name="run_a1_r2_continuation_short_v1_exact.continuation_rows",
    ),
    ControlSpec(
        control_id="r2_continuation_v4_atr45",
        source_module=continuation_v4,
        source_runner=Path(continuation_v4.__file__).resolve(),
        variant_name="r2_impulse_body45_atr45",
        input_sha256="4643f786ef326c314dd26f9102c99b8ab2f902d3689772140fc396b99f1ef635",
        source_priority=121,
        normalizer=continuation_v1.continuation_rows,
        normalizer_name="run_a1_r2_continuation_short_v1_exact.continuation_rows",
    ),
)

EXPECTED_CONTROL_IDS = (
    "r2_pullback_rejection_v1_h1",
    "r2_pullback_rejection_v2_body58",
    "r2_continuation_v1_body45",
    "r2_continuation_v2_break15_30",
    "r2_continuation_v4_atr45",
)

MANIFEST_PATH = REPORTS_DIR / f"{OUTPUT_PREFIX}_PROVENANCE.json"
MT5_REPORT_MD = REPORTS_DIR / f"{OUTPUT_PREFIX}_MT5.md"
MT5_REPORT_JSON = REPORTS_DIR / f"{OUTPUT_PREFIX}_MT5.json"

NORMALIZED_FIELDS = (
    "component",
    "source_id",
    "upstream_source_id",
    "upstream_component",
    "family_group",
    "source_priority",
    "cell_id",
    "component_priority",
    "variant_name",
    "entry_time",
    "entry_date",
    "exit_time",
    "exit_date",
    "direction",
    "pnl_usd",
    "tickets",
    "lots",
    "source_csv",
    "source_row",
    "drop_reason",
    "duplicate_of_source_id",
    "duplicate_of_entry_time",
)
PROVENANCE_FIELDS = (
    "control_id",
    "control_source_runner",
    "control_source_runner_sha256",
    "control_variant",
    "control_run_id",
    "control_input_sha256",
    "control_ea_sha256",
    "control_window",
    "control_period",
    "control_manifest",
    "control_generated_at_utc",
)


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _variant_matches(spec: ControlSpec) -> list[mt5.Variant]:
    return [
        variant
        for variant in spec.source_module.build_variants()
        if variant.name == spec.variant_name
    ]


def resolve_variants() -> dict[str, mt5.Variant]:
    selected: dict[str, mt5.Variant] = {}
    for spec in CONTROL_SPECS:
        matches = _variant_matches(spec)
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one authoritative variant {spec.variant_name!r} "
                f"for {spec.control_id}; found {len(matches)}"
            )
        variant = matches[0]
        observed_hash = stable_hash(variant.tester_inputs)
        if observed_hash != spec.input_sha256:
            raise RuntimeError(
                f"Frozen input drift for {spec.control_id}: "
                f"expected {spec.input_sha256}, observed {observed_hash}"
            )
        selected[spec.control_id] = variant
    return selected


def source_hashes() -> dict[str, str]:
    return {spec.control_id: sha256_file(spec.source_runner) for spec in CONTROL_SPECS}


def runtime_readiness() -> dict[str, bool]:
    return {
        "ea_source_exists": EA_SOURCE.exists(),
        "terminal_exists": (mt5.DEFAULT_BACKTEST_ROOT / "terminal64.exe").exists(),
        "metaeditor_exists": mt5.DEFAULT_METAEDITOR.exists(),
    }


def static_checks() -> dict[str, bool]:
    prereg_text = PREREG.read_text(encoding="utf-8") if PREREG.exists() else ""
    control_ids = tuple(spec.control_id for spec in CONTROL_SPECS)
    unique_matches = all(len(_variant_matches(spec)) == 1 for spec in CONTROL_SPECS)
    frozen_hashes_match = unique_matches and all(
        stable_hash(_variant_matches(spec)[0].tester_inputs) == spec.input_sha256
        for spec in CONTROL_SPECS
    )
    expected_paths = tuple(
        f"{OUTPUT_PREFIX}_{control_id}_NORMALIZED_TRADES.csv"
        for control_id in EXPECTED_CONTROL_IDS
    )
    return {
        "runner_complete": RUNNER_COMPLETE,
        "authorization_flag_is_boolean": isinstance(HISTORICAL_RUN_AUTHORIZED, bool),
        "exact_five_control_ids": control_ids == EXPECTED_CONTROL_IDS,
        "control_ids_unique": len(set(control_ids)) == len(control_ids),
        "authoritative_variant_match_unique": unique_matches,
        "frozen_input_hashes_match": frozen_hashes_match,
        "variant_names_unique": len({spec.variant_name for spec in CONTROL_SPECS}) == 5,
        "source_runners_exist": all(spec.source_runner.exists() for spec in CONTROL_SPECS),
        "source_module_paths_exact": all(
            Path(spec.source_module.__file__).resolve() == spec.source_runner
            for spec in CONTROL_SPECS
        ),
        "window_exact": FROM_DATE == "2016.01.01" and TO_DATE == "2021.12.31",
        "original_account_context_exact": TESTER_DEPOSIT == "1000" and TESTER_CURRENCY == "USD",
        "normalized_filenames_exact": tuple(spec.normalized_path.name for spec in CONTROL_SPECS)
        == expected_paths,
        "manifest_filename_exact": MANIFEST_PATH.name
        == "A1_XAU_R2_CONTROL_PREHISTORY_201601_202112_PROVENANCE.json",
        "prereg_exists": PREREG.exists(),
        "prereg_freezes_window_and_controls": all(
            token in prereg_text
            for token in (
                FROM_DATE,
                TO_DATE,
                *EXPECTED_CONTROL_IDS,
                *(spec.input_sha256 for spec in CONTROL_SPECS),
            )
        ),
        "ea_source_path_exact": EA_SOURCE.resolve()
        == (PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5").resolve(),
    }


def static_payload() -> dict[str, Any]:
    controls: list[dict[str, Any]] = []
    for spec in CONTROL_SPECS:
        matches = _variant_matches(spec)
        variant = matches[0] if len(matches) == 1 else None
        observed_hash = stable_hash(variant.tester_inputs) if variant else None
        controls.append(
            {
                "control_id": spec.control_id,
                "source_runner": rel(spec.source_runner),
                "source_runner_sha256": sha256_file(spec.source_runner)
                if spec.source_runner.exists()
                else None,
                "variant_name": spec.variant_name,
                "run_id": variant.run_id if variant else None,
                "frozen_input_sha256": spec.input_sha256,
                "observed_input_sha256": observed_hash,
                "exact_input_match": observed_hash == spec.input_sha256,
                "normalizer": spec.normalizer_name,
                "source_priority": spec.source_priority,
                "normalized_ledger": rel(spec.normalized_path),
            }
        )
    return {
        "status": "LOCKED_NOT_RUN" if not HISTORICAL_RUN_AUTHORIZED else "AUTHORIZED_NOT_RUN",
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
        "runner_complete": RUNNER_COMPLETE,
        "window": {"id": WINDOW_ID, "from_date": FROM_DATE, "to_date": TO_DATE},
        "tester_account": {"deposit": TESTER_DEPOSIT, "currency": TESTER_CURRENCY},
        "checks": static_checks(),
        "runtime_readiness": runtime_readiness(),
        "ea_source": rel(EA_SOURCE),
        "ea_source_sha256": sha256_file(EA_SOURCE) if EA_SOURCE.exists() else None,
        "controls": controls,
        "manifest": rel(MANIFEST_PATH),
    }


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def provenance_for_rows(
    spec: ControlSpec,
    variant: mt5.Variant,
    rows: list[dict[str, Any]],
    *,
    source_runner_sha256: str,
    ea_sha256: str,
    generated_at_utc: str,
) -> list[dict[str, Any]]:
    provenance = {
        "control_id": spec.control_id,
        "control_source_runner": rel(spec.source_runner),
        "control_source_runner_sha256": source_runner_sha256,
        "control_variant": variant.name,
        "control_run_id": variant.run_id,
        "control_input_sha256": spec.input_sha256,
        "control_ea_sha256": ea_sha256,
        "control_window": WINDOW_ID,
        "control_period": f"{FROM_DATE}->{TO_DATE}",
        "control_manifest": rel(MANIFEST_PATH),
        "control_generated_at_utc": generated_at_utc,
    }
    return [{**row, **provenance} for row in rows]


def write_normalized_ledger(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[*NORMALIZED_FIELDS, *PROVENANCE_FIELDS],
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _serialize(row.get(key, "")) for key in writer.fieldnames})


def _csv_row_count(path: Path, *, delimiter: str = ",") -> int:
    if not path.exists():
        return -1
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _row in csv.DictReader(handle, delimiter=delimiter))


def _read_order_failures(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get("action") == "ORDER_SEND_FAIL"
        ]


def _mt5_total_trades(result: dict[str, Any]) -> int:
    raw = str(result.get("mt5_report_metrics", {}).get("Total Trades", "0"))
    return int(re.sub(r"[^0-9]", "", raw) or "0")


def execution_reconciliation(
    spec: ControlSpec,
    variant: mt5.Variant,
    result: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    actions = result.get("order_activity", {}).get("actions", {})
    successful_sends = int(actions.get("ORDER_SEND_OK", 0) or 0)
    failed_sends = int(actions.get("ORDER_SEND_FAIL", 0) or 0)
    mt5_trades = _mt5_total_trades(result)
    summary_trades = int(result.get("summary", {}).get("overall", {}).get("trades", 0) or 0)
    trade_csv_rows = _csv_row_count(Path(result["trade_csv"]))
    failures = _read_order_failures(Path(result["order_csv"]))
    start = date(2016, 1, 1)
    end = date(2021, 12, 31)
    checks = {
        "result_identity_matches_variant": result.get("name") == variant.name,
        "successful_sends_match_mt5": successful_sends == mt5_trades,
        "mt5_matches_summary": mt5_trades == summary_trades,
        "mt5_matches_trade_csv": mt5_trades == trade_csv_rows,
        "mt5_matches_normalized": mt5_trades == len(rows),
        "failure_count_matches_order_csv": failed_sends == len(failures),
        "all_failures_described": all(
            bool(row.get("retcode")) and bool(row.get("retcode_description"))
            for row in failures
        ),
        "all_normalized_rows_closed": all(bool(row.get("exit_time")) for row in rows),
        "all_normalized_entries_short": all(str(row.get("direction", "")).upper() == "SHORT" for row in rows),
        "all_entries_inside_frozen_window": all(
            start <= row["entry_date"] <= end for row in rows
        ),
        "frozen_input_hash_still_exact": stable_hash(variant.tester_inputs) == spec.input_sha256,
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "order_send_ok_count": successful_sends,
        "order_send_fail_count": failed_sends,
        "mt5_total_trades": mt5_trades,
        "summary_trade_count": summary_trades,
        "trade_csv_row_count": trade_csv_rows,
        "normalized_trade_count": len(rows),
        "order_send_failures": failures,
    }


def _artifact_paths(result: dict[str, Any]) -> dict[str, str]:
    keys = (
        "tester_config",
        "html_report",
        "trade_csv",
        "order_csv",
        "signal_csv",
        "management_csv",
        "deal_csv",
        "summary_json",
    )
    return {key: str(Path(result[key]).resolve()) for key in keys}


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


def run_historical_package(variant_timeout_seconds: int) -> dict[str, Any]:
    checks = static_checks()
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError("Prehistory control static checks failed: " + ", ".join(failed))
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError(
            "Prehistory overlap-control history is locked; set "
            "HISTORICAL_RUN_AUTHORIZED=True only after explicit authorization"
        )
    readiness = runtime_readiness()
    if not all(readiness.values()):
        missing = [name for name, ready in readiness.items() if not ready]
        raise RuntimeError("MT5 runtime is not ready: " + ", ".join(missing))

    selected = resolve_variants()
    source_hashes_before = source_hashes()
    ea_hash_before = sha256_file(EA_SOURCE)
    mt5.VARIANTS = [selected[spec.control_id] for spec in CONTROL_SPECS]
    mt5_payload = mt5.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=mt5.safe_name(TAG),
        report_md=MT5_REPORT_MD,
        report_json=MT5_REPORT_JSON,
        variant_timeout_seconds=variant_timeout_seconds,
        deposit=TESTER_DEPOSIT,
        currency=TESTER_CURRENCY,
    )

    source_hashes_after = source_hashes()
    ea_hash_after = sha256_file(EA_SOURCE)
    if source_hashes_after != source_hashes_before:
        raise RuntimeError("An authoritative source runner changed during the MT5 run")
    if ea_hash_after != ea_hash_before:
        raise RuntimeError("The EA source changed during the MT5 run")

    results = mt5_payload.get("variants", [])
    results_by_name = {str(result.get("name")): result for result in results}
    expected_names = {spec.variant_name for spec in CONTROL_SPECS}
    if len(results) != len(CONTROL_SPECS) or set(results_by_name) != expected_names:
        raise RuntimeError(
            f"MT5 result identity mismatch: expected {sorted(expected_names)}, "
            f"observed {sorted(results_by_name)}"
        )

    generated_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    prepared: list[dict[str, Any]] = []
    for spec in CONTROL_SPECS:
        variant = selected[spec.control_id]
        result = results_by_name[variant.name]
        raw_rows = spec.normalizer(result, source_priority=spec.source_priority)
        rows = provenance_for_rows(
            spec,
            variant,
            raw_rows,
            source_runner_sha256=source_hashes_before[spec.control_id],
            ea_sha256=ea_hash_before,
            generated_at_utc=generated_at_utc,
        )
        reconciliation = execution_reconciliation(spec, variant, result, rows)
        prepared.append(
            {
                "spec": spec,
                "variant": variant,
                "result": result,
                "rows": rows,
                "reconciliation": reconciliation,
            }
        )

    failed_reconciliation = [
        item["spec"].control_id
        for item in prepared
        if not item["reconciliation"]["ready"]
    ]
    if failed_reconciliation:
        raise RuntimeError(
            "Control reconciliation failed; no normalized controls were published: "
            + ", ".join(failed_reconciliation)
        )

    temporary_ledgers: list[tuple[Path, Path]] = []
    try:
        for item in prepared:
            final_path = item["spec"].normalized_path
            temporary_path = final_path.with_suffix(final_path.suffix + ".tmp")
            write_normalized_ledger(temporary_path, item["rows"])
            if _csv_row_count(temporary_path) != len(item["rows"]):
                raise RuntimeError(f"Ledger write reconciliation failed: {final_path}")
            temporary_ledgers.append((temporary_path, final_path))

        compiled_ex5 = (
            mt5.DEFAULT_BACKTEST_ROOT / "MQL5" / "Experts" / f"{mt5.EA_NAME}.ex5"
        ).resolve()
        if not compiled_ex5.exists():
            raise RuntimeError(f"Compiled EA artifact is missing: {compiled_ex5}")

        controls_manifest: list[dict[str, Any]] = []
        for item, (temporary_path, final_path) in zip(prepared, temporary_ledgers, strict=True):
            spec = item["spec"]
            variant = item["variant"]
            result = item["result"]
            controls_manifest.append(
                {
                    "control_id": spec.control_id,
                    "source_runner": {
                        "path": rel(spec.source_runner),
                        "sha256": source_hashes_before[spec.control_id],
                        "module": spec.source_module.__name__,
                    },
                    "authoritative_variant": {
                        "name": variant.name,
                        "label": variant.label,
                        "run_id": variant.run_id,
                        "normalizer": spec.normalizer_name,
                        "source_priority": spec.source_priority,
                    },
                    "frozen_tester_inputs": {
                        "sha256": spec.input_sha256,
                        "values": variant.tester_inputs,
                    },
                    "mt5_artifacts": _artifact_paths(result),
                    "normalized_ledger": {
                        "path": rel(final_path),
                        "sha256": sha256_file(temporary_path),
                        "rows": len(item["rows"]),
                        "provenance_fields": list(PROVENANCE_FIELDS),
                    },
                    "reconciliation": item["reconciliation"],
                }
            )

        manifest = {
            "schema_version": 1,
            "status": "READY_EXACT_RECONCILED",
            "generated_at_utc": generated_at_utc,
            "window": {
                "id": WINDOW_ID,
                "from_date": FROM_DATE,
                "to_date": TO_DATE,
            },
            "tester_account": {
                "deposit": TESTER_DEPOSIT,
                "currency": TESTER_CURRENCY,
            },
            "package": {
                "runner": rel(Path(__file__).resolve()),
                "runner_sha256": sha256_file(Path(__file__).resolve()),
                "preregistration": rel(PREREG),
                "preregistration_sha256": sha256_file(PREREG),
                "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
                "anti_sweep_boundary": "Exactly five imported authoritative variants; no input overlay or threshold cell.",
            },
            "ea": {
                "source_path": rel(EA_SOURCE),
                "source_sha256": ea_hash_before,
                "compiled_ex5_path": str(compiled_ex5),
                "compiled_ex5_sha256": sha256_file(compiled_ex5),
            },
            "mt5_run": {
                "report_md": rel(MT5_REPORT_MD),
                "report_json": rel(MT5_REPORT_JSON),
                "compile_log": str(Path(mt5_payload["compile_log"]).resolve()),
                "variant_count": len(results),
            },
            "controls": controls_manifest,
            "all_reconciled": all(
                item["reconciliation"]["ready"] for item in prepared
            ),
        }

        manifest_temporary = MANIFEST_PATH.with_suffix(MANIFEST_PATH.suffix + ".tmp")
        manifest_temporary.write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8"
        )
        for temporary_path, final_path in temporary_ledgers:
            temporary_path.replace(final_path)
        manifest_temporary.replace(MANIFEST_PATH)
    finally:
        for temporary_path, _final_path in temporary_ledgers:
            if temporary_path.exists():
                temporary_path.unlink()

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the five exact frozen R2 prehistory overlap controls required by mode27."
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    payload = static_payload()
    if args.static_only:
        print(json.dumps(payload, indent=2, default=str))
        return 0 if all(payload["checks"].values()) else 1

    manifest = run_historical_package(args.variant_timeout_seconds)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "manifest": str(MANIFEST_PATH),
                "controls": [
                    {
                        "control_id": row["control_id"],
                        "trades": row["normalized_ledger"]["rows"],
                        "ledger": row["normalized_ledger"]["path"],
                    }
                    for row in manifest["controls"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
