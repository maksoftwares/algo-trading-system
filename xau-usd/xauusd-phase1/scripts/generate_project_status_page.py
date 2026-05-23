from __future__ import annotations

import argparse
import csv
import html
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path("status.html")


@dataclass(frozen=True)
class StatusPageOutput:
    output_path: Path
    candidate_count: int
    accepted_count: int
    rejected_count: int
    phase1_status: str
    phase2_status: str


def generate_project_status_page(
    repo_root: Path,
    output_path: Path | None = None,
) -> StatusPageOutput:
    repo_root = repo_root.resolve()
    if output_path is None:
        output_path = repo_root / DEFAULT_OUTPUT
    output_path = output_path.resolve()

    phase0_root = repo_root / "xau-usd" / "xauusd-phase0"
    phase1_root = repo_root / "xau-usd" / "xauusd-phase1"
    phase0_reports = phase0_root / "outputs" / "reports"
    phase1_reports = phase1_root / "outputs" / "reports"

    phase1_summary = _read_json(phase1_reports / "PHASE1_STATUS_SUMMARY.json")
    fixed_notional = _parse_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    measured_cost = _parse_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    candidates = _read_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    phase0_verdict = _read_markdown_status(phase0_reports / "PHASE0_VERDICT.md") or _phase0_verdict_status(
        phase0_reports / "PHASE0_VERDICT.md"
    )
    phase1_acceptance = _read_markdown_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md")
    phase2_readiness = _read_markdown_status(phase1_reports / "PHASE2_READINESS_REPORT.md")

    accepted_count = sum(1 for item in candidates if item.get("decision_scope") == "APPROVED_OR_ACTIVE")
    rejected_count = sum(1 for item in candidates if item.get("decision_scope") != "APPROVED_OR_ACTIVE")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_html(
            repo_root=repo_root,
            generated_at=generated_at,
            phase0_status=phase0_verdict,
            phase1_status=phase1_acceptance or "UNKNOWN",
            phase2_status=phase2_readiness or "UNKNOWN",
            summary=phase1_summary,
            fixed_notional=fixed_notional,
            measured_cost=measured_cost,
            candidates=candidates,
        ),
        encoding="utf-8",
    )
    return StatusPageOutput(
        output_path=output_path,
        candidate_count=len(candidates),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        phase1_status=phase1_acceptance or "UNKNOWN",
        phase2_status=phase2_readiness or "UNKNOWN",
    )


