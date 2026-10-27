# Literature gaps and required changes (2026-10-27)

Prior work, what it leaves open for us, and what our Experiment 1 must change. Figures were read from the papers' full text through paraphrasing extraction. Re-check any number against the original before citing it.

## Closest prior work

| Paper | What it claims | What it leaves open |
|---|---|---|
| Therianos, arXiv 2606.17745 (larva) | Frozen leaky-tanh operator. Degree and weight govern gross dynamics; exact wiring governs input routing. Real 19.9% of core active vs 66.8% rewired, 39.2% block-null. Confinement split 41% degree/weight, 34% class, 24% placement. 1,000 nulls. | Larva only, unsigned weights, no DN readout, no spiking model. Exp01 was designed as its adult test. |
| Park, arXiv 2609.39248 | Standard nulls create sensory→DN shortcuts: olfactory→DN share 10.6–10.7% vs 0.012%, median 1 hop vs 3. Null choice at the sensory-motor boundary decides the comparison. Interior-only nulls (N4/N5) remove the shortcuts. Shortcuts *raise* foraging fitness (+0.44). | Compressed to 512 groups, olfaction only, no DN specificity, no spiking model, no behaviour mapping. Found no interior-wiring advantage on fitness. Code: github.com/gyujeongion/flyconnectome-nulls |
| Dhiman, arXiv 2604.04033 | flyvis connectome advantages vanish under fair initialisation and degree-preserving nulls. | One task, 5–10 training steps, 3 seeds, no tests, 0.17 swaps/edge, ignores sign/Dale's law, no routing measure. |
| Shiu et al. 2024 | LIF model, 91% of 164 predictions validated. Their null was a weight shuffle: MN9 activated in 100% real vs 1/100 shuffled. | No degree- or block-preserving null. |
| Stürner et al. 2025 | FAFB DNs clustered by sensory-input rank (Dorkenwald flow model), 16 clusters. | Topological only, no dynamics, no null. |
| Lin et al. 2024 | Static network statistics vs ER, configuration and spatial nulls. | No dynamics, no sensory→DN test. |
| FlyGM 2602.17997, Cho 2610.10014 | Real wiring beats degree-preserving rewires on control tasks. | No per-sense DN specificity. |

## Required changes to Exp01 (in priority order)

1. **Boundary-preserving nulls (critical).** Rewire interior edges only. Keep every sensory-out and DN-in edge bit-identical, as in Park's N4/N5. If the real wiring still reaches far fewer DNs than these nulls, the result is about interior routing and survives Park's critique. If not, it is the shortcut effect Park already reported.
2. **Path statistics per sense and per null.** Report the direct sensory→DN weight share and hop distribution for all 7 senses. Park found vision goes the opposite way (connectome 0.38 vs nulls ~0.11).
3. **Fix the Shiu rewired file before running it.** `Connectivity_783_rewired.parquet` was rewired over all edges, so it likely contains the shortcuts. Rebuild it interior-only.
4. **More replicates.** p = 1/36 is the floor at N=35; Therianos used 1,000. About 4 min per rewire+run at full scale makes 1,000 × 2 nulls roughly 130 h, so 200 per null (p floor 1/201, about 27 h per null) is a practical target. Use p = (1 + exceedances)/(N + 1).
5. **Report controls Dhiman lacked:** swaps per edge, edge overlap, spectral radius per surrogate, and sign/Dale's-law preservation.
6. **Adopt Therianos' decomposition:** degree/weight vs class architecture vs within-class placement.
7. **Robustness:** synapse threshold sweep (≥5 already used; try ≥10), and Lin's spatial null as a third null.

## Opportunities (ranked)

1. **The adult, signed, DN-level generalisation of Therianos,** with boundary-preserving nulls. This is our main contribution.
2. **Behavioural validation.** Join our ~17 DNs per sense to Stürner `Supplemental_file5_FAFB_DNs.tsv` on `root_id`, then add behaviours from Cande 2018, Braun 2024 and Cheong (MDN, DNp01, DNp09, aDN1/2, DNg11/12…).
3. **Dynamic routing vs topological prediction.** Compare our per-sense DN sets with Stürner's sensory-rank clusters. Nobody has nulled the flow model.
4. **Shiu ground truth under strict nulls.** Gustatory→MN9 and JO→aDN1/aDN2 on an interior-only rewired LIF model. This upgrades their 1/100 weight-shuffle control.
5. **An answer to Park's puzzle.** If shortcuts help foraging, why does the brain avoid them? Test whether nulls create cross-behaviour leakage (feeding signals reaching grooming or escape DNs). That would be a cost Park's single-task world could not see.

## Limitation to state

VNC-side DN→DN axo-axonic interactions (Ceballos 2026, MANC) mean DN outputs are not independent downstream. FlyWire is brain-only.

## Data sources

- Stürner DN table: github.com/flyconnectome/2023neckconnective (`Supplemental_file5_FAFB_DNs.tsv`, `Supplemental_file4_DN_identification.tsv`)
- FlyWire v783 annotations: github.com/flyconnectome/flywire_annotations (`Supplemental_file1_neuron_annotations.tsv`)
- Braun DN networks: github.com/NeLy-EPFL/dn_networks
- Park code: github.com/gyujeongion/flyconnectome-nulls · Dhiman code: github.com/nalin-dhiman/Connectome-Constrained-Neural-Networks
