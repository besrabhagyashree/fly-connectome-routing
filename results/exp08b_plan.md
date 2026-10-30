# Step 8b plan — inside-only shuffles at gain 1.0

Written 30 Oct 2026 IST, before any step 8b simulation. **A new experiment, requested by Bhagyashree Besra after step 8 gave no answer.** Gain 1.0 was chosen after seeing the real brain's stage 1 table; no shuffled brain has been run above gain 0.001.

## Question

At the highest gain tested, is the real brain more focused than inside-only shuffles?

## Method

- Same rate operator, ≥ 5-synapse connectome, 7 sensory classes, spectral-radius normalisation and 60 steps as step 8. Gain fixed at 1.0.
- 50 inside-only degree, 50 inside-only block and 19 standard brains. Seeds `1000 + r − 1`, 10 swaps per edge.
- Every degree, block and boundary check from step 5 applies.
- Real-brain values come from step 8 stage 1 (spread 30.156, separation 0.918).

## Decision rule (one exit per case)

**Yes, focus holds at gain 1.0:** real spread is lower than both inside-only types at p < 0.05, with p = (1 + brains with spread ≤ real) / (N + 1). Otherwise **no**. Standard shuffles are reported alongside and are not part of the rule.

The size of the difference is reported with mean, SD and range. No size threshold applies.

## Reported alongside (exploratory)

Separation, direct-target share, active fraction, and agreement with Stürner's map (ρ).

## Limits

Direct connections still carry 61% of the real brain's descending activity at this gain, so this is a partial test of recurrence. Gain 1.0 was picked knowing only the real brain's values.