def _render_html(
    repo_root: Path,
    generated_at: str,
    phase0_status: str,
    phase1_status: str,
    phase2_status: str,
    summary: dict[str, Any],
    fixed_notional: dict[str, str],
    measured_cost: dict[str, str],
    candidates: list[dict[str, str]],
) -> str:
    status_fields = _mapping(summary.get("status"))
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(summary.get("soak"))
    would_signal = _mapping(summary.get("would_signal"))
    accepted = [item for item in candidates if item.get("decision_scope") == "APPROVED_OR_ACTIVE"]
    rejected = [item for item in candidates if item.get("decision_scope") != "APPROVED_OR_ACTIVE"]
    next_items = _next_actions(phase1_status, phase2_status, measured_cost)

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>Algo Trading System Status</title>",
            "  <style>",
            _css(),
            "  </style>",
            "</head>",
            "<body>",
            '  <main class="shell">',
            '    <section class="topbar">',
            "      <div>",
            '        <p class="eyebrow">Algo Trading System</p>',
            "        <h1>Project Status Dashboard</h1>",
            f'        <p class="subtle">Generated { _esc(generated_at) } from local repo artifacts. Open this file any time: <code>{ _esc(str(repo_root / DEFAULT_OUTPUT)) }</code></p>',
            "      </div>",
            f'      <div class="badge { _status_class(phase2_status) }">Phase 2 { _esc(phase2_status) }</div>',
            "    </section>",
            "",
            '    <section class="cards">',
            _metric_card(
                "Phase 0",
                phase0_status,
                "Final research verdict",
                "xau-usd/xauusd-phase0/outputs/reports/PHASE0_VERDICT.md",
            ),
            _metric_card(
                "Phase 1",
                phase1_status,
                "Dry-run shell acceptance",
                "xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md",
            ),
            _metric_card(
                "Phase 2",
                phase2_status,
                "Paper-mode readiness",
                "xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md",
            ),
            _metric_card(
                "Soak",
                f"{_cell(soak.get('progress_pct'))}%",
                f"{_cell(soak.get('observed_days'))} of {_cell(soak.get('required_days'))} days",
                "xau-usd/xauusd-phase1/outputs/reports/PHASE1_STATUS_SUMMARY.json",
            ),
            _metric_card(
                "Candidates",
                f"{len(accepted)} accepted / {len(rejected)} rejected",
                "Includes same-family approved candidates",
                "xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv",
            ),
            _metric_card(
                "Cost Model",
                measured_cost.get("status", "UNKNOWN"),
                f"{measured_cost.get('observed_rows', 'n/a')} rows, {measured_cost.get('observed_days', 'n/a')} observed days",
                "xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md",
            ),
            "    </section>",
            "",
            '    <section class="grid two">',
            _panel(
                "Runtime",
                _runtime_table(status_fields, latest, runtime, would_signal),
            ),
            _panel(
                "Breakout-Retest Cost Baseline",
                _cost_table(fixed_notional, measured_cost),
            ),
            "    </section>",
            "",
            '    <section class="panel">',
            "      <div class=\"panel-head\">",
            "        <h2>Milestones</h2>",
            "        <span>Current go/no-go surface</span>",
            "      </div>",
            _milestone_table(phase0_status, phase1_status, phase2_status, status_fields, measured_cost),
            "    </section>",
            "",
            '    <section class="panel">',
            "      <div class=\"panel-head\">",
            "        <h2>Expert Candidates</h2>",
            "        <span>Accepted, rejected, and why</span>",
            "      </div>",
            _candidate_table(candidates),
            "    </section>",
            "",
            '    <section class="grid two">',
            _panel("Open Work", _list(next_items)),
            _panel("Primary Artifacts", _artifact_links()),
            "    </section>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f6f8fb;
  --panel: #ffffff;
  --text: #1d2433;
  --muted: #657084;
  --line: #d9e1ec;
  --green: #18794e;
  --green-bg: #e9f7ef;
  --red: #b42318;
  --red-bg: #fff0ed;
  --yellow: #946200;
  --yellow-bg: #fff7db;
  --blue: #2454a6;
  --blue-bg: #edf4ff;
  --gray-bg: #eef2f7;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); }
