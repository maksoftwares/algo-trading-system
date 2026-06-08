# Phase 2 Demo Guard Router Spec

Status: SPEC_ONLY_NOT_DEPLOYED

This document defines the future demo-only guard/router that may be built if the weakness shadow report survives forward review. It does not authorize MT5 runtime changes, EA edits, chart changes, order changes, or canonical Phase 2 promotion.

## Purpose

The guard/router is intended to reduce the weaknesses found in actual demo trades without rewriting each EA:

- same-family duplicate stacking,
- weak EA clusters,
- weak XAUUSD morning/afternoon timing,
- unclear raw-vs-duplicate decision evidence.

## Inputs

The future guard/router should consume only broker/demo-safe runtime facts:

- candidate name,
- symbol,
- direction,
- volume,
- intended entry timestamp rounded to minute,
- Dubai time bucket,
- current open positions by magic/comment family,
- owner-approved allow/block policy version.

## Shadow Rules Under Review

The initial policy is measurement-only:

| Rule | Shadow action | Deployment status |
|---|---|---|
| Duplicate family mutex | Keep one event per same minute, symbol, direction, and volume | Not deployed |
| `session_extreme_retest_v0` quarantine | Block candidate | Not deployed |
| `symbol_normalized_round_retest_v0` quarantine | Block candidate | Not deployed |
| XAUUSD Morning/Afternoon filter | Block XAUUSD entries from `06:00-15:59` Dubai time | Not deployed |

Duplicate keeper priority is:

```text
breakout_retest
swing_breakout_retest_v0
symbol_normalized_round_retest_v0
provisional / experimental EAs
```

## Promotion Requirements

A rule can move from shadow-only to demo guard only if all are true:

- duplicate-hidden closed PnL improves,
- profit factor improves or is preserved,
- win rate improves or is preserved,
- enough trade count remains,
- at least one fresh week of forward demo data confirms the retrospective result,
- owner and reviewer approval are recorded.

## Runtime Boundary

The first implementation, if approved later, must be a separate demo-only guard/router component. It must not silently modify the existing 14 EAs. It must log every would-block decision with:

- timestamp,
- candidate,
- symbol,
- direction,
- volume,
- rule version,
- block reason,
- whether the decision was shadow-only or enforced.

## Current Decision

No runtime guard is authorized now. The current work is limited to shadow reporting and evidence collection.
