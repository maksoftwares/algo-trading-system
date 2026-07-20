# V74 Terminal Development Result

V74 audited 180 frozen DXY/XAU symbol-month manifests containing 131,424 hourly
rows and 447,967,303 declared ticks. Outcome-blind January 2019 calibration
selected policy `H01000__DM010__IN005__RR000__QC02` at 18/22 eligible weekdays
(`0.818182/day`), exactly nine long and nine short. Contract SHA-256:
`8e0ec9b0dd27282f9186976d97bd709d919764b34f0478a218aaa82ee78ca28d`.

Development resolved 710 trades over 871 eligible weekdays (`0.815155/day`),
with 368 longs and 342 shorts. Base/stress net was USD `-462.04/-516.71`;
base/stress PF was `0.3904/0.3519`; first/second-half stress PF was
`0.3230/0.3822`. Positive-day share was `22.50%`, no month was positive,
winner-removed stress net was USD `-541.04`, stressed closed DD was USD `517.76`,
and bootstrap p-value was `1.0`.

Decision: `V74_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. No threshold, horizon, response, quota, exit, cost, or gate may
be changed on these outcomes. The persistent directional failure permits one
fixed mirror on fresh periods; no further same-family reuse is allowed.

