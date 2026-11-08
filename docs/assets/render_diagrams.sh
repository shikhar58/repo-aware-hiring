#!/usr/bin/env bash
# Re-render the README diagrams from their Mermaid sources as 2x PNGs.
# PNGs are used (not Mermaid blocks) because the GitHub mobile app shows Mermaid as source code.
# Needs Node.js; uses @mermaid-js/mermaid-cli via npx.
set -euo pipefail
cd "$(dirname "$0")"
for n in how-it-works safeguards system-map; do
  npx -y @mermaid-js/mermaid-cli@11 -i "$n.mmd" -o "$n.png" -b white -s 2 -w 900
done