.shell { width: min(1480px, calc(100vw - 32px)); margin: 0 auto; padding: 28px 0 44px; }
.topbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
.eyebrow { margin: 0 0 4px; color: var(--blue); font-weight: 700; text-transform: uppercase; font-size: 12px; }
h1 { margin: 0; font-size: 34px; line-height: 1.1; letter-spacing: 0; }
h2 { margin: 0; font-size: 18px; letter-spacing: 0; }
.subtle { margin: 10px 0 0; color: var(--muted); line-height: 1.5; }
code { background: var(--gray-bg); padding: 2px 6px; border-radius: 5px; font-size: 13px; overflow-wrap: anywhere; }
.cards { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.card, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 1px 2px rgba(22, 34, 51, 0.04); }
.card { padding: 14px; min-height: 126px; display: flex; flex-direction: column; justify-content: space-between; }
.label { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }
.value { font-size: 22px; font-weight: 760; margin: 10px 0 6px; overflow-wrap: anywhere; }
.note { color: var(--muted); font-size: 13px; line-height: 1.35; }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }
.badge, .pill { display: inline-flex; align-items: center; min-height: 28px; padding: 5px 9px; border-radius: 999px; font-size: 12px; font-weight: 760; white-space: nowrap; }
.pass { color: var(--green); background: var(--green-bg); }
.fail { color: var(--red); background: var(--red-bg); }
.pending, .warn { color: var(--yellow); background: var(--yellow-bg); }
.unknown { color: var(--muted); background: var(--gray-bg); }
.grid { display: grid; gap: 12px; margin-bottom: 12px; }
.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.panel { padding: 16px; overflow: hidden; }
.panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.panel-head span { color: var(--muted); font-size: 13px; }
.table-wrap { width: 100%; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 9px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0; background: #fafcff; }
tr:last-child td { border-bottom: 0; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.tight td { padding: 8px 9px; }
.list { margin: 0; padding-left: 18px; line-height: 1.7; color: var(--text); }
.muted { color: var(--muted); }
@media (max-width: 1150px) {
  .cards { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .two { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .shell { width: min(100vw - 20px, 1480px); padding-top: 18px; }
  .topbar { flex-direction: column; }
  .cards { grid-template-columns: 1fr; }
  h1 { font-size: 28px; }
  .value { font-size: 20px; }
}
"""


def _metric_card(title: str, value: str, note: str, href: str) -> str:
    return "\n".join(
        [
            '      <article class="card">',
            f'        <div class="label">{_esc(title)}</div>',
            f'        <div class="value"><span class="pill {_status_class(value)}">{_esc(value)}</span></div>',
            f'        <div class="note">{_esc(note)}<br><a href="{_esc(_link(href))}">Open artifact</a></div>',
            "      </article>",
        ]
    )


def _panel(title: str, body: str) -> str:
    return "\n".join(
        [
            '      <section class="panel">',
            '        <div class="panel-head">',
            f"          <h2>{_esc(title)}</h2>",
            "        </div>",
            body,
            "      </section>",
        ]
    )


def _runtime_table(
    status_fields: dict[str, Any],
    latest: dict[str, Any],
    runtime: dict[str, Any],
    would_signal: dict[str, Any],
) -> str:
    rows = [
        ("Decision rows", _cell(runtime.get("decision_rows"))),
        ("Latest bar", _cell(latest.get("bar_time"))),
        ("Dry run", _cell(latest.get("dry_run"))),
        ("Trade permission", _cell(latest.get("trade_permission"))),
        ("Server time", _cell(latest.get("server_time_status"))),
        ("Risk state", _cell(latest.get("risk_state"))),
        ("Block reason", _cell(latest.get("block_reason"))),
        ("Log verification", _cell(status_fields.get("log_verification"))),
        ("Runtime health", _cell(status_fields.get("runtime_health"))),
        ("Soak analysis", _cell(status_fields.get("soak_analysis"))),
        ("Would-signal clusters", _cell(would_signal.get("clusters"))),
    ]
    return _key_value_table(rows)


def _cost_table(fixed: dict[str, str], measured: dict[str, str]) -> str:
    rows = [
        ("Trades", fixed.get("Trades", "n/a")),
        ("Win rate", _pct(fixed.get("Win %"))),
        ("Profit factor", fixed.get("PF", "n/a")),
        ("Net expectancy", _r_value(fixed.get("Avg R"))),
        ("Gross expectancy", _r_value(fixed.get("Gross R"))),
        ("Mean modeled cost", _r_value(fixed.get("Cost R"))),
        ("Cost edge consumption", _pct(fixed.get("Cost %"))),
        ("Cost flag", fixed.get("Flag", "n/a")),
        ("Measured cost status", measured.get("status", "n/a")),
        ("Measured rows/days", f"{measured.get('observed_rows', 'n/a')} rows / {measured.get('observed_days', 'n/a')} days"),
    ]
    return _key_value_table(rows)


def _milestone_table(
    phase0_status: str,
    phase1_status: str,
    phase2_status: str,
    status_fields: dict[str, Any],
    measured_cost: dict[str, str],
) -> str:
    rows = [
        ("Phase 0 research closure", phase0_status, "breakout_retest approved; trend_pullback and range_mr rejected"),
        ("D1 CPCV", "PASS", "Closed in Phase 0 independent validation"),
        ("D2 Reality Check / SPA", "PASS", "Full-universe Review #3 rerun closed"),
        ("D3 True holdout audit", "PASS", "Holdout remains locked"),
        ("D4 Independent reproduction", "PASS", "Independent reproduction within tolerance"),
        ("Phase 1 dry-run shell", _cell(status_fields.get("runtime_health")), "MT5 telemetry and dry-run boundaries"),
        ("Phase 1 five-day soak", phase1_status, "Wall-clock evidence still accumulating"),
        ("Measured cost model", measured_cost.get("status", "UNKNOWN"), "Needs required observed days before Phase 2"),
        ("Phase 2 paper readiness", phase2_status, "Paper-mode implementation not authorized until all gates pass"),
    ]
    table_rows = [
        {
            "Milestone": name,
            "Status": f'<span class="pill {_status_class(status)}">{_esc(status)}</span>',
            "Detail": _esc(detail),
        }
        for name, status, detail in rows
    ]
    return _html_table(table_rows, ("Milestone", "Status", "Detail"), raw_columns={"Status"})


def _candidate_table(candidates: list[dict[str, str]]) -> str:
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (0 if item.get("decision_scope") == "APPROVED_OR_ACTIVE" else 1, item.get("candidate", "")),
    )
    rows = []
    for item in sorted_candidates:
        status = "ACCEPTED" if item.get("decision_scope") == "APPROVED_OR_ACTIVE" else "REJECTED"
        if item.get("candidate") == "swing_breakout_retest_v0":
            status = "ACCEPTED SAME-FAMILY"
        rows.append(
            {
                "Expert": _esc(item.get("candidate", "")),
                "Status": f'<span class="pill {_status_class(status)}">{_esc(status)}</span>',
                "Diagnosis": _esc(item.get("frequency_bias_diagnosis", "")),
                "Cells": _esc(item.get("complete_cells", "")),
                "PF Cells": _esc(item.get("pf_passing_cells", "")),
                "Trades": _esc(item.get("total_trades", "")),
                "Median Cell Trades": _esc(item.get("median_cell_trades", "")),
                "Failed Gates": _esc(item.get("failed_gates", "")),
            }
        )
    return _html_table(
        rows,
        ("Expert", "Status", "Diagnosis", "Cells", "PF Cells", "Trades", "Median Cell Trades", "Failed Gates"),
        raw_columns={"Status"},
        numeric_columns={"Cells", "PF Cells", "Trades", "Median Cell Trades"},
    )


def _artifact_links() -> str:
    links = [
        ("Agent handoff", "agent.md"),
        ("Phase 0 verdict", "xau-usd/xauusd-phase0/outputs/reports/PHASE0_VERDICT.md"),
        ("Rejected candidate audit", "xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md"),
        ("Fixed-notional cost report", "xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md"),
        ("Measured cost model", "xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md"),
        ("Phase 1 status summary", "xau-usd/xauusd-phase1/outputs/reports/PHASE1_STATUS_SUMMARY.json"),
        ("Phase 1 acceptance", "xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md"),
        ("Phase 2 readiness", "xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md"),
    ]
    return _list([f'<a href="{_esc(_link(href))}">{_esc(label)}</a>' for label, href in links], raw=True)


def _next_actions(phase1_status: str, phase2_status: str, measured_cost: dict[str, str]) -> list[str]:
    items = []
    if phase1_status != "PASS":
        items.append("Let the five-trading-day Phase 1 soak continue; do not count weekend stale ticks as trading time.")
    if measured_cost.get("status") != "PASS":
        items.append("Keep the passive spread logger running until measured-cost coverage reaches the required observed days.")
    if phase2_status != "PASS":
        items.append("Keep Phase 2 in preparation mode only; no paper-mode implementation until readiness is PASS.")
    items.append("Continue independent candidate research without tuning rejected v0 hypotheses.")
    items.append("Keep dry-run and permission-lock safety audits green.")
    return items


def _key_value_table(rows: list[tuple[str, str]]) -> str:
    table_rows = [{"Metric": _esc(key), "Value": _esc(value)} for key, value in rows]
    return _html_table(table_rows, ("Metric", "Value"))


def _html_table(
    rows: list[dict[str, str]],
    columns: tuple[str, ...],
    raw_columns: set[str] | None = None,
    numeric_columns: set[str] | None = None,
) -> str:
    raw_columns = raw_columns or set()
    numeric_columns = numeric_columns or set()
    header = "".join(f"<th>{_esc(column)}</th>" for column in columns)
    body = []
    for row in rows:
        cells = []
        for column in columns:
            klass = ' class="num"' if column in numeric_columns else ""
            value = row.get(column, "")
            cells.append(f"<td{klass}>{value if column in raw_columns else _esc(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="table-wrap"><table><thead><tr>' + header + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _list(items: list[str], raw: bool = False) -> str:
    parts = [f"<li>{item if raw else _esc(item)}</li>" for item in items]
    return '<ul class="list">' + "".join(parts) + "</ul>"


def _read_candidate_audit(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_fixed_notional(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    columns: list[str] = []
    for line in text.splitlines():
        if line.startswith("| Cell |"):
            columns = [part.strip() for part in line.strip("|").split("|")]
        elif columns and line.startswith("| ALL |"):
            values = [part.strip() for part in line.strip("|").split("|")]
            return dict(zip(columns, values))
    return {}


def _parse_measured_cost(path: Path) -> dict[str, str]:
    result = {"status": _read_markdown_status(path) or "UNKNOWN"}
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    columns: list[str] = []
    for line in text.splitlines():
        if line.startswith("| Observed Rows |"):
            columns = [part.strip() for part in line.strip("|").split("|")]
        elif columns and line.startswith("| ") and not line.startswith("| ---"):
            values = [part.strip() for part in line.strip("|").split("|")]
            data = dict(zip(columns, values))
            result["observed_rows"] = data.get("Observed Rows", "")
            result["required_rows"] = data.get("Required Rows", "")
            result["observed_days"] = data.get("Observed Days", "")
            result["required_days"] = data.get("Required Days", "")
            return result
    return result


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("Overall status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _phase0_verdict_status(path: Path) -> str:
    if not path.exists():
        return "UNKNOWN"
    text = path.read_text(encoding="utf-8", errors="replace")
    return "PASS" if "| breakout_retest | PASS | PASS | PASS | PASS | PASS | PASS |" in text else "REVIEW"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _cell(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _link(path: str) -> str:
    return path.replace("\\", "/")


def _status_class(value: str) -> str:
    upper = value.upper()
    if "PASS" in upper or "ACCEPTED" in upper or "ACTIVE" in upper:
        return "pass"
    if "FAIL" in upper or "REJECTED" in upper or "BLOCKED" in upper:
        return "fail"
    if "PENDING" in upper or "WARN" in upper or "%" in upper or "ORANGE" in upper or "YELLOW" in upper:
        return "pending"
    return "unknown"


def _pct(value: str | None) -> str:
    if not value:
        return "n/a"
    return f"{value}%"


def _r_value(value: str | None) -> str:
    if not value:
        return "n/a"
    return f"{value}R"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the single-page project status dashboard.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    output = generate_project_status_page(args.repo_root, args.output)
    print(f"Project status page: {output.output_path}")
    print(f"Candidates: {output.candidate_count} ({output.accepted_count} accepted, {output.rejected_count} rejected)")
    print(f"Phase 1: {output.phase1_status}")
    print(f"Phase 2: {output.phase2_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
