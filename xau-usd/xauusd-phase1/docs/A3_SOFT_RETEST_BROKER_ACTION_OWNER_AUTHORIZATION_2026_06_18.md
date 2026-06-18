# A3 Soft Retest V2 Broker-Action Owner Authorization

Date: `2026-06-18`

Scope: demo-only A3 account `1033669`, `Capital.ComMena-Demo`, `XAUUSD` only, `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`, magic `933500`, fixed lot `0.01`.

Owner instruction in Codex thread:

```text
No need of shadow. We make a trade, do the needfuls, and then place it on account 3, and it should be placing trades after that.
```

## Authorized Action

Attach `Account3SoftRetestExecutor` to the A3 demo portable terminal with broker action enabled only after:

- source compile passes with `0 errors, 0 warnings`;
- no pre-existing A3 entry exposure is detected for the configured A3 entry magics;
- no duplicate chart or open/pending exposure exists for magic `933500`;
- profile backup is created before chart mutation;
- local armed preset is written outside committed safe defaults;
- startup log confirms account `1033669`, demo server, `XAUUSD`, magic `933500`, dry-run `false`, broker-action `true`, fixed lot `0.01`, and `ATTACHED_A3_SOFT_RETEST_V2`.

## Boundary

This authorization is demo-only and does not authorize real-capital or live-server trading. It does not promote canonical Phase 2/3. Committed defaults must remain dry-run and broker-action disabled.
