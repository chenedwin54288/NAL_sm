# Formatted tpCWND Results

This file reformats `tpCWND.md` and adds the drop-rate variant that counts both `loss_recovery` and `fast_retransmit` rows as drops.

## How to Read This File

- Summary-table cells use `<cwnd, throughput MiB/s>`.
- For capped runs, `cwnd` is the configured cwnd from the run directory or calculation.
- For TCP Reno, `cwnd` is the average post-slow-start top cwnd. If a TCP Reno section has multiple runs, the table uses the mean of the per-run averages and the mean throughput.
- Throughput uses post-slow-start throughput when `server.log` detected slow-start exit; otherwise it uses total-transfer throughput.
- `DR(loss)` is `loss_recovery / row_count`. `DR(loss+fast)` is `(loss_recovery + fast_retransmit) / row_count`.

## Calculation Notes

```text
BDP = R_tbf * RTT_base
Q_tbf = max(0, (R_arrival - R_tbf) * RTT_base)
Q_effective = max(0, Q_config - Q_tbf)
arrival-aware cwnd = floor((BDP + Q_effective - MSS) / MSS)
original queue-size cwnd = floor((BDP + Q_config - MSS) / MSS)
BDP cwnd = floor(BDP / MSS)
```

When `Q_tbf > Q_config`, the arrival-aware calculation uses the reduced usable BDP branch from `calculation.py`.

## TCP Reno Top-CWND Example

Example run: [1GB_41298_0](DB/1GB/1GB_41298_0), the TCP Reno run for `1000Mbit` and `Q_config=100000 bytes`.

1. In `filtered_context.csv`, rows 1-4 are `slow_start`, so the post-slow-start scan starts at row 5.
2. A top cwnd is a cwnd sample whose next sample is lower.
3. The post-slow-start top cwnds are `94, 120, 108, 134, 140`.
4. Average top cwnd = `(94 + 120 + 108 + 134 + 140) / 5 = 119.20`.

## Summary Tables

There are five queue-size tables because the sweep has five queue sizes.

### Queue Size = 6250 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <6.06, 27.65> | <5, 28.34> | <5, 28.34> | <11, 26.65> | <8, 28.28> |
| 500 Mbit/s | <9.59, 15.84> (3 runs) | <7, 56.94> | <2, 21.62> | <20, 17.60> | <17, 22.25> |
| 750 Mbit/s | <10.17, 20.03> (3 runs) | <9, 80.04> | <3, 25.86> | <28, 12.74> | <25, 14.23> |
| 1000 Mbit/s | <10.16, 16.38> | <9, 81.68> | <8, 74.80> | <37, 16.34> | <34, 15.03> |

### Queue Size = 12500 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <9.84, 28.43> | <8, 28.15> | <10, 28.31> | <16, 28.32> | <8, 28.15> |
| 500 Mbit/s | <11.54, 52.69> | <9, 56.58> | <6, 56.67> | <24, 56.75> | <17, 56.73> |
| 750 Mbit/s | <16.65, 71.96> | <11, 84.12> | <7, 63.16> | <33, 73.66> | <25, 75.44> |
| 1000 Mbit/s | <19.46, 67.15> | <17, 108.92> | <17, 108.92> | <41, 57.49> | <34, 53.46> |

### Queue Size = 25000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <18.20, 28.42> | <16, 28.43> | <17, 28.38> | <24, 28.38> | <8, 28.32> |
| 500 Mbit/s | <19.45, 56.95> | <17, 56.84> | <14, 56.42> | <33, 56.92> | <17, 56.61> |
| 750 Mbit/s | <23.72, 81.93> | <18, 84.34> | <15, 85.20> | <41, 85.16> | <25, 84.63> |
| 1000 Mbit/s | <39.15, 98.87> | <33, 111.79> | <34, 95.28> | <50, 105.72> | <34, 95.28> |

### Queue Size = 50000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <35.57, 28.46> | <33, 28.43> | <34, 28.46> | <41, 28.43> | <8, 28.34> |
| 500 Mbit/s | <36.99, 56.87> | <33, 56.79> | <31, 56.69> | <50, 56.83> | <17, 56.13> |
| 750 Mbit/s | <42.25, 85.23> | <34, 84.97> | <32, 84.79> | <58, 84.48> | <25, 85.30> |
| 1000 Mbit/s | <58.11, 111.87> | <67, 112.08> | <67, 112.08> | <67, 112.08> | <34, 111.75> |

### Queue Size = 100000 bytes

| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_effective - MSS | BDP + Q_size - MSS | BDP |
|---:|---:|---:|---:|---:|---:|
| 250 Mbit/s | <66.83, 28.47> | <65, 28.47> | <68, 28.45> | <76, 28.46> | <8, 28.39> |
| 500 Mbit/s | <66.88, 56.62> | <65, 56.57> | <65, 56.57> | <84, 56.77> | <17, 56.80> |
| 750 Mbit/s | <67.10, 85.13> | <66, 85.05> | <66, 85.05> | <93, 85.16> | <25, 84.45> |
| 1000 Mbit/s | <119.20, 111.40> | <102, 111.98> | <101, 111.67> | <101, 111.67> | <34, 110.51> |

## CWND Size Plots

Each plot converts the table cwnd value from segments to bytes with `cwnd_bytes = cwnd * 1460`.

### Queue Size = 6250 bytes

![CWND size plot for queue size 6250 bytes](research_images/ft_tpCWND/queue_6250_bytes_cwnd.png)

### Queue Size = 12500 bytes

![CWND size plot for queue size 12500 bytes](research_images/ft_tpCWND/queue_12500_bytes_cwnd.png)

### Queue Size = 25000 bytes

![CWND size plot for queue size 25000 bytes](research_images/ft_tpCWND/queue_25000_bytes_cwnd.png)

### Queue Size = 50000 bytes

![CWND size plot for queue size 50000 bytes](research_images/ft_tpCWND/queue_50000_bytes_cwnd.png)

### Queue Size = 100000 bytes

![CWND size plot for queue size 100000 bytes](research_images/ft_tpCWND/queue_100000_bytes_cwnd.png)

## Detailed Results

### TGR = 250 Mbit/s

#### Q_config = 6250 bytes

##### TCP Reno

- Table value: <6.06, 27.65> from 1 run(s).
- [1GB_48996_0](DB/1GB/1GB_48996_0); cwnd=0; throughput=27.65 MiB/s; elapsed=36.99s; DR(loss)=0.490038 (40631/82914); DR(loss+fast)=0.490038 (40631/82914); avg top cwnd=6.06; tops=39852; no slow_start samples captured.

##### Empirical

- Table selection: [1GB_47616_5](DB/1GB/1GB_47616_5) with <5, 28.34>.
- [1GB_43924_4](DB/1GB/1GB_43924_4); cwnd=4; throughput=28.08 MiB/s; elapsed=36.46s; DR(loss)=0.000267 (1/3746); DR(loss+fast)=0.000267 (1/3746); throughput source=total transfer.
- [1GB_47616_5](DB/1GB/1GB_47616_5); cwnd=5; throughput=28.34 MiB/s; elapsed=36.09s; DR(loss)=0.002897 (11/3797); DR(loss+fast)=0.002897 (11/3797); source note=OPTIMAL.
- [1GB_55966_6](DB/1GB/1GB_55966_6); cwnd=6; throughput=28.33 MiB/s; elapsed=36.11s; DR(loss)=0.458405 (15958/34812); DR(loss+fast)=0.458405 (15958/34812).

