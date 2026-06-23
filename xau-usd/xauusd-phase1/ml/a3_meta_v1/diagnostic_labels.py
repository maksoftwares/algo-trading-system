from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_LABEL_REPORT_JSON = Path("outputs") / "reports" / "C02_LABEL_AUDIT.json"
DEFAULT_SLIPPAGE_REPORT_JSON = Path("outputs") / "reports" / "C02_SLIPPAGE_READINESS.json"
DEFAULT_LABELED_DECISIONS_CSV = Path("outputs") / "reports" / "C02_LABELED_DECISIONS.csv"
POINT = 0.01
MIN_RISK_POINTS = 300
TP_R = 1.5
MAX_HOLD = timedelta(hours=24)
LABEL_ENGINE_VERSION = "c02_diag_tick_label_v1"


@dataclass
class LabelContext:
    signal_id: str
    candidate_id: str
    account_scope: str
    account_label: str
    source_key: tuple[str, str, str]
    decision_time: datetime
    entry_expiry: datetime
    label_end: datetime
    direction: str
    planned_entry: float
    planned_sl: float
    planned_tp: float
    planned_stop_points: float
    spread_points: float
    reason: str
    session_bucket: str
    done: bool = False
    entry_time: datetime | None = None
    actual_entry: float | None = None
    risk_price: float | None = None
    sl: float | None = None
    tp: float | None = None
    exit_time: datetime | None = None
    exit_price: float | None = None
    y_outcome: str = "DATA_UNRESOLVED"
    y_net_R_expected: float | None = None
    y_win_expected: int = 0
    y_MFE_R: float = 0.0
    y_MAE_R: float = 0.0
    label_status: str = "DATA_UNRESOLVED"
    tick_coverage_status: str = "NO_TICKS_SEEN"


