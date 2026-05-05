from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib-cache")
)

import matplotlib.pyplot as plt


# Add database directories here, relative to the repository root.
# Example:
# DATABASE_PATHS = [
#     "client_server/DB/1GB/1GB_58342_65",
#     "client_server/DB/1GB/1GB_44976_66",
# ]
DATABASE_PATHS = [
   "client_server/DB/1GB/1GB_58044_20",
   "client_server/DB/1GB/1GB_56648_10",
   "client_server/DB/1GB/1GB_50138_9",
   "client_server/DB/1GB/1GB_54170_8",
   "client_server/DB/1GB/1GB_41402_7",
   "client_server/DB/1GB/1GB_54302_6",
   "client_server/DB/1GB/1GB_33110_5"
]


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "CwndTime"
ELAPSED_TIME_PATTERN = re.compile(r"Sent\s+\d+\s+bytes\s+in\s+([0-9.]+)s")


def extract_cwnd(database_path: Path) -> int:
    """Extract cwnd from a database directory name like 1GB_58342_65."""
    match = re.search(r"_(\d+)$", database_path.name)
    if not match:
        raise ValueError(f"Could not extract cwnd from path: {database_path}")
    return int(match.group(1))


def extract_data_sent_size(database_path: Path) -> str:
    """Extract the data sent size from the parent directory, e.g. 1GB."""
    return database_path.parent.name


def read_elapsed_time(database_path: Path) -> float:
    server_log_path = database_path / "server.log"
    with server_log_path.open("r", encoding="utf-8") as file:
        server_log = file.read()

    match = ELAPSED_TIME_PATTERN.search(server_log)
    if not match:
        raise ValueError(f"Could not find elapsed time in {server_log_path}")

    return float(match.group(1))


def collect_points(database_paths: list[str]) -> tuple[str, list[tuple[int, float]]]:
    points = []
    data_sent_sizes = set()

    for path_string in database_paths:
        database_path = (REPO_ROOT / path_string).resolve()
        if not database_path.exists():
            raise FileNotFoundError(f"Database path does not exist: {database_path}")

        data_sent_sizes.add(extract_data_sent_size(database_path))
        points.append((extract_cwnd(database_path), read_elapsed_time(database_path)))

    if not points:
        raise ValueError("DATABASE_PATHS is empty. Add at least one database path.")

    if len(data_sent_sizes) != 1:
        sizes = ", ".join(sorted(data_sent_sizes))
        raise ValueError(f"Expected one data sent size, found: {sizes}")

    return data_sent_sizes.pop(), sorted(points)


def plot_cwnd_elapsed_time_correlation(
    data_sent_size: str, points: list[tuple[int, float]]
) -> Path:
    cwnds = [cwnd for cwnd, _ in points]
    elapsed_times = [elapsed_time for _, elapsed_time in points]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = (
        OUTPUT_DIR
        / f"cwnd_elp_time_corr_{data_sent_size}_{min(cwnds)}_{max(cwnds)}.png"
    )

    plt.figure(figsize=(8, 5))
    plt.scatter(cwnds, elapsed_times, s=70)
    plt.xlabel("cwnd")
    plt.ylabel("Elapsed time (seconds)")
    plt.title(f"cwnd vs elapsed time ({data_sent_size})")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return output_path


def main() -> None:
    data_sent_size, points = collect_points(DATABASE_PATHS)
    output_path = plot_cwnd_elapsed_time_correlation(data_sent_size, points)
    print(f"Saved graph to {output_path}")


if __name__ == "__main__":
    main()