##### BDP + Q_effective - MSS

- Calculation cwnd: 5.
- Note: Uses the 415.62 Mbit/s R_arrival estimate; the 472.6 Mbit/s estimate gives cwnd 3.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 11.
- [1GB_42902_11](DB/1GB/1GB_42902_11); cwnd=11; throughput=26.65 MiB/s; elapsed=38.39s; DR(loss)=0.489593 (40553/82830); DR(loss+fast)=0.489593 (40553/82830).

##### BDP

- Calculation cwnd: 8.
- [1GB_57162_8](DB/1GB/1GB_57162_8); cwnd=8; throughput=28.28 MiB/s; elapsed=36.17s; DR(loss)=0.481111 (26630/55351); DR(loss+fast)=0.481111 (26630/55351).

#### Q_config = 12500 bytes

##### TCP Reno

- Table value: <9.84, 28.43> from 1 run(s).
- [1GB_49098_0](DB/1GB/1GB_49098_0); cwnd=0; throughput=28.43 MiB/s; elapsed=35.99s; DR(loss)=0.451210 (13798/30580); DR(loss+fast)=0.451210 (13798/30580); avg top cwnd=9.84; tops=13491; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_59776_8](DB/1GB/1GB_59776_8) with <8, 28.15>.
- [1GB_32906_7](DB/1GB/1GB_32906_7); cwnd=7; throughput=28.09 MiB/s; elapsed=6.19s; DR(loss)=0.000456 (2/4385); DR(loss+fast)=0.000456 (2/4385).
- [1GB_59776_8](DB/1GB/1GB_59776_8); cwnd=8; throughput=28.15 MiB/s; elapsed=5.93s; DR(loss)=0.014961 (56/3743); DR(loss+fast)=0.014961 (56/3743); source note=OPTIMAL.
- [1GB_37122_9](DB/1GB/1GB_37122_9); cwnd=9; throughput=28.39 MiB/s; elapsed=36.04s; DR(loss)=0.422830 (8742/20675); DR(loss+fast)=0.422830 (8742/20675).

##### BDP + Q_effective - MSS

- Calculation cwnd: 10.
- [1GB_53654_10](DB/1GB/1GB_53654_10); cwnd=10; throughput=28.31 MiB/s; elapsed=36.14s; DR(loss)=0.452537 (13706/30287); DR(loss+fast)=0.452537 (13706/30287).

##### BDP + Q_size - MSS

- Calculation cwnd: 16.
- [1GB_47956_16](DB/1GB/1GB_47956_16); cwnd=16; throughput=28.32 MiB/s; elapsed=36.13s; DR(loss)=0.453666 (13840/30507); DR(loss+fast)=0.453666 (13840/30507).

##### BDP

- Calculation cwnd: 8.
- [1GB_59776_8](DB/1GB/1GB_59776_8); cwnd=8; throughput=28.15 MiB/s; elapsed=5.93s; DR(loss)=0.014961 (56/3743); DR(loss+fast)=0.014961 (56/3743).

#### Q_config = 25000 bytes

##### TCP Reno

- Table value: <18.20, 28.42> from 1 run(s).
- [1GB_35990_0](DB/1GB/1GB_35990_0); cwnd=0; throughput=28.42 MiB/s; elapsed=36.00s; DR(loss)=0.412677 (4792/11612); DR(loss+fast)=0.412677 (4792/11612); avg top cwnd=18.20; tops=4692; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_54104_16](DB/1GB/1GB_54104_16) with <16, 28.43>.
- [1GB_54104_16](DB/1GB/1GB_54104_16); cwnd=16; throughput=28.43 MiB/s; elapsed=36.02s; DR(loss)=0.000000 (0/2058); DR(loss+fast)=0.000000 (0/2058); throughput source=total transfer; source note=OPTIMAL.

##### BDP + Q_effective - MSS

- Calculation cwnd: 17.
- [1GB_57896_17](DB/1GB/1GB_57896_17); cwnd=17; throughput=28.38 MiB/s; elapsed=36.04s; DR(loss)=0.381511 (3413/8946); DR(loss+fast)=0.381511 (3413/8946).

##### BDP + Q_size - MSS

- Calculation cwnd: 24.
- [1GB_38022_24](DB/1GB/1GB_38022_24); cwnd=24; throughput=28.38 MiB/s; elapsed=36.05s; DR(loss)=0.415021 (4791/11544); DR(loss+fast)=0.415021 (4791/11544).

##### BDP

- Calculation cwnd: 8.
- [1GB_43544_8](DB/1GB/1GB_43544_8); cwnd=8; throughput=28.32 MiB/s; elapsed=36.16s; DR(loss)=0.000000 (0/3505); DR(loss+fast)=0.000000 (0/3505); throughput source=total transfer.

#### Q_config = 50000 bytes

##### TCP Reno

- Table value: <35.57, 28.46> from 1 run(s).
- [1GB_51446_0](DB/1GB/1GB_51446_0); cwnd=0; throughput=28.46 MiB/s; elapsed=35.95s; DR(loss)=0.327819 (1407/4292); DR(loss+fast)=0.327819 (1407/4292); avg top cwnd=35.57; tops=1374; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_44938_33](DB/1GB/1GB_44938_33) with <33, 28.43>.
- [1GB_44938_33](DB/1GB/1GB_44938_33); cwnd=33; throughput=28.43 MiB/s; elapsed=34.37s; DR(loss)=0.022270 (31/1392); DR(loss+fast)=0.022270 (31/1392); source note=OPTIMAL.

##### BDP + Q_effective - MSS

- Calculation cwnd: 34.
- [1GB_44228_34](DB/1GB/1GB_44228_34); cwnd=34; throughput=28.46 MiB/s; elapsed=35.94s; DR(loss)=0.323831 (1295/3999); DR(loss+fast)=0.323831 (1295/3999).

##### BDP + Q_size - MSS

- Calculation cwnd: 41.
- [1GB_40142_41](DB/1GB/1GB_40142_41); cwnd=41; throughput=28.43 MiB/s; elapsed=35.99s; DR(loss)=0.334123 (1411/4223); DR(loss+fast)=0.334123 (1411/4223).

##### BDP

- Calculation cwnd: 8.
- [1GB_58506_8](DB/1GB/1GB_58506_8); cwnd=8; throughput=28.34 MiB/s; elapsed=36.13s; DR(loss)=0.000000 (0/3710); DR(loss+fast)=0.000000 (0/3710); throughput source=total transfer.

#### Q_config = 100000 bytes

##### TCP Reno

