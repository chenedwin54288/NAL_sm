#!/usr/bin/env python3

# Example command[1]: plotting everything 
#    python3 AnalysisPhase/extract_ip_cwnd.py \
#      -i AnalysisPhase/filtered_56988.csv \
#      -o AnalysisPhase/cwnd_all.png

# Example command[2]: plotting with range
#    python3 AnalysisPhase/extract_ip_cwnd.py \
#      -i AnalysisPhase/filtered_context.csv \
#      -o AnalysisPhase/cwnd_range.png \
#      --start 100 \
#      --end 500

# Example command[3]: filter by ip, port, and then plotting with range
#    python3 client_server/AnalysisPhase/extract_ip_cwnd.py \
#      -i client_server/AnalysisPhase/filtered_context.csv \
#      --ip 128.178.122.39 \
#      --port 56988 \
#      --start 1 \
#      --end 500


import argparse
import csv
import sys
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "filtered_context.csv"
REQUIRED_COLUMNS = {"timestamp", "cwnd"}

CA_STATE_COLORS = {
    "open": "green",
    "disorder": "orange",
    "cwr": "purple",
    "recovery": "red",
    "loss": "brown",
    "unknown": "gray",
}

CA_PHASE_COLORS = {
    "slow_start": "green",
    "fast_retransmit": "orange",
    "loss_recovery": "red",
    "congestion_avoidance": "gray",
    "unknown": "black",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot cwnd samples from a filtered CSV file."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Path to filtered CSV file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: cwnd_<ip>_<port>.png when possible)",
    )
    parser.add_argument("--ip", default=None, help="Only plot this destination IP")
    parser.add_argument("--port", type=int, default=None, help="Only plot this destination port")
    parser.add_argument(
        "--start-row",
        "--start",
        type=int,
        default=None,
        help="First sample row to plot after filtering, 1-based and inclusive",
    )
    parser.add_argument(
        "--end-row",
        "--end",
        type=int,
        default=None,
        help="Last sample row to plot after filtering, 1-based and inclusive",
    )
    parser.add_argument(
        "--drop-threshold",
        type=int,
        default=10,
        help="Minimum cwnd drop between consecutive samples to mark top/bottom points",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the graph interactively in addition to saving it",
    )
    return parser.parse_args()


def validate_columns(fieldnames) -> None:
    missing_columns = REQUIRED_COLUMNS - set(fieldnames or [])
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV file is missing required columns: {missing}")


def extract_samples(csv_path: Path, ip: str | None, port: int | None):
    samples = []

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_columns(reader.fieldnames)

        for row in reader:
            if ip is not None and row.get("ip") != ip:
                continue

            row_port = row.get("port")
            if port is not None and (not row_port or int(row_port) != port):
                continue

            samples.append(
                {
                    "timestamp": float(row["timestamp"]),
                    "cwnd": int(row["cwnd"]),
                    "phase": (row.get("phase") or "unknown").lower(),
                    "ip": row.get("ip", ""),
                    "port": row.get("port", ""),
                }
            )

    return samples


def select_sample_range(samples, start_row: int | None, end_row: int | None):
    if start_row is not None and start_row < 1:
        raise ValueError("--start-row must be 1 or greater")

    if end_row is not None and end_row < 1:
        raise ValueError("--end-row must be 1 or greater")

    if start_row is not None and end_row is not None and start_row > end_row:
        raise ValueError("--start-row cannot be greater than --end-row")

    start_index = start_row - 1 if start_row is not None else 0
    end_index = end_row if end_row is not None else len(samples)
    return samples[start_index:end_index]


def find_sharktooth_edges(timestamps, cwnds, drop_threshold):
    tops = []
    bottoms = []

    for idx in range(1, len(cwnds)):
        prev_cwnd = cwnds[idx - 1]
        curr_cwnd = cwnds[idx]

        if prev_cwnd - curr_cwnd >= drop_threshold:
            tops.append((timestamps[idx - 1], prev_cwnd))
            bottoms.append((timestamps[idx], curr_cwnd))

    return tops, bottoms


# Use the user's --ip/--port if provided.
# Otherwise, if the plotted CSV rows all belong to one IP or one port, infer it automatically.
# If there are multiple IPs or ports, leave it unknown.
def infer_target(samples, ip: str | None, port: int | None):
    inferred_ip = ip
    inferred_port = str(port) if port is not None else None

    if samples and inferred_ip is None:
        ips = {sample["ip"] for sample in samples if sample["ip"]}
        if len(ips) == 1:
            inferred_ip = ips.pop()

    if samples and inferred_port is None:
        ports = {sample["port"] for sample in samples if sample["port"]}
        if len(ports) == 1:
            inferred_port = ports.pop()

    return inferred_ip, inferred_port


