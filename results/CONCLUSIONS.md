# Study conclusions

Bhagyashree Besra, 30 Oct 2026. Not peer-reviewed. Covers steps 1–7 of the fruit fly connectome routing study; the preprint is still to come.

## Question

Does the exact wiring of the adult *Drosophila* brain decide where each sense reaches the descending (brain-to-body) neurons, or do simpler statistics of the connectome explain it?

## Answer

**It depends on the model, and that is the main finding.**

- In a calibrated rate model, the connections at the brain's edges set most of how focused each sense is. The exact inside wiring adds about 0.5% to focus, but it strongly shapes *which* neurons each sense reaches.
- In the Shiu et al. 2024 spiking model, the focus result does not replicate. Shuffling the inside wiring cuts activity about in half and can abolish the sugar-to-feeding response, even with every edge connection intact.

So the inside wiring cannot be called unimportant. The small effect in the rate model is partly a product of that model's gain calibration.

## Findings

| Step | Question | Result | Standing |
|---|---|---|---|
| 1, 5 | Does focus survive inside-only shuffling? | Mostly. Spread: real 17.10, inside-only 17.19 / 17.17, standard 122. Real beats all 400 inside-only brains (p = 0.005), by about 0.5% | Confirmatory, rate model |
| 2 | Where do shortcuts come from? | Direct sense-to-descending shortcuts appear only in standard shuffles | Descriptive |
| 3 | Which descending neurons does each sense reach? | 1,303 of 1,305 matched to Stürner's atlas; routing is uneven across senses | Exploratory |
| 4, 5 | Does the simulation match the published map? | ρ = 0.65 real, 0.51 / 0.52 inside-only, 0.07 standard. No shuffled brain matches the real one (p = 0.005–0.006) | Confirmatory, rate model |
| 4b | Does the map itself survive shuffling? | Map vs real map: 0.57 inside-only, 0.09 standard. Standard shuffles replace the map | Confirmatory, rate and flow models |
| 7 | Do shortcuts make behaviours leak? | Separation: real 0.985, inside-only 0.983 / 0.984 (p = 0.005, about 0.2%), standard 0.815 | Confirmatory, rate model |
| 6a | Is focus seen in the spiking model? | **No.** Real 34.0, inside-only 20.7 / 21.7 (p = 1.0), standard 1.7 | Confirmatory, spiking model |
| 6a | Does activity survive shuffling? | Neurons firing: real 380, inside-only about 177, standard 122 | Exploratory |
| 6a | Does the feeding readout survive? | MN9: real 75 Hz; 0 Hz in all 50 inside-only degree brains; 29 Hz in inside-only block brains; 0 Hz in standard | Exploratory |
| 6b | Does matching activity reveal focus? | Rule not met. The match reached 260 neurons, not the target of 177 | Exploratory |
| 6c | Is the real brain more focused at equal activity? | **No answer.** None of 7 input rates landed in the band: activity jumps from 139 to 197 near 40 Hz. Either side of the band, the real brain's spread (7.2, 14.2) is below every shuffled brain, but its descending neurons fire about 8–16× less | New experiment after 6b; outcome no answer, numbers exploratory |

## What can and cannot be claimed

**Supported:**
- Degree-preserving null models that also move the sensory and descending connections overstate how much "focus" comes from wiring. Most of the 17-vs-122 gap comes from shortcuts.
- In the rate model, the real brain beats every inside-only brain, consistently but slightly.
- The inside wiring shapes which descending neurons a sense reaches, more for multi-layer senses such as smell than for touch.

**Suggested, not established:**
- In the spiking model, the sugar-to-MN9 pathway depends on the specific inside wiring. This was not a planned test.
- Shuffling the inside wiring reduces how much activity propagates in a fixed-parameter spiking network.
- The real brain's sugar response has a sharp threshold near 40 Hz input, and its spread runs from about 4 to 34 with input. Step 6a's "less focused" result may reflect activity level more than routing.

**Not established:**
- Whether the real brain is more or less focused than shuffled brains at equal activity in the spiking model. Spread mixes focus with throughput there, and the planned checks, including step 6c, did not separate them. The numbers near the target point towards more focus in the real brain, but with far less reaching the descending neurons.

## Limits

- Step 6 drove sugar neurons only; steps 1–5 used 7 sensory classes.
- Steps 1–5 used connections of ≥ 5 synapses (2.7M); step 6 used all synapses (15.1M).
- Both are simple models of a static wiring diagram, with no learning, modulation or body.
- Shuffled brains were not re-tuned in step 6, while the rate model calibrated every brain's gain.
- Every result rests on a single connectome.

## Open questions

1. Whole input-response curves for real and shuffled brains in the spiking model, compared across input levels. Step 6c tried a single point and could not land on it.
2. A planned test of which inside pathway carries sugar to MN9.

Either would be a new experiment, with its rule fixed first.

## Where the detail is

Step notes are in `results/`: `exp01_notes.md`, `dn_labels_summary.md`, `exp04_notes.md`, `exp04b_notes.md`, `exp05_notes.md`, `exp06_notes.md`, `exp06b_notes.md`, `exp06c_notes.md`, `exp07_notes.md`.
