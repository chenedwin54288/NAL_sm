In "client_server/report3/ft_RWND.md", we were able to make the client send the empirical rwnd to the server 
to let the server send with an optimal throughput. We later on also integrated, WeHe to the application
to use Wehe's replay function to estimate this empirical rwnd. However, as our application sends
data in "as fast as possible, capped at 1Gib/s" and the token generation rate is usually higher than 
the replaying rate of the WeHe server (TGN > WeHe replay), we cannot fill the TBF queue with the WeHe
server (the estimated rwnd is always smaller than the empirical rwnd, even when we use a replay 
that is mor aggresive). 

This is why, we decided to move on to the approach of estimating rwnd using culmulative bytes arrival rate .
The way how this works is that, at the start of the application, the server would do a 1.2s replay of 1Gib/s,
which the receiver would track the accumulated bytes with the timestamp. This readme contains the tracked result
of tis approach. 


Note that the replay is done in "bulk mode".
How about if we test with different burst size?
=> smaller burst size, more acurate values

### Queue Size = 6250 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <6.06, 27.65> | <5, 28.34> | <5, 28.34> | <11, 26.65> | <8, 28.28> |
| 500 Mbit/s | <9.59, 15.84> (3 runs) | <7, 56.94> | <2, 21.62> | <20, 17.60> | <17, 22.25> |
| 750 Mbit/s | <10.17, 20.03> (3 runs) | <9, 80.04> | <3, 25.86> | <28, 12.74> | <25, 14.23> |
| 1000 Mbit/s | <10.16, 16.38> | <9, 81.68> | <8, 74.80> | <37, 16.34> | <34, 15.03> |


