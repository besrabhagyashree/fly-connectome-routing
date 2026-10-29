# Step 5 — scaling to 200 randomised brains per type

Run 28 Oct 2026 16:46 IST → 29 Oct 2026 ~08:35 IST (PC asleep 01:12–08:09 IST; jobs paused and resumed, no data lost). Driver: `experiments/exp05_scale.py`.

## What was run

- Brains 36–200 of three randomisation types (495 new brains), added to the 35 per type from steps 1 and 4a: inside-only degree-preserving, inside-only block-preserving, standard degree-preserving.
- Each brain was built once (seed `1000 + r − 1`, 10 swaps per edge) and scored twice: the step 1 rate-model measures (Exp01 `evaluate`) and the step 4a simulation-vs-map agreement (`score`).
- Checks on every brain: degree / block invariants preserved (495/495 ok); inside-only brains leave every boundary connection untouched (330/330 ok). Brain #1 re-run reproduced steps 1 and 4a (rho exact; spread equal to the 5th decimal).
- Test: empirical p = (1 + brains at least as extreme as the real brain) / (N + 1). With N = 200 the floor is 1/201 = 0.005.

## Step 1 at 200 brains — focus (spread; lower = more focused)

| Network | N | Mean spread ± SD | Most focused shuffle | Brains ≤ real | p | z |
|---|---|---|---|---|---|---|
| **Real** | 1 | **17.099** | | | | |
| Inside-only, degree | 200 | 17.194 ± 0.008 | 17.151 | 0 | 0.005 | 11.2 |
| Inside-only, block | 200 | 17.165 ± 0.007 | 17.142 | 0 | 0.005 | 9.6 |
| Standard | 200 | 122.0 ± 4.7 | 105.6 | 0 | 0.005 | 22.1 |

**Pre-registered rule** (README, "Correction (28 Oct 2026)"): real more focused than both inside-only types at p < 0.05. **Met: p = 0.005 for both.** The real brain beats all 400 inside-only brains, but the margin is small: 0.4–0.6% of spread. Standard shuffles spread the signal ~7× wider.

## Step 4a at 200 brains — simulation agrees with Stürner's map (rho_own, higher = better)

Mean over the 6 scored senses: real 0.647; inside-only degree 0.508 ± 0.009 (best 0.530); inside-only block 0.518 ± 0.010 (best 0.545); standard 0.070 ± 0.014 (best 0.099).

| Sense | Real | Inside-only degree (mean / best) | Inside-only block (mean / best) | Standard (mean / best) |
|---|---|---|---|---|
| Taste | 0.799 | 0.657 / 0.686 | 0.665 / 0.691 | −0.032 / 0.070 |
| Humidity | 0.430 | 0.239 / 0.312 | 0.250 / 0.325 | 0.078 / 0.175 |
| Touch | 0.720 | 0.717 / 0.719 | 0.717 / 0.719 | −0.083 / −0.007 |
| Smell | 0.630 | 0.373 / 0.433 | 0.411 / 0.464 | 0.174 / 0.275 |
| Vision | 0.665 | 0.432 / 0.495 | 0.430 / 0.531 | 0.120 / 0.215 |
| Bilateral | 0.637 | 0.631 / 0.635 | 0.632 / 0.636 | 0.166 / 0.251 |

No randomised brain reaches the real value for any sense: p = 0.005 (N = 200) for inside-only degree and standard, p = 0.006 (N = 165) for inside-only block. Inside-only block has 165 brains here because step 4a scored only inside-only degree and standard for brains 1–35.

Touch and bilateral are the narrowest margins (real 0.7198 vs best shuffle 0.7192; 0.6366 vs 0.6355): significant by the rule, but the inside wiring adds almost nothing for these senses, consistent with their large direct-to-DN share (step 4b).

## Reading

- Every step 1 and 4a conclusion drawn at 35 brains holds at 200 with p at its floor; nothing changed direction, and the means moved by < 0.01.
- The effect of the inside wiring is real but small for focus (≈0.5%) and sense-dependent for the map (from ~0 for touch to ~0.26 for smell). Most of the focus lives in the boundary connections, which inside-only shuffles keep.
- Standard shuffles remain a different regime (7× spread, map erased), as steps 2 and 4b explained.

## Files

`exp05_exp01_j{1-4}.csv`, `exp05_exp04_j{1-4}.csv` (per-brain rows), `exp05_step1_summary.csv`, `exp05_step4a_summary.csv`, `logs/exp05_j{1-4}.log`; profiles in `exp04_profiles/` (used by step 7 leakage).