- Table value: <66.83, 28.47> from 1 run(s).
- [1GB_50088_0](DB/1GB/1GB_50088_0); cwnd=0; throughput=28.47 MiB/s; elapsed=35.94s; DR(loss)=0.219525 (434/1977); DR(loss+fast)=0.219525 (434/1977); avg top cwnd=66.83; tops=419; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_45748_65](DB/1GB/1GB_45748_65) with <65, 28.47>.
- [1GB_39048_64](DB/1GB/1GB_39048_64); cwnd=64; throughput=28.47 MiB/s; elapsed=35.96s; DR(loss)=0.000000 (0/1104); DR(loss+fast)=0.000000 (0/1104); throughput source=total transfer.
- [1GB_45748_65](DB/1GB/1GB_45748_65); cwnd=65; throughput=28.47 MiB/s; elapsed=32.00s; DR(loss)=0.008881 (10/1126); DR(loss+fast)=0.008881 (10/1126); source note=OPTIMAL.
- [1GB_36258_66](DB/1GB/1GB_36258_66); cwnd=66; throughput=28.48 MiB/s; elapsed=35.68s; DR(loss)=0.087956 (111/1262); DR(loss+fast)=0.087956 (111/1262).
- [1GB_51008_67](DB/1GB/1GB_51008_67); cwnd=67; throughput=28.47 MiB/s; elapsed=35.89s; DR(loss)=0.225230 (441/1958); DR(loss+fast)=0.225230 (441/1958).

##### BDP + Q_effective - MSS

- Calculation cwnd: 68.
- [1GB_55870_68](DB/1GB/1GB_55870_68); cwnd=68; throughput=28.45 MiB/s; elapsed=35.94s; DR(loss)=0.230769 (444/1924); DR(loss+fast)=0.230769 (444/1924).

##### BDP + Q_size - MSS

- Calculation cwnd: 76.
- [1GB_54576_76](DB/1GB/1GB_54576_76); cwnd=76; throughput=28.46 MiB/s; elapsed=35.95s; DR(loss)=0.232255 (445/1916); DR(loss+fast)=0.232255 (445/1916).

##### BDP

- Calculation cwnd: 8.
- [1GB_39700_8](DB/1GB/1GB_39700_8); cwnd=8; throughput=28.39 MiB/s; elapsed=36.07s; DR(loss)=0.000000 (0/3756); DR(loss+fast)=0.000000 (0/3756); throughput source=total transfer.

### TGR = 500 Mbit/s

#### Q_config = 6250 bytes

##### TCP Reno

- Table value: <9.59, 15.84> from 3 run(s).
- [1GB_37946_0](DB/1GB/1GB_37946_0); cwnd=0; throughput=15.87 MiB/s; elapsed=64.46s; DR(loss)=0.468926 (18403/39245); DR(loss+fast)=0.468926 (18403/39245); avg top cwnd=9.66; tops=17537; post-slow-start start row=956.
- [1GB_43236_0](DB/1GB/1GB_43236_0); cwnd=0; throughput=16.70 MiB/s; elapsed=61.27s; DR(loss)=0.468758 (18470/39402); DR(loss+fast)=0.468758 (18470/39402); avg top cwnd=9.62; tops=18025; no slow_start samples captured.
- [1GB_42906_0](DB/1GB/1GB_42906_0); cwnd=0; throughput=14.96 MiB/s; elapsed=68.37s; DR(loss)=0.468044 (18374/39257); DR(loss+fast)=0.468044 (18374/39257); avg top cwnd=9.48; tops=2135; post-slow-start start row=34592.

##### Empirical

- Table selection: [1GB_41802_7](DB/1GB/1GB_41802_7) with <7, 56.94>.
- [1GB_56530_3](DB/1GB/1GB_56530_3); cwnd=3; throughput=18.79 MiB/s; elapsed=54.50s; DR(loss)=0.000273 (1/3662); DR(loss+fast)=0.000273 (1/3662); throughput source=total transfer.
- [1GB_53576_4](DB/1GB/1GB_53576_4); cwnd=4; throughput=44.46 MiB/s; elapsed=23.03s; DR(loss)=0.000267 (1/3742); DR(loss+fast)=0.000267 (1/3742); throughput source=total transfer.
- [1GB_40956_5](DB/1GB/1GB_40956_5); cwnd=5; throughput=47.47 MiB/s; elapsed=21.55s; DR(loss)=0.000270 (1/3707); DR(loss+fast)=0.000270 (1/3707).
- [1GB_50208_5](DB/1GB/1GB_50208_5); cwnd=5; throughput=44.83 MiB/s; elapsed=22.82s; DR(loss)=0.000280 (1/3577); DR(loss+fast)=0.000280 (1/3577).
- [1GB_59138_5](DB/1GB/1GB_59138_5); cwnd=5; throughput=47.16 MiB/s; elapsed=21.69s; DR(loss)=0.000270 (1/3697); DR(loss+fast)=0.000270 (1/3697).
- [1GB_43198_6](DB/1GB/1GB_43198_6); cwnd=6; throughput=56.37 MiB/s; elapsed=18.15s; DR(loss)=0.016819 (68/4043); DR(loss+fast)=0.016819 (68/4043).
- [1GB_41802_7](DB/1GB/1GB_41802_7); cwnd=7; throughput=56.94 MiB/s; elapsed=17.97s; DR(loss)=0.000502 (2/3983); DR(loss+fast)=0.000502 (2/3983); source note=OPTIMAL.
- [1GB_47016_8](DB/1GB/1GB_47016_8); cwnd=8; throughput=56.86 MiB/s; elapsed=17.99s; DR(loss)=0.263779 (1900/7203); DR(loss+fast)=0.263779 (1900/7203).
- [1GB_47358_9](DB/1GB/1GB_47358_9); cwnd=9; throughput=56.76 MiB/s; elapsed=18.02s; DR(loss)=0.440519 (9702/22024); DR(loss+fast)=0.440519 (9702/22024).

##### BDP + Q_effective - MSS

- Calculation cwnd: 2.
- [1GB_38186_2](DB/1GB/1GB_38186_2); cwnd=2; throughput=21.62 MiB/s; elapsed=47.37s; DR(loss)=0.000268 (1/3734); DR(loss+fast)=0.000268 (1/3734); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 20.
- [1GB_46054_20](DB/1GB/1GB_46054_20); cwnd=20; throughput=17.60 MiB/s; elapsed=58.12s; DR(loss)=0.467844 (18223/38951); DR(loss+fast)=0.467844 (18223/38951).

##### BDP

- Calculation cwnd: 17.
- [1GB_43898_17](DB/1GB/1GB_43898_17); cwnd=17; throughput=22.25 MiB/s; elapsed=45.97s; DR(loss)=0.469217 (18497/39421); DR(loss+fast)=0.469217 (18497/39421).

#### Q_config = 12500 bytes

##### TCP Reno

