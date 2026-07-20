# V80 Terminal Development Result

V80 inherited the locked V78 FX-consensus source event, but replaced immediate
entry with a causal transmission-retracement pattern. Outcome-blind July-August
2022 calibration registered exactly 100 timing policies and selected
`TR150__RF075__MW010`: XAU had to transmit 1.50 bps in the implied direction,
then retrace 75% of its running favorable excursion within ten seconds. The
policy produced `43/44 = 0.977273` candidates per eligible weekday, split 21
long and 22 short. Contract SHA-256:
`2a0a7f897440c71c0dec6caa1b010f11cca536755ca880456d5d986ae375dab5`.

Fresh development from September 2022 through June 2023 resolved `202` trades
over `214` eligible weekdays (`0.943925/day`), split 105 long and 97 short.
Base/stress net was USD `-132.81/-149.24`; base/stress PF was
`0.4813/0.4417`; first/second-half stress PF was `0.3559/0.5198`; no month was
positive; winner-removed stress net was USD `-173.83`; stressed closed-trade DD
was USD `150.33`; and bootstrap p-value was `1.0`.

Decision: `V80_DEVELOPMENT_FAIL_TERMINAL`. Validation remains sealed. The
locked FX-consensus transmission-retracement mechanism, timing policy, entry
direction, exits, costs, and quota may not be tuned or rescued on these
outcomes. V59/V60 remain byte-identical and outside this rejection.
