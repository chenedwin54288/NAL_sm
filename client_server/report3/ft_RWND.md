# Formatted RWND Results

This file combines the server-side empirical `cwnd` tables with the client-side
tests where the receiver advertises a capped `rwnd` to the sender.

## How to Read This File

- Summary-table cells use `<window, throughput MiB/s>`.
- `Empirical cwnd` is the server-side capped result from `ft_tpCWND.md`.
- `Client rwnd test` uses the empirical cwnd value as
  `python3 Client/client.py --rwnd-segments <value>`.
- `only slow_start` means the server log did not detect a post-slow-start
  interval, so the listed throughput is total-transfer throughput.
- `DR` is the drop-rate value recorded for the client-side RWND run.

These results suggest that advertising a capped `rwnd` from the client, using
the empirical `cwnd` value, constrains the sender's effective sending window to
`min(cwnd, rwnd)`. As a result, this approach achieves behavior similar to
directly capping the sender-side `cwnd`.

## Summary Tables

### Queue Size = 6250 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical cwnd | Client rwnd test | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <6.06, 27.65> | <5, 28.34> | <5, 28.31> ([1GB_45306_0](../DB/1GB/1GB_45306_0), only slow_start) | <5, 28.34> | <11, 26.65> | <8, 28.28> |
| 500 Mbit/s | <9.59, 15.84> (3 runs) | <7, 56.94> | <7, 56.23> ([1GB_48362_0](../DB/1GB/1GB_48362_0), DR=0.023348) | <2, 21.62> | <20, 17.60> | <17, 22.25> |
| 750 Mbit/s | <10.17, 20.03> (3 runs) | <9, 80.04> | <9, 76.30> ([1GB_54814_0](../DB/1GB/1GB_54814_0), only slow_start; rwnd=10 gave 19.21 MiB/s, DR=0.417053) | <3, 25.86> | <28, 12.74> | <25, 14.23> |
| 1000 Mbit/s | <10.16, 16.38> | <9, 81.68> | <9, 60.29> ([1GB_60902_0](../DB/1GB/1GB_60902_0), only slow_start; rwnd=10 gave 18.31 MiB/s, DR=0.427113) | <8, 74.80> | <37, 16.34> | <34, 15.03> |

### Queue Size = 12500 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical cwnd | Client rwnd test | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <9.84, 28.43> | <8, 28.15> | <8, 28.36> ([1GB_36162_0](../DB/1GB/1GB_36162_0), only slow_start) | <10, 28.31> | <16, 28.32> | <8, 28.15> |
| 500 Mbit/s | <11.54, 52.69> | <9, 56.58> | <9, 56.60> ([1GB_60342_0](../DB/1GB/1GB_60342_0), only slow_start; rwnd=10 gave 56.71 MiB/s, DR=0.122938) | <6, 56.67> | <24, 56.75> | <17, 56.73> |
| 750 Mbit/s | <16.65, 71.96> | <11, 84.12> | <11, 82.80> ([1GB_45010_0](../DB/1GB/1GB_45010_0), only slow_start) | <7, 63.16> | <33, 73.66> | <25, 75.44> |
| 1000 Mbit/s | <19.46, 67.15> | <17, 108.92> | <17, 84.86> ([1GB_34464_0](../DB/1GB/1GB_34464_0), only slow_start; rwnd=18 gave 47.82 MiB/s, DR=0.353367) | <17, 108.92> | <41, 57.49> | <34, 53.46> |

### Queue Size = 25000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical cwnd | Client rwnd test | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <18.20, 28.42> | <16, 28.43> | <16, 28.41> ([1GB_60132_0](../DB/1GB/1GB_60132_0), only slow_start) | <17, 28.38> | <24, 28.38> | <8, 28.32> |
| 500 Mbit/s | <19.45, 56.95> | <17, 56.84> | <17, 56.58> ([1GB_59926_0](../DB/1GB/1GB_59926_0), only slow_start) | <14, 56.42> | <33, 56.92> | <17, 56.61> |
| 750 Mbit/s | <23.72, 81.93> | <18, 84.34> | <18, 85.27> ([1GB_34590_0](../DB/1GB/1GB_34590_0), DR=0.003716) | <15, 85.20> | <41, 85.16> | <25, 84.63> |
| 1000 Mbit/s | <39.15, 98.87> | <33, 111.79> | <33, 110.04> ([1GB_35752_0](../DB/1GB/1GB_35752_0), only slow_start) | <34, 95.28> | <50, 105.72> | <34, 95.28> |

### Queue Size = 50000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical cwnd | Client rwnd test | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <35.57, 28.46> | <33, 28.43> | <33, 28.44> ([1GB_39930_0](../DB/1GB/1GB_39930_0), DR=0.000778) | <34, 28.46> | <41, 28.43> | <8, 28.34> |
| 500 Mbit/s | <36.99, 56.87> | <33, 56.79> | <33, 56.75> ([1GB_36560_0](../DB/1GB/1GB_36560_0), DR=0.000523) | <31, 56.69> | <50, 56.83> | <17, 56.13> |
| 750 Mbit/s | <42.25, 85.23> | <34, 84.97> | <34, 84.62> ([1GB_39622_0](../DB/1GB/1GB_39622_0), DR=0.001629) | <32, 84.79> | <58, 84.48> | <25, 85.30> |
| 1000 Mbit/s | <58.11, 111.87> | <67, 112.08> | <67, 111.76> ([1GB_37508_0](../DB/1GB/1GB_37508_0), DR=0.017288; DR incl. fast=0.017672) | <67, 112.08> | <67, 112.08> | <34, 111.75> |

### Queue Size = 100000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical cwnd | Client rwnd test | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <66.83, 28.47> | <65, 28.47> | <65, 28.44> ([1GB_50878_0](../DB/1GB/1GB_50878_0), DR=0.001046) | <68, 28.45> | <76, 28.46> | <8, 28.39> |
| 500 Mbit/s | <66.88, 56.62> | <65, 56.57> | <65, 56.86> ([1GB_47798_0](../DB/1GB/1GB_47798_0), only slow_start) | <65, 56.57> | <84, 56.77> | <17, 56.80> |
| 750 Mbit/s | <67.10, 85.13> | <66, 85.05> | <66, 85.31> ([1GB_56074_0](../DB/1GB/1GB_56074_0), only slow_start) | <66, 85.05> | <93, 85.16> | <25, 84.45> |
| 1000 Mbit/s | <119.20, 111.40> | <102, 111.98> | <102, 111.70> ([1GB_49368_0](../DB/1GB/1GB_49368_0), DR=0.000000; DR incl. fast=0.002867) | <101, 111.67> | <101, 111.67> | <34, 110.51> |

## Test Commands

The server-side command keeps the `my_cca` cap disabled with `--cwnd 0`.
The client-side command applies the empirical cwnd value as the advertised
receive window:

```bash
./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit <TGR> --tbf-rate <TGR>Mbit --tbf-burst 50000b --tbf-limit <queue-size>b --cwnd 0
python3 Client/client.py --rwnd-segments <empirical-cwnd>
```
