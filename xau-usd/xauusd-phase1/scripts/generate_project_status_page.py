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
ACCOUNT_EXAMPLE_STARTING_USD = 1000.0
ACCOUNT_EXAMPLE_RISK_PCT = 0.01
ACCOUNT_EXAMPLE_RISK_USD = ACCOUNT_EXAMPLE_STARTING_USD * ACCOUNT_EXAMPLE_RISK_PCT
ACCOUNT_EXAMPLE_COST_MODEL = "p95"


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
    account_example = _load_account_example(phase0_root, candidates)
    phase0_verdict = _read_markdown_status(phase0_reports / "PHASE0_VERDICT.md") or _phase0_verdict_status(
        phase0_reports / "PHASE0_VERDICT.md"
    )
    phase1_acceptance = _read_markdown_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md")
    phase2_readiness = _read_markdown_status(phase1_reports / "PHASE2_READINESS_REPORT.md")

    accepted_count = sum(1 for item in candidates if _candidate_status(item).startswith("ACCEPTED"))
    rejected_count = sum(1 for item in candidates if _candidate_status(item) == "REJECTED")
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
            account_example=account_example,
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
    account_example: dict[str, Any],
) -> str:
    status_fields = _mapping(summary.get("status"))
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(summary.get("soak"))
    would_signal = _mapping(summary.get("would_signal"))
    accepted = [item for item in candidates if _candidate_status(item).startswith("ACCEPTED")]
    pending = [item for item in candidates if _candidate_status(item) == "PROVISIONAL"]
    rejected = [item for item in candidates if _candidate_status(item) == "REJECTED"]
    next_items = _next_actions(phase1_status, phase2_status, measured_cost)
    soak_progress = _to_float(soak.get("progress_pct")) or 0.0
    cost_consumption = _to_float(fixed_notional.get("Cost %")) or 0.0

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
            '  <div class="app-shell">',
            _sidebar(
                generated_at=generated_at,
                repo_root=repo_root,
                phase0_status=phase0_status,
                phase1_status=phase1_status,
                phase2_status=phase2_status,
                measured_status=measured_cost.get("status", "UNKNOWN"),
            ),
            '    <main class="workspace">',
            '      <section class="command-bar">',
            "        <div>",
            '          <p class="eyebrow">XAUUSD Program</p>',
            "          <h1>Mission Control</h1>",
            f'          <p class="subtle">Generated { _esc(generated_at) } from local artifacts.</p>',
            "        </div>",
            '        <div class="status-stack">',
            _status_pill("Dry run", _cell(latest.get("dry_run"))),
            _status_pill("Permission", _cell(latest.get("trade_permission"))),
            _status_pill("Server", _cell(latest.get("server_time_status"))),
            "        </div>",
            "      </section>",
            "",
            _kpi_grid(
                accepted_count=len(accepted),
                pending_count=len(pending),
                rejected_count=len(rejected),
                soak=soak,
                soak_progress=soak_progress,
                fixed_notional=fixed_notional,
                cost_consumption=cost_consumption,
                measured_cost=measured_cost,
                runtime=runtime,
                would_signal=would_signal,
            ),
            "",
            '      <section class="grid focus-grid">',
            _panel(
                "Milestone Rail",
                _timeline(phase0_status, phase1_status, phase2_status, status_fields, measured_cost),
            ),
            _panel(
                "Runtime Boundary",
                _runtime_table(status_fields, latest, runtime, would_signal),
            ),
            _panel(
                "Cost Lens",
                _cost_table(fixed_notional, measured_cost),
            ),
            "      </section>",
            "",
            '      <section class="panel candidates-panel">',
            '        <div class="panel-head candidates-head">',
            "          <div>",
            "            <h2>EA Candidate Bench</h2>",
            f'            <span>{len(accepted)} accepted, {len(pending)} pending, {len(rejected)} rejected</span>',
            "          </div>",
            '          <div class="table-tools">',
            '            <input id="candidateSearch" type="search" placeholder="Search experts">',
            '            <div class="segments" role="group" aria-label="Candidate filter">',
            '              <button class="seg active" type="button" data-filter="all">All</button>',
            '              <button class="seg" type="button" data-filter="accepted">Accepted</button>',
            '              <button class="seg" type="button" data-filter="pending">Pending</button>',
            '              <button class="seg" type="button" data-filter="rejected">Rejected</button>',
            "            </div>",
            "          </div>",
            "        </div>",
            _candidate_table(candidates),
            "      </section>",
            "",
            '      <section class="panel account-panel">',
            '        <div class="panel-head candidates-head">',
            "          <div>",
            "            <h2>$1,000 Account Example</h2>",
            f'            <span>{_esc(_account_assumption_text())}</span>',
            "          </div>",
            "        </div>",
            _account_summary_table(account_example.get("summary", [])),
            "      </section>",
            "",
            '      <section class="panel monthly-panel">',
            '        <div class="panel-head candidates-head">',
            "          <div>",
            "            <h2>Monthly Returns Ledger</h2>",
            f'            <span>{_esc(_monthly_coverage_text(account_example))}</span>',
            "          </div>",
            '          <div class="table-tools">',
            _monthly_expert_options(account_example.get("summary", [])),
            '            <input id="monthlySearch" type="search" placeholder="Search month or EA">',
            "          </div>",
            "        </div>",
            _monthly_return_table(account_example.get("monthly_rows", [])),
            "      </section>",
            "",
            '      <section class="grid lower-grid">',
            _panel("Open Work", _list(next_items)),
            _panel("Primary Artifacts", _artifact_links()),
            "      </section>",
            "    </main>",
            "  </div>",
            _dashboard_script(),
            "</body>",
            "</html>",
        ]
    )


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f3f5f7;
  --surface: #ffffff;
  --surface-2: #f8fafc;
  --ink: #111827;
  --muted: #64748b;
  --line: #d8dee8;
  --line-strong: #b8c2d0;
  --green: #147a4a;
  --green-bg: #e7f6ee;
  --red: #b42318;
  --red-bg: #fff1ee;
  --amber: #936000;
  --amber-bg: #fff4cf;
  --blue: #2454a6;
  --blue-bg: #eaf2ff;
  --violet: #6842a0;
  --violet-bg: #f3edff;
  --teal: #0f766e;
  --teal-bg: #e6f6f4;
  --gray-bg: #eef2f7;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }
