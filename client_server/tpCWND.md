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

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 11 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 6250b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 11

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 8

## Q_config = 12500 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 16 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 12500b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 16

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 8

## Q_config = 25000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 24 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 25000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 24

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 8

## Q_config = 50000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 41 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 50000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 41

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 8

## Q_config = 100000 bytes
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)

### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS
- cwnd: 76 (`python3 calculation.py --rate-mbit 250 --rtt-ms 0.4 --tbf-limit 100000b --json`)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 76

### BDP
- cwnd: 8 (`floor(BDP / MSS)`, BDP = 12500 bytes)
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 8















# TGR: 500 Mbit/s (burst size 50000b)
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
















# TGR: 750 Mbit/s (burst size 50000b)
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
