# fly-connectome-routing

**Does the fruit fly brain's exact wiring decide where sensory signals reach the body-command neurons, or do its connection statistics alone explain it?**

Bhagyashree Besra · independent research · started September 2026

> **Status: preliminary.** Results below are from work in progress. The key control (step 1, inside-only shuffles) is still running, and its first quick test changes how the earlier result should be read. Nothing here is peer-reviewed.

## The question

The adult *Drosophila* connectome (FlyWire v783: 139,255 neurons, 2.7M connections with ≥5 synapses) is now used as a network architecture in simulations, embodied models and reservoir-computing demos. A claim that "the connectome does X" needs a fair baseline: randomised brains that keep every neuron's number of connections but rewire the edges.

We drive each of 7 sensory classes through a frozen leaky-tanh rate model, calibrated so the real and randomised brains run at the same activity level, and measure how widely each signal spreads over the 1,305 descending (brain-to-body) neurons.

## Results so far

| Comparison | Spread over descending neurons (participation ratio) | Separation between senses | Status |
|---|---|---|---|
| Real brain | 17.1 | 0.985 | done |
| Standard degree-preserving shuffle | ~122 (35 replicates) | 0.817 | done |
| Standard block-preserving shuffle | ~101 (35 replicates) | 0.883 | done |
| **Inside-only shuffle** (sensory-out and descending-in edges locked) | **17.2** (1 replicate, quick test) | 0.983 | 35 + 35 replicates running |

Overall activity (dimensionality ≈ 2,428; 1.74% active) is the same in every brain.

**Reading so far:** standard shuffles create one-hop shortcuts from sensory neurons onto descending neurons (smell → descending share 0.012% real vs 3.2% after shuffling). When the shuffle keeps those boundary connections fixed, the first test shows no loss of focus. If the full run confirms this, the routing is set at the brain's sensory and motor boundaries rather than by its interior wiring. That independently supports Park (2026) at full single-neuron scale and across 7 senses.

**Other results**
- **Shiu et al. 2024 spiking model reproduced** (Pearson r = 0.99 over 386 neurons against their published rates). See [REPRODUCTIONS.md](REPRODUCTIONS.md), including an open discrepancy in directly stimulated neurons.
- **Descending-neuron identities.** 1,303 of 1,305 matched to Stürner et al. 2025. Each sense concentrates on descending neurons that Stürner's independent structural map also assigns to that sense. Links to specific behaviours are mostly not reproduced by this rate model. See `results/dn_labels_summary.md`.

## Plan

1. Inside-only shuffle test (running)
2. Shortcut statistics per sense (first table done)
3. Descending-neuron behaviour labels (done, exploratory)
4. Simulation vs Stürner's structural map
5. Scale to 200 shuffles per type
6. Shiu spiking model on an inside-only rewired brain
7. Cross-behaviour leakage under shortcuts

Gaps in the literature and the reasoning for each step: [LITERATURE_GAPS.md](LITERATURE_GAPS.md).

## Closest prior work

- Therianos 2026, arXiv:2606.17745: larval connectome; exact wiring governs input routing
- Park 2026, arXiv:2609.39248: null-model choice at the sensory-motor boundary decides connectome comparisons
- Dhiman 2026, arXiv:2604.04033: flyvis advantages vanish under degree-preserving nulls
- Shiu et al. 2024, Nature: whole-brain spiking model
- Stürner et al. 2025, Nature: descending-neuron atlas
- Lin et al. 2024, Nature: network statistics against null models

Full reading list: [PAPERS.md](PAPERS.md).

## Repository layout

```
flynull/       analysis code: data loading, null models, rate model, measures, experiments
results/       small result tables, summaries and figures
REPRODUCTIONS.md     what has been reproduced against published numbers
LITERATURE_GAPS.md   prior work and required changes
```

Not included: FlyWire data, paper PDFs, third-party repositories and large intermediate files.

## Reproducing

1. Download the FlyWire v783 Codex tables (`neurons`, `connections`, `classification`, `consolidated_cell_types`) from https://storage.googleapis.com/flywire-data/codex/data/fafb/783 into `data/flywire783/`.
2. Python 3.11 with numpy, scipy, pandas.
3. Run, for example:
   ```
   python flynull/exp01_routing_vs_gross.py --generators interior_degree_preserving --n-nulls 35 --swaps-per-edge 10 --tag _C1
   ```

## Data and licence

FlyWire data is CC BY-NC 4.0. Cite Dorkenwald et al. 2024 and Schlegel et al. 2024. Descending-neuron annotations are from Stürner et al. 2025. The code in this repository is MIT-licensed (see [LICENSE](LICENSE)).

## Note on tools

AI coding assistants (Claude Code) helped write the analysis code and literature summaries. Study design decisions, checks against published numbers and interpretation are the author's responsibility.
