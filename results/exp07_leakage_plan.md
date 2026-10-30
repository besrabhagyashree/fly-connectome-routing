# Step 7 — cross-behaviour leakage: analysis plan (fixed before running)

Written and agreed 28 Oct 2026, ~17:00 IST, before any leakage number was computed. Decided by Bhagyashree Besra.

## Question

Do randomised brains let one sense's signal spill onto descending neurons (DNs) that serve other senses, i.e. "mix up behaviours"? If yes, that is a cost of shortcuts that a single-task study (Park 2026) could not see.

## Main test (confirmatory)

- **Measure:** channel separation, as already computed by Exp01 (`rate_operator.channel_separation`): how distinct the DN activity profiles of the different senses are. Lower separation = more overlap between senses = more leakage. This is the established measure used throughout steps 1 and 5; nothing new is defined.
- **Data:** the real brain and the 200 + 200 + 200 randomised brains of steps 1 and 5 (inside-only degree, inside-only block, standard degree-preserving).
- **Rule:** leakage = **yes** if the real brain's separation is higher than the randomised brains' at **p < 0.05 for both inside-only types**, with p = (1 + brains with separation ≥ real) / (N + 1). Standard shuffles are reported alongside, not part of the rule.
- Effect sizes (mean difference and z) are reported with the p-values. No size threshold is used, because none is published for this measure.

## Exploratory check (not confirmatory)

- **Measure:** for each sense, the share of its |DN activity| that lands on Stürner et al. 2025 DN clusters whose dominant modality (lowest mean rank in Stürner's table) is a different sense.
- **Covers only** taste, touch, humidity and visual projection neurons: no Stürner cluster is dominated by smell or by photoreceptors, so those senses cannot be scored this way.
- The share is our own construction from published labels, so it is reported as exploratory, with the same p-value formula, and no conclusion rests on it alone.

## Data source

Saved DN activity profiles: `results/exp04_profiles/<network>_<replicate>.npz` (steps 4a and 5) and the Exp01/Exp05 result tables. No new simulation is needed for the main test.

## Correction, 30 Oct 2026 (audit)

The header says this was fixed "before any leakage number was computed". That is not accurate for the main test: separation at 35 brains was already on disk from step 1 (0.98283 / 0.98349 vs real 0.98519, p = 1/36). The rule was fixed before the 165 added brains, and before the exploratory off-target share was computed. All of this ran at gain 0.001.
