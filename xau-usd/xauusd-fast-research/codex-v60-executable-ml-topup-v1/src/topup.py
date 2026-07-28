from __future__ import annotations

import hashlib
import heapq
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONTRACT_PATH = ROOT / "config" / "EXECUTABLE_TOPUP_CONTRACT.json"
OUTPUTS = ROOT / "outputs"
PRIOR_SOURCE_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/codex-v60-ml-sizing-causal-retest-v1"
    / "src/retest.py"
)
PRIOR_CONTRACT_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/codex-v60-ml-sizing-causal-retest-v1"
    / "config/CAUSAL_RETEST_CONTRACT.json"
)
PNL = "fee_stress_pnl_usd"
BOOTSTRAP_REPS = 10_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for source in contract["inputs"].values():
        path = Path(str(source["path"]))
        if not path.is_absolute():
            path = REPO_ROOT / path
        actual = sha256_file(path)
        if actual != str(source["sha256"]):
            raise ValueError(f"Input hash mismatch for {path}: {actual}")
    return contract


def build_source_features(
    base: pd.DataFrame,
    meta: pd.DataFrame,
    source_ids: list[str],
) -> pd.DataFrame:
    result = base.copy()
    sources = meta["execution_source_id"].astype(str)
    known_risk_sources = set(sources.loc[meta["risk_usd"].notna()])
    unregistered = known_risk_sources.difference(source_ids)
    if unregistered:
        raise ValueError(f"Known-risk sources missing from contract: {unregistered}")
    for source_id in source_ids:
        result[f"source__{source_id}"] = sources.eq(source_id).astype(float)
    result = result.replace([np.inf, -np.inf], np.nan)
    if result.isna().any().any():
        raise ValueError("Source-aware feature matrix is not finite")
    forbidden = {
        PNL,
        "risk_usd",
        "entry_price",
        "exit_price",
        "exit_time",
        "holding_minutes",
    }
    overlap = forbidden.intersection(result.columns)
    if overlap:
        raise ValueError(f"Outcome or risk columns reached model features: {overlap}")
    return result


def causal_rank(
    values: np.ndarray,
    training_reference: np.ndarray,
    history: list[float],
    minimum_history: int,
) -> np.ndarray:
    ranks = np.empty(len(values), dtype=float)
    reference = np.sort(np.asarray(training_reference, dtype=float))
    if len(reference) == 0:
        raise ValueError("Cannot rank scores against an empty training reference")
    for index, value in enumerate(values):
        source = (
            np.sort(np.asarray(history, dtype=float))
            if len(history) >= minimum_history
            else reference
        )
        ranks[index] = np.searchsorted(source, value, side="right") / len(source)
        history.append(float(value))
    return ranks


