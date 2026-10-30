# Corrections after the audit, 30 Oct 2026

A read-only audit recomputed the results behind `CONCLUSIONS.md` and the step 6 notes. The numbers matched. These claims and labels did not, and each has been corrected.

## Main correction

**The rate model's gain calibration never took effect.** `calibrate_gain` returns its lower limit at once if activity there is already above the target. It always was. Gain is 0.001 in all 638 rate-model runs, and activity is 12.2–12.5%, not the 5% target. The driven sensory neurons alone are 12.2% of the brain, so 5% could not be reached.

Consequences:

- Every statement that gain was calibrated, or that brains ran at a matched operating point, was wrong. This includes "dimensionality ≈ 2,428, 1.74% active in every brain": those figures describe the driven neurons.
- At gain 0.001 recurrence is negligible. In the real brain, each sense's spread nearly equals the spread of its direct sense-to-descending weights (Pearson r = 0.99997 over 7 senses; 97.5–99.99% of activity sits on direct targets).
- Inside-only shuffles hold those direct connections fixed by design. So "edges set the focus, inside wiring adds about 0.5%" may be largely built in, not a discovery. Step 7's small inside-only effect may be affected in the same way. Neither has been tested.
- Step 4a's ranks rest on the small multi-step part of the signal and may be less affected. That is also untested.

Next test: `exp08_gain_sweep_plan.md`.

## Other corrections

| Where | Was | Now |
|---|---|---|
| Step 2 | Shortcuts appear only in standard shuffles | The real brain has 466 direct pairs; *new* ones appear only in standard shuffles, counted in one brain per type |
| Steps 4, 4b | Confirmatory | No prior rule found for the comparison with shuffles; descriptive. 4b's reproduction bar (ρ ≥ 0.90) was fixed first |
| Steps 1/5, 7 | Confirmatory, "pre-registered" | Rule fixed after 35 brains per type were seen; confirmatory only for the 165 added |
| Step 7 plan | "before any leakage number was computed" | Separation at 35 brains was already on disk |
| Step 6a | No descending neurons fired in one standard brain | Two (r = 9 and 15) |
| Step 6a | Shuffling "halves what gets through" | Halves neurons firing; descending output falls by about a third |
| Step 6 limits | "all synapses (15.1M)" | 15.1M connections, which hold 54.5M synapses. Readout was 1,301 descending neurons, not 1,305 |
| Steps 1–5 | "7 sensory classes" | 7 in steps 1 and 5, 6 in 4a, 8 in 4b |
| 6b notes | The study concludes, 6c not run | 6c was later reopened as a new experiment |
| 6b, 6c notes | Run ended about 21:35 / 22:00 | 21:19 / 21:54 |
| 6c notes | "about 8–16×" | About 8–17× |
| 6c notes | Activity "rises slowly" to 38.75 Hz | 63 at 30 Hz to 139 at 38.75 Hz, then a jump to 197 |
| Step 6, 6b plans | Stated times of ~11:00 and ~21:10 | Committed 10:42:43 and 21:04:01. Each still came before its first simulation |

## Unchanged

All 120 step 6 brains and every 6b and 6c level recompute from the raw spike files. The step 6, 6b and 6c rules were applied as written, and their plans were committed before their runs. Statistics for steps 1, 4, 5 and 7 match their result files.

Not rechecked by the audit: run-history details such as sleep windows, the 21-to-20 sugar neuron mapping, and step 7's exploratory table.
