#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="$(basename "$SKILL_DIR")"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST_PARENT="$CODEX_HOME/skills"
DEST="$DEST_PARENT/$SKILL_NAME"

install_one() {
  local dest_parent="$1"
  local dest="$dest_parent/$SKILL_NAME"
  mkdir -p "$dest_parent"
  rm -rf "$dest"
  cp -R "$SKILL_DIR" "$dest"
  find "$dest" -type d -name "__pycache__" -prune -exec rm -rf {} +
  find "$dest" -type f -name "*.pyc" -delete
  echo "Installed $SKILL_NAME -> $dest"
}

install_one "$DEST_PARENT"

if [[ "${1:-}" == "--claude" ]]; then
  install_one "$HOME/.claude/skills"
fi