def generate_diagnostic_labels(root: Path, label_report_json: Path | None = None) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    dataset_root = Path(pointer["output_root"])
    dataset_version = pointer["dataset_version"]
    decisions = _read_csv(Path(pointer["c02_decisions_csv"]))
    signal_instances = _read_csv(dataset_root / "normalized" / "signals" / "signal_instances.csv")
    by_source = {
        (row["source_file_sha256"], str(row["source_row_number"]), row["logical_source_name"]): row
        for row in signal_instances
    }
    contexts = _contexts_from_decisions(decisions, by_source)
    contexts_by_account: dict[str, list[LabelContext]] = {}
    for context in contexts:
        contexts_by_account.setdefault(context.account_label, []).append(context)
    for account_label, account_contexts in contexts_by_account.items():
        _label_account(dataset_root, account_label, account_contexts, _parse_time(pointer["snapshot_cutoff_utc"]))

    labels_csv = dataset_root / "normalized" / "labels" / "diagnostic_tick_labels.csv"
    label_rows = [_label_row(context) for context in sorted(contexts, key=lambda item: (item.account_scope, item.decision_time, item.signal_id))]
    _write_csv(labels_csv, label_rows, _label_fields())
    labeled_decisions_csv = root / DEFAULT_LABELED_DECISIONS_CSV
    _write_labeled_decisions(labeled_decisions_csv, decisions, label_rows)
    slippage_report = generate_slippage_readiness(root)
    audit = _label_audit_payload(dataset_version, dataset_root, label_rows, labels_csv, labeled_decisions_csv, slippage_report)
    label_report_json = (label_report_json or root / DEFAULT_LABEL_REPORT_JSON).resolve()
    label_report_md = label_report_json.with_suffix(".md")
    label_report_json.parent.mkdir(parents=True, exist_ok=True)
    label_report_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    label_report_md.write_text(render_label_audit_md(audit), encoding="utf-8")
    pointer["diagnostic_label_status"] = audit["status"]
    pointer["label_audit_report"] = str(label_report_json)
    pointer["diagnostic_labels_csv"] = str(labels_csv)
    pointer["c02_labeled_decisions_csv"] = str(labeled_decisions_csv)
    pointer["slippage_readiness_report"] = str(slippage_report)
    pointer["training_authorized"] = False
    pointer["python_demo_predictions_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return label_report_json


def generate_slippage_readiness(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    dataset_root = Path(pointer["output_root"])
    fill_rows = _collect_fill_reconciliation(dataset_root)
    fills_csv = dataset_root / "normalized" / "fills" / "fill_reconciliation.csv"
    _write_csv(fills_csv, fill_rows, _fill_fields())
    account_rows = []
    for account_label in ("A1", "A2", "A3"):
        deals = _read_csv(dataset_root / "raw" / account_label / "history" / "deals.csv")
        account_fills = [row for row in fill_rows if row["account_label"] == account_label]
        entries = [row for row in deals if str(row.get("entry", "")) == "0"]
        exits = [row for row in deals if str(row.get("entry", "")) != "0"]
        sl_exits = [row for row in exits if "[sl" in str(row.get("comment", "")).lower()]
        tp_exits = [row for row in exits if "[tp" in str(row.get("comment", "")).lower()]
        request_price_resolved = len(account_fills)
        status = (
            "ADEQUATE"
            if len(entries) >= 200 and len(sl_exits) >= 100 and len(tp_exits) >= 50 and request_price_resolved >= 200
            else "INSUFFICIENT"
        )
        adverse_values = sorted(float(row["slippage_points_adverse"]) for row in account_fills if row["slippage_points_adverse"] != "")
        account_rows.append(
            {
                "account_label": account_label,
                "entry_fills": len(entries),
                "sl_exits": len(sl_exits),
                "tp_exits": len(tp_exits),
                "timeout_or_other_exits": len(exits) - len(sl_exits) - len(tp_exits),
                "request_price_resolved": request_price_resolved,
                "p50_adverse_slippage_points": _percentile_value(adverse_values, 0.50),
                "p95_adverse_slippage_points": _percentile_value(adverse_values, 0.95),
                "slippage_status": status,
            }
        )
    overall = "ADEQUATE" if all(row["slippage_status"] == "ADEQUATE" for row in account_rows) else "INSUFFICIENT"
    payload = {
        "status": overall,
        "stage": "C02-06",
        "created_at_utc": _utc_now(),
        "dataset_version": pointer["dataset_version"],
        "boundary": {
            "mt5_connection_attempted": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
        },
        "requirements": {
            "entry_fills": 200,
            "sl_exits": 100,
            "tp_exits": 50,
            "request_price_resolved": 200,
        },
        "accounts": account_rows,
        "outputs": {
            "fill_reconciliation_csv": str(fills_csv),
            "fill_reconciliation_sha256": _sha256_file(fills_csv),
        },
        "notes": [
            "Request/result prices are mapped from configured runtime order logs where available.",
            "Final fold-causal P50/P95 slippage remains blocked until every account has adequate request-price coverage inside train-only folds.",
        ],
    }
    report_json = (report_json or root / DEFAULT_SLIPPAGE_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_slippage_readiness_md(payload), encoding="utf-8")
    return report_json


def render_label_audit_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": account,
            "Labels": values["labels"],
            "Mature": values["mature"],
            "TP": values["outcomes"].get("TP", 0),
            "SL": values["outcomes"].get("SL", 0),
            "Timeout": values["timeouts"],
            "Unresolved": values["unresolved"],
        }
        for account, values in payload["by_account"].items()
    ]
    return "\n".join(
        [
            "# C02 Label Audit",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Counts",
            "",
            f"- Labels: {payload['counts']['labels']}",
            f"- Mature labels: {payload['counts']['mature']}",
            f"- Positive labels: {payload['counts']['positive']}",
            f"- Negative labels: {payload['counts']['negative']}",
            f"- Unresolved labels: {payload['counts']['unresolved']}",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Labels", "Mature", "TP", "SL", "Timeout", "Unresolved"]),
            "",
            "## Outputs",
            "",
            f"- Labels CSV: {payload['outputs']['labels_csv']}",
            f"- Labeled decisions CSV: {payload['outputs']['labeled_decisions_csv']}",
            f"- Slippage readiness: {payload['outputs']['slippage_readiness_report']}",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def render_slippage_readiness_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": row["account_label"],
            "Status": row["slippage_status"],
            "Entry": row["entry_fills"],
            "SL": row["sl_exits"],
            "TP": row["tp_exits"],
            "Request Price": row["request_price_resolved"],
            "P95 Adv": row["p95_adverse_slippage_points"],
        }
        for row in payload["accounts"]
    ]
    return "\n".join(
        [
            "# C02 Slippage Readiness",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Status", "Entry", "SL", "TP", "Request Price", "P95 Adv"]),
            "",
            "## Outputs",
            "",
            f"- Fill reconciliation CSV: {payload['outputs']['fill_reconciliation_csv']}",
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in payload["notes"]],
            "",
        ]
    )


