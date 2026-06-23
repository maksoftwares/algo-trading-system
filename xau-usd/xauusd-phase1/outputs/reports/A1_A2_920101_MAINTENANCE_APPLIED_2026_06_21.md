# A1/A2 920101 Maintenance Applied - 2026-06-21

Status: `DRY_RUN_READY`
Mode: `dry-run`

Owner requested fixing runtime drift after forensic confirmation. Demo accounts only; no canonical Phase 2/live-capital approval.

## Scope

- A1 account: `1025742`
- A2 account: `1033030`
- Symbol/candidate: `XAUUSD / breakout_retest`
- Session server hours: `12->15`
- Lot: `0.01`
- A3 touched: `False`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| a1_has_one_active_xau_920101_chart | `FAIL` | chart27.chr |
| a2_has_one_active_xau_920101_chart | `FAIL` | chart04.chr |
| a1_non_spec_executors_disarmed | `PASS` | A1 non-spec broker action false/dry-run true |
| a1_wr50_disarmed | `PASS` | WR50 demo trading disabled |
| a1_guardian_active_loss_stop | `PASS` | A1 guardian active with -100 loss stop |
| a2_guardian_active_loss_stop | `PASS` | A2 guardian active with -100 loss stop |
| a3_profile_untouched | `PASS` | A3 profile hash map unchanged |

## Profile Backups


## Changed Files

| Action | Path |
| --- | --- |

## After Runtime-Relevant Charts

### A1

| Chart | Symbol | Expert | Candidate | Account | Dry-run | Broker | Session | Max open | Cost | Spread | Guardian loss | Halt file |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| chart24.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `` | `` | `` | `` |
| chart26.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | `` | `` | `` | `true -100.0` | `experimental_demo_kill_switch.txt` |
| chart27.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1025742` | `false` | `true` | `0->23` | `1` | `0.15` | `75.0` | `` | `` |

### A2

| Chart | Symbol | Expert | Candidate | Account | Dry-run | Broker | Session | Max open | Cost | Spread | Guardian loss | Halt file |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `` | `` | `` | `` |
| chart03.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | `` | `` | `` | `true -100.0` | `tier1_bestea_kill_switch.txt` |
| chart04.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1033030` | `false` | `true` | `0->23` | `1` | `0.15` | `75.0` | `` | `` |

## Claude Verification Focus

- Confirm A1 now has exactly one broker-action XAU Phase2ExperimentalDemoExecutor breakout_retest chart for account 1025742.
- Confirm A1 EURUSD/GBPUSD standard executor and A1 repair/WR50 lanes are disarmed.
- Confirm A2 XAU Phase2ExperimentalDemoExecutor remains broker-action enabled and aligned to A1.
- Confirm A1 and A2 both have active daily profit/loss guardians using their account-specific halt files.
- Confirm A3 profile hashes did not change and A3 remains paused.