- Table value: <11.54, 52.69> from 1 run(s).
- [1GB_54150_0](DB/1GB/1GB_54150_0); cwnd=0; throughput=52.69 MiB/s; elapsed=19.41s; DR(loss)=0.453230 (12244/27015); DR(loss+fast)=0.453230 (12244/27015); avg top cwnd=11.54; tops=11922; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_52890_9](DB/1GB/1GB_52890_9) with <9, 56.58>.
- [1GB_58828_7](DB/1GB/1GB_58828_7); cwnd=7; throughput=56.10 MiB/s; elapsed=18.25s; DR(loss)=0.000000 (0/4217); DR(loss+fast)=0.000000 (0/4217); throughput source=total transfer.
- [1GB_38632_8](DB/1GB/1GB_38632_8); cwnd=8; throughput=56.78 MiB/s; elapsed=18.03s; DR(loss)=0.000000 (0/3670); DR(loss+fast)=0.000000 (0/3670); throughput source=total transfer.
- [1GB_52890_9](DB/1GB/1GB_52890_9); cwnd=9; throughput=56.58 MiB/s; elapsed=17.85s; DR(loss)=0.001070 (4/3740); DR(loss+fast)=0.001070 (4/3740); source note=OPTIMAL.
- [1GB_38434_10](DB/1GB/1GB_38434_10); cwnd=10; throughput=56.62 MiB/s; elapsed=18.07s; DR(loss)=0.403353 (6183/15329); DR(loss+fast)=0.403353 (6183/15329).

##### BDP + Q_effective - MSS

- Calculation cwnd: 6.
- [1GB_53636_6](DB/1GB/1GB_53636_6); cwnd=6; throughput=56.67 MiB/s; elapsed=18.07s; DR(loss)=0.000000 (0/3693); DR(loss+fast)=0.000000 (0/3693); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 24.
- [1GB_35456_24](DB/1GB/1GB_35456_24); cwnd=24; throughput=56.75 MiB/s; elapsed=18.03s; DR(loss)=0.453997 (13091/28835); DR(loss+fast)=0.453997 (13091/28835).

##### BDP

- Calculation cwnd: 17.
- [1GB_45268_17](DB/1GB/1GB_45268_17); cwnd=17; throughput=56.73 MiB/s; elapsed=18.03s; DR(loss)=0.445223 (10859/24390); DR(loss+fast)=0.445223 (10859/24390).

#### Q_config = 25000 bytes

##### TCP Reno

- Table value: <19.45, 56.95> from 1 run(s).
- [1GB_51592_0](DB/1GB/1GB_51592_0); cwnd=0; throughput=56.95 MiB/s; elapsed=17.96s; DR(loss)=0.381196 (4391/11519); DR(loss+fast)=0.381196 (4391/11519); avg top cwnd=19.45; tops=4242; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_50214_17](DB/1GB/1GB_50214_17) with <17, 56.84>.
- [1GB_49998_15](DB/1GB/1GB_49998_15); cwnd=15; throughput=56.87 MiB/s; elapsed=18.01s; DR(loss)=0.000000 (0/3199); DR(loss+fast)=0.000000 (0/3199); throughput source=total transfer.
- [1GB_35082_16](DB/1GB/1GB_35082_16); cwnd=16; throughput=56.56 MiB/s; elapsed=18.10s; DR(loss)=0.000000 (0/2865); DR(loss+fast)=0.000000 (0/2865); throughput source=total transfer.
- [1GB_50214_17](DB/1GB/1GB_50214_17); cwnd=17; throughput=56.84 MiB/s; elapsed=17.98s; DR(loss)=0.150939 (667/4419); DR(loss+fast)=0.150939 (667/4419); source note=OPTIMAL.

##### BDP + Q_effective - MSS

- Calculation cwnd: 14.
- [1GB_40012_14](DB/1GB/1GB_40012_14); cwnd=14; throughput=56.42 MiB/s; elapsed=18.15s; DR(loss)=0.000000 (0/3121); DR(loss+fast)=0.000000 (0/3121); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 33.
- [1GB_48388_33](DB/1GB/1GB_48388_33); cwnd=33; throughput=56.92 MiB/s; elapsed=17.97s; DR(loss)=0.377370 (4359/11551); DR(loss+fast)=0.377370 (4359/11551).

##### BDP

- Calculation cwnd: 17.
- [1GB_58940_17](DB/1GB/1GB_58940_17); cwnd=17; throughput=56.61 MiB/s; elapsed=18.07s; DR(loss)=0.141003 (630/4468); DR(loss+fast)=0.141003 (630/4468).

#### Q_config = 50000 bytes

##### TCP Reno

- Table value: <36.99, 56.87> from 1 run(s).
- [1GB_47586_0](DB/1GB/1GB_47586_0); cwnd=0; throughput=56.87 MiB/s; elapsed=17.99s; DR(loss)=0.273276 (1359/4973); DR(loss+fast)=0.273276 (1359/4973); avg top cwnd=36.99; tops=1300; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_33104_33](DB/1GB/1GB_33104_33) with <33, 56.79>.
- [1GB_40718_32](DB/1GB/1GB_40718_32); cwnd=32; throughput=56.90 MiB/s; elapsed=18.00s; DR(loss)=0.000000 (0/2397); DR(loss+fast)=0.000000 (0/2397); throughput source=total transfer.
- [1GB_33104_33](DB/1GB/1GB_33104_33); cwnd=33; throughput=56.79 MiB/s; elapsed=15.97s; DR(loss)=0.005920 (14/2365); DR(loss+fast)=0.005920 (14/2365); source note=OPTIMAL.
- [1GB_53090_34](DB/1GB/1GB_53090_34); cwnd=34; throughput=56.71 MiB/s; elapsed=18.04s; DR(loss)=0.201076 (822/4088); DR(loss+fast)=0.201076 (822/4088).

##### BDP + Q_effective - MSS

- Calculation cwnd: 31.
- [1GB_51718_31](DB/1GB/1GB_51718_31); cwnd=31; throughput=56.69 MiB/s; elapsed=18.06s; DR(loss)=0.000000 (0/2448); DR(loss+fast)=0.000000 (0/2448); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 50.
- [1GB_38558_50](DB/1GB/1GB_38558_50); cwnd=50; throughput=56.83 MiB/s; elapsed=18.00s; DR(loss)=0.263398 (1327/5038); DR(loss+fast)=0.263398 (1327/5038).

##### BDP

- Calculation cwnd: 17.
- [1GB_51028_17](DB/1GB/1GB_51028_17); cwnd=17; throughput=56.13 MiB/s; elapsed=18.24s; DR(loss)=0.000000 (0/2894); DR(loss+fast)=0.000000 (0/2894); throughput source=total transfer.

#### Q_config = 100000 bytes

##### TCP Reno

- Table value: <66.88, 56.62> from 1 run(s).
- [1GB_57812_0](DB/1GB/1GB_57812_0); cwnd=0; throughput=56.62 MiB/s; elapsed=18.07s; DR(loss)=0.191323 (441/2305); DR(loss+fast)=0.191323 (441/2305); avg top cwnd=66.88; tops=419; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_33780_65](DB/1GB/1GB_33780_65) with <65, 56.57>.
- [1GB_33702_64](DB/1GB/1GB_33702_64); cwnd=64; throughput=56.97 MiB/s; elapsed=4.44s; DR(loss)=0.000698 (1/1432); DR(loss+fast)=0.000698 (1/1432).
- [1GB_33780_65](DB/1GB/1GB_33780_65); cwnd=65; throughput=56.57 MiB/s; elapsed=14.81s; DR(loss)=0.000606 (1/1649); DR(loss+fast)=0.000606 (1/1649); source note=OPTIMAL.
- [1GB_55776_67](DB/1GB/1GB_55776_67); cwnd=67; throughput=56.66 MiB/s; elapsed=18.04s; DR(loss)=0.180451 (456/2527); DR(loss+fast)=0.180451 (456/2527).
- [1GB_36552_68](DB/1GB/1GB_36552_68); cwnd=68; throughput=56.86 MiB/s; elapsed=17.99s; DR(loss)=0.179020 (442/2469); DR(loss+fast)=0.179020 (442/2469).

