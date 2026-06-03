# Integration Workflow

This directory contains the orchestration scripts that connect three pieces:

- `integration/wehe-py3`: the WeHe replay server Docker image.
- `integration/client_server`: the bulk TCP sender used for the controlled transfer.
- `integration/client`: the TCP receiver that advertises the computed receive window.

The scripts are intended to be run on two different machines:

- Server machine: `run_server.sh`
- Client machine: `run_client.sh`

## Scripts

### `run_server.sh`

Runs on the server machine.

It performs this sequence:

1. Builds the WeHe Docker image from `integration/wehe-py3`.
2. Starts the WeHe server container with host networking.
3. Stores the Docker container ID so it can stop the container later.
4. Waits until the WeHe ports are reachable.
5. Starts `integration/client_server/run.sh`.
6. Waits for `client_server/run.sh` to finish.
7. Stops the WeHe Docker container.

By default it passes these arguments to `client_server/run.sh`:

```bash
--cca my_cca --cwnd 0
```

This keeps `my_cca` as the default congestion-control module while disabling
the sender-side CWND cap. Any later `--cca` or `--cwnd` argument passed by the
user overrides these defaults.

Important: with the current launch order, `client_server/run.sh` is started
before the client runs the WeHe replay. If the user passes TBF settings,
`client_server/run.sh` applies the TBF qdisc before the WeHe replay runs. Since
the WeHe Docker container uses host networking, that TBF can also affect WeHe
server egress traffic on the same interface.

### `run_client.sh`

Runs on the client machine.

It performs this sequence:

1. Runs the WeHe command-line client against the WeHe server.
2. Reads the newest WeHe result log.
3. Extracts the configured throughput field, defaulting to `xput_avg_original`.
4. Computes an `rwnd` value in MSS-sized segments.
5. Starts `integration/client/client.py` with `--rwnd-segments`.

The WeHe replay is trace-paced. It is not a bulk capacity test like
`client_server/Server/server.py`. For example, the Amazon replay can average
around 15 Mbit/s even when the later bulk transfer can reach about 250 Mbit/s.

### `wehe_result_to_rwnd.py`

Helper used by `run_client.sh`.

It can also be run manually to inspect a WeHe result and the computed receive
window.

Without a queue value:

```text
BDP_bytes = throughput_mbit_per_second * 1,000,000 * RTT_seconds / 8
rwnd_segments = ceil(BDP_bytes / MSS_bytes)
```

With `--queue-bytes` or `--tbf-limit`:

```text
byte_budget = max(BDP_bytes + queue_bytes - MSS_bytes, MSS_bytes)
rwnd_segments = floor(byte_budget / MSS_bytes)
```

The default RTT is `0.4 ms`, and the default MSS is `1460 bytes`.

## Launch Order

Start the server side first:

```bash
./integration/run_server.sh --wehe-host 192.168.88.254 -- \
  --size-gib 1 \
  --rtt-ms 0.4 \
  --rate-mbit 250 \
  --tbf-rate 250Mbit \
  --tbf-burst 50000b \
  --tbf-limit 6250b
```

Then start the client side:

```bash
./integration/run_client.sh \
  --wehe-server 192.168.88.254 \
  --client-server-host 192.168.88.254 \
  --rtt-ms 0.4 \
  --queue-bytes 6250b
```

The client first runs the WeHe replay. After WeHe finishes, it computes `rwnd`
and connects to the `client_server` TCP server.

## Server Parameters

`run_server.sh` has two classes of parameters.

### Server Wrapper Parameters

These parameters control the WeHe Docker wrapper:

```text
--wehe-host HOST
```

Public hostname or IP passed to the WeHe Docker container. Default:
`192.168.88.254`.

```text
--wehe-interface IFACE
```

Optional network interface passed as the second argument to WeHe
`startserver.sh`.

```text
--wehe-image NAME
```

Docker image tag to build and run. Default: `wehe`.

```text
--wehe-ready-ports LIST
```

Space- or comma-separated port list to wait for before starting
`client_server/run.sh`. Default: `55556 56566 80 443`.

```text
--wehe-ready-timeout SEC
```

Seconds to wait for WeHe readiness. Default: `120`.

```text
--build
```

Build the WeHe Docker image before running it. This is the default.

```text
--no-build
```

Skip the Docker build and run the existing image.

### `client_server/run.sh` Pass-Through Parameters

Everything after `--` is passed to `integration/client_server/run.sh`.

Common user-set experiment parameters:

