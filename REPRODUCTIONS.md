# Reproduction status

**Rule:** a paper counts as *implemented* only when our run reproduces a number the authors published. Anything else is labelled "approximation" and must not be described as implementing that paper.

Updated 2026-09-18.

| Paper | Status | Evidence | What is ours vs theirs |
|---|---|---|---|
| **Shiu et al. 2024** (whole-brain spiking model) | **Reproduced (partial)** | Pearson r = 0.9916, Spearman 0.9879 over 386 neurons, against their stored `results/example/sugarR.parquet`. Population median rate 23.3 Hz ours vs 23.0 Hz theirs | Their `model.py`, their v630 connectivity file, their published parameters, their 21 sugar neurons. Nothing modelled by us |
| conn2res / reservoir papers | Approximation only | — | Our own memory-capacity implementation at one fixed spectral radius. Their protocol sweeps gain and reports capacity *at criticality*. Different measurement |
| Pospisil et al. 2024 (effectome) | Approximation only | — | We solve (I − A)⁻¹ for steady-state influence. They estimate *causal* effects from optogenetic perturbation data with an instrumental-variable estimator. Only the linear framing is shared |
| Larval frozen rate operator (arXiv 2606.17745) | Not implemented | — | We use a leaky-tanh operator as they do, but none of their measures (non-normality, activity confinement, mushroom-body modes) |
| Lin et al. 2024 (network statistics) | Not implemented | — | We compute reciprocity and a hub share of our own. They compute motif spectra and rich-club structure against their own nulls |
| Jin et al. 2026 (FlyGM) | Not implemented | — | Requires reinforcement-learning training against a MuJoCo body. No public code found |
| Lappalainen et al. 2024 (flyvis) | Cloned, not run | — | Repo at `external/flyvis`; needs PyTorch |

## Open discrepancy in the Shiu reproduction

The **directly stimulated** sugar neurons fire at ~145 Hz in our run versus ~199 Hz in theirs. Everything downstream matches closely (r = 0.99; population median within 1.5%).

Ruled out:
- **Trial count.** Their own first 3 trials give 194–205 Hz, the same as their 30-trial average. Running 3 instead of 30 is not the cause.
- **Connectivity version.** We used their v630 file, the same one their example uses.

Most likely cause: **Brian2 version.** Their `environment.yml` pins brian2 2.5.1 + numpy 1.24 + python 3.10; we ran brian2 2.9.0 on numpy 1.26 + python 3.11. A plausible mechanism is a change in how Poisson input is applied to a variable declared `(unless refractory)` — input arriving during the 2.2 ms refractory period would be dropped in one version and not the other, lowering the rate of directly driven cells while leaving network structure intact.

Blocked on: brian2 2.5.1 has no wheel for python 3.11 and cannot build here (no C++ compiler, no `pkg_resources`). Confirming it needs python 3.10 installed, or a compiler.

Also note: Brian2 fell back to the numpy code-generation target for the same reason (no compiler), which makes runs ~10× slower than they should be but does not change results.

## Environments

| Env | Python | For |
|---|---|---|
| `.venv` | 3.11.5, numpy 2.4 | our own analysis (`flynull/`) |
| `.venv-brian` | 3.11.5, numpy 1.26, brian2 2.9 | Shiu reproduction |
