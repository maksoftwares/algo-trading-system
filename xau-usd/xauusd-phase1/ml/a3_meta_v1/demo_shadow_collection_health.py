from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_shadow_collection_health_status_v1"
DEFAULT_MAX_STALE_SECONDS = 24 * 60 * 60
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
OBSERVER_STARTUP_LOG = "a3_ml_prediction_observer_startup.csv"
OBSERVER_PREDICTION_LOG = "a3_ml_prediction_observer_log.csv"
BROKER_SHADOW_TAP_LOG = "a3_ml_broker_shadow_tap.csv"


def check_demo_shadow_collection_health(
    root: Path,
    report_json: Path | None = None,
    *,
    max_stale_seconds: int = DEFAULT_MAX_STALE_SECONDS,
    now_utc: datetime | None = None,
) -> Path:
    root = root.resolve()
    now = _coerce_now(now_utc)
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    upstream = _upstream_reports(reports)
    accounts = [
        _account_collection_health(account, pointer.get("dataset_version", ""), now, max_stale_seconds)
        for account in registry.accounts
    ]
    aggregate = _aggregate(accounts, upstream)
    status = _status(aggregate, upstream)
    authorization = _authorization(status, upstream)
    payload = {
        "status": status,
        "stage": "C33-DEMO-SHADOW-COLLECTION-HEALTH",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "max_stale_seconds": int(max_stale_seconds),
        "summary": {
            "c03_status": upstream["c03"].get("status", "MISSING"),
            "c11_status": upstream["c11"].get("status", "MISSING"),
            "c23_status": upstream["c23"].get("status", "MISSING"),
            "c26_status": upstream["c26"].get("status", "MISSING"),
            "c27_status": upstream["c27"].get("status", "MISSING"),
            "c28_status": upstream["c28"].get("status", "MISSING"),
        },
        "collection_health": aggregate,
        "authorization": authorization,
        "accounts": accounts,
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "dataset_pointer": str(reports / "C02_DATASET_POINTER.json"),
            "c03_training_readiness": str(reports / "C03_TRAINING_READINESS_REPORT.json"),
            "c11_readiness_gap": str(reports / "A3_ML_READINESS_GAP_REPORT.json"),
            "c23_demo_python_launch_controller": str(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
            "c26_research_preview_handoff": str(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"),
            "c27_research_preview_runtime_verifier": str(
                reports / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"
            ),
            "c28_demo_shadow_post_attach_monitor": str(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": bool(authorization["python_demo_predictions_authorized"]),
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status, aggregate),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_shadow_collection_health_md(payload: dict[str, Any]) -> str:
    account_rows = []
    for account in payload.get("accounts", []):
        account_rows.append(
            {
                "Account": account.get("account_label", ""),
                "Handoff rows": str(account.get("handoff", {}).get("row_count", 0)),
                "Handoff current": _yes_no(account.get("handoff", {}).get("dataset_matches_pointer", False)),
                "Observer rows": str(account.get("observer_prediction", {}).get("csv_rows", 0)),
                "Observer age": _age_text(account.get("observer_prediction", {}).get("age_seconds")),
                "Broker tap rows": str(account.get("broker_shadow_tap", {}).get("csv_rows", 0)),
                "Collecting": _yes_no(account.get("collection", {}).get("collecting", False)),
            }
        )
    checks = payload.get("collection_health", {})
    check_rows = [
        {"Check": key, "Passed": str(value).lower()}
        for key, value in checks.items()
        if isinstance(value, bool)
    ]
    return "\n".join(
        [
            "# A3 ML Demo Shadow Collection Health",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Max stale seconds: {payload.get('max_stale_seconds', '')}",
            "",
            "## Upstream Status",
            "",
            f"- C03 readiness: {payload.get('summary', {}).get('c03_status', 'MISSING')}.",
            f"- C23 demo Python launch controller: {payload.get('summary', {}).get('c23_status', 'MISSING')}.",
            f"- C27 runtime verifier: {payload.get('summary', {}).get('c27_status', 'MISSING')}.",
            f"- C28 demo shadow monitor: {payload.get('summary', {}).get('c28_status', 'MISSING')}.",
            "",
            "## Accounts",
            "",
            _table(
                account_rows,
                [
                    "Account",
                    "Handoff rows",
                    "Handoff current",
                    "Observer rows",
                    "Observer age",
                    "Broker tap rows",
                    "Collecting",
                ],
            )
            if account_rows
            else "No accounts configured.",
            "",
            "## Collection Checks",
            "",
            _table(check_rows, ["Check", "Passed"]) if check_rows else "No checks ran.",
            "",
            "## Authorization",
            "",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- EA file drop authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _account_collection_health(
    account: MT5AccountSpec,
    pointer_dataset_version: str,
    now_utc: datetime,
    max_stale_seconds: int,
) -> dict[str, Any]:
    files_root = Path(account.files_roots[0]) if account.files_roots else Path(account.expected_data_path or "") / "MQL5" / "Files"
    handoff = _handoff_summary(files_root / HANDOFF_FILE_NAME, pointer_dataset_version, now_utc)
    observer_startup = _file_summary(files_root / OBSERVER_STARTUP_LOG, now_utc)
    observer_prediction = _file_summary(files_root / OBSERVER_PREDICTION_LOG, now_utc)
    broker_shadow_tap = _file_summary(files_root / BROKER_SHADOW_TAP_LOG, now_utc)
    observer_fresh = _is_fresh(observer_prediction, max_stale_seconds)
    collection = {
        "required_runtime_files_present": bool(
            observer_startup["exists"] and observer_prediction["exists"] and broker_shadow_tap["exists"]
        ),
        "observer_prediction_fresh": observer_fresh,
        "broker_shadow_tap_present": bool(broker_shadow_tap["exists"]),
        "handoff_usable": bool(
            handoff["exists"]
            and handoff["row_count"] > 0
            and handoff["dataset_matches_pointer"]
            and handoff["latest_expires_at_utc"]
            and not handoff["expired"]
        ),
    }
    collection["collecting"] = bool(
        collection["required_runtime_files_present"]
        and collection["observer_prediction_fresh"]
        and collection["handoff_usable"]
    )
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "files_root": str(files_root),
        "files_root_exists": files_root.exists(),
        "files_root_safe": _is_mql5_files_root(files_root),
        "handoff": handoff,
        "observer_startup": observer_startup,
        "observer_prediction": observer_prediction,
        "broker_shadow_tap": broker_shadow_tap,
        "collection": collection,
    }


def _file_summary(path: Path, now_utc: datetime) -> dict[str, Any]:
    csv_summary = _raw_csv_summary(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "last_write_utc": _mtime_utc(path),
        "age_seconds": _age_seconds(path, now_utc),
        **csv_summary,
    }


def _handoff_summary(path: Path, pointer_dataset_version: str, now_utc: datetime) -> dict[str, Any]:
    summary = _file_summary(path, now_utc)
    row_count = 0
    dataset_versions: set[str] = set()
    actions: set[str] = set()
    broker_flags: set[str] = set()
    expires: list[datetime] = []
    last_row: dict[str, str] = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    row_count += 1
                    last_row = {str(key): str(value or "") for key, value in row.items()}
                    if row.get("dataset_version"):
                        dataset_versions.add(str(row["dataset_version"]))
                    if row.get("action"):
                        actions.add(str(row["action"]))
                    if row.get("broker_action_authorized"):
                        broker_flags.add(str(row["broker_action_authorized"]).lower())
                    expiry = _parse_utc(row.get("expires_at_utc", ""))
                    if expiry is not None:
                        expires.append(expiry)
        except (OSError, UnicodeDecodeError, csv.Error):
            row_count = 0
            last_row = {}
    latest_expiry = max(expires) if expires else None
    summary.update(
        {
            "row_count": row_count,
            "dataset_versions": sorted(dataset_versions),
            "dataset_matches_pointer": bool(
                pointer_dataset_version and pointer_dataset_version in dataset_versions
            ),
            "actions": sorted(actions),
            "broker_action_authorized_values": sorted(broker_flags),
            "latest_expires_at_utc": _iso(latest_expiry) if latest_expiry else "",
            "expired": bool(latest_expiry is not None and latest_expiry <= now_utc),
            "tail_by_header": last_row,
        }
    )
    return summary


def _raw_csv_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"line_count": 0, "csv_rows": 0, "csv_header": [], "tail_raw": [], "tail_by_header": {}}
    line_count = 0
    header: list[str] = []
    tail: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                values = [str(item) for item in row]
                if line_count == 0:
                    header = values
                tail = values
                line_count += 1
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"line_count": 0, "csv_rows": 0, "csv_header": [], "tail_raw": [], "tail_by_header": {}}
    tail_by_header = {}
    if line_count > 1 and header and len(header) == len(set(header)):
        tail_by_header = {header[index]: tail[index] if index < len(tail) else "" for index in range(len(header))}
    return {
        "line_count": line_count,
        "csv_rows": max(0, line_count - 1),
        "csv_header": header,
        "tail_raw": tail,
        "tail_by_header": tail_by_header,
    }


def _upstream_reports(reports: Path) -> dict[str, dict[str, Any]]:
    return {
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c11": _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json"),
        "c23": _read_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c26": _read_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"),
        "c27": _read_json(reports / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"),
        "c28": _read_json(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json"),
    }


def _aggregate(accounts: list[dict[str, Any]], upstream: dict[str, dict[str, Any]]) -> dict[str, Any]:
    read_path_confirmed = upstream["c27"].get("status") == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS"
    post_attach_confirmed = upstream["c28"].get("status") == "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS"
    observer_ages = [
        int(account["observer_prediction"]["age_seconds"])
        for account in accounts
        if account["observer_prediction"].get("age_seconds") is not None
    ]
    return {
        "files_roots_exist_all_accounts": all(account["files_root_exists"] for account in accounts),
        "files_roots_safe_all_accounts": all(account["files_root_safe"] for account in accounts),
        "handoff_files_exist_all_accounts": all(account["handoff"]["exists"] for account in accounts),
        "handoff_rows_all_accounts": all(account["handoff"]["row_count"] > 0 for account in accounts),
        "handoff_dataset_current_all_accounts": all(
            account["handoff"]["dataset_matches_pointer"] for account in accounts
        ),
        "handoff_unexpired_all_accounts": all(
            account["handoff"]["latest_expires_at_utc"] and not account["handoff"]["expired"] for account in accounts
        ),
        "observer_startup_present_all_accounts": all(account["observer_startup"]["exists"] for account in accounts),
        "observer_prediction_present_all_accounts": all(account["observer_prediction"]["exists"] for account in accounts),
        "observer_prediction_fresh_all_accounts": all(
            account["collection"]["observer_prediction_fresh"] for account in accounts
        ),
        "broker_shadow_tap_present_all_accounts": all(account["broker_shadow_tap"]["exists"] for account in accounts),
        "research_preview_read_path_confirmed_all_accounts": bool(read_path_confirmed),
        "demo_shadow_post_attach_confirmed_all_accounts": bool(post_attach_confirmed),
        "all_accounts_collecting": all(account["collection"]["collecting"] for account in accounts)
        and bool(read_path_confirmed)
        and bool(post_attach_confirmed),
        "max_observer_prediction_age_seconds": max(observer_ages) if observer_ages else None,
        "total_handoff_rows": sum(int(account["handoff"]["row_count"]) for account in accounts),
        "total_observer_prediction_rows": sum(int(account["observer_prediction"]["csv_rows"]) for account in accounts),
        "total_broker_shadow_tap_rows": sum(int(account["broker_shadow_tap"]["csv_rows"]) for account in accounts),
    }


def _status(aggregate: dict[str, Any], upstream: dict[str, dict[str, Any]]) -> str:
    if not aggregate["files_roots_exist_all_accounts"] or not aggregate["files_roots_safe_all_accounts"]:
        return "PREFLIGHT_BLOCKED"
    if not aggregate["handoff_files_exist_all_accounts"] or not aggregate["handoff_rows_all_accounts"]:
        return "PREFLIGHT_BLOCKED"
    c23_auth = upstream["c23"].get("authorization", {})
    c23_authorized = bool(
        c23_auth.get("python_demo_predictions_authorized", False)
        and c23_auth.get("ea_consumption_authorized", False)
    )
    if c23_authorized and aggregate["all_accounts_collecting"]:
        return "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    if not aggregate["all_accounts_collecting"]:
        return "STALE_OR_PARTIAL_COLLECTION"
    if upstream["c03"].get("status") == "PASS":
        return "READY_FOR_OFFICIAL_PIPELINE_REVIEW"
    return "COLLECTING_LIVE_WAITING_FOR_DATA"


def _authorization(status: str, upstream: dict[str, dict[str, Any]]) -> dict[str, bool]:
    c23_auth = upstream["c23"].get("authorization", {})
    python_authorized = bool(
        status == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
        and c23_auth.get("python_demo_predictions_authorized", False)
    )
    ea_authorized = bool(
        status == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
        and c23_auth.get("ea_consumption_authorized", False)
    )
    return {
        "python_demo_predictions_authorized": python_authorized,
        "ea_consumption_authorized": ea_authorized,
        "broker_action_authorized": False,
    }


def _next_allowed_stage(status: str, aggregate: dict[str, Any]) -> str:
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return "Python demo predictions are authorized for passive EA consumption. Broker action remains false."
    if status == "READY_FOR_OFFICIAL_PIPELINE_REVIEW":
        return "C03 is passing and all accounts are collecting. Run C23/C10 to confirm official demo Python authorization."
    if status == "COLLECTING_LIVE_WAITING_FOR_DATA":
        return "Keep A1/A2/A3 terminals running, continue passive data collection, then rerun C08/C23 after more market data advances."
    if status == "STALE_OR_PARTIAL_COLLECTION":
        if not aggregate.get("observer_prediction_fresh_all_accounts", False):
            return "Observer logs are stale or missing. Reload/attach the observers, wait for fresh rows, then rerun C33 and C23."
        return "Some runtime evidence is missing or not confirmed. Recheck observer/broker shadow attachments, then rerun C33 and C23."
    return "Fix missing MT5 Files roots or handoff files, rerun C26/C27/C28, then rerun C33."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_shadow_collection_health_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c33_demo_shadow_collection_health_report"] = payload["outputs"]["status_report_json"]
    pointer["c33_demo_shadow_collection_health_status"] = payload["status"]
    pointer["c33_all_accounts_collecting"] = bool(payload["collection_health"]["all_accounts_collecting"])
    pointer["c33_observer_prediction_fresh_all_accounts"] = bool(
        payload["collection_health"]["observer_prediction_fresh_all_accounts"]
    )
    pointer["c33_max_observer_prediction_age_seconds"] = payload["collection_health"][
        "max_observer_prediction_age_seconds"
    ]
    pointer["python_demo_predictions_authorized"] = bool(
        payload["authorization"]["python_demo_predictions_authorized"]
    )
    pointer["ea_consumption_authorized"] = bool(payload["authorization"]["ea_consumption_authorized"])
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _mtime_utc(path: Path) -> str:
    if not path.exists():
        return ""
    return _iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))


def _age_seconds(path: Path, now_utc: datetime) -> int | None:
    if not path.exists():
        return None
    age = int((now_utc - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)).total_seconds())
    return max(0, age)


def _is_fresh(summary: dict[str, Any], max_stale_seconds: int) -> bool:
    age = summary.get("age_seconds")
    return bool(summary.get("exists") and age is not None and int(age) <= int(max_stale_seconds))


def _coerce_now(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=timezone.utc)
    return now_utc.astimezone(timezone.utc).replace(microsecond=0)


def _parse_utc(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _is_mql5_files_root(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    return len(parts) >= 2 and parts[-2:] == ["mql5", "files"]


def _age_text(value: Any) -> str:
    if value is None:
        return ""
    return f"{int(value)}s"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
