# Step 4b — Stürner's structural map, recomputed on randomised brains

Script: `experiments/exp04b_flow_model.py`. Settings and sources: `results/exp04b_flow_settings.md`. Run 27–28 Oct 2026 (22:05 → 16:39 IST; the PC slept for ~9 h of that).

## Question

Step 4a compared our simulation with Stürner's map of the **real** brain. Under standard shuffles the agreement fell to ρ 0.07. Two readings were possible:

1. the shuffled brain's routing no longer follows its own wiring (the simulation "breaks"), or
2. the shuffled brain simply has a **different map**, and the simulation still follows it.

Step 4b separates them by recomputing the map on every shuffled brain with Stürner's own method.

## Method

- **Map model:** the information-flow model behind Stürner's ranks (Schlegel et al. 2021; navis 1.5.0 `TraversalModel`, as used by Dorkenwald et al. 2024): edges ≥ 5 synapses, weight = synapses / target's input, traversal probability p = min(w / 0.3, 1), seeds at layer 1, max 15 steps; per-neuron layer = mean over runs that reach it; DN type value = mean over its neurons.
- **Implementation:** exact shortest-path form of navis' loop (an edge from a traversed node fires after a Geometric(p) number of steps). `--selftest` matches a transcription of navis' loop (mean |difference| 0.015 layers over 3,000 runs).
- **Reproduction (bar fixed beforehand: Spearman ρ ≥ 0.90 for every one of the 8 modalities):** real brain, published 10,000 runs per modality.
- **Randomised brains:** the same 35 inside-only and 35 standard degree-preserving brains as steps 1 and 4a (seeds 1000 + k; boundary checked on every inside-only brain). Each map from 500 runs per modality; the real-brain reference also at 500 runs, so noise is matched. (Stürner's own table reflects ~166 effective runs; see settings note A.)
- **Two measures per brain:**
  - *map vs real map:* mean over 8 modalities of Spearman ρ between the brain's DN-type layers and the real brain's.
  - *simulation vs own map:* step 4a's score (mean ρ over 6 senses of simulated DN activity vs −layer), scored against that brain's own map.
- **Test:** empirical p = (1 + brains ≥ real) / (N + 1); floor 1/36.

## Results

**Reproduction.** 10,000 runs, real brain vs Stürner's published ranks (`exp04b_repro_real.csv`): ρ = 0.972 taste, 0.910 humidity, 0.931 touch, 0.924 smell, 0.917 temperature, 0.972 visual projection, 0.959 photoreceptors, 0.964 ocellar. **All 8 pass.** Our layers sit 0.1–0.7 higher on average (a level offset; the order matches). 200 runs gave the same ρ within 0.01.

**Randomised brains** (`exp04b_nulls.csv`, `exp04b_summary.csv`):

| | Map vs real map | Simulation vs own map | Senses best-matched to own modality |
|---|---|---|---|
| Real brain | 1 | **0.721** | 4 / 6 |
| Inside-only (35) | 0.572 ± 0.018 (0.531–0.602) | 0.620 ± 0.013 (0.581–0.644) | 5.0 / 6 |
| Standard (35) | 0.089 ± 0.013 (0.069–0.122) | 0.569 ± 0.015 (0.533–0.601) | 5.0 / 6 |

- No randomised brain reaches the real brain's simulation–map agreement: p = 1/36 for both types (z = 7.9 inside-only, 9.9 standard).

**Per sense, how much of the map survives** (mean ρ vs real map; sd in brackets):

| Sense | Inside-only | Standard | Direct share to DNs (step 2) |
|---|---|---|---|
| Touch (mechanosensory) | **0.913** (0.007) | 0.047 | 27.6% |
| Visual projection neurons | **0.839** (0.016) | 0.054 | 4.2% |
| Taste | 0.600 (0.040) | 0.082 | 2.8% |
| Photoreceptors | 0.516 (0.048) | 0.084 | 0.19% |
| Humidity | 0.486 (0.051) | 0.139 | 1.1% |
| Smell | 0.457 (0.049) | 0.170 | 0.012% |
| Ocellar | 0.384 (0.059) | −0.033 | — |
| Temperature | 0.376 (0.076) | 0.169 | — |

## Reading

1. **Stürner's map is reproduced** from the published settings (ρ 0.91–0.97, all 8 senses).
2. **Standard shuffles replace the map**, not the simulation. Their maps keep almost nothing of the real one (ρ 0.09), yet our simulation still follows each brain's own new map (ρ 0.57). So step 4a's drop to 0.07 was mostly a changed map.
3. **Inside-only shuffles keep about half the map** (ρ 0.57): senses with direct routes to DNs keep theirs almost whole (touch 0.91, visual projection neurons 0.84); multi-layer senses keep 0.38–0.60. This is the same pattern as step 4a, now from Stürner's own method rather than our simulation.
4. **The real wiring gives the tightest fit between simulation and map** (0.72 vs at most 0.64 in 70 randomised brains). Simulation and structure agree best in the real brain, under either kind of shuffle.

Combined with steps 1 and 4a: **the boundary sets how many descending neurons a sense reaches; for multi-layer senses, the interior sets which ones** — now shown by two independent methods.

## Exploratory (n = 6, not a confirmatory test)

Across the 6 senses with a step-2 direct share, map survival under inside-only shuffling follows the direct share (Spearman ρ = 0.94) and mirrors step 4a's per-sense drop (ρ = −0.94).

## Limits

- 500 runs per map for randomised brains (real-brain reference matched); 35 brains per type, so p is at its floor (1/36). Step 5 scales steps 1 and 4a to 200.
- Seeds from FlyWire v783 labels; Stürner's table used an earlier annotation release (settings, open question 1). The reproduction bar was still met for every sense.
- In randomised brains 5 of 6 senses best-match their own modality vs 4 in the real brain. We have not tested why; the real brain's two exceptions (humidity, photoreceptors) go to the modality Stürner places next to them (step 4a notes).
- One map model (Schlegel/Stürner flow) and one dynamic model (our rate model); the spiking-model test is step 6.
