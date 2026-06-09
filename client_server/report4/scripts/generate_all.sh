#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

export PYTHONDONTWRITEBYTECODE=1

python3 scripts/export_results_csv.py
python3 scripts/plot_strategy_throughput.py
python3 scripts/plot_empirical_burst_sensitivity.py
python3 scripts/plot_empirical_gain_heatmap.py
python3 scripts/plot_cwnd_selection.py
python3 scripts/plot_best_strategy_counts.py
python3 scripts/write_analysis_readme.py
