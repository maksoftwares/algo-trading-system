# V95 Shared-Portfolio Precommitment

The shared-account test is fixed before any V95 XAU outcome opens.

- V59/V60 inputs and hashes must remain byte-identical.
- The router may accept at most two V95 entries per UTC date.
- At most two add-on positions and USD `45` add-on initial risk may overlap.
- New entries suspend at USD `225` closed drawdown and resume only at USD `180`.
- Combined frequency must be at least `2.0` trades per weekday separately in
  Development-2, Confirmation, and Final.
- Combined stress PF must be at least `1.50` in every window.
- Absolute daily P&L correlation between V95 and the baseline must not exceed
  `0.50` in any window.
- The V60 floating-equity replay must include every accepted V95 trade and keep
  buffered drawdown at or below USD `449.7675`.
- No V59/V60 trade may be removed to make room for V95.

A historical pass is still not demo or live authorization. Prospective shadow
evidence is required afterward.
