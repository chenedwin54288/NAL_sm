# CWND Sweep Results

- RTT: 0.4 ms
- Size: 1 GiB
- Server: 192.168.88.254:9000
- Client SSH host: nal@192.168.88.253:22
- Empirical max loss rate: 0.01

- Empirical search: start at floored Reno average-top cwnd, then decrease until loss is acceptable

## Queue Size = 5840 bytes (burst: 5840)

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP + 1 MSS |
|---:|---:|---:|---:|---:|