##### BDP + Q_effective - MSS

- Calculation cwnd: 65.
- Note: Calculation only in source notes; no run listed for this method.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 84.
- [1GB_50558_84](DB/1GB/1GB_50558_84); cwnd=84; throughput=56.77 MiB/s; elapsed=18.02s; DR(loss)=0.189765 (445/2345); DR(loss+fast)=0.189765 (445/2345).

##### BDP

- Calculation cwnd: 17.
- [1GB_59474_17](DB/1GB/1GB_59474_17); cwnd=17; throughput=56.80 MiB/s; elapsed=18.03s; DR(loss)=0.000000 (0/2997); DR(loss+fast)=0.000000 (0/2997); throughput source=total transfer.

### TGR = 750 Mbit/s

#### Q_config = 6250 bytes

##### TCP Reno

- Table value: <10.17, 20.03> from 3 run(s).
- [1GB_57514_0](DB/1GB/1GB_57514_0); cwnd=0; throughput=22.28 MiB/s; elapsed=45.90s; DR(loss)=0.463668 (17063/36800); DR(loss+fast)=0.463668 (17063/36800); avg top cwnd=10.17; tops=16674; no slow_start samples captured.
- [1GB_46544_0](DB/1GB/1GB_46544_0); cwnd=0; throughput=18.83 MiB/s; elapsed=54.32s; DR(loss)=0.463759 (17090/36851); DR(loss+fast)=0.463759 (17090/36851); avg top cwnd=10.17; tops=16710; no slow_start samples captured.
- [1GB_53600_0](DB/1GB/1GB_53600_0); cwnd=0; throughput=18.98 MiB/s; elapsed=53.90s; DR(loss)=0.464166 (17137/36920); DR(loss+fast)=0.464166 (17137/36920); avg top cwnd=10.16; tops=16775; no slow_start samples captured.

##### Empirical

- Table selection: [1GB_44004_9](DB/1GB/1GB_44004_9) with <9, 80.04>.
- [1GB_52268_4](DB/1GB/1GB_52268_4); cwnd=4; throughput=44.18 MiB/s; elapsed=23.18s; DR(loss)=0.000267 (1/3743); DR(loss+fast)=0.000267 (1/3743); throughput source=total transfer.
- [1GB_53718_5](DB/1GB/1GB_53718_5); cwnd=5; throughput=47.10 MiB/s; elapsed=21.72s; DR(loss)=0.000272 (1/3678); DR(loss+fast)=0.000272 (1/3678).
- [1GB_50682_6](DB/1GB/1GB_50682_6); cwnd=6; throughput=62.29 MiB/s; elapsed=16.42s; DR(loss)=0.000265 (1/3767); DR(loss+fast)=0.000265 (1/3767).
- [1GB_40848_7](DB/1GB/1GB_40848_7); cwnd=7; throughput=65.09 MiB/s; elapsed=15.72s; DR(loss)=0.000255 (1/3929); DR(loss+fast)=0.000255 (1/3929).
- [1GB_38158_8](DB/1GB/1GB_38158_8); cwnd=8; throughput=74.08 MiB/s; elapsed=13.81s; DR(loss)=0.000279 (1/3587); DR(loss+fast)=0.000279 (1/3587).
- [1GB_44004_9](DB/1GB/1GB_44004_9); cwnd=9; throughput=80.04 MiB/s; elapsed=12.78s; DR(loss)=0.002091 (7/3348); DR(loss+fast)=0.002091 (7/3348); source note=OPTIMAL.
- [1GB_54772_9](DB/1GB/1GB_54772_9); cwnd=9; throughput=81.03 MiB/s; elapsed=12.63s; DR(loss)=0.001418 (5/3527); DR(loss+fast)=0.001418 (5/3527).
- [1GB_35808_9](DB/1GB/1GB_35808_9); cwnd=9; throughput=62.47 MiB/s; elapsed=16.38s; DR(loss)=0.000286 (1/3500); DR(loss+fast)=0.000286 (1/3500).
- [1GB_49120_10](DB/1GB/1GB_49120_10); cwnd=10; throughput=10.02 MiB/s; elapsed=102.07s; DR(loss)=0.466055 (17004/36485); DR(loss+fast)=0.466055 (17004/36485).
- [1GB_58776_10](DB/1GB/1GB_58776_10); cwnd=10; throughput=13.28 MiB/s; elapsed=77.01s; DR(loss)=0.465004 (16915/36376); DR(loss+fast)=0.465004 (16915/36376).

##### BDP + Q_effective - MSS

- Calculation cwnd: 3.
- [1GB_40738_3](DB/1GB/1GB_40738_3); cwnd=3; throughput=25.86 MiB/s; elapsed=39.60s; DR(loss)=0.000272 (1/3679); DR(loss+fast)=0.000272 (1/3679); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 28.
- [1GB_39334_28](DB/1GB/1GB_39334_28); cwnd=28; throughput=12.74 MiB/s; elapsed=80.29s; DR(loss)=0.465424 (17203/36962); DR(loss+fast)=0.465424 (17203/36962).

##### BDP

- Calculation cwnd: 25.
- [1GB_55746_25](DB/1GB/1GB_55746_25); cwnd=25; throughput=14.23 MiB/s; elapsed=71.90s; DR(loss)=0.465675 (17162/36854); DR(loss+fast)=0.465675 (17162/36854).

#### Q_config = 12500 bytes

##### TCP Reno

- Table value: <16.65, 71.96> from 1 run(s).
- [1GB_42886_0](DB/1GB/1GB_42886_0); cwnd=0; throughput=71.96 MiB/s; elapsed=14.22s; DR(loss)=0.419457 (6364/15172); DR(loss+fast)=0.419457 (6364/15172); avg top cwnd=16.65; tops=6131; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_40200_11](DB/1GB/1GB_40200_11) with <11, 84.12>.
- [1GB_44146_10](DB/1GB/1GB_44146_10); cwnd=10; throughput=83.19 MiB/s; elapsed=12.31s; DR(loss)=0.000000 (0/3476); DR(loss+fast)=0.000000 (0/3476); throughput source=total transfer.
- [1GB_40200_11](DB/1GB/1GB_40200_11); cwnd=11; throughput=84.12 MiB/s; elapsed=11.85s; DR(loss)=0.015198 (55/3619); DR(loss+fast)=0.015198 (55/3619); source note=OPTIMAL.
- [1GB_38132_12](DB/1GB/1GB_38132_12); cwnd=12; throughput=84.18 MiB/s; elapsed=12.15s; DR(loss)=0.238126 (1454/6106); DR(loss+fast)=0.238126 (1454/6106).

##### BDP + Q_effective - MSS

