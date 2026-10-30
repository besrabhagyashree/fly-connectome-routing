# Step 6c — the real brain at equal activity

Run 30 Oct 2026 IST, 21:26 to 21:54, with `experiments/exp06c_equal_activity.py`, following `results/exp06c_plan.md` (committed in d4f97b7 before the run). This was a new experiment, decided after step 6b said not to run the original 6c.

## Results

Real v783 brain, 20 sugar neurons, 3 trials per rate. Target band: 159–195 neurons firing.

| Input rate | Whole-brain neurons firing | Descending neurons firing | DN mean rate (Hz) | Spread | MN9 (Hz) | In band? |
|---|---|---|---|---|---|---|
| 10 Hz | 45 | 4 | 0.001 | 3.57 | 0 | no |
| 20 Hz | 51 | 6 | 0.003 | 4.33 | 0 | no |
| 30 Hz | 63 | 7 | 0.026 | 5.12 | 0 | no |
| 35 Hz | 84 | 11 | 0.037 | 5.96 | 0.3 | no |
| 37.5 Hz | 124 | 29 | 0.044 | 8.27 | 1.0 | no |
| 38.75 Hz | 139 | 25 | 0.044 | 7.22 | 1.0 | no |
| 40 Hz | 197 | 47 | 0.093 | 14.19 | 6.0 | no, 2 above |
| *Inside-only shuffles in the band, 150 Hz (46 + 40 brains)* | *about 173* | *41 / 42* | *0.73 / 0.73* | *20.45 / 20.93 (lowest 18.05 / 16.48)* | | |

## Decision

**Rule: no tested rate landed in the band, so the outcome is "no answer". The question stays open and no further rates were added.** All three permitted midpoints were used.

## What the numbers show (exploratory)

These are not a verdict, because no rate met the rule.

- **Sharp threshold.** Activity climbs from 63 at 30 Hz to 139 at 38.75 Hz, then jumps to 197 by 40 Hz, and on to 260 at 50 Hz and 357 at 75 Hz. The band falls inside that jump, which is why the search missed it.
- **The real brain's spread is lower on both sides of the target.** At 139 and 197 neurons firing, its spread (7.2 and 14.2) is below every shuffled brain in the band (lowest 16.5). That is the opposite of step 6a. It suggests that the "real is less focused" result in 6a came from activity level, not from routing.
- **That reading has its own limit.** The match is on whole-brain neurons firing only. At these inputs the real brain's descending neurons fire about 8 to 17 times less than the shuffles' (0.04–0.09 Hz vs 0.73 Hz), and MN9 almost stops. So activity matched across the brain is not matched at the output. A brain sitting just above threshold will show a small spread partly because little reaches the output at all.
- **Spread is unstable near threshold.** It moves from 8.3 to 7.2 to 14.2 across three neighbouring rates. With a change this steep, spread alone is a weak measure here.

## Reading

The real brain's result depends strongly on input level: spread runs from about 4 to 34 as input rises, with a threshold near 40 Hz. Shuffled brains were only measured at 150 Hz, so their own input curves are unknown. The fair next comparison would be whole curves, real and shuffled, not one point. That would be a further experiment.

## Files

`exp06c_real_rates.csv`, `exp06c_plan.md`, `logs/exp06c.log`.
