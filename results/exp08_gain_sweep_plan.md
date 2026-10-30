# Step 8 plan — the rate-model test at gains where signals spread

Written 30 Oct 2026 IST, before any step 8 simulation. Approved by Bhagyashree Besra as drafted, 30 Oct 2026.

## Why

Every rate-model run used gain 0.001, the search floor, so signals barely travelled past one step (`CORRECTIONS.md`). Steps 1 and 5 therefore tested something close to a property of the boundary connections, which inside-only shuffles keep by design. This step asks the same question with recurrence switched on.

## Question

Once signals really travel through the network, is the real brain still more focused than inside-only shuffles, and how large is the difference?

## Method

- **Model:** the same rate operator, ≥ 5-synapse connectome, 7 sensory classes, spectral-radius normalisation, 60 steps. Gain is set directly; `calibrate_gain` is not used.
- **Gain grid:** 0.001 (reproduces step 1), 0.01, 0.03, 0.1, 0.3, 1.0.
- **Stage 1, real brain only, at every gain:** record spread, active fraction, and the share of descending activity on direct targets.
- **Primary gain, chosen in stage 1 before any shuffled brain is run:** the lowest grid gain where the direct-target share is below 50%, averaged over the 7 senses, and the active fraction is below 50%. This definition is ours, not a published standard. Its only job is to pick a gain where recurrence matters and the network is not saturated.
- **Stage 2, shuffles:** 50 inside-only degree and 50 inside-only block brains (seeds `1000 + r − 1`, 10 swaps per edge) at the primary gain, plus 19 standard. Every degree, block and boundary check from step 5 applies. Spread is also recorded at the other grid gains.

## Decision rule (one exit per case)

- **Yes, focus holds:** real spread is lower than both inside-only types at p < 0.05, with p = (1 + brains with spread ≤ real) / (N + 1).
- **No:** a primary gain exists and that test fails.
- **No answer:** no grid gain meets the stage 1 definition. No gains are added.

The size of the difference is reported either way, with mean, SD and range. There is no size threshold, because no published one applies.

## Reported alongside (exploratory)

Spread across all gains, step 4a's map agreement, and step 7's separation at the primary gain.

## Cost

Stage 1: minutes. Stage 2: to be timed on one brain first; steps 1 and 5 took about 3 minutes per brain per job, so roughly 3 hours on 4 jobs. Higher gain may slow this.

## Limits

- Gain is one global number; real synapses are not scaled that way.
- The rate model has no threshold like the spiking model's.
- The primary-gain definition is a choice. The all-gains table lets a reader see whether the answer depends on it.

## Definitions fixed before stage 1

- **Active fraction:** the share of neurons with |activity| > 0.001 at the last step with all 7 sensory classes driven together, as in `calibrate_gain`.
- **Direct-target share:** for each sense, the share of its |descending activity| on descending neurons with a direct connection from that sense; averaged over the 7 senses.
