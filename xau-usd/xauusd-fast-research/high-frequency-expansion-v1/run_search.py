from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dataset import MODEL_FEATURES, sha256_file  # noqa: E402
from evaluation import (  # noqa: E402
    attempt_policies,
    evaluate_gate,
    feature_subset,
    metrics,
    model_specifications,
    prepare_best_actions,
    ranking_key,
    select_trades,
)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_model(spec: dict[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=float(spec["learning_rate"]),
        max_iter=int(spec["max_iter"]),
        max_leaf_nodes=int(spec["max_leaf_nodes"]),
        min_samples_leaf=int(spec["min_samples_leaf"]),
        l2_regularization=float(spec["l2_regularization"]),
        max_bins=int(spec["max_bins"]),
        random_state=int(spec["random_state"]),
    )


def fit_and_score(
    spec: dict[str, Any],
    actions: pd.DataFrame,
    fit_end: pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    features = feature_subset(str(spec["feature_subset"]))
    training = actions.loc[
        (actions["signal_time"] < fit_end) & (actions["exit_time"] < fit_end)
    ]
    if len(training) < 1000:
        raise ValueError(f"Insufficient training rows for {spec['model_id']}: {len(training)}")
    target = training["stress_net_r"].clip(-1.5, 2.25)
    model = make_model(spec)
    model.fit(training[features], target)
    scored = actions.copy()
    scored["model_score"] = model.predict(scored[features])
    diagnostics = {
        "fit_rows": int(len(training)),
        "feature_count": int(len(features)),
        "fit_target_mean": float(target.mean()),
        "fit_score_mean": float(scored.loc[training.index, "model_score"].mean()),
        "fit_spearman": float(
            scored.loc[training.index, "model_score"].corr(
                training["stress_net_r"], method="spearman"
            )
        ),
    }
    return scored, diagnostics


def flat_metrics(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "calendar_year_pf"}


def attempt_row(
    stage: str,
    policy: Any,
    spec: dict[str, Any],
    value: dict[str, Any],
    passed: bool,
    checks: dict[str, bool],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "stage": stage,
        "attempt_id": policy.attempt_id,
        "model_id": policy.model_id,
        "quantile": policy.quantile,
        "score_floor": policy.score_floor,
        "gate_pass": passed,
        "failed_checks": ",".join(key for key, check in checks.items() if not check),
        **{key: spec[key] for key in spec if key not in {"model_id"}},
        **diagnostics,
        **flat_metrics(value),
    }


def sorted_passing(frame: pd.DataFrame, maximum: int | None = None) -> pd.DataFrame:
    passing = frame.loc[frame["gate_pass"]].copy()
    if passing.empty:
        return passing
    order = sorted(passing.index, key=lambda index: ranking_key(passing.loc[index]))
    result = passing.loc[order].reset_index(drop=True)
    return result.head(maximum) if maximum is not None else result


def render_report(payload: dict[str, Any], attempts: pd.DataFrame, finalists: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD High-Frequency Expansion V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Research only. The Core remains unchanged and no prediction or broker action is authorized.",
        "",
        "## Search",
        "",
        f"Exactly {payload['attempt_count']} locked attempts were evaluated. "
        f"{payload['selection_pass_count']} passed selection and "
        f"{payload['internal_test_pass_count']} passed internal test.",
        "",
        "| Stage | Attempt | Trades/day | Stress PF | Avg R | Min year PF | DD R | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    selection_top = attempts.sort_values(
        ["gate_pass", "stress_pf"], ascending=[False, False], kind="mergesort"
    ).head(5)
    display = pd.concat([selection_top, finalists], ignore_index=True)
    for row in display.to_dict("records"):
        pf = row.get("stress_pf")
        pf_text = "NA" if pd.isna(pf) else f"{float(pf):.3f}"
        lines.append(
            f"| {row['stage']} | `{row['attempt_id']}` | {float(row['trades_per_weekday']):.3f} | "
            f"{pf_text} | {float(row['average_stress_r']):.3f} | "
            f"{float(row['minimum_calendar_year_pf']):.3f} | "
            f"{float(row['closed_drawdown_r']):.2f} | "
            f"{'PASS' if row['gate_pass'] else 'FAIL'} |"
        )
    lines.extend(["", "## Final evaluation", ""])
    if payload.get("final_attempt") is None:
        lines.append("No attempt earned access to the final exam under the locked gates.")
    else:
        final = payload["final_exam"]["metrics"]
        tail = payload["recent_tail"]["metrics"]
        lines.extend(
            [
                f"Final attempt: `{payload['final_attempt']}`.",
                f"Final exam: {final['trades']} trades, {final['trades_per_weekday']:.3f}/weekday, "
                f"stress PF {final['stress_pf']}, average {final['average_stress_r']:.3f}R, "
                f"drawdown {final['closed_drawdown_r']:.2f}R.",
                f"Recent tail: {tail['trades']} trades, {tail['trades_per_weekday']:.3f}/weekday, "
                f"stress PF {tail['stress_pf']}, average {tail['average_stress_r']:.3f}R.",
            ]
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "high_frequency_expansion_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    dataset_manifest_path = output / config["outputs"]["manifest"]
    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    action_path = output / config["outputs"]["candidate_actions"]
    if sha256_file(action_path) != dataset_manifest["action_parquet_sha256"]:
        raise ValueError("Action ledger hash does not match the dataset manifest")
    actions = pd.read_parquet(action_path)
    if not np.isfinite(actions[list(MODEL_FEATURES)]).all(axis=None):
        raise ValueError("Action ledger contains non-finite model features")

    search = config["search"]
    specs = model_specifications(
        int(search["model_specifications"]), int(search["random_seed"])
    )
    specs_by_id = {str(spec["model_id"]): spec for spec in specs}
    policies = attempt_policies(search)
    if len(policies) != int(config["research_controls"]["parameter_search_count"]):
        raise ValueError("Locked attempt count is not exact")
    policies_by_model: dict[str, list[Any]] = {}
    for policy in policies:
        policies_by_model.setdefault(policy.model_id, []).append(policy)

    selection_start, selection_end = map(pd.Timestamp, config["windows"]["selection"])
    attempt_rows: list[dict[str, Any]] = []
    for spec in specs:
        scored, diagnostics = fit_and_score(spec, actions, selection_start)
        best = prepare_best_actions(scored)
        for policy in policies_by_model[str(spec["model_id"])]:
            selected = select_trades(
                best,
                selection_start,
                selection_end,
                policy.quantile,
                policy.score_floor,
                search,
                config["portfolio"],
            )
            value = metrics(
                selected,
                selection_start,
                selection_end,
                int(config["gates"]["selection"]["top_winners_removed"]),
            )
            passed, checks = evaluate_gate(value, config["gates"]["selection"])
            attempt_rows.append(
                attempt_row("selection", policy, spec, value, passed, checks, diagnostics)
            )
    attempts = pd.DataFrame(attempt_rows)
    if len(attempts) != len(policies):
        raise ValueError(f"Expected {len(policies)} attempts, found {len(attempts)}")
    attempts.to_csv(output / config["outputs"]["attempts"], index=False, lineterminator="\n")

    advancing = sorted_passing(attempts, int(search["maximum_advancing_attempts"]))
    internal_start, internal_end = map(pd.Timestamp, config["windows"]["internal_test"])
    finalist_rows: list[dict[str, Any]] = []
    internal_trades: dict[str, pd.DataFrame] = {}
    policy_by_id = {policy.attempt_id: policy for policy in policies}
    for row in advancing.to_dict("records"):
        policy = policy_by_id[str(row["attempt_id"])]
        spec = specs_by_id[policy.model_id]
        scored, diagnostics = fit_and_score(spec, actions, internal_start)
        best = prepare_best_actions(scored)
        selected = select_trades(
            best,
            internal_start,
            internal_end,
            policy.quantile,
            policy.score_floor,
            search,
            config["portfolio"],
        )
        value = metrics(
            selected,
            internal_start,
            internal_end,
            int(config["gates"]["internal_test"]["top_winners_removed"]),
        )
        passed, checks = evaluate_gate(value, config["gates"]["internal_test"])
        finalist_rows.append(
            attempt_row("internal_test", policy, spec, value, passed, checks, diagnostics)
        )
        internal_trades[policy.attempt_id] = selected
    finalists = pd.DataFrame(finalist_rows)
    finalists.to_csv(output / config["outputs"]["finalists"], index=False, lineterminator="\n")
    internal_passing = sorted_passing(finalists) if not finalists.empty else finalists

    final_attempt: str | None = None
    selected_final = actions.iloc[0:0].copy()
    selected_final["model_score"] = pd.Series(dtype=float)
    final_payload: dict[str, Any] | None = None
    tail_payload: dict[str, Any] | None = None
    if not internal_passing.empty:
        chosen = internal_passing.iloc[0]
        final_attempt = str(chosen["attempt_id"])
        policy = policy_by_id[final_attempt]
        spec = specs_by_id[policy.model_id]
        final_start, final_end = map(pd.Timestamp, config["windows"]["final_exam"])
        scored, final_diagnostics = fit_and_score(spec, actions, final_start)
        best = prepare_best_actions(scored)
        selected_final = select_trades(
            best,
            final_start,
            final_end,
            policy.quantile,
            policy.score_floor,
            search,
            config["portfolio"],
        )
        final_value = metrics(
            selected_final,
            final_start,
            final_end,
            int(config["gates"]["final_exam"]["top_winners_removed"]),
        )
        final_pass, final_checks = evaluate_gate(final_value, config["gates"]["final_exam"])
        final_payload = {
            "metrics": final_value,
            "gate_pass": final_pass,
            "checks": final_checks,
            "model": final_diagnostics,
        }
        tail_start, tail_end = map(pd.Timestamp, config["windows"]["recent_tail"])
        tail_value = metrics(
            selected_final,
            tail_start,
            tail_end,
            int(config["gates"]["recent_tail"]["top_winners_removed"]),
        )
        tail_pass, tail_checks = evaluate_gate(tail_value, config["gates"]["recent_tail"])
        tail_payload = {"metrics": tail_value, "gate_pass": tail_pass, "checks": tail_checks}

    selected_path = output / config["outputs"]["selected_trades"]
    selected_final.to_parquet(selected_path, index=False)
    selection_passes = int(attempts["gate_pass"].sum())
    internal_passes = int(finalists["gate_pass"].sum()) if not finalists.empty else 0
    passed = bool(
        final_payload is not None
        and tail_payload is not None
        and final_payload["gate_pass"]
        and tail_payload["gate_pass"]
    )
    if passed:
        decision = "EXPANSION_V1_PASSES_REQUIRES_CORE_PORTFOLIO_TEST"
        interpretation = (
            "One locked Expansion ranker met frequency, expectancy, stability, and drawdown gates. "
            "It remains research-only until a shared-account test proves exact Core P&L preservation."
        )
    else:
        decision = "EXPANSION_V1_REJECTED"
        if selection_passes == 0:
            interpretation = (
                "None of the 1,000 locked attempts simultaneously recovered stable edge and the required "
                "frequency in the selection period. The Core remains intact; V1 must not be tuned after outcome."
            )
        elif internal_passes == 0:
            interpretation = (
                "Selection produced candidates, but none survived the later internal test. The result is "
                "evidence of selection instability, not permission to weaken gates."
            )
        else:
            interpretation = (
                "A finalist reached the final exam but failed at least one locked final or recent-tail gate. "
                "The Expansion layer is not accepted."
            )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "interpretation": interpretation,
        "attempt_count": int(len(attempts)),
        "selection_pass_count": selection_passes,
        "advancing_attempt_count": int(len(advancing)),
        "internal_test_pass_count": internal_passes,
        "final_attempt": final_attempt,
        "final_exam": final_payload,
        "recent_tail": tail_payload,
        "selected_trade_rows": int(len(selected_final)),
        "attempt_digest": frame_digest(
            attempts,
            ["attempt_id", "gate_pass", "trades", "stress_pf", "average_stress_r"],
        ),
        "selected_digest": frame_digest(
            selected_final,
            ["event_id", "action_id", "entry_time", "exit_time", "stress_net_r"],
        ),
        "authorization": config["research_controls"],
    }
    result_path = output / config["outputs"]["result_json"]
    write_json(result_path, payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render_report(payload, attempts, finalists), encoding="utf-8"
    )
    final_manifest = {
        **dataset_manifest,
        "run_search_sha256": sha256_file(ROOT / "run_search.py"),
        "attempt_count": int(len(attempts)),
        "attempt_digest": payload["attempt_digest"],
        "selected_trade_parquet_sha256": sha256_file(selected_path),
        "selected_digest": payload["selected_digest"],
        "result_json_sha256": sha256_file(result_path),
    }
    write_json(dataset_manifest_path, final_manifest)
    print(json.dumps(json_ready(payload), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
