# A1 XAU M5 Momentum Split-Entry BE-on-TP1 Hash Verification

Generated: 2026-07-03

Scope: local repository verification only. No MT5 terminal, chart, preset, order, or demo/live runtime was touched.

## Verdict

`PASS`

Claude reported a possible hash-manifest mismatch. Local verification against the current repository bytes shows the bound files and manifests are consistent.

## Checked Files

| File | Current SHA256 | Manifest field | Status |
|---|---|---|---|
| `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md` | `e55cf920c68cb070965529f1f426856bb61627920e5f3d31dae790e7a52cd824` | `spec_sha256` | PASS |
| `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5` | `a4d75f617ef4864fd6e28fa210ec02ce4b0b6e87171382534f51dbbecdc016c4` | `ea_source_sha256` | PASS |
| `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_SPLIT_BE_SIGNAL_CLAIM_SMOKE_2026_07_03.md` | `e8e47719fa8483c2deb498d67bba9b7d4004b1031a28e8ec9bd45ff08effe452` | `signal_claim_smoke_sha256` | PASS |
| `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_OWNER_AUTHORIZATION_2026_07_03.md` | `2aa181ce9346b3e40c946ccf2167852dbb03c8c3e558fcb62fa293a2cb50e200` | `authorization_sha256` | PASS |

## Authorization Cross-References

| Check | Status |
|---|---|
| Owner authorization manifest references the current frozen spec hash | PASS |
| Owner authorization manifest references the current EA source hash | PASS |
| Owner authorization document shows the same spec hash as the spec manifest | PASS |
| Owner authorization document shows the same EA hash as the spec manifest | PASS |

## Quantified Exposure Acceptance

The hash blocker is closed locally. The owner explicitly accepted the quantified split-entry practical exposure in the project thread on 2026-07-03:

```text
I accept the quantified split-entry exposure and approve demo attach on A1
```

This authorizes only the A1 demo attach described in the frozen spec. It does not authorize live trading, real capital, canonical Phase 2 approval, or post-hoc parameter changes.
