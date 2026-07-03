from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from attach_a1_xau_m5_momentum_continuation import VARIANT_CONFIGS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02"

DRAFT = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md"
)
MANIFEST = DRAFT.with_suffix(DRAFT.suffix + ".sha256.json")
OPTIMIZER_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.json"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"

EXPECTED_SHA = "1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71"
EXPECTED_MAGICS = {
    "feature_band_residual_plus50_cooldown10_long": 932298,
    "feature_band_residual_plus50_cooldown10_v13_both": 932299,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def build_payload() -> dict[str, Any]:
    draft_sha = sha256(DRAFT)
    manifest = load_json(MANIFEST)
    optimizer = load_json(OPTIMIZER_JSON)
    candidate = optimizer.get("named_candidates", {}).get("owner_target_50", {})
    ea_text = EA_SOURCE.read_text(encoding="utf-8")

    checks: list[dict[str, str]] = [
        check("draft_hash_matches_expected", draft_sha == EXPECTED_SHA, f"draft_sha={draft_sha}"),
        check(
            "manifest_hash_matches_draft",
            manifest.get("sha256") == draft_sha,
            f"manifest_sha={manifest.get('sha256')}",
        ),
        check(
            "candidate_is_owner_plus50_cooldown10",
            candidate.get("profit_target_usd") == 50.0
            and candidate.get("max_trades_per_day_guard") == 6
            and candidate.get("cooldown_after_loss_minutes") == 10,
            (
                f"target={candidate.get('profit_target_usd')}, "
                f"max_trades={candidate.get('max_trades_per_day_guard')}, "
                f"cooldown={candidate.get('cooldown_after_loss_minutes')}"
            ),
        ),
        check(
            "candidate_preserves_frequency",
            candidate.get("trades", 0) >= 1800
            and candidate.get("trades_per_active_day", 0) >= 3.0
            and candidate.get("three_plus_trade_day_pct", 0) >= 50.0,
            (
                f"trades={candidate.get('trades')}, tpa={candidate.get('trades_per_active_day')}, "
                f"three_plus={candidate.get('three_plus_trade_day_pct')}"
            ),
        ),
        check(
            "candidate_meets_quality_floor",
            candidate.get("win_rate_pct", 0) >= 65.0
            and (candidate.get("profit_factor") or 0.0) >= 1.45
            and candidate.get("positive_day_pct", 0) >= 60.0
            and candidate.get("top100_removed_usd", 0) > 0
            and candidate.get("top200_removed_usd", 0) > 0
            and candidate.get("older_net_usd", 0) > 0
            and candidate.get("newer_net_usd", 0) > 0,
            (
                f"wr={candidate.get('win_rate_pct')}, pf={candidate.get('profit_factor')}, "
                f"pos_day={candidate.get('positive_day_pct')}, top200={candidate.get('top200_removed_usd')}"
            ),
        ),
        check(
            "ea_supports_required_inputs_default_off",
            "input int    InpPortfolioCooldownAfterLossMinutes = 0;" in ea_text
            and "input bool   InpFeatureLossFilterEnabled      = false;" in ea_text
            and "input bool   InpShortCloseToRecentExtremeBlockMaxEnabled = false;" in ea_text,
            "EA exposes all required inputs default-off.",
        ),
    ]

    for variant, magic in EXPECTED_MAGICS.items():
        config = VARIANT_CONFIGS.get(variant, {})
        checks.extend(
            [
                check(f"{variant}_magic", config.get("magic") == magic, f"magic={config.get('magic')}"),
                check(
                    f"{variant}_spec_hash",
                    config.get("spec_sha256") == EXPECTED_SHA,
                    f"spec_sha256={config.get('spec_sha256')}",
                ),
                check(
                    f"{variant}_package_guard",
                    config.get("portfolio_daily_guard_enabled") == "true"
                    and config.get("portfolio_guard_magic_csv") == "932298,932299"
                    and config.get("portfolio_daily_profit_target_usd") == "50.00"
                    and config.get("portfolio_max_trades_per_day") == "6"
                    and config.get("portfolio_daily_loss_stop_usd") == "0.00"
                    and config.get("portfolio_cooldown_after_loss_minutes") == "10",
                    (
                        f"guard_csv={config.get('portfolio_guard_magic_csv')}, "
                        f"target={config.get('portfolio_daily_profit_target_usd')}, "
                        f"cooldown={config.get('portfolio_cooldown_after_loss_minutes')}"
                    ),
                ),
            ]
        )

    status = "PASS_READY_FOR_REVIEW_NOT_ATTACHED"
    if any(item["status"] == "FAIL" for item in checks):
        status = "FAIL"

    return {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "No MT5 runtime, charts, presets, orders, or positions are touched by this readiness report.",
        "decision": "review_ready_not_attached",
        "draft": rel(DRAFT),
        "draft_sha256": draft_sha,
        "optimizer_report": rel(REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md"),
        "candidate": candidate,
        "planned_variants": {
            variant: {
                "magic": VARIANT_CONFIGS[variant]["magic"],
                "run_id": VARIANT_CONFIGS[variant]["run_id"],
                "order_comment": VARIANT_CONFIGS[variant]["order_comment"],
                "portfolio_guard_magic_csv": VARIANT_CONFIGS[variant]["portfolio_guard_magic_csv"],
                "portfolio_daily_profit_target_usd": VARIANT_CONFIGS[variant]["portfolio_daily_profit_target_usd"],
                "portfolio_max_trades_per_day": VARIANT_CONFIGS[variant]["portfolio_max_trades_per_day"],
                "portfolio_cooldown_after_loss_minutes": VARIANT_CONFIGS[variant][
                    "portfolio_cooldown_after_loss_minutes"
                ],
                "spec_sha256": VARIANT_CONFIGS[variant]["spec_sha256"],
            }
            for variant in EXPECTED_MAGICS
        },
        "checks": checks,
    }


def render(payload: dict[str, Any]) -> str:
    candidate = payload["candidate"]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Residual +50 Cooldown10 Readiness - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        "## Candidate",
        "",
        "Optimized owner-target package: `+50 USD` portfolio target, max `6` package trades/day, `10` minute package cooldown after any closed package loss, LONG hour `18` blocked, and SHORT close-to-recent-extreme min tightened to `-0.92`.",
        "",
        "| Metric | Candidate |",
        "|---|---:|",
        f"| Trades | {candidate.get('trades', 'n/a')} |",
        f"| Win rate | {candidate.get('win_rate_pct', 'n/a')}% |",
        f"| Net USD | {candidate.get('net_usd', 'n/a')} |",
        f"| Profit factor | {candidate.get('profit_factor', 'n/a')} |",
        f"| Trades / active day | {candidate.get('trades_per_active_day', 'n/a')} |",
        f"| 3+ trade active days | {candidate.get('three_plus_trade_day_pct', 'n/a')}% |",
        f"| Positive active days | {candidate.get('positive_day_pct', 'n/a')}% |",
        f"| Top 100 removed | {candidate.get('top100_removed_usd', 'n/a')} |",
        f"| Top 200 removed | {candidate.get('top200_removed_usd', 'n/a')} |",
        f"| Max closed DD | {candidate.get('max_closed_drawdown_usd', 'n/a')} |",
        "",
        "## Planned Lanes",
        "",
        "| Variant | Magic | Run id | Comment | Target | Max trades | Cooldown after loss |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    for variant, data in payload["planned_variants"].items():
        lines.append(
            f"| `{variant}` | {data['magic']} | `{data['run_id']}` | `{data['order_comment']}` | "
            f"{data['portfolio_daily_profit_target_usd']} | {data['portfolio_max_trades_per_day']} | "
            f"{data['portfolio_cooldown_after_loss_minutes']} |"
        )

    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for item in payload["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Forward draft: `{payload['draft']}`",
            f"- Draft SHA256: `{payload['draft_sha256']}`",
            f"- Optimizer report: `{payload['optimizer_report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_payload()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    payload["report"] = rel(output_md)
    payload["json"] = rel(output_json)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "draft_sha256": payload["draft_sha256"]}, indent=2))
    return 0 if payload["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
