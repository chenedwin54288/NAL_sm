"""Queue-growth arrival estimator and rwnd calculation.

All public estimator functions use seconds for time values, bytes for queue
sizes, and bytes/second for rates. The probe wire protocol stores timestamps as
integer nanoseconds since Unix epoch; callers convert them to seconds before
constructing ``ProbeSample``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ProbeSample:
    seq: int
    send_timestamp: float
    recv_timestamp: float
    payload_size: int


@dataclass(frozen=True)
class QueueDelaySample:
    seq: int
    send_timestamp: float
    recv_timestamp: float
    payload_size: int
    owd_seconds: float
    qdelay_seconds: float
    qbytes: float


@dataclass(frozen=True)
class ArrivalRateEstimate:
    r_arrival_bytes_per_second: float
    beta_queue_growth_rate: float
    sample_count: int
    loss_observed: bool
    saturation_observed: bool
    valid_estimate: bool
    not_overloaded: bool
    base_owd_seconds: float
    usable_sample_count: int
    received_sample_count: int


@dataclass(frozen=True)
class RwndCalculation:
    r_arrival_bytes_per_second: float
    rwnd_bytes: int
    cwnd_segments: int
    bdp_bytes: float
    q_tbf_bytes: float
    q_effective_bytes: float


def derive_base_owd_seconds(
    rtt_base_seconds: float,
    explicit_base_owd_seconds: float | None = None,
) -> float:
    if rtt_base_seconds <= 0:
        raise ValueError("RTT_base must be greater than 0")
    if explicit_base_owd_seconds is None:
        return rtt_base_seconds / 2.0
    if explicit_base_owd_seconds < 0:
        raise ValueError("base OWD must be non-negative")
    return explicit_base_owd_seconds


def compute_queue_delay_sample(
    sample: ProbeSample,
    r_tbf_bytes_per_second: float,
    rtt_base_seconds: float,
    base_owd_seconds: float | None = None,
) -> QueueDelaySample:
    if r_tbf_bytes_per_second <= 0:
        raise ValueError("R_tbf must be greater than 0")
    if sample.payload_size < 0:
        raise ValueError("payload_size must be non-negative")

    base_owd = derive_base_owd_seconds(rtt_base_seconds, base_owd_seconds)
    owd_seconds = sample.recv_timestamp - sample.send_timestamp
    qdelay_seconds = max(0.0, owd_seconds - base_owd)
    qbytes = qdelay_seconds * r_tbf_bytes_per_second

    return QueueDelaySample(
        seq=sample.seq,
        send_timestamp=sample.send_timestamp,
        recv_timestamp=sample.recv_timestamp,
        payload_size=sample.payload_size,
        owd_seconds=owd_seconds,
        qdelay_seconds=qdelay_seconds,
        qbytes=qbytes,
    )


def compute_queue_delay_samples(
    samples: Iterable[ProbeSample],
    r_tbf_bytes_per_second: float,
    rtt_base_seconds: float,
    base_owd_seconds: float | None = None,
) -> list[QueueDelaySample]:
    return [
        compute_queue_delay_sample(
            sample=sample,
            r_tbf_bytes_per_second=r_tbf_bytes_per_second,
            rtt_base_seconds=rtt_base_seconds,
            base_owd_seconds=base_owd_seconds,
        )
        for sample in samples
    ]


def linear_regression_slope(points: Sequence[tuple[float, float]]) -> float:
    if len(points) < 2:
        raise ValueError("at least two points are required")

    x0 = points[0][0]
    xs = [point[0] - x0 for point in points]
    ys = [point[1] for point in points]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("sample timestamps must not all be equal")

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return numerator / denominator


def samples_before_loss_or_saturation(
    samples: Sequence[QueueDelaySample],
    q_config_bytes: float,
) -> tuple[list[QueueDelaySample], bool, bool]:
    if q_config_bytes < 0:
        raise ValueError("Q_config must be non-negative")

    usable: list[QueueDelaySample] = []
    loss_observed = False
    queue_saturation_observed = False
    expected_seq: int | None = None

    for sample in samples:
        if expected_seq is not None and sample.seq != expected_seq:
            loss_observed = True
            break

        expected_seq = sample.seq + 1
        if sample.qbytes >= q_config_bytes:
            queue_saturation_observed = True
            break

        usable.append(sample)

    saturation_observed = loss_observed or queue_saturation_observed
    return usable, loss_observed, saturation_observed


def choose_regression_window(
    samples: Sequence[QueueDelaySample],
    window_size: int,
    min_samples: int,
) -> list[QueueDelaySample]:
    if window_size <= 0:
        raise ValueError("window_size must be greater than 0")
    if min_samples <= 1:
        raise ValueError("min_samples must be greater than 1")

    rising_samples = [sample for sample in samples if sample.qbytes > 0.0]
    candidates = rising_samples if len(rising_samples) >= min_samples else list(samples)
    if len(candidates) > window_size:
        return candidates[-window_size:]
    return list(candidates)


def estimate_arrival_rate(
    samples: Sequence[ProbeSample],
    r_tbf_bytes_per_second: float,
    rtt_base_seconds: float,
    q_config_bytes: float,
    base_owd_seconds: float | None = None,
    window_size: int = 20,
    min_samples: int = 3,
) -> ArrivalRateEstimate:
    if r_tbf_bytes_per_second <= 0:
        raise ValueError("R_tbf must be greater than 0")
    if rtt_base_seconds <= 0:
        raise ValueError("RTT_base must be greater than 0")
    if q_config_bytes < 0:
        raise ValueError("Q_config must be non-negative")

    base_owd = derive_base_owd_seconds(rtt_base_seconds, base_owd_seconds)
    queue_samples = compute_queue_delay_samples(
        samples=samples,
        r_tbf_bytes_per_second=r_tbf_bytes_per_second,
        rtt_base_seconds=rtt_base_seconds,
        base_owd_seconds=base_owd,
    )
    usable_samples, loss_observed, saturation_observed = (
        samples_before_loss_or_saturation(
            samples=queue_samples,
            q_config_bytes=q_config_bytes,
        )
    )
    regression_samples = choose_regression_window(
        samples=usable_samples,
        window_size=window_size,
        min_samples=min_samples,
    )

    beta = 0.0
    if len(regression_samples) >= 2:
        beta = linear_regression_slope(
            [
                (sample.send_timestamp, sample.qbytes)
                for sample in regression_samples
            ]
        )

    not_overloaded = beta <= 0.0
    valid_estimate = len(regression_samples) >= min_samples and beta > 0.0
    r_arrival = r_tbf_bytes_per_second + max(0.0, beta)

    return ArrivalRateEstimate(
        r_arrival_bytes_per_second=r_arrival,
        beta_queue_growth_rate=beta,
        sample_count=len(regression_samples),
        loss_observed=loss_observed,
        saturation_observed=saturation_observed,
        valid_estimate=valid_estimate,
        not_overloaded=not_overloaded,
        base_owd_seconds=base_owd,
        usable_sample_count=len(usable_samples),
        received_sample_count=len(samples),
    )


def calculate_rwnd(
    r_tbf_bytes_per_second: float,
    rtt_base_seconds: float,
    q_config_bytes: float,
    mss_bytes: int,
    r_arrival_bytes_per_second: float,
) -> RwndCalculation:
    if r_tbf_bytes_per_second <= 0:
        raise ValueError("R_tbf must be greater than 0")
    if rtt_base_seconds <= 0:
        raise ValueError("RTT_base must be greater than 0")
    if q_config_bytes < 0:
        raise ValueError("Q_config must be non-negative")
    if mss_bytes <= 0:
        raise ValueError("MSS must be greater than 0")
    if r_arrival_bytes_per_second < 0:
        raise ValueError("R_arrival must be non-negative")

    bdp_bytes = r_tbf_bytes_per_second * rtt_base_seconds
    q_tbf_bytes = max(
        0.0,
        (r_arrival_bytes_per_second - r_tbf_bytes_per_second) * rtt_base_seconds,
    )

    if q_tbf_bytes <= q_config_bytes:
        q_effective_bytes = q_config_bytes - q_tbf_bytes
        cwnd_segments = math.floor(
            (bdp_bytes + q_effective_bytes - mss_bytes) / mss_bytes
        )
    else:
        q_effective_bytes = 0.0
        cwnd_segments = math.floor(bdp_bytes / mss_bytes)

    cwnd_segments = max(1, cwnd_segments)
    rwnd_bytes = cwnd_segments * mss_bytes

    return RwndCalculation(
        r_arrival_bytes_per_second=r_arrival_bytes_per_second,
        rwnd_bytes=rwnd_bytes,
        cwnd_segments=cwnd_segments,
        bdp_bytes=bdp_bytes,
        q_tbf_bytes=q_tbf_bytes,
        q_effective_bytes=q_effective_bytes,
    )


def estimate_arrival_and_rwnd(
    samples: Sequence[ProbeSample],
    r_tbf_bytes_per_second: float,
    rtt_base_seconds: float,
    q_config_bytes: float,
    mss_bytes: int,
    base_owd_seconds: float | None = None,
    window_size: int = 20,
    min_samples: int = 3,
) -> dict:
    arrival = estimate_arrival_rate(
        samples=samples,
        r_tbf_bytes_per_second=r_tbf_bytes_per_second,
        rtt_base_seconds=rtt_base_seconds,
        q_config_bytes=q_config_bytes,
        base_owd_seconds=base_owd_seconds,
        window_size=window_size,
        min_samples=min_samples,
    )
    rwnd = calculate_rwnd(
        r_tbf_bytes_per_second=r_tbf_bytes_per_second,
        rtt_base_seconds=rtt_base_seconds,
        q_config_bytes=q_config_bytes,
        mss_bytes=mss_bytes,
        r_arrival_bytes_per_second=arrival.r_arrival_bytes_per_second,
    )

    result = asdict(rwnd)
    result.update(asdict(arrival))
    result["R_arrival"] = arrival.r_arrival_bytes_per_second
    result["r_tbf_bytes_per_second"] = r_tbf_bytes_per_second
    result["rtt_base_seconds"] = rtt_base_seconds
    result["q_config_bytes"] = q_config_bytes
    result["mss_bytes"] = mss_bytes
    return result
