# Step 6 plan — the same test in the Shiu et al. 2024 spiking model

Written 29 Oct 2026 IST, before any step 6 shuffled brain was simulated. The only step 6 number seen at the time of writing is the wall time of one trial on the real brain (the timing checkpoint).

## Question

Does the real brain's focus (signal reaching few descending neurons) also show up in Shiu's published leaky integrate-and-fire model, the way it did in our rate model (steps 1 and 5)?

## Networks

- Real: their `Connectivity_783.parquet`, unchanged.
- Inside-only degree-preserving and inside-only block-preserving: the same `flynull` shuffles as step 1. The boundary (sensory → anything, anything → descending) is recomputed on their edge list and kept fixed. Dale's law is kept: an edge's sign follows its presynaptic neuron.
- Standard degree-preserving: reported alongside, not part of the rule.
- Seeds `1000 + r − 1`, 10 swaps per edge, as in step 5.

## Run

Sugar neurons are excited: their published list of 21 right-hemisphere labellar sugar GRNs, restricted to the 20 present in v783 (720575940620900446 has no v783 counterpart). They are excited at their default rate, with their default parameters, 1 s per trial. Each brain gets 3 trials and its rates are averaged; their own first 3 trials match their 30-trial mean (REPRODUCTIONS.md).

## Measure

The measure is the spread over descending neurons: the participation ratio of the descending firing-rate profile (`participation_ratio` in `experiments/rewire_shiu_run.py`, the same definition as step 1's spread). Lower = more focused.

## Decision rule (one exit)

**Focus replicates in the spiking model = yes** if the real brain's spread is lower than both inside-only types' at p < 0.05, with p = (1 + brains with spread ≤ real) / (N + 1). Otherwise **no**.

The rule only works if N ≥ 19 per inside-only type, since a smaller N cannot reach p < 0.05. N per type is set from the timing checkpoint, recorded here before the run, and not changed afterwards.

N per type, fixed 29 Oct 2026 ~11:00 IST, before launch:

- inside-only degree: **50**
- inside-only block: **50**
- standard: **19**

This gives a p floor of 1/51 ≈ 0.02 for the rule.

Timing checkpoint (real brain, one trial, Brian2 numpy target, no compiler): 139 s, about 2.6 GB per simulation process, 3 trials run in parallel. Driver: `experiments/exp06_shiu_spiking.py`.

Scope limits fixed beforehand:
- The boundary is our step 1 boundary (FlyWire sensory channels of ≥ 50 neurons, plus all descending neurons), mapped onto their neuron index; all 138,639 of their neurons are in our annotation.
- Their edge list keeps every synapse count, including 1-synapse edges, so it is not our ≥ 5-synapse graph; the shuffles are done on their graph as it is.

## Checks (every brain)

- Degree (or block) invariants are preserved.
- Inside-only brains leave every boundary edge untouched.
- If either check fails, that brain is not simulated.

## Correction, 30 Oct 2026

This plan first said "their default 200 Hz". Their default (`r_poi` in `model.py`) is 150 Hz. The run used their unmodified default parameters, so all step 6 results are at 150 Hz, as the plan's "default parameters" intended; only the stated number was wrong. Found after the run while planning step 6b.
