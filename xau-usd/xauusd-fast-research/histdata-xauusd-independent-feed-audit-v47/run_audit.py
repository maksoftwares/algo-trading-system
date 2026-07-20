from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from audit import load_config, run_audit, sha256_file  # noqa: E402


def render_markdown(result: dict[str, object]) -> str:
    source = result["histdata_source_audit"]
    comparison = result["crossvenue_comparison"]
    gates = result["gates"]
    lines = [
        "# HistData XAUUSD Independent-Feed Audit V47",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "This is a source-quality decision only. It is not evidence of trading edge and has no execution authority.",
        "",
        "## Source Quality",
        "",
        f"- Rows: `{source['rows']:,}`",
        f"- UTC span: `{source['first_timestamp_utc']}` to `{source['last_timestamp_utc']}`",
        f"- Nonpositive/crossed quotes: `{source['nonpositive_quote_rows']}/{source['crossed_quote_rows']}`",
        f"- Median / p99 spread: `${source['median_spread_dollars']:.4f}` / `${source['spread_p99_dollars']:.4f}`",
        "",
        "## Dukascopy Comparison",
        "",
        f"- Matched M5 bars: `{comparison['matched_m5_bars']:,}`",
        f"- Active-bar coverage: `{comparison['active_bar_coverage_fraction']:.2%}`",
        f"- Contemporaneous return correlation: `{comparison['contemporaneous_return_correlation']:.6f}`",
        f"- Median absolute midpoint basis: `${comparison['median_absolute_basis_dollars']:.4f}`",
        f"- Basis standard deviation: `${comparison['basis_standard_deviation_dollars']:.4f}`",
        f"- Exact midpoint-close fraction: `{comparison['exact_mid_close_fraction']:.2%}`",
        "",
        "## Frozen Gates",
        "",
    ]
    lines.extend(
        f"- `{name}`: **{'PASS' if passed else 'FAIL'}**"
        for name, passed in gates.items()
    )
    lines.extend(
        [
            "",
            "## Next Decision",
            "",
            (
                "Acquire additional free months and preregister a causal cross-venue feature experiment."
                if result["all_gates_pass"]
                else "Discard this source route; do not mine strategies from it."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def artifact_manifest(paths: list[Path]) -> dict[str, object]:
    files = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in paths
    }
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"files": files, "manifest_sha256": hashlib.sha256(canonical).hexdigest()}


def main() -> int:
    config = load_config(ROOT)
    lock_path = ROOT / "outputs" / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError(
            "Write and verify the V47 contract before opening the comparison"
        )

    artifacts = run_audit(config)
    result = artifacts["result"]
    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    m5_path = output_dir / config["outputs"]["m5_quotes"]
    daily_path = output_dir / config["outputs"]["daily_audit"]
    json_path = output_dir / config["outputs"]["result_json"]
    markdown_path = output_dir / config["outputs"]["result_markdown"]
    artifacts["histdata_m5"].to_parquet(m5_path, index=False)
    artifacts["daily"].to_csv(daily_path, index=False, lineterminator="\n")
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    manifest_path = output_dir / config["outputs"]["manifest"]
    manifest = artifact_manifest(
        [lock_path, m5_path, daily_path, json_path, markdown_path]
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "decision": result["decision"],
        "rows": result["histdata_source_audit"]["rows"],
        "matched_m5_bars": result["crossvenue_comparison"]["matched_m5_bars"],
        "coverage": result["crossvenue_comparison"]["active_bar_coverage_fraction"],
        "return_correlation": result["crossvenue_comparison"][
            "contemporaneous_return_correlation"
        ],
        "execution_authorized": False,
    }
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
