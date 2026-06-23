from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the fail-closed A3 ML demo readiness refresh cycle.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--refresh-live-readonly", action="store_true")
    parser.add_argument("--skip-research-preview-publish", action="store_true")
    parser.add_argument("--decision-json", type=Path)
    parser.add_argument("--apply-reviewer-configs", action="store_true")
    parser.add_argument("--post-attach-timeout-seconds", type=int, default=0)
    parser.add_argument("--post-attach-poll-seconds", type=int, default=5)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_readiness_cycle import run_demo_readiness_cycle  # noqa: PLC0415

    output = run_demo_readiness_cycle(
        root,
        report_json=args.report_json,
        refresh_live_readonly=args.refresh_live_readonly,
        publish_research_preview=not args.skip_research_preview_publish,
        decision_json=args.decision_json,
        apply_reviewer_configs=args.apply_reviewer_configs,
        post_attach_timeout_seconds=args.post_attach_timeout_seconds,
        post_attach_poll_seconds=args.post_attach_poll_seconds,
    )
    print(f"A3 ML demo readiness cycle status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
