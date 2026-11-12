# Step 9 plan — can the fly connectome play Pong?

Written 12 Nov 2026 IST, before any brain played. The game, the teacher and the random and still-paddle baselines were checked with no brain attached: the teacher hits 100% of 300 balls, random moves 21% and a still paddle 23%.

This is the first rung of a ladder of games. Each rung gets its own plan.

## Question

The wiring is frozen; only a linear readout from the descending neurons is trained. Two questions:

1. **Does the wiring add anything?** Does the real brain play better than the same model with the wiring removed?
2. **Does the exact wiring matter?** Does the real brain play better than shuffled brains?

## Method (established: reservoir computing)

The connectome is used as a fixed reservoir (Jaeger 2001; leaky units, Jaeger et al. 2007), with a ridge-regression readout. Code: `flynull/pong.py`, `experiments/exp09_pong.py`.

- **Game:** a ball falls from the top of a unit square at 0.03 per frame, at a random angle of 30–150°, and bounces off the side walls. A paddle (width 0.2) at the bottom moves up to 0.04 per frame. One trial is one ball, ending in a hit or a miss.
- **Eye:** 3,129 lamina L1 and L2 cells, the photoreceptors' direct targets, each placed on screen by its eye column (FlyWire column assignment, Matsliah et al. 2024). The left eye covers the left half of the screen, mirrored. Each frame drives these cells with the brightness of the ball and paddle at their position (amplitude 1).
- **Model:** the rate model of steps 1–8, ≥ 5-synapse connectome, scaled to spectral radius 0.95, leak 0.3, 3 steps per frame. State resets before each ball.
- **Operating point:** each brain's gain is set by bisection (log scale, 1e-3 to 50, 14 halvings) so that 5% of neurons are active (|x| > 1e-3), averaged over every frame of 5 teacher-played balls (seed 99). This is the activity matching that failed in steps 1–5 because the driven neurons alone were 12% of the brain. Here the driven cells are under 2.3% of the brain.
- **Readout:** the activity of the 1,305 descending neurons after each frame, z-scored, with ridge regression onto the teacher's action. The ridge penalty is chosen by 5-fold cross-validation over whole balls from 1e-2 to 1e4.
- **Training:** 200 balls (seed 11), with the paddle moved by the teacher and replaced by a random action on 30% of frames.
- **Test:** 300 balls (seed 22), with the readout moving the paddle. The balls are the same for every brain and baseline.
- **Score:** hit rate on the 300 test balls.

## Baselines

- **No wiring (for question 1):** the same model with gain 0. It has the same leak memory, so ball speed can be read, but no connections. The readout uses the 3,129 eye cells themselves, since descending neurons are silent without wiring.
- **Teacher, random, still paddle:** reported for scale.

## Brains (for question 2)

Inside-only degree and block shuffles, 50 each, replicates 1–50 (seed 1000 + r − 1, 10 swaps per edge). These are the same brains as replicates 1–50 of steps 1 and 5, with the same sensory–descending boundary locked. L1 and L2 are inside cells, so their wiring is shuffled. The same eye cells and readout are used in every brain.

Standard degree-preserving shuffles, 20 brains, are reported alongside and are not part of a rule. Checks are as in step 6: an inside-only boundary failure stops the run, and other check failures are recorded.

## Decision rules (one exit per question)

**Gate.** If the real brain cannot reach 5% active within the gain limits, the step stops and is replanned before any score is read. A shuffled brain that cannot reach it is run at the limit, flagged, and kept.

**Question 1: wiring adds skill.** Yes if the real brain hits more test balls than the no-wiring baseline, with an exact one-sided McNemar test on the 300 paired balls at p < 0.05. Otherwise no.

**Question 2: exact wiring matters.** Yes if the real brain's hit rate is higher than both inside-only types, at p < 0.05 for each, with p = (1 + brains with hit rate ≥ real) / (N + 1). Otherwise no. Question 2 runs whatever question 1 shows.

**Ladder.** The next game (Breakout, then a reduced Tetris) is planned only if question 1 is yes. If the wiring adds nothing to Pong over leak memory, a harder game would only test the readout. Chess is not on the ladder, because the skill would sit in the readout, not the fly.

## Limits

- Only the readout learns; the fly brain has no plasticity here.
- The eye mapping's orientation is a convention. Photoreceptors R1–8 are not driven, since they have no column assignment in this table.
- The no-wiring baseline reads 3,129 eye cells, while the brain is read through 1,305 descending neurons. This favours the baseline.
- There is one game, one input amplitude and one activity target.
