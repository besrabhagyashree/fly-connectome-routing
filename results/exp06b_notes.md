# Step 6b — the real brain at lower input (exploratory)

Run 30 Oct 2026 IST, 21:04 to about 21:35, with `experiments/exp06b_matched_activity.py`, following `results/exp06b_plan.md` (committed in 3eff44c before the run). Exploratory: the shuffled-brain numbers were already known.

## Results

Real v783 brain, 20 sugar neurons, 3 trials per rate.

| Input rate | Whole-brain neurons firing | Descending neurons firing | DN mean rate (Hz) | Spread | MN9 (Hz) |
|---|---|---|---|---|---|
| 50 Hz | 260 | 59 | 0.20 | 21.18 | 14.0 |
| 75 Hz | 357 | 64 | 0.65 | 32.70 | 44.0 |
| 100 Hz | 372 | 65 | 0.87 | 33.95 | 59.3 |
| 125 Hz | 389 | 68 | 1.05 | 33.81 | 76.0 |
| 150 Hz (step 6a) | 380 | 68 | 1.13 | 34.01 | 75.3 |
| *Inside-only shuffles at 150 Hz, for reference* | *176 / 179* | *41 / 44* | *0.74 / 0.75* | *20.66 / 21.73* | *0 / 29.5* |

## Decision

**Rule: run step 6c if the real brain's spread at the matched rate is lower than both inside-only means. Not met.** The matched rate is 50 Hz, the closest to the 177 target. Its spread of 21.18 is below the block mean (21.73) but not the degree mean (20.66). **Step 6c is not run, and the study concludes on step 6.**

## Limits of this answer

- **The match fell short.** No tested rate reached 177: the lowest gave 260. As the plan set out, 50 Hz still counts as the matched rate, so the rule was applied to an incomplete match.
- **The extra bracket rate did not run,** because no pair of tested rates bracketed 177.
- **The answer depends on what is matched.** Matching on whole-brain neurons firing picks 50 Hz (spread 21.2). Matching on DN mean rate instead would pick 75 Hz (0.65 Hz vs 0.74; spread 32.7), where the real brain remains well above the shuffles. Only the first was in the plan.
- **Spread is not smooth with input.** It stays at 33–34 from 75 to 150 Hz, then falls by a third between 75 and 50 Hz. That looks like a threshold: at 50 Hz some active population stops reaching the descending neurons.

## Reading

Lowering the input does not make the real brain more focused than the shuffles in any clear way. It also does not settle the throughput question from step 6a: the real brain was never brought down to the shuffles' activity. A cleaner test (step 6c, calibrating every brain) remains possible, but the rule set before this run says not to run it here. Reopening it would be a new experiment with its own rule.

## Files

`exp06b_matched.csv`, `exp06b_plan.md`, `logs/exp06b.log`.
