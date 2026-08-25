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


spec = importlib.util.spec_from_file_location("v60_dynamic_v6_base_evidence", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load base evidence recorder: {BASE_PATH}")
BASE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = BASE
spec.loader.exec_module(BASE)
BASE_IMMUTABLE_EVENTS = BASE.immutable_events


def immutable_events(row):
    events = BASE_IMMUTABLE_EVENTS(row)
    for event_type, payload in events:
        if event_type == "SCORE_DECISION":
            payload.update(
                {
                    "prospective_contract_sha256": row.get(
                        "prospective_contract_sha256"
                    ),
                    "candidate_direction": row.get("candidate_direction"),
                    "feature_bar_time_utc": row.get("feature_bar_time_utc"),
                    "causal_policy_features_complete": bool(
                        row.get("causal_policy_features_complete")
                    ),
                }
            )
            for name in (
                "atr_ratio",
                "rv_1h",
                "rv_24h",
                "slope_atr",
                "ret_1h",
                "ret_4h",
                "ret_24h",
                "dist_hi_24h",
                "dist_lo_24h",
            ):
                value = row.get(name)
                payload[name] = float(value) if value is not None else None
        elif event_type == "BASELINE_EXECUTION_DECISION":
            payload.update(
                {
                    "prospective_contract_sha256": row.get(
                        "prospective_contract_sha256"
                    ),
                    "v2_veto_proposal": bool(row.get("v2_veto_proposal")),
                    "anti_chase_veto_proposal": bool(
                        row.get("anti_chase_veto_proposal")
                    ),
                    "proposal_rule": row.get("proposal_rule"),
                    "dynamic_hypothetical_state": True,
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
