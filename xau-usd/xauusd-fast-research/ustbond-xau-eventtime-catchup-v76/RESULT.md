# V76 Terminal Development Result

V76 audited 180 frozen USTBONDTRUSD/XAUUSD symbol-month manifests containing
131,424 hourly rows and 445,583,861 declared ticks. Outcome-blind January 2019
calibration registered exactly 1,000 policies and selected
`H02000__BM005__IN005__RR000__QC05`. The strict source-quality rule left nine
eligible calibration weekdays; the selected policy produced nine candidates,
with seven longs and two shorts. Contract SHA-256:
`56151a77385d55c6a19c577016075fa92b17db137e845695b472bd5e78b0f681`.

Development resolved 730 trades over 828 eligible weekdays (`0.881643/day`),
with exactly 365 longs and 365 shorts. Base/stress net was USD
`-512.26/-567.63`; base/stress PF was `0.3301/0.2952`; first/second-half stress
PF was `0.2233/0.3668`. Positive-day share was `23.43%`, no month was positive,
winner-removed stress net was USD `-584.37`, stressed closed DD was USD `567.88`,
and bootstrap p-value was `1.0`.

Decision: `V76_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. No threshold, horizon, response, quota, exit, cost, or gate may
be changed on these outcomes. The persistent directional failure permits one
fixed mirror on fresh periods; no further same-family reuse is allowed.
