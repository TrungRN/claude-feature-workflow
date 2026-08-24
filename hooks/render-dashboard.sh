#!/usr/bin/env bash
# render-dashboard.sh — PostToolUse hook: rebuild plans/<slug>/dashboard.html after any
# write to a plan's markdown file, so the human-readable view is never stale.
#
# Optional. The feature-workflow skill also runs the renderer itself at its report points;
# this hook just makes the page refresh on EVERY status write, including ones made by
# subagents. Costs no model tokens — it is a plain Python script.
#
# Wired up via hooks/hooks.json when installed as a plugin, or via .claude/settings.json
# (hooks.PostToolUse) when copied into a repo by hand. Never blocks: always exits 0.

input="$(cat)"

if command -v jq >/dev/null 2>&1; then
  path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)"
else
  path="$(printf '%s' "$input" | grep -oE '"(file_path|path)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')"
fi

# Only care about markdown inside a plans/ directory.
case "$path" in
  */plans/*.md) ;;
  *) exit 0 ;;
esac

command -v python3 >/dev/null 2>&1 || exit 0

# Locate the renderer. As an installed plugin CLAUDE_PLUGIN_ROOT points at the plugin dir;
# for a hand-copied install it is unset and the skill lives under the host's .claude/.
renderer=""
for candidate in \
  "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/feature-workflow/scripts/render-dashboard.py" \
  "${CLAUDE_PROJECT_DIR:-.}/.claude/skills/feature-workflow/scripts/render-dashboard.py"; do
  [ -f "$candidate" ] && { renderer="$candidate"; break; }
done
[ -n "$renderer" ] || exit 0

python3 "$renderer" "$path" --quiet >/dev/null 2>&1
exit 0
