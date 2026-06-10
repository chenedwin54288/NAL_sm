import unittest

from arrival_estimation import (
    ProbeSample,
    calculate_rwnd,
    compute_queue_delay_sample,
    estimate_arrival_and_rwnd,
    estimate_arrival_rate,
    linear_regression_slope,
)


def mbit_to_bytes_per_second(value):
    return value * 1_000_000.0 / 8.0


def probe_sample_for_qbytes(seq, send_timestamp, qbytes, r_tbf, base_owd):
    qdelay = qbytes / r_tbf
    return ProbeSample(
        seq=seq,
        send_timestamp=send_timestamp,
        recv_timestamp=send_timestamp + base_owd + qdelay,
        payload_size=1460,
    )


class ArrivalEstimationTests(unittest.TestCase):
    def test_qdelay_clamped_and_qbytes(self):
        r_tbf = mbit_to_bytes_per_second(100)
        rtt_base = 0.0004
        base_owd = rtt_base / 2.0

        early = ProbeSample(
            seq=1,
            send_timestamp=100.0,
            recv_timestamp=100.0 + base_owd - 0.00005,
            payload_size=1460,
        )
        early_queue = compute_queue_delay_sample(early, r_tbf, rtt_base)
        self.assertEqual(early_queue.qdelay_seconds, 0.0)
        self.assertEqual(early_queue.qbytes, 0.0)

        delayed = ProbeSample(
            seq=2,
            send_timestamp=100.0,
            recv_timestamp=100.0 + base_owd + 0.00005,
            payload_size=1460,
        )
        delayed_queue = compute_queue_delay_sample(delayed, r_tbf, rtt_base)
        self.assertAlmostEqual(delayed_queue.qdelay_seconds, 0.00005)
        self.assertAlmostEqual(delayed_queue.qbytes, 625.0, delta=1e-4)

    def test_linear_regression_slope(self):
        beta = mbit_to_bytes_per_second(50)
        points = [
            (10.0 + index * 0.001, 1234.0 + beta * index * 0.001)
            for index in range(8)
        ]
        self.assertAlmostEqual(linear_regression_slope(points), beta, delta=1e-3)

    def test_synthetic_arrival_rate_and_rwnd(self):
        r_tbf = mbit_to_bytes_per_second(100)
        beta = mbit_to_bytes_per_second(50)
        rtt_base = 0.0004
        q_config = 50_000.0
        mss = 1460
        base_owd = rtt_base / 2.0
        start = 100.0
        samples = [
            probe_sample_for_qbytes(
                seq=index,
                send_timestamp=start + index * 0.001,
                qbytes=1000.0 + beta * index * 0.001,
                r_tbf=r_tbf,
                base_owd=base_owd,
            )
            for index in range(10)
        ]

        result = estimate_arrival_and_rwnd(
            samples=samples,
            r_tbf_bytes_per_second=r_tbf,
            rtt_base_seconds=rtt_base,
            q_config_bytes=q_config,
            mss_bytes=mss,
            window_size=20,
        )

        self.assertTrue(result["valid_estimate"])
        self.assertAlmostEqual(result["beta_queue_growth_rate"], beta, delta=1e-3)
        self.assertAlmostEqual(
            result["r_arrival_bytes_per_second"],
            mbit_to_bytes_per_second(150),
            delta=1e-3,
        )
        self.assertAlmostEqual(
            result["R_arrival"],
            mbit_to_bytes_per_second(150),
            delta=1e-3,
        )

        bdp = r_tbf * rtt_base
        q_tbf = beta * rtt_base
        q_effective = q_config - q_tbf
        expected_segments = int((bdp + q_effective - mss) // mss)
        self.assertEqual(result["rwnd_bytes"], expected_segments * mss)

    def test_ignore_samples_after_loss(self):
        r_tbf = mbit_to_bytes_per_second(100)
        beta = mbit_to_bytes_per_second(50)
        rtt_base = 0.0004
        base_owd = rtt_base / 2.0
        samples = [
            probe_sample_for_qbytes(0, 10.000, 1000.0, r_tbf, base_owd),
            probe_sample_for_qbytes(1, 10.001, 1000.0 + beta * 0.001, r_tbf, base_owd),
            probe_sample_for_qbytes(3, 10.002, 1000.0 + beta * 0.002, r_tbf, base_owd),
            probe_sample_for_qbytes(4, 10.003, 1000.0 + beta * 0.003, r_tbf, base_owd),
        ]

        result = estimate_arrival_rate(
            samples=samples,
            r_tbf_bytes_per_second=r_tbf,
            rtt_base_seconds=rtt_base,
            q_config_bytes=1_000_000.0,
            window_size=10,
            min_samples=2,
        )

        self.assertTrue(result.loss_observed)
        self.assertTrue(result.saturation_observed)
        self.assertEqual(result.sample_count, 2)
        self.assertAlmostEqual(result.beta_queue_growth_rate, beta, delta=1e-3)

    def test_ignore_samples_after_saturation(self):
        r_tbf = mbit_to_bytes_per_second(100)
        rtt_base = 0.0004
        base_owd = rtt_base / 2.0
        samples = [
            probe_sample_for_qbytes(0, 20.000, 1000.0, r_tbf, base_owd),
            probe_sample_for_qbytes(1, 20.001, 2000.0, r_tbf, base_owd),
            probe_sample_for_qbytes(2, 20.002, 6000.0, r_tbf, base_owd),
            probe_sample_for_qbytes(3, 20.003, 8000.0, r_tbf, base_owd),
        ]

        result = estimate_arrival_rate(
            samples=samples,
            r_tbf_bytes_per_second=r_tbf,
            rtt_base_seconds=rtt_base,
            q_config_bytes=5000.0,
            window_size=10,
            min_samples=2,
        )

        self.assertFalse(result.loss_observed)
        self.assertTrue(result.saturation_observed)
        self.assertEqual(result.sample_count, 2)
        self.assertAlmostEqual(result.beta_queue_growth_rate, 1_000_000.0, delta=1e-3)

    def test_rwnd_q_over_config_branch(self):
        r_tbf = mbit_to_bytes_per_second(100)
        r_arrival = mbit_to_bytes_per_second(1000)
        rtt_base = 0.0004
        mss = 1460

        result = calculate_rwnd(
            r_tbf_bytes_per_second=r_tbf,
            rtt_base_seconds=rtt_base,
            q_config_bytes=1000.0,
            mss_bytes=mss,
            r_arrival_bytes_per_second=r_arrival,
        )

        expected_segments = int((r_tbf * rtt_base) // mss)
        self.assertEqual(result.cwnd_segments, expected_segments)
        self.assertEqual(result.rwnd_bytes, expected_segments * mss)


if __name__ == "__main__":
    unittest.main()
