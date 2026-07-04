#!/usr/bin/env bash
# guard-paths.sh — PreToolUse guard for the Write/Edit tools.
# Denies (or just warns on) edits to files outside an allowlist of directories.
# This is the "hard enforcement" layer: it runs deterministically on every
# matching tool call, including calls made by the task-executor subagents.
#
# Uses jq if available, with a pure-bash fallback otherwise (jq recommended for
# robustness). Wired up via .claude/settings.json (hooks.PreToolUse) — see that file.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ SHIPPED IN "warn" MODE so it can't surprise-block your work on first run. │
# │ To turn on real enforcement:                                             │
# │   1. Set ALLOWED_REGEX below to match YOUR repo's editable directories.  │
# │   2. Change MODE from "warn" to "block".                                  │
# └─────────────────────────────────────────────────────────────────────────┘

# --- edit these two lines for your repo ---
MODE="warn"                                    # "warn" = log only, allow | "block" = deny
ALLOWED_REGEX='(^|/)(src|plans|tests)/'        # paths matching this are allowed
# ------------------------------------------

input="$(cat)"
# Extract the target path. Prefer jq; fall back to a best-effort grep so the
# guard still works (and doesn't silently fail open) when jq isn't installed.
if command -v jq >/dev/null 2>&1; then
  path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)"
else
  path="$(printf '%s' "$input" | grep -oE '"(file_path|path)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')"
fi

# No file target on this tool call → nothing to guard.
[ -z "$path" ] && exit 0

# Inside the allowlist → allow.
if printf '%s' "$path" | grep -Eq "$ALLOWED_REGEX"; then
  exit 0
fi

# Outside the allowlist.
if [ "$MODE" = "warn" ]; then
  echo "guard-paths (warn): edit outside allowlist would be blocked: $path" >&2
  exit 0
fi

# MODE=block → deny the tool call. Exit code 2 blocks it; stderr is shown to Claude.
echo "Blocked by guard-paths hook: '$path' is outside the allowed directories. Adjust ALLOWED_REGEX in .claude/hooks/guard-paths.sh if this path should be editable." >&2
exit 2
