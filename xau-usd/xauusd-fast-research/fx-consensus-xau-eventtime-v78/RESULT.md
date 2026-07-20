# V78 Terminal Development Result

V78 audited 216 frozen EURUSD/USDJPY/XAUUSD symbol-month manifests containing
157,824 hourly rows and 608,967,406 declared ticks. Outcome-blind July-August
2018 calibration registered exactly 1,000 policies and selected
`H01000__LM025__CS050__RR000__QC05` at 37/44 eligible weekdays
(`0.840909/day`), with 21 longs and 16 shorts. Contract SHA-256:
`92dea393027f32e6d9e0e05220033fd63aa777f027b9f1c650ec6bb9485db091`.

Development resolved 613 trades over 723 eligible weekdays (`0.847856/day`),
with 322 longs and 291 shorts. Base/stress net was USD `-406.33/-452.66`;
base/stress PF was `0.3394/0.3023`; first/second-half stress PF was
`0.2499/0.3410`. Positive-day share was `21.58%`, no month was positive,
winner-removed stress net was USD `-474.61`, stressed closed DD was USD `454.91`,
and bootstrap p-value was `1.0`.

Decision: `V78_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. No threshold, horizon, response, quota, exit, cost, or gate may
be changed on these outcomes. The persistent directional failure permits one
fixed mirror on fresh periods; no further same-family reuse is allowed.
