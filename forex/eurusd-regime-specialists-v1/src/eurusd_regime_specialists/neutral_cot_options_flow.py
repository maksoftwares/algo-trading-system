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
from .neutral_cot_flow import execute_candidates
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
from .neutral_walkforward import _causal_candidate_features
from .research import (
    PACKAGE_ROOT,
    is_quarantined,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N11_NEUTRAL_CFTC_OPTIONS_EQUIVALENT_FLOW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_cot_options_flow"
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
PARTICIPANT_PREFIXES = {
    "dealer": "Dealer",
    "asset": "Asset_Mgr",
    "leveraged": "Lev_Money",
}


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_cot_options_flow.json"
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
            / "EURUSD_NEUTRAL_COT_OPTIONS_FLOW_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_neutral_cot_options_flow_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Neutral COT options-flow contract is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral COT options-flow preregistration "
                f"mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    parent_hash = sha256_file(parent_path)
    if parent_hash != cfg["parent_contract"]["sha256"]:
        raise RuntimeError(
            "Neutral COT options-flow parent contract mismatch"
        )
    checked[str(parent_path)] = parent_hash
    for source_name in (
        "futures_only",
        "futures_options_combined",
    ):
        source = cfg["source"][source_name]
        root = Path(source["root"])
        for name, expected in source["archives"].items():
            path = root / name
            actual = sha256_file(path)
            if actual != expected:
                raise RuntimeError(
                    "Neutral COT options-flow source mismatch: "
                    f"{path}"
                )
            checked[str(path)] = actual
    return checked


def _read_cot_format(
    cfg: dict[str, Any], source_name: str
) -> pd.DataFrame:
    source = cfg["source"][source_name]
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
                        != cfg["source"]["market"]
                    ):
                        continue
                    rows.append(
                        {
                            field: record.get(field)
                            for field in COT_FIELDS
                        }
                    )
    if not rows:
        raise RuntimeError(
            f"No frozen CME Euro FX rows for {source_name}"
        )
    return pd.DataFrame(rows)


