# Review request: V60 capital gate, resume deadlock, and four proposed fixes

Two tasks, in order. **Do not start the second until the first is done.**

1. **Review the diagnosis and the simulator.** Decide whether the findings are
   real. Say so plainly either way — confirming a correct diagnosis is as useful
   as breaking a wrong one.
2. **Only if it survives review**, advise on implementation. Note that two of the
   four fixes are not code changes at all (see §7) and one weakens a live safety
   control (§6), so "implement" is not automatically the right next step.

This concerns the **live demo runtime** on account `1033030`, not a research
package. Treat it accordingly.

---

## 1. The claims

**Claim 1 — the deployed account is capital-starved by 3x.**
The config carries drawdown limits as both absolute dollars and fractions of
activation equity and applies whichever is lower. Live activation equity is
**$987.66**, so the fractions bind:

| limit | config absolute | effective | source |
|---|---|---|---|
| suspend | $225.00 | **$74.07** | 7.5% |
| resume | $180.00 | $59.26 | 6.0% |
| combined hard stop | $300.00 | **$98.77** | 10% |
| floating hard stop | $449.77 | **$148.15** | 15% |

V60's historical maxDD is **$298 = 3.0x the permanent hard stop.** Its p90
drawdown ($175, 17.7% of equity) already exceeds the 15% floating stop. The
suspend line is breached at 437 of 1,713 trade-points.

**Claim 2 — the resume rule deadlocks.**
Resumption needs drawdown ≤ $59.26. Drawdown falls only when equity rises.
Equity rises only by trading. Trading is what is suspended. Replaying the real
ledger, the account suspends 2021-05-21 and, with no open positions left:

```
equity $175.03   peak $255.00   drawdown $79.97
needs $20.71 more profit to lift the suspension
open positions: 0  ->  equity frozen  ->  never resumes
```

It takes **130 of 1,713 trades** and stops for the remaining five years.

**Claim 3 — neither fix works alone.** Funding to $3,000 alone still freezes
(the deadlock is balance-independent). Fixing the resume rule alone still
hard-stops (at $999 the $98.77 ceiling is unavoidable).

| configuration | taken | net | maxDD | state |
|---|---|---|---|---|
| as deployed | 130 | $175 | $80 | frozen |
| resume fix only | 792 | $904 | $272 | **hard stopped** |
| funding only | 696 | $367 | $227 | **frozen** |
| both | 1,618 | $4,733 | $312 | running |
| both + 1x/2x sizing | 1,602 | **$7,249** | $317 | running |

**Claim 4 — dropping the dead sleeves is NEGATIVE.** An earlier recommendation
to remove V8/V25 to free the shared 2/day add-on budget was tested and
withdrawn: −$220 without sizing, −$879 with. Measured upper bound on the
reallocation upside is +$142, below the loss even in the best case.

---

## 2. Where everything is

Branch `claude/xau-ml-and-v8-audit-v1`, commits `eee5bcbf`, `9eae68a8`.
Package `xau-usd/xauusd-fast-research/claude-v60-portfolio-state-ml-v1/`

```
outputs/V60_IMPROVEMENT_FINDINGS.md   the written diagnosis
src/g1_live_capital_gate.py           limits, breach counts, deadlock proof
src/h1_fix_simulator.py               the four fixes and the comparison table
```

```bash
cd xau-usd/xauusd-fast-research/claude-v60-portfolio-state-ml-v1
PYTHONPATH=src ../balanced-horizon-ml-v5/.venv/Scripts/python.exe src/h1_fix_simulator.py
```

Evidence read (read-only) from the live runtime:
`C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2/{status.json,events.jsonl}`

---

## 3. What the simulator does NOT model — read this before trusting any number

These are disclosed limitations, not discovered ones. **Each is a candidate
reason the whole comparison is wrong, and checking them is the most valuable
thing you can do.**

1. **Only two gates are modelled.** The replay implements drawdown suspension
   and the combined hard stop. It does **not** model the other eighteen checks:
   position caps, concurrent/directional risk caps, per-source and account daily
   entry quotas, add-on quotas, the spread gate, stale candidate/tick, post-loss
   cooldown, duplicate add-on events. "1,618 of 1,713 trades taken" therefore
   assumes every ledger trade would be offered and would clear every other gate.
   **This almost certainly overstates trade count and net.**
2. **The ledger is not the live candidate stream.** It is V59/V60 research output
   built on Dukascopy M5. The live system trades Capital.com quotes from its own
   feeds. Ledger trades may not correspond to candidates the live executor would
   ever see, and the entry prices differ.
3. **The floating drawdown stop is not simulated at all.** Only realised
   (closed) drawdown drives the state machine here. The live floating stop
   ($148.15) watches unrealised loss on open positions and would likely trigger
   *earlier* and more often than anything modelled. This biases the results
   optimistic in an unquantified way.
4. **The daily guardian is not modelled.** `Account1DailyProfitFloorGuardian` is
   armed with a −100 AED daily loss stop and can force-close positions and write
   a halt file. None of that appears in the replay.
