# EURUSD V20R6 shared-account isolation deployment

## Deployment

- Demo account: `1033030`
- Server: `Capital.ComMena-Demo`
- Account currency: `AED`
- Terminal: `C:\MT5PortableEurUsdV20R5Demo1033030`
- Chart: `EURUSD,M15`
- EA: `EurUsdUnifiedPortfolioControlledDemoV20`
- Revision: `20.66`
- Preset: `EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_ARMED.set`
- Start config: `EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030_ARMED.ini`

V20R6 retains the V20R5 signal policy. It changes runtime risk accounting only:

1. Persistent drawdown uses EURUSD portfolio closed and floating P/L from the
   owned magic namespace, not total account equity.
2. AED deal, margin, equity, and floating values are converted at the AED peg
   (`3.6725 AED/USD`) before comparison with USD-labelled limits.
3. Minimum account equity and post-order free-margin floors remain disabled.
4. MT5 broker margin availability remains account-wide and cannot be isolated.
5. New R6 peak and breaker keys prevent reuse of the old account-equity peak.

## Build identities

| Artifact | SHA-256 |
|---|---|
| MQ5 source | `ab6a15f6122077599111ae5e97ea53923d7c725bb036436ab3387e53506d4d84` |
| EX5 binary | `1b313d8371cd7259af7f527fadbcce4e15c2c4ef9b3e24182bd5d485e4fbd03b` |
| Armed preset | `df2a72073f3aa0944bf9d4c1ad7c2795c420d50a56ef465a573cd56b3a6d52df` |
| Startup config | `c2711634a7a02d22b2e9724f2e633e5db32c3385a6669b0ac7178e9b8fb39bca` |
| Compile log | `43504a768ce7ee56faa48a30fd22d3f7deaf397b4a8b3adc5bb0d1ba0b54ea21` |

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
