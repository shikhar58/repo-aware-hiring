#!/usr/bin/env bash
# Score an eval workspace N times, each in a fresh headless Claude Code session,
# so consistency is measured across independent runs.
#
# Usage: evals/run_screening.sh <workspace> [N=3]
# Requires the Claude Code CLI with this plugin's skills installed in the project.
# Adjust the CLI flags below if your version differs.
set -euo pipefail

WS="${1:?usage: run_screening.sh <workspace> [N]}"
N="${2:-3}"

for i in $(seq 1 "$N"); do
  OUT="$WS/runs/run-$i/scores"
  if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
    echo "run-$i exists, skipping"; continue
  fi
  mkdir -p "$OUT"
  echo "== run-$i"
  claude -p "Use the screen-candidates skill on the workspace $WS. The CVs are already prepared and redacted: skip steps 1-2 and do not modify redacted/. Score every candidate into $OUT (one JSON per candidate id). Do not read any other folder under $WS/runs. Run validate_scores.py with --scores-dir $OUT and fix any errors. Do not rank or write a report." \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python3:*)"
done

python3 "$(dirname "$0")/evaluate.py" "$WS"