#### 
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 5.683578s (226.704 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013033/cumulative_arrival.csv
Recommended rwnd: 11336 bytes (8 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 3.128941s (411.798 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013141/cumulative_arrival.csv
Recommended rwnd: 20590 bytes (15 MSS segments, RTT=0.4 ms)
   

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 3.277207s (393.167 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013250/cumulative_arrival.csv
Recommended rwnd: 19659 bytes (14 MSS segments, RTT=0.4 ms)


####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 6250b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 3.432822s (375.344 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013351/cumulative_arrival.csv
Recommended rwnd: 18768 bytes (13 MSS segments, RTT=0.4 ms)
- Received 161061274 bytes in 3.671266s (350.966 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013504/cumulative_arrival.csv
Recommended rwnd: 17549 bytes (13 MSS segments, RTT=0.4 ms)


### Queue Size = 12500 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <9.84, 28.43> | <8, 28.15> | <10, 28.31> | <16, 28.32> | <8, 28.15> |
| 500 Mbit/s | <11.54, 52.69> | <9, 56.58> | <6, 56.67> | <24, 56.75> | <17, 56.73> |
| 750 Mbit/s | <16.65, 71.96> | <11, 84.12> | <7, 63.16> | <33, 73.66> | <25, 75.44> |
| 1000 Mbit/s | <19.46, 67.15> | <17, 108.92> | <17, 108.92> | <41, 57.49> | <34, 53.46> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 5.660143s (227.643 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013611/cumulative_arrival.csv
Recommended rwnd: 11383 bytes (8 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.969034s (433.976 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013745/cumulative_arrival.csv
Recommended rwnd: 21699 bytes (15 MSS segments, RTT=0.4 ms)
- Received 161061274 bytes in 3.228748s (399.068 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013826/cumulative_arrival.csv
Recommended rwnd: 19954 bytes (14 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.289027s (562.899 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_013921/cumulative_arrival.csv
Recommended rwnd: 28145 bytes (20 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 12500b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.466071s (878.873 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014012/cumulative_arrival.csv
Recommended rwnd: 43944 bytes (31 MSS segments, RTT=0.4 ms)

### Queue Size = 25000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <18.20, 28.42> | <16, 28.43> | <17, 28.38> | <24, 28.38> | <8, 28.32> |
| 500 Mbit/s | <19.45, 56.95> | <17, 56.84> | <14, 56.42> | <33, 56.92> | <17, 56.61> |
| 750 Mbit/s | <23.72, 81.93> | <18, 84.34> | <15, 85.20> | <41, 85.16> | <25, 84.63> |
| 1000 Mbit/s | <39.15, 98.87> | <33, 111.79> | <34, 95.28> | <50, 105.72> | <34, 95.28> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 5.447271s (236.539 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014136/cumulative_arrival.csv
Recommended rwnd: 11827 bytes (9 MSS segments, RTT=0.4 ms)


####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.755978s (467.526 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014244/cumulative_arrival.csv
Recommended rwnd: 23377 bytes (17 MSS segments, RTT=0.4 ms)


####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.860625s (692.504 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014324/cumulative_arrival.csv
Recommended rwnd: 34626 bytes (24 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 25000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.477881s (519.997 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014402/cumulative_arrival.csv
Recommended rwnd: 26000 bytes (18 MSS segments, RTT=0.4 ms)
- Received 161061274 bytes in 1.386630s (929.225 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014437/cumulative_arrival.csv
Recommended rwnd: 46462 bytes (32 MSS segments, RTT=0.4 ms)
- Received 161061274 bytes in 2.376871s (542.095 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014508/cumulative_arrival.csv
Recommended rwnd: 27105 bytes (19 MSS segments, RTT=0.4 ms)


### Queue Size = 50000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <35.57, 28.46> | <33, 28.43> | <34, 28.46> | <41, 28.43> | <8, 28.34> |
| 500 Mbit/s | <36.99, 56.87> | <33, 56.79> | <31, 56.69> | <50, 56.83> | <17, 56.13> |
| 750 Mbit/s | <42.25, 85.23> | <34, 84.97> | <32, 84.79> | <58, 84.48> | <25, 85.30> |
| 1000 Mbit/s | <58.11, 111.87> | <67, 112.08> | <67, 112.08> | <67, 112.08> | <34, 111.75> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 5.399258s (238.642 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014541/cumulative_arrival.csv
Recommended rwnd: 11933 bytes (9 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.726844s (472.521 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014715/cumulative_arrival.csv
Recommended rwnd: 23627 bytes (17 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.802123s (714.985 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014756/cumulative_arrival.csv
Recommended rwnd: 35750 bytes (25 MSS segments, RTT=0.4 ms)
  

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 50000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.381539s (932.648 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014859/cumulative_arrival.csv
Recommended rwnd: 46633 bytes (32 MSS segments, RTT=0.4 ms)

It seens like when queue_size is large enough, the throughput estimation will be more stable. However, in the cases above, the estimation have been all under-estimated. 

### Queue Size = 100000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <66.83, 28.47> | <65, 28.47> | <68, 28.45> | <76, 28.46> | <8, 28.39> |
| 500 Mbit/s | <66.88, 56.62> | <65, 56.57> | <65, 56.57> | <84, 56.77> | <17, 56.80> |
| 750 Mbit/s | <67.10, 85.13> | <66, 85.05> | <66, 85.05> | <93, 85.16> | <25, 84.45> |
| 1000 Mbit/s | <119.20, 111.40> | <102, 111.98> | <101, 111.67> | <101, 111.67> | <34, 110.51> |

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 250 --tbf-rate 250Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 5.401880s (238.526 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_014936/cumulative_arrival.csv
Recommended rwnd: 11927 bytes (9 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 500 --tbf-rate 500Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 2.728297s (472.269 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_015243/cumulative_arrival.csv
Recommended rwnd: 23614 bytes (17 MSS segments, RTT=0.4 ms)
- Received 161061274 bytes in 2.749123s (468.691 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_015342/cumulative_arrival.csv
Recommended rwnd: 23435 bytes (17 MSS segments, RTT=0.4 ms)

####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 750 --tbf-rate 750Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.861445s (692.199 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_015422/cumulative_arrival.csv
Recommended rwnd: 34610 bytes (24 MSS segments, RTT=0.4 ms)


####
- ./run.sh --cca my_cca --size-gib 1 --rtt-ms 0.4 --rate-mbit 1000 --tbf-rate 1000Mbit --tbf-burst 50000b --tbf-limit 100000b --cwnd 0 --cumulative-send-mode bulk
- Received 161061274 bytes in 1.373609s (938.032 Mbit/s)
Wrote cumulative samples to /home/nal/client_server/client_cul/client/cumulative_runs/20260608_015504/cumulative_arrival.csv
Recommended rwnd: 46902 bytes (33 MSS segments, RTT=0.4 ms)





Next idea: throughput estimation + 
