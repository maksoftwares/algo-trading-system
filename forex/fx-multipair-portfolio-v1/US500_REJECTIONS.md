# US500 lane — recorded rejections

Append-only, same discipline as `REJECTIONS.md`.

## U0 — BTCUSD rejected as the instrument (2026-07-31)

Not a strategy rejection: BTC was rejected **before** any strategy work, by the
measured range/cost screen on the live Capital.com demo
(`outputs/INSTRUMENT_SCREEN.json`, 21 days of broker ticks).

| Symbol | Spread | Median daily range | Ratio |
|---|---:|---:|---:|
| US30 | 20 pts | 4,951 | 141.5x |
| XAUUSD | 30 pts | 6,398 | 121.9x |
| **US500** | 6 pts | 777 | **74.0x** |
| EURUSD | 7 pts | 454 | 37.1x |
| ETHUSD | 175 pts | 6,062 | 19.8x |
| **BTCUSD** | **5,000 pts ($500)** | 140,195 | **16.0x** |

Capital.com charges a **$500 spread** on BTCUSD — 0.078% of price. BTC's 2.18%
daily range cannot outrun it, giving 16.0x: the worst instrument on the account
and *below* EURUSD, where eleven hypothesis classes already failed on cost
alone. The 1.6 GB of BTC tick history on disk does not change a cost structure.

**US500 selected instead at 74.0x** — roughly double EURUSD. This screen cost
minutes and is the single highest-leverage step the Forex lane taught.

## U1 — Three intraday families on 14 months of broker data (2026-07-31)

**Tested:** `opening_range` (break of the first 30 minutes of the US cash
session), `overnight_fade` (fade the opening gap), `session_trend` (H1 Donchian
inside the session). 27 grid points each over `rr` × `atr_mult` × `context_mult`,
chronological split inside the broker history (design 2025-06 → 2026-01,
validation 2026-02 → 2026-07), costed at the measured 9-point round trip.

**Result: REJECTED — 0 of 81 grid points profitable in both windows.**

Worse than flat, the sign is unstable across the split:

| Family | Design PF | Validation PF |
|---|---:|---:|
| `opening_range` | 0.888 | **1.139** |
| `overnight_fade` | **1.268** | 0.780 |
| `session_trend` | 0.857 | **1.048** |

Two families flip from losing to winning and one from winning to losing. That is
the signature of noise, not of an edge with unstable timing.

**This is a data-sufficiency rejection, not an instrument rejection.** With ~200
design and ~150 validation trades over 14 months — a single, strongly bullish
regime — the search has no power to separate signal from noise. It is recorded
so the same 14-month window is not mined again for a "survivor"; that is exactly
how the FX lane produced four overfit candidates.

Requirement before retrying: the Dukascopy `USA500.IDX-USD` history from 2016
(downloading, rate-limited to roughly 3 files/second, ~8 hours for 92,016
hours of data).

## Open note — H1 (overnight effect) is not yet tested

The preregistered primary hypothesis remains untested on long history. On the
14-month broker sample it points the right way — overnight +3.631 pts/day
(58.9% win, t +1.70) vs intraday +1.503 (53.7%, t +0.59), overnight capturing
71% of the move — but one bull regime cannot confirm it, and the free daily
sources that would have tested it over decades are now gated (Stooq serves a
JavaScript bot-check, Yahoo's download endpoint requires authentication).

It is therefore pending, not rejected.
