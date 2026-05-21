- The TCP packets in the TBF queue include headers. Earlier packet-count sweeps used `1p = 1500 bytes`.
- For the next sweep, use byte-sized queue limits directly: `6250b`, `12500b`, `25000b`, `50000b`, and `100000b`.
- Also note the calculation process between different algorithms.

# R_arrival into consideration
Whenever `R_arrival > R_tbf`.
```text
BDP = R_tbf * RTT_base

Q_tbf = burst_penalty
      = max(0, (R_arrival - R_tbf) * RTT_base)
      = BDP * max(0, R_arrival / R_tbf - 1)

if Q_tbf <= Q_config:
    Q_effective = Q_config - Q_tbf
    cwnd = floor((BDP + Q_effective - MSS) / MSS)

if Q_tbf > Q_config:
    Q_effective = 0
    usable_bdp = BDP * min(1, Q_config / Q_tbf)
    cwnd = floor((usable_bdp - MSS) / MSS)
```

# Original algorithm
```text
BDP = R_tbf * RTT_base
optimal_cwnd = floor((BDP + Q_config - MSS) / MSS)
```



# TGR: 250 Mbit/s (burst size 50000b)
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
- client_server/DB/1GB/1GB_48996_0 (DR:0.490, 27.65 MiB/s over 36.99s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_43924_4 (36.46s (28.08 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_47616_5 (DR:0.002897, 28.34 MiB/s over 36.09s)... OPTIMAL
- client_server/DB/1GB/1GB_55966_6 (DR:0.458, 28.33 MiB/s over 36.11s)

### BDP + Queue_effective - MSS
- python3 calculation.py --rate-mbit 250  --rtt-ms 0.4  --tbf-limit 6250b --optimal-cwnd 5  --json
- Estimated **R_arrival = 415.62 Mbit** 
- In the case of R_arrival = 472.6 Mbit (more applicable when Q_config > 6250b), cwnd == 3

### BDP + Queue_size - MSS
- cwnd: 11 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 11
- client_server/DB/1GB/1GB_42902_11 (DR:0.490, 26.65 MiB/s over 38.39s)

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 8
- client_server/DB/1GB/1GB_57162_8 (DR:0.481, 28.28 MiB/s over 36.17s)


## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- client_server/DB/1GB/1GB_49098_0 (DR: 0.451, 28.43 MiB/s over 35.99s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_32906_7 (Drop rate: 0.000456, 28.09 MiB/s over 6.19s (slowstart 3604/4385))
- client_server/DB/1GB/1GB_59776_8 (DR:0.0149, 28.15 MiB/s over 5.93s (slowstart 3011/3743))... OPTIMAL
- client_server/DB/1GB/1GB_37122_9 (DR: 0.423, 28.39 MiB/s over 36.04s)

### BDP + Queue_effective - MSS
- cwnd: 10 (`python3 calculation.py --rate-mbit 250 --r-arrival-mbit 415.62 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- client_server/DB/1GB/1GB_53654_10 (Drop rate: 0.452537, 28.31 MiB/s over 36.14s)
- Recalculating the R_arrival with OPTIMAL CWND == 8 again we then get: **472.6 Mbit** 
  

### BDP + Queue_size - MSS
- cwnd: 16 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 16
- client_server/DB/1GB/1GB_47956_16 (DR:0.454, 28.32 MiB/s over 36.13s)

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 8
- client_server/DB/1GB/1GB_59776_8 (DR:0.0149, 28.15 MiB/s over 5.93s (slowstart 3011/3743))

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- client_server/DB/1GB/1GB_35990_0 (Drop rate: 0.412677, 28.42 MiB/s over 36.00s)
  
### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_54104_16 (36.02s (28.43 MiB/s), only SLOWSTART)... OPTIMAL (or cwnd == 17)

### BDP + Queue_effective - MSS
- cwnd: 17 (`python3 calculation.py --rate-mbit 250 --r-arrival-mbit 472.6 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- client_server/DB/1GB/1GB_57896_17 (Drop rate: 0.381511, 28.38 MiB/s over 36.04s)


### BDP + Queue_size - MSS
- cwnd: 24 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 24
- client_server/DB/1GB/1GB_38022_24 (Drop rate: 0.415021, 28.38 MiB/s over 36.05s)

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 8
- client_server/DB/1GB/1GB_43544_8 (36.16s (28.32 MiB/s), only SLOWSTART)

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- client_server/DB/1GB/1GB_51446_0 (Drop rate: 0.327819, 28.46 MiB/s over 35.95s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_44938_33 (Drop rate: 0.022270, 28.43 MiB/s over 34.37s)... OPTIMAL

### BDP + Queue_effective - MSS
- cwnd: 34 (`python3 calculation.py --rate-mbit 250 --r-arrival-mbit 472.6 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- client_server/DB/1GB/1GB_44228_34 (Drop rate: 0.323831, 28.46 MiB/s over 35.94s)

### BDP + Queue_size - MSS
- cwnd: 41 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 41
- client_server/DB/1GB/1GB_40142_41 (Drop rate: 0.334123, 28.43 MiB/s over 35.99s)

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 8
- client_server/DB/1GB/1GB_58506_8 (36.13s (28.34 MiB/s), only SLOWSTART)

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- client_server/DB/1GB/1GB_50088_0 (Drop rate: 0.219525, 28.47 MiB/s over 35.94s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_39048_64 (35.96s (28.47 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_45748_65 (Drop rate: 0.008881, 28.47 MiB/s over 32.00s) ... OPTIMAL
- client_server/DB/1GB/1GB_36258_66 (Drop rate: 0.087956, 28.48 MiB/s over 35.68s)
- client_server/DB/1GB/1GB_51008_67 (Drop rate: 0.225230, 28.47 MiB/s over 35.89s)

### BDP + Queue_effective - MSS
- cwnd: 68 (`python3 calculation.py --rate-mbit 250 --r-arrival-mbit 472.6 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- client_server/DB/1GB/1GB_55870_68 (Drop rate: 0.230769, 28.45 MiB/s over 35.94s)

### BDP + Queue_size - MSS
- cwnd: 76 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 76
- client_server/DB/1GB/1GB_54576_76 (Drop rate: 0.232255, 28.46 MiB/s over 35.95s)

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 8
- client_server/DB/1GB/1GB_39700_8 (36.07s (28.39 MiB/s), only SLOWSTART)







# TGR: 500 Mbit/s (burst size 50000b)  R_arrival = 1000 Mbit
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 20 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 20

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 17

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 24 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 24

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 17

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 33 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 33

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 17

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 50 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 50

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 17

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 84 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 84

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 17
















# TGR: 750 Mbit/s (burst size 50000b)  R_arrival = 1420 Mbit
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 28 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 28

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 25

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 33 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 33

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 25

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 41 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 41

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 25

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 58 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 58

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 25

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 93 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 93

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 25





















# TGR: 1000 Mbit/s (burst size 50000b)
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 37 (`python3 calculation.py --rate-mbit 1000 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 37

### BDP
- cwnd: 34 (`floor(BDP / MSS)`, BDP = 50000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 34

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 41 (`python3 calculation.py --rate-mbit 1000 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 41

### BDP
- cwnd: 34 (`floor(BDP / MSS)`, BDP = 50000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 34

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 50 (`python3 calculation.py --rate-mbit 1000 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 50

### BDP
- cwnd: 34 (`floor(BDP / MSS)`, BDP = 50000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 34

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 67 (`python3 calculation.py --rate-mbit 1000 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 67

### BDP
- cwnd: 34 (`floor(BDP / MSS)`, BDP = 50000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 34

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 101 (`python3 calculation.py --rate-mbit 1000 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 101

### BDP
- cwnd: 34 (`floor(BDP / MSS)`, BDP = 50000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 34
