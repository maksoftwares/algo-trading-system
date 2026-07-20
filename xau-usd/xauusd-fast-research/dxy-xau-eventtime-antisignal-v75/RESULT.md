# V75 Terminal Development Result

V75 inherited V74 policy `H01000__DM010__IN005__RR000__QC02`, every event
timestamp, the one-per-day quota, and the full execution and gate geometry. It
inverted source direction exactly once and began on the first day after V74's
exposed period. Contract SHA-256:
`9384d5c77a82346f057a53759d4dfc200c54531c7d49c1349634965875b6d816`.

Fresh development resolved 231 trades over 256 eligible weekdays
(`0.902344/day`), with 115 longs and 116 shorts. Base/stress net was USD
`-131.42/-148.20`; base/stress PF was `0.4445/0.4025`; first/second-half stress
PF was `0.4536/0.3592`. Positive-day share was `27.34%`, one of 12 months was
positive, winner-removed stress net was USD `-166.78`, stressed closed DD was
USD `153.99`, and bootstrap p-value was `1.0`.

Decision: `V75_DEVELOPMENT_FAIL_TERMINAL`. Confirmation, validation, and exam
remain sealed. V74/V75 jointly retire both directional interpretations of this
fixed DXY event-time family. No mirror, threshold, horizon, response rule,
quota, stop, target, hold, cost, or gate reuse is allowed.
