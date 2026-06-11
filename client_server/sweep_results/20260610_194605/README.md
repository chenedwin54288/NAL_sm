# CWND Sweep Results

- RTT: 0.4 ms
- Size: 1 GiB
- Server: 192.168.88.254:9000
- Client SSH host: nal@192.168.88.253:22
- Empirical max loss rate: 0.05

- Empirical search: start at floored Reno average-top cwnd, then decrease until loss is acceptable

## Queue Size = 5840 bytes (burst: 5840)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
| 500 Mbit/s | <7.12, 35.90> | <5, 42.36> | <20.00, 36.85> | <18.00, 38.88> |
| 750 Mbit/s | <7.08, 40.04> | <7, 64.51> | <28.00, 29.41> | <26.00, 36.68> |
| 1000 Mbit/s | <7.10, 39.30> | <7, 59.50> | <37.00, 29.67> | <35.00, 29.10> |

## Queue Size = 5840 bytes (burst: 12500)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