def _clean_cot_format(
    raw: pd.DataFrame, suffix: str
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
    return frame.rename(
        columns={
            column: f"{column}_{suffix}"
            for column in numeric_columns
        }
    )


def prepare_options_flow_context(
    futures_raw: pd.DataFrame,
    combined_raw: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    futures = _clean_cot_format(futures_raw, "futures")
    combined = _clean_cot_format(combined_raw, "combined")
    frame = futures.merge(
        combined,
        on="report_date_utc",
        how="inner",
        validate="one_to_one",
    ).sort_values("report_date_utc")
    maximum_date = pd.Timestamp(
        cfg["source"]["maximum_report_date_utc"]
    )
    frame = frame[
        frame["report_date_utc"] <= maximum_date
    ].reset_index(drop=True)
    allowed = pd.Series(True, index=frame.index)
    for exclusion in cfg["availability"][
        "interrupted_report_date_exclusions"
    ]:
        start = pd.Timestamp(exclusion["start"], tz="UTC")
        end = pd.Timestamp(exclusion["end"], tz="UTC")
        allowed &= ~frame["report_date_utc"].between(start, end)
    frame = frame[allowed].reset_index(drop=True)
    futures_oi = frame["Open_Interest_All_futures"].astype(
        float
    )
    if (futures_oi <= 0).any():
        raise RuntimeError(
            "Futures-only COT open interest must be positive"
        )
    for participant in PARTICIPANTS:
        prefix = PARTICIPANT_PREFIXES[participant]
        futures_net = (
            frame[
                f"{prefix}_Positions_Long_All_futures"
            ].astype(float)
            - frame[
                f"{prefix}_Positions_Short_All_futures"
            ].astype(float)
        )
        combined_net = (
            frame[
                f"{prefix}_Positions_Long_All_combined"
            ].astype(float)
            - frame[
                f"{prefix}_Positions_Short_All_combined"
            ].astype(float)
        )
        orientation = -1.0 if participant == "dealer" else 1.0
        options_net = combined_net - futures_net
        frame[f"{participant}_options_equivalent_net"] = (
            options_net
        )
        frame[f"{participant}_flow_change"] = (
            options_net.diff()
        )
        frame[f"vote_{participant}"] = (
            np.sign(frame[f"{participant}_flow_change"])
            * orientation
        )
        futures_normalized = futures_net / futures_oi
        frame[f"{participant}_futures_flow_change"] = (
            futures_normalized.diff()
        )
        frame[f"futures_vote_{participant}"] = (
            np.sign(
                frame[f"{participant}_futures_flow_change"]
            )
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
    futures_vote_columns = [
        f"futures_vote_{participant}"
        for participant in PARTICIPANTS
    ]
    frame["futures_vote_sum"] = frame[
        futures_vote_columns
    ].sum(axis=1, min_count=len(futures_vote_columns))
    frame["futures_side"] = np.select(
        [
            frame["futures_vote_sum"].ge(1.0),
            frame["futures_vote_sum"].le(-1.0),
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


def build_options_candidates(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    parent: dict[str, Any],
    futures_raw: pd.DataFrame | None = None,
    combined_raw: pd.DataFrame | None = None,
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
    context = prepare_options_flow_context(
        (
            _read_cot_format(cfg, "futures_only")
            if futures_raw is None
            else futures_raw
        ),
        (
            _read_cot_format(
                cfg, "futures_options_combined"
            )
            if combined_raw is None
            else combined_raw
        ),
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
    candidates["futures_side"] = "CASH"
    for participant in PARTICIPANTS:
        candidates[f"vote_{participant}"] = np.nan
        candidates[f"{participant}_flow_change"] = np.nan
        candidates[
            f"{participant}_options_equivalent_net"
        ] = np.nan
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
        candidates.loc[index, "futures_side"] = report[
            "futures_side"
        ]
        candidates.loc[index, "vote_sum"] = report["vote_sum"]
        for participant in PARTICIPANTS:
            candidates.loc[
                index, f"vote_{participant}"
            ] = report[f"vote_{participant}"]
            candidates.loc[
                index, f"{participant}_flow_change"
            ] = report[f"{participant}_flow_change"]
            candidates.loc[
                index,
                f"{participant}_options_equivalent_net",
            ] = report[
                f"{participant}_options_equivalent_net"
            ]
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
    differences = int(
        chosen["side"].ne(chosen["futures_side"]).sum()
    )
    census = {
        "matched_admissible_reports": int(len(context)),
        "valid_options_flow_reports": int(
            context["three_valid_nonzero_votes"].sum()
        ),
        "neutral_open_candidates": int(len(candidates)),
        "trade_candidates": int(len(chosen)),
        "long_candidates": int(chosen["side"].eq("LONG").sum()),
        "short_candidates": int(
            chosen["side"].eq("SHORT").sum()
        ),
        "directions_different_from_futures_flow": differences,
        "direction_difference_fraction": (
            differences / len(chosen) if len(chosen) else 0.0
        ),
        "by_year": {
            str(year): int(len(group))
            for year, group in chosen.groupby("year")
        },
    }
    frozen = cfg["outcome_blind_census"]
    integer_keys = (
        "matched_admissible_reports",
        "valid_options_flow_reports",
        "neutral_open_candidates",
        "trade_candidates",
        "long_candidates",
        "short_candidates",
        "directions_different_from_futures_flow",
    )
    for key in integer_keys:
        if census[key] != int(frozen[key]):
            raise RuntimeError(
                f"Neutral COT options-flow census drift: {key} "
                f"{census[key]} != {frozen[key]}"
            )
    if census["by_year"] != frozen["by_year"]:
        raise RuntimeError(
            "Neutral COT options-flow annual census drift: "
            f"{census['by_year']} != {frozen['by_year']}"
        )
    return candidates, context, census


def _archive_manifest(
    cfg: dict[str, Any], source_name: str
) -> dict[str, Any]:
    source = cfg["source"][source_name]
    root = Path(source["root"])
    return {
        name: {
            "path": str(root / name),
            "sha256": sha256_file(root / name),
        }
        for name in source["archives"]
    }


def run_neutral_cot_options_flow() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_config()
    base = load_ensemble_config()
    eurusd, state, base_manifests = load_inputs(base)
    candidates, context, census = build_options_candidates(
        eurusd, state, cfg, parent
    )
    trades = execute_candidates(candidates, eurusd, parent)
    trades["family"] = FAMILY

    # Oracle information is attached only after options-flow direction and
    # exact price-path execution have been generated.
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
        and census["directions_different_from_futures_flow"]
        >= int(
            cfg["outcome_blind_census"][
                "minimum_directions_different_from_futures_flow"
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
            else "REJECTED_NEUTRAL_COT_OPTIONS_FLOW_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **base_manifests,
            "CFTC_EURO_FX_TFF_OPTIONS_EQUIVALENT": {
                "provider": cfg["source"]["provider"],
                "market": cfg["source"]["market"],
                "market_code": cfg["source"]["market_code"],
                "futures_only_archives": _archive_manifest(
                    cfg, "futures_only"
                ),
                "combined_archives": _archive_manifest(
                    cfg, "futures_options_combined"
                ),
                "paired_usable_rows": int(len(context)),
                "first_report_utc": (
                    context["report_date_utc"].min().isoformat()
                ),
                "last_report_utc": (
                    context["report_date_utc"].max().isoformat()
                ),
            },
        },
        "causality": {
            "signal": (
                "First Neutral 00:00 UTC opening after a "
                "conservatively available CFTC Euro FX "
                "options-equivalent participant-flow majority"
            ),
            "options_equivalent_definition": (
                "combined participant net minus futures-only "
                "participant net"
            ),
            "report_date_lag_calendar_days": int(
                cfg["availability"][
                    "report_date_lag_calendar_days"
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
            "The deterministic CFTC options-flow expert passed "
            "every frozen gate; prospective confirmation is "
            "mandatory."
            if admitted
            else "The deterministic CFTC options-flow expert "
            "failed at least one frozen development, forward, "
            "imitation, or robustness gate."
        ),
    }
    matches = (
        pd.concat(match_parts, ignore_index=True)
        if match_parts
        else pd.DataFrame()
    )
    return result, {
        "COT_OPTIONS_CONTEXT": context,
        "CANDIDATES": candidates,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "build_options_candidates",
    "load_config",
    "prepare_options_flow_context",
    "run_neutral_cot_options_flow",
    "verify_lock",
    "write_json",
]
