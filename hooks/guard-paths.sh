#!/usr/bin/env bash
# guard-paths.sh — PreToolUse guard for the Write/Edit tools.
# Denies (or just warns on) edits to files outside an allowlist of directories.
# This is the "hard enforcement" layer: it runs deterministically on every
# matching tool call, including calls made by the task-executor subagents.
#
# Uses jq if available, with a pure-bash fallback otherwise (jq recommended for
# robustness). Wired up via hooks/hooks.json (plugin install) or .claude/settings.json
# (hooks.PreToolUse) for a hand-copied install.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ SHIPPED OFF. As an installed plugin this hook runs in every repo, so it   │
# │ stays inert until you opt in, per repo, via env vars in that repo's       │
# │ .claude/settings.json:                                                    │
# │                                                                           │
# │   "env": {                                                                │
# │     "FW_GUARD_MODE": "warn",                    // or "block"             │
# │     "FW_GUARD_ALLOWED": "(^|/)(src|plans|tests)/"                         │
# │   }                                                                       │
# │                                                                           │
# │ off   = do nothing (default)                                              │
# │ warn  = log to stderr, allow the write                                    │
# │ block = deny the write (exit 2)                                           │
# └─────────────────────────────────────────────────────────────────────────┘

MODE="${FW_GUARD_MODE:-off}"                                  # off | warn | block
ALLOWED_REGEX="${FW_GUARD_ALLOWED:-(^|/)(src|plans|tests)/}"  # paths matching this are allowed

# Not opted in → stay out of the way entirely.
[ "$MODE" = "off" ] && exit 0

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
echo "Blocked by guard-paths hook: '$path' is outside the allowed directories. Adjust FW_GUARD_ALLOWED in this repo's .claude/settings.json if this path should be editable." >&2
exit 2
