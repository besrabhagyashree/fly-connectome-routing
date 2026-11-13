# Step 9 notes — Pong played by the frozen connectome

Plan: `exp09_pong_plan.md`, committed and pushed 12 Nov 2026 at 19:44:47 IST, before any brain played. The run went from 19:46 IST on 12 Nov to 16:13 IST on 13 Nov; the laptop slept from about 03:00 to 09:44 IST and the workers resumed. Code: `flynull/pong.py`, `experiments/exp09_pong.py`. Per-brain results: `exp09_pong_all.csv`; per-ball hits: `exp09_hits/`.

## Result

| Player (same 300 test balls) | Hit rate |
|---|---|
| Teacher | 100% |
| **Real brain** | **34.3%** |
| No wiring (gain 0, readout from the 3,129 eye cells) | 31.0% |
| Standard shuffles (N = 20) | 31.8% ± 2.3 (28.3–35.7) |
| Inside-only block shuffles (N = 50) | 30.9% ± 2.7 (25.0–37.0) |
| Inside-only degree shuffles (N = 50) | 29.8% ± 2.3 (25.3–37.0) |
| Still paddle | 23% |
| Random moves | 21% |

**Gate: passed.** The real brain reached 5.0% active at gain 2.21. Every shuffled brain also reached 5.0% (none flagged).

**Question 1, wiring adds skill: no.** The real brain hit 72 balls the no-wiring model missed and missed 62 it hit. Exact one-sided McNemar p = 0.22.

**Question 2, exact wiring matters: no.** The real brain is at or below 2 of 50 degree shuffles (p = 0.059) and 8 of 50 block shuffles (p = 0.18). The rule needed p < 0.05 for both. Standard shuffles, reported only: 4 of 20 at or above the real brain.

**Ladder: stops here.** The plan allowed harder games only if question 1 was yes.

All inside-only boundary checks and all invariant checks passed.

## Reading

Every player sits near chance, 25–37% against 21–23% for random moves. A linear readout learns little Pong from this input, with or without the fly's wiring. This rung therefore shows a weak setup more than it shows anything about the fly. The real brain is near the top of the shuffle distribution (34.3% against a mean of 30.6%), but not beyond it, and not beyond the model with no wiring.

## Exploratory observations (not part of any rule)

- **Gain.** To reach 5% active the real brain needed gain 2.21, against 0.33–0.62 for shuffles, 4–7× higher. This matches the spectral-radius scaling found in the second audit: the real brain's connections are scaled down more by normalisation. The activity was matched, but the per-connection strength was not, so "same operating point" here means the same activity only.
- **Readout penalty.** Cross-validation chose the smallest ridge penalty on the grid (0.01) for the real brain. Most shuffles chose 10 (78 of 120). A penalty at the edge of the grid means the best value may lie outside it. This could affect the real brain's score in either direction and was not tested.

## Limits

These are as in the plan: only the readout learns; the eye mapping's orientation is a convention; photoreceptors are not driven; there is one game, one input amplitude and one activity target. In addition, the laptop slept for about 7 hours. That paused the run but did not change any computation.