```text
--size-gib N
--rtt-ms N
--rate-mbit N
--tbf-rate RATE
--tbf-burst BURST
--tbf-limit LIMIT
```

Other useful pass-through parameters:

```text
--host HOST
--port PORT
--dev IFACE
--file PATH
--log-interval SECONDS
--cca NAME
--cwnd N
--mss-bytes N
```

Example:

```bash
./integration/run_server.sh --wehe-host 192.168.88.254 -- \
  --size-gib 1 \
  --rtt-ms 0.4 \
  --rate-mbit 250 \
  --tbf-rate 250Mbit \
  --tbf-burst 50000b \
  --tbf-limit 6250b
```

The `--` separator is recommended because it clearly separates wrapper options
from `client_server/run.sh` experiment options.

## Client Parameters

`run_client.sh` parameters:

```text
--replay NAME
```

WeHe replay name. Default: `amazon`.

Examples:

```text
amazon
deezer
molotovtv
port853l
```

`deezer` is the strongest app replay by sustained average rate among the traces
inspected in this repo. Some port-large replays have stronger short bursts.

```text
--wehe-server HOST
```

WeHe server hostname or IP. Default: `192.168.88.254`.

```text
--client-server-host HOST
```

Host for the later `client.py` connection. Default: `192.168.88.254`.

```text
--client-server-port PORT
```

Port for the later `client.py` connection. Default: `9000`.

```text
--results-dir DIR
```

Directory where the WeHe command-line client writes logs and UI output.
Default: `integration/client/wehe-cmdline/results`.

```text
--log-level LEVEL
```

WeHe command-line client log level. Default: `info`.

```text
--rtt-ms N
```

RTT used in the `rwnd` BDP calculation. Default: `0.4`.

```text
--mss-bytes N
```

MSS used to convert bytes to `rwnd` segments. Default: `1460`.

```text
--queue-bytes VALUE
--tbf-limit VALUE
```

Optional queue size used in the queue-aware `rwnd` formula. These are aliases.
Use the same value as the server-side TBF limit when the client-side calculation
should account for that queue.

```text
--throughput-field FIELD
```

WeHe JSON throughput field used for the BDP calculation. Default:
`xput_avg_original`.

```text
--rwnd-segments N
```

Skip WeHe-based calculation and use this receive-window value directly.

```text
--sudo-java
```

Run the WeHe Java client with `sudo`. This is the default.

```text
--no-sudo-java
```

Run the WeHe Java client without `sudo`.

```text
--java-bin PATH
```

Java binary to execute. Default: `java`.

Example:

```bash
./integration/run_client.sh \
  --replay deezer \
  --wehe-server 192.168.88.254 \
  --client-server-host 192.168.88.254 \
  --rtt-ms 0.4 \
  --queue-bytes 6250b
```

## Helper Parameters

`wehe_result_to_rwnd.py` is normally called by `run_client.sh`, but users can
run it directly when they want to inspect or override the calculation.

```text
--results-dir DIR
```

WeHe result directory to scan. Default:
`integration/client/wehe-cmdline/results`.

```text
--since-epoch SECONDS
```

Only consider WeHe result files modified at or after this Unix epoch time.
`run_client.sh` uses this to avoid accidentally reading an older replay result.

```text
--throughput-field FIELD
```

WeHe JSON field used as the throughput in Mbit/s. Default:
`xput_avg_original`.

```text
--throughput-mbit N
```

Use this throughput value directly instead of reading WeHe result files.

```text
--rtt-ms N
```

RTT used in the BDP calculation. Default: `0.4`.

```text
--mss-bytes N
```

MSS used to convert byte budget to `rwnd` segments. Default: `1460`.

```text
--queue-bytes VALUE
--tbf-limit VALUE
```

Optional queue/TBF limit. These are aliases and enable the queue-aware formula.

```text
--json
```

Print the complete calculation as JSON.

```text
--value-only
```

Print only the computed `rwnd` segment count.

Example:

```bash
python3 ./integration/wehe_result_to_rwnd.py \
  --throughput-mbit 15 \
  --rtt-ms 0.4 \
  --queue-bytes 6250b
```

## Notes

- WeHe throughput values are in Mbit/s.
- `client_server/Server/server.py` is a bulk sender, not a trace-paced replay.
- WeHe app replays may not saturate the TBF rate, depending on the replay.
- For the later bulk transfer, the effective rate is limited by TCP, the
  advertised client `rwnd`, the sender CCA, `SO_MAX_PACING_RATE`, and any TBF
  configuration.
