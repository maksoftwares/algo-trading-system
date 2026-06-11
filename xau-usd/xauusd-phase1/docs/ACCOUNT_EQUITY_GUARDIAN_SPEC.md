# Account Equity Guardian — Stage A Spec (shadow observer)

Date: 2026-06-11
Source brief: `Downloads/CODEX_BRIEF_ACCOUNT_EQUITY_GUARDIAN_2026_06_09.md` (owner-commissioned)
Artifact: `mt5/Experts/AccountEquityGuardianShadow.mq5`
Status: STAGE_A_SOURCE_DELIVERED_NOT_ATTACHED (attachment to a chart is an owner action)

## What it is

A new, independent EA in the supervision family (not a member of any trading-strategy
family): it watches TOTAL account balance/equity/floating PnL on a timer and LOGS what the
pre-registered rules R1-R5 WOULD do. Stage A closes nothing by construction — the source
contains no OrderSend, PositionClose, PositionModify, or any trade-action call.

## Locked rule config v0 (changing after results = new locked vN)

| Rule | Trigger | Would-action | v0 parameter |
| --- | --- | --- | --- |
| R1 hard daily loss stop | day_realized + floating <= -limit | FLATTEN_ALL_AND_HALT | 150 AED |
| R2 peak-giveback trail | peak >= arm AND floating <= peak x (1-giveback) | FLATTEN_ALL | arm 150 AED, giveback 0.40 |
| R3 profit target | floating >= target | FLATTEN_ALL | 300 AED |
| R5 correlation cap | same-symbol same-direction positions > cap | WOULD_HAVE_BLOCKED_ENTRY | cap 2 |

R4 (close-losers-first variant of R2) is evaluated offline from the same log per the brief.
Log schema (CSV in MQL5\Files): timestamp, balance, equity, total_floating,
session_peak_floating, day_realized, open_positions, max_same_dir_count, rule_fired,
would_action, hypothetical_locked_pnl_at_trigger.

## Safety

Demo-only guard (refuses non-demo unless explicitly overridden), optional account-login
allowlist, kill-switch file (`GUARDIAN_SHADOW_KILL.txt` in MQL5\Files pauses logging),
observer-only Stage A. Stage B (armed closing) remains a separate, owner-authorized,
gated follow-up per the brief; nothing here authorizes it. No existing EA, chart, preset,
or profile is touched by this delivery.

## Honest scope note

This EA supervises and protects; it is not a trading-edge EA. The second trading-edge EA
search is data-blocked per `xauusd-phase0/docs/CANDIDATE_RESEARCH_BACKLOG.md` (fourteen
locked rejections, 2026-06-10/11); the Guardian addresses the owner's other standing
request (the +300-to--100 giveback pain) and produces the shadow evidence the brief's
Stage-A/Stage-B decision requires.
