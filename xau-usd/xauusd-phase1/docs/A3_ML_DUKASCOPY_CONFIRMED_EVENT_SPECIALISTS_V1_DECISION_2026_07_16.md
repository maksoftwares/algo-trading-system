# A3 ML Dukascopy Confirmed Event Specialists V1 Decision

Date: 2026-07-16

Classification: `NO_TRAIN_FAMILY_SURVIVOR`

## Decision

Reject all three V1 mechanisms. Do not route them to ML, shared-account composition,
forward shadow, demo, or live execution. Do not change thresholds and rerun V1.

The result is a valid research rejection, not a source or execution failure.

## Source And Correctness

- verified Dukascopy XAUUSD Bid/Ask source: 120 of 120 months;
- source period: 2016-07 through 2026-06;
- causal M5 feature rows: 708,538;
- generated candidates: 149;
- resolved executable labels: 141;
- intentional entry-spread rejections: 8;
- unresolved labels: 0;
- resolved share among eligible labels: 100%;
- every source, uniqueness, chronology, and H1 reconciliation gate passed;
- maximum resolved entry spread: 0.148678R against the 0.15R ceiling;
- maximum initial 0.01-lot stop risk: $33.319 against the $50 ceiling.

Long entries used Ask and long exits used Bid. Short entries used Bid and short exits
used Ask. Native spread, an additional $0.30 per trade, and time-proportional holding
stress were included.

## Frozen Family Results

### Compression break and retest

This family produced zero candidates in every period. The full conjunction of a
12-bar compression, fixed ATR-ratio threshold, efficient high-intensity breakout,
separate retest, aligned tick imbalance, spread ceiling, and structural stop ceiling
was too sparse. It fails the train trade-count gate and provides no economic evidence.

This is a mechanism coverage failure. It is not permission to remove individual gates
after seeing the result.

### Session boundary sweep and reclaim

Train:

- 3 trades: 2 long and 1 short;
- stress PF 0.000;
- average stress result -1.1107R;
- stress net -3.3321R and -$10.05;
- 0.0024 trades per source day.

Exam outcomes were calculated for audit but were not opened for promotion because
train failed. They were also negative: 19 trades, PF 0.478, average -0.4162R, and
-$74.91 stress net.

### Shock failure and reclaim

Train:

- 15 trades: 5 long and 10 short;
- stress PF 0.201;
- average stress result -0.7943R;
- stress net -11.9143R and -$50.52;
- 0.0121 trades per source day;
- only 9.1% of active exit months positive.

The exam segment happened to be slightly positive at +0.9589R and +$19.97, with PF
1.054 across 30 trades. That evidence is not eligible: train failed badly, the exam
trade count and frequency gates failed, average R was below its gate, only 44.4% of
active months were positive, and removing the five largest winners made net negative.
Promoting this recent noise would violate the chronological firewall.

## What Was Learned

1. Added confirmation alone did not create edge. The V1 confirmations mostly removed
   opportunity while the surviving trades remained negative.
2. The short-hold 0.01-lot risk floor is feasible. Spread and stop risk were controlled,
   so those are not the reason V1 failed.
3. The campaign was far below the owner frequency objective. Even the most active
   family reached only 0.0597 trades per source day in any two-year segment.
4. ML cannot rescue this dataset. There are too few V1 labels, and the train economics
   are negative before any ranking model.
5. The reusable 120-month M5 Bid/Ask feature cache is now complete and source-locked,
   so later event censuses can run without rebuilding 137 million-plus ticks.

## Next Research Direction

Iteration 4 should not be another hand-tuned finished strategy. It should build a
label-first event census from mechanically broad, causal market events and measure
where conditional expectancy actually exists before prescribing a complete entry.

The census should:

- retain native Bid/Ask execution and the 0.01-lot risk ceiling;
- enumerate broad event populations without using outcome-selected thresholds;
- report forward MFE, MAE, time-to-event, spread, session, volatility, direction, and
  regime labels at several preregistered horizons;
- keep train, validation, internal test, and exam boundaries intact;
- require minimum population size and cross-window sign stability before any event
  may become a new specialist hypothesis;
- test event families that are structurally distinct from V1, especially trend
  pullback continuation with small stops and session opening-drive continuation;
- treat shock as no-trade unless a broad census shows stable conditional expectancy.

Any Iteration 4 specialist derived from that census requires a new preregistration and
cannot reuse V1's version name.

## Artifact Lock

- contract SHA256:
  `7e6c6f1f3f61f33d4cec2a7faafdd183e70ae8de31bf44f8e45ba8161e111530`
- candidates SHA256:
  `598aaffa8ab4739d65b3a2b8a651d72e5ddb1d707e97fc94a8c497d3bf2ffc9c`
- labels SHA256:
  `c662f659f66bf2e2670d3ae8ce6953e98c6659ffa43afefaa7d46599e45776da`
- family metrics SHA256:
  `95ac862c6331802f0280a2619ea59aee6e3815eb906d00fdf21dec6977f58e9c`
- empty survivor portfolio SHA256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- JSON report SHA256:
  `689763a8654c429f112c3322bc68cf3a1c678a7d55b904354deeca3297847cb3`
- Markdown report SHA256:
  `84281cebc728aae057bf085f1f4c1690591cd5b82377bc72e6e456eb7c594b9f`

## Authorization

- research result recorded: yes;
- forward-shadow candidate: no;
- Python prediction authorization: no;
- EA consumption authorization: no;
- demo authorization: no;
- live authorization: no.
