# Step 8b — shuffled brains at gain 1.0

Run 30–31 Oct 2026 IST, 23:02 to about 00:15, with `experiments/exp08b_gain1.py`, following `results/exp08b_plan.md` (committed in 75de797 before the run). A new experiment, chosen after step 8a gave no answer.

## Main test

| Network | N | Spread, mean ± SD | Range | Brains ≤ real | p |
|---|---|---|---|---|---|
| **Real** | 1 | **30.16** | | | |
| Inside-only, degree | 50 | 289.3 ± 30.3 | 169.3–332.0 | 0 | 0.0196 |
| Inside-only, block | 50 | 232.5 ± 19.1 | 180.5–273.7 | 0 | 0.0196 |
| Standard (reported alongside) | 19 | 364.4 ± 29.2 | 298.4–404.3 | 0 | 0.05 |

**Rule: real spread lower than both inside-only types at p < 0.05. Met: the answer under the rule is yes.** Every degree, block and boundary check passed.

## Why this yes should not be read as evidence of focus

**The real and shuffled brains were not at the same operating point.** The plan had no check for this, which was a design gap.

| Network | Raw spectral radius | Active fraction at gain 1.0 | Direct-target share | Separation |
|---|---|---|---|---|
| Real | 2,019 | 0.33 | 0.61 | 0.918 |
| Inside-only, degree | about 287 | 0.93 ± 0.01 | 0.14 ± 0.02 | 0.42 ± 0.07 |
| Inside-only, block | about 389 | 0.82 ± 0.02 | 0.19 ± 0.02 | 0.58 ± 0.05 |
| Standard | about 291 | 0.92 ± 0.01 | 0.37 ± 0.02 | 0.39 ± 0.04 |

- Each brain is scaled to spectral radius 0.95 before running. The real brain's raw value is about 5–7× larger, so its connections are scaled down that much more.
- The same nominal gain therefore drives shuffled brains much harder. They saturate, with 77–95% of neurons active, against 33% in the real brain.
- A saturated network spreads signal widely whatever its wiring, so the 10-fold gap in spread mostly reflects this difference. How much, if any, comes from routing cannot be told from this run. Across brains, spread rises with active fraction (Spearman 0.76).

## What the result does show (exploratory)

- **Inside-only shuffling lowers the spectral radius about 5–7×,** with every boundary connection intact. Something in the real inside wiring gives the network a much larger leading eigenvalue. What that is has not been studied.
- **The map result is consistent with this step's limit, not a test of it.** Agreement with Stürner's map is 0.21 / 0.27 inside-only and 0.07 standard at gain 1.0. No real-brain value was recorded at this gain.

## Next

A fair test would run each shuffled brain at the gain that gives the real brain's activity. That is what the original gain calibration was meant to do. It would be a new experiment with its own rule.

## Files

`exp08b_all_brains.csv`, `exp08b_summary.csv`, `exp08b_plan.md`, `logs/exp08b_j*.log`.
