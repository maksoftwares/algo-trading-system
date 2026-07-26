# Step 5.1 AED Account-Currency Correction

## Reason for correction

The read-only MT5 audit for account 1033030 showed that its account currency is
AED, while XAUUSD profit, margin, and base currencies are USD. Step 5 used the
numeric account balance as though it were USD. Its trade ordering and source
economics remain useful, but its account-specific risk percentages and drawdown
percentage cannot be used for this AED account.

Step 5.1 preserves every candidate, family, episode tie break, fixed 0.01-lot
size, portfolio policy, risk fraction, reporting window, and acceptance gate.
It changes only the monetary unit and starting-balance source.

## Frozen conversion

The account balance, equity, account currency, XAUUSD contract, tick values, and
one-dollar MT5 profit and margin probes are captured read-only with no positions
or orders. Positive USD outcomes use the broker's profit tick value. Negative
outcomes, initial risk, and costs use the slightly larger loss tick value.

The AED/USD peg is assumed stable across the historical test. Dynamic historical
FX conversion is not claimed. This is conservative for the broker snapshot but
remains a portability approximation rather than a historical Capital.com tick
value archive.

## Account controls

The same Step 5 fractions are applied after conversion to AED: 0.75% maximum
single-trade risk, 1.5% aggregate initial risk, 1.0% directional risk, 2% daily
closed loss, 10% drawdown suspension, 8% resumption, and 15% hard stop. The
three-position, family, mechanism, direction, daily-entry, fixed-lot, and margin
rules are unchanged.

## Decision boundary

All historical outcomes are exposed. A pass is research-only. A fail blocks the
prospective MT5 parity stage until a new strategy or capital decision is
preregistered; the risk limits may not be loosened after seeing this result.
No ML, Databento, COMEX, order placement, EA attachment, or runtime change is
authorized.
