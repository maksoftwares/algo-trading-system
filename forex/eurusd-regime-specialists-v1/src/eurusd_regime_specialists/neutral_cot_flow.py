from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config, load_inputs
from .neutral_oracle_imitation import (
    economic_metrics,
    load_oracle,
    oracle_match_metrics,
)
from .neutral_utc_open_vote import (
    _gate_pass,
    _safe_metrics,
    write_json,
)
from .neutral_walkforward import (
    _causal_candidate_features,
    _labeled_outcome,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N10_NEUTRAL_CFTC_PARTICIPANT_FLOW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_cot_flow"
COT_FIELDS = (
    "Report_Date_as_YYYY-MM-DD",
    "Open_Interest_All",
    "Dealer_Positions_Long_All",
    "Dealer_Positions_Short_All",
    "Asset_Mgr_Positions_Long_All",
    "Asset_Mgr_Positions_Short_All",
    "Lev_Money_Positions_Long_All",
    "Lev_Money_Positions_Short_All",
)
PARTICIPANTS = ("dealer", "asset", "leveraged")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_cot_flow.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config() -> dict[str, Any]:
    cfg = load_config()
    return json.loads(
        (PACKAGE_ROOT / cfg["parent_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_COT_FLOW_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_neutral_cot_flow_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral COT-flow contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Neutral COT-flow preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    parent_hash = sha256_file(parent_path)
    if parent_hash != cfg["parent_contract"]["sha256"]:
        raise RuntimeError("Neutral COT-flow parent contract mismatch")
    checked[str(parent_path)] = parent_hash
    source_root = Path(cfg["source"]["root"])
    for name, expected in cfg["source"]["archives"].items():
        path = source_root / name
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(
                f"Neutral COT-flow source mismatch: {path}"
            )
        checked[str(path)] = actual
    return checked


def _read_cot_archives(cfg: dict[str, Any]) -> pd.DataFrame:
    source = cfg["source"]
    root = Path(source["root"])
    rows: list[dict[str, Any]] = []
    for name in source["archives"]:
        path = root / name
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
            if len(members) != 1:
                raise RuntimeError(
                    f"Expected one COT CSV in {path}, got {members}"
                )
            with archive.open(members[0]) as raw:
                reader = csv.DictReader(
                    io.TextIOWrapper(
                        raw, encoding="latin1", newline=""
                    )
                )
                for record in reader:
                    if (
                        record.get(
                            "Market_and_Exchange_Names", ""
                        ).strip()
                        != source["market"]
                    ):
                        continue
                    rows.append(
                        {
                            field: record.get(field)
                            for field in COT_FIELDS
                        }
                    )
    if not rows:
        raise RuntimeError("No frozen CME Euro FX COT rows found")
    return pd.DataFrame(rows)


def prepare_cot_flow_context(
    raw: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    frame = raw.copy()
    frame["report_date_utc"] = pd.to_datetime(
        frame.pop("Report_Date_as_YYYY-MM-DD"),
        utc=True,
        errors="coerce",
    )
    numeric_columns = [
        column
        for column in COT_FIELDS
        if column != "Report_Date_as_YYYY-MM-DD"
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column], errors="coerce"
        )
    frame = (
        frame.dropna(
            subset=["report_date_utc", *numeric_columns]
        )
        .sort_values("report_date_utc")
        .drop_duplicates("report_date_utc", keep="last")
        .reset_index(drop=True)
    )
    allowed = pd.Series(True, index=frame.index)
    for exclusion in cfg["availability"][
        "interrupted_report_date_exclusions"
    ]:
        start = pd.Timestamp(exclusion["start"], tz="UTC")
        end = pd.Timestamp(exclusion["end"], tz="UTC")
        allowed &= ~frame["report_date_utc"].between(start, end)
    frame = frame[allowed].reset_index(drop=True)
    open_interest = frame["Open_Interest_All"].astype(float)
    if (open_interest <= 0).any():
        raise RuntimeError("COT open interest must remain positive")
    participant_columns = {
        "dealer": (
            "Dealer_Positions_Long_All",
            "Dealer_Positions_Short_All",
            -1.0,
        ),
        "asset": (
            "Asset_Mgr_Positions_Long_All",
            "Asset_Mgr_Positions_Short_All",
            1.0,
        ),
        "leveraged": (
            "Lev_Money_Positions_Long_All",
            "Lev_Money_Positions_Short_All",
            1.0,
        ),
    }
    for participant, (
        long_column,
        short_column,
        orientation,
    ) in participant_columns.items():
        net = (
            frame[long_column].astype(float)
            - frame[short_column].astype(float)
        ) / open_interest
        frame[f"{participant}_net_pct_oi"] = net
        frame[f"{participant}_flow_change"] = net.diff()
        frame[f"vote_{participant}"] = (
            np.sign(frame[f"{participant}_flow_change"])
            * orientation
        )
    vote_columns = [
        f"vote_{participant}"
        for participant in PARTICIPANTS
    ]
    frame["three_valid_nonzero_votes"] = (
        frame[vote_columns].abs().eq(1.0).all(axis=1)
    )
    frame["vote_sum"] = frame[vote_columns].sum(
        axis=1, min_count=len(vote_columns)
    )
    frame["side"] = np.select(
        [
            frame["three_valid_nonzero_votes"]
            & frame["vote_sum"].ge(1.0),
            frame["three_valid_nonzero_votes"]
            & frame["vote_sum"].le(-1.0),
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    lag_days = int(
        cfg["availability"]["report_date_lag_calendar_days"]
    )
    frame["availability_utc"] = (
        frame["report_date_utc"] + pd.Timedelta(days=lag_days)
    )
    return frame


def build_cot_candidates(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    parent: dict[str, Any],
    raw_cot: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    base_cfg = load_ensemble_config()
    causal = _causal_candidate_features(eurusd, state, parent)
    candidates = causal[
        causal["completion_time_utc"].dt.hour.eq(0)
        & causal["completion_time_utc"].dt.minute.eq(0)
    ][
        [
            "signal_time_utc",
            "completion_time_utc",
            "matched_state_time_utc",
        ]
    ].copy()
    candidates = candidates[
        ~candidates["completion_time_utc"].map(
            lambda value: is_quarantined(
                value, "EURUSD", base_cfg["quarantine"]
            )
        )
    ].sort_values("completion_time_utc")
    context = prepare_cot_flow_context(
        _read_cot_archives(cfg) if raw_cot is None else raw_cot,
        cfg,
    )
    candidates["trade_candidate"] = False
    candidates["report_date_utc"] = pd.Series(
        pd.NaT,
        index=candidates.index,
        dtype="datetime64[ns, UTC]",
    )
    candidates["availability_utc"] = pd.Series(
        pd.NaT,
        index=candidates.index,
        dtype="datetime64[ns, UTC]",
    )
    candidates["side"] = "CASH"
    for participant in PARTICIPANTS:
        candidates[f"vote_{participant}"] = np.nan
        candidates[f"{participant}_flow_change"] = np.nan
    candidates["vote_sum"] = np.nan
    maximum_age = pd.Timedelta(
        days=int(
            cfg["availability"][
                "maximum_signal_age_calendar_days"
            ]
        )
    )
    times = candidates["completion_time_utc"]
    for _, report in context[
        context["three_valid_nonzero_votes"]
    ].iterrows():
        eligible = candidates[
            (times >= report["availability_utc"])
            & (times < report["availability_utc"] + maximum_age)
            & ~candidates["trade_candidate"]
        ]
        if eligible.empty:
            continue
        index = eligible.index[0]
        candidates.loc[index, "trade_candidate"] = True
        candidates.loc[index, "report_date_utc"] = report[
            "report_date_utc"
        ]
        candidates.loc[index, "availability_utc"] = report[
            "availability_utc"
        ]
        candidates.loc[index, "side"] = report["side"]
        candidates.loc[index, "vote_sum"] = report["vote_sum"]
        for participant in PARTICIPANTS:
            candidates.loc[
                index, f"vote_{participant}"
            ] = report[f"vote_{participant}"]
            candidates.loc[
                index, f"{participant}_flow_change"
            ] = report[f"{participant}_flow_change"]
    candidates["candidate_id"] = (
        candidates["completion_time_utc"].dt.strftime(
            "%Y%m%dT%H%M%SZ"
        )
        + "_"
        + candidates["side"]
    )
    candidates["year"] = (
        candidates["completion_time_utc"].dt.year
    )
    chosen = candidates[candidates["trade_candidate"]]
    census = {
        "usable_cot_reports": int(len(context)),
        "valid_flow_reports": int(
            context["three_valid_nonzero_votes"].sum()
        ),
        "neutral_open_candidates": int(len(candidates)),
        "trade_candidates": int(len(chosen)),
        "long_candidates": int(chosen["side"].eq("LONG").sum()),
        "short_candidates": int(
            chosen["side"].eq("SHORT").sum()
        ),
        "by_year": {
            str(year): int(len(group))
            for year, group in chosen.groupby("year")
        },
    }
    frozen = cfg["outcome_blind_census"]
    for key in (
        "usable_cot_reports",
        "valid_flow_reports",
        "neutral_open_candidates",
        "trade_candidates",
        "long_candidates",
        "short_candidates",
    ):
        if census[key] != int(frozen[key]):
            raise RuntimeError(
                f"Neutral COT-flow census drift: {key} "
                f"{census[key]} != {frozen[key]}"
            )
    if census["by_year"] != frozen["by_year"]:
        raise RuntimeError(
            "Neutral COT-flow annual census drift: "
            f"{census['by_year']} != {frozen['by_year']}"
        )
    return candidates, context, census


def execute_candidates(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    parent: dict[str, Any],
) -> pd.DataFrame:
    chosen = candidates[candidates["trade_candidate"]].copy()
    arrays = {
        column: eurusd[column].to_numpy(dtype=float)
        for column in (
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        )
    }
    records: list[dict[str, Any]] = []
    for _, candidate in chosen.sort_values(
        "completion_time_utc"
    ).iterrows():
        entry_time = candidate["completion_time_utc"]
        position = int(
            eurusd.index.searchsorted(entry_time, side="left")
        )
        if (
            position >= len(eurusd)
            or eurusd.index[position] != entry_time
        ):
            continue
        outcome = _labeled_outcome(
            position,
            eurusd.index,
            arrays,
            candidate["side"],
            parent,
            float(parent["label"]["risk_pips"]),
        )
        risk = float(outcome["risk_distance"])
        record = {
            "candidate_id": candidate["candidate_id"],
            "family": FAMILY,
            "regime": "NEUTRAL",
            "side": candidate["side"],
            "signal_time_utc": candidate["signal_time_utc"],
            "completion_time_utc": entry_time,
            **outcome,
            "r": float(outcome["outcome_r"]),
            "extra_half_pip_stress_r": (
                float(outcome["outcome_r"])
                - 0.5 * PIP / risk
            ),
            "report_date_utc": candidate["report_date_utc"],
            "availability_utc": candidate["availability_utc"],
            "vote_sum": candidate["vote_sum"],
        }
        for participant in PARTICIPANTS:
            record[f"vote_{participant}"] = candidate[
                f"vote_{participant}"
            ]
            record[f"{participant}_flow_change"] = candidate[
                f"{participant}_flow_change"
            ]
        records.append(record)
    return pd.DataFrame(records).drop(columns=["outcome_r"])


def _cot_source_manifest(
    cfg: dict[str, Any], context: pd.DataFrame
) -> dict[str, Any]:
    root = Path(cfg["source"]["root"])
    archives = {
        name: {
            "path": str(root / name),
            "sha256": sha256_file(root / name),
        }
        for name in cfg["source"]["archives"]
    }
    return {
        "provider": cfg["source"]["provider"],
        "report": cfg["source"]["report"],
        "market": cfg["source"]["market"],
        "market_code": cfg["source"]["market_code"],
        "archives": archives,
        "usable_rows": int(len(context)),
        "first_report_utc": (
            context["report_date_utc"].min().isoformat()
        ),
        "last_report_utc": (
            context["report_date_utc"].max().isoformat()
        ),
        "last_conservative_availability_utc": (
            context["availability_utc"].max().isoformat()
        ),
    }


def run_neutral_cot_flow() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_config()
    base = load_ensemble_config()
    eurusd, state, base_manifests = load_inputs(base)
    candidates, context, census = build_cot_candidates(
        eurusd, state, cfg, parent
    )
    trades = execute_candidates(candidates, eurusd, parent)

    # Oracle data is loaded only after participant-flow direction and
    # price-path execution have been fixed.
    oracle = load_oracle(parent)
    oracle_keys = set(
        zip(oracle["entry_time_utc"], oracle["side"], strict=False)
    )
    trades["oracle_member"] = [
        int((entry, side) in oracle_keys)
        for entry, side in zip(
            trades["entry_time_utc"],
            trades["side"],
            strict=False,
        )
    ]

    development_start, development_end = map(
        pd.Timestamp, cfg["development_window"]
    )
    development_trades = trades[
        (trades["entry_time_utc"] >= development_start)
        & (trades["entry_time_utc"] <= development_end)
    ]
    development = economic_metrics(
        development_trades,
        eurusd,
        development_start,
        development_end,
        cfg,
    )
    development_pass = _gate_pass(
        development,
        cfg["development_gate"],
        int(cfg["development_gate"]["minimum_trades"]),
    )

    window_results: dict[str, Any] = {}
    match_parts: list[pd.DataFrame] = []
    for name, (start_raw, end_raw) in cfg[
        "walk_forward_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        frame = trades[
            (trades["entry_time_utc"] >= start)
            & (trades["entry_time_utc"] <= end)
        ]
        economics = economic_metrics(
            frame, eurusd, start, end, cfg
        )
        imitation, matches = oracle_match_metrics(
            frame,
            oracle,
            start,
            end,
            int(
                cfg["oracle_matching"][
                    "secondary_tolerance_minutes"
                ]
            ),
        )
        matches["walk_forward_window"] = name
        match_parts.append(matches)
        passed = _gate_pass(
            economics,
            cfg["final_admission"],
            int(
                cfg["final_admission"][
                    "minimum_trades_by_window"
                ][name]
            ),
        )
        window_results[name] = {
            "passed": passed,
            "economics": economics,
            "oracle_imitation": imitation,
        }

    forward_start = min(
        pd.Timestamp(value[0])
        for value in cfg["walk_forward_windows"].values()
    )
    forward_end = max(
        pd.Timestamp(value[1])
        for value in cfg["walk_forward_windows"].values()
    )
    forward_trades = trades[
        (trades["entry_time_utc"] >= forward_start)
        & (trades["entry_time_utc"] <= forward_end)
    ]
    forward_economics = economic_metrics(
        forward_trades,
        eurusd,
        forward_start,
        forward_end,
        cfg,
    )
    forward_imitation, _ = oracle_match_metrics(
        forward_trades,
        oracle,
        forward_start,
        forward_end,
        int(
            cfg["oracle_matching"]["secondary_tolerance_minutes"]
        ),
    )
    all_history = economic_metrics(
        trades,
        eurusd,
        pd.Timestamp(base["data"]["start_utc"]),
        pd.Timestamp(base["data"]["end_utc"]),
        cfg,
    )
    top_removed = _safe_metrics(remove_top_winners(trades))
    stressed = _safe_metrics(
        trades, "extra_half_pip_stress_r"
    )
    gate = cfg["final_admission"]
    imitation_pass = (
        forward_imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
        and forward_imitation["exact_recall"]
        >= float(gate["minimum_exact_match_recall_overall"])
        and forward_imitation["tolerant_precision"]
        >= float(gate["minimum_15m_match_precision_overall"])
    )
    robustness_pass = (
        all_history["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r_overall"])
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    census_pass = (
        census["trade_candidates"]
        >= int(
            cfg["outcome_blind_census"][
                "minimum_trade_candidates"
            ]
        )
        and all(
            census["by_year"].get(str(year), 0)
            >= int(
                cfg["outcome_blind_census"][
                    "minimum_each_full_forward_year"
                ]
            )
            for year in (2023, 2024, 2025)
        )
        and census["by_year"].get("2026", 0)
        >= int(
            cfg["outcome_blind_census"]["minimum_2026_h1"]
        )
    )
    admitted = (
        census_pass
        and development_pass
        and all(
            value["passed"] for value in window_results.values()
        )
        and imitation_pass
        and robustness_pass
    )
    membership_breakdown = {
        name: _safe_metrics(
            forward_trades[
                forward_trades["oracle_member"].eq(member)
            ]
        )
        for member, name in (
            (1, "exact_oracle_members"),
            (0, "nonmembers"),
        )
    }
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_COT_FLOW_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **base_manifests,
            "CFTC_EURO_FX_TFF": _cot_source_manifest(
                cfg, context
            ),
        },
        "causality": {
            "signal": (
                "First Neutral 00:00 UTC opening after a "
                "conservatively available CFTC Euro FX "
                "participant-flow majority"
            ),
            "report_date_lag_calendar_days": int(
                cfg["availability"][
                    "report_date_lag_calendar_days"
                ]
            ),
            "maximum_signal_age_calendar_days": int(
                cfg["availability"][
                    "maximum_signal_age_calendar_days"
                ]
            ),
            "interrupted_reports_excluded_before_change": True,
            "future_information_in_signal": False,
            "oracle_loaded_after_execution": True,
            "ml_used": False,
        },
        "outcome_blind_census": {
            **census,
            "passed": census_pass,
        },
        "development": {
            "passed": development_pass,
            "economics": development,
        },
        "walk_forward": {
            "admitted": admitted,
            "windows": window_results,
            "overall_economics": forward_economics,
            "overall_oracle_imitation": forward_imitation,
            "outcomes_by_exact_oracle_membership": (
                membership_breakdown
            ),
            "imitation_gate_passed": imitation_pass,
        },
        "all_history": {
            "economics": all_history,
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "robustness_gate_passed": robustness_pass,
        },
        "verdict": (
            "The deterministic CFTC-flow expert passed every "
            "frozen gate; prospective confirmation is mandatory."
            if admitted
            else "The deterministic CFTC-flow expert failed at "
            "least one frozen development, forward, imitation, "
            "or robustness gate."
        ),
    }
    matches = (
        pd.concat(match_parts, ignore_index=True)
        if match_parts
        else pd.DataFrame()
    )
    return result, {
        "COT_CONTEXT": context,
        "CANDIDATES": candidates,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "build_cot_candidates",
    "prepare_cot_flow_context",
    "run_neutral_cot_flow",
    "verify_lock",
    "write_json",
]