- Calculation cwnd: 7.
- [1GB_34366_7](DB/1GB/1GB_34366_7); cwnd=7; throughput=63.16 MiB/s; elapsed=16.21s; DR(loss)=0.000000 (0/3636); DR(loss+fast)=0.000000 (0/3636); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 33.
- [1GB_56996_33](DB/1GB/1GB_56996_33); cwnd=33; throughput=73.66 MiB/s; elapsed=13.89s; DR(loss)=0.415820 (6629/15942); DR(loss+fast)=0.415820 (6629/15942).

##### BDP

- Calculation cwnd: 25.
- [1GB_56908_25](DB/1GB/1GB_56908_25); cwnd=25; throughput=75.44 MiB/s; elapsed=13.56s; DR(loss)=0.417658 (6424/15381); DR(loss+fast)=0.417658 (6424/15381).

#### Q_config = 25000 bytes

##### TCP Reno

- Table value: <23.72, 81.93> from 1 run(s).
- [1GB_47760_0](DB/1GB/1GB_47760_0); cwnd=0; throughput=81.93 MiB/s; elapsed=12.49s; DR(loss)=0.356108 (3221/9045); DR(loss+fast)=0.356108 (3221/9045); avg top cwnd=23.72; tops=3044; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_39554_18](DB/1GB/1GB_39554_18) with <18, 84.34>.
- [1GB_40722_16](DB/1GB/1GB_40722_16); cwnd=16; throughput=85.12 MiB/s; elapsed=12.03s; DR(loss)=0.000000 (0/3359); DR(loss+fast)=0.000000 (0/3359); throughput source=total transfer.
- [1GB_38358_17](DB/1GB/1GB_38358_17); cwnd=17; throughput=85.34 MiB/s; elapsed=12.00s; DR(loss)=0.000000 (0/3111); DR(loss+fast)=0.000000 (0/3111); throughput source=total transfer.
- [1GB_39554_18](DB/1GB/1GB_39554_18); cwnd=18; throughput=84.34 MiB/s; elapsed=8.05s; DR(loss)=0.008998 (29/3223); DR(loss+fast)=0.008998 (29/3223); source note=OPTIMAL.
- [1GB_49228_19](DB/1GB/1GB_49228_19); cwnd=19; throughput=85.02 MiB/s; elapsed=12.02s; DR(loss)=0.141677 (583/4115); DR(loss+fast)=0.141677 (583/4115).

##### BDP + Q_effective - MSS

- Calculation cwnd: 15.
- [1GB_59382_15](DB/1GB/1GB_59382_15); cwnd=15; throughput=85.20 MiB/s; elapsed=12.02s; DR(loss)=0.000000 (0/3193); DR(loss+fast)=0.000000 (0/3193); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 41.
- [1GB_50160_41](DB/1GB/1GB_50160_41); cwnd=41; throughput=85.16 MiB/s; elapsed=12.01s; DR(loss)=0.371702 (3649/9817); DR(loss+fast)=0.371702 (3649/9817).

##### BDP

- Calculation cwnd: 25.
- [1GB_44104_25](DB/1GB/1GB_44104_25); cwnd=25; throughput=84.63 MiB/s; elapsed=12.09s; DR(loss)=0.368493 (3787/10277); DR(loss+fast)=0.368493 (3787/10277).

#### Q_config = 50000 bytes

##### TCP Reno

- Table value: <42.25, 85.23> from 1 run(s).
- [1GB_37610_0](DB/1GB/1GB_37610_0); cwnd=0; throughput=85.23 MiB/s; elapsed=11.99s; DR(loss)=0.219477 (1075/4898); DR(loss+fast)=0.219477 (1075/4898); avg top cwnd=42.25; tops=1005; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_55574_34](DB/1GB/1GB_55574_34) with <34, 84.97>.
- [1GB_55360_33](DB/1GB/1GB_55360_33); cwnd=33; throughput=83.76 MiB/s; elapsed=2.54s; DR(loss)=0.000366 (1/2735); DR(loss+fast)=0.000366 (1/2735).
- [1GB_55574_34](DB/1GB/1GB_55574_34); cwnd=34; throughput=84.97 MiB/s; elapsed=11.93s; DR(loss)=0.035757 (119/3328); DR(loss+fast)=0.035757 (119/3328); source note=OPTIMAL.
- [1GB_56152_35](DB/1GB/1GB_56152_35); cwnd=35; throughput=84.74 MiB/s; elapsed=12.04s; DR(loss)=0.053421 (171/3201); DR(loss+fast)=0.053421 (171/3201).

##### BDP + Q_effective - MSS

- Calculation cwnd: 32.
- [1GB_34202_32](DB/1GB/1GB_34202_32); cwnd=32; throughput=84.79 MiB/s; elapsed=12.08s; DR(loss)=0.000000 (0/2812); DR(loss+fast)=0.000000 (0/2812); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 58.
- [1GB_42312_58](DB/1GB/1GB_42312_58); cwnd=58; throughput=84.48 MiB/s; elapsed=12.11s; DR(loss)=0.209765 (1044/4977); DR(loss+fast)=0.209765 (1044/4977).

##### BDP

- Calculation cwnd: 25.
- [1GB_34144_25](DB/1GB/1GB_34144_25); cwnd=25; throughput=85.30 MiB/s; elapsed=12.01s; DR(loss)=0.000000 (0/3022); DR(loss+fast)=0.000000 (0/3022); throughput source=total transfer.

#### Q_config = 100000 bytes

##### TCP Reno

- Table value: <67.10, 85.13> from 1 run(s).
- [1GB_51192_0](DB/1GB/1GB_51192_0); cwnd=0; throughput=85.13 MiB/s; elapsed=12.00s; DR(loss)=0.132002 (443/3356); DR(loss+fast)=0.132002 (443/3356); avg top cwnd=67.10; tops=422; post-slow-start start row=3.

##### Empirical

- Table selection: [1GB_53612_66](DB/1GB/1GB_53612_66) with <66, 85.05>.
- [1GB_40626_65](DB/1GB/1GB_40626_65); cwnd=65; throughput=85.35 MiB/s; elapsed=12.00s; DR(loss)=0.000000 (0/2845); DR(loss+fast)=0.000000 (0/2845); throughput source=total transfer.
- [1GB_53612_66](DB/1GB/1GB_53612_66); cwnd=66; throughput=85.05 MiB/s; elapsed=9.60s; DR(loss)=0.005957 (16/2686); DR(loss+fast)=0.005957 (16/2686); source note=OPTIMAL.
- [1GB_42384_67](DB/1GB/1GB_42384_67); cwnd=67; throughput=84.91 MiB/s; elapsed=12.05s; DR(loss)=0.132682 (462/3482); DR(loss+fast)=0.132682 (462/3482).

##### BDP + Q_effective - MSS

- Calculation cwnd: 66.
- Note: Calculation only in source notes; no run listed for this method.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 93.
- [1GB_41120_93](DB/1GB/1GB_41120_93); cwnd=93; throughput=85.16 MiB/s; elapsed=12.01s; DR(loss)=0.131038 (472/3602); DR(loss+fast)=0.131038 (472/3602).

##### BDP

- Calculation cwnd: 25.
- [1GB_49098_25](DB/1GB/1GB_49098_25); cwnd=25; throughput=84.45 MiB/s; elapsed=12.13s; DR(loss)=0.000000 (0/3294); DR(loss+fast)=0.000000 (0/3294); throughput source=total transfer.

