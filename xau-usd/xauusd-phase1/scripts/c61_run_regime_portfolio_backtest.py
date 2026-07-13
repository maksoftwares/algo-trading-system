from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen continuous exact-MT5 regime portfolio backtest.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--variant-timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "scripts"))
    import run_a1_r1_box_clean_requalification_exact as r1_builder
    import run_a1_r2_pullback_rejection_short_v1_exact as r2_builder
    import run_a1_xau_m5_momentum_backtest_variants as runner
    from ml.a3_meta_v1.regime_portfolio_backtest import analyze_regime_portfolio

    r1_variant = r1_builder.build_variants()[0]
    r2_variant = next(variant for variant in r2_builder.build_variants() if variant.name == "r2_pullback_short_h1_confirm")
    variants = [r1_variant, r2_variant]
    runner.VARIANTS = variants

    reports = root / "outputs" / "reports"
    stem = "A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713"
    mt5_md = reports / f"{stem}_MT5.md"
    mt5_json = reports / f"{stem}_MT5.json"
    report_json = reports / f"{stem}.json"
    report_md = reports / f"{stem}.md"
    trades_csv = reports / f"{stem}_TRADES.csv"
    prereg = root / "docs" / "A3_ML_REGIME_PORTFOLIO_BACKTEST_PREREG_2026_07_13.md"

    payload = runner.run_variants(
        from_date="2016.07.01",
        to_date="2026.06.30",
        tag="A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713",
        report_md=mt5_md,
        report_json=mt5_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    payload["frozen_tester_input_sha256"] = _stable_hash([variant.tester_inputs for variant in variants])
    output = analyze_regime_portfolio(
        root,
        payload,
        preregistration=prereg,
        report_json=report_json,
        report_md=report_md,
        trades_csv=trades_csv,
    )
    print(f"A3 ML continuous regime portfolio status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
