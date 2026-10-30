# Step 8c — the 0.5% result is a scaling artefact

Run 31 Oct 2026 IST with `experiments/exp08c_effective_gain.py`, following `results/exp08c_plan.md` (committed in 511c9e0 before the run). A new experiment, prompted by the second audit.

| Inside-only type | Effective gain | Real spread | Shuffle spread, mean ± SD (N = 200) | Brains ≤ real | p | Real separation | Shuffle separation | p |
|---|---|---|---|---|---|---|---|---|
| Degree | 0.00704 | 17.191 | 17.194 ± 0.008 | 54 | 0.27 | 0.98279 | 0.98277 | 0.37 |
| Block | 0.00519 | 17.163 | 17.165 ± 0.007 | 67 | 0.34 | 0.98352 | 0.98350 | 0.42 |

## Decision

**Rule: the real advantage survives only if real spread is lower than both inside-only types at p < 0.05. It is not. The 0.5% result in steps 1 and 5 is treated as a scaling artefact.** The same holds for separation, so step 7's 0.2% is also treated as an artefact.

## Why it happened

Each brain is scaled to spectral radius 0.95. The real brain's raw radius is 2,019, against means of 287 and 389 for inside-only shuffles, so its connections are scaled down 5–7× more on average. At the same nominal gain, shuffled brains run at a higher effective gain.

## What this does not change

- Agreement with Stürner's map: the audit found no relation to the radius (R² 0.002), so the gap of about 0.13 stands. It was not retested at effective gain.
- The gap to standard shuffles: at gain 0.03 the real brain's spread is still only 17.6, against 122.
- The spiking results: that model has no such scaling.

## Limits

The real brain was run at one mean effective gain, while each shuffled brain has its own. A full test would rerun every shuffled brain at its own matched gain.

## Files

`exp08c_summary.csv`, `exp08c_plan.md`.
