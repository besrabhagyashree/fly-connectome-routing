# Study conclusions

Bhagyashree Besra, 31 Oct 2026. Final conclusions of this round of the fruit fly connectome routing study, including two audits ([what changed](CORRECTIONS.md)). Not peer-reviewed. A preprint draft exists; a further test may follow.

## Question

Does the exact wiring of the adult *Drosophila* brain decide where each sense reaches the descending (brain-to-body) neurons, or do simpler statistics of the connectome explain it?

## Answer

**This study does not show that exact wiring makes the brain more focused. Its main finding is that an apparent wiring effect can come from null model design and network scaling.**

- **The apparent advantage was an artefact.** The real brain looked 0.5% more focused than all 400 inside-only shuffles (p = 0.005). Run at the shuffles' effective gain, it lost that advantage (p = 0.27 and 0.34). Spectral-radius scaling caused it.
- **Inside wiring does shape which neurons a sense reaches** in the rate model: agreement with Stürner's map is 0.65 real against 0.51 and 0.52, and the radius does not explain it.
- **The spiking model does not show the real brain as more focused** at default input (34.0 vs 20.7 and 21.7). Shuffled brains fire about half as many neurons, so this result mixes focus with throughput.
- **A comparison at matched activity has not been made.** That remains the main open question.

**Main contribution:** a demonstration that a statistically strong wiring effect (p = 0.005, all 400 brains) can be a normalisation artefact, with a tested way to detect it.

## Findings

| Step | Question | Result | Standing |
|---|---|---|---|
| 1, 5 | Is the real brain more focused than inside-only shuffles? | Apparent advantage: 17.10 vs 17.19 / 17.17 (p = 0.005). Removed by step 8c | Rule fixed after the first 35 per type; artefact |
| 2 | Where do shortcuts come from? | The real brain has 466 direct sense-to-descending pairs, and inside-only shuffles keep them. *New* direct pairs appear only in standard shuffles (1,693 pairs in the one brain counted) | Descriptive, one brain per type |
| 3 | Which descending neurons does each sense reach? | 1,303 of 1,305 matched to Stürner's atlas; routing is uneven across senses | Exploratory |
| 4, 5 | Does the simulation match the published map? | ρ = 0.65 real, 0.51 / 0.52 inside-only, 0.07 standard. No shuffled brain matches the real one (p = 0.005–0.006) | No prior rule found; descriptive, rate model |
| 4b | Does the map itself survive shuffling? | Map vs real map: 0.57 inside-only, 0.09 standard (35 each; inside-only degree only). Standard shuffles replace the map | Reproduction bar (ρ ≥ 0.90) fixed first; the shuffled comparison is descriptive |
| 7 | Is separation higher in the real brain? | Apparent advantage: 0.985 vs 0.983 / 0.984 (p = 0.005). Removed by step 8c; standard 0.815 | Rule fixed after 35 brains per type; artefact |
| 6a | Is focus seen in the spiking model? | **No.** Real 34.0, inside-only 20.7 / 21.7 (p = 1.0), standard 1.7 | Confirmatory, spiking model |
| 6a | Does activity survive shuffling? | Neurons firing: real 380, inside-only about 177, standard 122 | Exploratory |
| 6a | Does the feeding readout survive? | MN9: real 75 Hz; 0 Hz in all 50 inside-only degree brains; 29.5 Hz inside-only block; 0 Hz standard. Its inputs were shuffled, and it tracks activity | Exploratory lead |
| 6b | Does matching activity reveal focus? | Rule not met. The match reached 260 neurons, not the target of 177 | Exploratory |
| 6c | Is the real brain more focused at equal activity? | **No answer.** None of 7 input rates landed in the band: activity jumps from 139 to 197 near 40 Hz. Either side of the band, the real brain's spread (7.2, 14.2) is below every shuffled brain, but its descending neurons fire about 8–17× less | New experiment after 6b; outcome no answer, numbers exploratory |
| 8a | At what gain do signals spread? | **No answer.** Direct-target share falls from 99.6% to 61% at gain 1.0, above the 50% bar | Real brain only; rule fixed first |
| 8b | Is the real brain more focused at gain 1.0? | Rule met (spread 30.2 vs 289 / 233, p = 0.02), **but not comparable:** shuffled brains saturate (82–93% active vs 33%) because the real brain's spectral radius is about 5–7× larger | New experiment after 8a. Rule met, not evidence of focus |
| 8c | Does the advantage survive at effective gain? | **No.** 17.191 vs 17.194 (p = 0.27); 17.163 vs 17.165 (p = 0.34); separation p = 0.37, 0.42 | Rule fixed first; prompted by a post hoc finding |

## What can and cannot be claimed

**Supported:**
- The 0.5% focus and 0.2% separation advantages were artefacts of spectral-radius scaling.
- Standard shuffles widen mean spread about sevenfold (ratio of means; 1.4× to 171× per sense).
- In the rate model, inside-only shuffling changes which descending neurons a sense reaches, more for smell than for touch.

**Suggested, not established:**
- New shortcuts drive the widening under standard shuffles. This rests on one rebuilt brain.
- Real inside wiring gives a spectral radius about 5–7× larger than its shuffles. Its cause has not been established.
- MN9 depends on inside wiring. Its own inputs were shuffled, so this is a lead only.
- Shuffling inside wiring reduces how much activity propagates in a fixed-parameter spiking network.
- Step 6a's result may reflect activity level more than routing.

**Not established:**
- Whether the rate-model result holds when signals actually spread through the network. No comparison has been made at a matched operating point.
- Whether the real brain is more or less focused than shuffled brains at equal activity in the spiking model. Spread mixes focus with throughput there, and the planned checks, including step 6c, did not separate them. The numbers near the target point towards more focus in the real brain, but with far less reaching the descending neurons.

## Limits

- Step 6 drove sugar neurons only; steps 1 and 5 used 7 sensory classes, step 4a scored 6 senses, and step 4b used 8 modalities.
- Steps 1–5 used connections of ≥ 5 synapses (2.7M connections); step 6 used all connections (15.1M). Step 6 read out 1,301 descending neurons, not 1,305.
- Both are simple models of a static wiring diagram, with no learning, modulation or body.
- No model was tuned brain by brain. The rate model's gain search returned its floor in every run (activity about 12%, target 5%), and step 6 used fixed parameters.
- Step 8c used one mean effective gain per type; each shuffled brain has its own.
- Every result rests on a single connectome.

## Open questions

1. Does the rate-model result hold at gains where signals spread? Step 8a gave no answer, and 8b's yes is not comparable. The fair test matches each shuffled brain to the real brain's activity.
2. Whole input-response curves for real and shuffled brains in the spiking model, compared across input levels. Step 6c tried a single point and could not land on it.
3. A planned test of which inside pathway carries sugar to MN9.

Each would be a new experiment, with its rule fixed first.

## Where the detail is

Step notes are in `results/`: `exp01_notes.md` (September preliminary run; step 1's inside-only results are in `exp05_notes.md`), `dn_labels_summary.md`, `exp04_notes.md`, `exp04b_notes.md`, `exp05_notes.md`, `exp06_notes.md`, `exp06b_notes.md`, `exp06c_notes.md`, `exp07_notes.md`, `exp08_notes.md` (8a), `exp08b_notes.md`, `exp08c_notes.md`.
