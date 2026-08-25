# V60 V57 Volatility Anti-Chase V1

Status: post-hoc research nomination. Deployment is unauthorized.

## Purpose

August 2026 exposed a concentrated failure mode in the V57 breakout sleeve:
low-ranked long breakouts entered very near the prior 24-hour high while short-
term volatility was expanding. This experiment asks whether one narrow causal
veto can reduce that failure mode without weakening V60's established portfolio
edge.

August outcomes were visible before this rule was nominated. August is therefore
a stress diagnostic, not untouched validation. The rule must first preserve the
frozen 2021-01-01 through 2026-06-30 exact runtime replay and then survive the
separately locked prospective period beginning 2026-08-26.

## Frozen Rule

After at least 50 earlier V57 source executions, veto only a V57 long candidate
when all of the following causal entry-time conditions hold:

- causal rank is below 0.10;
- ATR ratio is at least 1.20; and
- distance from the prior 24-hour high is below 1.00 ATR.

Missing or stale information retains the V60 trade. The rule does not resize,
change exits, affect another specialist, or authorize an order.

## Selection Disclosure

Five mechanism variants were screened after August was exposed. The frozen rule
above was the only screened variant that preserved every original historical
gate. This is multiple testing and prevents the historical or August result from
authorizing deployment.

## Acceptance

Historical preservation requires net P/L, profit factor, closed drawdown,
floating-equity drawdown, every calendar year, final 3/6/12-month windows,
frequency, and trade retention to be no worse than V60.

August diagnostic success requires positive August P/L, higher PF, and no worse
closed drawdown. These checks show relevance to the observed failure mode but are
not deployment evidence.

Forward review requires at least 90 elapsed days, 100 scored and resolved V60
executions, 10 resolved anti-chase veto opportunities, complete causal feature
and decision-timing coverage, at least 99% trade retention, positive avoided
broker P/L, veto-cohort PF below 0.8, and no degradation of whole-portfolio P/L,
PF, closed drawdown, or exact tick equity drawdown. Passing still requires
explicit review; no script in this package can trade.
