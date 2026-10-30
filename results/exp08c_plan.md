# Step 8c plan — is the 0.5% result a scaling artefact?

Written 31 Oct 2026 IST, before any step 8c simulation. **A new experiment, prompted by the second audit**, which found that spread and separation in steps 1 and 5 track each shuffled brain's raw spectral radius almost perfectly (R² 0.998–0.9999). That finding was post hoc.

## Question

Each brain is scaled to spectral radius 0.95, so a shuffled brain's connections are scaled down much less than the real brain's. If the real brain is run at the effective gain the shuffles ran at, does it still look more focused than they do?

## Method

Rate model as in steps 1 and 5: real brain only, ≥ 5-synapse connectome, 7 sensory classes, 60 steps.

- **Effective gain for a type:** 0.001 × (real raw radius) / (mean raw radius of that type's 200 brains), from the step 1 and 5 result files.
- Spread and separation are computed for the real brain at each type's effective gain.
- They are compared with that type's 200 shuffled brains from steps 1 and 5, unchanged.

## Decision rule (one exit per case)

**Real advantage survives:** real spread at the effective gain is lower than both inside-only types at p < 0.05, with p = (1 + brains with spread ≤ real) / (N + 1). Otherwise **the 0.5% result is treated as a scaling artefact**. The same test on separation (real higher) is reported for step 7, with its own yes or no.

## Limits

This scales the real brain to one mean effective gain, while shuffled brains each have their own. It tests gain only, so it does not show that no other difference exists. A full test would rerun every shuffled brain at its own matched gain.
