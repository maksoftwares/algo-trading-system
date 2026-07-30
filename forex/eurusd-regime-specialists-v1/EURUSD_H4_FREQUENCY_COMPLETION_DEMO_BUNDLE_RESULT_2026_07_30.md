# EURUSD H4 frequency-completion demo bundle result

Status: **BUNDLE_READY_NO_DEPLOYMENT**

The validated 12-sleeve EA is packaged for a future permissioned demo
installation. The bundle contains ten frozen files plus a deterministic
manifest. It contains only a disarmed shadow preset and an ordering
**template**; it contains no active ordering preset.

| Item | Result |
|---|---|
| Bundle SHA-256 | `0f6af4d01a063e4603a4a06c6a533716feb8a3648469c6de02758ecea511bf7b` |
| Manifest SHA-256 | `3461ba4a83f585bcb8227c0d82ef485ab87995eab2cacb916c2482193cf91b12` |
| Frozen files | 10 |
| Deployment performed | No |
| Demo orders authorized | No |
| Target-terminal writes during preflight | 0 |

The startup template independently enforces terminal-wide
`AllowLiveTrading=0` and `AllowDllImport=0`. The shadow preset enforces shadow
mode, disabled demo/tester orders, active emergency stop, disarmed token, and
exact 0.01-lot sizing.

The read-only preflight correctly refused:

1. `C:\MT5A1M5MomentumBacktest`, because a Strategy Tester root can never be a
   demo deployment target; and
2. `C:\MT5PortableM15RegimeShadow`, because existing demo terminals are
   prohibited reuse targets and its process is running.

Both checks performed zero target writes. A new dedicated portable demo
terminal must be selected after explicit user permission. Enabling demo orders
requires a separate explicit permission after the disarmed shadow identity and
runtime audit pass.
