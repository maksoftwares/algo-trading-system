# V82 Prelock Calibration-Coverage Correction

Date: `2026-07-21`

The first committed calibration definition used January 2019. Its source audit
passed the monthly manifest contract, but the per-session audit subsequently
showed that USTBONDTRUSD contained zero quotes before January 21. Only nine full
weekdays were jointly eligible. No post-entry XAUUSD outcome, P&L, stop, target,
MAE, MFE, or economic label was opened.

Before contract lock, calibration therefore moves mechanically to the next full
calendar month, February 2019, and development begins March 1. The 1,000-policy
grid, candidate rule, density target, direction gate, policy tie-break,
execution geometry, economic gates, and every later boundary remain unchanged.
The incomplete January density output is discarded and cannot participate in
selection.

This is a source-coverage correction, not an economic rescue. A second coverage
change is not authorized for V82. If February still provides an inadequate
eligible sample, V82 ends before economic testing.
