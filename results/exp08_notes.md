# Step 8 — gain sweep, stage 1

Run 30 Oct 2026 IST with `experiments/exp08_gain_sweep.py`, following `results/exp08_gain_sweep_plan.md` (approved and committed in 42ace78 before the run). Real brain only.

| Gain | Active fraction | Direct-target share | Spread | Separation |
|---|---|---|---|---|
| 0.001 | 0.122 | 0.996 | 17.10 | 0.985 |
| 0.01 | 0.126 | 0.967 | 17.24 | 0.982 |
| 0.03 | 0.134 | 0.927 | 17.59 | 0.974 |
| 0.1 | 0.158 | 0.861 | 18.80 | 0.955 |
| 0.3 | 0.214 | 0.777 | 21.27 | 0.939 |
| 1.0 | 0.326 | 0.610 | 30.16 | 0.918 |

## Decision

**Rule: the primary gain is the lowest grid gain with a direct-target share below 50% and an active fraction below 50%. No gain qualifies, so the outcome is "no answer".** As the plan says, no gains were added and stage 2 did not run. No shuffled brain was simulated in this step.

## What the numbers show (exploratory)

- **The audit's point holds.** At gain 0.001, 99.6% of descending activity sits on direct targets, and this run reproduces step 1's spread (17.0992).
- **The 0.5% result belongs to one end of a range.** As gain rises, the real brain's own spread nearly doubles, to 30.2, and separation falls to 0.918.
- **Direct connections still dominate at gain 1.0** (61%), even with a third of neurons active.
- **Still unknown:** whether inside-only shuffles differ from the real brain at higher gain. No shuffled brain has been run above gain 0.001.
- **The 50% cut-off was our choice,** and it decided this outcome. Testing at gain 1.0 would be a new experiment decided after seeing this table, and must be labelled that way.
