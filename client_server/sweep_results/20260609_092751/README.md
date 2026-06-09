# CWND Sweep Results

- RTT: 0.4 ms
- Size: 1 GiB
- Server: 192.168.88.254:9000
- Client SSH host: nal@192.168.88.253:22
- Empirical max loss rate: 0.20

- Empirical search: start at rounded Reno average-top cwnd, then decrease until loss is acceptable

## Queue Size = 25000 bytes (burst: 5840)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|
| 250 Mbit/s | <15.64, 28.24> | <16, 28.17> | <24.00, 28.33> | <8.00, 28.24> |
| 500 Mbit/s | <16.93, 56.27> | <17, 56.74> | <33.00, 55.19> | <17.00, 56.40> |
| 750 Mbit/s | <18.64, 81.54> | <19, 83.92> | <41.00, 81.65> | <25.00, 73.51> |
| 1000 Mbit/s | <23.93, 103.27> | <22, 109.02> | <50.00, 86.27> | <34.00, 78.95> |

## Queue Size = 25000 bytes (burst: 12500)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|
