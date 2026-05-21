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




# TGR: 500 Mbit/s (burst size 50000b) 
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
Taking more samples for balanced throughput
- client_server/DB/1GB/1GB_37946_0 (Drop rate: 0.468926, 15.87 MiB/s over 64.46s)
- client_server/DB/1GB/1GB_43236_0 (Drop rate: 0.468758, 16.70 MiB/s over 61.27s)
- client_server/DB/1GB/1GB_42906_0 (Drop rate: 0.468044, 14.96 MiB/s over 68.37s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_56530_3 (54.50s (18.79 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_53576_4 (23.03s (44.46 MiB/s), only SLOWSTART)

Testing cwnd == 5 more times for better accuracy
- client_server/DB/1GB/1GB_40956_5 (Drop rate: 0.000270, 47.47 MiB/s over 21.55s) 
- client_server/DB/1GB/1GB_50208_5 (Drop rate: 0.000280, 44.83 MiB/s over 22.82s)
- client_server/DB/1GB/1GB_59138_5 (Drop rate: 0.000270, 47.16 MiB/s over 21.69s)

- client_server/DB/1GB/1GB_43198_6 (Drop rate: 0.016819, 56.37 MiB/s over 18.15s)
- client_server/DB/1GB/1GB_41802_7 (Drop rate: 0.000502, 56.94 MiB/s over 17.97s)... OPTIMAL
- client_server/DB/1GB/1GB_47016_8 (Drop rate: 0.263779, 56.86 MiB/s over 17.99s )

### BDP + Queue_effective - MSS
- cwnd: 2 (`python3 calculation.py --rate-mbit 500 --r-arrival-mbit 1058.2 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- client_server/DB/1GB/1GB_38186_2 (47.37s (21.62 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 20 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 20
- client_server/DB/1GB/1GB_46054_20 (Drop rate: 0.467844, 17.60 MiB/s over 58.12s)

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 17
- client_server/DB/1GB/1GB_43898_17 (Drop rate: 0.469217, 22.25 MiB/s over 45.97s)

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- client_server/DB/1GB/1GB_54150_0 (Drop rate: 0.453230, 52.69 MiB/s over 19.41s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_58828_7 (18.25s (56.10 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_38632_8 (18.03s (56.78 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_52890_9 (Drop rate: 0.001070, 56.58 MiB/s over 17.85s)... OPTIMAL
- client_server/DB/1GB/1GB_38434_10 (Drop rate: 0.403353, 56.62 MiB/s over 18.07s)

### BDP + Queue_effective - MSS
- cwnd: 6 (` python3 calculation.py --rate-mbit 500 --r-arrival-mbit 1058.2 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- client_server/DB/1GB/1GB_53636_6 (18.07s (56.67 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 24 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 24
- client_server/DB/1GB/1GB_35456_24 (Drop rate: 0.453997, 56.75 MiB/s over 18.03s)

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 17
- client_server/DB/1GB/1GB_45268_17 (Drop rate: 0.445223, 56.73 MiB/s over 18.03s)

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- client_server/DB/1GB/1GB_51592_0 (Drop rate: 0.381196, 56.95 MiB/s over 17.96s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_49998_15 (18.01s (56.87 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_35082_16 (18.10s (56.56 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_50214_17 (Drop rate: 0.150939, 56.84 MiB/s over 17.98s)... OPTIMAL?

### BDP + Queue_effective - MSS
- cwnd: 14 (`python3 calculation.py --rate-mbit 500 --r-arrival-mbit 1058.2 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- client_server/DB/1GB/1GB_40012_14 (18.15s (56.42 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 33 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 33
- client_server/DB/1GB/1GB_48388_33 (Drop rate: 0.377370, 56.92 MiB/s over 17.97s)

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 17
- client_server/DB/1GB/1GB_58940_17 (Drop rate: 0.141003, 56.61 MiB/s over 18.07s)

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- client_server/DB/1GB/1GB_47586_0 (Drop rate: 0.273276, 56.87 MiB/s over 17.99s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_40718_32 (18.00s (56.90 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_33104_33 (Drop rate: 0.005920, 56.79 MiB/s over 15.97s)... OPTIMAL
- client_server/DB/1GB/1GB_53090_34 (Drop rate: 0.201076, 56.71 MiB/s over 18.04s)

### BDP + Queue_effective - MSS
- cwnd: 31 (`python3 calculation.py --rate-mbit 500 --r-arrival-mbit 1058.2 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- client_server/DB/1GB/1GB_51718_31 (18.06s (56.69 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 50 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 50
- client_server/DB/1GB/1GB_38558_50 (Drop rate: 0.263398, 56.83 MiB/s over 18.00s)

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 17
- client_server/DB/1GB/1GB_51028_17 (18.24s (56.13 MiB/s), only SLOWSTART)

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- client_server/DB/1GB/1GB_57812_0 (Drop rate: 0.191323, 56.62 MiB/s over 18.07s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_33702_64 (Drop rate: 0.000698, 56.97 MiB/s over 4.44s (SLOWSTART 3604/4385))
- client_server/DB/1GB/1GB_33780_65 (Drop rate: 0.000606, 56.57 MiB/s over 14.81s) ... OPTIMAL
- client_server/DB/1GB/1GB_55776_67 (Drop rate: 0.180451, 56.66 MiB/s over 18.04s)
- client_server/DB/1GB/1GB_36552_68 (Drop rate: 0.179020, 56.86 MiB/s over 17.99s)
  
### BDP + Queue_effective - MSS
- Estiated R_arrivale for TGR: 500Mbit is **1058.2Mbit** (`python3 calculation.py --rate-mbit 500  --rtt
-ms 0.4  --tbf-limit 100000b --optimal-cwnd 65  --json`)

### BDP + Queue_size - MSS
- cwnd: 84 (`python3 calculation.py --rate-mbit 500 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 84
- client_server/DB/1GB/1GB_50558_84 (Drop rate: 0.189765, 56.77 MiB/s over 18.02s)

### BDP
- cwnd: 17 (`floor(BDP / MSS)`, BDP = 25000 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 17
- client_server/DB/1GB/1GB_59474_17 (18.03s (56.80 MiB/s), only SLOWSTART)









# TGR: 750 Mbit/s (burst size 50000b)  
## Q_config = 6250 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0
  
Taking more samples for balanced throughput
- client_server/DB/1GB/1GB_57514_0 (Drop rate: 0.463668, 22.28 MiB/s over 45.90s)
- client_server/DB/1GB/1GB_46544_0 (Drop rate: 0.463759, 18.83 MiB/s over 54.32s)
- client_server/DB/1GB/1GB_53600_0 (Drop rate: 0.464166, 18.98 MiB/s over 53.90s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_52268_4 (23.18s (44.18 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_53718_5 (Drop rate: 0.000272, 47.10 MiB/s over 21.72s)
- client_server/DB/1GB/1GB_50682_6 (Drop rate: 0.000265, 62.29 MiB/s over 16.42s)
- client_server/DB/1GB/1GB_40848_7 (Drop rate: 0.000255, 65.09 MiB/s over 15.72s)
- client_server/DB/1GB/1GB_38158_8 (Drop rate: 0.000279, 74.08 MiB/s over 13.81s)
  
Testing cwnd == 9 more times for better accuracy
- client_server/DB/1GB/1GB_44004_9 (Drop rate: 0.002091, 80.04 MiB/s over 12.78s)... OPTIMAL!!!
- client_server/DB/1GB/1GB_54772_9 (Drop rate: 0.001418, 81.03 MiB/s over 12.63s)
- client_server/DB/1GB/1GB_35808_9 (Drop rate: 0.000286, 62.47 MiB/s over 16.38s)
  
- client_server/DB/1GB/1GB_49120_10 (Drop rate: 0.466055, 10.02 MiB/s over 102.07s)
- client_server/DB/1GB/1GB_58776_10 (Drop rate: 0.465004, 13.28 MiB/s over 77.01s)

### BDP + Queue_effective - MSS
- cwnd: 3 (`python3 calculation.py --rate-mbit 750 --r-arrival-mbit 1529 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- client_server/DB/1GB/1GB_40738_3 (39.60s (25.86 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 28 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 28
- client_server/DB/1GB/1GB_39334_28 (Drop rate: 0.465424, 12.74 MiB/s over 80.29s)

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 25
- client_server/DB/1GB/1GB_55746_25 (Drop rate: 0.465675, 14.23 MiB/s over 71.90s)

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0
- client_server/DB/1GB/1GB_42886_0 (Drop rate: 0.419457, 71.96 MiB/s over 14.22s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_44146_10 (12.31s (83.19 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_40200_11 (Drop rate: 0.015198, 84.12 MiB/s over 11.85s)... OPTIMAL
- client_server/DB/1GB/1GB_38132_12 (Drop rate: 0.238126, 84.18 MiB/s over 12.15s)

### BDP + Queue_effective - MSS
- cwnd: 7 (`python3 calculation.py --rate-mbit 750 --r-arrival-mbit 1529 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- client_server/DB/1GB/1GB_34366_7 (16.21s (63.16 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 33 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 33
- client_server/DB/1GB/1GB_56996_33 (Drop rate: 0.415820, 73.66 MiB/s over 13.89s)

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 25
- client_server/DB/1GB/1GB_56908_25 (Drop rate: 0.417658, 75.44 MiB/s over 13.56s)

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0
- client_server/DB/1GB/1GB_47760_0 (Drop rate: 0.356108, 81.93 MiB/s over 12.49s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_40722_16 (12.03s (85.12 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_38358_17 (12.00s (85.34 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_39554_18 (Drop rate: 0.008998, 84.34 MiB/s over 8.05s (SLOWSTART 1020/3223))... OPTIMAL?
- client_server/DB/1GB/1GB_49228_19 (Drop rate: 0.141677, 85.02 MiB/s over 12.02s)
### BDP + Queue_effective - MSS
- cwnd: 15 (`python3 calculation.py --rate-mbit 750 --r-arrival-mbit 1529 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- client_server/DB/1GB/1GB_59382_15 (12.02s (85.20 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 41 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 41
- client_server/DB/1GB/1GB_50160_41 (Drop rate: 0.371702, 85.16 MiB/s over 12.01s)

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 25
- client_server/DB/1GB/1GB_44104_25 (Drop rate: 0.368493, 84.63 MiB/s over 12.09s)

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0
- client_server/DB/1GB/1GB_37610_0 (Drop rate: 0.219477, 85.23 MiB/s over 11.99s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_55360_33 (Drop rate: 0.000366, 83.76 MiB/s over 2.54s (SLOWSTART 2118/2735))
- client_server/DB/1GB/1GB_55574_34 (Drop rate: 0.035757, 84.97 MiB/s over 11.93s)... OPTIMAL?
- client_server/DB/1GB/1GB_56152_35 (Drop rate: 0.053421, 84.74 MiB/s over 12.04s)

### BDP + Queue_effective - MSS
- cwnd: 32 (`python3 calculation.py --rate-mbit 750 --r-arrival-mbit 1529 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- client_server/DB/1GB/1GB_34202_32 (12.08s (84.79 MiB/s), only SLOWSTART)

### BDP + Queue_size - MSS
- cwnd: 58 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 58
- client_server/DB/1GB/1GB_42312_58 (Drop rate: 0.209765, 84.48 MiB/s over 12.11s)

### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 25
- client_server/DB/1GB/1GB_34144_25 (12.01s (85.30 MiB/s), only SLOWSTART)

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0
- client_server/DB/1GB/1GB_51192_0 (Drop rate: 0.132002, 85.13 MiB/s over 12.00s)

### Empirical optimal cwnd (maximum throughput)
- client_server/DB/1GB/1GB_40626_65 (12.00s (85.35 MiB/s), only SLOWSTART)
- client_server/DB/1GB/1GB_53612_66 (Drop rate: 0.005957, 85.05 MiB/s over 9.60s (SLOWSTART 595/2686))... OPTIMAL?
- client_server/DB/1GB/1GB_42384_67 (Drop rate: 0.132682, 84.91 MiB/s over 12.05s )

### BDP + Queue_effective - MSS
- Estiated R_arrivale for TGR: 750Mbit is **1529Mbit** (`python3 calculation.py --rate-mbit 750  --rtt-ms 0.4  --tbf-limit 100000b --optimal-cwnd 66  --json`)

### BDP + Queue_size - MSS
- cwnd: 93 (`python3 calculation.py --rate-mbit 750 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 93
- client_server/DB/1GB/1GB_41120_93 (Drop rate: 0.131038, 85.16 MiB/s over 12.01s)
  
### BDP
- cwnd: 25 (`floor(BDP / MSS)`, BDP = 37500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 25
- client_server/DB/1GB/1GB_49098_25 (12.13s (84.45 MiB/s), only SLOWSTART)





















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
