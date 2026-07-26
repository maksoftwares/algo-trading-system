# Auxiliary Transfer V15 Preregistration

## Question

Can a much larger, causally labelled mechanical-candidate population improve
the exact canonical V60 trade filter without allowing different strategy
attempts or action geometries to masquerade as independent evidence?

## Frozen populations

The primary evaluation population remains the 3,752-row canonical dataset.
Only its 3,024 mandatory-XAU-feature-pass rows may be modelled.

The auxiliary source registry contains 29,419 mechanical events, of which
28,432 have 73,116 resolved event/action labels, grouped into 15,172 structural
episodes. Before fitting, V15 removes every complete 30-minute auxiliary
episode containing an event with the same UTC decision timestamp and direction
as any canonical row. The remaining action rows retain their frozen structural
weights. The quarantined 117,534 journey rows remain excluded.

## Causal transfer surface

Only pre-trade semantics available in both domains are aligned: direction,
spread, quote intensity, direction-adjusted returns, one-hour range, tick
imbalance, planned action geometry, cyclic UTC time, and a coarse
outcome-blind mechanic mapping. Exact timestamps, identities, outcomes,
historical accept states, and post-trade fields are forbidden.

Continuous features are quantile-normalized separately using auxiliary-fit
and canonical-fit feature distributions. Canonical calibration or test
features never fit a transform. This permits transfer of ordinal
relationships without pretending the two feeds have identical scales.

For every outer fold:

1. auxiliary actions must have both decision and label-end times before the
   canonical calibration boundary;
2. Ridge Expected-R, conservative histogram-gradient Expected-R, and logistic
   win-probability models fit the auxiliary actions using structural weights;
3. their three scores are added to the frozen B1+B2+B3 canonical surface;
4. the partial-pooling canonical Ridge fits only canonical FIT labels;
5. the locked profit quantile grid is selected only on canonical CALIBRATION;
6. economics are measured only on canonical TEST and exact V60 replay rows.

## Decision

V15 advances only as a prospective challenger if it improves exact V60 net
P&L versus both raw V60 and the locked B1+B2+B3 historical diagnostic over all
history, does not lose money versus raw V60 in the latest three months,
improves raw V60 over six and twelve months, retains at least 85% of raw
trades, and does not worsen all-history profit factor or drawdown.

Historical outcomes were exposed before this design. A historical advance is
not deployment evidence. V14 stays locked and active; V15 has no prospective,
shadow, demo, live, EA, sizing, or broker authority.
