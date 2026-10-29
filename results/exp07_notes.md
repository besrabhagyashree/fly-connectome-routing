# Step 7 — cross-behaviour leakage

Run 29 Oct 2026 IST with `experiments/exp07_leakage.py`, following `results/exp07_leakage_plan.md` (fixed 28 Oct ~17:00 IST, before any leakage number was computed). No new simulation: separation from steps 1 and 5, DN activity profiles from `results/exp04_profiles/`.

## Main test (confirmatory): channel separation

Higher separation = the senses' DN activity patterns are more distinct = less leakage. p = (1 + brains with separation ≥ real) / (N + 1).

| Network | N | Separation, mean ± SD | Highest shuffle | Brains ≥ real | p | Real − mean | z |
|---|---|---|---|---|---|---|---|
| **Real** | 1 | **0.98519** | | | | | |
| Inside-only, degree | 200 | 0.98277 ± 0.00021 | 0.98383 | 0 | 0.005 | 0.00242 | 11.7 |
| Inside-only, block | 200 | 0.98350 ± 0.00017 | 0.98408 | 0 | 0.005 | 0.00168 | 10.0 |
| Standard (reported alongside) | 200 | 0.81534 ± 0.01373 | 0.85743 | 0 | 0.005 | 0.16984 | 12.4 |

**Rule: real separation higher than both inside-only types at p < 0.05. Met (p = 0.005 for both): leakage = yes.**

Size matters for reading this. Shuffling only the inside wiring makes the senses overlap slightly more at the descending neurons, consistently across all 400 brains, but by 0.2% of separation. Standard shuffles, which also create sense-to-DN shortcuts, cut separation from 0.985 to 0.815: about 70–100× the inside-only effect. As in steps 1 and 5, the large z-values reflect how little the inside-only brains vary, not a large effect.

## Exploratory (not confirmatory): activity on other senses' DN clusters

Share of each sense's |DN activity| that lands on Stürner et al. 2025 DN clusters whose dominant modality (lowest mean rank) is a different sense. Cluster dominance from the published table: taste 1, 2; touch 3, 4, 10, 11, 13, 14 and the sensory-descending cluster; visual projection 6, 7, 9, 12, 15, 16; humidity 8; ocellar 5. As planned, smell and photoreceptors cannot be scored (no cluster is dominated by them).

| Sense | Real | Inside-only degree (mean) | Inside-only block (mean) | Standard (mean) |
|---|---|---|---|---|
| Taste | 0.245 | 0.247 (p = 0.005) | 0.246 (p = 0.006) | 0.979 (p = 0.005) |
| Touch | 0.040 | 0.040 (p = 0.005) | 0.040 (p = 0.006) | 0.763 (p = 0.005) |
| Visual projection | 0.130 | 0.130 (no difference) | 0.130 (no difference) | 0.272 (p = 0.005) |
| Humidity | 0.9996 | 0.9975 (real higher) | 0.9982 (real higher) | 0.9986 (p = 0.06) |

p here = real leaks less than the shuffles, (1 + shuffles ≤ real) / (N + 1).

- Under standard shuffles, taste's activity on non-taste clusters goes from 25% to 98%, touch's from 4% to 76%: the shortcuts send each sense to the wrong behaviour clusters.
- Under inside-only shuffles the changes are tiny (≤ 0.2 percentage points) and not all in the same direction: taste and touch leak slightly less in the real brain, visual projection neurons are unchanged, and humidity leaks slightly more.
- Humidity is a poor fit for this measure: only one small cluster (8) is humidity-dominated, so ~100% of humidity's activity counts as "off-target" in every brain.
- This measure is our own construction from published labels, so no conclusion rests on it alone.

## Reading

The confirmatory test says the inside wiring keeps the senses slightly more separate than inside-only randomised wiring does, consistently but by a very small amount. Behaviour mixing of a meaningful size only appears when the boundary connections are randomised as well (standard shuffles), which is the cost of shortcuts a single-task comparison would not show. This matches steps 1, 4 and 5: the boundary sets most of the routing; the inside wiring adds a small, consistent refinement.

## Files

`exp07_separation.csv`, `exp07_offtarget_exploratory.csv`, `logs/exp07.log`.
