# Step 4a — does the simulation agree with Stürner's structural map, and does the agreement survive randomisation?

Script: `flynull/exp04_sim_vs_map.py`. Run 27 Oct 2026, 17:39–19:56 IST.

## Method

- **Map:** Stürner et al. 2025, `DN_ranking_df_783_sensory_combined_byDNtype.tsv`: for every descending-neuron (DN) type, its rank (layers from each sensory modality) in the information-flow model of Schlegel et al. 2021. Lower = closer. DNg06 is listed twice (clusters 14 and 16, different ranks) and was dropped; 473 types remain, 468 of them present in FlyWire v783.
- **Simulation:** Exp01's rate model and `routing_profile`, unchanged: |steady activity| of all 1,305 DNs when one sense is driven, averaged over the DNs of each Stürner type.
- **Agreement:** Spearman ρ between type-mean activity and −rank for the sense's own modality (6 senses; "unknown sensory" has no modality). *Diagonal* = the sense's own modality has the highest ρ of Stürner's 8 main modalities.
- **Randomised brains:** the same generators and seeds as Exp01 (`1000 + k`, 10 swaps per edge): 35 inside-only degree-preserving (boundary checked for every brain) and 35 standard degree-preserving. The map is always the published real-brain map.
- **Test:** empirical p = (1 + brains with ρ ≥ real) / (N + 1); floor 1/36.

## Results

| | Mean ρ over 6 senses | Range | Senses best-matched to their own modality |
|---|---|---|---|
| Real brain | **0.647** | — | 4 / 6 |
| Inside-only (35) | 0.509 ± 0.008 | 0.490–0.525 | 4.0 / 6 |
| Standard (35) | 0.070 ± 0.013 | 0.040–0.092 | 0.9 / 6 |

No randomised brain of either kind reaches the real value (p = 1/36 for both).

Per sense (`results/exp04_summary.csv`):

| Sense | Real | Inside-only | Drop | Standard | Direct share (step 2) | Mean hops |
|---|---|---|---|---|---|---|
| Touch (mechanosensory) | 0.720 | 0.717 ± 0.001 | 0.003 | −0.087 | 27.6% | 2.01 |
| Visual projection neurons | 0.637 | 0.631 ± 0.001 | 0.005 | 0.170 | 4.2% | 2.25 |
| Taste | 0.799 | 0.657 ± 0.013 | 0.142 | −0.033 | 2.8% | 2.95 |
| Humidity | 0.430 | 0.241 ± 0.029 | 0.189 | 0.082 | 1.1% | 3.26 |
| Photoreceptors | 0.665 | 0.431 ± 0.026 | 0.235 | 0.120 | 0.19% | 3.32 |
| Smell | 0.630 | 0.379 ± 0.022 | 0.250 | 0.170 | 0.012% | 3.25 |

The real brain beats all 35 inside-only brains for **every** sense (p = 1/36 each), but by very different margins.

Humidity and photoreceptors are best-matched to a neighbouring modality (smell; visual projection neurons) in the real brain too, so the diagonal count is 4/6 throughout. Stürner's own clusters put humidity next to smell, and visual projection neurons are the photoreceptors' next layer.

## Exploratory: which senses lose their match?

Across the 6 senses, the drop under inside-only shuffling is perfectly ordered by the share of the sense's output that reaches DNs directly (Spearman ρ = −1.00), and follows the mean hop count (ρ = 0.83, p = 0.04). With n = 6 this is exploratory, not a confirmatory test.

## Reading

1. **The simulation reproduces the structural map in the real brain** (ρ = 0.65; 4/6 senses best-matched to their own modality, and the 2 exceptions go to the modality Stürner places next to them). Two independent methods, dynamic and static, agree.
2. **Standard randomisation destroys the agreement** (ρ ≈ 0.07), consistent with the boundary shortcuts found in Exp01 and Park 2026.
3. **Inside-only randomisation keeps the focus (step 1) but moves the destination.** Senses with direct routes to DNs (touch, visual projection neurons) keep their match almost exactly; senses that pass through several interior layers (smell, photoreceptors, humidity, taste) lose 18–40% of it.
4. Combined with step 1: **the boundary sets how many DNs a sense reaches; for multi-layer senses, the interior wiring sets which ones.**

## Limits

- One rate model, one map; the map's ranks are computed on the real brain only. Step 4b recomputes the map on randomised brains.
- Type-level averaging: Stürner ranks types, so single-neuron differences within a type are not tested.
- 35 brains per null; p is at its floor (1/36).