def _label_account(dataset_root: Path, account_label: str, contexts: list[LabelContext], snapshot_cutoff: datetime) -> None:
    contexts.sort(key=lambda item: item.decision_time)
    pending_index = 0
    active: list[LabelContext] = []
    tick_files = sorted((dataset_root / "raw" / account_label / "ticks").glob("XAUUSD_ticks_*.csv"))
    for tick_file in tick_files:
        for tick in _iter_ticks(tick_file):
            tick_time = tick["time"]
            while pending_index < len(contexts) and contexts[pending_index].decision_time < tick_time:
                active.append(contexts[pending_index])
                pending_index += 1
            if not active:
                continue
            remaining: list[LabelContext] = []
            for context in active:
                _process_tick(context, tick)
                if not context.done:
                    remaining.append(context)
            active = remaining
    for context in contexts[pending_index:]:
        _finish_without_more_ticks(context, snapshot_cutoff)
    for context in active:
        _finish_without_more_ticks(context, snapshot_cutoff)


def _process_tick(context: LabelContext, tick: dict[str, Any]) -> None:
    if context.done:
        return
    tick_time = tick["time"]
    bid = tick["bid"]
    ask = tick["ask"]
    if context.entry_time is None:
        if tick_time > context.entry_expiry:
            _finish_cancelled(context)
            return
        if tick_time <= context.decision_time:
            return
        context.tick_coverage_status = "HAS_ENTRY_TICK"
        context.entry_time = tick_time
        context.actual_entry = ask if context.direction == "LONG" else bid
        spread = max((ask - bid), 0.0)
        raw_risk = abs(context.planned_entry - context.planned_sl)
        context.risk_price = max(raw_risk, 3 * spread, MIN_RISK_POINTS * POINT)
        if context.direction == "LONG":
            context.sl = context.actual_entry - context.risk_price
            context.tp = context.actual_entry + TP_R * context.risk_price
        else:
            context.sl = context.actual_entry + context.risk_price
            context.tp = context.actual_entry - TP_R * context.risk_price
    if context.entry_time is None or context.actual_entry is None or context.risk_price is None:
        return
    quote = bid if context.direction == "LONG" else ask
    if context.direction == "LONG":
        favorable = (quote - context.actual_entry) / context.risk_price
        adverse = (context.actual_entry - quote) / context.risk_price
        hit_sl = quote <= float(context.sl)
        hit_tp = quote >= float(context.tp)
    else:
        favorable = (context.actual_entry - quote) / context.risk_price
        adverse = (quote - context.actual_entry) / context.risk_price
        hit_sl = quote >= float(context.sl)
        hit_tp = quote <= float(context.tp)
    context.y_MFE_R = max(context.y_MFE_R, favorable)
    context.y_MAE_R = max(context.y_MAE_R, adverse)
    if hit_sl:
        _finish_exit(context, tick_time, quote, "SL", -1.0)
    elif hit_tp:
        _finish_exit(context, tick_time, quote, "TP", TP_R)
    elif tick_time >= context.label_end:
        net_r = favorable
        if net_r > 0.05:
            outcome = "TIMEOUT_POSITIVE"
        elif net_r < -0.05:
            outcome = "TIMEOUT_NEGATIVE"
        else:
            outcome = "TIMEOUT_FLAT"
        _finish_exit(context, tick_time, quote, outcome, net_r)


def _finish_exit(context: LabelContext, when: datetime, price: float, outcome: str, net_r: float) -> None:
    context.exit_time = when
    context.exit_price = price
    context.y_outcome = outcome
    context.y_net_R_expected = net_r
    context.y_win_expected = 1 if net_r > 0 else 0
    context.label_status = outcome
    context.tick_coverage_status = "TICK_LABEL_RESOLVED"
    context.done = True


