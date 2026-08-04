# EURUSD V20R6.1 shared-account isolation deployment

## Deployment

- Demo account: `1033030`
- Server: `Capital.ComMena-Demo`
- Account currency: `AED`
- Terminal: `C:\MT5PortableEurUsdV20R5Demo1033030`
- Chart: `EURUSD,M15`
- EA: `EurUsdUnifiedPortfolioControlledDemoV20`
- Revision: `20.67`
- Preset: `EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_ARMED.set`
- Start config: `EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_ARMED.ini`

V20R6.1 retains the V20R5 signal policy. It changes runtime risk and order
validation only:

1. Persistent drawdown uses EURUSD portfolio closed and floating P/L from the
   owned magic namespace, not total account equity.
2. AED deal, margin, equity, and floating values are converted at the AED peg
   (`3.6725 AED/USD`) before comparison with USD-labelled limits.
3. Minimum account equity and post-order free-margin floors remain disabled.
4. MT5 broker margin availability remains account-wide and cannot be isolated.
5. New R6 peak and breaker keys prevent reuse of the old account-equity peak.
6. Every core long and short validates SL/TP against the broker's current
   `SYMBOL_TRADE_STOPS_LEVEL` before the common pretrade guard and order send.
7. If the broker minimum requires a wider stop, the target is moved to preserve
   the sleeve's reward-to-risk ratio. The existing cash-risk guard then checks
   the adjusted geometry and may reject it.

## Build identities

| Artifact | SHA-256 |
|---|---|
| MQ5 source | `0d93cdd3f240b0ad3dacaad026413a39ca96fee5868cebd48986611ea4806db0` |
| EX5 binary | `3afb4a954562b1021bb66cde70cd0b5dd8f9d8f7f0fc1869afe2afa5f0b895df` |
| Armed preset | `df2a72073f3aa0944bf9d4c1ad7c2795c420d50a56ef465a573cd56b3a6d52df` |
| Startup config | `c2711634a7a02d22b2e9724f2e633e5db32c3385a6669b0ac7178e9b8fb39bca` |
| Compile log | `22a9474e51e9cc54a08cccb7f8e148fdd4a16cbf7a1fc694da6a9e01ac705da2` |

MetaEditor result: `0 errors, 0 warnings`.

## Recovery

1. Copy the MQ5 and EX5 files to the terminal's `MQL5\Experts` directory.
2. Copy the armed preset to `MQL5\Presets`.
3. Copy the startup config to `Config`.
4. Confirm account `1033030` has no open EURUSD position or pending order.
5. Start `terminal64.exe /portable /config:<absolute R6 config path>`.
6. If a previous terminal was killed rather than closed normally, wait at least
   180 seconds for the duplicate-instance mutex to become stale.
7. Require `INIT_OK`, `STARTUP_LATCH`, and `RESTART_RECOVERY_OK` in
   `%APPDATA%\MetaQuotes\Terminal\Common\Files\EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030.csv`.
8. Require a heartbeat containing `mode=ordering`, `rsi_orders=true`,
   `breaker=false`, `persistence=true`, and `mutex=true`.

No live-account authorization is provided by this deployment.