### TGR = 1000 Mbit/s

#### Q_config = 6250 bytes

##### TCP Reno

- Table value: <10.16, 16.38> from 1 run(s).
- [1GB_53158_0](DB/1GB/1GB_53158_0); cwnd=0; throughput=16.38 MiB/s; elapsed=62.46s; DR(loss)=0.465010 (17124/36825); DR(loss+fast)=0.465010 (17124/36825); avg top cwnd=10.16; tops=16746; no slow_start samples captured.

##### Empirical

- Table selection: [1GB_53024_9](DB/1GB/1GB_53024_9) with <9, 81.68>.
- [1GB_40416_8](DB/1GB/1GB_40416_8); cwnd=8; throughput=74.80 MiB/s; elapsed=13.68s; DR(loss)=0.000274 (1/3643); DR(loss+fast)=0.000274 (1/3643).
- [1GB_50464_9](DB/1GB/1GB_50464_9); cwnd=9; throughput=80.66 MiB/s; elapsed=12.68s; DR(loss)=0.000295 (1/3393); DR(loss+fast)=0.000295 (1/3393).
- [1GB_53024_9](DB/1GB/1GB_53024_9); cwnd=9; throughput=81.68 MiB/s; elapsed=12.52s; DR(loss)=0.000294 (1/3397); DR(loss+fast)=0.000294 (1/3397).
- [1GB_47860_9](DB/1GB/1GB_47860_9); cwnd=9; throughput=80.40 MiB/s; elapsed=12.72s; DR(loss)=0.000299 (1/3347); DR(loss+fast)=0.000299 (1/3347).
- [1GB_58008_10](DB/1GB/1GB_58008_10); cwnd=10; throughput=11.44 MiB/s; elapsed=89.40s; DR(loss)=0.464480 (16934/36458); DR(loss+fast)=0.464480 (16934/36458).

##### BDP + Q_effective - MSS

- Calculation cwnd: 8.
- [1GB_40416_8](DB/1GB/1GB_40416_8); cwnd=8; throughput=74.80 MiB/s; elapsed=13.68s; DR(loss)=0.000274 (1/3643); DR(loss+fast)=0.000274 (1/3643).

##### BDP + Q_size - MSS

- Calculation cwnd: 37.
- [1GB_35476_37](DB/1GB/1GB_35476_37); cwnd=37; throughput=16.34 MiB/s; elapsed=62.60s; DR(loss)=0.462948 (17049/36827); DR(loss+fast)=0.462948 (17049/36827).

##### BDP

- Calculation cwnd: 34.
- [1GB_57946_34](DB/1GB/1GB_57946_34); cwnd=34; throughput=15.03 MiB/s; elapsed=68.07s; DR(loss)=0.464038 (17136/36928); DR(loss+fast)=0.464038 (17136/36928).

#### Q_config = 12500 bytes

##### TCP Reno

- Table value: <19.46, 67.15> from 1 run(s).
- [1GB_45216_0](DB/1GB/1GB_45216_0); cwnd=0; throughput=67.15 MiB/s; elapsed=15.24s; DR(loss)=0.397025 (4885/12304); DR(loss+fast)=0.397025 (4885/12304); avg top cwnd=19.46; tops=4694; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_53560_17](DB/1GB/1GB_53560_17) with <17, 108.92>.
- [1GB_40760_16](DB/1GB/1GB_40760_16); cwnd=16; throughput=90.24 MiB/s; elapsed=11.35s; DR(loss)=0.000000 (0/3091); DR(loss+fast)=0.000000 (0/3091); throughput source=total transfer.
- [1GB_53560_17](DB/1GB/1GB_53560_17); cwnd=17; throughput=108.92 MiB/s; elapsed=9.40s; DR(loss)=0.000000 (0/2854); DR(loss+fast)=0.000000 (0/2854); throughput source=total transfer; source note=OPTIMAL.
- [1GB_38928_17](DB/1GB/1GB_38928_17); cwnd=17; throughput=107.74 MiB/s; elapsed=9.50s; DR(loss)=0.000000 (0/2901); DR(loss+fast)=0.000000 (0/2901); throughput source=total transfer.
- [1GB_48178_17](DB/1GB/1GB_48178_17); cwnd=17; throughput=107.42 MiB/s; elapsed=9.53s; DR(loss)=0.000000 (0/2869); DR(loss+fast)=0.000000 (0/2869); throughput source=total transfer.
- [1GB_33978_18](DB/1GB/1GB_33978_18); cwnd=18; throughput=77.28 MiB/s; elapsed=13.24s; DR(loss)=0.295819 (2045/6913); DR(loss+fast)=0.295819 (2045/6913).

##### BDP + Q_effective - MSS

- Calculation cwnd: 17.
- [1GB_53560_17](DB/1GB/1GB_53560_17); cwnd=17; throughput=108.92 MiB/s; elapsed=9.40s; DR(loss)=0.000000 (0/2854); DR(loss+fast)=0.000000 (0/2854); throughput source=total transfer.

##### BDP + Q_size - MSS

- Calculation cwnd: 41.
- [1GB_52892_41](DB/1GB/1GB_52892_41); cwnd=41; throughput=57.49 MiB/s; elapsed=17.80s; DR(loss)=0.402268 (4966/12345); DR(loss+fast)=0.402268 (4966/12345).

##### BDP

- Calculation cwnd: 34.
- [1GB_40704_34](DB/1GB/1GB_40704_34); cwnd=34; throughput=53.46 MiB/s; elapsed=19.13s; DR(loss)=0.400145 (4973/12428); DR(loss+fast)=0.400145 (4973/12428).

#### Q_config = 25000 bytes

##### TCP Reno

- Table value: <39.15, 98.87> from 1 run(s).
- [1GB_54296_0](DB/1GB/1GB_54296_0); cwnd=0; throughput=98.87 MiB/s; elapsed=10.35s; DR(loss)=0.248795 (1239/4980); DR(loss+fast)=0.248795 (1239/4980); avg top cwnd=39.15; tops=1179; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_59422_33](DB/1GB/1GB_59422_33) with <33, 111.79>.
- [1GB_50452_32](DB/1GB/1GB_50452_32); cwnd=32; throughput=112.08 MiB/s; elapsed=9.13s; DR(loss)=0.000345 (1/2900); DR(loss+fast)=0.000345 (1/2900).
- [1GB_59422_33](DB/1GB/1GB_59422_33); cwnd=33; throughput=111.79 MiB/s; elapsed=9.16s; DR(loss)=0.000000 (0/2873); DR(loss+fast)=0.000000 (0/2873); throughput source=total transfer; source note=OPTIMAL.
- [1GB_33796_35](DB/1GB/1GB_33796_35); cwnd=35; throughput=82.05 MiB/s; elapsed=12.47s; DR(loss)=0.126055 (448/3554); DR(loss+fast)=0.127181 (452/3554); fast_retransmit=4.

##### BDP + Q_effective - MSS

