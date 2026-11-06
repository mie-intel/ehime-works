#!/usr/bin/env bash
# Run every benchmark script one after another.
#
#   bash benchmark/run_all.sh               # solve every grid, then plot
#   bash benchmark/run_all.sh --plot-only   # redraw all plots from the saved csv files
#
# A failing script does not stop the rest; the exit status is 1 if any script failed.

cd "$(dirname "$0")/.." || exit 1  # project root: scripts read and write results/ and plots/ relative to it

SCRIPTS=(
    n_vs_k
    n_vs_q
    q_vs_k
    lkh_vs_pyvrp_xmax_vs_q
)

failed=()
total_start=$SECONDS

for name in "${SCRIPTS[@]}"; do
    echo
    echo "=== $name ==="
    start=$SECONDS
    if uv run python "benchmark/$name.py" "$@"; then
        echo "--- $name done in $((SECONDS - start))s"
    else
        echo "--- $name FAILED after $((SECONDS - start))s"
        failed+=("$name")
    fi
done

echo
echo "=== finished in $((SECONDS - total_start))s ==="
if [ ${#failed[@]} -gt 0 ]; then
    echo "failed: ${failed[*]}"
    exit 1
fi
echo "all ${#SCRIPTS[@]} scripts succeeded"
