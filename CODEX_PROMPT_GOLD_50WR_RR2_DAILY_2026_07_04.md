# CODEX PROMPT — NEW GOLD GOAL: 50%+ WIN RATE, 2:1 WIN/LOSS, DAILY ACTIVITY
Owner: Ali | Date: 2026-07-04 | Supersedes the Forex-diversification goal as PRIMARY focus.
The Forex lane drops to background/watchlist maintenance only. The four-family research plan
(NEW_STRATEGY_FAMILIES_RESEARCH_PLAN_2026_07_04.md) stays approved but is re-scoped to serve this goal.

## THE GOAL (owner's target, verbatim requirements)
Find a GOLD (XAUUSD) strategy where:
1. **Win/loss money ratio is 1:2** — when we lose, we lose about $X; when we win, we win about $2X.
   Measured as: realized average winning trade / realized average losing trade >= 2.0, in account
   currency, AFTER all exits/management, at SIGNAL level (one decision = one signal, even if it uses
   multiple tickets).
2. **Win rate 50% or above** — measured at signal level, same definition.
3. **At least one trade every trading day** — measured as: percentage of market days with >= 1 signal.
   Target: 100%. Report the achieved number honestly; 90%+ with the other two goals met is a success
   worth showing the owner.

## HONESTY BOX (read before starting, re-read weekly)
- 50% WR at 2:1 payoff = +0.50R per trade expectancy. Our best fully validated book earns +0.23R.
  This target is roughly 2x beyond anything proven in this repo. That is the assignment, not a
  reason to fake it — but it means:
- **No metric games.** Signal-level WR only (never ticket-level). Realized W/L only (never nominal
  RR). No outcome-aware guards (the leaky-guard incident must never repeat). No survivorship-hidden
  sweeps — every variant tried gets logged in a ledger with its result.
- **Report the frontier, not just hits.** Each report must show the 3–5 best candidates as a table of
  (WR, realized W/L, % days active, PF, net, DD) so the owner sees what each corner of his goal costs.
  A candidate at 48% / 1.9x / 85% days is a near-miss the owner wants to SEE, not a failure to hide.
- If after the full plan below the intersection provably does not exist on gold at our costs, say so
  with the frontier table as evidence. That is an acceptable outcome. Quietly delivering a fragile
  overfit that "hits" all three numbers is not.

## WHERE TO START (ordered — do not reorder without reviewer sign-off)

### Step 1 — Shape the split-entry family (1 week; highest probability)
The split-entry BE-on-TP1 machinery is already exact-MT5-validated. Its knobs move us along exactly
the frontier this goal lives on:
- Unfixed variant measured: 45.3% signal WR, 1.86x realized W/L (already CLOSE to the goal).
- BE-fixed variant measured: 65.6% WR, 0.79x W/L (other corner).
PRE-REGISTER ONE grid, in writing, before any run: TP1 fraction {1/3, 1/2, 2/3} x runner target
{2.0R, 2.5R, 3.0R} x BE timing {on TP1 fill, at +1.0R, never} = 27 cells, declared once, run once on
2022–2026 in exact MT5, full ledger published. This is the family's single allowed refinement pass —
after this grid, the family is frozen forever. Judge every cell on the three goal metrics at signal
level. Daily coverage will need Step 3's portfolio layer — that is expected.

### Step 2 — Macro traffic-light gate on gold (2 weeks; the WR lever)
Phase 1 of the approved research plan, now aimed at THIS goal: a daily rates/dollar tailwind gate
(machinery already exists in forex-research, lookahead-safe joins proven) applied over the momentum
entry family. Purpose here: raising signal QUALITY is the only honest way to buy win-rate without
paying payoff for it. Design on 2016–2021 gold data (never yet used — free learning years), freeze,
one exam on 2022–2026. If green-light trades don't beat red-light trades clearly, the gate dies.

### Step 3 — Portfolio layer for daily coverage (1 week; the frequency lever)
One strategy will not trade every day — a portfolio of 2–4 non-overlapping ones can. Use the proven
causal composition machinery (priority stack + runtime signal-claim, dedupe, published kept/dropped
lists). Compose the best Step-1 cells + Step-2-gated entries + (if useful) existing validated books.
Goal metrics measured on the COMPOSED book. Exposure per signal must be quantified in dollars for
the owner exactly as done for the split-entry authorization.

### Step 4 — Only if Steps 1–3 miss: one genuinely new entry family (2 weeks max)
Design on 2016–2021 exclusively (e.g., mean-reversion at session extremes — the one style never
tried on gold, naturally high-WR). Freeze. One exam. One refinement pass maximum. Then stop and
present the frontier regardless of outcome.

## PROCESS RULES (all inherited from hard lessons — none are optional)
1. Headline claims come from EXACT MT5 Strategy Tester runs in the isolated root only. Python/offline
   replay is for triage and must be labeled DIAGNOSTIC.
2. Every composition step (dedupe, priority, daily guards) must be event-time causal, with kept/
   dropped trade lists published. Reviewer will reconstruct — the arithmetic must reproduce.
3. All specs/EAs hash-manifested; manifests regenerated on every edit (no stale-hash repeats).
4. Recency gate: any candidate must ALSO show its last-12-months stats standalone. Weak recent
   regime = disclosed prominently, not averaged away.
5. Costs: report per-trade net after spread, and a slippage stress line (+$0.10/+$0.30 per ticket).
   At RR-shaped books with runners, swap/overnight must be included for multi-day holds.
6. Runtime boundary unchanged: nothing attaches without frozen spec + owner sign-off + reviewer
   check. Existing demo lanes and their forward tests stay untouched. Kill-switch separation,
   dedicated magics, USD-vs-AED guard checks as per standing conditions.
7. agent.md + status pages updated per milestone; every report carries a variant-count ledger.
8. Independent reviewer (Claude) checkpoints: after Step 1 grid, after Step 2 exam, before any
   Step 3 composition is called a candidate, and before any spec is drafted.

## TIMEBOX AND KILL RULES
- Total budget: 6 weeks. Weekly one-page status to owner: frontier table + best candidate + blockers.
- A step that exhausts its budget without movement toward the goal metrics dies; do not extend
  silently. Parking-lot new ideas for the next cycle; do not branch mid-plan.
- Definition of done (any one): (a) a candidate meets all three goal metrics on the exam window and
  survives the standard robustness suite -> frozen forward-demo spec for owner approval; (b) the
  frontier table proves the intersection is unreachable at our costs -> owner decides which corner
  to relax; (c) budget exhausted -> same frontier presentation, owner decides.
