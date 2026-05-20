- Note below, the TCP packets in the queue also includes the header, so we will just consider 1p = 1500 bytes.
- Also note the calculation process between different algorithms

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


# TGR: 250 Mbits (burst size 50000)
## 1p (TimeoutError: [Errno 110] Connection timed out)
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 1500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)
### BDP + Queue_effective - MSS
### BDP + Queue_size - MSS
### BDP 


## 2p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 3000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 3p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 4500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 7p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 10500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 10p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 15000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 11p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 16500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 20p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 30000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 33p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 49500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 67p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 










# TGR: 500 Mbits (burst size 50000)

## 1p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 1500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 2p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 3000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 3p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 4500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 7p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 10500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 10p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 15000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 11p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 16500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 20p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 30000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 33p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 49500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 67p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 






# TGR: 750 Mbits (burst size 50000)

## 1p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 1500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 2p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 3000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 3p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 4500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 7p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 10500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 10p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 15000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 11p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 16500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 20p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 30000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 33p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 49500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 67p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 






# TGR: 1000 Mbits (burst size 50000)

## 1p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 1500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 2p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 3000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 3p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 4500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 



## 7p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 10500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 10p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 15000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 11p 
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 16500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 20p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 30000b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


## 33p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 49500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 




## 67p
### TCP Reno
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100500b --cwnd 0

### Empirical optimal cwnd (maximum throughput)


### BDP + Queue_effective - MSS

### BDP + Queue_size - MSS

### BDP 