def build_plot(samples, top_points, bottom_points, output_path: Path, show: bool, title: str):
    first_ts = samples[0]["timestamp"]
    timestamps = [(sample["timestamp"] - first_ts) * 1000.0 for sample in samples]
    cwnds = [sample["cwnd"] for sample in samples]
    ca_phases = [sample["phase"] for sample in samples]

    top_points = [((ts - first_ts) * 1000.0, cwnd) for ts, cwnd in top_points]
    bottom_points = [((ts - first_ts) * 1000.0, cwnd) for ts, cwnd in bottom_points]

    seen_phases = []

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for idx, ca_phase in enumerate(ca_phases):
        color = CA_PHASE_COLORS.get(ca_phase, CA_PHASE_COLORS["unknown"])
        if ca_phase not in seen_phases:
            seen_phases.append(ca_phase)

        ax.scatter(
            timestamps[idx],
            cwnds[idx],
            color=color,
            s=28,
            zorder=3,
        )

        if idx > 0:
            ax.plot(
                timestamps[idx - 1:idx + 1],
                cwnds[idx - 1:idx + 1],
                color=color,
                linewidth=1.8,
                alpha=0.9,
                zorder=2,
            )

    if top_points:
        ax.scatter(
            [ts for ts, _ in top_points],
            [cwnd for _, cwnd in top_points],
            color="red",
            s=70,
            zorder=4,
            label="Sharktooth tops",
        )

    if bottom_points:
        ax.scatter(
            [ts for ts, _ in bottom_points],
            [cwnd for _, cwnd in bottom_points],
            color="green",
            s=70,
            zorder=4,
            label="Sharktooth bottoms",
        )

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=CA_PHASE_COLORS.get(ca_phase, CA_PHASE_COLORS["unknown"]),
            lw=2,
            marker="o",
            label=ca_phase,
        )
        for ca_phase in seen_phases
    ]
    if top_points:
        legend_handles.append(
            Line2D([0], [0], color="red", lw=0, marker="o", label="Sharktooth tops")
        )
    if bottom_points:
        legend_handles.append(
            Line2D([0], [0], color="green", lw=0, marker="o", label="Sharktooth bottoms")
        )

    ax.set_title(title)
    ax.set_xlabel("Time since first plotted sample (ms)")
    ax.set_ylabel("cwnd")
    ax.grid(True, linestyle="--", alpha=0.4)
    if legend_handles:
        ax.legend(handles=legend_handles, title="Legend")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return 0


def default_output_path(args, ip: str | None, port: str | None) -> Path:
    if args.output:
        return Path(args.output)

    if ip and port:
        return Path(f"cwnd_{ip.replace('.', '_')}_{port}.png")

    return Path(f"cwnd_plot.png")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input CSV file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        all_samples = extract_samples(input_path, args.ip, args.port)
        samples = select_sample_range(all_samples, args.start_row, args.end_row)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    if not samples:
        print(
            f"No matching cwnd samples found in {input_path}",
            file=sys.stderr,
        )
        return 1

    ip, port = infer_target(samples, args.ip, args.port)
    output_path = default_output_path(args, ip, port)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamps = [sample["timestamp"] for sample in samples]
    cwnds = [sample["cwnd"] for sample in samples]
    top_points, bottom_points = find_sharktooth_edges(timestamps, cwnds, args.drop_threshold)

    title_target = f" for {ip}:{port}" if ip and port else ""
    title = f"TCP cwnd{title_target}"
    if args.start_row is not None or args.end_row is not None:
        start_label = args.start_row if args.start_row is not None else 1
        end_label = args.end_row if args.end_row is not None else len(all_samples)
        title = f"{title} rows {start_label}-{end_label}"

    rc = build_plot(samples, top_points, bottom_points, output_path, args.show, title)
    if rc != 0:
        return rc

    avg_tops_cwnd = sum(cwnd for _, cwnd in top_points) / len(top_points) if top_points else 0
    avg_bottoms_cwnd = sum(cwnd for _, cwnd in bottom_points) / len(bottom_points) if bottom_points else 0
    print(f"Found {len(top_points)} sharktooth edges with drop threshold {args.drop_threshold}")
    print(f"Average top cwnd: {avg_tops_cwnd:.2f}")
    print(f"Average bottom cwnd: {avg_bottoms_cwnd:.2f}")
    print(
        f"Saved graph with {len(samples)} samples from {input_path} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