def _finish_cancelled(context: LabelContext) -> None:
    context.y_outcome = "CANCELLED_NO_FRESH_TICK"
    context.label_status = "CANCELLED_NO_FRESH_TICK"
    context.tick_coverage_status = "NO_FRESH_TICK_BEFORE_ENTRY_EXPIRY"
    context.done = True


def _finish_without_more_ticks(context: LabelContext, snapshot_cutoff: datetime) -> None:
    if context.done:
        return
    if context.entry_time is None:
        if snapshot_cutoff > context.entry_expiry:
            _finish_cancelled(context)
        else:
            context.y_outcome = "NOT_MATURE"
            context.label_status = "NOT_MATURE"
            context.tick_coverage_status = "ENTRY_WINDOW_NOT_MATURE"
            context.done = True
        return
    if snapshot_cutoff < context.label_end:
        context.y_outcome = "NOT_MATURE"
        context.label_status = "NOT_MATURE"
        context.tick_coverage_status = "LABEL_WINDOW_NOT_MATURE"
        context.done = True
        return
    context.y_outcome = "DATA_UNRESOLVED_TIMEOUT"
    context.label_status = "DATA_UNRESOLVED_TIMEOUT"
    context.tick_coverage_status = "NO_TICK_AT_TIMEOUT"
    context.done = True


def _contexts_from_decisions(decisions: list[dict[str, str]], by_source: dict[tuple[str, str, str], dict[str, str]]) -> list[LabelContext]:
    contexts: list[LabelContext] = []
    for row in decisions:
        key = (row.get("source_file_sha256", ""), str(row.get("source_row_number", "")), row.get("source_logical_source_name", ""))
        source = by_source.get(key)
        if source is None:
            continue
        parts = row["signal_id"].split("|")
        if len(parts) != 8:
            continue
        decision_time = _parse_time(row["decision_time"])
        planned_entry = _float(source.get("entry_price"))
        planned_sl = _float(source.get("stop_loss"))
        planned_tp = _float(source.get("take_profit"))
        planned_stop_points = _float(source.get("stop_distance_points"))
        if min(planned_entry, planned_sl, planned_tp, planned_stop_points) <= 0:
            continue
        contexts.append(
            LabelContext(
                signal_id=row["signal_id"],
                candidate_id=row["candidate_id"],
                account_scope=parts[0],
                account_label=source["account_label"],
                source_key=key,
                decision_time=decision_time,
                entry_expiry=_next_m5_close(decision_time),
                label_end=decision_time + MAX_HOLD,
                direction=parts[3],
                planned_entry=planned_entry,
                planned_sl=planned_sl,
                planned_tp=planned_tp,
                planned_stop_points=planned_stop_points,
                spread_points=_float(source.get("spread_points")),
                reason=row.get("reason", ""),
                session_bucket=row.get("session_bucket", ""),
            )
        )
    return contexts


def _label_row(context: LabelContext) -> dict[str, Any]:
    return {
        "signal_id": context.signal_id,
        "candidate_id": context.candidate_id,
        "account_scope": context.account_scope,
        "account_label": context.account_label,
        "decision_time_utc": _fmt(context.decision_time),
        "entry_expiry_utc": _fmt(context.entry_expiry),
        "label_end_time_utc": _fmt(context.label_end),
        "direction": context.direction,
        "planned_entry": _num(context.planned_entry),
        "planned_sl": _num(context.planned_sl),
        "planned_tp": _num(context.planned_tp),
        "planned_stop_points": _num(context.planned_stop_points),
        "entry_time_utc": _fmt(context.entry_time),
        "actual_entry": _num(context.actual_entry),
        "risk_price": _num(context.risk_price),
        "sl": _num(context.sl),
        "tp": _num(context.tp),
        "exit_time_utc": _fmt(context.exit_time),
        "exit_price": _num(context.exit_price),
        "y_outcome": context.y_outcome,
        "y_win_expected": context.y_win_expected,
        "y_net_R_expected": _num(context.y_net_R_expected),
        "y_MFE_R": _num(context.y_MFE_R),
        "y_MAE_R": _num(context.y_MAE_R),
        "label_status": context.label_status,
        "label_mature": str(context.label_status not in {"NOT_MATURE"}).lower(),
        "tick_coverage_status": context.tick_coverage_status,
        "label_engine_version": LABEL_ENGINE_VERSION,
        "model_training_authorized": "false",
    }


