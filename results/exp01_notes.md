# Experiment 1 — routing vs gross dynamics in the adult connectome

Run 2026-09-18. FlyWire v783, 139,255 neurons, 2,700,513 edges (min 5 synapses), signed by predicted neurotransmitter.

**Question.** The larval result (arXiv:2606.17745) says degree and weight statistics govern gross dynamics, while exact wiring governs input routing. Does that hold in the adult brain, where every game demo and embodied model operates?

**Design.** Frozen leaky-tanh rate operator, no fitted single-neuron parameters. Drive each of 7 annotated sensory classes; read out on the 1,305 descending neurons. Compare the real connectome against surrogates that each destroy one property.

**Critical methodological step.** Spectral-radius normalisation alone is NOT enough. Before calibration the rewired network ran at 71% of neurons active versus 5% for the real one, so its apparent routing collapse (−57%) was mostly hyperactivity. After calibrating gain to a matched operating point, all three networks sit at 1.74% active and dimensionality 2428.

## Result (1 replicate, 2 swaps/edge — preliminary)

| Network | Channel separation | Specificity (DNs carrying the signal) | Dimensionality | Active fraction |
| --- | --- | --- | --- | --- |
| Real | 0.985 | 17.1 | 2428.0 | 1.74% |
| Weight shuffle | 0.976 (−0.9%) | 20.6 | 2428.1 | 1.75% |
| Degree preserving | 0.799 (−18.9%) | 131.7 | 2428.7 | 1.74% |

**Reading.** At matched excitability and matched dimensionality, the real connectome routes each sensory channel onto ~17 of 1,305 descending neurons. Degree- and weight-matched rewiring spreads the same signal over ~132 — a **7.7× loss of focus** — while every gross measure is unchanged. Shuffling weights over the real topology costs almost nothing, so it is the wiring, not the weight-topology alignment, that focuses the signal.

**If it survives replication**, the two-audience claim holds: frozen-reservoir demos (chess, Tetris) read gross dynamics that any degree-matched rewiring reproduces, while the sensory-to-descending routing that embodied models depend on is destroyed by the same rewiring.

## What is NOT yet established

1. **n = 1 per generator.** No statistics. Needs ~20 replicates per surrogate.
2. **Under-mixed.** 2 swaps per edge; standard practice is 10+. Edge overlap was already 0.017, but mixing should be shown to have converged.
3. **Dimensionality equality is partly circular** — calibrating on active fraction pins it. An independent gross measure (memory capacity, transient amplification) is needed before claiming "gross dynamics are preserved".
4. **One operating point** (1.74% active) and one threshold (1e-3). Both need a sweep.
5. **`block_preserving` not yet run** — it is the informative middle rung: if block-preserving rewiring keeps routing, then coarse projection structure suffices and exact wiring is not needed.
6. Modulatory transmitters treated as excitatory; ~14% of neurons have no predicted transmitter.

## Next

- Replicates + bootstrap CIs; mixing-convergence check.
- Add `block_preserving`.
- Add a calibration-independent gross measure.
- Then: reproduce one public chess/Tetris pipeline and test whether its score moves under the same surrogates.
