# CWND Sweep Results

- RTT: 0.4 ms
- Size: 1 GiB
- Server: 192.168.88.254:9000
- Client SSH host: nal@192.168.88.253:22
- Empirical max loss rate: 0.0001

- Empirical search: start at floored Reno average-top cwnd, then decrease until loss is acceptable

## Queue Size = 5840 bytes (burst: 5840)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
| 500 Mbit/s | <7.15, 39.40> | <5, 43.39> | <20.00, 38.84> | <18.00, 39.77> |
| 750 Mbit/s | <7.08, 40.28> | <7, 63.83> | <28.00, 37.97> | <26.00, 38.72> |
| 1000 Mbit/s | <7.09, 40.01> | <6, 60.75> | <37.00, 39.84> | <35.00, 36.93> |

## Queue Size = 5840 bytes (burst: 12500)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
| 500 Mbit/s | <8.01, 6.48> | <4, 42.71> | <20.00, 6.06> | <18.00, 6.96> |
| 750 Mbit/s | <8.02, 5.85> | <7, 64.79> | <28.00, 6.84> | <26.00, 5.46> |
| 1000 Mbit/s | <8.01, 5.16> | <5, 40.27> | <37.00, 5.17> | <35.00, 7.37> |

## Queue Size = 5840 bytes (burst: 25000)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
| 500 Mbit/s | <8.01, 6.61> | <5, 43.59> | <20.00, 9.14> | <18.00, 6.66> |
