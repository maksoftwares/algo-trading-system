from __future__ import annotations

import json

from src.serving import OUTPUTS, load_bundle, load_config, run_parity


def main() -> int:
    config = load_config()
    bundle = load_bundle(OUTPUTS / "MODEL_BUNDLE.joblib")
    audit = json.loads(
        (OUTPUTS / "BUILD_AUDIT.json").read_text(encoding="utf-8")
    )
    result, rows = run_parity(config, bundle, audit)
    rows.to_parquet(OUTPUTS / "CROSS_FEED_PARITY_ROWS.parquet", index=False)
    (OUTPUTS / "PARITY_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# V60 Portable Mature Top-Up Prospective V3",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "No July outcome labels were used.",
        "",
        "## Metrics",
        "",
    ]
    for key, value in result["metrics"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Gates", ""])
    for key, value in result["gates"].items():
        lines.append(f"- {'PASS' if value else 'FAIL'}: `{key}`")
    lines.extend(
        [
            "",
            "This result grants no live authority. Demo integration remains",
            "fail-closed to the deterministic baseline unless separately deployed.",
        ]
    )
    (OUTPUTS / "PARITY_RESULT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
