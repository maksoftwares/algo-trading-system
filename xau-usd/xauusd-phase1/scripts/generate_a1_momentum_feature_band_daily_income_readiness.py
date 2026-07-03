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
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02"

DRAFT = PHASE1_ROOT / "docs" / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md"
MANIFEST = DRAFT.with_suffix(DRAFT.suffix + ".sha256.json")
TRADEOFF_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.json"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"

EXPECTED_SHA = "188b3ded97da503ecb43faa38671f7a0b7482df935091f9fa8a91cf9d0f79a1b"
EXPECTED_MAGICS = {
    "feature_band_daily_income_long": 932292,
    "feature_band_daily_income_v13_both": 932293,
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
    tradeoff = load_json(TRADEOFF_JSON)
    owner = tradeoff.get("owner_target_50_candidate", {})
    ea_text = EA_SOURCE.read_text(encoding="utf-8")

    checks: list[dict[str, str]] = [
        check(
            "draft_hash_matches_expected",
            draft_sha == EXPECTED_SHA,
            f"draft_sha={draft_sha}",
        ),
        check(
            "manifest_hash_matches_draft",
            manifest.get("sha256") == draft_sha,
            f"manifest_sha={manifest.get('sha256')}",
        ),
        check(
            "owner_target_metrics_present",
            owner.get("profit_target_usd") == 50.0
            and owner.get("max_trades_per_day_guard") == 6.0
            and owner.get("trades", 0) >= 1800
            and owner.get("trades_per_active_day", 0) >= 3.0
            and owner.get("win_rate_pct", 0) >= 60.0
            and owner.get("profit_factor", 0) >= 1.25
            and owner.get("positive_day_pct", 0) >= 58.0
            and owner.get("top100_removed_usd", 0) > 0,
            (
                f"trades={owner.get('trades')}, wr={owner.get('win_rate_pct')}, "
                f"pf={owner.get('profit_factor')}, tpa={owner.get('trades_per_active_day')}, "
                f"pos_day={owner.get('positive_day_pct')}"
            ),
        ),
        check(
            "ea_default_off_profit_target_input",
            "input double InpPortfolioDailyProfitTargetUsd = 0.00;" in ea_text,
            "EA exposes portfolio profit target default-off.",
        ),
        check(
            "ea_feature_band_default_off_inputs",
            "input bool   InpShortCloseToRecentExtremeBlockMaxEnabled = false;" in ea_text
            and "input double InpShortCloseToRecentExtremeBlockMax = -2.51;" in ea_text,
            "EA exposes short close-to-recent-extreme max block default-off.",
        ),
    ]

    for variant, magic in EXPECTED_MAGICS.items():
        config = VARIANT_CONFIGS.get(variant, {})
        checks.extend(
            [
                check(
                    f"{variant}_magic",
                    config.get("magic") == magic,
                    f"magic={config.get('magic')}",
                ),
                check(
                    f"{variant}_spec_hash",
                    config.get("spec_sha256") == EXPECTED_SHA,
                    f"spec_sha256={config.get('spec_sha256')}",
                ),
                check(
                    f"{variant}_owner_target_guard",
                    config.get("portfolio_daily_guard_enabled") == "true"
                    and config.get("portfolio_guard_magic_csv") == "932292,932293"
                    and config.get("portfolio_daily_profit_target_usd") == "50.00"
                    and config.get("portfolio_max_trades_per_day") == "6"
                    and config.get("portfolio_daily_loss_stop_usd") == "0.00",
                    (
                        f"guard_csv={config.get('portfolio_guard_magic_csv')}, "
                        f"target={config.get('portfolio_daily_profit_target_usd')}, "
                        f"max_trades={config.get('portfolio_max_trades_per_day')}"
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
        "tradeoff_report": rel(REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md"),
        "owner_target_50_candidate": owner,
        "planned_variants": {
            variant: {
                "magic": VARIANT_CONFIGS[variant]["magic"],
                "run_id": VARIANT_CONFIGS[variant]["run_id"],
                "order_comment": VARIANT_CONFIGS[variant]["order_comment"],
                "portfolio_guard_magic_csv": VARIANT_CONFIGS[variant]["portfolio_guard_magic_csv"],
                "portfolio_daily_profit_target_usd": VARIANT_CONFIGS[variant]["portfolio_daily_profit_target_usd"],
                "portfolio_max_trades_per_day": VARIANT_CONFIGS[variant]["portfolio_max_trades_per_day"],
                "spec_sha256": VARIANT_CONFIGS[variant]["spec_sha256"],
            }
            for variant in EXPECTED_MAGICS
        },
        "checks": checks,
    }


def render(payload: dict[str, Any]) -> str:
    owner = payload["owner_target_50_candidate"]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Daily-Income Readiness - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        "## Candidate",
        "",
        "Owner-target package: `+50 USD` portfolio target, max `6` package trades/day, no daily loss stop.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Trades | {owner.get('trades', 'n/a')} |",
        f"| Win rate | {owner.get('win_rate_pct', 'n/a')}% |",
        f"| Net USD | {owner.get('net_usd', 'n/a')} |",
        f"| Profit factor | {owner.get('profit_factor', 'n/a')} |",
        f"| Active days | {owner.get('active_days', 'n/a')} |",
        f"| Trades / active day | {owner.get('trades_per_active_day', 'n/a')} |",
        f"| 3+ trade days | {owner.get('three_plus_trade_day_pct', 'n/a')}% |",
        f"| Positive active days | {owner.get('positive_day_pct', 'n/a')}% |",
        f"| Top 100 removed | {owner.get('top100_removed_usd', 'n/a')} |",
        f"| Max closed DD | {owner.get('max_closed_drawdown_usd', 'n/a')} |",
        "",
        "## Planned Lanes",
        "",
        "| Variant | Magic | Run id | Comment | Target | Max trades |",
        "|---|---:|---|---|---:|---:|",
    ]
    for variant, data in payload["planned_variants"].items():
        lines.append(
            f"| `{variant}` | {data['magic']} | `{data['run_id']}` | `{data['order_comment']}` | "
            f"{data['portfolio_daily_profit_target_usd']} | {data['portfolio_max_trades_per_day']} |"
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
            f"- Tradeoff report: `{payload['tradeoff_report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_payload()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "draft_sha256": payload["draft_sha256"]}, indent=2))
    return 0 if payload["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
