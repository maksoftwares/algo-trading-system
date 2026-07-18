from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "ppi_fade_regime_confirmation_v2.json"
PREFIX = "PPI_FADE_REGIME_CONFIRMATION"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVENT = _load_module(
    "ppi_fade_regime_confirmation_engine",
    RESEARCH_ROOT / "macro-event-reaction-replication-v2" / "src" / "event_reaction.py",
)
DATA = _load_module(
    "ppi_fade_regime_confirmation_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0.0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def _paths(output: Path) -> dict[str, Path]:
    return {
        "marker": output / f"{PREFIX}_OUTCOMES_OPENED.json",
        "outcomes": output / f"{PREFIX}_OUTCOMES.parquet",
        "execution_audit": output / f"{PREFIX}_EXECUTION_AUDIT.json",
        "metrics": output / f"{PREFIX}_METRICS.csv",
        "diagnostics": output / f"{PREFIX}_DIAGNOSTICS.csv",
        "survivors": output / f"{PREFIX}_SURVIVORS.csv",
        "result": output / f"{PREFIX}_RESULT.json",
        "markdown": output / f"{PREFIX}_RESULT.md",
    }


def _verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening V2 outcomes")
    lock_module = _load_module(
        "ppi_fade_regime_contract_verify", ROOT / "lock_contract.py"
    )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("V2 contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("V2 contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"V2 contract input changed: {name}")
    parent_output = (ROOT / config["parent_package"]).resolve() / "outputs"
    if (parent_output / "PPI_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json").exists():
        raise RuntimeError("Parent PPI confirmation must remain sealed")
    return lock


def _diagnostics(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dimension in ("regime", "direction"):
        for key, frame in outcomes.groupby(dimension, sort=True):
            rows.append(
                {
                    "dimension": dimension,
                    "value": str(key),
                    "trades": int(len(frame)),
                    "stress_net_r": float(frame["stress_net_r"].sum()),
                    "average_stress_r": float(frame["stress_net_r"].mean()),
                    "wins": int(frame["stress_net_r"].gt(0.0).sum()),
                }
            )
    return pd.DataFrame(rows)


def _update_artifact_manifest(output: Path, contract_hash: str) -> None:
    path = output / f"{PREFIX}_ARTIFACT_MANIFEST.json"
    artifacts = {}
    for artifact in sorted(output.iterdir()):
        if not artifact.is_file() or artifact == path or artifact.suffix == ".part":
            continue
        artifacts[artifact.name] = {
            "bytes": artifact.stat().st_size,
            "sha256": _sha256(artifact),
        }
    _write_json(
        path,
        {
            "contract_sha256": contract_hash,
            "artifacts": artifacts,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def _render(payload: Mapping[str, Any], metrics: pd.DataFrame) -> str:
    row = metrics.iloc[0]
    return "\n".join(
        [
            "# XAUUSD PPI Non-Trend Fade V2 Related Confirmation",
            "",
            f"Decision: `{payload['decision']}`",
            f"Official events: **{payload['event_rows']}**",
            f"Outcome-free candidates: **{payload['candidate_rows']}**",
            f"Executed trades: **{int(row['trades'])}**",
            f"Stress PF: **{float(row['stress_pf']):.3f}**",
            f"Average stress R: **{float(row['average_stress_r']):.3f}**",
            f"Closed drawdown: **{float(row['closed_drawdown_r']):.3f}R**",
            f"Top three winners removed: **{float(row['top_winners_removed_stress_net_r']):.3f}R**",
            f"Positive active months: **{float(row['positive_active_month_share']):.1%}**",
            f"Positive active years: **{float(row['positive_active_year_share']):.1%}**",
            f"One-policy Holm q-value: **{float(row['holm_qvalue']):.4f}**",
            f"Full gate: **{'PASS' if bool(row['stage_pass']) else 'FAIL'}**",
            "",
            "This is related-data confirmation, not a pristine blind exam.",
            "No result grants model, EA, demo, live, broker, paid-data, or Databento authority.",
            "",
        ]
    )


def run_confirmation() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = _verify_contract(config)
    contract_hash = str(lock["contract_sha256"])
    output = ROOT / config["outputs"]["directory"]
    paths = _paths(output)
    if paths["result"].exists() or paths["marker"].exists():
        raise RuntimeError("Refusing to rerun completed/opened V2 confirmation")

    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    parent = (ROOT / config["parent_package"]).resolve()
    calendar = pd.read_csv(
        parent / "outputs" / "PPI_EVENT_CALENDAR.csv",
        parse_dates=["event_time_utc"],
    )
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    events = calendar.loc[
        calendar["event_time_utc"].ge(start)
        & calendar["event_time_utc"].lt(end)
    ].copy()
    if len(events) != int(config["source"]["expected_event_rows"]):
        raise ValueError("V2 official-event count changed")

    _write_json(
        paths["marker"],
        {
            "schema_version": "xauusd_ppi_fade_regime_confirmation_open_v2",
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "attempt_no": int(config["policy"]["attempt_no"]),
            "training_authorized": False,
            "execution_authorized": False,
        },
    )
    base_config = json.loads(
        (ROOT / config["base_contract"]).resolve().read_text(encoding="utf-8")
    )
    bundle = DATA.load_bundle(base_config)
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    outcomes, execution_audit = EVENT.label_candidates(
        candidates,
        bundle.bars["M5"],
        storage_root,
        str(source["symbol"]),
        source,
        config["execution"],
    )
    temporary = paths["outcomes"].with_suffix(".parquet.part")
    outcomes.to_parquet(temporary, index=False)
    os.replace(temporary, paths["outcomes"])
    _write_json(paths["execution_audit"], execution_audit)

    values, checks = EVENT.policy_metrics(outcomes, len(events), config["gate"])
    pvalue = EVENT.one_sided_trade_pvalue(outcomes)
    qvalue = float(EVENT.holm_adjust(pd.Series([pvalue])).iloc[0])
    qpass = qvalue <= float(config["gate"]["maximum_holm_qvalue"])
    checks = dict(checks)
    checks["maximum_holm_qvalue"] = qpass
    stage_pass = bool(checks["quantitative_gate"] and qpass)
    metric = {
        "attempt_no": int(config["policy"]["attempt_no"]),
        "policy_id": str(config["policy"]["policy_id"]),
        "event_type": "PPI",
        "mode": "FADE",
        "trade_pvalue": pvalue,
        "holm_qvalue": qvalue,
        "maximum_holm_qvalue_pass": qpass,
        "stage_pass": stage_pass,
        "gate_checks": checks,
        **values,
    }
    metrics = pd.DataFrame([metric])
    csv_metrics = metrics.copy()
    csv_metrics["gate_checks"] = csv_metrics["gate_checks"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    _write_csv(paths["metrics"], csv_metrics)
    _write_csv(paths["diagnostics"], _diagnostics(outcomes))
    survivor_columns = ["attempt_no", "policy_id", "event_type", "mode"]
    survivors = (
        pd.DataFrame([config["policy"]])[survivor_columns]
        if stage_pass
        else pd.DataFrame(columns=survivor_columns)
    )
    _write_csv(paths["survivors"], survivors)

    decision = (
        "PPI_NON_TREND_FADE_RELATED_CONFIRMATION_SURVIVOR_REQUIRES_INDEPENDENT_REPLICATION_AND_SHADOW"
        if stage_pass
        else "NO_PPI_NON_TREND_FADE_V2_CONFIRMATION_SURVIVOR"
    )
    payload = {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "attempt_first": int(config["policy"]["attempt_no"]),
        "attempt_last": int(config["policy"]["attempt_no"]),
        "cumulative_campaign_attempts": int(config["policy"]["attempt_no"]),
        "window_start_utc": start.isoformat(),
        "window_end_exclusive_utc": end.isoformat(),
        "event_rows": int(len(events)),
        "candidate_rows": int(len(candidates)),
        "outcome_rows": int(len(outcomes)),
        "survivor_rows": int(stage_pass),
        "survivor_policy_ids": [str(config["policy"]["policy_id"])]
        if stage_pass
        else [],
        "decision": decision,
        "execution_audit": execution_audit,
        "related_confirmation_is_blind_exam": False,
        "parent_confirmation_remained_sealed": True,
        "paid_data_request_made": False,
        "databento_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _write_json(paths["result"], payload)
    paths["markdown"].write_text(
        _render(payload, metrics), encoding="utf-8", newline="\n"
    )
    _update_artifact_manifest(output, contract_hash)
    return payload


def main() -> int:
    payload = run_confirmation()
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
