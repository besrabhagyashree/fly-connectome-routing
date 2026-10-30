# Step 6b plan — does the real brain look more focused at matched activity?

Written 30 Oct 2026 ~21:10 IST, before any step 6b simulation. **Exploratory:** the shuffled-brain numbers are already known, so this cannot be confirmatory. Its only job is to decide whether the calibrated test (step 6c) is worth running.

## Why

Step 6 found the real brain's spread (34.0) above every inside-only brain (about 21), but the real brain also fires about twice as many neurons (380 vs about 177). Spread cannot separate focus from throughput.

## Method

Same model, parameters and 20 sugar neurons as step 6, real v783 brain, 3 trials per rate. Only the Poisson input rate (`r_poi`) changes, in this order:

1. Run 50, 75, 100 and 125 Hz. 150 Hz is the step 6 run.
2. The matching target is 177 neurons firing across the brain (mean of the 100 inside-only brains: 177.3).
3. Run one more rate, midway between the two tested rates that bracket 177. If none bracket it, run nothing extra.
4. The matched rate is the tested rate whose active count is closest to 177.

## Decision rule (one exit)

Run step 6c if the real brain's spread at the matched rate is **lower than the mean spread of both inside-only types** (20.66 and 21.73). Otherwise skip step 6c: matching activity does not bring back focus, and the study concludes on step 6.

The rate-by-rate table is reported either way.
