#!/usr/bin/env bash
# Re-run the two grids used on the poster, then redraw the poster figure.
#
#   bash benchmark/run_poster.sh
#
# Writes results/n_vs_k.csv, results/n_vs_q.csv, plots/results/overview_v2.png,
# and a log per step in logs/. Stops at the first step that fails.

cd "$(dirname "$0")/.." || exit 1  # project root: scripts read and write results/ and plots/ relative to it
mkdir -p logs

STEPS=(
    "grids:uv run python benchmark/poster_grids.py"  # N vs K and N vs Q in one process: shared cells solved once
    "results_viz:uv run python results_viz.py"
)

total_start=$SECONDS

for step in "${STEPS[@]}"; do
    name=${step%%:*}
    cmd=${step#*:}
    echo
    echo "=== $name ($(date '+%F %T')) ==="
    start=$SECONDS
    if $cmd 2>&1 | tee "logs/$name.log"; [ "${PIPESTATUS[0]}" -eq 0 ]; then
        echo "--- $name done in $((SECONDS - start))s"
    else
        echo "--- $name FAILED after $((SECONDS - start))s (see logs/$name.log)"
        exit 1
    fi
done

echo
echo "=== all done in $((SECONDS - total_start))s ==="