- Calculation cwnd: 34.
- Note: Calculation only in source notes; no run listed for this method.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 50.
- [1GB_39790_50](DB/1GB/1GB_39790_50); cwnd=50; throughput=105.72 MiB/s; elapsed=9.68s; DR(loss)=0.229259 (1144/4990); DR(loss+fast)=0.229259 (1144/4990).

##### BDP

- Calculation cwnd: 34.
- [1GB_42658_34](DB/1GB/1GB_42658_34); cwnd=34; throughput=95.28 MiB/s; elapsed=10.74s; DR(loss)=0.147090 (556/3780); DR(loss+fast)=0.147090 (556/3780).

#### Q_config = 50000 bytes

##### TCP Reno

- Table value: <58.11, 111.87> from 1 run(s).
- [1GB_44360_0](DB/1GB/1GB_44360_0); cwnd=0; throughput=111.87 MiB/s; elapsed=9.14s; DR(loss)=0.003212 (10/3113); DR(loss+fast)=0.066817 (208/3113); fast_retransmit=198; avg top cwnd=58.11; tops=379; post-slow-start start row=2.

##### Empirical

- Table selection: [1GB_57156_67](DB/1GB/1GB_57156_67) with <67, 112.08>.
- [1GB_56430_66](DB/1GB/1GB_56430_66); cwnd=66; throughput=111.71 MiB/s; elapsed=9.16s; DR(loss)=0.000767 (2/2606); DR(loss+fast)=0.001151 (3/2606); fast_retransmit=1.
- [1GB_57156_67](DB/1GB/1GB_57156_67); cwnd=67; throughput=112.08 MiB/s; elapsed=9.13s; DR(loss)=0.001386 (4/2885); DR(loss+fast)=0.001386 (4/2885); source note=OPTIMAL.
- [1GB_35436_68](DB/1GB/1GB_35436_68); cwnd=68; throughput=112.00 MiB/s; elapsed=9.12s; DR(loss)=0.001379 (4/2901); DR(loss+fast)=0.037229 (108/2901); fast_retransmit=104.

##### BDP + Q_effective - MSS

- Calculation cwnd: 67.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 67.
- [1GB_57156_67](DB/1GB/1GB_57156_67); cwnd=67; throughput=112.08 MiB/s; elapsed=9.13s; DR(loss)=0.001386 (4/2885); DR(loss+fast)=0.001386 (4/2885).

##### BDP

- Calculation cwnd: 34.
- [1GB_34096_34](DB/1GB/1GB_34096_34); cwnd=34; throughput=111.75 MiB/s; elapsed=9.16s; DR(loss)=0.000000 (0/2682); DR(loss+fast)=0.000000 (0/2682); throughput source=total transfer.

#### Q_config = 100000 bytes

##### TCP Reno

- Table value: <119.20, 111.40> from 1 run(s).
- [1GB_41298_0](DB/1GB/1GB_41298_0); cwnd=0; throughput=111.40 MiB/s; elapsed=9.17s; DR(loss)=0.000000 (0/2502); DR(loss+fast)=0.003597 (9/2502); fast_retransmit=9; avg top cwnd=119.20; tops=5; post-slow-start start row=5.

##### Empirical

- Table selection: [1GB_47422_102](DB/1GB/1GB_47422_102) with <102, 111.98>.
- [1GB_47422_102](DB/1GB/1GB_47422_102); cwnd=102; throughput=111.98 MiB/s; elapsed=9.12s; DR(loss)=0.000348 (1/2874); DR(loss+fast)=0.001740 (5/2874); fast_retransmit=4; source note=OPTIMAL.
- [1GB_60986_103](DB/1GB/1GB_60986_103); cwnd=103; throughput=112.11 MiB/s; elapsed=9.12s; DR(loss)=0.000000 (0/2856); DR(loss+fast)=0.001050 (3/2856); fast_retransmit=3.
- [1GB_55214_105](DB/1GB/1GB_55214_105); cwnd=105; throughput=112.13 MiB/s; elapsed=9.11s; DR(loss)=0.000000 (0/2817); DR(loss+fast)=0.000710 (2/2817); fast_retransmit=2.
- [1GB_56564_110](DB/1GB/1GB_56564_110); cwnd=110; throughput=111.94 MiB/s; elapsed=9.13s; DR(loss)=0.000000 (0/2902); DR(loss+fast)=0.002757 (8/2902); fast_retransmit=8.
- [1GB_37612_115](DB/1GB/1GB_37612_115); cwnd=115; throughput=112.14 MiB/s; elapsed=3.94s; DR(loss)=0.000000 (0/2712); DR(loss+fast)=0.000369 (1/2712); fast_retransmit=1.
- [1GB_52694_120](DB/1GB/1GB_52694_120); cwnd=120; throughput=111.67 MiB/s; elapsed=9.03s; DR(loss)=0.000000 (0/2842); DR(loss+fast)=0.001759 (5/2842); fast_retransmit=5.
- [1GB_36534_125](DB/1GB/1GB_36534_125); cwnd=125; throughput=108.95 MiB/s; elapsed=7.39s; DR(loss)=0.000000 (0/2663); DR(loss+fast)=0.001127 (3/2663); fast_retransmit=3.
- [1GB_44074_130](DB/1GB/1GB_44074_130); cwnd=130; throughput=111.48 MiB/s; elapsed=9.17s; DR(loss)=0.000000 (0/2399); DR(loss+fast)=0.007086 (17/2399); fast_retransmit=17.
- [1GB_58472_135](DB/1GB/1GB_58472_135); cwnd=135; throughput=111.81 MiB/s; elapsed=8.40s; DR(loss)=0.000000 (0/2749); DR(loss+fast)=0.001819 (5/2749); fast_retransmit=5.
- [1GB_49092_140](DB/1GB/1GB_49092_140); cwnd=140; throughput=112.16 MiB/s; elapsed=7.94s; DR(loss)=0.000000 (0/2770); DR(loss+fast)=0.001805 (5/2770); fast_retransmit=5.
- [1GB_41380_145](DB/1GB/1GB_41380_145); cwnd=145; throughput=111.65 MiB/s; elapsed=6.38s; DR(loss)=0.000000 (0/2675); DR(loss+fast)=0.002991 (8/2675); fast_retransmit=8.
- [1GB_44942_150](DB/1GB/1GB_44942_150); cwnd=150; throughput=112.03 MiB/s; elapsed=9.11s; DR(loss)=0.000000 (0/2794); DR(loss+fast)=0.001790 (5/2794); fast_retransmit=5.

##### BDP + Q_effective - MSS

- Calculation cwnd: 101.
- No run listed in `tpCWND.md`.

##### BDP + Q_size - MSS

- Calculation cwnd: 101.
- [1GB_42440_101](DB/1GB/1GB_42440_101); cwnd=101; throughput=111.67 MiB/s; elapsed=8.47s; DR(loss)=0.000000 (0/2816); DR(loss+fast)=0.001776 (5/2816); fast_retransmit=5.

##### BDP

- Calculation cwnd: 34.
- [1GB_44554_34](DB/1GB/1GB_44554_34); cwnd=34; throughput=110.51 MiB/s; elapsed=9.27s; DR(loss)=0.000000 (0/2860); DR(loss+fast)=0.000000 (0/2860); throughput source=total transfer.
