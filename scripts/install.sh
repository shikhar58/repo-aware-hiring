#!/usr/bin/env bash
# Install the repo-aware-hiring skills into a coding agent's skills folder, by copying them.
# No network access, no Node, no dependencies beyond bash and cp.
#
#   ./scripts/install.sh --agents            # Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode…: ./.agents/skills/
#   ./scripts/install.sh --claude            # Claude Code: ./.claude/skills/
#   ./scripts/install.sh --agents --global   # for every project: ~/.agents/skills/ (or ~/.claude/skills/ with --claude)
#   ./scripts/install.sh --dir PATH          # any other skills folder
#   ./scripts/install.sh --agents --remove   # uninstall from that folder
#
# Run it from the project you're hiring for (project installs go into the current folder).
# Existing copies of these skills are updated in place; a different skill with the same name is left alone unless
# you pass --force.
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills"
MARKER=".repo-aware-hiring"
targets=() global=0 remove=0 force=0 custom=""

while [ $# -gt 0 ]; do
  case "$1" in
    --claude) targets+=("claude") ;;
    --agents|--codex|--cursor|--gemini|--copilot|--opencode) targets+=("agents") ;;
    --global|-g) global=1 ;;
    --dir) shift; [ $# -gt 0 ] || { echo "--dir needs a path" >&2; exit 2; }; custom="$1"; targets+=("custom") ;;
    --remove|--uninstall) remove=1 ;;
    --force) force=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ ! -d "$SRC" ] || [ ! -f "$SRC/map-codebase/SKILL.md" ]; then
  echo "Can't find the skills next to this script ($SRC). Run it from a clone of repo-aware-hiring." >&2
  exit 1
fi
if [ ${#targets[@]} -eq 0 ]; then
  echo "Choose where to install: --agents (Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode…), --claude, or --dir PATH." >&2
  usage >&2
  exit 2
fi
if [ "$global" -eq 0 ] && [ "$(pwd -P)" = "$(cd "$SRC/.." && pwd -P)" ]; then
  echo "You're inside the repo-aware-hiring clone. cd into the project you're hiring for, or use --global." >&2
  exit 2
fi

dest_for() {
  case "$1" in
    claude) [ "$global" -eq 1 ] && echo "$HOME/.claude/skills" || echo "$(pwd)/.claude/skills" ;;
    agents) [ "$global" -eq 1 ] && echo "$HOME/.agents/skills" || echo "$(pwd)/.agents/skills" ;;
    custom) echo "$custom" ;;
  esac
}

status=0
for t in $(printf '%s\n' "${targets[@]}" | sort -u); do
  dest="$(dest_for "$t")"
  if [ "$remove" -eq 1 ]; then
    n=0
    for skill in "$SRC"/*/; do
      name="$(basename "$skill")"
      if [ -f "$dest/$name/$MARKER" ]; then rm -rf "${dest:?}/$name"; n=$((n + 1)); fi
    done
    echo "Removed $n skill(s) from $dest"
    continue
  fi
  mkdir -p "$dest"
  installed=0 skipped=0
  for skill in "$SRC"/*/; do
    name="$(basename "$skill")"
    if [ -e "$dest/$name" ] && [ ! -f "$dest/$name/$MARKER" ] && [ "$force" -eq 0 ]; then
      echo "  skip $name: $dest/$name exists and isn't from repo-aware-hiring (use --force to replace it)" >&2
      skipped=$((skipped + 1)); status=1; continue
    fi
    rm -rf "${dest:?}/$name"
    cp -R "$skill" "$dest/$name"
    find "$dest/$name" -name '__pycache__' -type d -prune -exec rm -rf {} +
    echo "installed by scripts/install.sh; remove with: install.sh --remove" > "$dest/$name/$MARKER"
    installed=$((installed + 1))
  done
  echo "Installed $installed skill(s) into $dest$([ "$skipped" -gt 0 ] && echo " ($skipped skipped)")"
done

if [ "$remove" -eq 0 ]; then
  echo
  echo "Next: open your coding agent in your project and ask, for example:"
  echo "  Write a job description for someone to own the database layer"
  command -v python3 >/dev/null 2>&1 || echo "Note: the skills need python3 (3.9 or later) on your PATH." >&2
fi
exit $status
