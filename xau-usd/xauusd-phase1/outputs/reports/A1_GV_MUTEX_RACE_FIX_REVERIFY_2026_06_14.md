# A1 GV Mutex Race Fix Reverify

Status: `PASS`

## Review Stop Issue

The NO-GO review challenged T0 on two concrete points: the executor was described as truncated versus HEAD, and the mutex report was described as false because the focused pytest suite failed.

Current workspace recheck does not reproduce that broken state. `Phase2ExperimentalDemoExecutor.mq5` matches current branch HEAD exactly and still contains the full startup, shutdown, timer, mutex, and order-send paths.

## Source Parity

| Check | Result |
|---|---:|
| Git diff for executor | empty |
| Working lines | 1630 |
| HEAD lines | 1630 |
| Working SHA-256 | `a04123fd590303b9fa576c485883ae54b67fbb9066336e37ef8fae31904290ce` |
| HEAD SHA-256 | `a04123fd590303b9fa576c485883ae54b67fbb9066336e37ef8fae31904290ce` |
| Working file equals HEAD | `true` |

## Source Landmarks

| Symbol | Line |
|---|---:|
| `if(!ClaimFamilyMutexBeforeOrder(observation, mutex_name))` | 1403 |
| `bool sent = OrderSend(request, result);` | 1425 |
| `int OnInit()` | 1455 |
| `WriteStartupRow(gv_mutex_self_test_status);` | 1524 |
| `void OnDeinit(const int reason)` | 1536 |
| `void OnTimer()` | 1567 |

The mutex claim still precedes `OrderSend`.

## Verification

| Gate | Evidence |
|---|---|
| Focused pytest | `tests/test_phase2_experimental_demo_mutex.py` - 3 passed in 0.02s |
| MetaEditor scratch compile | `C:\MT5CompileScratch\A1GvMutexReverify_20260614_014944\Logs\compile_Phase2ExperimentalDemoExecutor.log` |
| Compile result | `Result: 0 errors, 0 warnings, 978 ms elapsed, cpu='X64 Regular'` |
| `.ex5` produced | `true` |

MetaEditor returned process exit code `1` on this local invocation despite creating the `.ex5` and writing the clean result line above; the compile gate is therefore the emitted compile log plus artifact existence.

## Boundary

- A1 login `1025742` was reverified only for the owed mutex fix.
- A2 login `1033030` was not touched.
- A3 demo login `1033669` remains gated for later attach.
- No orders, positions, charts, profiles, or runtime presets were changed by this reverify pass.

## Result

T0 is clean in this workspace. No source restoration was required because the executor already matches HEAD and retains `OnInit`, `OnDeinit`, `OnTimer`, and the mutex-guarded order-send path.
