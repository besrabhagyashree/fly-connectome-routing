# Step 10 plan — can the fly connectome learn Pong if it is trained?

Written 14 Nov 2026 IST, after tuning on a held-out brain and before any test brain is trained. Code: `flynull/pong_train.py`, `experiments/exp10_tune.py`, `experiments/exp10_trained_pong.py`. Settings: `results/exp10_config.json`.

Step 9 froze the wiring and trained only a linear readout; every player sat near chance. This step trains the network itself, as people do in the game demos and in FlyGM, but keeps the wiring, so the question stays about the fly.

## Question

1. **Does trained wiring add anything?** Does the trained real brain play better than the same model with the wiring removed, trained the same way?
2. **Does the exact wiring matter?** Does the trained real brain play better than trained shuffled brains?

## Method (established: connectome-constrained training)

Following Lappalainen et al. (2024, *Nature*): which neurons connect, the synapse counts and the signs stay fixed; only shared strengths are learned.

- **Game, eye, model, readout neurons, training and test balls:** as in step 9 (`exp09_pong_plan.md`). 200 training balls (seed 11, teacher with 30% random actions), 300 test balls (seed 22), the same for every brain.
- **Trained parameters:** one output scale per presynaptic cell type (FlyWire `primary_type`; untyped neurons grouped by super-class), 8,779 scales, each multiplying every edge from that type's neurons (scale = exp(θ) > 0, so signs are kept), plus the linear readout from the 1,305 descending neurons.
- **Training:** imitation of the teacher (behavioural cloning), mean squared error between readout and teacher action on every frame, backpropagation through time over each ball, Adam (Kingma & Ba 2015), learning rate 0.003, 9 epochs over the 200 balls, 10 balls per update, ball order shuffled each epoch (seed 7 + epoch). All parameters start at scale 1 and readout 0.
- **Gain:** fixed at each brain's step 9 calibration (5% active, same brains and seeds), held fixed during training.
- **Score:** hit rate on the 300 test balls, with the trained network and readout moving the paddle.

**How the settings were chosen.** On a held-out inside-only degree shuffle (replicate 51, not a test brain), the 200 training balls were split 160/40 and learning rates 1e-3, 3e-3 and 1e-2 were run for 10 epochs. The rule, committed before tuning (23287ac), took the lowest validation error, or within 1% of it the smaller learning rate and then fewer epochs: 3e-3 at 9 epochs (validation error 0.3449; best 0.3422 at 1e-2, epoch 5). No hit rate was computed in tuning.

**Seen before this plan (held-out brain only):** validation error fell from 0.385 to 0.344, which is about the cross-validated error of step 9's frozen ridge readouts (0.32–0.34, a different split). Training may therefore add little.

## Baselines and brains

- **No wiring (question 1):** the same model with gain 0, trained with the same settings; the readout reads the 3,129 eye cells (descending neurons are silent without wiring). The cell-type scales have no effect there.
- **Shuffled brains (question 2):** inside-only degree and inside-only block shuffles, **20 each**, replicates 1–20 (the same brains as step 9's replicates 1–20). Shuffles keep every neuron's type and out-degree, so every brain has exactly the same 8,779 scales and training budget. Boundary and invariant checks as in step 9; a boundary failure stops the run.
- **Why 20:** about 2 hours per brain on 3 workers, so 42 brains take about 28 hours. With 20 brains the smallest possible p is 1/21 = 0.048, so question 2 can be yes only if the real brain beats every one of the 20 in both types. Standard shuffles are not run.

## Decision rules (one exit per question)

**Question 1: trained wiring adds skill.** Yes if the trained real brain hits more test balls than the trained no-wiring baseline, exact one-sided McNemar test on the 300 paired balls, p < 0.05. Otherwise no.

**Question 2: exact wiring matters.** Yes if the trained real brain's hit rate is higher than both inside-only types at p < 0.05 each, with p = (1 + brains with hit rate ≥ real) / (N + 1). Otherwise no. Runs whatever question 1 shows.

**Ladder.** A harder game is planned only if question 1 is yes. Not otherwise.

**Reported, not part of a rule:** each brain's hit rate against its own frozen step 9 hit rate (does training help?), and the spread of the learned scales.

## Limits

- Only cell-type-level strengths and the readout learn; single synapses do not. A finer parameterisation could learn more, for every brain alike.
- Imitation of a teacher, not reinforcement learning; one game, one gain, one learning rate and epoch count chosen on one held-out brain.
- The no-wiring baseline reads 3,129 eye cells against 1,305 descending neurons, favouring the baseline (as in step 9).
- 20 shuffles per type make question 2 strict: one shuffled brain at or above the real one gives no.
