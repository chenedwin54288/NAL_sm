from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib-cache")
)

import matplotlib.pyplot as plt


# Add database directory groups here, relative to the repository root.
# Each inner list becomes one line on the graph.
DATABASE_PATH_GROUPS = [
    [
        "client_server/DB/1GB/1GB_44976_66",
        "client_server/DB/1GB/1GB_60496_66",
        "client_server/DB/1GB/1GB_59712_66",

        "client_server/DB/3GB/3GB_41720_66",
        "client_server/DB/3GB/3GB_53118_66",
        "client_server/DB/3GB/3GB_42416_66",

        "client_server/DB/5GB/5GB_47564_66",
        "client_server/DB/5GB/5GB_39666_66",
        "client_server/DB/5GB/5GB_49806_66",

        "client_server/DB/10GB/10GB_43516_66",
        "client_server/DB/10GB/10GB_49130_66",
        "client_server/DB/10GB/10GB_35696_66",
    ],
    [
        "client_server/DB/1GB/1GB_49584_0",
        "client_server/DB/1GB/1GB_54842_0",
        "client_server/DB/1GB/1GB_49888_0",

        "client_server/DB/3GB/3GB_52036_0",
        "client_server/DB/3GB/3GB_53844_0",
        "client_server/DB/3GB/3GB_50212_0",

        "client_server/DB/5GB/5GB_39710_0",
        "client_server/DB/5GB/5GB_46362_0",
        "client_server/DB/5GB/5GB_43370_0",

        "client_server/DB/10GB/10GB_40504_0",
        "client_server/DB/10GB/10GB_48670_0",
        "client_server/DB/10GB/10GB_41618_0",
    ],
]


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "DataSizeTime"
ELAPSED_TIME_PATTERN = re.compile(r"Sent\s+\d+\s+bytes\s+in\s+([0-9.]+)s")
SIZE_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)([KMGTP]?B)$", re.IGNORECASE)
SIZE_UNITS = {
    "B": 1,
    "KB": 1_000,
    "MB": 1_000_000,
    "GB": 1_000_000_000,
    "TB": 1_000_000_000_000,
    "PB": 1_000_000_000_000_000,
}


def extract_data_size(database_path: Path) -> str:
    """Extract the data size from the parent directory, e.g. 1GB."""
    return database_path.parent.name


def data_size_sort_key(data_size: str) -> float:
    """Sort labels like 1GB, 3GB, 10GB by their numeric byte size."""
    match = SIZE_PATTERN.match(data_size)
    if not match:
        return float("inf")

    value = float(match.group(1))
    unit = match.group(2).upper()
    return value * SIZE_UNITS[unit]


def read_elapsed_time(database_path: Path) -> float:
    server_log_path = database_path / "server.log"
    with server_log_path.open("r", encoding="utf-8") as file:
        server_log = file.read()

    matches = ELAPSED_TIME_PATTERN.findall(server_log)
    if not matches:
        raise ValueError(f"Could not find elapsed time in {server_log_path}")

    return float(matches[-1]) * 1000.0


def infer_group_label(group_index: int, database_paths: list[str]) -> str:
    """Use a shared final directory suffix as the line label when possible."""
    suffixes = set()

    for path_string in database_paths:
        suffix = Path(path_string).name.rsplit("_", 1)[-1]
        suffixes.add(suffix)

    if len(suffixes) == 1:
        suffix = suffixes.pop()
        return f"cwnd={suffix}"

    return f"group {group_index}"


def collect_group_averages(
    database_paths: list[str],
) -> list[tuple[str, float]]:
    elapsed_times_by_size: dict[str, list[float]] = defaultdict(list)

    for path_string in database_paths:
        database_path = (REPO_ROOT / path_string).resolve()
        if not database_path.exists():
            raise FileNotFoundError(f"Database path does not exist: {database_path}")

        data_size = extract_data_size(database_path)
        elapsed_times_by_size[data_size].append(read_elapsed_time(database_path))

    if not elapsed_times_by_size:
        raise ValueError("Empty database path group. Add at least one path.")

    return sorted(
        (
            (data_size, mean(elapsed_times))
            for data_size, elapsed_times in elapsed_times_by_size.items()
        ),
        key=lambda point: data_size_sort_key(point[0]),
    )


def collect_all_group_averages(
    database_path_groups: list[list[str]],
) -> list[tuple[str, list[tuple[str, float]]]]:
    if not database_path_groups:
        raise ValueError("DATABASE_PATH_GROUPS is empty. Add at least one path group.")

    group_averages = []
    for group_index, database_paths in enumerate(database_path_groups, start=1):
        label = infer_group_label(group_index, database_paths)
        averages = collect_group_averages(database_paths)
        group_averages.append((label, averages))

    return group_averages


def plot_data_elapsed_time_correlation(
    group_averages: list[tuple[str, list[tuple[str, float]]]]
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "data_elp_time_corr.png"

    plt.figure(figsize=(8, 5))

    for label, averages in group_averages:
        data_sizes = [data_size for data_size, _ in averages]
        elapsed_times = [elapsed_time for _, elapsed_time in averages]
        plt.plot(data_sizes, elapsed_times, marker="o", linewidth=2, label=label)

    plt.xlabel("Data size")
    plt.ylabel("Average elapsed time (ms)")
    plt.title("Data size vs average elapsed time")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return output_path


def main() -> None:
    group_averages = collect_all_group_averages(DATABASE_PATH_GROUPS)
    output_path = plot_data_elapsed_time_correlation(group_averages)

    for label, averages in group_averages:
        print(label)
        for data_size, elapsed_time in averages:
            print(f"  {data_size}: {elapsed_time:.2f}ms")

    print(f"Saved graph to {output_path}")


if __name__ == "__main__":
    main()
