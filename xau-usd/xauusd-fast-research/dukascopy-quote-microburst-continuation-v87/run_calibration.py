from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    ManifestTickStore,
    canonical_hash,
    load_json,
    sha256_file,
)
from quote_microburst import (  # noqa: E402
    build_microburst_features,
    generate_candidates,
    policy_grid,
    policy_id,
    select_policy,
    session_quality,
    summarize_candidate_facts,
)


CONFIG = ROOT / "config" / "dukascopy_quote_microburst_continuation_v87.json"


def load_day(
    date: pd.Timestamp,
    *,
    store: ManifestTickStore,
    rule: Mapping[str, Any],
    maximum_lookback_ms: int,
    execution: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    start_hour = int(str(rule["session_start_utc"]).split(":")[0])
    end_hour = int(str(rule["session_end_utc"]).split(":")[0])
    start_ms = int(
        (date.normalize() + pd.Timedelta(hours=start_hour)).timestamp() * 1000
    )
    start_ms -= maximum_lookback_ms + int(rule["maximum_boundary_quote_age_ms"])
    end_ms = (
        int((date.normalize() + pd.Timedelta(hours=end_hour)).timestamp() * 1000)
        - 1
    )
    if execution is not None:
        end_ms += (
            int(execution["maximum_entry_delay_ms"])
            + int(execution["hold_seconds"]) * 1000
            + int(execution["maximum_exit_delay_ms"])
        )
    return store.quote_frame(start_ms, end_ms)


def run_calibration() -> dict[str, Any]:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    candidate_path = output / str(config["outputs"]["calibration_candidates"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    audit_path = output / str(config["outputs"]["calibration_audit"])
    if any(path.exists() for path in (candidate_path, grid_path, audit_path)):
        raise FileExistsError("V87 calibration outputs already exist")
    if (output / str(config["outputs"]["contract_lock"])).exists():
        raise RuntimeError("V87 calibration cannot run after lock")
    source_path = output / str(config["outputs"]["calibration_source_audit"])
    source_audit = load_json(source_path)
    if (
        source_audit.get("decision") != "V87_CALIBRATION_SOURCE_AUDIT_PASS"
        or canonical_hash(source_audit, "audit_sha256")
        != source_audit.get("audit_sha256")
    ):
        raise ValueError("V87 calibration source audit is invalid")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    calibration = config["calibration"]
    start, end = pd.Timestamp(calibration["start"]), pd.Timestamp(calibration["end"])
    policies = policy_grid(calibration)
    if len(policies) != 1000:
        raise ValueError(f"V87 registered {len(policies)} policies, expected 1000")
    policies_by_lookback: dict[int, list[dict[str, Any]]] = {}
    for policy in policies:
        policies_by_lookback.setdefault(int(policy["lookback_ms"]), []).append(policy)
    rule = config["candidate_rule"]
    candidates_by_policy: dict[str, list[pd.DataFrame]] = {
        policy_id(policy): [] for policy in policies
    }
    quality_rows: list[dict[str, Any]] = []
    for date in pd.date_range(
        start.normalize(), end.normalize(), inclusive="left", freq="D"
    ):
        if date.weekday() >= 5:
            continue
        quotes = load_day(
            date,
            store=store,
            rule=rule,
            maximum_lookback_ms=max(policies_by_lookback),
        )
        quality = session_quality(date, quotes, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            for lookback, lookback_policies in policies_by_lookback.items():
                features = build_microburst_features(
                    date, quotes, lookback_ms=lookback, rule=rule
                )
                for policy in lookback_policies:
                    candidate = generate_candidates(
                        features, policy=policy, rule=rule
                    )
                    if not candidate.empty:
                        candidates_by_policy[policy_id(policy)].append(candidate)
        print(f"V87 calibrated {date.date()}", flush=True)
    eligible_dates = [
        row["date_utc"] for row in quality_rows if bool(row["eligible_full_weekday"])
    ]
    rows: list[dict[str, Any]] = []
    materialized: dict[str, pd.DataFrame] = {}
    for policy in policies:
        identifier = policy_id(policy)
        frames = candidates_by_policy[identifier]
        candidates = (
            pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        )
        materialized[identifier] = candidates
        rows.append(
            summarize_candidate_facts(
                candidates,
                eligible_dates=eligible_dates,
                policy=policy,
                calibration=calibration,
            )
        )
    grid = pd.DataFrame(rows).sort_values("policy_id", kind="stable")
    selected = select_policy(rows, calibration)
    selected_candidates = (
        materialized[str(selected["policy_id"])]
        if selected is not None
        else pd.DataFrame()
    )
    output.mkdir(parents=True, exist_ok=True)
    selected_candidates.to_parquet(candidate_path, index=False)
    grid.to_csv(grid_path, index=False, lineterminator="\n")
    decision = (
        "V87_CALIBRATION_POLICY_SELECTED"
        if selected is not None
        else "V87_NO_CALIBRATION_POLICY"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_quote_microburst_continuation_v87_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": str(start),
        "calibration_end_exclusive": str(end),
        "source_audit_sha256": sha256_file(source_path),
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "registered_policy_count": len(policies),
        "eligible_policy_count": int(grid["selection_eligible"].sum()),
        "selected_policy": selected,
        "selected_candidate_rows": int(len(selected_candidates)),
        "selected_candidates_sha256": sha256_file(candidate_path),
        "grid_sha256": sha256_file(grid_path),
        "post_candidate_prices_used_for_label_or_outcome": False,
        **config["research_controls"],
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(
        json.dumps(
            {
                "decision": decision,
                "eligible_policies": int(grid["selection_eligible"].sum()),
                "selected_policy": selected,
                "selected_candidate_rows": len(selected_candidates),
            },
            indent=2,
        )
    )
    return audit


if __name__ == "__main__":
    run_calibration()
