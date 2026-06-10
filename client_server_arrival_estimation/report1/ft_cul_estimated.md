# FT Cumulative Arrival Rate RWND Estimate

## Goal

The goal of this experiment is to let the receiver estimate the sender-side
window cap and report it back as `rwnd`. The sender should then be capped at a
window close to the throughput-maximizing `cwnd`, without requiring an offline
empirical sweep for every path.

This document summarizes the current `cul_estimate.md` results and gives an
opinion on whether cumulative-byte arrival rate is enough to estimate the
optimal receive window.

## Current Method

The current cumulative probe runs before the real transfer. The server replays a
short burst at a nominal `1 Gib/s`, while the receiver records cumulative bytes
arriving over time.

The client-side estimator currently computes:

```text
measured_rate = cumulative_bytes / elapsed_seconds
estimated_rwnd = ceil(measured_rate * RTT * rwnd_gain)
```

For the runs in `cul_estimate.md`, the probe is run in `bulk` mode and the
reported recommendations use `RTT = 0.4 ms` and `rwnd_gain = 1.0`.

This formula is important: it estimates a BDP-like window from the measured
arrival rate. It does not include an explicit queue term. Therefore, unless the
arrival trace contains an additional signal for queued bytes, the result should
mostly follow the bottleneck service rate, which in these tests is the token
generation rate.

## Test Context

The tested cases vary:

- Token generation rate / TBF rate: `250`, `500`, `750`, and `1000 Mbit/s`.
- TBF queue limit: `6250`, `12500`, `25000`, `50000`, and `100000 bytes`.
- TBF burst: `50000b`.
- Probe mode: `--cumulative-send-mode bulk`.
- Normal replay size: `--size-gib 1`.

The tables in `cul_estimate.md` compare several window choices:

- TCP Reno average top `cwnd`.
- Empirical best `rwnd`.
- `BDP + Q_effective - MSS`.
- `BDP + Q_size - MSS`.
- BDP-only.

The raw cumulative probe output also reports a recommended `rwnd` in bytes and
MSS segments. The segment counts from those raw recommendations are summarized
below.

## Raw Cumulative Recommendations

Each cell is the cumulative-probe recommended `rwnd` in MSS segments for
`250 / 500 / 750 / 1000 Mbit/s`.

| Queue limit | Cumulative recommendation | Empirical optimum |
|---:|---:|---:|
| `6250 B` | `8 / 15 / 14 / 13` | `5 / 7 / 9 / 9` |
| `12500 B` | `8 / 14-15 / 20 / 31` | `8 / 9 / 11 / 17` |
| `25000 B` | `9 / 17 / 24 / 18-32` | `16 / 17 / 18 / 33` |
| `50000 B` | `9 / 17 / 25 / 32` | `33 / 33 / 34 / 67` |
| `100000 B` | `9 / 17 / 24 / 33` | `65 / 65 / 66 / 102` |

The larger-queue rows show the main pattern. For a fixed token generation rate,
the cumulative recommendation is almost constant even when queue size grows by
4x or 8x. For example:

- At `250 Mbit/s`, the recommendation stays near `9 MSS`, while the empirical
  optimum grows from `16 MSS` at `25000 B` to `65 MSS` at `100000 B`.
- At `500 Mbit/s`, the recommendation stays near `17 MSS`, while the empirical
  optimum grows from `17 MSS` to `65 MSS`.
- At `750 Mbit/s`, the recommendation stays near `24-25 MSS`, while the
  empirical optimum grows from `18 MSS` to `66 MSS`.
- At `1000 Mbit/s`, the recommendation stays near `32-33 MSS` for larger
  queues, while the empirical optimum grows to `67 MSS` and `102 MSS`.

This matches the observation that the estimated `rwnd` is capped by the token
generation rate rather than by `queue_size`, except when the queue is very
small.

## Main Interpretation

The cumulative arrival-rate probe is mainly measuring the bottleneck service
rate. Once the queue is large enough to absorb the bulk replay burst, the
receiver sees a delivery slope close to the token generation rate. Increasing
the queue limit does not increase that steady-state slope, so the estimator has
no way to infer the larger queue allowance.

That means the current method is a good rate estimator, but not yet an optimal
`cwnd` estimator.

More specifically:

- `estimated_rwnd = measured_rate * RTT` gives a BDP-like lower bound.
- The empirical throughput-maximizing window often looks closer to
  `BDP + queue_allowance - MSS`.
- The queue allowance is not observable from average arrival rate alone.
- In large queues, the probe underestimates the empirical optimum because it
  measures the token rate but ignores the amount of data that can safely sit in
  the queue.
- In very small queues, such as the `6250 B` case, the queue is small enough to
  disturb the bulk replay itself. The measured rate becomes less stable, and the
  recommendation no longer follows the clean larger-queue pattern.

