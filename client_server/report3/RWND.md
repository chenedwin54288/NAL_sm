In `ft_tpCWND.md`, we limited the empirical `cwnd` on the server side. In
practice, we want to apply this limit from the client side through the `rwnd`
advertised by the client to the server.

Below, we test this by setting the empirical receive-window value on the client
socket, so that the sender becomes limited by the client-advertised `rwnd`:

```c
// my_cca.c (line 167)
if (!tcp_is_cwnd_limited(sk))
    return;
```

### Queue Size = 6250 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <6.06, 27.65> | <5, 28.34> | <5, 28.34> | <11, 26.65> | <8, 28.28> |
| 500 Mbit/s | <9.59, 15.84> (3 runs) | <7, 56.94> | <2, 21.62> | <20, 17.60> | <17, 22.25> |
| 750 Mbit/s | <10.17, 20.03> (3 runs) | <9, 80.04> | <3, 25.86> | <28, 12.74> | <25, 14.23> |
| 1000 Mbit/s | <10.16, 16.38> | <9, 81.68> | <8, 74.80> | <37, 16.34> | <34, 15.03> |


#### 
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
- python3 client/client.py --rwnd-segments 5
  - client_server/DB/1GB/1GB_45306_0 (36.17s (28.31 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
- python3 client/client.py --rwnd-segments 7
  - client_server/DB/1GB/1GB_48362_0 (Drop rate: 0.023348, Drop rate incl. fast retransmit: 0.023348, 56.23 MiB/s over 17.96s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
- python3 client/client.py --rwnd-segments 9... still OPTIMAL 
  - client_server/DB/1GB/1GB_54814_0 (13.42s (76.30 MiB/s), only SLOWSTART)
- python3 client/client.py --rwnd-segments 10
  - client_server/DB/1GB/1GB_39330_0 (Drop rate: 0.417053, Drop rate incl. fast retransmit: 0.417053, 19.21 MiB/s over 53.27s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
- python3 client/client.py --rwnd-segments 9... still OPTIMAL
  - client_server/DB/1GB/1GB_60902_0 (16.98s (60.29 MiB/s), only SLOWSTART)
- python3 client/client.py --rwnd-segments 10
  - client_server/DB/1GB/1GB_49020_0 (Drop rate: 0.427113, Drop rate incl. fast retransmit: 0.427113, 18.31 MiB/s over 55.88s)

### Queue Size = 12500 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <9.84, 28.43> | <8, 28.15> | <10, 28.31> | <16, 28.32> | <8, 28.15> |
| 500 Mbit/s | <11.54, 52.69> | <9, 56.58> | <6, 56.67> | <24, 56.75> | <17, 56.73> |
| 750 Mbit/s | <16.65, 71.96> | <11, 84.12> | <7, 63.16> | <33, 73.66> | <25, 75.44> |
| 1000 Mbit/s | <19.46, 67.15> | <17, 108.92> | <17, 108.92> | <41, 57.49> | <34, 53.46> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- python3 client/client.py --rwnd-segments 8
  - client_server/DB/1GB/1GB_36162_0 (36.11s (28.36 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- python3 client/client.py --rwnd-segments 9... still OPTIMAL
  - client_server/DB/1GB/1GB_60342_0 (18.09s (56.60 MiB/s), only SLOWSTART)
- python3 client/client.py --rwnd-segments 10
  - client_server/DB/1GB/1GB_52686_0 (Drop rate: 0.122938, Drop rate incl. fast retransmit: 0.122938, 56.71 MiB/s over 18.00s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- python3 client/client.py --rwnd-segments 11
  - client_server/DB/1GB/1GB_45010_0 (12.37s (82.80 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- python3 client/client.py --rwnd-segments 17... still OPTIMAL
  - client_server/DB/1GB/1GB_34464_0 (12.07s (84.86 MiB/s), only SLOWSTART)
- python3 client/client.py --rwnd-segments 18
  - client_server/DB/1GB/1GB_60766_0 (Drop rate: 0.353367, Drop rate incl. fast retransmit: 0.353367, 47.82 MiB/s over 21.39s)

### Queue Size = 25000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <18.20, 28.42> | <16, 28.43> | <17, 28.38> | <24, 28.38> | <8, 28.32> |
| 500 Mbit/s | <19.45, 56.95> | <17, 56.84> | <14, 56.42> | <33, 56.92> | <17, 56.61> |
| 750 Mbit/s | <23.72, 81.93> | <18, 84.34> | <15, 85.20> | <41, 85.16> | <25, 84.63> |
| 1000 Mbit/s | <39.15, 98.87> | <33, 111.79> | <34, 95.28> | <50, 105.72> | <34, 95.28> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- python3 client/client.py --rwnd-segments 16
  - client_server/DB/1GB/1GB_60132_0 (36.04s (28.41 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- python3 client/client.py --rwnd-segments 17
  - client_server/DB/1GB/1GB_59926_0 (18.10s (56.58 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- python3 client/client.py --rwnd-segments 18
  - client_server/DB/1GB/1GB_34590_0 (Drop rate: 0.003716, Drop rate incl. fast retransmit: 0.003716, 85.27 MiB/s over 8.63s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- python3 client/client.py --rwnd-segments 33
  - client_server/DB/1GB/1GB_35752_0 (9.31s (110.04 MiB/s), only SLOWSTART)


### Queue Size = 50000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <35.57, 28.46> | <33, 28.43> | <34, 28.46> | <41, 28.43> | <8, 28.34> |
| 500 Mbit/s | <36.99, 56.87> | <33, 56.79> | <31, 56.69> | <50, 56.83> | <17, 56.13> |
| 750 Mbit/s | <42.25, 85.23> | <34, 84.97> | <32, 84.79> | <58, 84.48> | <25, 85.30> |
| 1000 Mbit/s | <58.11, 111.87> | <67, 112.08> | <67, 112.08> | <67, 112.08> | <34, 111.75> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- python3 client/client.py --rwnd-segments 33
  - client_server/DB/1GB/1GB_39930_0 (Drop rate: 0.000778, Drop rate incl. fast retransmit: 0.000778, 28.44 MiB/s over 33.43s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- python3 client/client.py --rwnd-segments 33
  - client_server/DB/1GB/1GB_36560_0 (Drop rate: 0.000523, Drop rate incl. fast retransmit: 0.000523, 56.75 MiB/s over 5.94s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- python3 client/client.py --rwnd-segments 34
  - client_server/DB/1GB/1GB_39622_0 (Drop rate: 0.001629, Drop rate incl. fast retransmit: 0.001629, 84.62 MiB/s over 11.10s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- python3 client/client.py --rwnd-segments 67
  - client_server/DB/1GB/1GB_37508_0 (Drop rate: 0.017288, Drop rate incl. fast retransmit: 0.017672, 111.76 MiB/s over 5.82s)

### Queue Size = 100000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <66.83, 28.47> | <65, 28.47> | <68, 28.45> | <76, 28.46> | <8, 28.39> |
| 500 Mbit/s | <66.88, 56.62> | <65, 56.57> | <65, 56.57> | <84, 56.77> | <17, 56.80> |
| 750 Mbit/s | <67.10, 85.13> | <66, 85.05> | <66, 85.05> | <93, 85.16> | <25, 84.45> |
| 1000 Mbit/s | <119.20, 111.40> | <102, 111.98> | <101, 111.67> | <101, 111.67> | <34, 110.51> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- python3 client/client.py --rwnd-segments 65
  - client_server/DB/1GB/1GB_50878_0 (Drop rate: 0.001046, Drop rate incl. fast retransmit: 0.001046, 28.44 MiB/s over 29.96s)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- python3 client/client.py --rwnd-segments 65
  - client_server/DB/1GB/1GB_47798_0 (18.01s (56.86 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- python3 client/client.py --rwnd-segments 66
  - client_server/DB/1GB/1GB_56074_0 (12.00s (85.31 MiB/s), only SLOWSTART)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- python3 client/client.py --rwnd-segments 102
  - client_server/DB/1GB/1GB_49368_0 (Drop rate: 0.000000, Drop rate incl. fast retransmit: 0.002867, 111.70 MiB/s over 9.14s)