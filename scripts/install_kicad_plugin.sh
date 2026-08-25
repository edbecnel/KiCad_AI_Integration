#!/usr/bin/env bash
# Install or refresh the KiCad AI Assistant ActionPlugin symlink for local development.
#
# Usage:
#   ./scripts/install_kicad_plugin.sh
#   ./scripts/install_kicad_plugin.sh --plugin-dir "$HOME/Documents/KiCad/10.0/scripting/plugins"
#   ./scripts/install_kicad_plugin.sh --check
#
# After install or code changes: restart KiCad PCB Editor (Python modules are cached
# in the running process). No file copy is required when using a symlink.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_ENTRY="$REPO_ROOT/src/plugin/kicad_ai_assistant_plugin.py"
LINK_NAME="kicad_ai_assistant.py"
CHECK_ONLY=0
PLUGIN_DIR=""

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \?//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --check)
      CHECK_ONLY=1
      shift
      ;;
    --plugin-dir)
      PLUGIN_DIR="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$PLUGIN_ENTRY" ]]; then
  echo "Plugin entry not found: $PLUGIN_ENTRY" >&2
  exit 1
fi

discover_plugin_dir() {
  if [[ -n "$PLUGIN_DIR" ]]; then
    echo "$PLUGIN_DIR"
    return
  fi
  if [[ -n "${KICAD_PLUGIN_DIR:-}" ]]; then
    echo "$KICAD_PLUGIN_DIR"
    return
  fi

  local candidates=()
  local docs_base="$HOME/Documents/KiCad"
  local prefs_base="$HOME/Library/Preferences/kicad"

  if [[ -d "$docs_base" ]]; then
    while IFS= read -r ver; do
      candidates+=("$docs_base/$ver/scripting/plugins")
    done < <(find "$docs_base" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort -Vr)
  fi
  if [[ -d "$prefs_base" ]]; then
    while IFS= read -r ver; do
      candidates+=("$prefs_base/$ver/scripting/plugins")
    done < <(find "$prefs_base" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort -Vr)
  fi

  for dir in "${candidates[@]}"; do
    if [[ -d "$(dirname "$dir")" ]]; then
      echo "$dir"
      return
    fi
  done

  echo ""
}

PLUGIN_DIR="$(discover_plugin_dir)"
if [[ -z "$PLUGIN_DIR" ]]; then
  echo "Could not find KiCad scripting/plugins directory." >&2
  echo "Set KICAD_PLUGIN_DIR or pass --plugin-dir." >&2
  echo "Find yours in KiCad PCB Editor → Tools → Scripting Console:" >&2
  echo "  import pcbnew; print(pcbnew.PLUGIN_DIRECTORIES_SEARCH)" >&2
  exit 1
fi

LINK_PATH="$PLUGIN_DIR/$LINK_NAME"

report_status() {
  echo "Repository:  $REPO_ROOT"
  echo "Plugin file: $PLUGIN_ENTRY"
  echo "Plugins dir: $PLUGIN_DIR"
  echo "Symlink:     $LINK_PATH"
  if [[ -L "$LINK_PATH" ]]; then
    echo "Target:      $(readlink "$LINK_PATH")"
    echo "Resolved:    $(readlink -f "$LINK_PATH" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$LINK_PATH")"
  elif [[ -e "$LINK_PATH" ]]; then
    echo "Status:      exists but is not a symlink (manual install?)"
  else
    echo "Status:      not installed"
  fi
}

verify_link() {
  if [[ ! -L "$LINK_PATH" ]]; then
    echo "FAIL: symlink missing at $LINK_PATH" >&2
    return 1
  fi
  local resolved
  resolved="$(readlink -f "$LINK_PATH" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$LINK_PATH")"
  if [[ "$resolved" != "$(readlink -f "$PLUGIN_ENTRY" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$PLUGIN_ENTRY")" ]]; then
    echo "FAIL: symlink points to $resolved" >&2
    echo "      expected $PLUGIN_ENTRY" >&2
    return 1
  fi
  echo "OK: plugin symlink points at repository entry file."
  return 0
}

report_status

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  verify_link
  exit $?
fi

mkdir -p "$PLUGIN_DIR"
ln -sfn "$PLUGIN_ENTRY" "$LINK_PATH"

# Remove legacy package symlink if present (directory install — less reliable).
LEGACY_LINK="$PLUGIN_DIR/kicad_ai_assistant"
if [[ -L "$LEGACY_LINK" && "$(basename "$(readlink "$LEGACY_LINK")")" == "kicad_ai_assistant" ]]; then
  rm "$LEGACY_LINK"
  echo "Removed legacy package symlink: $LEGACY_LINK"
fi

echo
verify_link
echo
echo "Next steps:"
echo "  1. Restart KiCad PCB Editor (required to reload Python after code changes)."
echo "  2. Open Tools → External Plugins → KiCad AI Assistant."
echo "  3. Optional: export KICAD_AI_SRC if the symlink ever breaks:"
echo "       export KICAD_AI_SRC=\"$REPO_ROOT/src\""
