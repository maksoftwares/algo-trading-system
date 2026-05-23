# Round Number Retest v0 XAU-Specific Mechanism Note

Date: 2026-05-23

`round_number_retest_v0` uses fixed absolute XAUUSD price handles at 10, 25, and 50 dollar increments. Those handles are meaningful on the XAUUSD price scale but are not a symbol-normalized round-number definition for EURUSD.

The multisymbol run produced:

| Symbol | Trades | Profit Factor | Verdict |
| --- | ---: | ---: | --- |
| EURUSD | 0 | 0.000 | FAIL |
| USDJPY | 559 | 1.435 | PASS |

Interpretation:

- This v0 should be treated as XAU-specific.
- The EURUSD zero-trade result is not evidence of cross-asset transfer.
- The USDJPY pass is supportive but insufficient to call this a diversified multi-symbol behavior.
- Any future universal round-number candidate must pre-register symbol-normalized increments before testing.

This note can support `PASS_WITH_XAU_SPECIFIC_JUSTIFICATION` for the multisymbol gate, but it should not be read as full multisymbol consistency.