5. **Activation equity is treated as a constant $987.66.** If the executor
   recomputes it as balance changes, every limit moves and the whole analysis
   needs redoing. **Verify this — it is load-bearing.**
6. **Costs are as-booked in the ledger** (`fee_stress_pnl_usd`). Live spread,
   swap and commission on Capital.com may differ.
7. **Fix D's multipliers come from an ML ranking that is itself still under
   review** (see `outputs/CODEX_REVIEW_PROMPT.md`). If that review rejects the
   ranking, the $7,249 column falls back to the $4,733 column. Fixes A/B do not
   depend on it.

---

## 4. Verify the diagnosis against the actual code

The diagnosis was inferred from `status.json` and config, not from reading the
executor's drawdown logic line by line. Confirm or refute:

1. `refresh_drawdown_state` in `run_portfolio.py` — does it really take
   `min(absolute, fraction x activation_equity)`? Is `activation_equity` fixed at
   activation or recomputed?
2. Is the resume condition genuinely `drawdown <= resume_line`, with no
   time-based or manual path back? Is there an operator reset that makes the
   "deadlock" a non-issue in practice?
3. Is realised drawdown measured from a running peak of closed equity, or from
   activation equity? These differ materially and the replay assumes the former.
4. Does suspension block only entries, or does anything else change?
5. The live account shows `balance_usd: 999.47` against a design point of
   $2,998.45. **Is the $999 balance intentional?** If the owner deliberately
   funded it at $999, "fund to $3,000" is a question for them, not a fix.

## 5. Attack the simulator

6. `h1_fix_simulator.py::replay` — entries and exits as separate sorted events,
   exits settling before same-instant entries. Is that ordering right? What
   happens on ties?
7. The re-baseline in FIX B fires when `suspended and open_ct == 0` for
   `rebaseline_days`. Is `open_ct` tracked correctly across blocked entries?
8. Trades blocked during suspension are dropped permanently rather than deferred.
   Real suspension ends and later candidates arrive normally — is dropping them
   the right model, and does it bias the comparison?
9. `stats()` computes maxDD on the raw equity path while the state machine uses a
   re-baselined peak, so reported "true maxDD" ($312) exceeds the nominal cap
   ($300). Is that reported honestly, and is the gap correctly attributed to
   re-baselining rather than to a bug?
10. Fix C was measured as negative largely through path effects rather than
    direct P&L. Is that a real mechanism or an artefact of dropping trades from
    a fixed historical sequence?

---

## 6. Fix B is a safety-control change, not a bug fix

The proposed re-baseline lets the account resume by **forgiving accumulated
drawdown**. Measured consequence: true peak-to-trough loss reaches $311-$334
against a nominal $300 cap, depending on the cooling period.

| cooling period | net | true maxDD | nominal cap |
|---|---|---|---|
| 14 days | $4,910 | $311 | $300 |
| 30 days | $4,733 | $312 | $300 |
| 90 days | $3,863 | **$266** | $300 |

Treat this as a **risk-policy decision requiring explicit owner authorization**,
not a defect repair. If you disagree that a deadlock exists — for instance if
there is an operator reset path — then say so and Fix B should be dropped
entirely rather than softened.

Whatever you conclude: **do not weaken a drawdown control without the owner
saying so in writing.** A system that stops trading is failing safe. A system
that forgives its own drawdown limit may not be.

---

## 7. What is actually implementable, and by whom

- **Fix A (funding to ~$3,000)** — an account action. Not a code change. Owner
  only. Do not attempt it.
- **Fix B (resume rule)** — a real code change in the executor, gated on §6.
- **Fix C (drop V8/V25)** — **withdrawn, measured negative.** Do not implement.
- **Fix D (1x/2x sizing)** — blocked on the separate ML review. Also note it
  raises drawdown, which is the wrong direction until A and B are settled.

If you recommend implementing Fix B, propose it as a config-gated option that
defaults **off**, with the cooling period as a parameter, plus tests covering:
suspend, recovery by profit, recovery by re-baseline, and the flat-forever case.

---

## 8. Deliver

For each finding: **file:line, what is wrong, why it matters, and what it does to
the numbers.** Rank by severity. Separate "invalidates the diagnosis" from
"changes the magnitude" from "cosmetic".

Then one of:
- **DIAGNOSIS CONFIRMED** — with the corrected numbers once the unmodelled gates
  in §3 are accounted for, and a recommendation on Fix B.
- **DIAGNOSIS PARTLY WRONG** — state which claims survive.
- **DIAGNOSIS REJECTED** — state the single finding that kills it.

Constraints: this analysis authorizes nothing.
`ml_runtime_authorized: false`, `live_authorized: false`. Do not modify the V60
runtime, MT5 terminals, chart profiles, account settings, or any frozen package
as part of the review. Read everything; write only in your own package and
branch. Any change to the live executor needs owner authorization separately from
your technical verdict.