The `25000 B`, `1000 Mbit/s` case is also a useful warning sign: repeated runs
recommended `18`, `32`, and `19 MSS`. That variance suggests the bulk probe can
be sensitive to replay timing, TBF state, or startup effects. It should not be
treated as a stable queue estimator.

## Opinion

I would not use cumulative average arrival rate alone as the final `rwnd`
selection rule if the target is maximum throughput. It is useful, but it is
answering a narrower question: "What rate did the path deliver during the
probe?" It is not answering: "How much window should the sender be allowed to
hold in flight, including useful queue occupancy?"

The current approach is still valuable as the first half of the estimator:

```text
BDP_est = measured_rate * RTT
```

But for the throughput-maximizing `rwnd`, we probably need:

```text
rwnd_target = BDP_est + Q_effective_est - MSS
```

or a controlled approximation of that form.

The main missing variable is `Q_effective_est`. If we do not estimate the queue
term, the receiver will keep reporting a BDP-only `rwnd`. That is safe and
reasonable for avoiding queue buildup, but it will underfill the sender window
in the large-buffer cases where the empirical optimum depends heavily on queue
size.

There is also a product-level tradeoff here. The empirical optimum maximizes
throughput, but it may intentionally keep more data queued. If latency matters,
we should decide whether the receiver wants maximum throughput, low queueing
delay, or a tunable balance between the two.

## Recommended Next Steps

### 1. Split the Estimator Into Two Parts

Keep the cumulative arrival-rate probe as the rate estimator:

```text
rate_est = slope(cumulative_bytes over time)
BDP_est = rate_est * RTT
```

Then add a second estimator for queue allowance:

```text
rwnd_target = BDP_est + Q_effective_est - MSS
```

This makes the model match the empirical tables more directly.

### 2. Replace Whole-Run Average With a Stable Slope

The current implementation uses the whole-run average:

```text
average_rate = total_received_bytes / total_elapsed_time
```

This can be skewed by startup, stop-marker timing, and queue drain. A more
stable rate estimator would compute the slope of cumulative bytes over a middle
window, for example:

- Ignore the first `100-200 ms`.
- Ignore the final drain/stop region.
- Use median or linear-regression slope over the steady region.
- Repeat the probe and report median plus variation.

This will not solve queue-size estimation by itself, but it will make the BDP
part less noisy.

### 3. Add a Queue-Drain Probe

To estimate queue occupancy, add an explicit signal for "the sender stopped
writing data now" and count how many data bytes still arrive afterward.

One practical design:

- Use a separate control channel.
- During the data probe, the server sends bulk data faster than the TBF rate.
- At the moment the server stops writing data, it sends a control message.
- The receiver keeps reading the data socket.
- Data bytes received after the control message approximate bytes already
  queued in the bottleneck/TBF path.

Then:

```text
Q_effective_est ~= bytes_received_after_sender_stop
```

This is much closer to the value needed by `BDP + Q_effective - MSS` than the
average arrival rate is.

### 4. Test Controlled Burst Sizes Instead of Only Bulk

Bulk mode is useful for stressing the path, but it is a blunt measurement tool.
It can hide queue behavior behind large writes, receive coalescing, and timing
noise.

Run the cumulative probe with controlled burst sizes such as:

```text
4 MSS, 8 MSS, 16 MSS, 32 MSS, 64 MSS, 128 MSS
```

For each burst size, record:

- Cumulative arrival slope.
- Bytes received after sender stop.
- Recommended `rwnd`.
- Final normal-transfer throughput.
- Retransmissions or drops, if available.

Smaller controlled bursts should make the boundary between BDP-only behavior
and queue-filling behavior easier to see.

### 5. Validate With a Window Sweep Around the Estimate

For each `(TGR, queue_size)` pair, run normal transfers with:

```text
BDP_est
BDP_est + 0.25 * Q_effective_est
BDP_est + 0.50 * Q_effective_est
BDP_est + 0.75 * Q_effective_est
BDP_est + 1.00 * Q_effective_est
```

Compare throughput, retransmissions, and latency. This will show whether the
queue term should be used fully or with a safety factor.

### 6. Track Variance Explicitly

Some cases already show run-to-run variance, especially `25000 B` at
`1000 Mbit/s`. For the next report, each cell should include at least:

- Median throughput.
- Median recommended `rwnd`.
- Min/max or interquartile range.
- Number of runs.

This will make it easier to tell whether a new estimator is actually better or
just lucky on one replay.

## Proposed Direction

The best next version is a hybrid estimator:

```text
rate_est = stable cumulative arrival slope
BDP_est = rate_est * RTT
Q_effective_est = queue-drain bytes after sender stop
rwnd_target = BDP_est + alpha * Q_effective_est - MSS
```

Start with `alpha = 1.0` for maximum-throughput experiments, then evaluate
smaller `alpha` values if latency or drops become unacceptable.

In short: keep the cumulative arrival-rate idea, but treat it as the rate
measurement component. Add a queue measurement component before using it as the
final `rwnd` estimator.
