# Step 6c plan — is the real brain more focused at equal activity?

Written 30 Oct 2026 IST, before any step 6c simulation. This is a **new experiment, decided after step 6b said not to run the original 6c.** That decision was made after seeing the 6a and 6b results, and it should be read that way.

## Why this design

The original 6c would have rebuilt and tuned 40 shuffled brains (about 14 h). That is not needed: 86 of the 100 inside-only brains from step 6a already fire within 10% of the target. Only the real brain has to be brought to that activity.

## Method

- **Target:** 177 whole-brain neurons firing (mean of the inside-only brains). **Band:** 159–195 (±10%).
- **Shuffled brains:** the step 6a brains already inside the band, at 150 Hz: 46 inside-only degree and 40 inside-only block. Selection uses activity only. No new shuffled simulation.
- **Real brain:** same model, parameters, 20 sugar neurons and 3 trials as step 6a, at 40, 30, 20 and 10 Hz. If none lands in the band and two adjacent rates bracket 177, run the midpoint, up to 3 times.
- **Matched rate:** the tested rate inside the band whose activity is closest to 177.

## Decision rule (one exit per case)

- **Yes, focus at equal activity:** real spread at the matched rate is lower than both inside-only types at p < 0.05, with p = (1 + band brains with spread ≤ real) / (N + 1).
- **No:** a matched rate exists and that test fails.
- **No answer:** no tested rate lands in the band. The question stays open and no new rates are added.

## What this test cannot do

- The shuffled spreads were already known when this was written; the real brain's value at these rates was not.
- The real brain gets far less input than the shuffles (about 30 Hz vs 150 Hz). Equal activity is reached by unequal input, which is what any such calibration does.
- It is one sense (sugar) and one activity level.
- Exploratory: MN9 and the rate-by-rate table are reported either way.
