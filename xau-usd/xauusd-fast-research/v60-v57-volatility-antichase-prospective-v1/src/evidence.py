from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT.parent
    / "v60-mature-source-health-rank-veto-prospective-v2"
    / "src"
    / "evidence.py"
)


def load_base():
    spec = importlib.util.spec_from_file_location(
        "v60_antichase_base_evidence", BASE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base evidence recorder: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base()
BASE_IMMUTABLE_EVENTS = BASE.immutable_events


def immutable_events(row):
    events = BASE_IMMUTABLE_EVENTS(row)
    for event_type, payload in events:
        if event_type == "SCORE_DECISION":
            atr_ratio = row.get("atr_ratio")
            distance = row.get("dist_hi_24h")
            payload.update(
                {
                    "candidate_direction": row.get("candidate_direction"),
                    "feature_bar_time_utc": row.get("feature_bar_time_utc"),
                    "atr_ratio": (
                        float(atr_ratio) if atr_ratio is not None else None
                    ),
                    "dist_hi_24h": (
                        float(distance) if distance is not None else None
                    ),
                    "causal_policy_features_complete": bool(
                        row["causal_policy_features_complete"]
                    ),
                }
            )
    return events


BASE.immutable_events = immutable_events

atomic_write = BASE.atomic_write
load_chain = BASE.load_chain
update_evidence_chain = BASE.update_evidence_chain
annotate_decision_timing = BASE.annotate_decision_timing
attach_execution_details = BASE.attach_execution_details
add_forward_comparison = BASE.add_forward_comparison
build_equity_mark = BASE.build_equity_mark
update_equity_marks = BASE.update_equity_marks