def fit_dual_ensemble(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    pnl: np.ndarray,
    contract: dict[str, Any],
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    model_config = contract["model"]
    parameters = dict(model_config["parameters"])
    quantiles = model_config["regression_winsor_quantiles"]
    regression_target = np.clip(
        pnl,
        np.quantile(pnl, float(quantiles[0])),
        np.quantile(pnl, float(quantiles[1])),
    )
    classification_target = (pnl > 0.0).astype(int)
    if len(np.unique(classification_target)) != 2:
        raise ValueError("Training window does not contain both outcome classes")

    train_regression = np.zeros(len(X_train), dtype=float)
    test_regression = np.zeros(len(X_test), dtype=float)
    train_probability = np.zeros(len(X_train), dtype=float)
    test_probability = np.zeros(len(X_test), dtype=float)
    bags = int(model_config["bags"])

    for _ in range(bags):
        sample = rng.integers(0, len(X_train), len(X_train))
        sampled_classes = classification_target[sample]
        if len(np.unique(sampled_classes)) != 2:
            sample = np.arange(len(X_train))
        regressor = HistGradientBoostingRegressor(**parameters).fit(
            X_train.iloc[sample],
            regression_target[sample],
        )
        classifier = HistGradientBoostingClassifier(**parameters).fit(
            X_train.iloc[sample],
            classification_target[sample],
        )
        train_regression += regressor.predict(X_train)
        test_regression += regressor.predict(X_test)
        train_probability += classifier.predict_proba(X_train)[:, 1]
        test_probability += classifier.predict_proba(X_test)[:, 1]

    return (
        train_regression / bags,
        test_regression / bags,
        train_probability / bags,
        test_probability / bags,
    )


def walkforward_dual(
    X: pd.DataFrame,
    meta: pd.DataFrame,
    contract: dict[str, Any],
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_config = contract["model"]
    score_policy = contract["score_policy"]
    years = set(int(value) for value in contract["population"]["test_entry_years"])
    purge = pd.Timedelta(hours=int(model_config["purge_hours"]))
    known_risk = meta["risk_usd"].notna().to_numpy()
    rng = np.random.default_rng(seed)
    expected_history: list[float] = []
    probability_history: list[float] = []
    result = pd.DataFrame(
        {
            "expected_pnl_score": np.nan,
            "win_probability_score": np.nan,
            "expected_pnl_rank": np.nan,
            "win_probability_rank": np.nan,
            "joint_score": np.nan,
            "topup_proposed": False,
        },
        index=meta.index,
    )
    annual: list[dict[str, Any]] = []

    for year in sorted(years):
        cutoff = pd.Timestamp(f"{year}-01-01", tz="UTC") - purge
        train = known_risk & meta["exit_time"].lt(cutoff).to_numpy()
        test = known_risk & meta["entry_time"].dt.year.eq(year).to_numpy()
        train_rows = int(train.sum())
        test_rows = int(test.sum())
        if train_rows < int(model_config["minimum_train_rows"]):
            annual.append(
                {
                    "target_year": year,
                    "training_rows": train_rows,
                    "target_known_risk_rows": test_rows,
                    "topup_proposals": 0,
                    "status": "INSUFFICIENT_TRAINING_ROWS",
                }
            )
            continue
        if test_rows == 0:
            continue
        pnl = meta.loc[train, PNL].to_numpy(dtype=float)
        (
            train_expected,
            test_expected,
            train_probability,
            test_probability,
        ) = fit_dual_ensemble(
            X.loc[train],
            X.loc[test],
            pnl,
            contract,
            rng,
        )
        expected_rank = causal_rank(
            test_expected,
            train_expected,
            expected_history,
            int(score_policy["minimum_oos_history"]),
        )
        probability_rank = causal_rank(
            test_probability,
            train_probability,
            probability_history,
            int(score_policy["minimum_oos_history"]),
        )
        joint = (
            float(score_policy["expected_pnl_weight"]) * expected_rank
            + float(score_policy["win_probability_weight"]) * probability_rank
        )
        proposed = (
            (
                expected_rank
                > float(score_policy["minimum_expected_pnl_rank_exclusive"])
            )
            & (
                probability_rank
                > float(score_policy["minimum_win_probability_rank_exclusive"])
            )
            & (
                joint
                > float(score_policy["minimum_joint_score_exclusive"])
            )
        )
        result.loc[test, "expected_pnl_score"] = test_expected
        result.loc[test, "win_probability_score"] = test_probability
        result.loc[test, "expected_pnl_rank"] = expected_rank
        result.loc[test, "win_probability_rank"] = probability_rank
        result.loc[test, "joint_score"] = joint
        result.loc[test, "topup_proposed"] = proposed
        annual.append(
            {
                "target_year": year,
                "training_rows": train_rows,
                "training_last_exit_utc": meta.loc[
                    train, "exit_time"
                ].max().isoformat(),
                "training_positive_rate": float((pnl > 0.0).mean()),
                "target_known_risk_rows": test_rows,
                "topup_proposals": int(proposed.sum()),
                "expected_score_mean": float(np.mean(test_expected)),
                "win_probability_mean": float(np.mean(test_probability)),
                "joint_score_mean": float(np.mean(joint)),
                "status": "SCORED",
            }
        )

    result["topup_proposed"] = result["topup_proposed"].astype(bool)
    return result, pd.DataFrame(annual)


def topup_factors(
    meta: pd.DataFrame,
    proposed: np.ndarray,
    demo_config: dict[str, Any],
    limits: dict[str, float],
    prior: ModuleType,
) -> tuple[np.ndarray, dict[str, Any]]:
    proposal = np.asarray(proposed, dtype=bool)
    if len(proposal) != len(meta):
        raise ValueError("Proposal length does not match the trade population")
    factors = np.ones(len(meta), dtype=float)
    source_limits = prior.source_risk_limits(demo_config)
    active: list[tuple[int, int, float, str, bool, bool]] = []
    sequence = 0
    known_account_risk = 0.0
    known_direction_risk = {"LONG": 0.0, "SHORT": 0.0}
    known_addon_risk = 0.0
    unknown_active = 0
    core_positions = 0
    addon_positions = 0
    accepted = 0
    rejected: dict[str, int] = {}
    maximum_account_risk = 0.0
    maximum_direction_risk = 0.0
    maximum_addon_risk = 0.0
    maximum_unknown_active = 0
    maximum_core_positions = 0
    maximum_addon_positions = 0
    maximum_account_positions = 0

    def reject(reason: str) -> None:
        rejected[reason] = rejected.get(reason, 0) + 1

    ordered = meta.reset_index(drop=True)
    for index, row in ordered.iterrows():
        entry_ns = int(row["entry_time"].value)
        while active and active[0][0] <= entry_ns:
            _, _, risk, direction, addon, unknown = heapq.heappop(active)
            if unknown:
                unknown_active -= 1
            else:
                known_account_risk -= risk
                known_direction_risk[direction] -= risk
                if addon:
                    known_addon_risk -= risk
            if addon:
                addon_positions -= 1
            else:
                core_positions -= 1

        risk_value = row["risk_usd"]
        known = pd.notna(risk_value)
        risk = float(risk_value) if known else 0.0
        direction = str(row["direction"]).upper()
        addon = not bool(row["is_core"])
        source = str(row["execution_source_id"])
        factor = 1.0

        if proposal[index]:
            scaled_risk = risk * 2.0
            reason = None
            if not known:
                reason = "MISSING_INITIAL_RISK"
            elif source not in source_limits:
                reason = "UNKNOWN_SOURCE_RISK_LIMIT"
            elif scaled_risk > source_limits[source]:
                reason = "SOURCE_RISK_LIMIT"
            elif unknown_active > 0:
                reason = "ACTIVE_UNKNOWN_RISK"
            elif (
                known_account_risk + scaled_risk
                > float(limits["account_initial_risk_usd"])
            ):
                reason = "ACCOUNT_RISK_LIMIT"
            elif (
                known_direction_risk[direction] + scaled_risk
                > float(limits["directional_initial_risk_usd"])
            ):
                reason = "DIRECTIONAL_RISK_LIMIT"
            elif addon and (
                known_addon_risk + scaled_risk
                > float(limits["addon_initial_risk_usd"])
            ):
                reason = "ADDON_RISK_LIMIT"
            if reason is None:
                factor = 2.0
                accepted += 1
            else:
                reject(reason)
        factors[index] = factor

        scaled_base_risk = risk * factor
        unknown = not known
        if unknown:
            unknown_active += 1
        else:
            known_account_risk += scaled_base_risk
            known_direction_risk[direction] += scaled_base_risk
            if addon:
                known_addon_risk += scaled_base_risk
        if addon:
            addon_positions += 1
        else:
            core_positions += 1
        heapq.heappush(
            active,
            (
                int(row["exit_time"].value),
                sequence,
                scaled_base_risk,
                direction,
                addon,
                unknown,
            ),
        )
        sequence += 1
        maximum_account_risk = max(maximum_account_risk, known_account_risk)
        maximum_direction_risk = max(
            maximum_direction_risk,
            known_direction_risk["LONG"],
            known_direction_risk["SHORT"],
        )
        maximum_addon_risk = max(maximum_addon_risk, known_addon_risk)
        maximum_unknown_active = max(maximum_unknown_active, unknown_active)
        maximum_core_positions = max(maximum_core_positions, core_positions)
        maximum_addon_positions = max(maximum_addon_positions, addon_positions)
        maximum_account_positions = max(
            maximum_account_positions,
            core_positions + addon_positions,
        )

    audit = {
        "proposed_topups": int(proposal.sum()),
        "accepted_topups": int(accepted),
        "rejected_topups": int(proposal.sum() - accepted),
        "rejections": rejected,
        "base_trade_rows": int(len(meta)),
        "skipped_trade_rows": int(np.sum(factors <= 0.0)),
        "one_lot_unit_rows": int(np.sum(factors == 1.0)),
        "two_lot_unit_rows": int(np.sum(factors == 2.0)),
        "lot_values": sorted(set((factors * 0.01).tolist())),
        "accepted_missing_risk_topups": int(
            np.sum((factors == 2.0) & meta["risk_usd"].isna().to_numpy())
        ),
        "maximum_known_account_risk_usd": float(maximum_account_risk),
        "maximum_known_direction_risk_usd": float(maximum_direction_risk),
        "maximum_known_addon_risk_usd": float(maximum_addon_risk),
        "maximum_unknown_risk_positions": int(maximum_unknown_active),
        "maximum_core_positions": int(maximum_core_positions),
        "maximum_addon_positions": int(maximum_addon_positions),
        "maximum_account_positions": int(maximum_account_positions),
    }
    return factors, audit


def policy_metrics(
    prior: ModuleType,
    meta: pd.DataFrame,
    bars: pd.DataFrame,
    factors: np.ndarray,
    baseline_closed: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    closed, monthly, yearly = prior.closed_metrics(meta, factors)
    floating = prior.weighted_floating_metrics(bars, meta, factors)
    delta = meta[PNL].to_numpy(dtype=float) * (
        np.asarray(factors, dtype=float) - 1.0
    )
    bootstrap = prior.moving_week_block_bootstrap(
        meta,
        delta,
        repetitions=BOOTSTRAP_REPS,
    )
    return (
        {
            "closed": closed,
            "floating": floating,
            "delta_pnl_usd": float(
                closed["net_pnl_usd"] - baseline_closed["net_pnl_usd"]
            ),
            "weekly_block_bootstrap": bootstrap,
        },
        monthly,
        yearly,
    )


def subset_policy_metrics(
    prior: ModuleType,
    meta: pd.DataFrame,
    bars: pd.DataFrame,
    factors: np.ndarray,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    mask = meta["entry_time"].ge(start) & meta["entry_time"].lt(end)
    window_meta = meta.loc[mask].reset_index(drop=True)
    window_factors = np.asarray(factors, dtype=float)[mask.to_numpy()]
    if window_meta.empty:
        raise ValueError("Recent evaluation window has no trades")
    start_bar = window_meta["entry_time"].min().floor("5min")
    end_bar = window_meta["exit_time"].max().ceil("5min")
    window_bars = bars.loc[
        bars["timestamp_utc"].ge(start_bar)
        & bars["timestamp_utc"].le(end_bar)
    ].reset_index(drop=True)
    closed, _, _ = prior.closed_metrics(window_meta, window_factors)
    floating = prior.weighted_floating_metrics(
        window_bars,
        window_meta,
        window_factors,
    )
    return {"closed": closed, "floating": floating}


def gate_results(
    baseline: dict[str, Any],
    policy: dict[str, Any],
    recent_baseline: dict[str, Any],
    recent_policy: dict[str, Any],
    feature_audit: dict[str, Any],
    training_audit: dict[str, Any],
    risk_audit: dict[str, Any],
    risk_limits: dict[str, float],
    seed_sensitivity: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, bool]:
    gates = contract["gates"]
    baseline_closed = baseline["closed"]
    policy_closed = policy["closed"]
    baseline_floating = baseline["floating"]
    policy_floating = policy["floating"]
    required_ratio = (
        baseline_floating["net_to_floating_drawdown"]
        * (
            1.0
            + float(
                gates[
                    "minimum_net_to_floating_drawdown_improvement_fraction"
                ]
            )
        )
    )
    nonnegative_seeds = sum(
        item["delta_pnl_usd"] >= 0.0 for item in seed_sensitivity
    )
    return {
        "all_features_available_at_entry": (
            feature_audit["selected_bar_unavailable_at_entry_rows"] == 0
        ),
        "training_used_no_missing_risk": (
            training_audit["training_missing_risk_rows"] == 0
        ),
        "topups_used_no_missing_risk": (
            risk_audit["accepted_missing_risk_topups"] == 0
        ),
        "no_baseline_trade_skipped": (
            risk_audit["skipped_trade_rows"] == 0
        ),
        "net_pnl_not_below_baseline": (
            policy_closed["net_pnl_usd"] >= baseline_closed["net_pnl_usd"]
        ),
        "profit_factor_not_below_baseline": (
            policy_closed["profit_factor"] >= baseline_closed["profit_factor"]
        ),
        "floating_drawdown_not_above_baseline": (
            policy_floating["maximum_floating_drawdown_usd"]
            <= baseline_floating["maximum_floating_drawdown_usd"]
        ),
        "net_to_floating_drawdown_improves_at_least_5pct": (
            policy_floating["net_to_floating_drawdown"] >= required_ratio
        ),
        "green_month_within_2_points": (
            policy_closed["green_month_percentage"]
            >= baseline_closed["green_month_percentage"]
            - float(gates["maximum_green_month_decline_percentage_points"])
        ),
        "at_least_5_of_6_delta_years_nonnegative": (
            policy_closed["nonnegative_entry_years"]
            >= int(gates["minimum_nonnegative_delta_years"])
        ),
        "weekly_block_bootstrap_lower_bound_above_zero": (
            policy["weekly_block_bootstrap"]["lower_95_one_sided_usd"] > 0.0
        ),
        "recent_net_pnl_not_below_baseline": (
            recent_policy["closed"]["net_pnl_usd"]
            >= recent_baseline["closed"]["net_pnl_usd"]
        ),
        "recent_profit_factor_not_below_baseline": (
            recent_policy["closed"]["profit_factor"]
            >= recent_baseline["closed"]["profit_factor"]
        ),
        "recent_closed_drawdown_not_above_baseline": (
            recent_policy["closed"]["closed_trade_drawdown_usd"]
            <= recent_baseline["closed"]["closed_trade_drawdown_usd"]
        ),
        "minimum_4_of_5_seeds_nonnegative": (
            nonnegative_seeds >= int(gates["minimum_seeds_with_nonnegative_delta"])
        ),
        "lot_values_broker_expressible": set(
            risk_audit["lot_values"]
        ).issubset({0.01, 0.02}),
        "account_risk_limit_respected": (
            risk_audit["maximum_known_account_risk_usd"]
            <= float(risk_limits["account_initial_risk_usd"]) + 1e-9
        ),
        "directional_risk_limit_respected": (
            risk_audit["maximum_known_direction_risk_usd"]
            <= float(risk_limits["directional_initial_risk_usd"]) + 1e-9
        ),
        "addon_risk_limit_respected": (
            risk_audit["maximum_known_addon_risk_usd"]
            <= float(risk_limits["addon_initial_risk_usd"]) + 1e-9
        ),
        "position_limits_respected": (
            risk_audit["maximum_account_positions"]
            <= int(risk_limits["maximum_account_positions"])
            and risk_audit["maximum_core_positions"]
            <= int(risk_limits["maximum_core_positions"])
            and risk_audit["maximum_addon_positions"]
            <= int(risk_limits["maximum_addon_positions"])
        ),
    }


def evaluate_diagnostic(
    name: str,
    prior: ModuleType,
    meta: pd.DataFrame,
    bars: pd.DataFrame,
    proposals: np.ndarray,
    demo_config: dict[str, Any],
    risk_limits: dict[str, float],
    baseline_closed: dict[str, Any],
) -> dict[str, Any]:
    factors, risk_audit = topup_factors(
        meta,
        proposals,
        demo_config,
        risk_limits,
        prior,
    )
    closed, _, yearly = prior.closed_metrics(meta, factors)
    floating = prior.weighted_floating_metrics(bars, meta, factors)
    return {
        "name": name,
        "proposals": int(np.asarray(proposals, dtype=bool).sum()),
        "accepted_topups": risk_audit["accepted_topups"],
        "net_pnl_usd": closed["net_pnl_usd"],
        "delta_pnl_usd": (
            closed["net_pnl_usd"] - baseline_closed["net_pnl_usd"]
        ),
        "profit_factor": closed["profit_factor"],
        "floating_drawdown_usd": floating["maximum_floating_drawdown_usd"],
        "net_to_floating_drawdown": floating["net_to_floating_drawdown"],
        "nonnegative_delta_years": int(
            yearly["delta_pnl_usd"].ge(0.0).sum()
        ),
    }


def write_result_markdown(result: dict[str, Any]) -> None:
    baseline = result["baseline"]
    policy = result["primary_policy"]
    recent_baseline = result["recent_window"]["baseline"]
    recent_policy = result["recent_window"]["primary_policy"]
    lines = [
        "# V60 Executable ML Top-Up V1 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Historical development research only. No runtime or broker authorization "
        "is granted.",
        "",
        "## Causality And Behavior",
        "",
        f"- Current V60 population: "
        f"{result['population_audit']['current_population_rows']} rows.",
        f"- Incomplete M5 bars used: "
        f"{result['feature_audit']['selected_bar_unavailable_at_entry_rows']}.",
        f"- Known-risk model-training population: "
        f"{result['training_audit']['known_risk_rows']} rows.",
        f"- Proposed / accepted top-ups: "
        f"{policy['risk_audit']['proposed_topups']} / "
        f"{policy['risk_audit']['accepted_topups']}.",
        f"- Baseline trades skipped: "
        f"{policy['risk_audit']['skipped_trade_rows']}.",
        "",
        "## Full Walk-Forward",
        "",
        "| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD | delta years >= 0 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, item in (
        ("V60 baseline", baseline),
        ("Primary source-aware ML", policy),
    ):
        closed = item["closed"]
        floating = item["floating"]
        lines.append(
            f"| {label} | {closed['trade_rows']} | "
            f"${closed['net_pnl_usd']:.2f} | "
            f"{closed['profit_factor']:.3f} | "
            f"{100.0 * closed['win_rate']:.2f}% | "
            f"${closed['closed_trade_drawdown_usd']:.2f} | "
            f"${floating['maximum_floating_drawdown_usd']:.2f} | "
            f"{floating['net_to_floating_drawdown']:.2f} | "
            f"{closed['nonnegative_entry_years']}/"
            f"{closed['evaluated_entry_years']} |"
        )
    lines.extend(
        [
            "",
            f"Primary delta: **${policy['delta_pnl_usd']:.2f}**. "
            f"Weekly-block one-sided 95% lower bound: "
            f"**${policy['weekly_block_bootstrap']['lower_95_one_sided_usd']:.2f}**.",
            "",
            "## Recent Window",
            "",
            "Window: 2025-07-01 through 2026-06-30, grouped by entry time.",
            "",
            "| policy | trades | net | PF | win rate | closed DD | floating DD |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, item in (
        ("V60 baseline", recent_baseline),
        ("Primary source-aware ML", recent_policy),
    ):
        closed = item["closed"]
        floating = item["floating"]
        lines.append(
            f"| {label} | {closed['trade_rows']} | "
            f"${closed['net_pnl_usd']:.2f} | "
            f"{closed['profit_factor']:.3f} | "
            f"{100.0 * closed['win_rate']:.2f}% | "
            f"${closed['closed_trade_drawdown_usd']:.2f} | "
            f"${floating['maximum_floating_drawdown_usd']:.2f} |"
        )
    passed = sum(result["gates"].values())
    total = len(result["gates"])
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- Passed: **{passed}/{total}**.",
        ]
    )
    for name, value in result["gates"].items():
        lines.append(f"- {'PASS' if value else 'FAIL'}: `{name}`.")
    lines.extend(
        [
            "",
            "## Demo Verdict",
            "",
            result["demo_verdict"],
            "",
        ]
    )
    (OUTPUTS / "RESULT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    contract = load_contract()
    prior = load_module("codex_v60_causal_retest", PRIOR_SOURCE_PATH)
    prior_contract = prior.load_contract()
    feature_module = prior.load_module(
        "codex_topup_market_features",
        prior.FEATURES_PATH,
    )
    cooldown_module = prior.load_module(
        "codex_topup_cooldown",
        prior.COOLDOWN_PATH,
    )
    floating_module = prior.load_module(
        "codex_topup_floating",
        prior.FLOATING_AUDIT_PATH,
    )
    demo_config_path = (
        REPO_ROOT / contract["inputs"]["current_demo_config"]["path"]
    )
    demo_config = json.loads(demo_config_path.read_text(encoding="utf-8"))

    ledger, population_audit = prior.load_current_population(
        prior_contract,
        cooldown_module,
    )
    base_X, meta, feature_audit = prior.build_corrected_features(
        ledger,
        feature_module,
    )
    source_X = build_source_features(
        base_X,
        meta,
        list(contract["features"]["primary_source_ids"]),
    )
    years = set(int(value) for value in contract["population"]["test_entry_years"])
    evaluation_mask = meta["entry_time"].dt.year.isin(years).to_numpy()
    meta_evaluation = meta.loc[evaluation_mask].reset_index(drop=True)
    base_X_evaluation = base_X.loc[evaluation_mask].reset_index(drop=True)
    source_X_evaluation = source_X.loc[evaluation_mask].reset_index(drop=True)
    if meta_evaluation.empty:
        raise ValueError("No rows reached the outer evaluation years")

    primary_all, annual_models = walkforward_dual(
        source_X,
        meta,
        contract,
        int(contract["model"]["primary_seed"]),
    )
    primary = primary_all.loc[evaluation_mask].reset_index(drop=True)
    proposals = primary["topup_proposed"].to_numpy(dtype=bool)
    risk_limits = {
        key: float(value)
        for key, value in contract["frozen_risk_limits"].items()
    }
    primary_factors, primary_risk_audit = topup_factors(
        meta_evaluation,
        proposals,
        demo_config,
        risk_limits,
        prior,
    )

    bars, market_data_audit = prior.load_floating_bars(
        floating_module,
        meta_evaluation,
    )
    baseline_factors = np.ones(len(meta_evaluation), dtype=float)
    baseline_closed, baseline_monthly, baseline_yearly = prior.closed_metrics(
        meta_evaluation,
        baseline_factors,
    )
    baseline_floating = prior.weighted_floating_metrics(
        bars,
        meta_evaluation,
        baseline_factors,
    )
    baseline = {
        "closed": baseline_closed,
        "floating": baseline_floating,
    }
    primary_policy, primary_monthly, primary_yearly = policy_metrics(
        prior,
        meta_evaluation,
        bars,
        primary_factors,
        baseline_closed,
    )
    primary_policy["risk_audit"] = primary_risk_audit

    recent_start = pd.Timestamp(
        contract["population"]["recent_window_start_utc"]
    )
    recent_end = pd.Timestamp(
        contract["population"]["recent_window_end_utc"]
    )
    recent_baseline = subset_policy_metrics(
        prior,
        meta_evaluation,
        bars,
        baseline_factors,
        recent_start,
        recent_end,
    )
    recent_primary = subset_policy_metrics(
        prior,
        meta_evaluation,
        bars,
        primary_factors,
        recent_start,
        recent_end,
    )

    seed_sensitivity: list[dict[str, Any]] = []
    seed_decisions: dict[int, pd.DataFrame] = {
        int(contract["model"]["primary_seed"]): primary
    }
    for seed in [
        int(contract["model"]["primary_seed"]),
        *[int(value) for value in contract["model"]["diagnostic_seeds"]],
    ]:
        if seed not in seed_decisions:
            decisions_all, _ = walkforward_dual(
                source_X,
                meta,
                contract,
                seed,
            )
            seed_decisions[seed] = decisions_all.loc[
                evaluation_mask
            ].reset_index(drop=True)
        seed_proposals = seed_decisions[seed][
            "topup_proposed"
        ].to_numpy(dtype=bool)
        seed_factors, seed_risk = topup_factors(
            meta_evaluation,
            seed_proposals,
            demo_config,
            risk_limits,
            prior,
        )
        seed_closed, _, seed_yearly = prior.closed_metrics(
            meta_evaluation,
            seed_factors,
        )
        seed_sensitivity.append(
            {
                "seed": seed,
                "proposed_topups": int(seed_proposals.sum()),
                "accepted_topups": int(seed_risk["accepted_topups"]),
                "net_pnl_usd": float(seed_closed["net_pnl_usd"]),
                "delta_pnl_usd": float(
                    seed_closed["net_pnl_usd"]
                    - baseline_closed["net_pnl_usd"]
                ),
                "profit_factor": float(seed_closed["profit_factor"]),
                "nonnegative_delta_years": int(
                    seed_yearly["delta_pnl_usd"].ge(0.0).sum()
                ),
            }
        )

    threshold = float(
        contract["score_policy"]["minimum_joint_score_exclusive"]
    )
    expected_only = (
        primary["expected_pnl_rank"].fillna(-np.inf).to_numpy() > threshold
    )
    probability_only = (
        primary["win_probability_rank"].fillna(-np.inf).to_numpy() > threshold
    )
    market_all, _ = walkforward_dual(
        base_X,
        meta,
        contract,
        int(contract["model"]["primary_seed"]),
    )
    market = market_all.loc[evaluation_mask].reset_index(drop=True)
    diagnostics = [
        evaluate_diagnostic(
            "expected_pnl_rank_only",
            prior,
            meta_evaluation,
            bars,
            expected_only,
            demo_config,
            risk_limits,
            baseline_closed,
        ),
        evaluate_diagnostic(
            "win_probability_rank_only",
            prior,
            meta_evaluation,
            bars,
            probability_only,
            demo_config,
            risk_limits,
            baseline_closed,
        ),
        evaluate_diagnostic(
            "market_only_dual_model",
            prior,
            meta_evaluation,
            bars,
            market["topup_proposed"].to_numpy(dtype=bool),
            demo_config,
            risk_limits,
            baseline_closed,
        ),
    ]

    training_audit = {
        "known_risk_rows": int(meta["risk_usd"].notna().sum()),
        "missing_risk_rows": int(meta["risk_usd"].isna().sum()),
        "training_missing_risk_rows": 0,
        "source_feature_columns": [
            name for name in source_X.columns if name.startswith("source__")
        ],
        "source_aware_feature_count": int(source_X.shape[1]),
        "evaluation_rows": int(len(meta_evaluation)),
        "evaluation_known_risk_rows": int(
            meta_evaluation["risk_usd"].notna().sum()
        ),
    }
    gates = gate_results(
        baseline,
        primary_policy,
        recent_baseline,
        recent_primary,
        feature_audit,
        training_audit,
        primary_risk_audit,
        risk_limits,
        seed_sensitivity,
        contract,
    )
    passed = bool(all(gates.values()))
    decision = (
        "HISTORICAL_DEVELOPMENT_GATES_PASS_PROSPECTIVE_SHADOW_NOMINATION_ONLY"
        if passed
        else "HISTORICAL_OR_EXECUTION_GATES_FAIL_KEEP_ML_OFF_DEMO"
    )
    demo_verdict = (
        "The historical development gates pass, but the record was already "
        "exposed. Prepare a separate fail-closed prospective shadow candidate; "
        "do not let ML affect demo orders."
        if passed
        else "Do not connect this ML candidate to demo shadow or orders. Keep "
        "deterministic V60 unchanged."
    )

    decision_rows = pd.concat(
        [
            meta_evaluation.reset_index(drop=True),
            primary.reset_index(drop=True),
        ],
        axis=1,
    )
    decision_rows["topup_accepted"] = primary_factors == 2.0
    decision_rows["lot"] = primary_factors * 0.01
    decision_rows["baseline_pnl_usd"] = decision_rows[PNL]
    decision_rows["policy_pnl_usd"] = (
        decision_rows[PNL] * primary_factors
    )

    result = {
        "schema_version": "codex_v60_executable_ml_topup_v1_result",
        "decision": decision,
        "demo_verdict": demo_verdict,
        "runtime_changed": False,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "population_audit": population_audit,
        "feature_audit": feature_audit,
        "training_audit": training_audit,
        "market_data_audit": market_data_audit,
        "baseline": baseline,
        "primary_policy": primary_policy,
        "recent_window": {
            "start_utc": recent_start.isoformat(),
            "end_utc_exclusive": recent_end.isoformat(),
            "baseline": recent_baseline,
            "primary_policy": recent_primary,
        },
        "seed_sensitivity": seed_sensitivity,
        "locked_diagnostics": diagnostics,
        "gates": gates,
        "gates_passed": int(sum(gates.values())),
        "gates_total": int(len(gates)),
        "limitations": [
            "The architecture was chosen after the historical V60 record was exposed.",
            "A historical pass can nominate prospective shadow observation only.",
            "M5 bar extremes cannot order an intrabar entry against that bar's high or low.",
            "The current-account floating halt and restart path is not simulated.",
            "R1 has missing historical initial risk and is never trained or topped up.",
        ],
    }
    result = prior.json_ready(result)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    source_X_evaluation.to_parquet(
        OUTPUTS / "SOURCE_AWARE_FEATURES.parquet",
        index=False,
    )
    decision_rows.to_parquet(
        OUTPUTS / "PRIMARY_DECISIONS.parquet",
        index=False,
    )
    annual_models.to_csv(OUTPUTS / "ANNUAL_MODELS.csv", index=False)
    pd.DataFrame(seed_sensitivity).to_csv(
        OUTPUTS / "SEED_SENSITIVITY.csv",
        index=False,
    )
    pd.DataFrame(diagnostics).to_csv(
        OUTPUTS / "LOCKED_DIAGNOSTICS.csv",
        index=False,
    )
    baseline_monthly.rename(
        columns={"policy_pnl_usd": "baseline_policy_pnl_usd"}
    ).to_csv(OUTPUTS / "BASELINE_MONTHLY.csv", index=False)
    primary_monthly.to_csv(OUTPUTS / "PRIMARY_MONTHLY.csv", index=False)
    baseline_yearly.rename(
        columns={"policy_pnl_usd": "baseline_policy_pnl_usd"}
    ).to_csv(OUTPUTS / "BASELINE_YEARLY.csv", index=False)
    primary_yearly.to_csv(OUTPUTS / "PRIMARY_YEARLY.csv", index=False)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_result_markdown(result)

    integrity_files = [
        path
        for path in sorted(OUTPUTS.iterdir())
        if path.name != "INTEGRITY.json" and path.is_file()
    ]
    integrity = {
        "schema_version": "codex_v60_executable_ml_topup_v1_integrity",
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "files": {
            path.name: {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in integrity_files
        },
    }
    integrity["integrity_sha256"] = canonical_sha256(integrity)
    (OUTPUTS / "INTEGRITY.json").write_text(
        json.dumps(integrity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
