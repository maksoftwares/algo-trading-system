# EURUSD controlled demo rehearsal

Candidate: `EURCAPV2_CHOP_ASIA_LONDON_SHORT`

Attach the compiled EA to EURUSD using `mt5/Presets/EURUSD_V4_SHADOW_DEMO.set`.
The shadow preset logs signals and cannot place orders.

Before a demo-order rehearsal:

1. Confirm the account is `Capital.ComMena-Demo`.
2. Confirm broker UTC offset is zero for the tested history/session mapping.
3. Confirm lot size is 0.01 and maximum spread is 2.0 pips.
4. Review the real-tick report and its SHA-256 in
   `outputs/capital_mt5_real_tick/VERDICT.json`.
5. Use the owner-authorized template only after explicit authorization.

The EA evaluates completed H1 bars at 06:00–09:00 UTC. It sells the first
Asia-range downside expansion only when the completed H4 classifier is `chop`,
uses a 1.75 ATR stop, 1.25R target, and 12-H1-bar time exit.

This package is for controlled demo rehearsal. It is not approved for live funds.
