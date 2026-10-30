# Step 6 — the focus test in the Shiu et al. 2024 spiking model

Run 29–30 Oct 2026 IST with `experiments/exp06_shiu_spiking.py`, following `results/exp06_plan.md` (rule and N committed in e027887 before any shuffled brain was simulated). Real brain 29 Oct 10:47; last shuffled brain 30 Oct 19:24 IST.

## Main test (confirmatory): spread over descending neurons

Sugar neurons driven at 150 Hz (their default `r_poi`; the plan first misstated this as 200 Hz, see its correction), 3 trials of 1 s per brain, Shiu's default parameters, their full v783 edge list (15.1M connections). Spread = participation ratio of the descending-neuron rate profile; lower = more focused. p = (1 + brains with spread ≤ real) / (N + 1).

| Network | N | Spread, mean ± SD | Range | Brains ≤ real | p |
|---|---|---|---|---|---|
| **Real** | 1 | **34.01** | | | |
| Inside-only, degree | 50 | 20.66 ± 2.00 | 18.05–31.52 | 50 | 1.0 |
| Inside-only, block | 50 | 21.73 ± 3.44 | 16.48–33.32 | 50 | 1.0 |
| Standard (reported alongside) | 19 | 1.69 ± 0.85 | 0.00–3.00 | 19 | 1.0 |

**Rule: real spread lower than both inside-only types at p < 0.05. Not met: the answer is no.** The focus result of the rate model (steps 1 and 5) does not replicate in this spiking model. The difference is in the opposite direction: the real brain has the largest spread of all 120 brains.

Checks: degree and block invariants held in all 119 shuffled brains; inside-only brains left every boundary connection untouched (100/100); no brain was simulated twice.

## Why this "no" must be read with care

These are context for the verdict, not a change to it.

1. **The measure mixes focus with throughput here.** The rate model was meant to calibrate each brain's gain to a 5% active fraction, but the search returned its floor in every run (see `CORRECTIONS.md`). Shiu's model runs at fixed published parameters, so shuffled brains also carry less activity (table below). A weaker signal reaching fewer neurons gives a lower spread without being better routed. The test as planned cannot separate the two, and the plan did not anticipate this.
2. **One sense, not seven.** This test drives sugar neurons only; steps 1 and 5 averaged 7 sensory classes. The two spreads (34 vs 17) are not directly comparable.
3. **Different graph.** Shiu's edge list keeps every synapse count; steps 1–5 used connections with ≥ 5 synapses.
4. **The real brain is one estimate from 3 trials,** as are the shuffled brains. The real value is 34.0; the nearest shuffles reach 31.5 and 33.3.

## Exploratory (not confirmatory; noticed during the run, not in the plan)

These measures were recorded for every brain, but they were read as the run went on and no decision rule was set for them. Treat them as leads.

| Network | N | Descending neurons firing | Whole-brain neurons firing | DN mean rate (Hz) | MN9 rate (Hz) |
|---|---|---|---|---|---|
| **Real** | 1 | **68** | **380** | **1.13** | **75.3** |
| Inside-only, degree | 50 | 40.9 ± 4.1 | 176 ± 13 | 0.74 ± 0.07 | 0 in 50/50 |
| Inside-only, block | 50 | 43.5 ± 6.3 | 179 ± 17 | 0.75 ± 0.09 | 29.5 ± 6.4 (2–41); fires in 50/50 |
| Standard | 19 | 2.5 ± 1.4 | 122 ± 12 | 0.008 ± 0.008 | 0 in 19/19 |

- **Throughput falls.** No shuffled brain reaches the real brain's whole-brain activity (highest 233 vs 380). Inside-only shuffles fire about half as many neurons, though the sensory input and all boundary connections are unchanged.
- **The feeding pathway depends on inside wiring.** MN9 is the motor neuron Shiu et al. use as the readout of sugar-evoked feeding. It fires at 75 Hz in the real brain, is silent in all 50 inside-only degree brains, and fires at less than half the real rate in inside-only block brains. Keeping each neuron's connections within its super-class keeps part of the pathway; keeping only degrees does not.
- **Standard shuffles nearly silence the output.** About 2.5 descending neurons fire, and none in two brains. In the rate model these shuffles spread the signal about 7× wider instead. A likely reason, not tested here: activity spread thinly over many shortcuts stays below spiking threshold.

## Reading

Across the two models the same shuffles have different effects. In the rate model as run (gain 0.001, almost no recurrence) the boundary sets most of the focus and the inside wiring adds about 0.5%. In the fixed-parameter spiking model, shuffling the inside wiring roughly halves the neurons firing, cuts descending output by about a third, and removes the sugar → MN9 response, even with the boundary intact. So the conclusion from steps 1 and 5, that the inside wiring matters little for routing, depends on the model and may reflect its very low gain. It should not be stated without that qualifier.

What this step does not show is that the real brain is less focused than shuffled brains in any useful sense, because of point 1 above. A cleaner comparison would equalise throughput across brains first (for example calibrating input rate per brain). That is a new experiment and would need its own rule fixed in advance.

## Run record

- **Timing checkpoint:** 139 s for one trial without a C++ compiler (Brian2 numpy target).
- **Sugar neurons:** 20 of the published 21; 720575940620900446 has no v783 ID.
- **Run history:** the first run died with a session restart (only the real brain was kept); relaunched as 3 detached drivers. A free-RAM guard set too high stalled two drivers on 29 Oct from 14:13 and 14:33 until 14:52 IST. The PC slept 23:33–06:29 and 17:35–18:11 IST; drivers resumed. On 30 Oct the remaining brains moved to claim-file drivers.
- **Code change during the run:** `_sorted_lookup` in `flynull/nulls.py` (0783ae2) gives bit-identical shuffles (16 of 16 old-vs-new comparisons, full test suite including the brain #1 regression). Seeds, swaps and N were not changed.
- **Trials ran one after another** rather than in parallel, to fit memory; this does not affect results.

## Files

`exp06_all_brains.csv` (one row per brain), `exp06_summary.csv`, `exp06_plan.md`, `logs/exp06_*.log`. Per-brain spike files stay local (`results/exp06/`, not in git).