def _write_labeled_decisions(path: Path, decisions: list[dict[str, str]], label_rows: list[dict[str, Any]]) -> None:
    by_key = {(row["signal_id"], row["candidate_id"]): row for row in label_rows}
    rows = []
    for row in decisions:
        output = dict(row)
        label = by_key.get((row["signal_id"], row["candidate_id"]))
        if label is not None:
            output["final_r_if_raw"] = label["y_net_R_expected"]
            output["label_status"] = label["label_status"]
            output["candidate_trainable"] = "false"
            output["label_engine_version"] = LABEL_ENGINE_VERSION
        rows.append(output)
    fields = list(decisions[0].keys()) if decisions else []
    for extra in ("label_status", "candidate_trainable", "label_engine_version"):
        if extra not in fields:
            fields.append(extra)
    _write_csv(path, rows, fields)


def _label_audit_payload(
    dataset_version: str,
    dataset_root: Path,
    label_rows: list[dict[str, Any]],
    labels_csv: Path,
    labeled_decisions_csv: Path,
    slippage_report: Path,
) -> dict[str, Any]:
    mature_statuses = {"TP", "SL", "TIMEOUT_POSITIVE", "TIMEOUT_NEGATIVE", "TIMEOUT_FLAT"}
    mature = [row for row in label_rows if row["label_status"] in mature_statuses]
    positive = [row for row in mature if int(row["y_win_expected"]) == 1]
    negative = [row for row in mature if int(row["y_win_expected"]) == 0]
    unresolved = [row for row in label_rows if row["label_status"] not in mature_statuses]
    by_account: dict[str, Any] = {}
    for account in sorted({row["account_label"] for row in label_rows}):
        account_rows = [row for row in label_rows if row["account_label"] == account]
        account_mature = [row for row in account_rows if row["label_status"] in mature_statuses]
        outcomes = Counter(row["label_status"] for row in account_rows)
        by_account[account] = {
            "labels": len(account_rows),
            "mature": len(account_mature),
            "positive": sum(1 for row in account_mature if int(row["y_win_expected"]) == 1),
            "negative": sum(1 for row in account_mature if int(row["y_win_expected"]) == 0),
            "timeouts": sum(outcomes.get(name, 0) for name in ("TIMEOUT_POSITIVE", "TIMEOUT_NEGATIVE", "TIMEOUT_FLAT")),
            "unresolved": len(account_rows) - len(account_mature),
            "outcomes": dict(outcomes),
        }
    return {
        "status": "PASS",
        "stage": "C02-06",
        "created_at_utc": _utc_now(),
        "dataset_version": dataset_version,
        "boundary": {
            "mt5_connection_attempted": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "diagnostic_labels_only": True,
        },
        "counts": {
            "labels": len(label_rows),
            "mature": len(mature),
            "positive": len(positive),
            "negative": len(negative),
            "unresolved": len(unresolved),
            "outcomes": dict(Counter(row["label_status"] for row in label_rows)),
        },
        "by_account": by_account,
        "outputs": {
            "labels_csv": str(labels_csv),
            "labels_sha256": _sha256_file(labels_csv),
            "labeled_decisions_csv": str(labeled_decisions_csv),
            "labeled_decisions_sha256": _sha256_file(labeled_decisions_csv),
            "slippage_readiness_report": str(slippage_report),
        },
        "next_allowed_stage": "C03 label/slippage promotion and leakage validation before training",
    }