code { background: var(--gray-bg); padding: 2px 6px; border-radius: 5px; font-size: 12px; overflow-wrap: anywhere; }
.app-shell {
  display: grid;
  grid-template-columns: 276px minmax(0, 1fr);
  min-height: 100vh;
}
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 24px 18px;
  background: #172033;
  color: #edf2f7;
  border-right: 1px solid #0f172a;
  overflow-y: auto;
}
.brand { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #f8c14a;
  color: #172033;
  display: grid;
  place-items: center;
  font-weight: 900;
  letter-spacing: 0;
}
.brand-title { font-size: 14px; font-weight: 780; }
.brand-subtitle { color: #aab7ca; font-size: 12px; margin-top: 2px; }
.rail-label { color: #9fb0c6; font-size: 11px; font-weight: 760; text-transform: uppercase; margin: 22px 0 9px; }
.rail { display: grid; gap: 8px; }
.rail-item {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 9px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.055);
}
.rail-dot { width: 10px; height: 10px; border-radius: 50%; background: #94a3b8; }
.rail-item.pass .rail-dot { background: #32c48d; }
.rail-item.fail .rail-dot { background: #ff7b6e; }
.rail-item.pending .rail-dot, .rail-item.warn .rail-dot { background: #f6c453; }
.rail-name { font-size: 13px; font-weight: 680; overflow-wrap: anywhere; }
.rail-status { color: #d5deeb; font-size: 11px; font-weight: 760; }
.sidebar-path { color: #aab7ca; font-size: 12px; line-height: 1.55; overflow-wrap: anywhere; }
.workspace { min-width: 0; padding: 22px 24px 40px; }
.command-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 0 16px;
}
.eyebrow { margin: 0 0 5px; color: var(--teal); font-weight: 800; text-transform: uppercase; font-size: 12px; }
h1 { margin: 0; font-size: 32px; line-height: 1.05; letter-spacing: 0; }
h2 { margin: 0; font-size: 17px; letter-spacing: 0; }
.subtle { margin: 8px 0 0; color: var(--muted); line-height: 1.45; }
.status-stack { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.badge, .pill { display: inline-flex; align-items: center; min-height: 24px; padding: 4px 8px; border-radius: 999px; font-size: 11px; font-weight: 800; white-space: nowrap; }
.status-chip { display: inline-flex; gap: 6px; align-items: center; padding: 7px 9px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); font-size: 12px; font-weight: 760; }
.status-chip span:first-child { color: var(--muted); font-weight: 700; }
.pill.pass, .badge.pass { color: var(--green); background: var(--green-bg); }
.pill.fail, .badge.fail { color: var(--red); background: var(--red-bg); }
.pill.pending, .badge.pending, .pill.warn, .badge.warn { color: var(--amber); background: var(--amber-bg); }
.pill.unknown, .badge.unknown { color: var(--muted); background: var(--gray-bg); }
.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.kpi {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  min-height: 140px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.05);
}
.kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.kpi-label { color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.kpi-value { font-size: 28px; font-weight: 840; line-height: 1.05; overflow-wrap: anywhere; }
.kpi-note { color: var(--muted); font-size: 12px; line-height: 1.45; margin-top: 8px; }
.progress { height: 9px; border-radius: 999px; background: #e7ebf1; overflow: hidden; margin-top: 12px; }
.progress span { display: block; height: 100%; width: var(--value); border-radius: inherit; background: var(--blue); }
.progress.cost span { background: var(--amber); }
.grid { display: grid; gap: 12px; margin-bottom: 12px; }
.focus-grid { grid-template-columns: minmax(320px, 1.2fr) minmax(300px, 0.9fr) minmax(300px, 0.9fr); align-items: start; }
.lower-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 15px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.05);
}
.panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.panel-head span { color: var(--muted); font-size: 13px; }
.timeline { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.timeline li {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  padding: 9px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-2);
}
.step-num {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: var(--gray-bg);
  color: var(--muted);
  font-size: 11px;
  font-weight: 820;
}
.timeline .name { font-size: 13px; font-weight: 780; }
.timeline .detail { margin-top: 3px; color: var(--muted); font-size: 12px; line-height: 1.4; }
.candidates-panel { padding-bottom: 6px; }
.candidates-head { align-items: center; }
.table-tools { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }
input[type="search"], select {
  width: 220px;
  min-height: 34px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  padding: 7px 10px;
  color: var(--ink);
  background: #fff;
}
select { width: 260px; }
.segments { display: inline-flex; border: 1px solid var(--line-strong); border-radius: 8px; overflow: hidden; background: #fff; }
.seg {
  min-height: 34px;
  border: 0;
  border-right: 1px solid var(--line-strong);
  padding: 7px 11px;
  background: transparent;
  color: var(--muted);
  font-weight: 760;
  cursor: pointer;
}
.seg:last-child { border-right: 0; }
.seg.active { background: var(--blue-bg); color: var(--blue); }
.table-wrap { width: 100%; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 9px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0; background: #f8fafc; position: sticky; top: 0; z-index: 1; }
tr:last-child td { border-bottom: 0; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.money-positive { color: var(--green); font-weight: 760; }
.money-negative { color: var(--red); font-weight: 760; }
.money-flat { color: var(--muted); font-weight: 700; }
.monthly-panel .table-wrap { max-height: 620px; overflow: auto; }
.monthly-panel th { top: 0; }
.kv table td:first-child { color: var(--muted); font-weight: 700; width: 46%; }
.list { margin: 0; padding-left: 18px; line-height: 1.7; color: var(--ink); }
.muted { color: var(--muted); }
@media (max-width: 1280px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .focus-grid { grid-template-columns: 1fr; }
}
@media (max-width: 920px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; }
  .workspace { padding: 16px; }
  .lower-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .command-bar { flex-direction: column; }
  .status-stack { justify-content: flex-start; }
  .kpi-grid { grid-template-columns: 1fr; }
  .candidates-head { align-items: stretch; flex-direction: column; }
  .table-tools { justify-content: stretch; }
  input[type="search"], select, .segments { width: 100%; }
  .seg { flex: 1; }
  h1 { font-size: 26px; }
}
"""


def _sidebar(
    generated_at: str,
    repo_root: Path,
    phase0_status: str,
    phase1_status: str,
    phase2_status: str,
    measured_status: str,
) -> str:
    items = (
        ("Phase 0", phase0_status),
        ("Phase 1", phase1_status),
        ("Measured Cost", measured_status),
        ("Phase 2", phase2_status),
    )
    rail = "\n".join(
        [
            f'        <div class="rail-item {_status_class(status)}">'
            f'<span class="rail-dot"></span><span class="rail-name">{_esc(name)}</span>'
            f'<span class="rail-status">{_esc(status)}</span></div>'
            for name, status in items
        ]
    )
    return "\n".join(
        [
            '    <aside class="sidebar">',
            '      <div class="brand">',
            '        <div class="brand-mark">AT</div>',
            "        <div>",
            '          <div class="brand-title">Algo Trading System</div>',
            '          <div class="brand-subtitle">XAUUSD evidence dashboard</div>',
            "        </div>",
            "      </div>",
            '      <div class="rail-label">Status rail</div>',
            '      <div class="rail">',
            rail,
            "      </div>",
            '      <div class="rail-label">Updated</div>',
            f'      <div class="sidebar-path">{_esc(generated_at)}</div>',
            '      <div class="rail-label">Local file</div>',
            f'      <div class="sidebar-path">{_esc(str(repo_root / DEFAULT_OUTPUT))}</div>',
            "    </aside>",
        ]
    )


def _status_pill(label: str, value: str) -> str:
    display = value if value else "n/a"
    class_value = display
    normalized = display.strip().lower()
    if label == "Dry run" and normalized == "true":
        class_value = "PASS"
    elif label == "Permission" and normalized == "false":
        class_value = "PASS"
    elif label == "Server" and display.upper() == "CLOCK_OK":
        class_value = "PASS"
    return (
        f'<div class="status-chip"><span>{_esc(label)}</span>'
        f'<strong class="{_status_class(class_value)} pill">{_esc(display)}</strong></div>'
    )


def _kpi_grid(
    accepted_count: int,
    pending_count: int,
    rejected_count: int,
    soak: dict[str, Any],
    soak_progress: float,
    fixed_notional: dict[str, str],
    cost_consumption: float,
    measured_cost: dict[str, str],
    runtime: dict[str, Any],
    would_signal: dict[str, Any],
) -> str:
    return "\n".join(
        [
            '      <section class="kpi-grid">',
            _kpi(
                label="Soak progress",
                value=f"{_fmt_float(soak_progress)}%",
                status="PASS" if soak_progress >= 100.0 else "PENDING",
                note=f"{_cell(soak.get('observed_days'))} of {_cell(soak.get('required_days'))} trading days",
                bar=_progress_bar(soak_progress, "soak"),
            ),
            _kpi(
                label="Modeled cost load",
                value=f"{_fmt_float(cost_consumption)}%",
                status=fixed_notional.get("Flag", ""),
                note=f"Net { _r_value(fixed_notional.get('Avg R')) }, cost { _r_value(fixed_notional.get('Cost R')) }",
                bar=_progress_bar(cost_consumption, "cost"),
            ),
            _kpi(
                label="EA bench",
                value=f"{accepted_count} / {pending_count} / {rejected_count}",
                status="ACTIVE",
                note="accepted / pending / rejected candidates",
                bar="",
            ),
            _kpi(
                label="Runtime evidence",
                value=_cell(runtime.get("decision_rows")),
                status="PASS",
                note=f"{_cell(would_signal.get('clusters'))} would-signal clusters",
                bar="",
            ),
            "      </section>",
        ]
    )


def _kpi(label: str, value: str, status: str, note: str, bar: str) -> str:
    return "\n".join(
        [
            '        <article class="kpi">',
            '          <div class="kpi-top">',
            f'            <div class="kpi-label">{_esc(label)}</div>',
            f'            <span class="pill {_status_class(status)}">{_esc(status or "tracked")}</span>',
            "          </div>",
            f'          <div class="kpi-value">{_esc(value)}</div>',
            f'          <div class="kpi-note">{_esc(note)}</div>',
            f"          {bar}" if bar else "",
            "        </article>",
        ]
    )


def _progress_bar(value: float, kind: str) -> str:
    bounded = max(0.0, min(100.0, value))
    return f'<div class="progress {kind}"><span style="--value: {bounded:.2f}%"></span></div>'


def _timeline(
    phase0_status: str,
    phase1_status: str,
    phase2_status: str,
    status_fields: dict[str, Any],
    measured_cost: dict[str, str],
) -> str:
    rows = [
        ("Phase 0", phase0_status, "Research closure and final expert verdict"),
        ("Validation D1-D4", "PASS", "CPCV, Reality Check, holdout, reproduction"),
        ("Dry-run shell", _cell(status_fields.get("runtime_health")), "MT5 runtime boundary and observer telemetry"),
        ("Five-day soak", phase1_status, "Wall-clock dry-run evidence"),
        ("Measured cost", measured_cost.get("status", "UNKNOWN"), "Passive spread evidence and revalidation"),
        ("Phase 2 paper", phase2_status, "Paper-mode readiness and owner approval"),
    ]
    items = []
    for index, (name, status, detail) in enumerate(rows, start=1):
        items.append(
            "\n".join(
                [
                    f'        <li class="{_status_class(status)}">',
                    f'          <span class="step-num">{index}</span>',
                    "          <div>",
                    f'            <div class="name">{_esc(name)}</div>',
                    f'            <div class="detail">{_esc(detail)}</div>',
                    "          </div>",
                    f'          <span class="pill {_status_class(status)}">{_esc(status)}</span>',
                    "        </li>",
                ]
            )
        )
    return '<ol class="timeline">\n' + "\n".join(items) + "\n      </ol>"


def _dashboard_script() -> str:
    return """
  <script>
    const search = document.getElementById("candidateSearch");
    const monthlySearch = document.getElementById("monthlySearch");
    const monthlyExpertFilter = document.getElementById("monthlyExpertFilter");
    const buttons = Array.from(document.querySelectorAll("[data-filter]"));
    const rows = Array.from(document.querySelectorAll("[data-candidate-row]"));
    const monthlyRows = Array.from(document.querySelectorAll("[data-monthly-row]"));
    let activeFilter = "all";

    function applyCandidateFilter() {
      const query = (search?.value || "").toLowerCase().trim();
      rows.forEach((row) => {
        const status = row.dataset.status;
        const haystack = row.dataset.search || "";
        const statusMatch = activeFilter === "all" || status === activeFilter;
        const queryMatch = !query || haystack.includes(query);
        row.hidden = !(statusMatch && queryMatch);
      });
    }

    function applyMonthlyFilter() {
      const query = (monthlySearch?.value || "").toLowerCase().trim();
      const selectedExpert = monthlyExpertFilter?.value || "all";
      monthlyRows.forEach((row) => {
        const haystack = row.dataset.search || "";
        const expertMatch = selectedExpert === "all" || row.dataset.expert === selectedExpert;
        const queryMatch = !query || haystack.includes(query);
        row.hidden = !(expertMatch && queryMatch);
      });
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        buttons.forEach((item) => item.classList.toggle("active", item === button));
        applyCandidateFilter();
      });
    });

    search?.addEventListener("input", applyCandidateFilter);
    monthlySearch?.addEventListener("input", applyMonthlyFilter);
    monthlyExpertFilter?.addEventListener("change", applyMonthlyFilter);
  </script>
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
        ("Phase 0 research closure", phase0_status, "breakout_retest approved; same-family provisional candidates remain Gate 9 pending"),
        ("D1 CPCV", "PASS", "Closed in Phase 0 independent validation"),
        ("D2 Reality Check / SPA", "PASS", "Full-universe rerun remains PASS after latest provisional candidate"),
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
        key=lambda item: (_candidate_sort_rank(item), item.get("candidate", "")),
    )
    columns = ("Expert", "Status", "Diagnosis", "Cells", "PF Cells", "Trades", "Median Cell Trades", "Failed Gates")
    header = "".join(f"<th>{_esc(column)}</th>" for column in columns)
    body = []
    for item in sorted_candidates:
        status = _candidate_status(item)
        filter_status = _candidate_filter_status(status)
        search_text = " ".join(
            (
                item.get("candidate", ""),
                status,
                item.get("frequency_bias_diagnosis", ""),
                item.get("failed_gates", ""),
            )
        ).lower()
        cells = [
            _esc(item.get("candidate", "")),
            f'<span class="pill {_status_class(status)}">{_esc(status)}</span>',
            _esc(item.get("frequency_bias_diagnosis", "")),
            _esc(item.get("complete_cells", "")),
            _esc(item.get("pf_passing_cells", "")),
            _esc(item.get("total_trades", "")),
            _esc(item.get("median_cell_trades", "")),
            _esc(item.get("failed_gates", "")),
        ]
        numeric_indexes = {3, 4, 5, 6}
        table_cells = []
        for index, value in enumerate(cells):
            cell_class = ' class="num"' if index in numeric_indexes else ""
            table_cells.append(f"<td{cell_class}>{value}</td>")
        tds = "".join(table_cells)
        body.append(
            f'<tr data-candidate-row data-status="{filter_status}" data-search="{_esc(search_text)}">{tds}</tr>'
        )
    return '<div class="table-wrap candidate-wrap"><table><thead><tr>' + header + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _candidate_status(item: dict[str, str]) -> str:
    if item.get("decision_scope") == "APPROVED_OR_ACTIVE":
        if item.get("candidate") == "swing_breakout_retest_v0":
            return "ACCEPTED SAME-FAMILY"
        return "ACCEPTED"
    if (
        item.get("frequency_bias_diagnosis") == "NON_MATRIX_REJECTION_OR_PENDING"
        and item.get("failed_gates", "").strip().lower() == "none"
    ):
        return "PROVISIONAL"
    return "REJECTED"


def _candidate_filter_status(status: str) -> str:
    if status.startswith("ACCEPTED"):
        return "accepted"
    if status == "PROVISIONAL":
        return "pending"
    return "rejected"


def _candidate_sort_rank(item: dict[str, str]) -> int:
    status = _candidate_status(item)
    if status.startswith("ACCEPTED"):
        return 0
    if status == "PROVISIONAL":
        return 1
    return 2


def _account_summary_table(rows: list[dict[str, Any]]) -> str:
    columns = (
        "Expert",
        "Status",
        "Trades",
        "Win Rate",
        "Total PnL",
        "Total Return",
        "Avg Month",
        "Worst Month",
        "Best Month",
        "Positive Months",
    )
    header = "".join(f"<th>{_esc(column)}</th>" for column in columns)
    body = []
    for row in rows:
        status = _cell(row.get("status"))
        total_pnl = float(row.get("total_pnl_usd", 0.0))
        avg_month = float(row.get("avg_monthly_pnl_usd", 0.0))
        worst_month = float(row.get("worst_month_pnl_usd", 0.0))
        best_month = float(row.get("best_month_pnl_usd", 0.0))
        values = [
            _esc(row.get("expert", "")),
            f'<span class="pill {_status_class(status)}">{_esc(status)}</span>',
            _esc(row.get("trades", 0)),
            _esc(_format_pct(row.get("win_rate_pct"))),
            _money_cell(total_pnl, include_sign=True),
            _money_cell(float(row.get("total_return_pct", 0.0)), suffix="%", include_sign=True),
            _money_cell(avg_month, include_sign=True),
            _money_cell(worst_month, include_sign=True),
            _money_cell(best_month, include_sign=True),
            _esc(f"{row.get('positive_months', 0)} / {row.get('total_months', 0)}"),
        ]
        numeric_indexes = {2, 3, 4, 5, 6, 7, 8, 9}
        cells = []
        for index, value in enumerate(values):
            klass = ' class="num"' if index in numeric_indexes else ""
            cells.append(f"<td{klass}>{value}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    if not body:
        body.append(f'<tr><td colspan="{len(columns)}" class="muted">No p95 trade ledgers found.</td></tr>')
    return '<div class="table-wrap"><table><thead><tr>' + header + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _monthly_return_table(rows: list[dict[str, Any]]) -> str:
    columns = ("Month", "Expert", "Status", "Trades", "PnL", "Return")
    header = "".join(f"<th>{_esc(column)}</th>" for column in columns)
    body = []
    for row in rows:
        expert = _cell(row.get("expert"))
        status = _cell(row.get("status"))
        pnl = float(row.get("pnl_usd", 0.0))
        return_pct = float(row.get("return_pct", 0.0))
        search_text = " ".join((_cell(row.get("month")), expert, status)).lower()
        values = [
            _esc(row.get("month", "")),
            _esc(expert),
            f'<span class="pill {_status_class(status)}">{_esc(status)}</span>',
            _esc(row.get("trades", 0)),
            _money_cell(pnl, include_sign=True),
            _money_cell(return_pct, suffix="%", include_sign=True),
        ]
        numeric_indexes = {3, 4, 5}
        cells = []
        for index, value in enumerate(values):
            klass = ' class="num"' if index in numeric_indexes else ""
            cells.append(f"<td{klass}>{value}</td>")
        body.append(
            f'<tr data-monthly-row data-expert="{_esc(expert)}" data-search="{_esc(search_text)}">'
            + "".join(cells)
            + "</tr>"
        )
    if not body:
        body.append(f'<tr><td colspan="{len(columns)}" class="muted">No monthly rows available.</td></tr>')
    return '<div class="table-wrap"><table><thead><tr>' + header + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _monthly_expert_options(rows: list[dict[str, Any]]) -> str:
    options = ['<option value="all">All EAs</option>']
    for row in rows:
        expert = _cell(row.get("expert"))
        if not expert or expert == "n/a":
            continue
        status = _cell(row.get("status"))
        label = f"{expert} ({status})"
        options.append(f'<option value="{_esc(expert)}">{_esc(label)}</option>')
    return (
        '<select id="monthlyExpertFilter" aria-label="Filter monthly returns by EA">'
        + "".join(options)
        + "</select>"
    )


def _account_assumption_text() -> str:
    return (
        f"{ACCOUNT_EXAMPLE_COST_MODEL.upper()} matrix ledgers; "
        f"${ACCOUNT_EXAMPLE_STARTING_USD:,.0f} starting account; "
        f"{ACCOUNT_EXAMPLE_RISK_PCT:.0%} fixed risk per trade (${ACCOUNT_EXAMPLE_RISK_USD:,.0f}/R); no compounding."
    )


def _monthly_coverage_text(account_example: dict[str, Any]) -> str:
    start = account_example.get("start_month") or "n/a"
    end = account_example.get("end_month") or "n/a"
    total = account_example.get("total_months") or 0
    return f"{total} months shown from {start} to {end}; filter by month or EA name."


def _load_account_example(phase0_root: Path, candidates: list[dict[str, str]]) -> dict[str, Any]:
    matrix_root = phase0_root / "outputs" / "matrix_results"
    candidate_items = sorted(
        candidates,
        key=lambda item: (_candidate_sort_rank(item), item.get("candidate", "")),
    )
    monthly_by_expert: dict[str, dict[str, dict[str, float]]] = {}
    summary_base: dict[str, dict[str, Any]] = {}
    months: set[str] = set()

    for item in candidate_items:
        expert = item.get("candidate", "")
        if not expert:
            continue
        status = _candidate_status(item)
        buckets: dict[str, dict[str, float]] = {}
        trades = 0
        wins = 0
        total_r = 0.0
        for path in sorted((matrix_root / expert).glob(f"*_{ACCOUNT_EXAMPLE_COST_MODEL}_trades.csv")):
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    month = _month_key(row.get("exit_time_utc") or row.get("entry_time_utc"))
                    if not month:
                        continue
                    r_multiple = _to_float(row.get("r_multiple")) or 0.0
                    pnl = r_multiple * ACCOUNT_EXAMPLE_RISK_USD
                    bucket = buckets.setdefault(month, {"pnl_usd": 0.0, "trades": 0.0})
                    bucket["pnl_usd"] += pnl
                    bucket["trades"] += 1
                    months.add(month)
                    trades += 1
                    wins += 1 if r_multiple > 0 else 0
                    total_r += r_multiple
        monthly_by_expert[expert] = buckets
        summary_base[expert] = {
            "expert": expert,
            "status": status,
            "trades": trades,
            "wins": wins,
            "total_r": total_r,
        }

    ordered_months = sorted(months)
    total_months = len(ordered_months)
    summary_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    for item in candidate_items:
        expert = item.get("candidate", "")
        if not expert:
            continue
        base = summary_base.get(expert, {"expert": expert, "status": "UNKNOWN", "trades": 0, "wins": 0, "total_r": 0.0})
        buckets = monthly_by_expert.get(expert, {})
        month_pnls = [float(buckets.get(month, {}).get("pnl_usd", 0.0)) for month in ordered_months]
        total_pnl = sum(month_pnls)
        positive_months = sum(1 for value in month_pnls if value > 0)
        active_months = sum(1 for month in ordered_months if buckets.get(month, {}).get("trades", 0.0) > 0)
        summary_rows.append(
            {
                "expert": expert,
                "status": base["status"],
                "trades": int(base["trades"]),
                "win_rate_pct": (float(base["wins"]) / float(base["trades"]) * 100.0) if base["trades"] else 0.0,
                "total_pnl_usd": total_pnl,
                "total_return_pct": (total_pnl / ACCOUNT_EXAMPLE_STARTING_USD) * 100.0,
                "avg_monthly_pnl_usd": total_pnl / total_months if total_months else 0.0,
                "avg_monthly_return_pct": (total_pnl / total_months / ACCOUNT_EXAMPLE_STARTING_USD * 100.0)
                if total_months
                else 0.0,
                "worst_month_pnl_usd": min(month_pnls) if month_pnls else 0.0,
                "best_month_pnl_usd": max(month_pnls) if month_pnls else 0.0,
                "positive_months": positive_months,
                "active_months": active_months,
                "total_months": total_months,
            }
        )
        for month in reversed(ordered_months):
            bucket = buckets.get(month, {"pnl_usd": 0.0, "trades": 0.0})
            pnl = float(bucket.get("pnl_usd", 0.0))
            monthly_rows.append(
                {
                    "month": month,
                    "expert": expert,
                    "status": base["status"],
                    "trades": int(bucket.get("trades", 0.0)),
                    "pnl_usd": pnl,
                    "return_pct": (pnl / ACCOUNT_EXAMPLE_STARTING_USD) * 100.0,
                }
            )

    return {
        "summary": summary_rows,
        "monthly_rows": monthly_rows,
        "start_month": ordered_months[0] if ordered_months else "",
        "end_month": ordered_months[-1] if ordered_months else "",
        "total_months": total_months,
    }


def _month_key(value: str | None) -> str:
    if not value:
        return ""
    return value.strip()[:7]


def _money_cell(value: float, suffix: str = "", include_sign: bool = False) -> str:
    klass = _money_class(value)
    if suffix:
        sign = "+" if include_sign and value > 0 else ""
        formatted = f"{sign}{value:,.2f}{suffix}"
    elif value < 0:
        formatted = f"-${abs(value):,.2f}"
    else:
        sign = "+" if include_sign and value > 0 else ""
        formatted = f"{sign}${value:,.2f}"
    return f'<span class="{klass}">{_esc(formatted)}</span>'


def _money_class(value: float) -> str:
    if value > 0.000001:
        return "money-positive"
    if value < -0.000001:
        return "money-negative"
    return "money-flat"


def _format_pct(value: Any) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return "n/a"
    return f"{numeric:.2f}%"


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
    return '<div class="kv">' + _html_table(table_rows, ("Metric", "Value")) + "</div>"


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
    if "PASS" in upper or "ACCEPTED" in upper or "ACTIVE" in upper or "GREEN" in upper:
        return "pass"
    if "FAIL" in upper or "REJECTED" in upper or "BLOCKED" in upper:
        return "fail"
    if "PENDING" in upper or "PROVISIONAL" in upper or "WARN" in upper or "%" in upper or "ORANGE" in upper or "YELLOW" in upper:
        return "pending"
    return "unknown"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return None


def _fmt_float(value: float) -> str:
    if abs(value - round(value)) < 0.005:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


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
