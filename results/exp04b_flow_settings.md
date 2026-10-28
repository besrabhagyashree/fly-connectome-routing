# Exp04b: information-flow settings behind Stürner et al. 2025's DN ranks

Written 2026-10-27, before Step 4b. Read-only research: no model was run.

## Where the ranks come from (the chain)

Stürner et al. did **not** run the traversal themselves. They took FlyWire's published flow ranks and averaged them by DN type.

- Stürner et al. 2025, Nature 643:158, Methods: "The information flow ranking previously reported for FlyWire [ref 2] was subsetted for DNs and averaged by DN type." "The information flow analysis is based on an algorithm implemented in a previous study [ref 40]." Ref 2 = Dorkenwald et al. 2024, Nature 634:124. Ref 40 = Schlegel et al. 2021, eLife 10:e66018. ([PMC12222017](https://pmc.ncbi.nlm.nih.gov/articles/PMC12222017))
- Stürner Fig. 3 legend: "The ranks, ranging from 1 to 12, taken from a previous study, are defined as the traversal distances from a given sensory modality to each DN and then averaged by type. Low rank indicates a more direct connection."
- Stürner Results: the analysis "excluded four types of DN that are themselves sensory neurons (sensory descending, SD)".
- The code that produced the FlyWire ranks is **not public**. The Stürner repo ([flyconnectome/2023neckconnective](https://github.com/flyconnectome/2023neckconnective)) only ships the finished table (`code/DN_ranking_df_783_sensory_combined_byDNtype.tsv`) and reads it in `code/2_FAFB_DNs.Rmd` lines 126–129. Dorkenwald's code links (CAVE, Codex, seung-lab/FlyConnectome) contain no traversal script.

## Spec table

| # | Setting | Value | Source |
|---|---|---|---|
| 1 | Algorithm | navis `TraversalModel` (Monte-Carlo), from Schlegel et al. 2021 | Dorkenwald 2024 Methods, "Rank analysis and information flow": "We used the information flow algorithm implemented by Schlegel et al. (https://github.com/navis-org/navis)" |
| 2 | navis version | 1.5.0 | Dorkenwald ref 128: "navis-org/navis: version 1.5.0. Zenodo doi:10.5281/zenodo.8191725"; Stürner Code availability also lists navis v1.5.0 |
| 3 | Connectome | FlyWire FAFB v783 (Stürner); Dorkenwald uses the v783 public release | Stürner Methods "in the 783 FAFB version"; table file name `..._783_...` |
| 4 | Synapse threshold | > 4 synapses per connection (i.e. ≥ 5) | Dorkenwald Methods, "Connection threshold": "For all the analyses presented in this paper, save for synapse distributions, we employed a consistent threshold of >4." |
| 5 | Edge weight | Synapses i→j divided by total input synapses of j; each edge tested on its own weight | Schlegel 2021 Methods (graph traversal): probability uses w_ij / Σ_k w_kj. navis code tests each edge separately (navis 1.5.0 `network_models.py` L272–288) |
| 6 | Probability function | Linear in edge weight, 0 at 0, 1 at ≥ 0.3: `p = clip(w/0.3, 0, 1)`; traverse if `p >= U(0,1)` | Dorkenwald Methods: "increased linearly with the fraction of synapses it receives from already traversed neurons up to 30% and was guaranteed above this threshold". navis 1.5.0 `linear_activation_p` L511–533, `random_activation_function` L556–562, `random_linear_activation_function` L567–587 (default `max_w=.3`) |
| 7 | Step semantics | Seeds = layer 1. Each step tests every edge from a traversed to an untraversed node. Failed edges stay and are re-tested next step. Edges whose target is already traversed are dropped. | navis 1.5.0 `TraversalModel.run` L241–312 (esp. L272–279) |
| 8 | Runs | "For each modality we performed 10,000 runs, which were averaged." | Dorkenwald Methods, "Rank analysis and information flow" |
| 9 | Per-neuron layer | Mean of the traversal step over runs (`layer_mean`) | Schlegel 2021: "use the mean over 10,000 runs to calculate its layer"; navis 1.5.0 `make_summary` L222–239. Confirmed by the table's fractions (see note A) |
| 10 | Seed groups (Dorkenwald) | ORNs, gustatory receptor neurons, mechanosensory JO, head and neck bristle, mechanosensory taste peg, thermosensory, hygrosensory, VPNs, visual photoreceptors, ocellar photoreceptors, ascending neurons; plus combined seeds | Dorkenwald Methods, "Rank analysis and information flow" |
| 11 | Columns in the published table | gustatory, hygrosensory, mechanosensory, mechanosensory_auditory, _eye_bristle, _head_bristle, _jo, _taste_peg, ocellar, olfactory, thermosensory, visual_projection, visual (13) | local `data/external_tables/sturner2025/DN_ranking_df_783_sensory_combined_byDNtype.tsv` |
| 12 | Aggregation to DN type | Arithmetic mean of per-neuron `layer_mean` over neurons of the type. No re-ranking, no rounding. | Stürner Methods "averaged by DN type"; checked locally: a 1-neuron type has values k/166, a 2-neuron type k/332, a 4-neuron type k/664 |
| 13 | DNs excluded | Sensory descending (SD) types removed before plotting/clustering | Stürner Results; `2_FAFB_DNs.Rmd` L128 drops `cluster == "sensory descending"` |
| 14 | Max steps | Not stated. navis 1.5.0 default is 15 | navis 1.5.0 `TraversalModel.__init__` L177. Table max ≈ 11, so 15 would not truncate DNs |
| 15 | Random seed | Not stated. navis sets none (global `np.random.rand`) | navis 1.5.0 L556 |

### Note A. The fractions point to 166 runs, not 10,000

- Every single-neuron DN value in the table is an integer over 166 (e.g. 625/83 = 7.530). Two-neuron types are over 332, four-neuron types over 664.
- A mean over 10,000 independent runs would give denominators dividing 10,000. 83 is prime, so it cannot.
- A few values have denominator 166 × 165. That is a mean over 165 runs: the neuron was missed in one run. So `layer_mean` counts only the runs that reached the neuron.
- 166 = int(10,000 / 60). navis 1.5.0 `run_parallel` gives each of `n_cores` workers `int(iterations/n_cores)` runs (L65). With `multiprocessing` fork on Linux, every worker inherits the same NumPy global RNG state. All workers would then return identical runs. 60 identical copies of 166 runs give exactly this pattern.
- This is an inference from the numbers plus the code, not a stated fact. Either way, **their per-neuron layers carry the Monte-Carlo noise of about 166 runs**, not 10,000.

### Note B. navis API now vs 1.5.0

- Current release is navis 1.12.0 (2026-07-13). `TraversalModel`, `linear_activation_p`, `random_linear_activation_function` keep the same names, defaults (`max_steps=15`, `max_w=.3`) and logic.
- Change: 1.5.0 builds one array from `[source, target, weight]` (L250). With 18-digit FlyWire root IDs plus float weights, the IDs become float64 and lose precision. HEAD splits the columns. Using small integer node indices avoids this in either version.
- `BayesianTraversalModel` is a deterministic approximation and was corrected later (changelog, #194). It is **not** what Dorkenwald used. Do not use it for the reproduction.

## Open questions (not stated anywhere I could find)

1. **Exact seed definitions.** The table's columns do not match v783 `classification.csv` one-to-one. v783 has no `jo` sub_class (it has `auditory` and `wind_gravity`). The columns probably follow an earlier annotation release. Which root IDs were in each seed set is unknown.
2. **What "mechanosensory" means.** Is it all `class == mechanosensory`, or the combined seed set? The five SD types score exactly 1.0 there, so they were seeds. In v783 DNx01/DNx02 are `unknown_sensory`, not mechanosensory. Annotation release again differs.
3. **visual vs visual_projection vs ocellar.** Probably photoreceptors (`sub_class photo_receptor`), `super_class visual_projection`, and `sub_class ocellar`. Not stated. Our `SENSE_TO_STURNER` maps `bilateral` → `visual_projection`; that is only a subset of VPNs.
4. **Graph scope.** Dorkenwald Fig. 6a says the model was applied "to the connectome of the central brain neurons". Photoreceptor seeds need the optic lobe. Were optic-lobe neurons kept as traversable nodes?
5. **Normalisation denominator.** Total input of j over all synapses, over synapses after the >4 threshold, or over only neurons in the graph? Schlegel 2021 used the graph's own edges; FlyWire is not stated.
6. **Threshold unit.** ">4" per neuron pair (summed over neuropils) or per Codex neuropil row? Probably per pair. Not stated.
7. **Max steps.** Default 15 assumed but not stated.
8. **Effective runs.** 10,000 stated; the numbers show 166 (Note A). Whether the 60 workers were truly identical cannot be proven from the table.
9. **"sensory_combined".** The name likely means "all modality tables combined into one file". It may instead mean a combined seed. Not stated.
10. **Type grouping.** DNg06 appears twice (clusters 14 and 16) with different values. So rows are type × cluster, not pure type. How DNg06 neurons were split is not stated.
11. **Unreached neurons.** `layer_mean` ignores runs that miss a neuron. Whether any DN was never reached (and dropped) is not stated.
12. **Ascending seeds and combined seeds** (Dorkenwald) are not in the table. Not needed for 4b.
13. **Match threshold.** No published criterion exists for "reproduced". The Spearman cut-off (e.g. 0.9 or 0.95) must be agreed before running, not after.

## Reproduction plan

1. Build the v783 graph: sum `connections.csv.gz` over neuropils per pair, keep ≥ 5 synapses, weight = syn / total kept input of the target. Seeds from v783 `classification.csv` for the 8 main modalities.
2. Reimplement navis 1.5.0 `TraversalModel.run` in NumPy on integer indices (per-edge test, failed edges re-tested, `p = clip(w/0.3,0,1)`, max_steps 15). Unit-test it against the navis docstring example semantics.
3. Run 10,000 runs per modality (fixed, logged seeds). Per neuron, `layer_mean` over reached runs. Average per DN type (type × cluster for DNg06). Drop SD types.
4. Match criterion per modality: Spearman ρ between our type means and the published column (the pass threshold is our choice, not published; see open question 13), plus median absolute difference in layer. Expect some scatter from their ~166-run noise.
5. If a modality misses, vary only the open choices above (seed set, normalisation denominator, optic-lobe scope, per-pair vs per-row threshold), one at a time. Report each variant. Do not tune anything else.

## Decisions (Bhagyashree, 27 Oct 2026) and first check

- **Match bar:** Spearman ρ ≥ 0.90 between our DN-type layers and the published column, for every one of the 8 main modalities. Fixed before running.
- **Seeds:** v783 classification (main version); vary the open choices one at a time only if a modality misses.
- **Implementation:** `flynull/exp04b_flow_model.py`. navis 1.5.0's loop is equivalent to a multi-source shortest path with Geometric(p) edge lengths (an edge from a traversed node is retried each step until it fires). `--selftest` compares a transcription of navis' loop with this form on a random graph: mean |difference| in per-node layer 0.015 over 3,000 runs (within Monte-Carlo noise).
- **Quick check, 200 runs per modality** (`results/exp04b_repro_quick.csv`): ρ = 0.97 gustatory, 0.91 hygrosensory, 0.93 mechanosensory, 0.92 olfactory, 0.91 thermosensory, 0.97 visual projection, 0.96 visual, 0.96 ocellar. All pass; no variant needed. Our layers are 0.1–0.65 higher on average (a level offset, not an order change). 3.6% of DNs are never reached (no input edges at ≥ 5 synapses).
- Full run with the published 10,000 runs per modality: `results/exp04b_repro_real.csv`, log `results/logs/exp04b_real.log`.