def _collect_fill_reconciliation(dataset_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest in sorted(dataset_root.glob("raw/*/manifest/HISTORY_LOG_MANIFEST.json")):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        account_label = payload["account_label"]
        account_scope = payload["account_scope"]
        for source in payload.get("log_records", []):
            if source.get("source_type") != "runtime_order_log" or not source.get("snapshot_path"):
                continue
            path = Path(source["snapshot_path"])
            for index, raw in enumerate(_read_csv(path), start=1):
                if str(raw.get("action", "")).upper() != "ORDER_SEND_OK":
                    continue
                request_price = _float(raw.get("actual_request_price") or raw.get("request_price"))
                result_price = _float(raw.get("result_price"))
                if request_price <= 0 or result_price <= 0:
                    continue
                direction = str(raw.get("direction", "")).upper()
                if direction == "LONG":
                    adverse_points = max((result_price - request_price) / POINT, 0.0)
                    signed_points = (result_price - request_price) / POINT
                elif direction == "SHORT":
                    adverse_points = max((request_price - result_price) / POINT, 0.0)
                    signed_points = (request_price - result_price) / POINT
                else:
                    adverse_points = abs(result_price - request_price) / POINT
                    signed_points = (result_price - request_price) / POINT
                rows.append(
                    {
                        "account_label": account_label,
                        "account_scope": account_scope,
                        "logical_source_name": source.get("logical_source_name", ""),
                        "source_row_number": index,
                        "timestamp_utc": _normalize_time(raw.get("timestamp_utc", "")),
                        "symbol": raw.get("symbol", ""),
                        "candidate": raw.get("candidate", ""),
                        "magic": raw.get("magic", ""),
                        "direction": direction,
                        "order_ticket": raw.get("order_ticket", ""),
                        "deal_ticket": raw.get("deal_ticket", ""),
                        "request_price": _num(request_price),
                        "result_price": _num(result_price),
                        "slippage_points_signed": _num(signed_points),
                        "slippage_points_adverse": _num(adverse_points),
                        "spread_points": raw.get("spread_at_order_points") or raw.get("spread_points", ""),
                        "source_quality": "RUNTIME_ORDER_LOG_REQUEST_AND_RESULT",
                    }
                )
    rows.sort(key=lambda row: (row["account_scope"], row["timestamp_utc"], row["logical_source_name"], int(row["source_row_number"])))
    return rows


def _iter_ticks(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            bid = _float(row.get("bid"))
            ask = _float(row.get("ask"))
            time_text = row.get("time_utc", "")
            if bid <= 0 or ask <= 0 or not time_text:
                continue
            yield {"time": _parse_time(time_text), "bid": bid, "ask": ask}


def _load_pointer(root: Path) -> dict[str, Any]:
    return json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _label_fields() -> list[str]:
    return [
        "signal_id",
        "candidate_id",
        "account_scope",
        "account_label",
        "decision_time_utc",
        "entry_expiry_utc",
        "label_end_time_utc",
        "direction",
        "planned_entry",
        "planned_sl",
        "planned_tp",
        "planned_stop_points",
        "entry_time_utc",
        "actual_entry",
        "risk_price",
        "sl",
        "tp",
        "exit_time_utc",
        "exit_price",
        "y_outcome",
        "y_win_expected",
        "y_net_R_expected",
        "y_MFE_R",
        "y_MAE_R",
        "label_status",
        "label_mature",
        "tick_coverage_status",
        "label_engine_version",
        "model_training_authorized",
    ]


def _fill_fields() -> list[str]:
    return [
        "account_label",
        "account_scope",
        "logical_source_name",
        "source_row_number",
        "timestamp_utc",
        "symbol",
        "candidate",
        "magic",
        "direction",
        "order_ticket",
        "deal_ticket",
        "request_price",
        "result_price",
        "slippage_points_signed",
        "slippage_points_adverse",
        "spread_points",
        "source_quality",
    ]


def _parse_time(value: str) -> datetime:
    text = str(value).strip().replace("T", " ").replace("Z", "").replace("+00:00", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _normalize_time(value: str) -> str:
    if not value:
        return ""
    try:
        return _fmt(_parse_time(value))
    except ValueError:
        return ""


def _next_m5_close(value: datetime) -> datetime:
    floored = value.replace(minute=(value.minute // 5) * 5, second=0, microsecond=0)
    return floored + timedelta(minutes=5)


def _fmt(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _num(value: float | int | None) -> str:
    if value is None:
        return ""
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        return ""
    return f"{number:.8f}".rstrip("0").rstrip(".")


def _float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return number


def _percentile_value(values: list[float], percentile: float) -> str:
    if not values:
        return ""
    index = min(max(math.ceil(len(values) * percentile) - 1, 0), len(values) - 1)
    return _num(values[index])
